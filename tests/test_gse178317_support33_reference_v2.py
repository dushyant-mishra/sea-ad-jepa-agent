"""Adversarial fixtures for qualified reference comparison (never use protected outcomes)."""
import csv
import io
import pathlib
import sys
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] /
                       "analysis/therapeutic_perturbation_etl/scripts"))
from build_gse178317_support33_reference_v2 import compare, Stop

def fixture():
    out=io.StringIO()
    w=csv.writer(out)
    w.writerow(["target_gene","n_cells","n_lanes","engagement_log2fc",
                "engagement_sd_across_lanes","ref_log2fc","ref_fdr"])
    w.writerows([
        ["A",60,3,-1.0,"",-0.8,.001],
        ["B",60,3,-2.0,"",-0.4,.7],
        ["C",18,1,-3.0,"",-0.2,1.],
        ["D",60,3,-0.5,"",-0.6,.02]])
    support={}
    for target,good in [("A",True),("B",True),("C",False),("D",True)]:
        cells=dict(zip(("L1","L2","L3","L4"),(20,20,20,0) if good else (4,4,10,0)))
        support[target]={"assigned_cells":sum(cells.values()),"cells_by_lane":cells,
                         "paired_lanes":["L1","L2","L3"] if good else ["L3"],
                         "lane_support_sufficient":good}
    receipt={
        "schema":"GSE178317_GUIDE_ASSIGNMENT_V2","verdict":"PASS_LANE_SUPPORT_ONLY",
        "prospective_confirmation_eligible":False,"guide_identity_independently_verified":False,
        "ntc_cells":80,
        "verdict_basis":{
            "min_cells_per_usable_target":40,"min_paired_lanes":3,
            "min_target_and_ntc_cells_per_lane":10,"usable_targets":3,
            "ntc_cells_by_lane":dict.fromkeys(["L1","L2","L3","L4"],20),
            "ntc_supported_lanes":["L1","L2","L3","L4"],
            "target_lane_support":support}}
    return out.getvalue(),receipt

def run(text,receipt):
    return compare(text,receipt,expected=(4,3,3,4))

def test_support_derived_from_recomputed_census():
    text,receipt=fixture()
    qualified,out=run(text,receipt)
    assert [r["target_gene"] for r in qualified]==["A","B","D"]
    assert out["excluded_targets"]==["C"]
    assert out["direction_agree"]==3
    assert out["independent_validation"] is False

def test_unsupported_lane_cannot_claim_pass():
    text,receipt=fixture()
    s=receipt["verdict_basis"]["target_lane_support"]["A"]
    s["cells_by_lane"]["L2"]=0
    s["assigned_cells"]=40
    with pytest.raises(Stop):
        run(text,receipt)

def test_ntc_lane_mismatch_is_not_estimable():
    text,receipt=fixture()
    receipt["verdict_basis"]["ntc_cells_by_lane"]["L2"]=0
    receipt["ntc_cells"]=60
    receipt["verdict_basis"]["ntc_supported_lanes"].remove("L2")
    with pytest.raises(Stop):
        run(text,receipt)

def test_duplicate_join_rejected():
    text,receipt=fixture()
    lines=text.splitlines()
    lines[2]=lines[1]
    with pytest.raises(Stop):
        run(chr(10).join(lines)+chr(10),receipt)

def test_missing_target_not_silently_dropped():
    text,receipt=fixture()
    with pytest.raises(Stop):
        run(chr(10).join(text.splitlines()[:-1])+chr(10),receipt)

def test_historical_v1_pass_is_not_support_authority():
    text,_=fixture()
    with pytest.raises(Stop):
        run(text,{"schema":"GSE178317_CRISPRBRAIN_VALIDATION_V1","verdict":"PASS"})

def test_prospective_promotion_rejected():
    text,receipt=fixture()
    receipt["prospective_confirmation_eligible"]=True
    with pytest.raises(Stop):
        run(text,receipt)

@pytest.mark.parametrize("old,new",[
    (",-1.0,",",nan,"), (",0.7",",1.4"), (",-0.4,",",inf,")])
def test_invalid_numeric_data_rejected(old,new):
    text,receipt=fixture()
    with pytest.raises(Stop):
        run(text.replace(old,new),receipt)

def test_claimed_supported_total_must_match():
    text,receipt=fixture()
    receipt["verdict_basis"]["usable_targets"]=4
    with pytest.raises(Stop):
        run(text,receipt)
