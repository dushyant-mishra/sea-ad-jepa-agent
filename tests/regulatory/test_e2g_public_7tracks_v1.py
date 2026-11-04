"""Hostile offline tests for strictly descriptive E2G track survey."""
import gzip
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("e2g7",ROOT/"scripts/regulatory/survey_e2g_public_7tracks_v1.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
TARGETS={"APOE","TREM2"}

def row(name, score="0.60", ench="chr19", tchr="chr19", start="100", end="500", tss="25000"):
    return "\t".join([ench,start,end,tchr,tss,tss,name,score,".","."])+"\n"

def test_frozen_stage75_identity():
    genes=m.authenticated_stage75(ROOT/"results/v4/stage81a1b_existing_regulatory_evidence_integration.csv")
    assert len(genes)==27 and {"APOE","TREM2"}.issubset(genes)

def test_source_name_and_canonical_uncertainty():
    assert m.gene_from_name("APOE|chr19:100-500",TARGETS)=="APOE"
    assert m.gene_from_name("APOE_promoter|chr19:100-500",TARGETS)=="APOE"
    assert m.gene_from_name("APOE_genic|chr19:100-500",TARGETS)=="APOE"
    assert m.gene_from_name("APOE2_promoter|chr19:100-500",TARGETS) is None
    assert m.gene_from_name("APOE_pseudogene|chr19:100-500",TARGETS) is None

def test_schema_counts_and_provisional_result():
    data=(row("APOE_promoter|chr19:100-500")+
          row("APOE_intergenic|chr19:900-1000",score="0.1",start="900",end="1000",tss="100000")+
          row("TREM2|chr19:1200-1500",score="0.4",start="1200",end="1500",tss="1300")+
          row("OTHER|chr19:1200-1500")).encode()
    report=m.parse_track(gzip.compress(data),True,TARGETS)
    assert report["file_total_predictions"]==4
    assert report["matched_prediction_rows"]==3
    assert report["per_gene"]["APOE"]["prediction_count"]==2
    assert report["per_gene"]["APOE"]["distal_at_least_20kb_count"]==2
    assert report["per_gene"]["TREM2"]["prediction_count"]==1
    assert report["per_gene"]["APOE"]["symbol_status"]=="PROVISIONAL_SYMBOL_MATCH"

def test_no_predictions_not_negative():
    d=m.parse_track(row("OTHER").encode(),False,TARGETS)
    assert d["per_gene"]["APOE"]["symbol_status"]=="NO_ROW_IN_THRESHOLD_FILE__NOT_BIOLOGICAL_NEGATIVE"
    assert d["per_gene"]["APOE"]["max_score_within_source"] is None

@pytest.mark.parametrize("data",[
    row("APOE",score="nan"),
    row("APOE",score="1.2"),
    row("APOE",ench="chr1",tchr="chr2"),
    row("APOE",start="-1"),
    row("APOE").replace("\t.\t.\n","\t.\n"),
])
def test_malformed_track_fails_closed(data):
    with pytest.raises(m.EvidenceError):
        m.parse_track(data.encode(),False,TARGETS)

def test_must_not_visit_unapproved_url():
    assert m.public_url("https://storage.googleapis.com/real/path")
    for bad in ("https://evil.example/file","https://storage.googleapis.com/path?bill=token",
                "http://storage.googleapis.com/path","https://127.0.0.1/private"):
        assert not m.public_url(bad)
