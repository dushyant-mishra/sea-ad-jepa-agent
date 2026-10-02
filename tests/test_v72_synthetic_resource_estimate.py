import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_v72_coupled_multidataset_synthetic_fixture.py"
EST = ROOT / "scripts/v64/measure_v72_synthetic_resource_estimate.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    root = tmp_path / "challenge"
    load(BUILDER, "v72_resource_builder").build(root)
    return root


def test_resource_receipt_is_measured_but_full_projection_is_not_qualification(tmp_path, monkeypatch):
    # Make sibling-script import resolvable the same way direct execution does.
    import sys
    monkeypatch.syspath_prepend(str(ROOT / "scripts/v64"))
    est = load(EST, "v72_resource_est")
    receipt = est.make_receipt(fixture(tmp_path))
    assert receipt["status"] == "MEASURED_SMALL_CI_BYTES__PROJECTIONS_ARE_PLANNING_ONLY"
    assert receipt["measured"]["observable_bytes"] > 0
    assert receipt["measured"]["bytes_by_family"]["FULL104_LIKE"] > 0
    full = receipt["projections"]["FULL104_SCALE"]
    assert full["cells"] == 4553407
    assert full["status"] == "PLANNING_ESTIMATE_ONLY"
    assert receipt["promotion"]["FULL104_SCALE"].startswith("forbidden")


def test_projection_increases_with_scale(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/v64"))
    est = load(EST, "v72_resource_est2")
    p = est.make_receipt(fixture(tmp_path))["projections"]
    assert p["SMALL_CI_10K"]["FULL104_like_linear_projection_bytes"] < p["MEDIUM_STRESS_100K"]["FULL104_like_linear_projection_bytes"]
    assert p["MEDIUM_STRESS_100K"]["FULL104_like_linear_projection_bytes"] < p["MEDIUM_STRESS_500K"]["FULL104_like_linear_projection_bytes"]
    assert p["MEDIUM_STRESS_500K"]["FULL104_like_linear_projection_bytes"] < p["FULL104_SCALE"]["FULL104_like_linear_projection_bytes"]
