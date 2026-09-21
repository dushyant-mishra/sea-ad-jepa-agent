"""Audit D -- what estimand does the attacker's standardization define?

The current primary attacker standardizes features donor-by-donor, and that
includes each HELD-OUT donor's own feature mean and SD. From
``_standardized_components``, verbatim::

    mean_x = st.sum_x / st.n
    var_x  = np.maximum(st.sum_x2 / st.n - mean_x * mean_x, 0.0)
    sd     = np.sqrt(var_x); sd = np.where(sd > _EPS, sd, 1.0)
    gram   = (st.sum_xx - np.outer(st.sum_x, st.sum_x) / st.n) / (sd[:,None] * sd[None,:])
    rhs    = (st.sum_xy - st.sum_x * (st.sum_y / st.n)) / sd

and in ``_source_balanced_prediction_score`` those components are taken from
``stats[d]`` where ``d`` ranges over the HELD-OUT donors.

No held-out TARGET label is used, so this is not classic target leakage. It is
transductive feature adaptation, and it has a precise consequence:

    the D1 score is EXACTLY INVARIANT to any per-donor, per-feature affine
    transformation of the features.

If donor d's features are transformed x -> a*x + b with a > 0, then centring by
that donor's own mean and dividing by that donor's own SD returns numerically
identical standardized features, so ``gram``, ``rhs`` and hence ``r`` are
unchanged. A shortcut that lives purely in per-donor feature scale or offset is
therefore invisible to this attacker by construction -- not because the shortcut
is small, but because the estimand cannot express it.

That matters here because Audit A shows the normalization denominator carries a
strongly source-dependent component. To the extent that component acts as a
per-donor scale, D1 cannot see it, while a production JEPA reading absolute
normalized values could.

Three regimes compared
----------------------
``D1_CURRENT``     standardize with each donor's own mean/SD, held-out included.
``D2_TRAIN_ONLY``  standardize with mean/SD pooled over TRAINING donors only,
                   applied unchanged to held-out donors.
``D3_NO_DONOR_ADAPTATION``
                   no donor-specific recentring or rescaling at all beyond the
                   frozen production normalization; features used as-is.

Each is a different scientific question, not a different implementation of one:

* D1 asks "given this donor's internal feature geometry, does the masked
  representation still predict the target WITHIN this donor?"
* D2 asks "does a predictor fitted and scaled on training donors transfer to an
  unseen donor?"
* D3 asks "is the target predictable from absolute normalized values, including
  whatever donor- and source-level scale those carry?"

This script does not choose between them. It states what each measures and
demonstrates, on controlled fixtures, where they diverge.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

SCHEMA = "V5_FULL104_ATTACKER_STANDARDIZATION_ESTIMAND_AUDIT_V1"
_EPS = 1e-12
REGIMES = ("D1_CURRENT", "D2_TRAIN_ONLY", "D3_NO_DONOR_ADAPTATION")


def fit_ridge(x: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    """The production ridge form: A = X'X + alpha*n*I, b = X'y / scale."""
    n = x.shape[0]
    gram = x.T @ x
    rhs = x.T @ y
    scale = float(np.sqrt(max(float(y @ y) / n, 0.0)))
    if scale <= _EPS:
        return np.zeros(x.shape[1], dtype=np.float64)
    a = gram + (alpha * n) * np.eye(x.shape[1], dtype=np.float64)
    return np.linalg.solve(a, rhs / scale)


def _standardize(x: np.ndarray, mean: np.ndarray, sd: np.ndarray) -> np.ndarray:
    sd = np.where(sd > _EPS, sd, 1.0)
    return (x - mean) / sd


def score_regime(
    regime: str,
    *,
    x: np.ndarray,
    y: np.ndarray,
    donor: np.ndarray,
    source: np.ndarray,
    train_donors: np.ndarray,
    heldout_donors: np.ndarray,
    alpha: float = 0.01,
) -> float:
    """Source-balanced mean of squared within-donor centred prediction correlation.

    The scoring shape mirrors the frozen primary score: per held-out donor a
    within-donor centred correlation, squared, averaged within source, then
    averaged across sources. Only the STANDARDIZATION differs between regimes.
    """
    train_mask = np.isin(donor, train_donors)
    if regime == "D2_TRAIN_ONLY":
        mean_tr = x[train_mask].mean(axis=0)
        sd_tr = x[train_mask].std(axis=0)

    # --- fit weights on training donors, standardized per the regime
    parts_x, parts_y = [], []
    for d in train_donors:
        sel = donor == d
        xd, yd = x[sel], y[sel]
        if regime == "D1_CURRENT":
            xs = _standardize(xd, xd.mean(axis=0), xd.std(axis=0))
        elif regime == "D2_TRAIN_ONLY":
            xs = _standardize(xd, mean_tr, sd_tr)
        else:
            xs = xd
        parts_x.append(xs)
        parts_y.append(yd - yd.mean())
    w = fit_ridge(np.vstack(parts_x), np.concatenate(parts_y), alpha)

    # --- evaluate on held-out donors
    per_source: dict[object, list[float]] = {}
    for d in heldout_donors:
        sel = donor == d
        xd, yd = x[sel], y[sel]
        if regime == "D1_CURRENT":
            # The held-out donor's OWN mean/SD. This is the transductive step.
            xs = _standardize(xd, xd.mean(axis=0), xd.std(axis=0))
        elif regime == "D2_TRAIN_ONLY":
            xs = _standardize(xd, mean_tr, sd_tr)
        else:
            xs = xd
        pred = xs @ w
        yc = yd - yd.mean()
        pc = pred - pred.mean()
        den = float(np.sqrt(float(yc @ yc) * float(pc @ pc)))
        r = 0.0 if den <= _EPS else float(yc @ pc) / den
        per_source.setdefault(int(source[np.flatnonzero(sel)[0]]), []).append(r * r)
    return float(np.mean([float(np.mean(v)) for v in per_source.values()]))


# --------------------------------------------------------------------------- #
# Fixtures. Geometry mirrors the real design: many cells per donor, a modest
# feature count, donors nested in sources, donor-honest folds.
# --------------------------------------------------------------------------- #

def make_fixture(
    *,
    kind: str,
    n_donors: int = 24,
    cells_per_donor: int = 400,
    n_features: int = 32,
    seed: int = 20260920,
) -> dict:
    rng = np.random.default_rng(seed)
    donor = np.repeat(np.arange(n_donors), cells_per_donor)
    source = (np.arange(n_donors) % 3)[donor]
    n = donor.size

    x = rng.normal(size=(n, n_features))
    beta = rng.normal(size=n_features) / np.sqrt(n_features)

    if kind == "within_donor_signal":
        # Genuine within-donor structure: the target is predictable from the
        # features inside every donor. Every regime should detect this.
        y = x @ beta + 0.5 * rng.normal(size=n)

    elif kind == "null":
        y = rng.normal(size=n)

    elif kind == "donor_scale_nuisance":
        # The shortcut lives ENTIRELY in per-donor feature scale and offset,
        # which also encodes source. There is no within-donor covariance
        # between features and target beyond noise.
        y = rng.normal(size=n)
        for d in range(n_donors):
            sel = donor == d
            scale = 1.0 + 0.8 * (d % 3)          # source-linked scale
            offset = 2.0 * (d % 3)               # source-linked offset
            x[sel] = x[sel] * scale + offset
            y[sel] = y[sel] + 3.0 * (d % 3)      # target shares the donor-level offset

    elif kind == "within_donor_signal_plus_donor_scale":
        y = x @ beta + 0.5 * rng.normal(size=n)
        for d in range(n_donors):
            sel = donor == d
            x[sel] = x[sel] * (1.0 + 0.8 * (d % 3)) + 2.0 * (d % 3)

    elif kind in ("per_cell_denominator_channel", "per_cell_denominator_channel_no_target_link"):
        # Models the Audit A channel at REAL geometry, which the earlier
        # mean-zero Gaussian version could not: counts are sparse and
        # NON-NEGATIVE, and the frozen normalization is applied literally.
        #
        #   feature = log1p(raw * 10000 / L),  L = ledger_mass / (1 - outside)
        #
        # With non-negative counts the per-cell denominator shifts the MEAN of
        # every feature, so a linear predictor can express it. With mean-zero
        # features it cannot, which is why the earlier fixture detected nothing
        # and was not evidence either way.
        counts = rng.poisson(0.9, size=(n, n_features)).astype(np.float64)
        counts[rng.random((n, n_features)) < 0.83] = 0.0      # ~83% measured zeros
        ledger = counts.sum(axis=1) + rng.integers(400, 4000, size=n)
        outside = np.array([0.0, 0.040, 0.015])[source]        # cf. HVS / SEA_AD / NPH52
        outside = np.clip(outside + rng.normal(scale=0.004, size=n), 0.0, 0.5)
        library = ledger / (1.0 - outside)
        x = np.log1p(counts * (10000.0 / library[:, None]))
        if kind == "per_cell_denominator_channel":
            # The masked target is itself a normalized address, so it carries the
            # same denominator. This is the actual mechanism, not an analogy.
            t_counts = rng.poisson(1.2, size=n)
            t_counts[rng.random(n) < 0.83] = 0
            y = np.log1p(t_counts * (10000.0 / library))
        else:
            # Negative control: identical denominator structure, target
            # independent of it. Nothing should exceed the null floor.
            y = rng.normal(size=n)

    else:
        raise ValueError(f"unknown fixture kind {kind!r}")

    fold = np.arange(n_donors) % 4
    return {"x": x, "y": y, "donor": donor, "source": source,
            "fold_by_donor": fold, "n_donors": n_donors, "kind": kind}


def evaluate(fixture: dict, alpha: float = 0.01) -> dict[str, dict]:
    """Unconditional across all four folds; every fold in the denominator."""
    out: dict[str, dict] = {}
    for regime in REGIMES:
        per_fold = []
        finite = 0
        for f in range(4):
            heldout = np.flatnonzero(fixture["fold_by_donor"] == f)
            train = np.flatnonzero(fixture["fold_by_donor"] != f)
            s = score_regime(
                regime, x=fixture["x"], y=fixture["y"], donor=fixture["donor"],
                source=fixture["source"], train_donors=train, heldout_donors=heldout,
                alpha=alpha,
            )
            per_fold.append(s)
            finite += int(np.isfinite(s))
        arr = np.asarray(per_fold, dtype=np.float64)
        out[regime] = {
            "folds_attempted": 4,
            "folds_finite": finite,
            "mean_score": float(np.mean(arr)),
            "min_score": float(np.min(arr)),
            "max_score": float(np.max(arr)),
            "per_fold": [float(v) for v in arr],
        }
    return out


def affine_invariance_check(seed: int = 4242) -> dict:
    """Demonstrate D1's exact invariance to per-donor affine feature transforms.

    This is the load-bearing claim of the audit, so it is measured rather than
    argued: the same fixture is scored before and after a per-donor affine
    transformation of the features.
    """
    base = make_fixture(kind="within_donor_signal", seed=seed)
    moved = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in base.items()}
    rng = np.random.default_rng(seed + 1)
    for d in range(base["n_donors"]):
        sel = moved["donor"] == d
        a = float(np.exp(rng.normal(scale=0.5)))
        b = float(rng.normal(scale=3.0))
        moved["x"][sel] = moved["x"][sel] * a + b

    before = evaluate(base)
    after = evaluate(moved)
    return {
        regime: {
            "before": before[regime]["mean_score"],
            "after": after[regime]["mean_score"],
            "absolute_change": abs(before[regime]["mean_score"] - after[regime]["mean_score"]),
        }
        for regime in REGIMES
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    kinds = ("null", "within_donor_signal", "donor_scale_nuisance",
             "within_donor_signal_plus_donor_scale",
             "per_cell_denominator_channel",
             "per_cell_denominator_channel_no_target_link")
    results = {kind: evaluate(make_fixture(kind=kind)) for kind in kinds}
    invariance = affine_invariance_check()

    rows = []
    for kind, per_regime in results.items():
        for regime, stats in per_regime.items():
            rows.append({
                "fixture": kind, "regime": regime,
                "folds_attempted": stats["folds_attempted"],
                "folds_finite": stats["folds_finite"],
                "mean_score": stats["mean_score"],
                "min_score": stats["min_score"],
                "max_score": stats["max_score"],
            })
    path = args.out_dir / "ATTACKER_STANDARDIZATION_FIXTURE_RESULTS.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "schema": SCHEMA,
        "regimes": {
            "D1_CURRENT": "standardize with each donor's own mean/SD, held-out donor included "
                          "(transductive feature adaptation; no held-out TARGET label is used)",
            "D2_TRAIN_ONLY": "standardize with mean/SD pooled over training donors only",
            "D3_NO_DONOR_ADAPTATION": "no donor-specific recentring or rescaling beyond the "
                                      "frozen production normalization",
        },
        "estimands": {
            "D1_CURRENT": "within-donor predictability given that donor's own feature geometry",
            "D2_TRAIN_ONLY": "transfer of a train-fitted, train-scaled predictor to an unseen donor",
            "D3_NO_DONOR_ADAPTATION": "predictability from absolute normalized values, including "
                                      "donor- and source-level scale",
        },
        "fixture_results": results,
        "affine_invariance_check": invariance,
        "regime_selected": None,
        "canonical_attacker_changed": False,
        "training_authorized": False,
    }
    (args.out_dir / "ATTACKER_STANDARDIZATION_CALIBRATION_RESULTS.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fixture_results": results, "affine_invariance": invariance}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
