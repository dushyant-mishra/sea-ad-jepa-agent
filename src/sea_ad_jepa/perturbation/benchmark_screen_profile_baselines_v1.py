"""Retrospective within-screen target-heldout baselines for processed CRISPRbrain DE.

This is a SMALL adapter for studies whose released unit is one target-level
differential-expression profile, NOT a fake donor/guide replicate. It complements
benchmark_target_holdout_v1 (real guide x donor effects) without modifying it.
For GSE178317 Day-8, the screen and our recovered cells are the SAME experiment.
No confirmation, brain causal generalization, biological SE or JEPA result.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np


class ScreenBaselineError(ValueError):
    pass


@dataclass(frozen=True)
class ScreenProfiles:
    screen: str
    source_csv_sha256: str
    targets: tuple[str, ...]
    genes: tuple[str, ...]
    effects: np.ndarray  # target x assayed gene; missing is NaN, never zero

    def validate(self) -> None:
        if not self.screen or not self.targets or not self.genes:
            raise ScreenBaselineError("nonempty screen, target and gene universe required")
        if len(set(self.targets)) != len(self.targets) or len(set(self.genes)) != len(self.genes):
            raise ScreenBaselineError("duplicate target or gene identity")
        if (len(self.source_csv_sha256) != 64 or
                any(c not in "0123456789abcdef" for c in self.source_csv_sha256)):
            raise ScreenBaselineError("missing source CSV SHA256")
        if self.effects.shape != (len(self.targets), len(self.genes)):
            raise ScreenBaselineError("profile geometry/identity mismatch")
        if not np.issubdtype(self.effects.dtype, np.floating):
            raise ScreenBaselineError("profile values must be floating point")
        if np.isinf(self.effects).any():
            raise ScreenBaselineError("infinite effect is invalid")


def load_verified_screen_gzip(path: str | Path, *, screen: str,
                              expected_csv_sha256: str) -> ScreenProfiles:
    """Verify the decompressed, provider-authored CSV before parsing any outcomes."""
    if len(expected_csv_sha256) != 64:
        raise ScreenBaselineError("an exact uncompressed CSV SHA256 is required")
    h = hashlib.sha256()
    with gzip.open(path, "rb") as raw:
        for block in iter(lambda: raw.read(1 << 20), b""):
            h.update(block)
    observed = h.hexdigest()
    if observed != expected_csv_sha256:
        raise ScreenBaselineError("source CSV SHA256 mismatch; no result authorized")
    entries: dict[tuple[str, str], float] = {}
    targets: set[str] = set()
    genes: set[str] = set()
    with gzip.open(path, "rt", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not {"name", "Gene", "Log2FC"} <= set(reader.fieldnames or []):
            raise ScreenBaselineError("CRISPRbrain source columns missing")
        for row in reader:
            target = row["name"].strip()
            gene = row["Gene"].strip()
            if not target or not gene or (target, gene) in entries:
                raise ScreenBaselineError("empty or duplicate original target/gene identity")
            try:
                value = float(row["Log2FC"])
            except (TypeError, ValueError) as exc:
                raise ScreenBaselineError("invalid observed Log2FC") from exc
            if not np.isfinite(value):
                raise ScreenBaselineError("nonfinite source effect; review before use")
            entries[(target, gene)] = value
            targets.add(target)
            genes.add(gene)
    ordered_targets, ordered_genes = tuple(sorted(targets)), tuple(sorted(genes))
    mat = np.full((len(ordered_targets), len(ordered_genes)), np.nan, dtype=np.float64)
    ti = {name: i for i, name in enumerate(ordered_targets)}
    gi = {name: i for i, name in enumerate(ordered_genes)}
    for (target, gene), effect in entries.items():
        mat[ti[target], gi[gene]] = effect
    out = ScreenProfiles(screen, observed, ordered_targets, ordered_genes, mat)
    out.validate()
    return out


def fixed_target_folds(profiles: ScreenProfiles, *, seed: str, n_folds: int = 5) -> dict[str, int]:
    """Balanced deterministic target splits; all source outcomes already DEVELOPMENT."""
    profiles.validate()
    if not seed or n_folds < 2 or len(profiles.targets) < n_folds:
        raise ScreenBaselineError("fixed seed and >=one target per fold required")
    order = sorted(profiles.targets, key=lambda t: (
        hashlib.sha256(json.dumps([seed, profiles.screen, t]).encode()).hexdigest(), t,
    ))
    return {target: idx % n_folds for idx, target in enumerate(order)}


def score_retrospective_baselines(
    profiles: ScreenProfiles, *, seed: str, n_folds: int = 5,
) -> dict:
    """No-change vs equal TRAIN-target mean; score only mutually estimable genes.

    Every target is evaluated only in its held-out fold, excluding its OWN
    perturbed gene from evaluation. A screen profile is not a donor sample and
    folds are DEVELOPMENT partitions, not untouched prospective test cohorts.
    """
    profiles.validate()
    folds = fixed_target_folds(profiles, seed=seed, n_folds=n_folds)
    data = profiles.effects
    gidx = {name: i for i, name in enumerate(profiles.genes)}
    per_target: list[dict] = []
    for fold in range(n_folds):
        train = np.asarray([folds[t] != fold for t in profiles.targets])
        test = np.asarray([folds[t] == fold for t in profiles.targets])
        if not train.any() or not test.any():
            raise ScreenBaselineError("empty train/test fold")
        train_data = data[train]
        n_train = np.isfinite(train_data).sum(axis=0)
        train_mean = np.full(data.shape[1], np.nan)
        supported = n_train > 0
        train_mean[supported] = np.nansum(train_data[:, supported], axis=0) / n_train[supported]
        for i in np.flatnonzero(test):
            target = profiles.targets[int(i)]
            own_gene_col = gidx.get(target)
            observed = data[i]
            measured = np.isfinite(observed)
            if own_gene_col is not None:
                measured[own_gene_col] = False
            paired = measured & np.isfinite(train_mean)
            if not paired.any():
                per_target.append({"target": target, "fold": fold, "status": "NOT_ESTIMABLE",
                                   "measured_genes_excluding_target": int(measured.sum()),
                                   "scored_genes": 0})
                continue
            error_zero = observed[paired]
            error_mean = observed[paired] - train_mean[paired]
            per_target.append({
                "target": target, "fold": fold, "status": "ESTIMABLE",
                "measured_genes_excluding_target": int(measured.sum()),
                "scored_genes": int(paired.sum()),
                "no_change_mae": float(np.mean(np.abs(error_zero))),
                "no_change_rmse": float(np.sqrt(np.mean(error_zero ** 2))),
                "train_target_equal_mean_mae": float(np.mean(np.abs(error_mean))),
                "train_target_equal_mean_rmse": float(np.sqrt(np.mean(error_mean ** 2))),
            })
    observed_rows = [r for r in per_target if r["status"] == "ESTIMABLE"]
    def macro(key: str) -> float | None:
        return float(np.mean([r[key] for r in observed_rows])) if observed_rows else None
    return {
        "schema": "CRISPRBRAIN_SCREEN_RETROSPECTIVE_BASELINES_V1",
        "screen": profiles.screen,
        "source_uncompressed_csv_sha256": profiles.source_csv_sha256,
        "split_seed": seed, "n_folds": n_folds,
        "targets": len(profiles.targets),
        "targets_estimable": len(observed_rows),
        "genes_in_original_screen": len(profiles.genes),
        "exposure": "DEVELOPMENT_RETROSPECTIVE_ALREADY_INSPECTED",
        "split_kind": "TARGET_HELDOUT_WITHIN_SAME_EXPERIMENT_NOT_INDEPENDENT_VALIDATION",
        "scoring": "MACRO_TARGET_EQUAL_WEIGHT_OFF_TARGET_SAME_FEATURE_SUPPORT",
        "original_feature_namespace": "PROVIDER_GENE_LABEL_UNHARMONIZED_WITH_FULL104",
        "biological_uncertainty_estimable": False,
        "independent_confirmation_authorized": False,
        "brain_causal_generalization_authorized": False,
        "jepa_prediction_used": False,
        "jepa_training_authorized": False,
        "therapeutic_ranking_authorized": False,
        "macro": {
            "no_change_mae": macro("no_change_mae"),
            "no_change_rmse": macro("no_change_rmse"),
            "train_target_equal_mean_mae": macro("train_target_equal_mean_mae"),
            "train_target_equal_mean_rmse": macro("train_target_equal_mean_rmse"),
        },
        "per_target": sorted(per_target, key=lambda r: r["target"]),
    }
