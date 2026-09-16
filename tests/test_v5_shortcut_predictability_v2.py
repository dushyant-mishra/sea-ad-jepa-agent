"""Synthetic qualification of CROSS_FITTED_SHORTCUT_PREDICTABILITY_V2.

Runs BEFORE the V2 contract freezes, which is permitted: synthetic fixtures and
calibration may precede the freeze; real FULL104 shortcut results may not.

Every nuisance fixture also carries a planted real shortcut, so that suppressing a
confound can never be satisfied by predicting nothing.
"""
from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.v5.shortcut_predictability_v2 import (
    CheapRidgeAttackerV1,
    global_cell_state_baseline,
    DonorBalancedScreenerV1,
    ForbiddenShortcutInputError,
    MODULE_ID,
    inner_rotation,
    reject_forbidden,
    stratified_outer_folds,
)

ND, NC, NA = 20, 80, 200
TARGET = 0
ALPHA, MAXF = 1e-2, 64            # calibrated on synthetic only (see calibration test)
BUDGET = 40


def world(rng, *, plant="single", confound=None, n_donors=ND, cells=NC, sources=2,
          unequal=False):
    """Synthetic world with a known planted shortcut and an optional nuisance."""
    if unequal:
        counts = np.array([cells * 4] * (n_donors // 2) + [cells // 2] * (n_donors - n_donors // 2))
    else:
        counts = np.full(n_donors, cells)
    donor = np.repeat(np.arange(n_donors), counts)
    n = donor.size
    src_of_donor = np.array([i % sources for i in range(n_donors)])
    V = rng.normal(size=(n, NA))
    truth = []
    latent = rng.normal(size=n)
    if plant == "single":
        V[:, TARGET] = latent + 0.20 * rng.normal(size=n)
        V[:, 5] = latent + 0.20 * rng.normal(size=n)
        truth = [5]
    elif plant == "redundant":
        V[:, TARGET] = latent + 0.20 * rng.normal(size=n)
        for j in (5, 6, 7, 8):
            V[:, j] = latent + 0.25 * rng.normal(size=n)
        truth = [5, 6, 7, 8]
    elif plant == "distributed":
        parts = [rng.normal(size=n) for _ in range(4)]
        for j, p in zip((5, 6, 7, 8), parts):
            V[:, j] = p
        V[:, TARGET] = sum(parts) / 2.0 + 0.35 * rng.normal(size=n)
        truth = [5, 6, 7, 8]
    meas = np.ones((n_donors, NA), dtype=bool)

    if confound == "donor":
        V += (rng.normal(size=n_donors) * 20.0)[donor][:, None]
    elif confound == "operator":
        op = np.arange(n_donors) % 4
        V += (rng.normal(size=(4, NA)) * 12.0)[op[donor]]
    elif confound == "source":
        V += (rng.normal(size=(sources, NA)) * 15.0)[src_of_donor[donor]]
    elif confound == "within_donor_depth":
        V = V + rng.lognormal(0.0, 0.8, n)[:, None] * 3.0
    elif confound == "within_donor_shift":
        V = V + rng.normal(size=n)[:, None] * 4.0
    elif confound == "missingness":
        meas[: n_donors // 2, 40] = False
        meas[: n_donors // 2, 41] = False
        for d in range(n_donors // 2):
            V[donor == d, 40] = 0.0
            V[donor == d, 41] = 0.0
    return V, donor, src_of_donor, meas, truth


def screen_and_attack(V, donor, src, meas, *, budget=BUDGET, alpha=ALPHA):
    """One honest cross-fit: screen on inner-A, fit on inner-B, evaluate on held-out."""
    n_donors = meas.shape[0]
    folds = stratified_outer_folds(src, 4, "TEST_V2")
    val = np.flatnonzero(folds == 0)
    train = np.flatnonzero(folds != 0)
    iA, iB = inner_rotation(train, src, "TEST_V2")
    eligible = meas.all(0).copy()
    scr = DonorBalancedScreenerV1(candidate_budget=budget)
    rowsA = np.flatnonzero(np.isin(donor, iA))
    cand = scr.candidates(values=V[rowsA], target=TARGET, donor_codes=donor[rowsA],
                          eligible=eligible, source_by_donor=src)
    rowsB = np.flatnonzero(np.isin(donor, iB))
    rowsV = np.flatnonzero(np.isin(donor, val))
    atk = CheapRidgeAttackerV1(alpha=alpha, max_features=MAXF)
    visible = eligible.copy()
    visible[TARGET] = False           # the target is hidden; its own value is never a feature
    out = atk.incremental_r2(values=V, target=TARGET, features=cand, visible=visible,
                             train_rows=rowsB, eval_rows=rowsV,
                             eval_donor_codes=donor[rowsV], train_donor_codes=donor[rowsB],
                             source_by_donor=src)
    # PRIMARY statistic: partial R2 over the residual global cell state cannot explain
    return cand, out["partial_r2"], out


# ------------------------------------------------------------------ hygiene
def test_module_identity_and_forbidden_inputs() -> None:
    assert MODULE_ID == "CROSS_FITTED_SHORTCUT_PREDICTABILITY_V2"
    for bad in ("symbol", "biotype", "ontology", "chromosome", "source_label",
                "operator_index", "donor_id", "q_depth", "visibility", "target_value"):
        with pytest.raises(ForbiddenShortcutInputError):
            reject_forbidden(**{bad: 1})


def test_attacker_rejects_unfrozen_configuration() -> None:
    for kw in ({"alpha": 0.0}, {"alpha": -1.0}, {"max_features": 0}):
        base = dict(alpha=ALPHA, max_features=MAXF)
        base.update(kw)
        with pytest.raises(ValueError):
            CheapRidgeAttackerV1(**base)


def test_outer_folds_validate_every_donor_exactly_once() -> None:
    src = np.array([0, 0, 0, 1, 1, 2, 2, 2, 2, 1])
    f = stratified_outer_folds(src, 3, "NS")
    assert (f >= 0).all() and f.size == src.size
    for s in np.unique(src):
        assert len(set(f[src == s])) >= min(3, int((src == s).sum()))


def test_inner_rotation_partitions_training_donors() -> None:
    src = np.array([0] * 8 + [1] * 6)
    train = np.arange(14)
    a, b = inner_rotation(train, src, "NS")
    assert set(a) | set(b) == set(train)
    assert not (set(a) & set(b))


# ------------------------------------------------------------------ S1 / S2 / S3 recall
def test_S1_single_strong_shortcut_is_retained_and_detected() -> None:
    V, d, s, m, truth = world(np.random.default_rng(1), plant="single")
    cand, r2, per = screen_and_attack(V, d, s, m)
    assert truth[0] in cand, "screening dropped the single planted shortcut"
    assert per["evaluated_donors"] > 0, "VACUOUS: no held-out donor evaluated"
    assert r2 > 0.30, f"attacker failed to detect a strong shortcut (incremental R2={r2:.3f})"


def test_S2_redundant_shortcut_set_is_retained() -> None:
    V, d, s, m, truth = world(np.random.default_rng(2), plant="redundant")
    cand, r2, per = screen_and_attack(V, d, s, m)
    kept = [t for t in truth if t in cand]
    assert len(kept) >= 3, f"screening kept only {kept} of redundant set {truth}"
    assert r2 > 0.30


def test_S3_weak_distributed_shortcut_is_retained() -> None:
    V, d, s, m, truth = world(np.random.default_rng(3), plant="distributed")
    cand, r2, per = screen_and_attack(V, d, s, m)
    kept = [t for t in truth if t in cand]
    assert len(kept) >= 3, f"screening kept only {kept} of distributed set {truth}"
    assert r2 > 0.15, f"combination shortcut not detected (incremental R2={r2:.3f})"


# ------------------------------------------------------------------ S4-S8 confounds
@pytest.mark.parametrize("confound", ["donor", "operator", "source",
                                      "within_donor_depth", "within_donor_shift"])
def test_confound_does_not_manufacture_a_shortcut_and_real_one_survives(confound: str) -> None:
    rng = np.random.default_rng(4)
    # nuisance only: no planted shortcut -> held-out predictability must stay near zero
    V, d, s, m, _ = world(rng, plant="none", confound=confound)
    _, r2_null, per_null = screen_and_attack(V, d, s, m)
    assert per_null["evaluated_donors"] > 0, "VACUOUS: no held-out donor evaluated"
    assert r2_null < 0.10, f"{confound} manufactured held-out predictability ({r2_null:.3f})"
    # same nuisance WITH a planted shortcut -> must still be detected (specificity)
    V2, d2, s2, m2, truth = world(np.random.default_rng(5), plant="single", confound=confound)
    cand, r2, _ = screen_and_attack(V2, d2, s2, m2)
    assert truth[0] in cand, f"{confound} caused screening to drop the real shortcut"
    assert r2 > 0.20, f"specificity lost under {confound} (incremental R2={r2:.3f})"


# ------------------------------------------------------------------ S9 missingness
def test_S9_shared_missingness_does_not_become_a_shortcut() -> None:
    V, d, s, m, truth = world(np.random.default_rng(6), plant="single", confound="missingness")
    cand, r2, _ = screen_and_attack(V, d, s, m)
    assert 40 not in cand and 41 not in cand, "co-missing addresses entered the candidate set"
    assert truth[0] in cand, "missingness handling dropped the real shortcut"


# ------------------------------------------------------------------ S10 source imbalance
def test_S10_larger_source_does_not_crowd_out_a_cross_source_shortcut() -> None:
    V, d, s, m, truth = world(np.random.default_rng(7), plant="single", unequal=True)
    cand, r2, _ = screen_and_attack(V, d, s, m)
    assert truth[0] in cand, "source-size imbalance crowded out the real shortcut"
    assert r2 > 0.20


# ------------------------------------------------------------------ empty-set gaming
def test_returning_no_candidates_cannot_count_as_specificity() -> None:
    V, d, s, m, truth = world(np.random.default_rng(8), plant="single")
    atk = CheapRidgeAttackerV1(alpha=ALPHA, max_features=MAXF)
    vis = np.ones(NA, bool); vis[TARGET] = False
    out = atk.incremental_r2(values=V, target=TARGET, features=[], visible=vis,
                             train_rows=np.arange(500), eval_rows=np.arange(500, 800),
                             eval_donor_codes=d[500:800], train_donor_codes=d[:500],
                             source_by_donor=s)
    assert out["partial_r2"] == 0.0, "empty feature set must give zero partial gain"


# ------------------------------------------------------------------ determinism
def test_screening_and_attacker_are_deterministic() -> None:
    V, d, s, m, _ = world(np.random.default_rng(9), plant="single")
    a1, r1, _ = screen_and_attack(V, d, s, m)
    a2, r2, _ = screen_and_attack(V, d, s, m)
    assert np.array_equal(a1, a2) and r1 == r2


# ------------------------------------------------------------------ baseline behaviour
def test_global_cell_state_baseline_absorbs_a_universal_factor() -> None:
    """The confound that broke the first V2 draft must land in the BASELINE, not the gain."""
    rng = np.random.default_rng(31)
    V, d, s, m, _ = world(rng, plant="none", confound="within_donor_shift")
    _, incr, out = screen_and_attack(V, d, s, m)
    assert out["baseline_r2"] > 0.5, "global cell state should be highly predictive here"
    assert incr < 0.10, f"universal factor leaked into the incremental gain ({incr:.3f})"


def test_baseline_uses_only_visible_addresses() -> None:
    V = np.arange(40, dtype=float).reshape(4, 10)
    vis = np.zeros(10, bool); vis[[1, 3, 5]] = True
    b = global_cell_state_baseline(V, vis)
    assert b.shape == (4, 2)
    assert np.allclose(b[:, 0], V[:, [1, 3, 5]].mean(1))
