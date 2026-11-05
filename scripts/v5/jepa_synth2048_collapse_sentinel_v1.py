#!/usr/bin/env python3
"""Failure-only JEPA synthetic sentinel grounded in actual R03/R04, Stage81A3, C2 history.

No synthetic target/C1-C6 PASS may be issued from its diagnostics.
Do not add learned variance/covariance penalties, invent collapse thresholds,
choose EMA timescales, or promote a checkpoint from this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np

SCHEMA = "JEPA_SYNTH2048_FAILURE_ONLY_SENTINEL_V1"
REQUIRE_GENE_ANCHOR_WEIGHT = 0.0  # Stage81B rejected the old anchor
PRODUCTION_TRAINING_AUTHORIZED = False


class CollapseStop(RuntimeError):
    """A factual mechanical failure that cannot be ignored."""


@dataclass(frozen=True)
class GeometryReport:
    status: str
    cells: int
    dimensions: int
    finite: bool
    exactly_constant_across_cells: bool
    centered_energy: float
    cell_state_effective_rank: float | None
    top_singular_energy_fraction: float | None
    per_dimension_std_median: float
    median_pairwise_distance: float | None
    interpretation: str
    qualified_biological_representation: bool = False


def geometry_diagnostic(states: np.ndarray) -> GeometryReport:
    """Historical raw-latent centered singular diagnostics, no tuned cutoffs.

    Exactly constant/nonfinite CELL state is a hard mechanical STOP.
    Low rank or top-singular dominance alone is a WARNING, not automatic failure:
    genuine low-rank biological worlds exist (#438). Never report a PASS.
    """
    x = np.asarray(states)
    if x.ndim != 2 or min(x.shape) < 2:
        raise CollapseStop("CELL geometry requires >=2 cells and >=2 coordinates")
    if x.dtype.kind not in "fiu":
        raise CollapseStop("non-numeric CELL state")
    a = x.astype(np.float64, copy=False)
    if not np.isfinite(a).all():
        raise CollapseStop("nonfinite CELL state")
    centered = a - a.mean(axis=0, keepdims=True)
    if not np.any(centered):
        raise CollapseStop("exactly constant CELL state (old collapse mode)")
    std = np.std(a, axis=0, ddof=0)
    # Two-cell U0 is mathematically rank <= 1 by construction. Reporting
    # "effective rank 1" as collapse would be scientifically misleading.
    # Eight is a descriptive telemetry reporting minimum, NOT a pass criterion.
    if len(a) < 8:
        energy = float(np.sum(centered * centered))
        return GeometryReport(
            status="NOT_ESTIMABLE_TOO_FEW_CELLS_FOR_GEOMETRY",
            cells=len(a), dimensions=a.shape[1], finite=True,
            exactly_constant_across_cells=False,
            centered_energy=energy, cell_state_effective_rank=None,
            top_singular_energy_fraction=None,
            per_dimension_std_median=float(np.median(std)),
            median_pairwise_distance=None,
            interpretation="U0_ONLY__GEOMETRY_RANK_NOT_IDENTIFIABLE__NO_PASS",
        )
    spectrum = np.linalg.svd(centered, compute_uv=False)
    squared = spectrum * spectrum
    energy = float(np.sum(squared))
    if not math.isfinite(energy) or energy <= 0:
        raise CollapseStop("zero/nonfinite centered CELL energy")
    p = spectrum[spectrum > 0] / spectrum.sum()
    effective_rank = math.exp(-float(np.sum(p * np.log(p))))
    top_fraction = float(squared.max() / energy)
    distances: list[float] = []
    # Deterministic bounded first-32-cell diagnostic; not a donor-weighted estimator.
    sub = a[:min(32, len(a))]
    for i in range(len(sub)):
        for j in range(i+1, len(sub)):
            distances.append(float(np.linalg.norm(sub[i] - sub[j])))
    return GeometryReport(
        status="UNQUALIFIED_GEOMETRY_TELEMETRY_ONLY",
        cells=len(a), dimensions=a.shape[1], finite=True,
        exactly_constant_across_cells=False,
        centered_energy=energy,
        cell_state_effective_rank=effective_rank,
        top_singular_energy_fraction=top_fraction,
        per_dimension_std_median=float(np.median(std)),
        median_pairwise_distance=float(np.median(distances)) if distances else None,
        interpretation="RAW_CELL_GEOMETRY_ONLY__LOW_RANK_MAY_BE_REAL_BIOLOGY__NO_PASS",
    )



def token_geometry_diagnostic(
    states: np.ndarray, *, gene_ids: np.ndarray | None = None,
) -> dict[str, object]:
    """Check BOTH gene-token collapse axes, aligned by physical gene identity.

    Original #548 checked only 'every gene within a cell is identical'.
    Macha #552 showed the opposite failure: every *same gene* token can be
    identical across distinct cells, yielding identity-only JEPA predictions
    while CELL embeddings are not collapsed. Positions cannot be compared
    when structural measurements/masks differ: use supplied exact gene IDs.

    No tuned threshold: exact-equality failure is a mechanical STOP; partial
    cell-specific diversity is telemetry ONLY, NOT biology qualification.
    """
    x = np.asarray(states)
    if x.ndim != 3 or min(x.shape) < 2 or x.dtype.kind not in "fiu":
        raise CollapseStop("gene-token geometry requires numeric [cells,tokens,width]")
    a = x.astype(np.float64, copy=False)
    if not np.isfinite(a).all():
        raise CollapseStop("nonfinite gene-token state")

    if gene_ids is None:
        # Compatibility with original synthetic fixture tests only; real V5
        # must pass packed canonical gene IDs to avoid comparing shifted tokens.
        ids = np.broadcast_to(
            np.arange(a.shape[1], dtype=np.int64), a.shape[:2]
        )
        alignment = "POSITIONAL_SYNTHETIC_ONLY__NO_SUPPORT_PARITY_AUTHORITY"
    else:
        raw = np.asarray(gene_ids)
        if raw.shape != a.shape[:2] or raw.dtype.kind not in "iu":
            raise CollapseStop("gene IDs must be integral [cells,tokens] aligned to states")
        ids = raw
        if (ids < 0).any():
            raise CollapseStop("negative invalid or padding gene ID")
        if any(len(np.unique(row)) != len(row) for row in ids):
            raise CollapseStop("duplicate physical gene ID within a cell")
        alignment = "EXPLICIT_CANONICAL_GENE_IDS"

    within_equal = np.all(a == a[:, :1, :], axis=(1, 2))
    if np.any(within_equal):
        raise CollapseStop("exactly identical gene-token states within a cell")

    # Accumulate first-seen gene token per canonical address, compare the
    # *same* address across all participating cells regardless of column.
    first_by_gene: dict[int, np.ndarray] = {}
    observations_by_gene: dict[int, int] = {}
    varying_gene: set[int] = set()
    for row in range(a.shape[0]):
        for col in range(a.shape[1]):
            gene = int(ids[row, col])
            vec = a[row, col]
            if gene in first_by_gene:
                observations_by_gene[gene] += 1
                if not np.array_equal(vec, first_by_gene[gene]):
                    varying_gene.add(gene)
            else:
                first_by_gene[gene] = vec
                observations_by_gene[gene] = 1

    shared = {gene for gene, n in observations_by_gene.items() if n >= 2}
    if shared and not varying_gene:
        raise CollapseStop(
            "identity-only gene-token collapse: aligned same-gene tokens "
            "are exactly invariant across all observed cells"
        )

    within_std = np.std(a, axis=1, ddof=0)
    return {
        "status": (
            "UNQUALIFIED_TOKEN_GEOMETRY_TELEMETRY_ONLY" if shared
            else "NOT_ESTIMABLE_NO_SHARED_GENE_IDS"
        ),
        "cells": int(a.shape[0]),
        "tokens_per_cell": int(a.shape[1]),
        "width": int(a.shape[2]),
        "within_cell_feature_std_median": float(np.median(within_std)),
        "exact_token_collapsed_cells": 0,
        "shared_gene_ids_compared_across_cells": len(shared),
        "shared_gene_ids_with_cell_specific_states": len(varying_gene),
        "shared_gene_ids_without_detected_cell_specific_states": (
            len(shared) - len(varying_gene)
        ),
        "gene_id_alignment": alignment,
        "qualified_biological_representation": False,
    }



def check_encoder_gradient_registry(online: object) -> dict:
    """Reuse exactly the accepted C2 48-mandatory-tensor registry, not a new norm gate."""
    from scripts.v4.c2_mandatory_gradient_gate_v1 import enforce_registry
    receipt = enforce_registry(online)
    if receipt["discovered_count"] != 48 or receipt["passed"] is not True:
        raise CollapseStop("48 protected encoder tensors not established")
    return {"registry": "ORIGINAL_C2_PROTECTED_48", "count": 48,
            "status": "STRUCTURAL_REGISTRY_ONLY__NO_GRADIENT_STEP"}


def enforce_live_update_gradients(online: object, predictor: object,
                                  teacher: object) -> dict:
    """Must be called after GradScaler.unscale_ and before every optimizer step.

    This is a verifier helper, not a runnable training or alternate mutation route.
    """
    from scripts.v4.c2_mandatory_gradient_gate_v1 import enforce, enforce_registry
    import torch
    enforce_registry(online)
    report = enforce(online)
    if report["total"] != 48:
        raise CollapseStop("mandatory protected-48 set changed")
    predictor_grads = list(predictor.named_parameters())
    if not predictor_grads:
        raise CollapseStop("predictor absent")
    for name, p in predictor_grads:
        g = p.grad
        if g is None or not bool(torch.isfinite(g).all()) or not bool((g != 0).any()):
            raise CollapseStop("missing/nonfinite/exact-zero predictor gradient: " + name)
    if any(p.grad is not None for p in teacher.parameters()):
        raise CollapseStop("EMA teacher received gradient")
    return {"status": "FINITE_NONZERO_48_AND_PREDICTOR_GRADIENTS__PRESTEP_ONLY",
            "protected_encoder": 48,
            "predictor_parameters_checked": len(predictor_grads),
            "ema_teacher_gradients": 0,
            "training_authorized": False}


def check_anchor_loss_weight(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CollapseStop("hidden-gene/CELL anchor weight must be exactly numeric zero")
    if not math.isfinite(float(value)) or float(value) != REQUIRE_GENE_ANCHOR_WEIGHT:
        raise CollapseStop("historically rejected hidden-gene/CELL anchor reintroduced")


def evaluate_training_record(record: Mapping[str, object]) -> dict:
    """Fail closed on known collapse/mechanics risks, NEVER infer success from loss.

    A completed synthetic rehearsal requires its own later independent donor-heldout
    biological readout. Falling loss, optimizer success and healthy global geometry
    can coexist with no masked biology (original Stage81A3 history).
    """
    mandatory = {
        "step_before", "step_after", "ema_updates", "teacher_gradients",
        "mandatory_gradient_gate", "adam_moment_gate", "student_cell_states",
        "train_jepa_loss", "hidden_anchor_weight",
    }
    if set(record) != mandatory:
        raise CollapseStop("required historical failure telemetry missing or unexpected")
    check_anchor_loss_weight(record["hidden_anchor_weight"])
    before, after = record["step_before"], record["step_after"]
    if isinstance(before, bool) or isinstance(after, bool) or not isinstance(before, int) or not isinstance(after, int):
        raise CollapseStop("optimizer counters must be exact integers")
    if before < 0 or after != before+1 or type(record["ema_updates"]) is not int or record["ema_updates"] != 1:
        raise CollapseStop("incomplete/skipped optimizer->EMA transition")
    if type(record["teacher_gradients"]) is not int or record["teacher_gradients"] != 0:
        raise CollapseStop("EMA teacher gradient violation")
    if record["mandatory_gradient_gate"] is not True:
        raise CollapseStop("C2 mandatory 48-parameter gradient protection not proven")
    if record["adam_moment_gate"] is not True:
        raise CollapseStop("mandatory Adam first/second moment protection not proven")
    loss = record["train_jepa_loss"]
    if isinstance(loss, bool) or not isinstance(loss, (int, float)) or not math.isfinite(float(loss)):
        raise CollapseStop("nonfinite/invalid JEPA training loss")
    geometry = geometry_diagnostic(np.asarray(record["student_cell_states"]))
    return {
        "schema": SCHEMA, "status": "MECHANICS_VALIDATION_ONLY__NO_BIOLOGICAL_PASS",
        "optimizer_step_verified": after, "ema_step_verified": True,
        "cell_geometry": geometry.__dict__,
        "must_compare_to_visible_RNA_and_wrong_cell_on_held_donors": True,
        "masked_student_biology_qualified": False,
        "teacher_biology_qualified": False,
        "all_six_C_candidates": "UNASSESSED",
        "authority": "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED",
    }


def check_biology_endpoint(*,
                           masked_student_score: float | None,
                           visible_rna_score: float | None,
                           wrong_cell_score: float | None,
                           genuine_donor_heldout: bool,
                           externally_authenticated: bool) -> str:
    """Never issue PASS here; detect non-improvement or missing trustworthy evidence."""
    if not genuine_donor_heldout or not externally_authenticated:
        return "NOT_ESTIMABLE__DONOR_OR_EXTERNAL_READOUT_UNVERIFIED"
    values = (masked_student_score, visible_rna_score, wrong_cell_score)
    if any(v is None or isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(float(v)) for v in values):
        return "STOP__MISSING_OR_NONFINITE_BIOLOGY_READOUT"
    if float(masked_student_score) <= float(visible_rna_score):
        return "FAIL__STUDENT_NOT_BETTER_THAN_VISIBLE_RNA"
    if float(masked_student_score) <= float(wrong_cell_score):
        return "FAIL__STUDENT_NOT_BETTER_THAN_WRONG_CELL"
    return "NOT_ESTIMABLE__POSITIVE_DEVELOPMENT_DIAGNOSTIC_NOT_PROTECTED_PASS"


def synthetic_training_readiness() -> dict:
    """No training launcher: list unresolved gates instead of inventing a YES."""
    return {
        "schema": SCHEMA, "current": "U0_MECHANICS_ONLY",
        "historical_failure_modes": [
            "Stage81A3_V4A_FALLING_LOSS_BUT_PLANTED_BIOLOGY_FAIL",
            "SIX_IPB_PARTIAL_CELL_MASKED_LEARNING_FAILURE",
            "R03_R04_CELL_AND_SLOT_COLLAPSE",
            "T1_128_8_FP16_BACKWARD_INSIDE_AUTOCAST_48_DEAD_ATTENTION_TENSORS",
            "STAGE81B_HIDDEN_GENE_ANCHOR_REJECTED",
            "UNQUALIFIED_TECHNICAL_SHORTCUT_AND_VISIBLE_RNA_REFERENCE",
        ],
        "mandatory_before_any_synthetic_training": [
            "V5_PERSISTED_GUARDED_MULTIUPDATE_SUCCESSOR_INDEPENDENTLY_REVIEWED",
            "SIX_BLOCK_48_PARAMETER_UNSCALED_GRADIENT_AND_ADAM_MOMENT_GATE_EVERY_STEP",
            "STUDENT_TEACHER_GENE_IDENTITY_AND_Q_RIGHTS_VERIFIED_PER_UPDATE",
            "RAW_CELL_AND_PER_TOKEN_GEOMETRY_HELD_DONOR_FULL_DATA_MONITOR",
            "FROZEN_BIOLOGY_VS_VISIBLE_RNA_WRONG_CELL_TECHNICAL_BASELINES",
            "NO_HIDDEN_GENE_ANCHOR_NO_COLLAPSE_PENALTY_TUNING_AFTER_RESULTS",
            "GPU_KEYED_RNG_PERFORMANCE_AND_CPU_CUDA_PARITY",
            "INDEPENDENT_MACHA_SOURCE_REVIEW_BEFORE_TRAINING",
        ],
        "synthetic_training_ready": False,
        "production_training_authorized": False,
    }
