"""CROSS_FITTED_SHORTCUT_PREDICTABILITY_V2 -- masking shortcut discovery and qualification.

V1 asked "is address B repeatedly in A's top-K correlation list across donors". That
definition dissolves as the address universe grows: top-10 is the top 1.7% of 600
candidates but the top 0.17% of 6,000. V2 asks the question we actually care about --
can a deliberately cheap predictor reconstruct a hidden target from visible addresses --
and tests it on donors that took no part in discovery.

Two roles are kept strictly apart:

  SCREENING   a generous RECALL instrument. It exists only because fitting every target
              against 41,238 addresses is expensive. It never defines the shortcut set.
  ATTACKER    a small, bounded, fully specified ridge. It measures how cheaply a target
              can be reconstructed. It is refit from scratch for every condition.

Forbidden as input anywhere in this module, by construction: gene symbol, biotype,
ontology, pathway, chromosome/coordinate, graph structure, disease or phenotype labels,
source/operator/donor/dataset identity as a FEATURE, QC, depth, detection, visibility,
and any hidden target value from validation donors. Donor and source codes appear only as
stratification and balancing keys.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

MODULE_ID = "CROSS_FITTED_SHORTCUT_PREDICTABILITY_V2"

FORBIDDEN_FEATURE_KINDS: Tuple[str, ...] = (
    "symbol", "biotype", "ontology", "pathway", "chromosome", "coordinate", "graph",
    "disease", "phenotype", "source", "operator", "donor", "dataset",
    "qc", "depth", "detection", "visibility", "target_value", "hidden_target",
)


class ForbiddenShortcutInputError(ValueError):
    """Raised when privileged information is offered to screening or the attacker."""


def reject_forbidden(**kwargs: object) -> None:
    bad = sorted(k for k in kwargs if any(f in k.lower() for f in FORBIDDEN_FEATURE_KINDS))
    if bad:
        raise ForbiddenShortcutInputError(
            f"forbidden shortcut input(s): {bad}; only lawful molecular values are permitted"
        )


# --------------------------------------------------------------------------- ranks
def _rank_columns(x: np.ndarray) -> np.ndarray:
    try:
        from scipy.stats import rankdata
        return rankdata(x, axis=0).astype(np.float64)
    except Exception:                                   # pragma: no cover - fallback
        order = np.argsort(x, axis=0, kind="mergesort")
        r = np.empty_like(x, dtype=np.float64)
        rows = np.arange(x.shape[0])[:, None]
        r[order, np.arange(x.shape[1])[None, :]] = rows.astype(np.float64)
        return r


def _zscore(a: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    return (a - mu) / np.where(sd > 0, sd, 1.0)


# --------------------------------------------------------------------------- screening
@dataclass(frozen=True)
class DonorBalancedScreenerV1:
    """Generous candidate generator. RECALL instrument, never authority.

    Per donor, ranks candidates by |Spearman| against the target; combines donor evidence
    with equal donor weight and equal source weight so a larger source cannot crowd out a
    shortcut that recurs in smaller ones. Continuous evidence is averaged rather than
    reduced to a per-donor yes/no, which is what made V1 scale-unstable.
    """

    candidate_budget: int

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_budget, int) or self.candidate_budget < 1:
            raise ValueError("candidate_budget must be a positive int")

    def score(
        self,
        *,
        values: np.ndarray,
        target: int,
        donor_codes: np.ndarray,
        eligible: np.ndarray,
        source_by_donor: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        n_addr = values.shape[1]
        acc = np.zeros(n_addr, dtype=np.float64)
        wsum = 0.0
        donors = np.unique(donor_codes)
        if source_by_donor is not None:
            per_src: Dict[object, int] = {}
            for d in donors:
                s = source_by_donor[int(d)]
                per_src[s] = per_src.get(s, 0) + 1
            ns = len(per_src)
            wof = {int(d): 1.0 / (ns * per_src[source_by_donor[int(d)]]) for d in donors}
        else:
            wof = {int(d): 1.0 for d in donors}
        for d in donors:
            sel = donor_codes == d
            if int(sel.sum()) < 10:
                continue
            X = values[sel]
            if X[:, target].var() <= 0:
                continue
            live = eligible & (X.var(axis=0) > 0)
            live[target] = False
            if live.sum() < 1:
                continue
            li = np.flatnonzero(live)
            R = _rank_columns(np.column_stack([X[:, target], X[:, li]]))
            R -= R.mean(0)
            sd = np.sqrt((R * R).sum(0))
            sd[sd == 0] = np.nan
            R /= sd
            rho = np.abs(R[:, 0] @ R[:, 1:])
            w = wof[int(d)]
            contrib = np.zeros(n_addr)
            contrib[li] = np.nan_to_num(rho, nan=0.0)
            acc += w * contrib
            wsum += w
        return acc / max(wsum, 1e-12)

    def candidates(self, **kw) -> np.ndarray:
        s = self.score(**kw)
        m = min(self.candidate_budget, int((s > 0).sum()))
        if m <= 0:
            return np.empty(0, dtype=np.int64)
        # deterministic: by -score then by address index
        idx = np.lexsort((np.arange(s.size), -s))[:m]
        return np.sort(idx.astype(np.int64))


# --------------------------------------------------------------------------- attacker
@dataclass(frozen=True)
class CheapRidgeAttackerV1:
    """Deliberately limited linear attacker. Every setting is explicit.

    Bounded feature count, frozen ridge penalty, train-only standardization, closed-form
    deterministic solve, no warm start, no iterative solver, no random state.
    """

    alpha: float
    max_features: int

    def __post_init__(self) -> None:
        if not (isinstance(self.alpha, float) and self.alpha > 0):
            raise ValueError("alpha must be a positive float frozen before real evaluation")
        if not isinstance(self.max_features, int) or self.max_features < 1:
            raise ValueError("max_features must be a positive int")

    def fit_predict_r2(
        self,
        *,
        values: np.ndarray,
        target: int,
        features: Sequence[int],
        train_rows: np.ndarray,
        eval_rows: np.ndarray,
        eval_donor_codes: np.ndarray,
        source_by_donor: Optional[np.ndarray] = None,
    ) -> Tuple[float, Dict[int, float]]:
        """Fit on train_rows, score on eval_rows. Returns (balanced R2, per-donor R2)."""
        feats = np.asarray(sorted(set(int(f) for f in features)), dtype=np.int64)
        if feats.size == 0:
            return 0.0, {}
        if feats.size > self.max_features:
            feats = feats[: self.max_features]
        Xtr = values[np.ix_(train_rows, feats)].astype(np.float64)
        ytr = values[train_rows, target].astype(np.float64)
        mu, sd = Xtr.mean(0), Xtr.std(0)
        ym, ys = ytr.mean(), ytr.std()
        if ys <= 0:
            return 0.0, {}
        A = _zscore(Xtr, mu, sd)
        b = (ytr - ym) / ys
        G = A.T @ A + self.alpha * len(A) * np.eye(feats.size)
        w = np.linalg.solve(G, A.T @ b)

        per_donor: Dict[int, float] = {}
        for d in np.unique(eval_donor_codes):
            rows = eval_rows[eval_donor_codes == d]
            if rows.size < 10:
                continue
            Xe = _zscore(values[np.ix_(rows, feats)].astype(np.float64), mu, sd)
            ye = (values[rows, target].astype(np.float64) - ym) / ys
            if ye.var() <= 0:
                continue
            yc = ye - ye.mean()
            pc = Xe @ w
            pc = pc - pc.mean()
            sst = float((yc * yc).sum())
            if sst <= 0:
                continue
            per_donor[int(d)] = 1.0 - float(((yc - pc) ** 2).sum()) / sst
        if not per_donor:
            return 0.0, {}
        return _balanced_mean(per_donor, source_by_donor), per_donor

    def incremental_r2(
        self,
        *,
        values: np.ndarray,
        target: int,
        features: Sequence[int],
        visible: np.ndarray,
        train_rows: np.ndarray,
        eval_rows: np.ndarray,
        eval_donor_codes: np.ndarray,
        train_donor_codes: np.ndarray,
        source_by_donor: Optional[np.ndarray] = None,
    ) -> Dict[str, object]:
        """PRIMARY shortcut statistic: predictability BEYOND global cell state.

        Returns baseline R2 (global cell state only), full R2 (baseline + candidates) and
        their difference. A universal depth/global factor inflates baseline and full
        equally, so it contributes ~0 incrementally, which is the intended behaviour.
        """
        base = global_cell_state_baseline(values, visible)
        aug = np.hstack([base, values[:, np.asarray(sorted(set(int(f) for f in features)),
                                                    dtype=np.int64)]])             if len(features) else base

        # per-donor standardisation over ALL rows involved, computed independently per donor
        all_rows = np.concatenate([train_rows, eval_rows])
        all_donor = np.concatenate([train_donor_codes, eval_donor_codes])

        def _fit_eval(M: np.ndarray) -> Tuple[float, Dict[int, float]]:
            Ms = np.empty_like(M, dtype=np.float64)
            Ms[all_rows] = donor_standardize(M[all_rows], all_donor)
            Xtr = Ms[train_rows]
            ytr = values[train_rows, target].astype(np.float64)
            ym, ys = ytr.mean(), ytr.std()
            if ys <= 0:
                return 0.0, {}
            A = Xtr
            b = (ytr - ym) / ys
            G = A.T @ A + self.alpha * len(A) * np.eye(M.shape[1])
            w = np.linalg.solve(G, A.T @ b)
            per: Dict[int, float] = {}
            for d in np.unique(eval_donor_codes):
                rows = eval_rows[eval_donor_codes == d]
                if rows.size < 10:
                    continue
                Xe = Ms[rows]
                ye = (values[rows, target].astype(np.float64) - ym) / ys
                if ye.var() <= 0:
                    continue
                # Donor-centred evaluation. The shortcut we are trying to remove is
                # within-donor, cell-to-cell interpolation. A per-donor level offset --
                # which is exactly what an operator- or source-only effect produces -- is
                # batch structure, not a local shortcut, and must not count either way.
                # Without this, an operator offset drove baseline R2 to -45 and inflated
                # the incremental gain to +44.8 with no shortcut planted at all.
                yc = ye - ye.mean()
                pc = Xe @ w
                pc = pc - pc.mean()
                sst = float((yc * yc).sum())
                if sst > 0:
                    per[int(d)] = 1.0 - float(((yc - pc) ** 2).sum()) / sst
            if not per:
                return 0.0, {}
            return _balanced_mean(per, source_by_donor), per

        r2_base, per_base = _fit_eval(base)
        if aug.shape[1] > base.shape[1]:
            if aug.shape[1] - base.shape[1] > self.max_features:
                aug = aug[:, : base.shape[1] + self.max_features]
            r2_full, per_full = _fit_eval(aug)
        else:
            r2_full, per_full = r2_base, per_base
        # PARTIAL R2: of the variance global cell state could NOT explain, how much do the
        # candidates explain? Raw incremental R2 is diluted when a strong global factor
        # dominates target variance -- a planted shortcut scored only 0.084 that way.
        denom = 1.0 - r2_base
        partial = (r2_full - r2_base) / denom if denom > 1e-9 else 0.0
        return {"baseline_r2": r2_base, "full_r2": r2_full,
                "incremental_r2": r2_full - r2_base,
                "partial_r2": float(np.clip(partial, -1.0, 1.0)),
                "per_donor_baseline": per_base, "per_donor_full": per_full,
                "evaluated_donors": len(per_full)}


def global_cell_state_baseline(values: np.ndarray, visible: np.ndarray) -> np.ndarray:
    """Summary of BROADER CELL STATE, computed from lawful visible molecular values only.

    A per-cell global factor -- sequencing depth, overall expression level -- lifts every
    address at once, so a cheap predictor can reconstruct any target from any other address
    without learning anything local. Synthetic qualification showed this yields held-out
    R2 of 0.94 with NO planted shortcut present.

    That is not the shortcut we are trying to remove. The stated goal is reconstruction
    "without having to understand broader cellular state"; a global cell factor IS broader
    cell state, so predicting from it is the legitimate signal. Shortcut strength is
    therefore measured INCREMENTALLY over this baseline.

    Uses no QC, depth, detection or visibility metadata -- only the visible values.
    """
    vis = np.flatnonzero(np.asarray(visible, dtype=bool))
    if vis.size == 0:
        return np.zeros((values.shape[0], 1))
    block = values[:, vis].astype(np.float64)
    mean = block.mean(axis=1, keepdims=True)
    sd = block.std(axis=1, keepdims=True)
    return np.hstack([mean, sd])


def donor_standardize(M: np.ndarray, donor_codes: np.ndarray) -> np.ndarray:
    """Z-score every feature WITHIN each donor, using that donor's own visible cells.

    Lawful: features are visible at inference time, so normalising visible evidence per
    donor uses no target information. Necessary: operator- and source-only effects are
    constant within a donor but shift its feature distribution, which otherwise makes a
    train-fitted standardisation catastrophically mis-scaled on held-out donors --
    measured at baseline R2 = -22 before this was applied.
    """
    out = np.empty_like(M, dtype=np.float64)
    for d in np.unique(donor_codes):
        rows = donor_codes == d
        block = M[rows].astype(np.float64)
        mu = block.mean(0)
        sd = block.std(0)
        out[rows] = (block - mu) / np.where(sd > 0, sd, 1.0)
    return out


def _balanced_mean(per_donor: Dict[int, float], source_by_donor: Optional[np.ndarray]) -> float:
    """Equal donor weight inside a source, equal weight across sources."""
    if source_by_donor is None:
        return float(np.mean(list(per_donor.values())))
    by_src: Dict[object, List[float]] = {}
    for d, v in per_donor.items():
        by_src.setdefault(source_by_donor[int(d)], []).append(v)
    return float(np.mean([float(np.mean(v)) for v in by_src.values()]))


# --------------------------------------------------------------------------- folds
def stratified_outer_folds(source_by_donor: np.ndarray, n_folds: int, namespace: str) -> np.ndarray:
    """Deterministic source-stratified outer folds; every donor validates exactly once."""
    import hashlib
    n = len(source_by_donor)
    fold = np.full(n, -1, dtype=np.int64)
    for s in np.unique(source_by_donor):
        idx = np.flatnonzero(source_by_donor == s)
        seed = int.from_bytes(hashlib.sha256(f"{namespace}|{s}".encode()).digest()[:8], "big")
        perm = np.random.default_rng(seed).permutation(idx)
        for i, d in enumerate(perm):
            fold[d] = i % n_folds
    if (fold < 0).any():
        raise ValueError("every donor must receive an outer fold")
    return fold


def inner_rotation(train_donors: np.ndarray, source_by_donor: np.ndarray,
                   namespace: str) -> Tuple[np.ndarray, np.ndarray]:
    """Source-stratified inner halves for screen/fit role rotation."""
    import hashlib
    a, b = [], []
    for s in np.unique(source_by_donor[train_donors]):
        idx = train_donors[source_by_donor[train_donors] == s]
        seed = int.from_bytes(hashlib.sha256(f"{namespace}|inner|{s}".encode()).digest()[:8], "big")
        perm = np.random.default_rng(seed).permutation(idx)
        a += list(perm[: len(perm) // 2])
        b += list(perm[len(perm) // 2:])
    return np.array(sorted(a), dtype=np.int64), np.array(sorted(b), dtype=np.int64)
