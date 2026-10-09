import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/v64/estimate_v72_synthetic_twin_resources.py"


def load():
    spec = importlib.util.spec_from_file_location("v72_resource", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_resource_estimate_is_monotone_in_cells():
    m = load()
    a = m.estimate(10_000, 1000, 2000)
    b = m.estimate(100_000, 1000, 2000)
    assert b["estimated"]["sparse_matrix_bytes"] > a["estimated"]["sparse_matrix_bytes"]
    assert b["estimated"]["fragment_records"] == 10 * a["estimated"]["fragment_records"]
    assert b["estimated"]["working_set_bytes_planning"] > a["estimated"]["working_set_bytes_planning"]


def test_resource_estimate_forbids_dense_full_matrix():
    r = load().estimate(4553407, 41238, 150614)
    assert r["recommended"]["materialize_dense_full_matrix"] is False
    assert r["recommended"]["stream_fragments"] is True
    assert r["recommended"]["promotion_requires_measured_stress_receipt"] is True


def test_resource_estimate_is_explicitly_planning_only():
    r = load().estimate(100_000, 41238, 150614)
    assert r["scope"] == "PLANNING_ONLY__MEASURE_ON_STRESS_TWIN_BEFORE_FULL104_SCALE"


def test_resource_estimate_rejects_nonpositive_dimensions():
    m = load()
    for args in [(0,10,10),(10,0,10),(10,10,0)]:
        try:
            m.estimate(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(f"did not reject {args}")
