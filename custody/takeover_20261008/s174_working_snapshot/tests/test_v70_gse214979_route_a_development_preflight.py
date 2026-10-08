import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"results/v64/V70_GSE214979_ROUTE_A_DEVELOPMENT_PREFLIGHT_V1.json"

def load(): return json.loads(P.read_text())

def test_population_reconciles():
    x=load()["population"]
    assert x["cells"]==2534
    assert x["donors"]==12
    assert sum(x["donor_cell_counts"].values())==2534
    assert min(x["donor_cell_counts"].values())==17
    assert max(x["donor_cell_counts"].values())==415

def test_low_n_donors_remain_explicit():
    d=load()["population"]["donor_cell_counts"]
    assert d["4313"]==17
    assert d["HCTZZT"]==26

def test_feature_detection_counts_are_bounded():
    f=load()["feature_observation"]
    g=f["genes"]; p=f["peaks"]
    assert 0 <= g["detected_in_all_12_donors"] <= g["detected_in_at_least_9_donors"] <= g["detected_in_at_least_6_donors"] <= g["detected_in_at_least_3_donors"] <= g["detected_in_at_least_1_cell"] <= g["submitted"]
    assert 0 <= p["detected_in_all_12_donors"] <= p["detected_in_at_least_9_donors"] <= p["detected_in_at_least_6_donors"] <= p["detected_in_at_least_3_donors"] <= p["detected_in_at_least_1_cell"] <= p["submitted"]

def test_exact_observed_counts_frozen():
    f=load()["feature_observation"]
    assert f["genes"]["detected_in_at_least_1_cell"]==25630
    assert f["genes"]["detected_in_at_least_1pct_cells"]==12848
    assert f["genes"]["detected_in_all_12_donors"]==6877
    assert f["peaks"]["detected_in_at_least_1_cell"]==149590
    assert f["peaks"]["detected_in_at_least_1pct_cells"]==43450
    assert f["peaks"]["detected_in_all_12_donors"]==12319

def test_preflight_does_not_invent_network_threshold():
    x=load()
    assert "No minimum donor-cell threshold is invented" in x["population"]["note"]
    assert any("does not choose TFs" in s for s in x["implications"])

def test_governance_unchanged():
    g=load()["governance"]
    assert g["stage4"]=="NOT_AUTHORIZED"
    assert g["correspondence"]=="UNOPENED"
    assert g["Morabito"]=="PROTECTED"
    assert g["recoverability_TEST"]=="SEALED"
