"""Cross-fitted multivariate decomposition primitives for current V5 teacher states.

This module measures vector-valued predictability from query-address identity,
context identity, their additive combination, and a repeated joint-group
predictor. It does not assert that residual variance is biological, does not
choose a production context definition, and does not consume query scalar
expression or pathology labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class LatentDecompositionResultV1:
    oof_grand_sse: float
    oof_address_sse: float
    oof_context_sse: float
    oof_additive_sse: float
    oof_joint_sse: float
    address_skill_vs_grand: float
    context_skill_vs_grand: float
    additive_skill_vs_grand: float
    joint_skill_vs_grand: float
    joint_increment_over_additive: float
    unseen_address_rows: int
    unseen_context_rows: int
    unseen_joint_rows: int
    n_rows: int
    latent_dim: int

    @property
    def residual_after_additive_fraction_of_oof_grand(self) -> float:
        return self.oof_additive_sse / self.oof_grand_sse


def _labels(value: Any, name: str, n: int) -> np.ndarray:
    x = np.asarray([str(v) for v in value], dtype=object)
    if x.ndim != 1 or x.size != n or any(not str(v) for v in x):
        raise ValueError(f"{name} must be {n} nonempty labels")
    return x


def _group_means(labels: np.ndarray, y: np.ndarray) -> dict[object, np.ndarray]:
    out: dict[object, np.ndarray] = {}
    for key in dict.fromkeys(labels.tolist()):
        ix = np.flatnonzero(labels == key)
        out[key] = y[ix].mean(axis=0)
    return out


def _fit_additive(
    address: np.ndarray,
    context: np.ndarray,
    y: np.ndarray,
    *,
    max_iter: int = 200,
    tol: float = 1.0e-12,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Fit y = grand + address_effect + context_effect by deterministic backfitting."""

    grand = y.mean(axis=0)
    address_keys = tuple(dict.fromkeys(address.tolist()))
    context_keys = tuple(dict.fromkeys(context.tolist()))
    a = {str(k): np.zeros(y.shape[1], dtype=np.float64) for k in address_keys}
    c = {str(k): np.zeros(y.shape[1], dtype=np.float64) for k in context_keys}
    aix = {str(k): np.flatnonzero(address == k) for k in address_keys}
    cix = {str(k): np.flatnonzero(context == k) for k in context_keys}

    for _ in range(max_iter):
        before = sum(float(np.dot(v, v)) for v in a.values()) + sum(float(np.dot(v, v)) for v in c.values())
        for key, ix in aix.items():
            context_effect = np.vstack([c[str(v)] for v in context[ix]])
            a[key] = (y[ix] - grand - context_effect).mean(axis=0)
        shift = sum(ix.size * a[key] for key, ix in aix.items()) / y.shape[0]
        grand = grand + shift
        for key in a:
            a[key] = a[key] - shift

        for key, ix in cix.items():
            address_effect = np.vstack([a[str(v)] for v in address[ix]])
            c[key] = (y[ix] - grand - address_effect).mean(axis=0)
        shift = sum(ix.size * c[key] for key, ix in cix.items()) / y.shape[0]
        grand = grand + shift
        for key in c:
            c[key] = c[key] - shift

        after = sum(float(np.dot(v, v)) for v in a.values()) + sum(float(np.dot(v, v)) for v in c.values())
        if abs(after - before) <= tol * (1.0 + abs(before)):
            break
    return grand, a, c


def _sse(y: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sum(np.square(y - pred), dtype=np.float64))


def crossfit_latent_state_decomposition(
    teacher_state: Any,
    query_address_id: Any,
    context_id: Any,
    fold_by_row: Any,
) -> LatentDecompositionResultV1:
    """Cross-fit vector-state predictors without held-out-row fitting.

    context_id is intentionally caller-defined and must be frozen separately.
    The joint address x context predictor is estimable only when a pair repeats
    across folds; unseen held-out pairs fall back to the training grand mean and
    are explicitly counted.
    """

    y = np.asarray(teacher_state, dtype=np.float64)
    if y.ndim != 2 or y.shape[0] < 2 or y.shape[1] < 1 or not np.all(np.isfinite(y)):
        raise ValueError("teacher_state must be a finite nonempty row x latent matrix")
    n = y.shape[0]
    address = _labels(query_address_id, "query_address_id", n)
    context = _labels(context_id, "context_id", n)
    fold = np.asarray(fold_by_row, dtype=np.int64)
    if fold.ndim != 1 or fold.size != n:
        raise ValueError("fold_by_row must align with teacher_state rows")
    folds = sorted(set(map(int, fold)))
    if len(folds) < 2:
        raise ValueError("cross-fitting requires at least two folds")

    pred_grand = np.empty_like(y)
    pred_address = np.empty_like(y)
    pred_context = np.empty_like(y)
    pred_additive = np.empty_like(y)
    pred_joint = np.empty_like(y)
    unseen_address = unseen_context = unseen_joint = 0

    for f in folds:
        test = fold == f
        train = ~test
        if not np.any(test) or not np.any(train):
            raise ValueError("every fold must have both train and held-out rows")
        yt = y[train]
        grand = yt.mean(axis=0)
        address_mean = _group_means(address[train], yt)
        context_mean = _group_means(context[train], yt)
        joint_labels = np.asarray(
            [str(a) + "\x1f" + str(c) for a, c in zip(address[train], context[train])],
            dtype=object,
        )
        joint_mean = _group_means(joint_labels, yt)
        additive_grand, a_effect, c_effect = _fit_additive(address[train], context[train], yt)

        test_ix = np.flatnonzero(test)
        for i in test_ix:
            akey = str(address[i])
            ckey = str(context[i])
            jkey = akey + "\x1f" + ckey
            pred_grand[i] = grand

            if akey in address_mean:
                pred_address[i] = address_mean[akey]
            else:
                pred_address[i] = grand
                unseen_address += 1

            if ckey in context_mean:
                pred_context[i] = context_mean[ckey]
            else:
                pred_context[i] = grand
                unseen_context += 1

            pred_additive[i] = (
                additive_grand
                + a_effect.get(akey, np.zeros(y.shape[1], dtype=np.float64))
                + c_effect.get(ckey, np.zeros(y.shape[1], dtype=np.float64))
            )

            if jkey in joint_mean:
                pred_joint[i] = joint_mean[jkey]
            else:
                pred_joint[i] = grand
                unseen_joint += 1

    grand_sse = _sse(y, pred_grand)
    if not np.isfinite(grand_sse) or grand_sse <= 0:
        raise ValueError("OOF grand baseline has zero/nonfinite error; decomposition is not estimable")
    address_sse = _sse(y, pred_address)
    context_sse = _sse(y, pred_context)
    additive_sse = _sse(y, pred_additive)
    joint_sse = _sse(y, pred_joint)
    skill = lambda sse: float(1.0 - sse / grand_sse)

    return LatentDecompositionResultV1(
        oof_grand_sse=grand_sse,
        oof_address_sse=address_sse,
        oof_context_sse=context_sse,
        oof_additive_sse=additive_sse,
        oof_joint_sse=joint_sse,
        address_skill_vs_grand=skill(address_sse),
        context_skill_vs_grand=skill(context_sse),
        additive_skill_vs_grand=skill(additive_sse),
        joint_skill_vs_grand=skill(joint_sse),
        joint_increment_over_additive=float((additive_sse - joint_sse) / grand_sse),
        unseen_address_rows=int(unseen_address),
        unseen_context_rows=int(unseen_context),
        unseen_joint_rows=int(unseen_joint),
        n_rows=int(n),
        latent_dim=int(y.shape[1]),
    )
