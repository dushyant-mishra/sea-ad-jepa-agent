"""Prospective scale-free relational target mechanics for Teacher/Student V4.

This module is deliberately *not* called by ``production_update``.  It turns the
surviving Target Discovery object (anchored distance ordering) into an auditable,
differentiable teacher->student target without matching absolute distance
magnitudes.  Activation still requires learned-teacher continuity, partial-
evidence qualification, full-reader schedule authority, and an explicit
execution contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import log
from numbers import Integral
from typing import Sequence

import torch
import torch.nn.functional as F

RELATIONAL_DIMENSION = 160
EVIDENCE_LEVELS = (20, 40, 60, 80, 100)
TRAINABLE_EVIDENCE_LEVELS_PROSPECTIVE = (20, 40, 60, 80)
CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL = 60
DEFAULT_MIN_GROUP_SIZE = 3
LOG_TWO = log(2.0)


@dataclass(frozen=True)
class CollapseCalibration:
    """Externally frozen teacher-relative geometry floors.

    No numerical defaults are provided because 50k Target Discovery is not
    permitted to set production collapse thresholds.
    """

    min_variance_ratio: float
    min_spread_ratio: float
    min_effective_rank_ratio: float

    def validate(self) -> None:
        for name, value in (
            ("min_variance_ratio", self.min_variance_ratio),
            ("min_spread_ratio", self.min_spread_ratio),
            ("min_effective_rank_ratio", self.min_effective_rank_ratio),
        ):
            value = float(value)
            if not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must lie in (0,1]")


def _require_authority_int(value: object, *, name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer authority value")
    out = int(value)
    if minimum is not None and out < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return out


def hidden_fraction_for_evidence(evidence_percent: int) -> float:
    evidence_percent = _require_authority_int(evidence_percent, name="evidence_percent")
    if evidence_percent not in EVIDENCE_LEVELS:
        raise ValueError(f"unsupported evidence level: {evidence_percent}")
    return (100.0 - evidence_percent) / 100.0


def validate_cell_states(teacher: torch.Tensor, student: torch.Tensor) -> None:
    if teacher.ndim != 2 or student.ndim != 2:
        raise ValueError("teacher and student cell_state must be [cells,width]")
    if teacher.shape != student.shape:
        raise ValueError("teacher/student cell_state shapes differ")
    if teacher.shape[1] != RELATIONAL_DIMENSION:
        raise ValueError(f"expected {RELATIONAL_DIMENSION}-D cell_state")
    if not teacher.is_floating_point() or not student.is_floating_point():
        raise ValueError("cell_state must be floating point")
    if not bool(torch.isfinite(teacher).all()) or not bool(torch.isfinite(student).all()):
        raise ValueError("cell_state contains nonfinite values")


def _validate_group_ids(group_ids: torch.Tensor, cells: int) -> torch.Tensor:
    if group_ids.ndim != 1 or len(group_ids) != cells:
        raise ValueError("group_ids must be one-dimensional and match cell count")
    if group_ids.dtype not in (torch.int32, torch.int64):
        raise ValueError("group_ids must use an integer dtype")
    return group_ids


def cosine_distance_matrix(states: torch.Tensor) -> torch.Tensor:
    """Direct-cell-state cosine distance with fail-closed zero-norm handling."""
    if states.ndim != 2 or not states.is_floating_point():
        raise ValueError("states must be floating [cells,width]")
    if not bool(torch.isfinite(states).all()):
        raise ValueError("states contain nonfinite values")
    norms = states.float().norm(dim=1)
    if bool((norms <= 0).any()):
        raise ValueError("cosine geometry undefined for zero-norm cell_state")
    unit = states.float() / norms[:, None]
    cosine = (unit @ unit.T).clamp(-1.0, 1.0)
    return 1.0 - cosine


def enumerate_within_group_triplets(
    group_ids: torch.Tensor,
    *,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
) -> torch.Tensor:
    """Deterministically enumerate anchor + unordered comparator pairs.

    For each eligible group and anchor ``i``, every pair ``j < k`` among the
    remaining group members is emitted exactly once.  No cross-group relation
    can enter the target.
    """
    min_group_size = _require_authority_int(
        min_group_size, name="min_group_size", minimum=3
    )
    group_ids = _validate_group_ids(group_ids, len(group_ids))
    cpu_ids = group_ids.detach().cpu()
    triplets: list[tuple[int, int, int]] = []
    for group in torch.unique(cpu_ids, sorted=True):
        idx = torch.nonzero(cpu_ids.eq(group), as_tuple=False).flatten().tolist()
        if len(idx) < min_group_size:
            continue
        for anchor in idx:
            others = [x for x in idx if x != anchor]
            for j, k in combinations(others, 2):
                triplets.append((anchor, j, k))
    if not triplets:
        raise ValueError("no relational group yields an eligible triplet")
    return torch.tensor(triplets, dtype=torch.int64, device=group_ids.device)


def validate_frozen_triplets(
    triplets: torch.Tensor,
    group_ids: torch.Tensor,
    *,
    cells: int,
) -> torch.Tensor:
    """Validate externally frozen global/mesoscale triplet identities.

    This is the only route for a later mesoscale authority: the target module
    accepts exact frozen triplets but never chooses a neighborhood fraction or
    k on its own.
    """
    group_ids = _validate_group_ids(group_ids, cells)
    if triplets.ndim != 2 or triplets.shape[1] != 3 or triplets.dtype != torch.int64:
        raise ValueError("triplets must be int64 [triplets,3]")
    if len(triplets) == 0:
        raise ValueError("triplet set is empty")
    if int(triplets.min()) < 0 or int(triplets.max()) >= cells:
        raise ValueError("triplet index out of range")
    if bool((triplets[:, 0] == triplets[:, 1]).any()) or bool((triplets[:, 0] == triplets[:, 2]).any()) or bool((triplets[:, 1] == triplets[:, 2]).any()):
        raise ValueError("triplet cells must be distinct")
    if not bool((triplets[:, 1] < triplets[:, 2]).all()):
        raise ValueError("frozen triplets must use canonical comparator order j < k")
    gids = group_ids.to(triplets.device)
    gi, gj, gk = gids[triplets[:, 0]], gids[triplets[:, 1]], gids[triplets[:, 2]]
    if not bool(((gi == gj) & (gi == gk)).all()):
        raise ValueError("frozen triplet crosses relational group")
    # Duplicate rows, including comparator-swapped duplicates, would silently
    # overweight one anchored relation. Comparator order is not itself a new
    # relation because the teacher sign is recomputed from the same two cells.
    cpu = triplets.detach().cpu()
    canonical = torch.stack(
        (cpu[:, 0], torch.minimum(cpu[:, 1], cpu[:, 2]), torch.maximum(cpu[:, 1], cpu[:, 2])),
        dim=1,
    )
    if len(torch.unique(canonical, dim=0)) != len(triplets):
        raise ValueError("duplicate frozen anchored relation")
    return triplets


def _triplet_deltas(distance: torch.Tensor, triplets: torch.Tensor) -> torch.Tensor:
    i, j, k = triplets[:, 0], triplets[:, 1], triplets[:, 2]
    # Positive delta means j is closer to anchor i than k.
    return distance[i, k] - distance[i, j]


def scale_free_triplet_order_loss(
    teacher_cell_state: torch.Tensor,
    student_cell_state: torch.Tensor,
    group_ids: torch.Tensor,
    *,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
    frozen_triplets: torch.Tensor | None = None,
) -> dict[str, torch.Tensor]:
    """Differentiable anchored-order target aligned to TD57B/TD59 semantics.

    Teacher supervision is *only* the sign of ``d(i,k)-d(i,j)`` under direct
    160-D cosine distance.  Absolute teacher distances, their scale, and angles
    are not matched.  Student order is trained with a parameter-free logistic
    ranking surrogate:

        softplus(- y * (d_s(i,k)-d_s(i,j))) / log(2)

    where ``y`` is the teacher order sign.  A student tie therefore has loss 1,
    correct order has loss < 1, and reversed order has loss > 1.  Positive
    per-cell rescaling cannot game the objective because cosine distance is
    norm-invariant.
    """
    validate_cell_states(teacher_cell_state, student_cell_state)
    group_ids = _validate_group_ids(group_ids, len(teacher_cell_state)).to(teacher_cell_state.device)
    if student_cell_state.device != teacher_cell_state.device:
        raise ValueError("teacher/student cell_state must be on the same device")

    if frozen_triplets is None:
        triplets = enumerate_within_group_triplets(group_ids, min_group_size=min_group_size)
    else:
        triplets = validate_frozen_triplets(
            frozen_triplets.to(teacher_cell_state.device), group_ids, cells=len(teacher_cell_state)
        )

    teacher_distance = cosine_distance_matrix(teacher_cell_state.detach())
    student_distance = cosine_distance_matrix(student_cell_state)
    teacher_delta = _triplet_deltas(teacher_distance, triplets)
    student_delta = _triplet_deltas(student_distance, triplets)

    labels = torch.sign(teacher_delta)
    resolved = labels.ne(0)
    if not bool(resolved.any()):
        raise ValueError("teacher has no resolved triplet orders")

    signed_margin = labels[resolved] * student_delta[resolved]
    per_triplet = F.softplus(-signed_margin) / LOG_TWO
    loss = per_triplet.mean()

    student_sign = torch.sign(student_delta[resolved])
    agreement = student_sign.eq(labels[resolved]) & student_sign.ne(0)
    return {
        "loss": loss,
        "triplet_count": torch.tensor(len(triplets), dtype=torch.int64, device=loss.device),
        "teacher_resolved_count": resolved.sum(),
        "teacher_unresolved_count": (~resolved).sum(),
        "student_tie_count_on_teacher_resolved": student_sign.eq(0).sum(),
        "order_agreement": agreement.float().mean().detach(),
        "mean_signed_student_margin": signed_margin.mean().detach(),
    }


def triplet_order_agreement(
    teacher_cell_state: torch.Tensor,
    student_cell_state: torch.Tensor,
    group_ids: torch.Tensor,
    *,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
    frozen_triplets: torch.Tensor | None = None,
) -> dict[str, torch.Tensor]:
    """Non-loss qualification statistic using the same exact order relation."""
    report = scale_free_triplet_order_loss(
        teacher_cell_state,
        student_cell_state,
        group_ids,
        min_group_size=min_group_size,
        frozen_triplets=frozen_triplets,
    )
    return {
        key: value.detach() if isinstance(value, torch.Tensor) else value
        for key, value in report.items()
        if key != "loss"
    }


def effective_rank(states: torch.Tensor) -> torch.Tensor:
    if states.ndim != 2 or len(states) < 2 or not states.is_floating_point():
        raise ValueError("effective_rank requires floating [cells,width] with at least 2 cells")
    if not bool(torch.isfinite(states).all()):
        raise ValueError("effective_rank states contain nonfinite values")
    centered = states.float() - states.float().mean(dim=0, keepdim=True)
    singular = torch.linalg.svdvals(centered)
    power = singular.square()
    total = power.sum()
    if not bool(torch.isfinite(total)) or float(total.detach()) <= 0:
        return torch.zeros((), dtype=torch.float32, device=states.device)
    p = power / total
    entropy = -(p[p > 0] * p[p > 0].log()).sum()
    return entropy.exp()


def geometry_health(
    states: torch.Tensor,
    group_ids: torch.Tensor,
    *,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
) -> dict[str, torch.Tensor]:
    """Per-group anti-collapse telemetry with no pooled rescue.

    Every eligible relational group is measured separately.  A later collapse
    calibration compares the same group IDs teacher-to-student and rejects if
    *any* group falls below its externally frozen floor.
    """
    if states.ndim != 2 or not states.is_floating_point() or not bool(torch.isfinite(states).all()):
        raise ValueError("states must be finite floating [cells,width]")
    min_group_size = _require_authority_int(
        min_group_size, name="min_group_size", minimum=3
    )
    group_ids = _validate_group_ids(group_ids, len(states)).to(states.device)
    eligible_group_ids: list[torch.Tensor] = []
    variances: list[torch.Tensor] = []
    spreads: list[torch.Tensor] = []
    effective_ranks: list[torch.Tensor] = []
    eligible_cells = 0
    for group in torch.unique(group_ids, sorted=True):
        idx = torch.nonzero(group_ids.eq(group), as_tuple=False).flatten()
        if len(idx) < min_group_size:
            continue
        chunk = states[idx].float()
        centered = chunk - chunk.mean(dim=0, keepdim=True)
        d = torch.cdist(centered, centered)
        mask = torch.triu(torch.ones_like(d, dtype=torch.bool), diagonal=1)
        eligible_group_ids.append(group.to(torch.int64))
        variances.append(centered.square().mean())
        spreads.append(d[mask].median())
        effective_ranks.append(effective_rank(centered))
        eligible_cells += len(idx)
    if not eligible_group_ids:
        raise ValueError("no relational group meets minimum group size")
    return {
        "group_ids": torch.stack(eligible_group_ids),
        "variance_by_group": torch.stack(variances),
        "pairwise_spread_by_group": torch.stack(spreads),
        "effective_rank_by_group": torch.stack(effective_ranks),
        "eligible_cells": torch.tensor(eligible_cells, dtype=torch.int64, device=states.device),
    }


def enforce_collapse_calibration(
    teacher_health: dict[str, torch.Tensor],
    student_health: dict[str, torch.Tensor],
    calibration: CollapseCalibration,
) -> dict[str, float]:
    """Require every matched relational group to clear every collapse floor."""
    calibration.validate()
    teacher_groups = teacher_health.get("group_ids")
    student_groups = student_health.get("group_ids")
    if teacher_groups is None or student_groups is None:
        raise RuntimeError("per-group collapse telemetry missing group IDs")
    if teacher_groups.shape != student_groups.shape or not torch.equal(
        teacher_groups.detach().cpu(), student_groups.detach().cpu()
    ):
        raise RuntimeError("teacher/student collapse group identities differ")

    ratios: dict[str, float] = {}
    mapping = (
        ("variance_by_group", calibration.min_variance_ratio),
        ("pairwise_spread_by_group", calibration.min_spread_ratio),
        ("effective_rank_by_group", calibration.min_effective_rank_ratio),
    )
    for key, threshold in mapping:
        teacher_values = teacher_health.get(key)
        student_values = student_health.get(key)
        if teacher_values is None or student_values is None:
            raise RuntimeError(f"per-group collapse metric missing: {key}")
        if teacher_values.shape != teacher_groups.shape or student_values.shape != teacher_groups.shape:
            raise RuntimeError(f"per-group collapse metric shape mismatch: {key}")
        if not bool(torch.isfinite(teacher_values).all()) or not bool(torch.isfinite(student_values).all()):
            raise RuntimeError(f"nonfinite collapse metric: {key}")
        if bool((teacher_values <= 0).any()) or bool((student_values <= 0).any()):
            raise RuntimeError(f"collapsed or invalid geometry: {key}")
        metric_ratios = student_values.float() / teacher_values.float()
        failing = metric_ratios < float(threshold)
        if bool(failing.any()):
            first = int(torch.nonzero(failing, as_tuple=False).flatten()[0])
            group = int(teacher_groups[first].detach().cpu())
            ratio = float(metric_ratios[first].detach().cpu())
            raise RuntimeError(
                f"relational collapse gate rejected {key} in group {group}: "
                f"ratio={ratio} threshold={threshold}"
            )
        ratios[key] = float(metric_ratios.min().detach().cpu())
    ratios["groups_checked"] = float(len(teacher_groups))
    return ratios

def fine_matched_null_permutation(
    fine_stratum_ids: torch.Tensor,
    *,
    seed: int,
) -> torch.Tensor:
    """Qualification-only deterministic no-fixed-point within-stratum null."""
    if fine_stratum_ids.ndim != 1:
        raise ValueError("fine_stratum_ids must be one-dimensional")
    if fine_stratum_ids.dtype not in (torch.int32, torch.int64):
        raise ValueError("fine_stratum_ids must use an integer dtype")
    seed = _require_authority_int(seed, name="seed")
    ids = fine_stratum_ids.detach().cpu()
    generator = torch.Generator(device="cpu").manual_seed(seed)
    perm = torch.arange(len(ids), dtype=torch.int64)
    for group in torch.unique(ids, sorted=True):
        idx = torch.nonzero(ids.eq(group), as_tuple=False).flatten()
        if len(idx) < 2:
            raise ValueError("fine-matched null stratum has fewer than 2 cells")
        order = idx[torch.randperm(len(idx), generator=generator)]
        perm[order] = order.roll(-1)
    if bool((perm == torch.arange(len(perm))).any()):
        raise RuntimeError("fine-matched null failed to derange all cells")
    return perm


def relational_batch_contract(
    donor_ids: Sequence[str],
    operator_ids: Sequence[str],
    *,
    group_size: int,
    groups_per_batch: int,
    expected_batch_size: int,
) -> dict[str, object]:
    """Validate an externally frozen grouped batch geometry.

    ``group_size``, ``groups_per_batch``, and ``expected_batch_size``
    intentionally have no defaults: the full-reader schedule authority, not
    this pilot/mechanics package, must provide them before relational training
    can be activated.
    """
    group_size = _require_authority_int(group_size, name="group_size", minimum=3)
    groups_per_batch = _require_authority_int(
        groups_per_batch, name="groups_per_batch", minimum=1
    )
    expected_batch_size = _require_authority_int(
        expected_batch_size, name="expected_batch_size", minimum=3
    )
    if group_size * groups_per_batch != expected_batch_size:
        raise ValueError("relational grouping does not match expected batch size")
    if len(donor_ids) != expected_batch_size or len(operator_ids) != expected_batch_size:
        raise ValueError("identity vectors do not match expected batch size")
    counts: dict[tuple[str, str], int] = {}
    for donor, operator in zip(donor_ids, operator_ids):
        if not isinstance(donor, str) or not donor or not isinstance(operator, str) or not operator:
            raise ValueError("donor/operator IDs must be nonempty canonical strings")
        key = (donor, operator)
        counts[key] = counts.get(key, 0) + 1
    if len(counts) != groups_per_batch or any(v != group_size for v in counts.values()):
        raise RuntimeError(
            f"expected {groups_per_batch} donor-by-operator groups of {group_size}; got {counts}"
        )
    return {
        "cells": expected_batch_size,
        "groups": groups_per_batch,
        "cells_per_group": group_size,
        "grouping": "canonical_donor_id x operator_id",
    }
