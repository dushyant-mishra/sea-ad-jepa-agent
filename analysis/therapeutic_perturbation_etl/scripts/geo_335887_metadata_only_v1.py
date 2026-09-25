#!/usr/bin/env python3
"""Read GEO series SAMPLE/SERIES metadata, never any sample expression table."""
import argparse,gzip,hashlib,io,json,re,urllib.request
from pathlib import Path
GSE="GSE335887"
URL="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE335nnn/GSE335887/soft/GSE335887_family.soft.gz"
SAMPLE_KEYS={"title","source_name_ch1","characteristics_ch1","description","relation","growth_protocol_ch1","treatment_protocol_ch1","extract_protocol_ch1","library_strategy","instrument_model"}
SERIES_KEYS={"title","overall_design","sample_id","relation","summary"}
def parse_header_only(plain):
    """Stop at each sample table and skip its rows. Do not inspect tabular data."""
    if not isinstance(plain,(bytes,bytearray)):raise ValueError("source must be bytes")
    series={};samples={};current=None;in_table=False;table_skipped=0
    for line in io.TextIOWrapper(io.BytesIO(plain),encoding="utf-8-sig",errors="strict"):
        line=line.rstrip("\r\n")
        if line.startswith("^"):
            in_table=False
            if line.startswith("^SAMPLE = "):
                current=line.split(" = ",1)[1].strip()
                if not re.fullmatch(r"GSM\d+",current) or current in samples:raise ValueError("STOP: invalid/duplicate GEO sample ID")
                samples[current]={}
            else:current=None
            continue
        if in_table:
            if line.lower().startswith("!sample_table_end"):in_table=False
            else:table_skipped+=1
            continue
        if line.lower().startswith("!sample_table_begin"):
            if current is None:raise ValueError("STOP: sample table outside sample")
            in_table=True;continue
        if not line.startswith("!") or " = " not in line:continue
        key,value=line[1:].split(" = ",1)
        if current and key.startswith("Sample_"):
            field=key[len("Sample_"):].lower()
            if field in SAMPLE_KEYS:samples[current].setdefault(field,[]).append(value.strip()[:4000])
        elif current is None and key.startswith("Series_"):
            field=key[len("Series_"):].lower()
            if field in SERIES_KEYS:series.setdefault(field,[]).append(value.strip()[:4000])
    if in_table:raise ValueError("STOP: unterminated sample expression table")
    if len(samples)!=8:raise ValueError("STOP: GEO sample census %s not 8"%len(samples))
    series_ids=series.get("sample_id",[])
    if series_ids and sorted(series_ids)!=sorted(samples):raise ValueError("STOP: Series/sample ID mismatch")
    for gsm,v in samples.items():
        if not v.get("title") or not v.get("source_name_ch1"):raise ValueError("STOP: missing title/source for "+gsm)
    return {"series_metadata":series,"samples":samples,"sample_count":len(samples),
            "sample_expression_values_inspected":False,"sample_expression_table_lines_skipped":table_skipped}
def build_from_source(compressed):
    if len(compressed)>30000000:raise ValueError("STOP: unexpected source size")
    if compressed[:2]!=b"\x1f\x8b":raise ValueError("STOP: source not gzip")
    plain=gzip.decompress(compressed)
    o=parse_header_only(plain)
    o.update({"schema":"GSE335887_GEO_METADATA_ONLY_V1","gse":GSE,
              "source_url":URL,"soft_gzip_bytes":len(compressed),
              "soft_gzip_sha256":hashlib.sha256(compressed).hexdigest(),
              "source_status":"PUBLIC_GEO_METADATA_NOT_PERTURBATION_RESPONSE",
              "replicate_authority":"READ_EXPLICIT_METADATA_DO_NOT_INFER_FROM_CELL_COUNTS",
              "jepa_training_authorized":False})
    return o
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-soft-gz",type=Path,help="Authenticated public GEO SOFT gzip provided locally")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():raise SystemExit("STOP: refuse overwrite")
    if args.input_soft_gz:source=args.input_soft_gz.read_bytes()
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":"JEPA-METADATA-AUDIT/1.0 (public GEO metadata)"})
        with urllib.request.urlopen(req,timeout=70) as response:
            if int(response.status)!=200:raise RuntimeError("GEO HTTP %s"%response.status)
            source=response.read(30000001)
    report=build_from_source(source);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("GEO METADATA ONLY:",report["sample_count"],"samples, soft_sha256",report["soft_gzip_sha256"])
if __name__=="__main__":main()
