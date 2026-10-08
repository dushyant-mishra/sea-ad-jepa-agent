import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/heldout_source_observation_operator_synthetic_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("v67_obs",P)
    assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_estimated_descriptor_leave_one_source_out_smoke_passes():
    o=mod().run_smoke()
    assert o["pass"]
    assert o["descriptor_source"]=="INDEPENDENT_TECHNICAL_CALIBRATION_CHANNEL"
    assert o["governance"]["real_data_used"] is False
    assert o["governance"]["training"]=="OFF"

def test_each_source_is_held_out_and_descriptor_is_estimated():
    o=mod().run_smoke()
    assert all(x["heldout_source_absent_from_train"] for x in o["per_source"])
    assert max(x["relative_estimation_error"] for x in o["per_source"])<0.10
    assert all(x["donor_overlap"]==0 for x in o["per_source"])
    assert o["structural_diagnostics"]["donor_disjointness_is_a_split_property_not_a_scientific_gate"]

def test_operator_calibration_improves_transfer():
    o=mod().run_smoke()
    assert o["means"]["operator_aware_shared_r2"]>o["means"]["raw_shared_r2"]+0.10
    assert all(x["operator_aware_shared_r2"]>0.95 for x in o["per_source"])

def test_wrong_heldout_descriptor_breaks_the_transfer_gate():
    o=mod().run_smoke(misspecify_heldout=1.35)
    assert o["pass"] is False
    assert o["gates"]["operator_aware_transfer_is_strong"] is False
