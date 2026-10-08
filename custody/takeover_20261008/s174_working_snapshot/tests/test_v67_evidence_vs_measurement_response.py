import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/evidence_vs_measurement_response_synthetic_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("v67_resp",P)
    assert s and s.loader
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_evidence_and_measurement_response_smoke_passes():
    o=mod().run_smoke()
    assert o["pass"]
    assert o["evidence_response"]["relative_error_reduction"]>0.25
    assert o["measurement_response"]["relative_error_reduction"]>0.10
    assert o["governance"]["real_data_used"] is False
    assert o["governance"]["training"]=="OFF"

def test_evidence_fraction_means_distinct_features_not_relabelled_same_subset():
    o=mod().run_smoke(evidence_override_same_subset=True)
    assert o["pass"] is False
    assert o["gates"]["evidence_curve_converges_as_distinct_features_are_added"] is False

def test_measurement_depth_means_noise_change_not_relabelled_same_measurement():
    o=mod().run_smoke(depth_override_fixed_noise=True)
    assert o["pass"] is False
    assert o["gates"]["measurement_curve_converges_as_noise_falls_at_fixed_features"] is False

def test_axes_are_separated_by_construction():
    o=mod().run_smoke()
    counts=[x["n_features"] for x in o["evidence_response"]["curve"]]
    assert len(set(counts))>1
    assert all(x["n_features"]==mod().P for x in o["measurement_response"]["curve"])
