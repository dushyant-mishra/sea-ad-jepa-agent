"""The rebuild's join follows identifiers, never positions; collisions are excluded and recorded,
never summed; unmapped columns are counted; and the library is every count in the physical row."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("s174_rebuild", ROOT / "scripts" / "v77" / "rebuild_s174_train_cache.py")
R = importlib.util.module_from_spec(spec)
sys.modules["s174_rebuild"] = R
spec.loader.exec_module(R)

GENES = [f"G{i:02d}" for i in range(12)]
ID2ADDR = {g: 100 + i for i, g in enumerate(GENES)}                 # identity decision, by gene
VAR = [GENES[i] for i in np.random.default_rng(1).permutation(12)]  # physical (genomic) order


def test_join_follows_identifiers_not_positions():
    col2addr, excluded = R.id_join_map(VAR, ID2ADDR, set())
    assert not excluded
    assert all(col2addr[j] == ID2ADDR[VAR[j]] for j in range(12))
    positional = {j: 100 + j for j in range(12)}
    assert sum(col2addr[j] != positional[j] for j in range(12)) > 6, "the fixture must scramble most columns"


def test_ledger_collisions_are_excluded_never_summed_and_recorded():
    victim = VAR[3]
    col2addr, excluded = R.id_join_map(VAR, ID2ADDR, {victim})
    assert excluded == {3: "LEDGER_COLLISION"} and 3 not in col2addr
    row, total = R.build_row([3, 4], [7, 2], col2addr)
    assert row == {ID2ADDR[VAR[4]]: 2} and total == 9, "the excluded count leaves the row but stays in the library"
    assert R.collision_addresses(VAR, ID2ADDR, excluded) == {ID2ADDR[victim]}


def test_two_columns_reaching_one_address_are_both_excluded():
    var = list(VAR) + [VAR[0]]                                      # a duplicated identifier
    col2addr, excluded = R.id_join_map(var, ID2ADDR, set())
    assert excluded == {0: "JOIN_COLLISION", 12: "JOIN_COLLISION"}
    assert R.collision_addresses(var, ID2ADDR, excluded) == {ID2ADDR[VAR[0]]}


def test_unmapped_columns_are_counted_not_guessed():
    col2addr, excluded = R.id_join_map(list(VAR) + ["NOT_IN_PROVENANCE"], ID2ADDR, set())
    assert excluded == {12: "UNMAPPED"} and len(col2addr) == 12


def test_library_is_every_count_and_negative_counts_are_refused():
    col2addr, _ = R.id_join_map(VAR, ID2ADDR, set())
    row, total = R.build_row([0, 1, 2], [1.0, 0.0, 4.0], col2addr)
    assert total == 5 and len(row) == 2, "zeros are not stored"
    with pytest.raises(ValueError):
        R.build_row([0], [-1], col2addr)
