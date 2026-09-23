"""Leakage-aware target-held-out benchmark mechanics, CPU/synthetic qualification.

This module implements prospectively frozen target partitions and target-excluded
evaluation of *measured* guide×donor effects. No real experiment is opened
here and no JEPA is trained. A separate physical producer must authenticate
count arrays and generate donor-matched control-relative effects first.

One guide×donor row is NOT an independent donor. Results are summarized per
held-out target; donor transport is a separate question and is never inferred
from a random cell/guide split.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

SCHEMA = "PERTURBATION_TARGET_HOLDOUT_BENCHMARK_V1"
EXPOSURES = frozenset({
    "DEVELOPMENT", "HISTORICALLY_EXPOSED",
    "RETROSPECTIVE_BENCHMARK", "HELD_OUT",
})


def digest(body: object) -> str:
    return hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProspectivePartition:
    schema: str
    assay: str
    source_sha256: str
    exposure: str
    seed: str
    n_folds: int
    target_to_fold: tuple[tuple[str, int], ...]
    partition_sha256: str

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ValueError("partition schema mismatch")
        if self.exposure not in EXPOSURES:
            raise ValueError("unknown exposure")
        if self.n_folds < 2 or len(self.target_to_fold) < self.n_folds:
            raise ValueError("insufficient targets for requested folds")
        if not isinstance(self.source_sha256, str) or len(self.source_sha256) != 64:
            raise ValueError("source SHA identity is missing")
        if not self.seed:
            raise ValueError("a fixed seed is required")
        names = [t for t, _ in self.target_to_fold]
        if len(names) != len(set(names)) or names != sorted(names):
            raise ValueError("target IDs must be unique and sorted")
        if {k for _, k in self.target_to_fold} != set(range(self.n_folds)):
            raise ValueError("all folds must contain targets")
        if digest(self.body()) != self.partition_sha256:
            raise ValueError("prospective partition self-digest mismatch")

    def body(self) -> dict:
        return {
            "schema": self.schema, "assay": self.assay,
            "source_sha256": self.source_sha256, "exposure": self.exposure,
            "seed": self.seed, "n_folds": self.n_folds,
            "target_to_fold": [list(x) for x in self.target_to_fold],
        }


def freeze_target_partition(
    *, target_ids: Sequence[str], assay: str, source_sha256: str,
    exposure: str, seed: str, n_folds: int = 5,
) -> ProspectivePartition:
    """Freeze without loading response values; stable under input row order."""
    targets = sorted(set(target_ids))
    if not targets or len(targets) < n_folds or n_folds < 2:
        raise ValueError("at least one target per fold is required")
    if any(not isinstance(x, str) or not x.strip() for x in target_ids):
        raise ValueError("target identity missing")
    if not assay or exposure not in EXPOSURES or not seed:
        raise ValueError("assay, declared exposure and fixed seed required")
    if len(source_sha256) != 64 or any(c not in "0123456789abcdef" for c in source_sha256):
        raise ValueError("source SHA must be lowercase hex")
    # Sorted digest order makes fold assignment independent of data row order.
    shuffled = sorted(targets, key=lambda t: (digest([seed, assay, t]), t))
    assignments = tuple(sorted(
        ((target, i % n_folds) for i, target in enumerate(shuffled)),
    ))
    body = {
        "schema": SCHEMA, "assay": assay,
        "source_sha256": source_sha256, "exposure": exposure,
        "seed": seed, "n_folds": n_folds,
        "target_to_fold": [list(x) for x in assignments],
    }
    frozen = ProspectivePartition(
        SCHEMA, assay, source_sha256, exposure, seed, n_folds,
        assignments, digest(body),
    )
    frozen.validate()
    return frozen


@dataclass(frozen=True)
class GuideDonorEffects:
    assay: str
    feature_ids: tuple[str, ...]
    guide_ids: tuple[str, ...]
    donor_ids: tuple[str, ...]
    target_ids: tuple[str, ...]
    effects: np.ndarray  # rows: guide×donor; columns: measured molecular features
    measured: np.ndarray  # same shape; false requires NaN in effects

    def validate(self) -> None:
        x, mask = np.asarray(self.effects), np.asarray(self.measured)
        n = len(self.guide_ids)
        p = len(self.feature_ids)
        if x.shape != (n, p) or mask.shape != x.shape or mask.dtype != np.bool_:
            raise ValueError("effects/mask must be aligned guide×donor matrices")
        if len(self.donor_ids) != n or len(self.target_ids) != n:
            raise ValueError("guide, donor and target identities do not align")
        if not self.assay or not all(self.guide_ids) or not all(self.donor_ids):
            raise ValueError("assay, donor and guide must be present")
        if not all(self.target_ids) or not all(self.feature_ids):
            raise ValueError("target and molecular-feature IDs must be nonempty")
        if len(set(self.feature_ids)) != p:
            raise ValueError("duplicate feature identifiers")
        if len(set(zip(self.guide_ids, self.donor_ids))) != n:
            raise ValueError("a guide×donor unit is duplicated")
        guide_to_target: dict[str, str] = {}
        for g, t in zip(self.guide_ids, self.target_ids):
            if g in guide_to_target and guide_to_target[g] != t:
                raise ValueError("same guide assigned conflicting targets")
            guide_to_target[g] = t
        if not np.all(np.isfinite(x[mask])):
            raise ValueError("measured effects must be finite")
        if not np.all(np.isnan(x[~mask])):
            raise ValueError("unmeasured entries must be NaN, never zero")


def donor_matched_effects(
    *, assay: str, feature_ids: Sequence[str],
    guide_ids: Sequence[str], donor_ids: Sequence[str],
    target_ids: Sequence[str], is_control: Sequence[bool],
    logcpm: np.ndarray, measured_features: Sequence[bool],
) -> GuideDonorEffects:
    """Produce descriptive effects from guide×donor logCPM using within-donor NT.

    No inferential DE claim; biological uncertainty requires further analysis.
    """
    x = np.asarray(logcpm, dtype=float)
    n, p = x.shape
    controls = np.asarray(is_control, dtype=bool)
    measured = np.asarray(measured_features, dtype=bool)
    if (len(feature_ids) != p or len(guide_ids) != n or len(donor_ids) != n
            or len(target_ids) != n or controls.shape != (n,)
            or measured.shape != (p,)):
        raise ValueError("guide metadata / measured mask / matrix shape mismatch")
    if not np.all(np.isfinite(x[:, measured])):
        raise ValueError("nonfinite observed logCPM")
    # Control rows use their true donor and NEVER become candidate target rows.
    effects, gids, dids, tids = [], [], [], []
    for donor in sorted(set(donor_ids)):
        ctrl = np.array(
            [i for i, d in enumerate(donor_ids) if d == donor and controls[i]],
            dtype=int,
        )
        pert = [i for i, d in enumerate(donor_ids) if d == donor and not controls[i]]
        if pert and len(ctrl) == 0:
            raise ValueError(f"donor {donor} has no matched non-targeting controls")
        if not pert:
            continue
        baseline = x[ctrl][:, measured].mean(axis=0)
        for i in pert:
            row = np.full(p, np.nan, dtype=float)
            row[measured] = x[i, measured] - baseline
            effects.append(row)
            gids.append(str(guide_ids[i]))
            dids.append(str(donor_ids[i]))
            tids.append(str(target_ids[i]))
    if not effects:
        raise ValueError("no perturbed guide×donor units")
    mask = np.broadcast_to(measured, (len(effects), p)).copy()
    out = GuideDonorEffects(
        assay, tuple(feature_ids), tuple(gids), tuple(dids),
        tuple(tids), np.asarray(effects), mask,
    )
    out.validate()
    return out


def select_fold(data: GuideDonorEffects, partition: ProspectivePartition, fold: int):
    data.validate()
    partition.validate()
    if partition.assay != data.assay:
        raise ValueError("assay differs from frozen partition")
    if not 0 <= fold < partition.n_folds:
        raise ValueError("fold outside frozen partition")
    mapping = dict(partition.target_to_fold)
    if set(data.target_ids) != set(mapping):
        raise ValueError("data targets differ from prospective frozen target universe")
    test = np.array([mapping[t] == fold for t in data.target_ids], dtype=bool)
    train = ~test
    if not train.any() or not test.any():
        raise ValueError("empty train/test fold")
    if set(np.asarray(data.target_ids)[train]) & set(np.asarray(data.target_ids)[test]):
        raise AssertionError("TARGET LEAKAGE: target appears on both sides")
    return train, test


def training_baselines(data: GuideDonorEffects, train: np.ndarray):
    """Fit simple baselines on TRAIN ONLY, equal target weight."""
    data.validate()
    train = np.asarray(train, dtype=bool)
    if train.shape != (len(data.target_ids),) or not train.any():
        raise ValueError("invalid train mask")
    targets = sorted(set(np.asarray(data.target_ids)[train]))
    by_target = []
    for target in targets:
        rows = train & (np.asarray(data.target_ids) == target)
        observed = data.effects[rows]
        finite = np.isfinite(observed)
        denom_target = finite.sum(axis=0)
        per_feature = np.full(observed.shape[1], np.nan, dtype=float)
        supported_target = denom_target > 0
        per_feature[supported_target] = (
            np.nansum(observed[:, supported_target], axis=0)
            / denom_target[supported_target]
        )
        by_target.append(per_feature)
    target_matrix = np.asarray(by_target)
    # Avoid poison from masked-only columns; those remain non-estimable.
    available = np.isfinite(target_matrix)
    denom = available.sum(axis=0)
    mean = np.full(len(data.feature_ids), np.nan, dtype=float)
    supported = denom > 0
    mean[supported] = np.nansum(target_matrix[:, supported], axis=0) / denom[supported]
    # Target-only prediction uses training-target engagement alone.
    target_effects = []
    fidx = {gene: i for i, gene in enumerate(data.feature_ids)}
    for target, row in zip(targets, by_target):
        j = fidx.get(target)
        if j is not None and np.isfinite(row[j]):
            target_effects.append(float(row[j]))
    engagement = float(np.median(target_effects)) if target_effects else 0.0
    return mean, engagement


def evaluate_target_excluded_baselines(
    data: GuideDonorEffects, partition: ProspectivePartition, fold: int,
) -> dict:
    """Macro-average held-out targets, exclude each target gene from scoring.

    Results are DESCRIPTIVE BASELINES. This function is not a predictive model
    training authorization or a prospective external validation claim.
    """
    train, test = select_fold(data, partition, fold)
    mean, median_engagement = training_baselines(data, train)
    fidx = {gene: i for i, gene in enumerate(data.feature_ids)}
    report = {}
    for name in ("no_change", "train_target_equal_mean", "target_identity_only"):
        target_rows = []
        for target in sorted(set(np.asarray(data.target_ids)[test])):
            rows = test & (np.asarray(data.target_ids) == target)
            observed = data.effects[rows]
            support = data.measured[rows].copy()
            target_col = fidx.get(target)
            if target_col is not None:
                support[:, target_col] = False
            if name == "no_change" or name == "target_identity_only":
                # Target-identity-only baseline predicts engagement on the
                # targeted gene; this is intentionally excluded downstream.
                prediction = np.zeros(len(data.feature_ids))
            else:
                prediction = mean
            evaluable = support & np.isfinite(prediction[None, :])
            if not evaluable.any():
                target_rows.append({"target": target, "status": "NOT_ESTIMABLE", "n": 0})
                continue
            error = observed[evaluable] - np.broadcast_to(
                prediction, observed.shape,
            )[evaluable]
            target_rows.append({
                "target": target, "status": "ESTIMABLE",
                "n": int(error.size),
                "mae": float(np.abs(error).mean()),
                "rmse": float(np.sqrt(np.square(error).mean())),
            })
        estimable = [row for row in target_rows if row["status"] == "ESTIMABLE"]
        report[name] = {
            "per_target": target_rows,
            "macro_mae": float(np.mean([x["mae"] for x in estimable]))
            if estimable else None,
            "macro_rmse": float(np.mean([x["rmse"] for x in estimable]))
            if estimable else None,
            "n_estimable_targets": len(estimable),
        }
    return {
        "schema": SCHEMA, "status": "BASELINE_ONLY_NO_JEPA_TRAINING",
        "exposure": partition.exposure,
        "partition_sha256": partition.partition_sha256,
        "fold": fold,
        "n_train_targets": len(set(np.asarray(data.target_ids)[train])),
        "n_test_targets": len(set(np.asarray(data.target_ids)[test])),
        "train_only_median_engagement": median_engagement,
        "baselines": report,
        "jepa_training_authorized": False,
        "therapeutic_ranking_authorized": False,
    }
