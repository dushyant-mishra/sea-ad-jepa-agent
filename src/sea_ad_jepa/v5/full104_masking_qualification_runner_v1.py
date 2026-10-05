"""Canonical primary-attacker runner for prospective FULL104 masking qualification.

The runner is intentionally data-path agnostic.  Callers supply already bound arrays
and explicit authority objects.  Partner selection uses outer-training donors only;
all policy arms are evaluated with the same ridge expression-proxy attacker and the
same source-balanced donor-centered correlation-squared score.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable, Sequence

import numpy as np
import scipy.sparse as sp


_EPS = 1e-12
_METHODS = (
    "UNIFORM_RANDOM",
    "TOP8_CORRELATION",
    "RIDGE8_CONDITIONAL",
    "PREFIX3_SELECTIVE",
)


def _as_int_vector(value: Any, name: str) -> np.ndarray:
    out = np.asarray(value)
    if out.ndim != 1 or not np.issubdtype(out.dtype, np.integer):
        raise ValueError(f"{name} must be a one-dimensional integer array")
    return out.astype(np.int64, copy=False)


def _seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


@dataclass(frozen=True)
class QualificationArrays:
    X: sp.spmatrix
    donor_code: np.ndarray
    source_by_donor: np.ndarray
    fold_by_donor: np.ndarray
    universe_cols: np.ndarray
    target_cols: np.ndarray
    target_ids: np.ndarray

    def validate(self) -> None:
        if not sp.issparse(self.X) or self.X.ndim != 2:
            raise ValueError("X must be a two-dimensional scipy sparse matrix")
        donor = _as_int_vector(self.donor_code, "donor_code")
        if donor.size != self.X.shape[0] or donor.size == 0 or donor.min() < 0:
            raise ValueError("donor_code must provide one nonnegative donor index per cell")
        source = np.asarray(self.source_by_donor, dtype=object)
        folds = _as_int_vector(self.fold_by_donor, "fold_by_donor")
        if source.ndim != 1 or source.size != folds.size or source.size == 0:
            raise ValueError("source_by_donor and fold_by_donor must align")
        if donor.max() >= source.size:
            raise ValueError("donor_code references a donor outside donor metadata")
        universe = _as_int_vector(self.universe_cols, "universe_cols")
        targets = _as_int_vector(self.target_cols, "target_cols")
        target_ids = np.asarray(self.target_ids, dtype=object)
        if universe.size < 2 or np.unique(universe).size != universe.size:
            raise ValueError("universe_cols must contain at least two unique columns")
        if universe.min() < 0 or universe.max() >= self.X.shape[1]:
            raise ValueError("universe_cols contains an out-of-range matrix column")
        if targets.size == 0 or np.unique(targets).size != targets.size:
            raise ValueError("target_cols must be nonempty and unique")
        if target_ids.ndim != 1 or target_ids.size != targets.size:
            raise ValueError("target_ids must align one-to-one with target_cols")
        if not set(map(int, targets)).issubset(set(map(int, universe))):
            raise ValueError("every target must belong to universe_cols")


def infer_strict_measured_scalar_common_core(
    observation_state: np.ndarray,
    *,
    expected_size: int,
) -> tuple[int, np.ndarray]:
    """Infer the unique nonzero observation code yielding the frozen terminal size.

    A strict common-core address has the same nonzero observation-state code in every
    row.  The frozen cardinality is used only to identify the code; if more than one
    code produces that cardinality the function fails closed.
    """

    obs = np.asarray(observation_state)
    if obs.ndim != 2 or obs.shape[0] == 0 or obs.shape[1] == 0:
        raise ValueError("observation_state must be a nonempty two-dimensional array")
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size < 1:
        raise ValueError("expected_size must be a positive integer")
    matches: list[tuple[int, np.ndarray]] = []
    for raw_code in np.unique(obs):
        code = int(raw_code)
        if code == 0:
            continue
        indices = np.flatnonzero(np.all(obs == raw_code, axis=0)).astype(np.int64)
        if indices.size == expected_size:
            matches.append((code, indices))
    if len(matches) != 1:
        raise ValueError("strict measured-scalar common-core code is not unique at the frozen terminal cardinality")
    return matches[0]


def apply_burden_preserving_swaps(
    *,
    base_mask: Iterable[int],
    target_col: int,
    targeted_cols: Sequence[int],
    removable_order: Sequence[int],
) -> set[int]:
    """Swap targeted partners into a common-random base mask with exact cardinality."""

    base = {int(x) for x in base_mask}
    target = int(target_col)
    if target not in base:
        raise ValueError("base_mask must contain target_col")
    requested: list[int] = []
    seen: set[int] = set()
    for raw in targeted_cols:
        col = int(raw)
        if col == target:
            continue
        if col not in seen:
            seen.add(col)
            requested.append(col)
    additions = [col for col in requested if col not in base]
    removable: list[int] = []
    seen_removable: set[int] = set()
    requested_set = set(requested)
    for raw in removable_order:
        col = int(raw)
        if col in seen_removable:
            continue
        seen_removable.add(col)
        if col in base and col != target and col not in requested_set:
            removable.append(col)
    if len(removable) < len(additions):
        raise ValueError("insufficient removable base-mask addresses for exact burden-preserving swaps")
    out = set(base)
    for add, remove in zip(additions, removable[: len(additions)]):
        out.remove(remove)
        out.add(add)
    if len(out) != len(base) or target not in out:
        raise ValueError("burden-preserving swap violated exact cardinality or target masking")
    return out


def source_balanced_donor_centered_prediction_correlation_squared(
    y_true: np.ndarray,
    prediction: np.ndarray,
    donor_code: np.ndarray,
    source_by_donor: np.ndarray,
) -> float:
    """Mean donor-centered prediction correlation squared, equal-weighted by source."""

    y = np.asarray(y_true, dtype=np.float64).reshape(-1)
    p = np.asarray(prediction, dtype=np.float64).reshape(-1)
    donor = _as_int_vector(donor_code, "donor_code")
    source = np.asarray(source_by_donor, dtype=object)
    if y.size != p.size or y.size != donor.size or y.size == 0:
        raise ValueError("score inputs must be nonempty and cell-aligned")
    if donor.min() < 0 or donor.max() >= source.size:
        raise ValueError("donor_code references donor metadata out of range")
    by_source: dict[object, list[float]] = {}
    for d in np.unique(donor):
        ix = donor == d
        yy = y[ix] - float(np.mean(y[ix]))
        pp = p[ix] - float(np.mean(p[ix]))
        den = float(np.sqrt(np.dot(yy, yy) * np.dot(pp, pp)))
        r = 0.0 if den <= _EPS else float(np.dot(yy, pp) / den)
        by_source.setdefault(source[int(d)], []).append(r * r)
    if not by_source:
        raise ValueError("score requires at least one donor")
    return float(np.mean([np.mean(values) for values in by_source.values()]))


def _rows_for_donors(donor_code: np.ndarray, donors: np.ndarray) -> np.ndarray:
    return np.flatnonzero(np.isin(donor_code, donors)).astype(np.int64)


def _source_balanced_abs_corr_scores(
    arrays: QualificationArrays,
    *,
    donors: np.ndarray,
    target_col: int,
    candidate_cols: np.ndarray,
) -> np.ndarray:
    """Training-only source-balanced mean absolute within-donor correlations."""

    cols = _as_int_vector(candidate_cols, "candidate_cols")
    if cols.size == 0:
        return np.empty(0, dtype=np.float64)
    source = np.asarray(arrays.source_by_donor, dtype=object)
    per_source: dict[object, list[np.ndarray]] = {}
    X = arrays.X.tocsr()
    for raw_d in donors:
        d = int(raw_d)
        rows = np.flatnonzero(arrays.donor_code == d)
        if rows.size == 0:
            continue
        block = X[rows, :][:, cols].astype(np.float64)
        y = X[rows, int(target_col)].toarray().reshape(-1).astype(np.float64)
        yc = y - float(np.mean(y))
        sy2 = float(np.dot(yc, yc))
        if sy2 <= _EPS:
            corr = np.zeros(cols.size, dtype=np.float64)
        else:
            sums = np.asarray(block.sum(axis=0)).reshape(-1)
            sums2 = np.asarray(block.power(2).sum(axis=0)).reshape(-1)
            sx2 = np.maximum(sums2 - (sums * sums) / rows.size, 0.0)
            num = np.asarray(block.T @ yc).reshape(-1)
            den = np.sqrt(sx2 * sy2)
            corr = np.divide(np.abs(num), den, out=np.zeros_like(num), where=den > _EPS)
        per_source.setdefault(source[d], []).append(corr)
    if not per_source:
        raise ValueError("correlation screening requires training donors")
    source_means = [np.mean(np.vstack(values), axis=0) for values in per_source.values()]
    return np.mean(np.vstack(source_means), axis=0)


def _rank_by_score(cols: np.ndarray, scores: np.ndarray, count: int) -> np.ndarray:
    if cols.size != scores.size:
        raise ValueError("columns and scores must align")
    if count < 0:
        raise ValueError("count cannot be negative")
    order = np.lexsort((cols, -scores))
    return cols[order[: min(count, cols.size)]]


def _standardized_features(
    arrays: QualificationArrays,
    *,
    rows: np.ndarray,
    cols: np.ndarray,
) -> np.ndarray:
    if cols.size == 0:
        return np.empty((rows.size, 0), dtype=np.float64)
    out = arrays.X.tocsr()[rows, :][:, cols].toarray().astype(np.float64)
    row_donor = arrays.donor_code[rows]
    for d in np.unique(row_donor):
        ix = row_donor == d
        block = out[ix]
        mean = np.mean(block, axis=0)
        sd = np.std(block, axis=0)
        out[ix] = (block - mean) / np.where(sd > _EPS, sd, 1.0)
    return out


def _center_target_by_donor(arrays: QualificationArrays, *, rows: np.ndarray, target_col: int) -> np.ndarray:
    y = arrays.X.tocsr()[rows, int(target_col)].toarray().reshape(-1).astype(np.float64)
    row_donor = arrays.donor_code[rows]
    for d in np.unique(row_donor):
        ix = row_donor == d
        y[ix] -= float(np.mean(y[ix]))
    return y


def _fit_ridge_weights(
    arrays: QualificationArrays,
    *,
    donors: np.ndarray,
    target_col: int,
    feature_cols: np.ndarray,
    alpha: float,
) -> np.ndarray:
    rows = _rows_for_donors(arrays.donor_code, donors)
    if rows.size == 0:
        raise ValueError("ridge fit requires training rows")
    features = _standardized_features(arrays, rows=rows, cols=feature_cols)
    y = _center_target_by_donor(arrays, rows=rows, target_col=target_col)
    scale = float(np.std(y))
    if scale <= _EPS or feature_cols.size == 0:
        return np.zeros(feature_cols.size, dtype=np.float64)
    y = y / scale
    gram = features.T @ features + (alpha * rows.size) * np.eye(feature_cols.size, dtype=np.float64)
    return np.linalg.solve(gram, features.T @ y)


def _ridge_primary_score(
    arrays: QualificationArrays,
    *,
    train_donors: np.ndarray,
    heldout_donors: np.ndarray,
    target_col: int,
    mask: set[int],
    feature_count: int,
    alpha: float,
) -> float:
    visible = np.asarray(
        [int(col) for col in arrays.universe_cols if int(col) not in mask and int(col) != int(target_col)],
        dtype=np.int64,
    )
    if visible.size == 0:
        return 0.0
    screen = _source_balanced_abs_corr_scores(
        arrays,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=visible,
    )
    features = _rank_by_score(visible, screen, feature_count)
    weights = _fit_ridge_weights(
        arrays,
        donors=train_donors,
        target_col=target_col,
        feature_cols=features,
        alpha=alpha,
    )
    heldout_rows = _rows_for_donors(arrays.donor_code, heldout_donors)
    if heldout_rows.size == 0:
        raise ValueError("primary score requires heldout rows")
    heldout_features = _standardized_features(arrays, rows=heldout_rows, cols=features)
    prediction = heldout_features @ weights
    y = arrays.X.tocsr()[heldout_rows, int(target_col)].toarray().reshape(-1).astype(np.float64)
    return source_balanced_donor_centered_prediction_correlation_squared(
        y,
        prediction,
        arrays.donor_code[heldout_rows],
        arrays.source_by_donor,
    )


def _top_partners(
    arrays: QualificationArrays,
    *,
    train_donors: np.ndarray,
    target_col: int,
    cap: int,
) -> tuple[int, ...]:
    candidates = np.asarray([int(c) for c in arrays.universe_cols if int(c) != int(target_col)], dtype=np.int64)
    scores = _source_balanced_abs_corr_scores(
        arrays,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=candidates,
    )
    return tuple(map(int, _rank_by_score(candidates, scores, cap)))


def _ridge_partners(
    arrays: QualificationArrays,
    *,
    train_donors: np.ndarray,
    target_col: int,
    candidate_pool_count: int,
    cap: int,
    alpha: float,
) -> tuple[int, ...]:
    candidates = np.asarray([int(c) for c in arrays.universe_cols if int(c) != int(target_col)], dtype=np.int64)
    screen = _source_balanced_abs_corr_scores(
        arrays,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=candidates,
    )
    pool = _rank_by_score(candidates, screen, candidate_pool_count)
    weights = _fit_ridge_weights(
        arrays,
        donors=train_donors,
        target_col=target_col,
        feature_cols=pool,
        alpha=alpha,
    )
    order = np.lexsort((pool, -np.abs(weights)))
    return tuple(map(int, pool[order[: min(cap, pool.size)]]))


def _inner_donor_groups(
    arrays: QualificationArrays,
    *,
    train_donors: np.ndarray,
    global_seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    groups: list[list[int]] = [[], [], []]
    sources = np.asarray(arrays.source_by_donor, dtype=object)
    for source in sorted(set(sources[train_donors]), key=str):
        donors = train_donors[sources[train_donors] == source]
        rng = np.random.default_rng(_seed("V5_PREFIX3_INNER", global_seed, source))
        perm = rng.permutation(donors)
        for index, donor in enumerate(perm):
            groups[index % 3].append(int(donor))
    if any(len(group) == 0 for group in groups):
        return None
    return tuple(np.asarray(sorted(group), dtype=np.int64) for group in groups)  # type: ignore[return-value]


def _single_partner_score(
    arrays: QualificationArrays,
    *,
    donors: np.ndarray,
    target_col: int,
    partner_col: int,
) -> float:
    rows = _rows_for_donors(arrays.donor_code, donors)
    y = arrays.X.tocsr()[rows, int(target_col)].toarray().reshape(-1).astype(np.float64)
    p = arrays.X.tocsr()[rows, int(partner_col)].toarray().reshape(-1).astype(np.float64)
    return source_balanced_donor_centered_prediction_correlation_squared(
        y,
        p,
        arrays.donor_code[rows],
        arrays.source_by_donor,
    )


def _prefix3_partners(
    arrays: QualificationArrays,
    *,
    train_donors: np.ndarray,
    target_col: int,
    candidate_count: int,
    cap: int,
    floor: float,
    reduction: float,
    global_seed: int,
) -> tuple[int, ...]:
    groups = _inner_donor_groups(arrays, train_donors=train_donors, global_seed=global_seed)
    if groups is None:
        return ()
    universe = np.asarray([int(c) for c in arrays.universe_cols if int(c) != int(target_col)], dtype=np.int64)
    selected_sets: list[tuple[int, ...]] = []
    for rotation in range(3):
        screen_donors = groups[rotation]
        rank_donors = groups[(rotation + 1) % 3]
        validate_donors = groups[(rotation + 2) % 3]
        screen = _source_balanced_abs_corr_scores(
            arrays,
            donors=screen_donors,
            target_col=target_col,
            candidate_cols=universe,
        )
        candidates = _rank_by_score(universe, screen, candidate_count)
        if candidates.size == 0:
            selected_sets.append(())
            continue

        def remaining_proxy_score(remaining: np.ndarray) -> float:
            if remaining.size == 0:
                return 0.0
            rank_score = _source_balanced_abs_corr_scores(
                arrays,
                donors=rank_donors,
                target_col=target_col,
                candidate_cols=remaining,
            )
            best = int(_rank_by_score(remaining, rank_score, 1)[0])
            return _single_partner_score(
                arrays,
                donors=validate_donors,
                target_col=target_col,
                partner_col=best,
            )

        baseline = remaining_proxy_score(candidates)
        if baseline < floor:
            selected_sets.append(())
            continue
        chosen: tuple[int, ...] = ()
        for k in range(1, min(cap, candidates.size) + 1):
            remaining = candidates[k:]
            if remaining_proxy_score(remaining) <= (1.0 - reduction) * baseline:
                chosen = tuple(map(int, candidates[:k]))
                break
        selected_sets.append(chosen)

    support: dict[int, int] = {}
    for selected in selected_sets:
        for col in set(selected):
            support[col] = support.get(col, 0) + 1
    if not support:
        return ()
    items = np.asarray(sorted(support), dtype=np.int64)
    evidence = _source_balanced_abs_corr_scores(
        arrays,
        donors=train_donors,
        target_col=target_col,
        candidate_cols=items,
    )
    support_count = np.asarray([support[int(col)] for col in items], dtype=np.int64)
    order = np.lexsort((items, -evidence, -support_count))
    return tuple(map(int, items[order[: min(cap, items.size)]]))


def _base_uniform_mask(
    universe_cols: np.ndarray,
    *,
    target_col: int,
    co_mask_count: int,
    fold_index: int,
    target_id: object,
    global_seed: int,
) -> set[int]:
    universe = _as_int_vector(universe_cols, "universe_cols")
    pool = universe[universe != int(target_col)]
    if co_mask_count < 0 or co_mask_count > pool.size:
        raise ValueError("co-mask burden is infeasible for the supplied universe")
    rng = np.random.default_rng(
        _seed("V5_COMMON_RANDOM_BASE_MASK", global_seed, fold_index, target_id, universe.size)
    )
    chosen = rng.choice(pool, size=co_mask_count, replace=False) if co_mask_count else np.empty(0, dtype=np.int64)
    return {int(target_col), *map(int, chosen)}


def _removable_order(
    base_mask: set[int],
    *,
    target_col: int,
    fold_index: int,
    target_id: object,
    global_seed: int,
) -> tuple[int, ...]:
    candidates = [int(c) for c in base_mask if int(c) != int(target_col)]
    candidates.sort(key=lambda c: hashlib.sha256(
        f"V5_MASK_REMOVE|{global_seed}|{fold_index}|{target_id}|{c}".encode("utf-8")
    ).digest())
    return tuple(candidates)


def run_primary_fold(
    *,
    arrays: QualificationArrays,
    fold_index: int,
    parameters: Any,
    evidence_budget: Any,
    global_seed: int,
) -> list[dict[str, Any]]:
    """Run the four prospectively declared primary policy arms for one outer fold."""

    arrays.validate()
    parameters.validate()
    evidence_budget.validate()
    if isinstance(fold_index, bool) or not isinstance(fold_index, int):
        raise ValueError("fold_index must be an integer")
    donor = _as_int_vector(arrays.donor_code, "donor_code")
    folds = _as_int_vector(arrays.fold_by_donor, "fold_by_donor")
    heldout_donors = np.flatnonzero(folds == fold_index).astype(np.int64)
    train_donors = np.flatnonzero(folds != fold_index).astype(np.int64)
    if heldout_donors.size == 0 or train_donors.size == 0:
        raise ValueError("outer fold must contain both training and heldout donors")
    if not np.all(np.isin(np.unique(donor), np.arange(folds.size))):
        raise ValueError("cell donor codes do not align with donor fold metadata")

    eligible_non_target = int(arrays.universe_cols.size - 1)
    co_mask_count = int(evidence_budget.mask_count(eligible_non_target))
    if int(parameters.targeted_partner_cap) > co_mask_count:
        raise ValueError("targeted partner cap exceeds the authorized co-mask burden")

    rows: list[dict[str, Any]] = []
    for target_index, (raw_target, target_id) in enumerate(zip(arrays.target_cols, arrays.target_ids)):
        target_col = int(raw_target)
        base_mask = _base_uniform_mask(
            arrays.universe_cols,
            target_col=target_col,
            co_mask_count=co_mask_count,
            fold_index=fold_index,
            target_id=target_id,
            global_seed=int(global_seed),
        )
        uniform_score = _ridge_primary_score(
            arrays,
            train_donors=train_donors,
            heldout_donors=heldout_donors,
            target_col=target_col,
            mask=base_mask,
            feature_count=int(parameters.ridge_score_feature_count),
            alpha=float(parameters.ridge_alpha),
        )
        policy_targets = {
            "UNIFORM_RANDOM": (),
            "TOP8_CORRELATION": _top_partners(
                arrays,
                train_donors=train_donors,
                target_col=target_col,
                cap=int(parameters.targeted_partner_cap),
            ),
            "RIDGE8_CONDITIONAL": _ridge_partners(
                arrays,
                train_donors=train_donors,
                target_col=target_col,
                candidate_pool_count=int(parameters.ridge_candidate_pool_count),
                cap=int(parameters.targeted_partner_cap),
                alpha=float(parameters.ridge_alpha),
            ),
            "PREFIX3_SELECTIVE": _prefix3_partners(
                arrays,
                train_donors=train_donors,
                target_col=target_col,
                candidate_count=int(parameters.prefix_candidate_count),
                cap=int(parameters.targeted_partner_cap),
                floor=float(parameters.prefix_floor),
                reduction=float(parameters.prefix_reduction),
                global_seed=int(global_seed),
            ),
        }
        removable = _removable_order(
            base_mask,
            target_col=target_col,
            fold_index=fold_index,
            target_id=target_id,
            global_seed=int(global_seed),
        )
        for method in _METHODS:
            targeted = tuple(map(int, policy_targets[method]))
            if method == "UNIFORM_RANDOM":
                mask = set(base_mask)
                score = uniform_score
            else:
                mask = apply_burden_preserving_swaps(
                    base_mask=base_mask,
                    target_col=target_col,
                    targeted_cols=targeted,
                    removable_order=removable,
                )
                score = _ridge_primary_score(
                    arrays,
                    train_donors=train_donors,
                    heldout_donors=heldout_donors,
                    target_col=target_col,
                    mask=mask,
                    feature_count=int(parameters.ridge_score_feature_count),
                    alpha=float(parameters.ridge_alpha),
                )
            effective = len([col for col in targeted if col not in base_mask and col != target_col])
            rows.append(
                {
                    "fold": int(fold_index),
                    "target_index": int(target_index),
                    "target_col": target_col,
                    "target_id": target_id,
                    "method": method,
                    "primary_attacker_id": parameters.primary_attacker_id,
                    "primary_score_id": parameters.primary_score_id,
                    "score": float(score),
                    "uniform_score": float(uniform_score),
                    "delta": float(uniform_score - score),
                    "targeted_cols": targeted,
                    "targeted_n": len(targeted),
                    "effective_targeted_n": int(effective),
                    "mask_cardinality": len(mask),
                    "uniform_mask_cardinality": len(base_mask),
                }
            )
    return rows
