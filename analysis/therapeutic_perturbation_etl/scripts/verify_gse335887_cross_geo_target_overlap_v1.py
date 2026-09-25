#!/usr/bin/env python3
"""Exact-label guide-library overlaps against source-verified 31-target microglia set.

Only committed guide identity and guide-by-donor *metadata* are read.
No gene-expression effects, protected outcome table, donor inference or gene alias guessing.
"""
import argparse,csv,hashlib,io,json
from pathlib import Path
ROOT=Path("analysis/therapeutic_perturbation_etl")
REFERENCE_TARGETS=tuple(sorted("ARID2 ARID5B ATMIN BHLHE40 BHLHE41 BPTF CEBPD CNOT10 DEAF1 DNMT1 FOXK1 IRF9 MAF MEF2C MEF2D MITF POU5F1 PRDM1 RELA RUNX1 SALL4 SMAD3 SPI1 SREBF1 STAT1 STAT2 TCF4 ZNF148 ZNF532 ZNF644 ZNF783".split()))
REFERENCE_SET_SHA="105105c043ef67f6d393d7d2538bfd5f82871de6c6f6a9ca46171593142ad260"
SOURCES={
 "GSE178317":("reference/GSE178317_sgrna_library_suppl_table5.csv","e9f40526f64df31b56d95657657ab068094ac3a0"),
 "GSE293118":("evidence/gse293118/GSE293118_perturbation_identity.csv","7cd6be560f211e0e053e98e8e834500232a185a8"),
 "GSE311359":("evidence/gse311359/GSE311359_perturbation_identity.csv","ce7bf6de8e5523bc7c3fdef5021f35b7f55ceff0"),
 "GSE301119_CRISPRi":("evidence/gse301119/CRISPRi_guide_donor_meta.csv","890dcd42b8b3000d4e0d9da7921d7fddb3b50b32"),
 "GSE301119_CRISPRa":("evidence/gse301119/CRISPRa_guide_donor_meta.csv","bfff54bc7e0a89d47320465ed1d764e03724db1a")}
def members_root(names):
    return hashlib.sha256(("\n".join(sorted(names))+"\n").encode()).hexdigest()
def git_blob_digest(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def parse_metadata(source,label,blob):
    if git_blob_digest(source)!=blob:raise ValueError("STOP: committed source blob changed: "+label)
    txt=source.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(txt,newline=""))
    if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):raise ValueError("STOP: missing/duplicate headers")
    rows=[]
    for r in reader:
        if any(v is None for v in r.values()) or None in r:raise ValueError("STOP: malformed row")
        rows.append(r)
    if not rows:raise ValueError("STOP: empty metadata")
    return rows
def derive(loaded):
    if members_root(REFERENCE_TARGETS)!=REFERENCE_SET_SHA or len(REFERENCE_TARGETS)!=31:
        raise ValueError("STOP: verified HGNC-linked 31-target set mutated")
    t=set(REFERENCE_TARGETS)
    day8={r["target_gene"] for r in loaded["GSE178317"] if r["target_gene"]!="NTC"}
    direct_hmc3={r["target_id"] for r in loaded["GSE293118"] if r["target_class"]=="gene"}
    nominated_ms={r["nominated_gene"] for r in loaded["GSE311359"] if r["nominated_gene"]}
    out={}
    for key,s,scope in [
        ("GSE178317",day8,"DIRECT_CRISPRI_TARGET"),
        ("GSE293118",direct_hmc3,"DIRECT_GENE_CRISPRI_ONLY"),
        ("GSE311359",nominated_ms,"NOMINATED_GENE_ONLY_NOT_EQUAL_DIRECT_INTERVENTION"),
        ("GSE301119_CRISPRi",{r["Gene_Targeted"] for r in loaded["GSE301119_CRISPRi"] if r["crispr"]=="Perturbed"},"DIRECT_CRISPRI_TARGET_MACROPHAGE"),
        ("GSE301119_CRISPRa",{r["Gene_Targeted"] for r in loaded["GSE301119_CRISPRa"] if r["crispr"]=="Perturbed"},"DIRECT_CRISPRA_TARGET_MACROPHAGE")
    ]:
        if not s or any(not v for v in s):raise ValueError("STOP: missing source target identity "+key)
        hits=sorted(t&s)
        out[key]={"source_target_count":len(s),"shared_exact_labels":hits,"shared_exact_label_count":len(hits),
                  "comparison_scope":scope,"same_biological_intervention_proved":False}
    if len(day8)!=39 or len(direct_hmc3)!=6:raise ValueError("STOP: historic guide-target census changed")
    return out
def build(repo):
    sources,loaded={},{}
    for key,(rel,blob) in SOURCES.items():
        p=ROOT/rel;b=(repo/p).read_bytes()
        loaded[key]=parse_metadata(b,key,blob)
        sources[key]={"path":p.as_posix(),"git_blob_sha1":blob,"physical_sha256":hashlib.sha256(b).hexdigest(),"metadata_rows":len(loaded[key])}
    overlaps=derive(loaded)
    if overlaps["GSE178317"]["shared_exact_label_count"] or overlaps["GSE293118"]["shared_exact_label_count"]:
        raise ValueError("STOP: previously verified Day8/HMC3 set changed")
    if overlaps["GSE301119_CRISPRi"]["shared_exact_labels"]!=["SPI1"] or overlaps["GSE301119_CRISPRa"]["shared_exact_labels"]!=["SPI1"]:
        raise ValueError("STOP: expected macrophage overlap changed")
    if overlaps["GSE311359"]["shared_exact_labels"]!=["MAF"]:
        raise ValueError("STOP: expected nominated-gene overlap changed")
    return {"schema":"GSE335887_31_TARGET_CROSS_GEO_METADATA_OVERLAP_V1",
            "reference":"GSE335887_31_TARGETS__SAME_WTC11_PARENTAL_LINE",
            "reference_target_set_sha256":REFERENCE_SET_SHA,
            "sources":sources,"overlaps":overlaps,
            "note":"Identical gene names do not prove equivalent interventions, cell biology or functional response.",
            "numeric_outcomes_inspected":False,"full104_alignment_authorized":False,
            "prediction_authorized":False,"training_authorized":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit("STOP: refuse overwrite")
    obj=build(a.repo);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:x["shared_exact_labels"] for k,x in obj["overlaps"].items()}))
if __name__=="__main__":main()
