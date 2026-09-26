"""G3 independent scalar/ridge adversaries: synthetic only, never FULL104 outcomes."""
from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.g3_explicit_attacker_fit_objective_v1 import (
    OBJECTIVES, SCHEMA, donor_total_masses, fit_from_standardized_donor_components,
)


def planted():
    rng = np.random.default_rng(20260926)
    sizes = {0: 500, 1: 15, 2: 15, 3: 15}
    sources = {0: "BIG", 1: "SMALL", 2: "SMALL", 3: "SMALL"}
    inputs = {}
    for d, n in sizes.items():
        x = rng.normal(size=(n, 3))
        beta = np.array([-0.95, 0.0, 0.0] if d == 0 else [0.95, 0.0, 0.0])
        y = x @ beta + 0.2 * rng.normal(size=n)
        inputs[d] = (x, y)
    return sizes, sources, inputs


def standardized(inputs):
    stats = {}
    for d, (x, y) in inputs.items():
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        sx = np.std(x, axis=0)
        sx = np.where(sx > 1e-12, sx, 1.0)
        z = (x - x.mean(axis=0)) / sx
        yc = y - y.mean()
        stats[d] = (z.T @ z, z.T @ yc, float(yc @ yc))
    return stats


def ref_objective(sizes, sources, inputs, objective, alpha):
    """Raw row-level independent closed-form comparator; no production code reuse."""
    keys = sorted(sizes)
    if objective == "CURRENT_CELL_WEIGHTED":
        m = {d: sizes[d] / sum(sizes.values()) for d in keys}
    elif objective == "PRODUCTION_OBJECTIVE_MATCHED":
        m = {d: 1 / len(keys) for d in keys}
    else:
        source_set = set(sources.values())
        m = {d: 1 / (len(source_set) * sum(sources[j] == sources[d] for j in keys)) for d in keys}
    xx, yy, ww = [], [], []
    for d in keys:
        x, y = inputs[d]
        sd = np.std(x, axis=0)
        z = (x - x.mean(axis=0)) / np.where(sd > 1e-12, sd, 1.0)
        xx.append(z)
        yy.append(y - np.mean(y))
        ww.append(np.full(len(y), m[d] / sizes[d]))
    X, Y, W = np.concatenate(xx), np.concatenate(yy), np.concatenate(ww)
    scale = np.sqrt(np.dot(W, Y * Y))
    return np.linalg.solve(
        (X * W[:, None]).T @ X + alpha * W.sum() * np.eye(X.shape[1]),
        (X * W[:, None]).T @ Y / scale,
    )


@pytest.mark.parametrize("objective", OBJECTIVES)
def test_exact_masses_sum_to_one(objective):
    sizes, sources, _ = planted()
    m = donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=objective)
    assert abs(sum(m.values()) - 1) < 1e-14


def test_historical_cell_mass_is_not_donor_uniform():
    sizes, sources, _ = planted()
    cell = donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=OBJECTIVES[0])
    donor = donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=OBJECTIVES[1])
    source = donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=OBJECTIVES[2])
    assert cell[0] > 0.90
    assert all(abs(v - 0.25) < 1e-14 for v in donor.values())
    assert abs(source[0] - 0.5) < 1e-14
    assert all(abs(source[d] - 1 / 6) < 1e-14 for d in (1, 2, 3))


@pytest.mark.parametrize("objective", OBJECTIVES)
def test_weighted_sufficient_statistics_match_independent_row_level_reference(objective):
    sizes, sources, data = planted()
    got = fit_from_standardized_donor_components(
        components=standardized(data), donor_counts=sizes, source_by_donor=sources,
        objective=objective, alpha=0.01,
    )
    expected = ref_objective(sizes, sources, data, objective, alpha=0.01)
    assert np.allclose(got, expected, rtol=1e-11, atol=1e-11)


def test_conflicting_source_effects_change_fit_objective_without_changing_data():
    sizes, sources, data = planted()
    stats = standardized(data)
    fits = [fit_from_standardized_donor_components(
        components=stats, donor_counts=sizes, source_by_donor=sources,
        objective=obj, alpha=0.01,
    ) for obj in OBJECTIVES]
    assert fits[0][0] < -0.6
    assert fits[1][0] > 0.25
    assert abs(fits[2][0]) < 0.25
    assert fits[0][0] < fits[2][0] < fits[1][0]


def test_equal_donor_counts_recover_cell_equals_donor_uniform():
    rng = np.random.default_rng(2048)
    data = {k: (rng.normal(size=(50, 3)), rng.normal(size=50)) for k in range(4)}
    sizes = {k: 50 for k in data}
    src = {k: "A" if k < 2 else "B" for k in data}
    st = standardized(data)
    a = fit_from_standardized_donor_components(
        components=st, donor_counts=sizes, source_by_donor=src,
        objective="CURRENT_CELL_WEIGHTED", alpha=0.1,
    )
    b = fit_from_standardized_donor_components(
        components=st, donor_counts=sizes, source_by_donor=src,
        objective="PRODUCTION_OBJECTIVE_MATCHED", alpha=0.1,
    )
    assert np.array_equal(a, b)


def test_common_multiplier_on_donor_counts_changes_cell_mass_but_not_donor_mass():
    sizes, sources, _ = planted()
    altered = {**sizes, 0: sizes[0] * 2}
    m = donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=OBJECTIVES[1])
    n = donor_total_masses(donor_counts=altered, source_by_donor=sources, objective=OBJECTIVES[1])
    assert m == n
    cell_m = donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=OBJECTIVES[0])
    cell_n = donor_total_masses(donor_counts=altered, source_by_donor=sources, objective=OBJECTIVES[0])
    assert cell_n[0] > cell_m[0]


def test_reordered_donor_mapping_does_not_change_estimate():
    sizes, sources, data = planted()
    st = standardized(data)
    a = fit_from_standardized_donor_components(
        components=st, donor_counts=sizes, source_by_donor=sources,
        objective=OBJECTIVES[1], alpha=0.01,
    )
    b = fit_from_standardized_donor_components(
        components=dict(reversed(list(st.items()))),
        donor_counts=dict(reversed(list(sizes.items()))),
        source_by_donor=dict(reversed(list(sources.items()))),
        objective=OBJECTIVES[1], alpha=0.01,
    )
    assert np.array_equal(a, b)


def test_no_heldout_or_unexpected_donor_sufficient_statistics():
    sizes, sources, data = planted()
    st = standardized(data)
    st[999] = st[0]
    with pytest.raises(ValueError, match="missing/extra or held-out"):
        fit_from_standardized_donor_components(
            components=st, donor_counts=sizes, source_by_donor=sources,
            objective=OBJECTIVES[1], alpha=0.01,
        )


@pytest.mark.parametrize("bad", ["", "AUTO", "SOURCE_BALANCED_DEFAULT", None])
def test_no_implicit_fit_objective(bad):
    sizes, sources, _ = planted()
    with pytest.raises(ValueError, match="explicit fit objective"):
        donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=bad)


@pytest.mark.parametrize("bad", [0, -1, 1.5, True])
def test_invalid_donor_count_stops(bad):
    sizes, sources, _ = planted()
    sizes[0] = bad
    with pytest.raises(ValueError, match="invalid donor"):
        donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=OBJECTIVES[1])


@pytest.mark.parametrize("bad", [-0.1, float("nan"), float("inf"), True])
def test_invalid_regularization_stops(bad):
    sizes, sources, data = planted()
    with pytest.raises(ValueError, match="ridge alpha"):
        fit_from_standardized_donor_components(
            components=standardized(data), donor_counts=sizes, source_by_donor=sources,
            objective=OBJECTIVES[1], alpha=bad,
        )


def test_nonfinite_moments_do_not_produce_false_clean_fit():
    sizes, sources, data = planted()
    st = standardized(data)
    gram, rhs, rss = st[0]
    tampered = gram.copy()
    tampered[0, 0] = float("nan")
    st[0] = (tampered, rhs, rss)
    with pytest.raises(ValueError, match="invalid donor standardized moments"):
        fit_from_standardized_donor_components(
            components=st, donor_counts=sizes, source_by_donor=sources,
            objective=OBJECTIVES[1], alpha=0.01,
        )


def test_missing_source_roster_stops():
    sizes, sources, _ = planted()
    del sources[2]
    with pytest.raises(ValueError, match="roster"):
        donor_total_masses(donor_counts=sizes, source_by_donor=sources, objective=OBJECTIVES[2])


def test_all_constant_targets_return_zero_without_pretending_scientific_power():
    sizes, sources, data = planted()
    st = standardized(data)
    st = {d: (g, np.zeros_like(r), 0.) for d, (g, r, rss) in st.items()}
    got = fit_from_standardized_donor_components(
        components=st, donor_counts=sizes, source_by_donor=sources,
        objective=OBJECTIVES[1], alpha=0.01,
    )
    assert np.array_equal(got, np.zeros(3))
    # Separate six-state evidence contract MUST mark heldout constant target
    # NOT_ESTIMABLE, never use the zero vector as a clean shortcut score.


def test_g3_schema_and_objective_registry_are_explicit():
    assert SCHEMA == "V26_G3_EXPLICIT_ATTACKER_FIT_OBJECTIVE_V1"
    assert set(OBJECTIVES) == {
        "CURRENT_CELL_WEIGHTED", "PRODUCTION_OBJECTIVE_MATCHED",
        "SOURCE_DONOR_BALANCED_DIAGNOSTIC",
    }
