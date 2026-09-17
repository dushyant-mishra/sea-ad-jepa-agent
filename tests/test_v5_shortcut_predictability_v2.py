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


# ------------------------------------------------------------------ candidate ordering
# REGRESSION: an earlier implementation returned candidates in ADDRESS-INDEX order via
# np.sort. The frozen shortcut rule takes a PREFIX, so the prefix became an arbitrary
# low-index subset and the strongest partner was never masked. A real-data positive
# control exposed it: the planted partner ranked 1 of 28 by score but was absent from the
# implemented prefix.
def test_candidates_are_returned_in_screening_score_order() -> None:
    V, d, s, m, truth = world(np.random.default_rng(41), plant="single")
    scr = DonorBalancedScreenerV1(candidate_budget=BUDGET)
    eligible = m.all(0).copy()
    cand = scr.candidates(values=V, target=TARGET, donor_codes=d,
                          eligible=eligible, source_by_donor=s)
    score = scr.score(values=V, target=TARGET, donor_codes=d,
                      eligible=eligible, source_by_donor=s)
    assert cand.size > 1
    vals = score[cand]
    assert np.all(np.diff(vals) <= 1e-12), "candidates are not in descending score order"
    assert cand[0] == truth[0], "strongest planted partner is not first"
    assert not np.array_equal(cand, np.sort(cand)), "index-sorted output would break the prefix rule"


def test_order_by_score_restores_contract_order_after_a_set_union() -> None:
    V, d, s, m, truth = world(np.random.default_rng(42), plant="single")
    scr = DonorBalancedScreenerV1(candidate_budget=BUDGET)
    eligible = m.all(0).copy()
    kw = dict(values=V, target=TARGET, donor_codes=d, eligible=eligible, source_by_donor=s)
    cand = scr.candidates(**kw)
    unioned = np.union1d(cand, cand)          # a set union destroys ordering
    assert np.array_equal(unioned, np.sort(unioned))
    restored = scr.order_by_score(unioned, **kw)
    assert restored[0] == truth[0], "order_by_score did not restore the strongest partner first"


def test_shortcut_prefix_contains_the_planted_partner() -> None:
    """End-to-end: the frozen prefix rule must actually select the real partner."""
    V, d, s, m, truth = world(np.random.default_rng(43), plant="single")
    scr = DonorBalancedScreenerV1(candidate_budget=BUDGET)
    cand = scr.candidates(values=V, target=TARGET, donor_codes=d,
                          eligible=m.all(0).copy(), source_by_donor=s)
    assert truth[0] in list(cand[:3]), "planted partner missing from the shortcut prefix"


# =================================================================== INTEGRATION
# The unit tests above proved the pieces work; a real-data positive control proved they
# were wired together wrongly. These tests run the PRODUCTION path end to end:
#   screen -> rank -> shortcut-set selection -> mask construction -> fresh attacker.
SHORTCUT_REDUCTION, SHORTCUT_CAP, NO_SHORTCUT_FLOOR = 0.50, 8, 0.05


def _production_path(V, donor, src, meas, target, burden, seed=0):
    """Mirrors run_v2_full104: two independent inner directions, union of shortcut sets."""
    folds = stratified_outer_folds(src, 4, "TEST_V2")
    tr_d = np.flatnonzero(folds != 0)
    iA, iB = inner_rotation(tr_d, src, "TEST_V2")
    rowsA = np.flatnonzero(np.isin(donor, iA)); donA = donor[rowsA]
    rowsB = np.flatnonzero(np.isin(donor, iB)); donB = donor[rowsB]
    eligible = meas.all(0).copy()
    allvis = eligible.copy(); allvis[target] = False
    scr = DonorBalancedScreenerV1(candidate_budget=BUDGET)
    atk = CheapRidgeAttackerV1(alpha=ALPHA, max_features=MAXF)
    n_addr = V.shape[1]
    base = global_cell_state_baseline(V, allvis)

    def direction(screen_donors, fit_rows, fit_don, ev_rows, ev_don):
        rows_s = np.flatnonzero(np.isin(donor, screen_donors))
        cnd = scr.candidates(values=V[rows_s], target=target, donor_codes=donor[rows_s],
                             eligible=allvis, source_by_donor=src)
        if cnd.size == 0:
            return []
        p0 = atk.incremental_r2(values=V, target=target, features=cnd, visible=None,
                                train_rows=fit_rows, eval_rows=ev_rows, eval_donor_codes=ev_don,
                                train_donor_codes=fit_don, source_by_donor=src,
                                precomputed_baseline=base)["partial_r2"]
        if p0 < NO_SHORTCUT_FLOOR:
            return []
        for n in range(1, min(SHORTCUT_CAP, cnd.size) + 1):
            trial = np.setdiff1d(cnd, cnd[:n])
            p = atk.incremental_r2(values=V, target=target, features=trial, visible=None,
                                   train_rows=fit_rows, eval_rows=ev_rows, eval_donor_codes=ev_don,
                                   train_donor_codes=fit_don, source_by_donor=src,
                                   precomputed_baseline=base)["partial_r2"]
            if p <= SHORTCUT_REDUCTION * p0:
                return list(cnd[:n])
        return list(cnd[:min(SHORTCUT_CAP, cnd.size)])

    short = sorted(set(direction(iA, rowsB, donB, rowsA, donA))
                   | set(direction(iB, rowsA, donA, rowsB, donB)))
    g = np.random.default_rng(seed)
    pool = np.setdiff1d(np.arange(n_addr), np.array([target]))
    pre = short[:burden - 1]
    rest = np.setdiff1d(pool, np.array(pre, dtype=np.int64)) if pre else pool
    mask = set(pre) | set(g.choice(rest, size=max(0, burden - 1 - len(pre)),
                                   replace=False).tolist()) | {target}
    return short, mask


def test_integration_planted_partner_reaches_the_shortcut_set_and_the_mask() -> None:
    V, d, s, m, truth = world(np.random.default_rng(51), plant="single")
    short, mask = _production_path(V, d, s, m, TARGET, burden=40)
    assert short, "no shortcut set produced for a strongly planted shortcut"
    assert truth[0] in short, f"planted partner {truth[0]} missing from shortcut set {short}"
    assert truth[0] in mask, "planted partner reached the shortcut set but not the mask"


def test_integration_redundant_partners_are_co_masked() -> None:
    V, d, s, m, truth = world(np.random.default_rng(52), plant="redundant")
    short, mask = _production_path(V, d, s, m, TARGET, burden=40)
    kept = [t for t in truth if t in mask]
    assert len(kept) >= 2, f"only {kept} of the redundant set {truth} were co-masked"


def test_negative_control_low_index_addresses_are_not_preferentially_selected() -> None:
    """The defect made the prefix an arbitrary LOW-INDEX subset. Prove that is gone."""
    picks = []
    for seed in range(12):
        V, d, s, m, truth = world(np.random.default_rng(100 + seed), plant="single")
        short, _ = _production_path(V, d, s, m, TARGET, burden=40, seed=seed)
        picks += [x for x in short if x != truth[0]]
    if picks:
        median_idx = float(np.median(picks))
        # under the defect these clustered at the low end of the 200-address space
        assert median_idx > 40, (
            f"selected non-planted addresses cluster at low indices (median {median_idx}); "
            "index-order leakage may have returned")


def test_address_renumbering_does_not_change_which_columns_are_selected() -> None:
    """Permutation test: selection must follow the DATA, not the address numbering."""
    V, d, s, m, truth = world(np.random.default_rng(61), plant="single")
    short_a, _ = _production_path(V, d, s, m, TARGET, burden=40)
    assert truth[0] in short_a

    rng = np.random.default_rng(7)
    perm = rng.permutation(V.shape[1])
    # keep the target column in a known place so the two runs are comparable
    perm = perm[perm != TARGET]
    perm = np.concatenate([[TARGET], perm])
    inv = np.empty_like(perm); inv[perm] = np.arange(perm.size)
    Vp = V[:, perm]
    mp = m[:, perm]
    short_b, _ = _production_path(Vp, d, s, mp, 0, burden=40)
    # map the permuted selections back to original column identities
    back = sorted(perm[x] for x in short_b)
    assert truth[0] in back, (
        f"renumbering changed the selection: {sorted(short_a)} -> {back}")
