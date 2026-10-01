import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/heldout_source_observation_operator_synthetic_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("v67_obs",P)
    assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_heldout_source_observation_operator_smoke_passes():
    o=mod().run_smoke()
    assert o["pass"]
    assert o["governance"]["real_data_used"] is False
    assert o["governance"]["training"]=="OFF"

def test_each_source_and_donors_are_truly_held_out():
    o=mod().run_smoke()
    for x in o["per_source"]:
        assert x["heldout_source_absent_from_train"]
        assert x["donor_overlap"]==0

def test_operator_descriptor_improves_transfer_without_being_biology():
    o=mod().run_smoke()
    assert o["means"]["operator_aware_shared_r2"]>o["means"]["raw_shared_r2"]+0.10
    assert o["means"]["capture_only_shared_r2"]<0.03
    assert all(x["operator_aware_shared_r2"]>0.95 for x in o["per_source"])
