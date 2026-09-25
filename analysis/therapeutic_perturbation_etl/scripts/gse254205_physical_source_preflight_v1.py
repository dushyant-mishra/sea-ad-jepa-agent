#!/usr/bin/env python3
"""Read-only physical source preflight for GSE254205 bulk V2 execution.

The nine immutable input CSV file digests below are not user-supplied:
they are bound to PR77's source-authenticated GSE254205 sample inventory.
This preflight never computes/looks at differential expression and never writes
inside the input directory. Claude should execute it BEFORE draft PR86 V2.
"""
import argparse,csv,hashlib,io,json,os,tarfile
from pathlib import Path
SOURCE_INVENTORY="analysis/therapeutic_perturbation_etl/evidence/gse254205/GSE254205_sample_identity.csv"
SOURCE_GIT_BLOB_ID="4e0296a6aedeb31b36d1dc2361b451f334b2588e"
ARCHIVE_NAME="GSE254205_iMG_AB_GNE_treatment_RNA_Seq.tar.gz"
ARCHIVE_BYTES=2327894
ARCHIVE_SHA256="ae3761514b5ac0bf37ae727ab956f6e6bee70c4dab52519ab2f20cc9a322d569"
N_EXPECTED=9
def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def git_blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
def parse_frozen_inventory(raw, *, fake_fixture=False):
    if not fake_fixture and git_blob(raw)!=SOURCE_GIT_BLOB_ID:
        raise ValueError("STOP: frozen PR77 nine-sample source inventory blob differs")
    rd=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    expected=("sample_id","condition","replicate","amyloid","compound","file","file_sha256","total_counts","genes_detected")
    if tuple(rd.fieldnames or ())!=expected:raise ValueError("STOP: frozen source inventory schema/order")
    parsed={};samples=set();cell_design={}
    for row in rd:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("STOP: malformed source inventory row")
        name=row["file"];sid=row["sample_id"];cond=row["condition"];rep=row["replicate"]
        if name!=f"{cond}_{rep}ReadsPerGene.out.tab" or sid!=f"{cond}_{rep}":
            raise ValueError("STOP: source file/sample/condition identity mismatch")
        if name in parsed or sid in samples:raise ValueError("STOP: duplicate source sample")
        if len(row["file_sha256"])!=64 or not all(c in "0123456789abcdef" for c in row["file_sha256"]):
            raise ValueError("STOP: invalid source file digest")
        try:tot=int(row["total_counts"]);det=int(row["genes_detected"])
        except ValueError as exc:raise ValueError("STOP: invalid count census") from exc
        if tot<=0 or det<=0 or det>58395:raise ValueError("STOP: implausible source census")
        parsed[name]={"sample_id":sid,"condition":cond,"replicate":rep,
                      "sha256":row["file_sha256"],"total_counts":tot,
                      "genes_detected":det}
        samples.add(sid);cell_design.setdefault(cond,set()).add(rep)
    if len(parsed)!=N_EXPECTED or cell_design!={"NT":{"rep1","rep2","rep3"},
                                              "AB":{"rep1","rep2","rep3"},
                                              "AB_GNE":{"rep1","rep2","rep3"}}:
        raise ValueError("STOP: expected 3×3 biological design incomplete")
    return parsed
def validate_inputs(meta,counts_dir,archive_path,*,fake_archive_sha=None):
    if not counts_dir.is_dir():raise ValueError("STOP: counts directory missing")
    matches={p.name for p in counts_dir.glob("*ReadsPerGene.out.tab") if p.is_file()}
    if matches!=set(meta):raise ValueError("STOP: missing/extra nine count inputs")
    if not archive_path.is_file():raise ValueError("STOP: parent source archive missing")
    actual_archive_bytes=archive_path.stat().st_size
    actual_archive_sha=sha_bytes(archive_path.read_bytes())
    expected_archive_sha=ARCHIVE_SHA256 if fake_archive_sha is None else fake_archive_sha
    expected_archive_bytes=ARCHIVE_BYTES if fake_archive_sha is None else actual_archive_bytes
    if actual_archive_sha!=expected_archive_sha or actual_archive_bytes!=expected_archive_bytes:
        raise ValueError("STOP: parent archive source digest/bytes mismatch")
    outputs={};inputs={}
    for filename,row in sorted(meta.items()):
        path=counts_dir/filename
        raw=path.read_bytes()
        if sha_bytes(raw)!=row["sha256"]:raise ValueError("STOP: extracted input source changed: "+filename)
        inputs[filename]=raw
        outputs[filename]={"file_size_bytes":len(raw),"input_file_sha256":row["sha256"],
                           "sample_id":row["sample_id"],"condition":row["condition"],
                           "replicate":row["replicate"],"expected_total_counts":row["total_counts"],
                           "expected_detected_genes":row["genes_detected"]}
    # Compare raw archive MEMBER BYTES to already-verified extracted source bytes.
    seen=set()
    with tarfile.open(archive_path,"r:gz") as tar:
        for m in tar:
            if not m.isfile():continue
            name=os.path.basename(m.name)
            if name not in meta:continue
            if name in seen:raise ValueError("STOP: duplicated sample inside source archive")
            seen.add(name)
            fh=tar.extractfile(m)
            if fh is None or fh.read()!=inputs[name]:
                raise ValueError("STOP: archive member != authenticated extracted sample: "+name)
    if seen!=set(meta):raise ValueError("STOP: source archive lacks the nine authenticated inputs")
    return {"schema":"GSE254205_NINE_SAMPLE_SOURCE_PREFLIGHT_V1",
            "scope":"PHYSICAL_SOURCE_ONLY__NO_EFFECTS_OR_NEW_CONFIRMATION",
            "frozen_repo_metadata_git_blob_id":SOURCE_GIT_BLOB_ID,
            "source_archive_sha256":actual_archive_sha,"source_archive_bytes":actual_archive_bytes,
            "verified_samples":outputs,"nine_sources_physically_authenticated":True,
            "archive_member_bytes_equal_extracted_source_bytes":True,
            "assay_status_still_requires_PHYSICAL_V2":True,
            "no_differential_expression_values_inspected":True,
            "jepa_training_authorized":False}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--counts-dir",type=Path,required=True)
    ap.add_argument("--source-archive",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise SystemExit("STOP: refuse to overwrite previous physical receipt")
    source=(a.repo/SOURCE_INVENTORY).read_bytes()
    meta=parse_frozen_inventory(source)
    report=validate_inputs(meta,a.counts_dir,a.source_archive)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"nine_sources_physically_authenticated":report["nine_sources_physically_authenticated"],
        "archive_member_bytes_equal_extracted_source_bytes":True,"biological_effects_analyzed":False}))
if __name__=="__main__":main()
