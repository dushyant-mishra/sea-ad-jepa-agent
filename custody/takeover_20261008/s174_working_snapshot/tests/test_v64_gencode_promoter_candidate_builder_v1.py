from __future__ import annotations
import gzip
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/build_gencode_promoter_candidates_v1.py"
    spec=importlib.util.spec_from_file_location("v64_gencode_promoters",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fixture(tmp_path:Path):
    p=tmp_path/"tiny.gtf.gz"
    lines=[
      'chr1\tHAVANA\ttranscript\t101\t200\t.\t+\t.\tgene_id "ENSG1.2"; transcript_id "ENST1.1"; gene_type "protein_coding"; gene_name "G1"; transcript_type "protein_coding";',
      'chr1\tHAVANA\ttranscript\t101\t250\t.\t+\t.\tgene_id "ENSG1.2"; transcript_id "ENST2.1"; gene_type "protein_coding"; gene_name "G1"; transcript_type "protein_coding";',
      'chr2\tHAVANA\ttranscript\t300\t450\t.\t-\t.\tgene_id "ENSG2.7"; transcript_id "ENST3.4"; gene_type "lncRNA"; gene_name "G2"; transcript_type "lncRNA";',
    ]
    with gzip.open(p,"wt") as f:
        f.write("\n".join(lines)+"\n")
    return p


def test_plus_and_minus_tss_coordinates_and_same_tss_collapse(tmp_path):
    m=_load()
    rows,c=m.build(_fixture(tmp_path))
    assert c["transcript_features"]==3
    assert c["candidate_gene_tss"]==2
    by_gene={r["gene_id"]:r for r in rows}
    a=by_gene["ENSG1.2"]
    assert a["tss_1based"]==101 and a["tss_0based"]==100
    assert a["n_transcripts_at_tss"]==2
    b=by_gene["ENSG2.7"]
    assert b["tss_1based"]==450 and b["tss_0based"]==449


def test_versioned_and_base_ids_are_both_preserved(tmp_path):
    m=_load()
    rows,_=m.build(_fixture(tmp_path))
    a={r["gene_id"]:r for r in rows}["ENSG1.2"]
    assert a["gene_id"]=="ENSG1.2"
    assert a["gene_id_base"]=="ENSG1"
    assert a["transcript_ids"]==["ENST1.1","ENST2.1"]
    assert a["transcript_id_bases"]==["ENST1","ENST2"]


def test_candidate_id_is_deterministic_and_coordinate_specific():
    m=_load()
    a=m.stable_candidate_id("ENSG1.2","chr1","+",100)
    b=m.stable_candidate_id("ENSG1.2","chr1","+",100)
    c=m.stable_candidate_id("ENSG1.2","chr1","+",101)
    assert a==b and a!=c


def test_no_activity_gate_or_promoter_width_is_introduced(tmp_path):
    m=_load()
    _,c=m.build(_fixture(tmp_path))
    assert c["annotation_only"] is True
    assert c["activity_gating_used"] is False
    assert c["promoter_interval_width_defined"] is False
