import numpy as np
import pytest

from sea_ad_jepa.v5.technical_only_decoy_v1 import (
    apply_technical_only_decoy,
    build_technical_stratum_id,
    deterministic_stratified_derangement,
)


def test_decoy_is_deterministic_fixed_point_free_and_stratum_preserving() -> None:
    source = ["HVS"] * 4 + ["SEA"] * 4
    operator = ["o1", "o1", "o2", "o2"] * 2
    strata = build_technical_stratum_id(source, operator)
    keys = [f"r{i}" for i in range(8)]
    receipt = deterministic_stratified_derangement(keys, strata, salt="fixture")
    replay = deterministic_stratified_derangement(keys, strata, salt="fixture")
    assert np.array_equal(receipt.permutation, replay.permutation)
    assert np.all(receipt.permutation != np.arange(8))
    state = np.arange(16).reshape(8, 2)
    decoy = apply_technical_only_decoy(state, receipt, strata)
    for s in set(strata.tolist()):
        ix = np.flatnonzero(strata == s)
        assert sorted(map(tuple, state[ix])) == sorted(map(tuple, decoy[ix]))


def test_singleton_stratum_fails_closed_instead_of_leaking_identity() -> None:
    with pytest.raises(ValueError, match="<2 rows"):
        deterministic_stratified_derangement(["a", "b", "c"], ["x", "x", "y"])


def test_duplicate_row_keys_fail_closed() -> None:
    with pytest.raises(ValueError, match="unique"):
        deterministic_stratified_derangement(["a", "a"], ["x", "x"])


def test_fixture_breaks_row_specific_biology_while_preserving_technical_means_exactly() -> None:
    n_per = 12
    strata = np.array(["A"] * n_per + ["B"] * n_per, dtype=object)
    keys = [f"row-{i}" for i in range(2 * n_per)]
    technical = np.array([[10.0, 0.0]] * n_per + [[-10.0, 0.0]] * n_per)
    biology = np.column_stack([np.arange(2 * n_per), -np.arange(2 * n_per)]).astype(float)
    state = technical + biology
    receipt = deterministic_stratified_derangement(keys, strata, salt="biology-break")
    decoy = apply_technical_only_decoy(state, receipt, strata)
    assert not np.any(np.all(decoy == state, axis=1))
    for s in ("A", "B"):
        ix = np.flatnonzero(strata == s)
        assert np.allclose(decoy[ix].mean(axis=0), state[ix].mean(axis=0))


def test_decoy_never_requires_pathology_component() -> None:
    strata = build_technical_stratum_id(["source"] * 4, ["operator"] * 4, ["depth-bin"] * 4)
    receipt = deterministic_stratified_derangement([f"r{i}" for i in range(4)], strata)
    assert receipt.permutation.size == 4
