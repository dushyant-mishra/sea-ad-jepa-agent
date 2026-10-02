import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "scripts/v64/plan_v72_synthetic_scale.py"


def load():
    spec = importlib.util.spec_from_file_location("v72_scale", PLANNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_small_scale_plan_exactly_covers_cells():
    p = load().plan(10000, 12, 3000)
    assert p["source_count_sum"] == 10000
    assert sum(s["n_cells"] for s in p["shards"]) == 10000
    assert p["shards"][0]["start_global_index"] == 0
    assert p["shards"][-1]["stop_global_index_exclusive"] == 10000


def test_non_divisible_last_shard_is_preserved():
    p = load().plan(10001, 12, 3000)
    assert p["n_shards"] == 4
    assert p["shards"][-1]["n_cells"] == 1001
    assert sum(s["n_cells"] for s in p["shards"]) == 10001


def test_full104_source_allocation_reproduces_exact_counts():
    m = load()
    p = m.plan(m.FULL104_TOTAL, 104, 50000)
    assert p["source_counts"] == m.FULL104_COUNTS
    assert p["source_count_sum"] == 4553407


def test_global_registry_digest_is_deterministic():
    m = load()
    a = m.plan(2500, 10, 1000)
    b = m.plan(2500, 10, 1000)
    assert a["global_cell_registry_digest"] == b["global_cell_registry_digest"]
    assert [x["ordered_cell_digest"] for x in a["shards"]] == [
        x["ordered_cell_digest"] for x in b["shards"]
    ]


def test_bad_scale_arguments_fail():
    m = load()
    for args in [(0, 10, 100), (100, 0, 100), (100, 10, 0)]:
        try:
            m.plan(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {args}")
