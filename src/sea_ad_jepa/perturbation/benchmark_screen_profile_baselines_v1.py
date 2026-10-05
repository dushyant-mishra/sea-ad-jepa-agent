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
    responsive_roots: dict[str, str] = {}
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
        # Secondary DEVELOPMENT diagnostic. Genes are selected solely from
        # training-target effect magnitudes, never from a held-out target's
        # apparent response. The 10% rule is post-exposure development only.
        reactivity = np.full(data.shape[1], -np.inf)
        reactivity[supported] = (
            np.nansum(np.abs(train_data[:, supported]), axis=0)
            / n_train[supported]
        )
        ranked = sorted(
            np.flatnonzero(supported),
            key=lambda j: (-reactivity[int(j)], profiles.genes[int(j)]),
        )
        n_reactive = max(1, int(np.ceil(0.10 * len(ranked))))
        reactive_indices = np.asarray(ranked[:n_reactive], dtype=int)
        reactive_mask = np.zeros(data.shape[1], dtype=bool)
        reactive_mask[reactive_indices] = True
        responsive_roots[str(fold)] = hashlib.sha256(
            json.dumps(sorted(profiles.genes[int(j)] for j in reactive_indices)).encode()
        ).hexdigest()
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
            reactive_paired = paired & reactive_mask
            reactive_zero = observed[reactive_paired]
            reactive_mean = observed[reactive_paired] - train_mean[reactive_paired]
            per_target.append({
                "target": target, "fold": fold, "status": "ESTIMABLE",
                "measured_genes_excluding_target": int(measured.sum()),
                "scored_genes": int(paired.sum()),
                "no_change_mae": float(np.mean(np.abs(error_zero))),
                "no_change_rmse": float(np.sqrt(np.mean(error_zero ** 2))),
                "train_target_equal_mean_mae": float(np.mean(np.abs(error_mean))),
                "train_target_equal_mean_rmse": float(np.sqrt(np.mean(error_mean ** 2))),
                "training_only_reactive_genes_scored": int(reactive_paired.sum()),
                "reactive_no_change_mae": float(np.mean(np.abs(reactive_zero)))
                    if reactive_zero.size else None,
                "reactive_train_mean_mae": float(np.mean(np.abs(reactive_mean)))
                    if reactive_mean.size else None,
            })
    observed_rows = [r for r in per_target if r["status"] == "ESTIMABLE"]
    def macro(key: str) -> float | None:
        values = [r[key] for r in observed_rows if r.get(key) is not None]
        return float(np.mean(values)) if values else None
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
        "responsive_subset": {
            "scope": "SECONDARY_DEVELOPMENT_DIAGNOSTIC",
            "selection": "TOP_10_PERCENT_BY_MEAN_ABSOLUTE_EFFECT_TRAIN_TARGETS_ONLY",
            "selection_digest_by_fold": responsive_roots,
            "macro_no_change_mae": macro("reactive_no_change_mae"),
            "macro_train_target_equal_mean_mae": macro("reactive_train_mean_mae"),
        },
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
