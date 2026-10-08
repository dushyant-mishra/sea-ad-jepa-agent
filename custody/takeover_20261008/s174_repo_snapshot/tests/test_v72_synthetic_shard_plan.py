import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/plan_v72_synthetic_shards.py"

def load():
    s=importlib.util.spec_from_file_location("v72_shards",SCRIPT)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def test_shard_plan_exactly_covers_full104_scale():
    m=load()
    p=m.plan(4_553_407,100_000,7202)
    assert m.validate(p)==[]
    assert p["shards"][0]["cell_start_inclusive"]==0
    assert p["shards"][-1]["cell_end_exclusive"]==4_553_407
    assert sum(s["n_cells"] for s in p["shards"])==4_553_407
    assert p["n_shards"]==46

def test_shard_plan_is_deterministic():
    m=load()
    a=m.plan(300_123,100_000,7202)
    b=m.plan(300_123,100_000,7202)
    assert a["ordered_plan_sha256"]==b["ordered_plan_sha256"]
    assert [s["seed"] for s in a["shards"]]==[s["seed"] for s in b["shards"]]

def test_shard_seeds_are_distinct():
    p=load().plan(1_000_000,100_000,7202)
    seeds=[s["seed"] for s in p["shards"]]
    assert len(seeds)==len(set(seeds))

def test_validate_detects_gap():
    m=load()
    p=m.plan(250_000,100_000,7202)
    p["shards"][1]["cell_start_inclusive"]+=1
    assert any(x.startswith("GAP_OR_OVERLAP_BEFORE") for x in m.validate(p))
