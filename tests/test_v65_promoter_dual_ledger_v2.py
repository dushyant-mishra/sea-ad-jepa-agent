from __future__ import annotations
import gzip, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _load():
    p=ROOT/"scripts/v64/build_promoter_dual_ledger_v2.py"
    spec=importlib.util.spec_from_file_location("dual",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_dual_ledger_preserves_transcripts_and_collapses_only_exact_tss(tmp_path):
    m=_load()
    g=tmp_path/"g.gtf.gz"
    with gzip.open(g,"wt") as f:
        f.write('chr1\tx\ttranscript\t101\t200\t.\t+\t.\tgene_id "ENSG1.1"; transcript_id "ENST1.1"; gene_name "G1"; transcript_type "pc";\n')
        f.write('chr1\tx\ttranscript\t101\t300\t.\t+\t.\tgene_id "ENSG1.1"; transcript_id "ENST2.1"; gene_name "G1"; transcript_type "pc";\n')
        f.write('chr1\tx\ttranscript\t501\t700\t.\t+\t.\tgene_id "ENSG2.1"; transcript_id "ENST3.1"; gene_name "G2"; transcript_type "pc";\n')
    s=tmp_path/"pls.bed"
    s.write_text("chr1\t100\t101\tPLS1\n")
    class A: pass
    a=A()
    a.gencode_gtf=g; a.screen_pls=s; a.dong_data7=None; a.fantom_bed=None
    a.transcript_output=tmp_path/"transcript.tsv.gz"
    a.tss_output=tmp_path/"tss.tsv.gz"
    a.membership_output=tmp_path/"membership.tsv.gz"
    a.receipt=tmp_path/"receipt.json"
    r=m.build(a)
    assert r["transcript_promoter_records"]==3
    assert r["exact_tss_loci"]==2
    with gzip.open(a.transcript_output,"rt") as f:
        tx=f.readlines()
    with gzip.open(a.tss_output,"rt") as f:
        tss=f.readlines()
    with gzip.open(a.membership_output,"rt") as f:
        mem=f.readlines()
    assert len(tx)==4 and len(tss)==3 and len(mem)==4
    assert sum("GENCODE50:TSS:ENSG1:chr1:101:+" in x for x in mem)==2

def test_evidence_absence_does_not_prune_candidate(tmp_path):
    m=_load()
    g=tmp_path/"g.gtf.gz"
    with gzip.open(g,"wt") as f:
        f.write('chr2\tx\ttranscript\t1001\t1200\t.\t+\t.\tgene_id "ENSG9"; transcript_id "ENST9"; gene_name "G9"; transcript_type "pc";\n')
    s=tmp_path/"pls.bed"; s.write_text("chr1\t1\t10\tX\n")
    class A: pass
    a=A(); a.gencode_gtf=g; a.screen_pls=s; a.dong_data7=None; a.fantom_bed=None
    a.transcript_output=tmp_path/"t.tsv.gz"; a.tss_output=tmp_path/"x.tsv.gz"
    a.membership_output=tmp_path/"m.tsv.gz"; a.receipt=tmp_path/"r.json"
    r=m.build(a)
    assert r["transcript_promoter_records"]==1
    assert r["exact_tss_loci"]==1
    with gzip.open(a.transcript_output,"rt") as f:
        body=f.read()
    assert "\t0\t0\t" in body


def test_fantom_evidence_is_strand_aware(tmp_path):
    m=_load()
    g=tmp_path/"g.gtf.gz"
    with gzip.open(g,"wt") as f:
        f.write('chr1\tx\ttranscript\t101\t200\t.\t+\t.\tgene_id "ENSG1"; transcript_id "ENST1"; gene_name "G1"; transcript_type "pc";\n')
    screen=tmp_path/"pls.bed"; screen.write_text("chr9\t1\t2\tX\n")
    fantom=tmp_path/"fantom.bed"
    # Same coordinate, opposite strand only: must NOT annotate the + GENCODE TSS.
    fantom.write_text("chr1\t100\t110\tCAGE\t0\t-\t100\t101\t0\n")
    class A: pass
    a=A(); a.gencode_gtf=g; a.screen_pls=screen; a.dong_data7=None; a.fantom_bed=fantom
    a.transcript_output=tmp_path/"t.tsv.gz"; a.tss_output=tmp_path/"x.tsv.gz"
    a.membership_output=tmp_path/"m.tsv.gz"; a.receipt=tmp_path/"r.json"
    m.build(a)
    with gzip.open(a.transcript_output,"rt") as f:
        rows=list(__import__("csv").DictReader(f,delimiter="\t"))
    assert rows[0]["fantom_cage_overlap"]=="0"
    assert rows[0]["fantom_cage_count"]=="0"
