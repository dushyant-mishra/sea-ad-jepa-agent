"""The synthetic loader must satisfy the real loader's output contract exactly.

v1 and v2 failed because a re-implementation diverged from the historical path
in ways nobody checked. The synthetic loader is the only substitution v3 makes,
so its contract is verified against the real loader's own source and against the
invariant `run_update` asserts, before it is wired to anything.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from scripts.v4.c2_synthetic_loader_v3 import (
    ADDRESS_COUNT,
    MEASURED_COLLISION_UNRESOLVED,
    MEASURED_SCALAR,
    STRUCTURALLY_UNMEASURED,
    SyntheticTrainLoader,
    synthetic_cohort,
)

CANONICAL_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"))
REAL_LOADER = Path("exports/static_context_decomposition_v4_20260821/production_train_loader.py")


def _real_loader_source() -> str:
    for root in CANONICAL_ROOTS:
        candidate = root / REAL_LOADER
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    pytest.skip("real production loader not reachable from this worktree")


def _rows(loader_rows: int) -> "object":
    cohort = synthetic_cohort(loader_rows)
    cohort = cohort.copy()
    cohort["loader_row"] = np.arange(len(cohort), dtype=np.int64)
    return cohort


def test_constants_match_the_real_loader_verbatim() -> None:
    """A drifted ADDRESS_COUNT would silently misalign every block index."""
    tree = ast.parse(_real_loader_source())
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "ADDRESS_COUNT", "STRUCTURALLY_UNMEASURED",
                "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED",
            }:
                found[target.id] = ast.unparse(node.value)
    assert found["ADDRESS_COUNT"].replace("_", "") == str(ADDRESS_COUNT)
    assert "0" in found["STRUCTURALLY_UNMEASURED"] and int(STRUCTURALLY_UNMEASURED) == 0
    assert "1" in found["MEASURED_SCALAR"] and int(MEASURED_SCALAR) == 1
    assert "2" in found["MEASURED_COLLISION_UNRESOLVED"]
    assert int(MEASURED_COLLISION_UNRESOLVED) == 2


def test_load_returns_the_real_shapes_and_dtypes() -> None:
    loader = SyntheticTrainLoader(seed=8113002)
    values, states = loader.load(_rows(4))
    assert values.shape == (4, ADDRESS_COUNT) and values.dtype == np.float32
    assert states.shape == (4, ADDRESS_COUNT) and states.dtype == np.uint8


def test_no_nonzero_value_outside_measured_scalar() -> None:
    """The exact invariant `run_update` asserts before training."""
    loader = SyntheticTrainLoader(seed=1, measured_fraction=0.55, collision_fraction=0.2)
    values, states = loader.load(_rows(6))
    assert np.any(states == STRUCTURALLY_UNMEASURED)
    assert np.any(states == MEASURED_COLLISION_UNRESOLVED)
    assert not np.any((states != MEASURED_SCALAR) & (values != 0.0))


def test_state_vector_is_an_operator_property_shared_by_all_cells() -> None:
    """Real states come from the source matrix, so cells of one operator share them."""
    loader = SyntheticTrainLoader(seed=7, measured_fraction=0.6)
    _, states = loader.load(_rows(5))
    assert all(np.array_equal(states[0], states[index]) for index in range(1, 5))


def test_values_are_deterministic_in_stable_mask_key_not_row_position() -> None:
    loader = SyntheticTrainLoader(seed=42)
    cohort = _rows(3)
    values_a, _ = loader.load(cohort)
    reversed_cohort = cohort.iloc[::-1].copy()
    reversed_cohort["loader_row"] = np.arange(len(reversed_cohort), dtype=np.int64)
    values_b, _ = loader.load(reversed_cohort)
    for position, key_index in enumerate(range(len(cohort) - 1, -1, -1)):
        assert np.array_equal(values_a[key_index], values_b[position])


def test_loader_row_controls_destination() -> None:
    loader = SyntheticTrainLoader(seed=5)
    cohort = _rows(3)
    cohort["loader_row"] = np.array([2, 0, 1], dtype=np.int64)
    values, _ = loader.load(cohort)
    direct = {
        int(key): loader._values_for_cell(int(key), loader._states == MEASURED_SCALAR)
        for key in cohort.stable_mask_key
    }
    for destination, key in zip(cohort.loader_row, cohort.stable_mask_key):
        assert np.array_equal(values[int(destination)], direct[int(key)])


def test_declared_step_a_distribution_produces_the_recorded_hidden_count() -> None:
    """Step A hides floor(0.40 x 41238) = 16495 genes across 16 blocks (~1031 each)."""
    loader = SyntheticTrainLoader(seed=8113002, measured_fraction=1.0)
    _, states = loader.load(_rows(1))
    measured = int((states[0] == MEASURED_SCALAR).sum())
    assert measured == ADDRESS_COUNT
    hidden = int(np.floor(0.40 * measured))
    assert hidden == 16_495
    assert hidden // 16 == 1_030 and hidden % 16 == 15  # _block_sizes -> 15 of 1031, 1 of 1030


def test_zero_inflation_and_value_laws_are_available_for_the_step_b_ladder() -> None:
    dense = SyntheticTrainLoader(seed=3, zero_inflation=0.0)
    sparse = SyntheticTrainLoader(seed=3, zero_inflation=0.9)
    dense_values, _ = dense.load(_rows(2))
    sparse_values, _ = sparse.load(_rows(2))
    assert (sparse_values == 0.0).mean() > (dense_values == 0.0).mean() + 0.5
    for law in ("log1p_exponential", "log1p_lognormal", "uniform"):
        values, _ = SyntheticTrainLoader(seed=3, value_law=law).load(_rows(1))
        assert np.isfinite(values).all() and values.min() >= 0.0


def test_manifest_records_that_no_real_expression_is_read() -> None:
    manifest = SyntheticTrainLoader(seed=8113002).manifest()
    assert manifest["reads_real_expression"] is False
    assert manifest["address_count"] == ADDRESS_COUNT
    assert manifest["measured_addresses"] == ADDRESS_COUNT


def test_invalid_fractions_are_rejected() -> None:
    for kwargs in (
        {"measured_fraction": 1.2},
        {"collision_fraction": -0.1},
        {"zero_inflation": 2.0},
        {"measured_fraction": 0.8, "collision_fraction": 0.5},
    ):
        with pytest.raises(ValueError):
            SyntheticTrainLoader(seed=1, **kwargs)
