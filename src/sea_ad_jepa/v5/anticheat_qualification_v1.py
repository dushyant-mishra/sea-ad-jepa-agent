"""Executable anti-cheat qualification primitives for prospective Teacher/Student V5.

Trainer-independent, pathology-blind qualification helpers.  These routines
measure shortcut availability, split integrity, proposal weighting, latent
collapse, response curves, donor memorization, and hardware replay.  They do
not authorize training or protected-data access.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any, Mapping, Sequence

import numpy as np

PASS = "PASS"
FAIL = "FAIL"
BLOCKED = "BLOCKED"
NOT_ESTIMABLE = "NOT_ESTIMABLE"


class AntiCheatQualificationError(RuntimeError):
    pass


def _one(values: Sequence[Any] | np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(values)
    if arr.ndim != 1 or arr.size == 0:
        raise AntiCheatQualificationError(f"{name} must be a nonempty 1-D array")
    return arr


def _finite2(values: Sequence[Sequence[float]] | np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < 2 or arr.shape[1] < 1 or not np.isfinite(arr).all():
        raise AntiCheatQualificationError(f"{name} must be finite [rows,features]")
    return arr


def stable_hash_u64(value: Any, *, salt: str) -> int:
    if not isinstance(salt, str) or not salt:
        raise AntiCheatQualificationError("salt must be nonempty")
    payload = (salt + "\0" + str(value)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def deterministic_group_folds(groups: Sequence[Any] | np.ndarray, *, n_folds: int, salt: str) -> np.ndarray:
    g = _one(groups, "groups").astype(str)
    if isinstance(n_folds, bool) or not isinstance(n_folds, int) or n_folds < 2:
        raise AntiCheatQualificationError("n_folds must be integer >=2")
    mapping = {x: stable_hash_u64(x, salt=salt) % n_folds for x in np.unique(g)}
    return np.asarray([mapping[x] for x in g], dtype=np.int64)


def balanced_accuracy(y_true: Sequence[Any] | np.ndarray, y_pred: Sequence[Any] | np.ndarray) -> float:
    yt = _one(y_true, "y_true").astype(str)
    yp = _one(y_pred, "y_pred").astype(str)
    if yt.shape != yp.shape:
        raise AntiCheatQualificationError("y_true/y_pred mismatch")
    return float(np.mean([np.mean(yp[yt == c] == c) for c in np.unique(yt)]))


def categorical_purity(feature: Sequence[Any] | np.ndarray, label: Sequence[Any] | np.ndarray) -> dict[str, Any]:
    x = _one(feature, "feature").astype(str)
    y = _one(label, "label").astype(str)
    if x.shape != y.shape:
        raise AntiCheatQualificationError("feature/label mismatch")
    correct = 0
    for value in np.unique(x):
        _, counts = np.unique(y[x == value], return_counts=True)
        correct += int(counts.max())
    classes = int(np.unique(y).size)
    return {
        "rows": int(len(y)),
        "feature_levels": int(np.unique(x).size),
        "label_classes": classes,
        "weighted_purity": float(correct / len(y)),
        "balanced_chance": float(1.0 / classes),
    }


def _majority(y: np.ndarray) -> str:
    values, counts = np.unique(y.astype(str), return_counts=True)
    order = np.lexsort((values, -counts))
    return str(values[order[0]])


def _equal_prior_lookup(feature: np.ndarray, labels: np.ndarray) -> dict[str, str]:
    f = feature.astype(str)
    y = labels.astype(str)
    classes, counts = np.unique(y, return_counts=True)
    denominators = {str(c): int(n) for c, n in zip(classes, counts)}
    out: dict[str, str] = {}
    for level in np.unique(f):
        mask = f == level
        score = [(float(np.sum(y[mask] == c)) / denominators[str(c)], str(c)) for c in classes]
        score.sort(key=lambda x: (-x[0], x[1]))
        out[str(level)] = score[0][1]
    return out


def categorical_group_holdout_attack(
    feature: Sequence[Any] | np.ndarray,
    label: Sequence[Any] | np.ndarray,
    groups: Sequence[Any] | np.ndarray,
    *,
    n_folds: int = 5,
    salt: str = "V5_CATEGORICAL_ATTACK_V1",
) -> dict[str, Any]:
    x = _one(feature, "feature").astype(str)
    y = _one(label, "label").astype(str)
    g = _one(groups, "groups").astype(str)
    if not (x.shape == y.shape == g.shape):
        raise AntiCheatQualificationError("feature/label/groups mismatch")
    folds = deterministic_group_folds(g, n_folds=n_folds, salt=salt)
    pred_all = np.empty(len(y), dtype=object)
    used = np.zeros(len(y), dtype=bool)
    per_fold = []
    for fold in range(n_folds):
        test = folds == fold
        train = ~test
        if not test.any() or not train.any():
            continue
        fallback = _majority(y[train])
        lookup = _equal_prior_lookup(x[train], y[train])
        pred = np.asarray([lookup.get(v, fallback) for v in x[test]], dtype=object)
        pred_all[test] = pred
        used[test] = True
        per_fold.append({
            "fold": fold,
            "rows": int(test.sum()),
            "groups": int(np.unique(g[test]).size),
            "balanced_accuracy": balanced_accuracy(y[test], pred),
            "unseen_feature_rate": float(1.0 - np.isin(x[test], np.unique(x[train])).mean()),
        })
    if not used.any():
        raise AntiCheatQualificationError("no evaluable fold")
    score = balanced_accuracy(y[used], pred_all[used])
    chance = 1.0 / int(np.unique(y[used]).size)
    return {
        "attack": "categorical_equal_prior_lookup_group_holdout",
        "rows_evaluated": int(used.sum()),
        "n_folds_evaluated": len(per_fold),
        "balanced_accuracy": score,
        "balanced_chance": chance,
        "excess_over_chance": float(score - chance),
        "per_fold": per_fold,
    }


def quantile_scalar_group_holdout_attack(
    values: Sequence[float] | np.ndarray,
    label: Sequence[Any] | np.ndarray,
    groups: Sequence[Any] | np.ndarray,
    *,
    bin_grid: Sequence[int] = (8, 16, 32, 64),
    n_folds: int = 5,
    salt: str = "V5_SCALAR_ATTACK_V1",
) -> dict[str, Any]:
    v = _one(values, "values").astype(np.float64)
    y = _one(label, "label").astype(str)
    g = _one(groups, "groups").astype(str)
    if not (v.shape == y.shape == g.shape) or not np.isfinite(v).all():
        raise AntiCheatQualificationError("values/label/groups invalid")
    folds = deterministic_group_folds(g, n_folds=n_folds, salt=salt)
    chance = 1.0 / int(np.unique(y).size)
    reports = []
    for raw_bins in bin_grid:
        if isinstance(raw_bins, bool) or int(raw_bins) < 2:
            raise AntiCheatQualificationError("bin grid entries must be >=2")
        bins = int(raw_bins)
        pred_all = np.empty(len(y), dtype=object)
        used = np.zeros(len(y), dtype=bool)
        fold_reports = []
        for fold in range(n_folds):
            test = folds == fold
            train = ~test
            if not test.any() or not train.any():
                continue
            edges = np.unique(np.quantile(v[train], np.linspace(0, 1, bins + 1)))
            internal = edges[1:-1] if len(edges) > 2 else np.asarray([], dtype=np.float64)
            tr_bin = np.searchsorted(internal, v[train], side="right")
            te_bin = np.searchsorted(internal, v[test], side="right")
            fallback = _majority(y[train])
            lookup = _equal_prior_lookup(tr_bin.astype(str), y[train])
            pred = np.asarray([lookup.get(str(int(k)), fallback) for k in te_bin], dtype=object)
            pred_all[test] = pred
            used[test] = True
            fold_reports.append({
                "fold": fold,
                "rows": int(test.sum()),
                "learned_bin_count": int(len(internal) + 1),
                "balanced_accuracy": balanced_accuracy(y[test], pred),
            })
        if not used.any():
            raise AntiCheatQualificationError("no evaluable fold")
        score = balanced_accuracy(y[used], pred_all[used])
        reports.append({
            "requested_bins": bins,
            "balanced_accuracy": score,
            "excess_over_chance": float(score - chance),
            "per_fold": fold_reports,
        })
    return {
        "attack": "quantile_scalar_equal_prior_lookup_group_holdout",
        "balanced_chance": chance,
        "grid": reports,
        "max_descriptive_balanced_accuracy": float(max(r["balanced_accuracy"] for r in reports)),
    }


def mask_row_sha256(states: Sequence[Sequence[int]] | np.ndarray) -> np.ndarray:
    arr = np.asarray(states)
    if arr.ndim != 2 or arr.shape[0] < 1 or arr.shape[1] < 1 or arr.dtype.kind not in "iu":
        raise AntiCheatQualificationError("states must be integer [operators,addresses]")
    canonical = np.asarray(arr, dtype="<u1") if arr.min() >= 0 and arr.max() <= 255 else np.asarray(arr, dtype="<i8")
    return np.asarray([
        hashlib.sha256(np.ascontiguousarray(row).tobytes()).hexdigest()
        for row in canonical
    ], dtype=object)


def state_count_features(states: Sequence[Sequence[int]] | np.ndarray, state_values: Sequence[int] = (0, 1, 2)) -> np.ndarray:
    arr = np.asarray(states)
    if arr.ndim != 2:
        raise AntiCheatQualificationError("states must be 2-D")
    return np.stack([np.sum(arr == int(v), axis=1) for v in state_values], axis=1).astype(np.float64)


def split_manifest_for_entities(
    columns: Mapping[str, Sequence[Any] | np.ndarray],
    *,
    n_folds: int = 5,
    leave_one_out_max_levels: int = 8,
    salt_prefix: str = "V5_TRANSFER_SPLIT_V1",
) -> dict[str, Any]:
    if not columns:
        raise AntiCheatQualificationError("columns cannot be empty")
    out: dict[str, Any] = {}
    for name, values in columns.items():
        arr = _one(values, name).astype(str)
        levels = np.asarray(sorted(np.unique(arr)), dtype=object)
        if len(levels) < 2:
            out[name] = {"status": NOT_ESTIMABLE, "reason": "fewer_than_two_levels", "levels": int(len(levels))}
            continue
        if len(levels) <= leave_one_out_max_levels:
            assignment = {str(level): i for i, level in enumerate(levels)}
            mode = "leave_one_entity_out"
            fold_count = len(levels)
        else:
            assignment = {
                str(level): int(stable_hash_u64(level, salt=f"{salt_prefix}:{name}") % n_folds)
                for level in levels
            }
            mode = "deterministic_hash_group_fold"
            fold_count = n_folds
        out[name] = {
            "status": PASS,
            "mode": mode,
            "levels": int(len(levels)),
            "fold_count": int(fold_count),
            "assignment": assignment,
            "row_counts": {str(level): int(np.sum(arr == level)) for level in levels},
        }
    return out


def cosine_centroid_memorization_attack(
    embeddings: Sequence[Sequence[float]] | np.ndarray,
    entity_labels: Sequence[Any] | np.ndarray,
    stable_row_keys: Sequence[Any] | np.ndarray,
    *,
    test_modulus: int = 5,
    test_bucket: int = 0,
    salt: str = "V5_DONOR_MEMORIZATION_V1",
) -> dict[str, Any]:
    z = _finite2(embeddings, "embeddings")
    y = _one(entity_labels, "entity_labels").astype(str)
    keys = _one(stable_row_keys, "stable_row_keys")
    if len(z) != len(y) or len(y) != len(keys):
        raise AntiCheatQualificationError("embedding/entity/key mismatch")
    test = np.asarray([stable_hash_u64(k, salt=salt) % test_modulus == test_bucket for k in keys], dtype=bool)
    eligible = [e for e in np.unique(y) if ((y == e) & test).any() and ((y == e) & ~test).any()]
    if len(eligible) < 2:
        raise AntiCheatQualificationError("too few evaluable entities")
    norms = np.linalg.norm(z, axis=1)
    if np.any(norms <= 0):
        raise AntiCheatQualificationError("zero-norm embedding row")
    zn = z / norms[:, None]
    ordered = np.asarray(sorted(eligible), dtype=object)
    centroids = []
    for entity in ordered:
        c = zn[(~test) & (y == entity)].mean(axis=0)
        n = np.linalg.norm(c)
        if n <= 0:
            raise AntiCheatQualificationError("zero-norm centroid")
        centroids.append(c / n)
    C = np.stack(centroids)
    use = test & np.isin(y, ordered)
    pred = ordered[np.argmax(zn[use] @ C.T, axis=1)].astype(str)
    score = balanced_accuracy(y[use], pred)
    chance = 1.0 / len(ordered)
    return {
        "attack": "cosine_centroid_within_entity_held_cell_out",
        "entities": int(len(ordered)),
        "test_rows": int(use.sum()),
        "balanced_accuracy": score,
        "balanced_chance": chance,
        "excess_over_chance": float(score - chance),
    }


def latent_health_metrics(embeddings: Sequence[Sequence[float]] | np.ndarray, *, eps: float = 1e-12) -> dict[str, Any]:
    z = _finite2(embeddings, "embeddings")
    centered = z - z.mean(axis=0, keepdims=True)
    per_dim_var = np.mean(centered * centered, axis=0)
    total = float(per_dim_var.sum())
    if total <= eps:
        return {
            "rows": int(z.shape[0]), "dimensions": int(z.shape[1]), "total_variance": total,
            "entropy_effective_rank": 0.0, "effective_rank_fraction": 0.0,
            "participation_ratio": 0.0, "nonzero_variance_dimensions": 0,
        }
    cov = centered.T @ centered / float(z.shape[0])
    eig = np.clip(np.linalg.eigvalsh(cov), 0.0, None)
    s1 = float(eig.sum())
    s2 = float(np.square(eig).sum())
    p = eig / s1
    nz = p > eps
    erank = float(math.exp(float(-np.sum(p[nz] * np.log(p[nz])))))
    return {
        "rows": int(z.shape[0]),
        "dimensions": int(z.shape[1]),
        "total_variance": total,
        "entropy_effective_rank": erank,
        "effective_rank_fraction": float(erank / z.shape[1]),
        "participation_ratio": float((s1 * s1 / s2) if s2 > eps else 0.0),
        "nonzero_variance_dimensions": int(np.sum(per_dim_var > eps)),
    }


def collapse_negative_control_report(embeddings: Sequence[Sequence[float]] | np.ndarray) -> dict[str, Any]:
    z = _finite2(embeddings, "embeddings")
    constant = np.broadcast_to(z.mean(axis=0, keepdims=True), z.shape).copy()
    row_signal = z[:, 0] - np.mean(z[:, 0])
    direction = z.mean(axis=0)
    if np.linalg.norm(direction) <= 1e-12:
        direction = np.ones(z.shape[1])
    direction = direction / np.linalg.norm(direction)
    rank1 = row_signal[:, None] * direction[None, :]
    base = latent_health_metrics(z)
    c = latent_health_metrics(constant)
    r = latent_health_metrics(rank1)
    ok_constant = c["total_variance"] <= 1e-12 and c["entropy_effective_rank"] == 0.0
    ok_rank1 = r["entropy_effective_rank"] <= 1.000001
    return {
        "status": PASS if ok_constant and ok_rank1 else FAIL,
        "reference": base,
        "constant_control": c,
        "rank1_control": r,
        "constant_collapse_detected": bool(ok_constant),
        "rank1_low_rank_detected": bool(ok_rank1),
    }


def proposal_p_over_q_audit(
    p: Sequence[float] | np.ndarray,
    q: Sequence[float] | np.ndarray,
    *,
    donor_labels: Sequence[Any] | np.ndarray | None = None,
    normalization_tolerance: float = 1e-10,
) -> dict[str, Any]:
    p_arr = _one(p, "p").astype(np.float64)
    q_arr = _one(q, "q").astype(np.float64)
    if p_arr.shape != q_arr.shape or not np.isfinite(p_arr).all() or not np.isfinite(q_arr).all():
        raise AntiCheatQualificationError("p/q invalid")
    if np.any(p_arr < 0) or np.any(q_arr < 0):
        raise AntiCheatQualificationError("p/q must be nonnegative")
    if abs(float(p_arr.sum()) - 1.0) > normalization_tolerance or abs(float(q_arr.sum()) - 1.0) > normalization_tolerance:
        raise AntiCheatQualificationError("p/q must be normalized")
    if np.any((p_arr > 0) & (q_arr <= 0)):
        raise AntiCheatQualificationError("proposal support gap")
    w = np.zeros_like(p_arr)
    w[q_arr > 0] = p_arr[q_arr > 0] / q_arr[q_arr > 0]
    identity = float(np.sum(q_arr * w))
    second = float(np.sum(q_arr * w * w))
    positive = w[w > 0]
    out: dict[str, Any] = {
        "rows": int(len(w)),
        "q_expectation_of_p_over_q": identity,
        "importance_identity_error": abs(identity - 1.0),
        "importance_weight_max": float(w.max(initial=0.0)),
        "importance_weight_ratio": float(positive.max() / positive.min()) if len(positive) else math.inf,
        "asymptotic_ess_fraction_under_q": float(identity * identity / second) if second > 0 else 0.0,
        "support_gap_rows": 0,
    }
    if donor_labels is not None:
        donor = _one(donor_labels, "donor_labels").astype(str)
        if donor.shape != p_arr.shape:
            raise AntiCheatQualificationError("donor_labels mismatch")
        levels = np.unique(donor)
        masses = np.asarray([p_arr[donor == d].sum() for d in levels])
        target = 1.0 / len(levels)
        out["donor_count"] = int(len(levels))
        out["max_abs_donor_mass_deviation_from_uniform"] = float(np.max(np.abs(masses - target)))
    return out


def response_curve_against_full_evidence(
    embeddings_by_fraction: Mapping[float, Sequence[Sequence[float]] | np.ndarray],
    *,
    reference_fraction: float = 1.0,
) -> dict[str, Any]:
    if reference_fraction not in embeddings_by_fraction:
        raise AntiCheatQualificationError("reference fraction missing")
    fractions = sorted(float(k) for k in embeddings_by_fraction)
    if len(fractions) < 2 or fractions[-1] != float(reference_fraction):
        raise AntiCheatQualificationError("reference must be largest supplied fraction")
    ref = _finite2(embeddings_by_fraction[reference_fraction], "reference")
    ref_norm = np.linalg.norm(ref, axis=1)
    if np.any(ref_norm <= 0):
        raise AntiCheatQualificationError("zero-norm reference")
    rows = []
    drift_columns = []
    for frac in fractions:
        cur = _finite2(embeddings_by_fraction[frac], f"embeddings[{frac}]")
        if cur.shape != ref.shape:
            raise AntiCheatQualificationError("response curve shape mismatch")
        cur_norm = np.linalg.norm(cur, axis=1)
        if np.any(cur_norm <= 0):
            raise AntiCheatQualificationError("zero-norm response row")
        cosine = np.clip(np.sum(cur * ref, axis=1) / (cur_norm * ref_norm), -1.0, 1.0)
        drift = 1.0 - cosine
        drift_columns.append(drift)
        rows.append({
            "fraction": frac,
            "mean_cosine_to_full": float(cosine.mean()),
            "mean_cosine_drift": float(drift.mean()),
            "p90_cosine_drift": float(np.quantile(drift, 0.90)),
            "mean_l2_drift": float(np.linalg.norm(cur - ref, axis=1).mean()),
        })
    diffs = np.diff(np.stack(drift_columns, axis=1), axis=1)
    return {
        "rows": int(ref.shape[0]),
        "dimensions": int(ref.shape[1]),
        "fractions": rows,
        "cell_step_monotonicity_violation_rate": float(np.mean(diffs > 1e-12)) if diffs.size else 0.0,
    }


def hardware_invariance_replay(
    reference: Sequence[Sequence[float]] | np.ndarray,
    candidate: Sequence[Sequence[float]] | np.ndarray,
    *,
    reference_ids: Sequence[Any] | np.ndarray | None = None,
    candidate_ids: Sequence[Any] | np.ndarray | None = None,
    atol: float = 0.0,
    rtol: float = 0.0,
) -> dict[str, Any]:
    a = np.asarray(reference)
    b = np.asarray(candidate)
    if a.shape != b.shape:
        return {"status": FAIL, "reason": "shape_mismatch"}
    if reference_ids is not None or candidate_ids is not None:
        if reference_ids is None or candidate_ids is None:
            raise AntiCheatQualificationError("both identity vectors required")
        if not np.array_equal(_one(reference_ids, "reference_ids").astype(str), _one(candidate_ids, "candidate_ids").astype(str)):
            return {"status": FAIL, "reason": "identity_mismatch"}
    if a.dtype.kind in "iu?" and b.dtype.kind in "iu?" and atol == 0.0 and rtol == 0.0:
        equal = bool(np.array_equal(a, b))
        max_abs = 0.0 if equal else math.inf
    else:
        aa = np.asarray(a, dtype=np.float64)
        bb = np.asarray(b, dtype=np.float64)
        if not np.isfinite(aa).all() or not np.isfinite(bb).all():
            raise AntiCheatQualificationError("nonfinite replay arrays")
        equal = bool(np.allclose(aa, bb, atol=atol, rtol=rtol))
        max_abs = float(np.max(np.abs(aa - bb))) if aa.size else 0.0
    return {"status": PASS if equal else FAIL, "shape": list(a.shape), "atol": float(atol), "rtol": float(rtol), "max_abs_difference": max_abs}


REQUIRED_CHECKPOINT_GATES = (
    "SUPPORT_ONLY_SOURCE_ATTACK_ON_Z_BIO",
    "DEPTH_QC_ONLY_ATTACK_ON_Z_BIO",
    "MASK_ONLY_ATTACK_ON_Z_BIO",
    "DONOR_MEMORIZATION_PROBE",
    "HELD_OUT_DONOR_TRANSFER",
    "HELD_OUT_MATRIX_OPERATOR_TRANSFER",
    "HELD_OUT_STUDY_SOURCE_TRANSFER",
    "HELD_OUT_TECHNOLOGY_TRANSFER",
    "EVIDENCE_RESPONSE_CURVE",
    "DEPTH_RESPONSE_CURVE",
    "PROPOSAL_P_OVER_Q_AUDIT",
    "LATENT_COLLAPSE_VARIANCE_EFFECTIVE_RANK",
    "CONSTANT_VECTOR_LOW_RANK_NEGATIVE_CONTROLS",
    "HARDWARE_INVARIANCE_REPLAY",
    "MANDATORY_T1_MECHANICS_CHAIN",
)


def qualification_skeleton(*, input_shortcut_atlas: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": "TEACHER_STUDENT_V5_ANTI_CHEAT_QUALIFICATION_V1",
        "training_authorized": False,
        "cheat_qualified": False,
        "input_shortcut_atlas": dict(input_shortcut_atlas or {}),
        "checkpoint_gates": {
            gate: {"status": BLOCKED, "reason": "required_checkpoint_or_trainer_evidence_not_supplied"}
            for gate in REQUIRED_CHECKPOINT_GATES
        },
        "terminal": "V5_NOT_CHEAT_QUALIFIED__CHECKPOINT_GATES_PENDING",
    }
