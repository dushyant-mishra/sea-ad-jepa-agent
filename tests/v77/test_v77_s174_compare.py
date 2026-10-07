"""The side-by-side receipt keeps every old number beside its corrected one, pairs them by path,
skips provenance blocks, and never drops a number that exists on only one side."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("s174_compare", ROOT / "scripts" / "v77" / "compare_s174_rebuild.py")
C = importlib.util.module_from_spec(spec)
sys.modules["s174_compare"] = C
spec.loader.exec_module(C)


def test_pairs_by_path_with_deltas_and_skips_provenance():
    old = {"A": {"frac": 0.6, "deg": 10}, "ok": True, "source": {"shard_digests": [1, 2]}, "command": "x"}
    new = {"A": {"frac": 0.4, "deg": 10}, "ok": False, "source": {"shard_digests": [3]}, "command": "y"}
    rows = {r["path"]: r for r in C.pair(old, new)}
    assert set(rows) == {"A.frac", "A.deg", "ok"}
    assert abs(rows["A.frac"]["delta"] + 0.2) < 1e-12 and rows["A.deg"]["delta"] == 0
    assert rows["ok"]["old"] is True and rows["ok"]["corrected"] is False and "delta" not in rows["ok"]


def test_a_number_on_one_side_only_is_kept_not_dropped():
    rows = {r["path"]: r for r in C.pair({"S": {"HVS": 1.0}}, {"S": {"HVS": 2.0, "NPH52": 3.0}})}
    assert rows["S.NPH52"]["old"] is None and rows["S.NPH52"]["corrected"] == 3.0
