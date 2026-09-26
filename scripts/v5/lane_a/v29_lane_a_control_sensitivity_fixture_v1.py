#!/usr/bin/env python3
"""Synthetic fixture that proves the Lane A controls can actually fail.

WHAT THIS IS
    A control is only evidence if some outcome would make it fire. This module
    builds small synthetic cell populations in which a specific failure mode is
    *planted*, runs each control specified in the Lane A decision sheet, and lets
    the accompanying tests assert that the control fires on the planted failure
    and does not fire on a healthy population.

WHAT THIS IS NOT
    - It is not FULL104 and touches no real data, no protected outcome, and no
      sealed confirmation set.
    - It trains nothing. The probe is a closed-form ridge solve, used only so
      that each control's discriminating power is measurable without a model.
    - Every number in this file is a fixture-internal constant for a unit test.
      None of them is a proposed project parameter, a model geometry, a mask
      fraction, an EMA half-life, an optimizer setting, or a training seed. The
      Lane A proposal records all of those as UNSET_REQUIRES_APPROVAL, and
      nothing here changes that.
    - Scores produced here are properties of planted synthetic structure. They
      are not biology and must never be cited as a project result.

GEOMETRY
    The fixture reproduces the *kind* of geometry the real problem has, at a
    scale a test can run: donors as the clustering unit with cells nested inside
    them, per-cell library depth, depth-driven detection and structural
    missingness, overdispersed integer counts, and a shared low-dimensional
    latent cell state. It is deliberately much smaller than the real substrate
    and is not a stand-in for it.

TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# Fixture-internal constants. Not project parameters. See module docstring.
# --------------------------------------------------------------------------- #
FIXTURE_DONORS = 24
FIXTURE_CELLS_PER_DONOR = 40
FIXTURE_ADDRESSES = 60
FIXTURE_QUERIES = 12
FIXTURE_LATENT_DIM = 6
FIXTURE_TARGET_DIM = 8
# The pooled cell summary must be able to carry the cell-level state. An
# under-capacity summary can never fire as a control, which would wrongly credit
# the construction; UNDERCAPACITY below exists to demonstrate exactly that.
FIXTURE_POOLED_SUMMARY_DIM = 16
FIXTURE_UNDERCAPACITY_SUMMARY_DIM = 2
FIXTURE_HELD_OUT_DONORS = 8
FIXTURE_RIDGE = 1e-2
FIXTURE_BOOTSTRAP_DRAWS = 400
FIXTURE_SEED = 20260926

REGIMES = (
    "QUERY_LOCAL",          # healthy: target is cell-specific and query-specific
    "IDENTITY_ONLY",        # planted failure: target depends only on the address
    "GLOBAL_ONLY",          # planted failure: target is a cell-level object
    "TECHNICAL_ONLY",       # planted failure: target is a measurement-state object
    "QUERY_SCALAR",         # target depends on the hidden count (leak sensitivity)
    "PURE_NOISE",           # null: target depends on nothing
)

CONDITIONS = (
    "FULL",
    "IDENTITY_ONLY",
    "GLOBAL_CONTEXT_ONLY",
    "GLOBAL_CONTEXT_ONLY_UNDERCAPACITY",
    "TECHNICAL_ONLY",
    "RNA_SHUFFLED_WITHIN_CELL",
    "DONOR_KEY_ONLY",
    "LEAKED",
)


@dataclass(frozen=True)
class Population:
    """One synthetic cell population. Cells are nested inside donors."""

    donor_of_cell: np.ndarray      # (cells,) int donor index
    latent: np.ndarray             # (cells, k) latent cell state
    counts: np.ndarray             # (cells, addresses) integer counts
    measured: np.ndarray           # (cells, addresses) bool structural support
    depth: np.ndarray              # (cells,) library depth
    detection: np.ndarray          # (cells,) detected fraction
    queries: np.ndarray            # (q,) address indices used as queries

    @property
    def n_cells(self) -> int:
        return int(self.latent.shape[0])

    @property
    def n_donors(self) -> int:
        return int(self.donor_of_cell.max()) + 1


def _softplus(x: np.ndarray) -> np.ndarray:
    return np.log1p(np.exp(np.clip(x, -30.0, 30.0)))


def build_population(seed: int = FIXTURE_SEED) -> Population:
    rng = np.random.default_rng(seed)
    n_donors = FIXTURE_DONORS
    n_cells = n_donors * FIXTURE_CELLS_PER_DONOR
    k = FIXTURE_LATENT_DIM
    a = FIXTURE_ADDRESSES

    donor_of_cell = np.repeat(np.arange(n_donors), FIXTURE_CELLS_PER_DONOR)

    # Donor structure plus within-donor cell variation: cells are clustered, so the
    # donor is the independent unit and cells are not independent replicates.
    donor_offset = rng.normal(scale=0.8, size=(n_donors, k))
    latent = donor_offset[donor_of_cell] + rng.normal(scale=1.0, size=(n_cells, k))

    loadings = rng.normal(scale=0.7, size=(a, k))
    depth = np.exp(rng.normal(loc=0.0, scale=0.45, size=n_cells))

    rate = _softplus(latent @ loadings.T) * depth[:, None] * 3.0
    counts = rng.poisson(rate).astype(np.float64)

    # Structural support: an address-level panel probability modulated by depth,
    # so missingness is depth-dependent the way real detection is.
    panel = rng.uniform(0.55, 0.98, size=a)
    detect_prob = np.clip(panel[None, :] * (0.55 + 0.45 * (depth[:, None] / depth.mean())), 0.0, 1.0)
    measured = rng.random((n_cells, a)) < detect_prob
    counts = np.where(measured, counts, 0.0)
    detection = measured.mean(axis=1)

    queries = rng.choice(a, size=FIXTURE_QUERIES, replace=False)
    return Population(
        donor_of_cell=donor_of_cell,
        latent=latent,
        counts=counts,
        measured=measured,
        depth=depth,
        detection=detection,
        queries=queries,
    )


def build_targets(pop: Population, regime: str, seed: int = FIXTURE_SEED + 1) -> np.ndarray:
    """Return targets of shape (queries, cells, target_dim) under a planted regime."""
    if regime not in REGIMES:
        raise ValueError("unknown regime: " + regime)
    rng = np.random.default_rng(seed)
    n_q = len(pop.queries)
    n_cells = pop.n_cells
    d = FIXTURE_TARGET_DIM
    k = FIXTURE_LATENT_DIM
    noise = rng.normal(scale=0.25, size=(n_q, n_cells, d))
    targets = np.zeros((n_q, n_cells, d))

    if regime == "QUERY_LOCAL":
        # Cell-specific AND query-specific: a different read-out of the latent
        # state for each address, plus a per-address offset.
        maps = rng.normal(scale=1.0, size=(n_q, d, k))
        offsets = rng.normal(scale=1.0, size=(n_q, d))
        for j in range(n_q):
            targets[j] = pop.latent @ maps[j].T + offsets[j]
    elif regime == "IDENTITY_ONLY":
        offsets = rng.normal(scale=2.0, size=(n_q, d))
        for j in range(n_q):
            targets[j] = np.broadcast_to(offsets[j], (n_cells, d))
    elif regime == "GLOBAL_ONLY":
        shared = rng.normal(scale=1.0, size=(d, k))
        cell_state = pop.latent @ shared.T
        for j in range(n_q):
            targets[j] = cell_state
    elif regime == "TECHNICAL_ONLY":
        tech = np.column_stack(
            [
                (pop.depth - pop.depth.mean()) / pop.depth.std(),
                (pop.detection - pop.detection.mean()) / pop.detection.std(),
            ]
        )
        gain = rng.normal(scale=1.5, size=(d, 2))
        cell_state = tech @ gain.T
        for j in range(n_q):
            targets[j] = cell_state
    elif regime == "QUERY_SCALAR":
        directions = rng.normal(scale=1.0, size=(n_q, d))
        for j, q in enumerate(pop.queries):
            hidden = np.log1p(pop.counts[:, q])
            hidden = (hidden - hidden.mean()) / (hidden.std() + 1e-9)
            targets[j] = hidden[:, None] * directions[j]
    elif regime == "PURE_NOISE":
        pass

    return targets + noise


def _log1p_visible(pop: Population, query: int) -> np.ndarray:
    """Remaining observed RNA: log1p counts with the query column withheld."""
    visible = np.log1p(pop.counts.copy())
    visible[:, query] = 0.0
    return visible


def _shuffle_within_cell(values: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Permute each cell's values across its own addresses.

    Destroys the address-to-value pairing while leaving that cell's library depth
    and detected fraction exactly unchanged, so any score drop is attributable to
    molecular content rather than a technical side-effect.
    """
    out = values.copy()
    for i in range(out.shape[0]):
        out[i] = rng.permutation(out[i])
    return out


def build_features(
    pop: Population, query: int, condition: str, rng: np.random.Generator
) -> np.ndarray:
    """Feature matrix (cells, p) for one query address under one control condition."""
    n_cells = pop.n_cells
    ones = np.ones((n_cells, 1))
    visible = _log1p_visible(pop, query)

    if condition == "IDENTITY_ONLY":
        # The address code is constant within a per-query fit, so knowing only the
        # address means predicting that address's mean state.
        return ones
    if condition == "FULL":
        return np.hstack([ones, visible])
    if condition == "GLOBAL_CONTEXT_ONLY":
        projection = np.random.default_rng(FIXTURE_SEED + 7).normal(
            size=(FIXTURE_ADDRESSES, FIXTURE_POOLED_SUMMARY_DIM)
        )
        return np.hstack([ones, visible @ projection])
    if condition == "GLOBAL_CONTEXT_ONLY_UNDERCAPACITY":
        projection = np.random.default_rng(FIXTURE_SEED + 7).normal(
            size=(FIXTURE_ADDRESSES, FIXTURE_UNDERCAPACITY_SUMMARY_DIM)
        )
        return np.hstack([ones, visible @ projection])
    if condition == "TECHNICAL_ONLY":
        support = pop.measured.astype(np.float64)
        projection = np.random.default_rng(FIXTURE_SEED + 11).normal(
            size=(FIXTURE_ADDRESSES, FIXTURE_POOLED_SUMMARY_DIM)
        )
        return np.hstack(
            [
                ones,
                pop.depth[:, None],
                pop.detection[:, None],
                support @ projection,
            ]
        )
    if condition == "RNA_SHUFFLED_WITHIN_CELL":
        shuffled = _shuffle_within_cell(visible, rng)
        return np.hstack([ones, shuffled])
    if condition == "DONOR_KEY_ONLY":
        n_donors = pop.n_donors
        onehot = np.zeros((n_cells, n_donors))
        onehot[np.arange(n_cells), pop.donor_of_cell] = 1.0
        return np.hstack([ones, onehot])
    if condition == "LEAKED":
        hidden = np.log1p(pop.counts[:, query])[:, None]
        return np.hstack([ones, visible, hidden])
    raise ValueError("unknown condition: " + condition)


def _standardize(train: np.ndarray, full: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Z-score every non-intercept column using training statistics.

    Without this the ridge penalty is not scale-invariant, and a condition that
    happens to carry large-scale columns shrinks its own informative columns. That
    would make a control look weak for a purely numerical reason.
    """
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    constant = std < 1e-12
    mean = np.where(constant, 0.0, mean)
    std = np.where(constant, 1.0, std)
    return (train - mean) / std, (full - mean) / std


def _ridge_fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    gram = x.T @ x
    scale = float(np.trace(gram)) / max(gram.shape[0], 1)
    reg = FIXTURE_RIDGE * (scale if scale > 0 else 1.0) * np.eye(gram.shape[0])
    return np.linalg.solve(gram + reg, x.T @ y)


def per_donor_scores(
    pop: Population, targets: np.ndarray, condition: str, seed: int = FIXTURE_SEED + 3
) -> np.ndarray:
    """Bounded per-held-out-donor score for one condition.

    Score is the fraction of held-out target variance explained, measured about the
    training-set global mean, so an identity-only condition earns exactly the
    between-address share and nothing more. The donor is the unit; cells inside a
    donor are not independent replicates.

    Every condition sees the same cells, the same donor split and the same query
    set: only the ablated channel differs. That is the common-random-numbers
    pairing the decision sheet requires.
    """
    rng = np.random.default_rng(seed)
    held_out_donors = np.arange(FIXTURE_HELD_OUT_DONORS)
    is_held_out = np.isin(pop.donor_of_cell, held_out_donors)
    train = ~is_held_out

    global_mean = targets[:, train, :].reshape(-1, targets.shape[2]).mean(axis=0)

    sse = np.zeros(len(held_out_donors))
    sst = np.zeros(len(held_out_donors))
    for j, query in enumerate(pop.queries):
        features = build_features(pop, int(query), condition, rng)
        scaled_train, scaled_all = _standardize(features[train], features)
        coefficients = _ridge_fit(scaled_train, targets[j][train])
        predicted = scaled_all[is_held_out] @ coefficients
        actual = targets[j][is_held_out]
        donors = pop.donor_of_cell[is_held_out]
        residual = ((actual - predicted) ** 2).sum(axis=1)
        total = ((actual - global_mean) ** 2).sum(axis=1)
        for index, donor in enumerate(held_out_donors):
            rows = donors == donor
            sse[index] += residual[rows].sum()
            sst[index] += total[rows].sum()
    return 1.0 - sse / sst


def paired_delta_interval(
    full: np.ndarray, ablated: np.ndarray, seed: int = FIXTURE_SEED + 5
) -> Tuple[float, float, float]:
    """Donor-clustered bootstrap interval for the paired delta S(full) - S(ablated).

    Resampling is over donors because the donor is the independent unit. Returns
    (point estimate, lower bound, upper bound).
    """
    rng = np.random.default_rng(seed)
    delta = full - ablated
    n = len(delta)
    draws = np.empty(FIXTURE_BOOTSTRAP_DRAWS)
    for b in range(FIXTURE_BOOTSTRAP_DRAWS):
        draws[b] = delta[rng.integers(0, n, size=n)].mean()
    return float(delta.mean()), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def evaluate(regime: str, seed: int = FIXTURE_SEED) -> Dict[str, Dict[str, float]]:
    """Run every control against one planted regime.

    Returns, per condition, the mean score and the donor-clustered interval for the
    paired delta against FULL. A control FIRES (disqualifies the construction) when
    that interval includes or lies below zero.
    """
    pop = build_population(seed)
    targets = build_targets(pop, regime, seed + 1)
    scores = {c: per_donor_scores(pop, targets, c, seed + 3) for c in CONDITIONS}
    out: Dict[str, Dict[str, float]] = {}
    for condition, value in scores.items():
        point, low, high = paired_delta_interval(scores["FULL"], value, seed + 5)
        out[condition] = {
            "score": float(value.mean()),
            "delta_vs_full": point,
            "delta_low": low,
            "delta_high": high,
            "fires": bool(low <= 0.0),
        }
    return out


def variance_decomposition(targets: np.ndarray) -> Dict[str, float]:
    """Split target variance into address, cell, and cell-by-query interaction shares.

    This is the executable form of the pre-training teacher-only screen. It needs no
    student, no optimizer and no gradient: one teacher forward pass produces the
    targets and this reads them.

    Shares are of total variance about the grand mean:
      address_share     - how much is explained by which address was asked
      cell_share        - how much is explained by which cell it is
      interaction_share - how much varies with the cell AND the query together

    A target whose interaction share is negligible is a cell-level or address-level
    object wearing a query label, and no amount of training makes it query-local.

    LIMITATION, tested below: without replicate targets for the same (cell, query)
    this cannot separate genuine interaction from noise. A pure-noise target also
    shows a high interaction share. The screen must be read together with the probe
    score: high interaction share AND a near-zero probe score means noise, not
    query-local structure.
    """
    grand = targets.mean(axis=(0, 1))
    per_query = targets.mean(axis=1) - grand
    per_cell = targets.mean(axis=0) - grand
    interaction = targets - grand - per_query[:, None, :] - per_cell[None, :, :]
    total = ((targets - grand) ** 2).mean()
    if total <= 0:
        return {"address_share": 0.0, "cell_share": 0.0, "interaction_share": 0.0}
    return {
        "address_share": float((per_query ** 2).mean() / total),
        "cell_share": float((per_cell ** 2).mean() / total),
        "interaction_share": float((interaction ** 2).mean() / total),
    }


def query_exchangeability(
    pop: Population, targets: np.ndarray, seed: int = FIXTURE_SEED + 13
) -> Dict[str, float]:
    """Does it matter which query was asked?

    This is the falsifying test for query-locality that GLOBAL_CONTEXT_ONLY cannot
    provide. Each query's model is fitted on its own targets, then scored twice on
    held-out donors: once against its own targets, once against a different query's
    targets under a fixed derangement. Each query's targets are first centred by
    their own training mean, so the address main effect cannot carry the comparison.

    If the target has no cell-by-query structure, every query's map is the same and
    asking the wrong query costs nothing: the paired delta then includes zero and
    the construction is disqualified for the stated goal.
    """
    rng = np.random.default_rng(seed)
    held_out_donors = np.arange(FIXTURE_HELD_OUT_DONORS)
    is_held_out = np.isin(pop.donor_of_cell, held_out_donors)
    train = ~is_held_out
    donors = pop.donor_of_cell[is_held_out]
    n_q = len(pop.queries)
    partner = (np.arange(n_q) + 1) % n_q

    centred = np.empty_like(targets)
    for j in range(n_q):
        centred[j] = targets[j] - targets[j][train].mean(axis=0)

    own_sse = np.zeros(len(held_out_donors))
    cross_sse = np.zeros(len(held_out_donors))
    sst = np.zeros(len(held_out_donors))
    for j, query in enumerate(pop.queries):
        features = build_features(pop, int(query), "FULL", rng)
        scaled_train, scaled_all = _standardize(features[train], features)
        coefficients = _ridge_fit(scaled_train, centred[j][train])
        predicted = scaled_all[is_held_out] @ coefficients
        own = centred[j][is_held_out]
        cross = centred[partner[j]][is_held_out]
        for index, donor in enumerate(held_out_donors):
            rows = donors == donor
            own_sse[index] += ((own[rows] - predicted[rows]) ** 2).sum()
            cross_sse[index] += ((cross[rows] - predicted[rows]) ** 2).sum()
            sst[index] += (own[rows] ** 2).sum()
    own_score = 1.0 - own_sse / sst
    cross_score = 1.0 - cross_sse / sst
    point, low, high = paired_delta_interval(own_score, cross_score, seed + 1)
    return {
        "own_query_score": float(own_score.mean()),
        "wrong_query_score": float(cross_score.mean()),
        "delta": point,
        "delta_low": low,
        "delta_high": high,
        "fires": bool(low <= 0.0),
    }


def control_fires(result: Dict[str, Dict[str, float]], condition: str) -> bool:
    """A negative control fires when the paired delta does not clearly exceed zero."""
    return bool(result[condition]["delta_low"] <= 0.0)


def leak_detector_is_sensitive(result: Dict[str, Dict[str, float]]) -> bool:
    """The positive control: injecting the answer must raise the score."""
    return bool(result["LEAKED"]["delta_high"] < 0.0)


def main() -> int:
    for regime in REGIMES:
        print("")
        print("=== planted regime: " + regime + " ===")
        result = evaluate(regime)
        for condition in CONDITIONS:
            row = result[condition]
            print(
                f"  {condition:34s} score={row['score']:+.4f} "
                f"delta={row['delta_vs_full']:+.4f} "
                f"[{row['delta_low']:+.4f},{row['delta_high']:+.4f}] "
                f"fires={row['fires']}"
            )
        pop = build_population()
        targets = build_targets(pop, regime)
        shares = variance_decomposition(targets)
        print(
            f"  SCREEN address={shares['address_share']:.3f} "
            f"cell={shares['cell_share']:.3f} "
            f"interaction={shares['interaction_share']:.3f}"
        )
        exch = query_exchangeability(pop, targets)
        print(
            f"  QUERY_EXCHANGEABILITY own={exch['own_query_score']:+.4f} "
            f"wrong={exch['wrong_query_score']:+.4f} "
            f"delta={exch['delta']:+.4f} "
            f"[{exch['delta_low']:+.4f},{exch['delta_high']:+.4f}] "
            f"fires={exch['fires']}"
        )
    print("")
    print(
        "Synthetic planted structure only. Not biology, not FULL104, "
        "not a project result, and not permission to train."
    )
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
