from __future__ import annotations
import gzip, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _load():
    p=ROOT/"scripts/v64/build_promoter_candidate_ledger_v1.py"
    spec=importlib.util.spec_from_file_location("ledger",p); assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_gencode_candidate_not_removed_when_no_evidence(tmp_path):
    m=_load()
    g=tmp_path/"a.gtf.gz"
    with gzip.open(g,"wt") as f:
        f.write('chr1\tx\ttranscript\t101\t200\t.\t+\t.\tgene_id "ENSG1.1"; transcript_id "ENST1.2"; gene_name "G"; transcript_type "protein_coding";\n')
    s=tmp_path/"pls.bed"; s.write_text("chr1\t300\t400\tP1\n")
    out=tmp_path/"ledger.tsv.gz"; rec=tmp_path/"r.json"
    class A: pass
    a=A(); a.gencode_gtf=g; a.screen_pls=s; a.dong_data7=None; a.fantom_bed=None; a.output=out; a.receipt=rec
    r=m.build(a)
    assert r["candidates"]==1 and r["screen_pls_overlap"]==0
    with gzip.open(out,"rt") as f:
        rows=f.readlines()
    assert len(rows)==2
    assert "GENCODE50:ENST1:chr1:101:+" in rows[1]

def test_point_overlap_uses_bed_zero_based_half_open(tmp_path):
    m=_load()
    p=tmp_path/"a.bed"; p.write_text("chr1\t100\t101\tX\n")
    idx,starts=m.load_bed_index(p)
    assert len(m.point_hits(idx,starts,"chr1",101))==1
    assert len(m.point_hits(idx,starts,"chr1",100))==0
