"""Prospective relational geometry mechanics for the canonical teacher/student stack.

This module is intentionally NOT called by production_update. It freezes pure
relational estimators/loss mechanics that may be promoted only by a later
reviewed execution contract. The currently frozen healthy-teacher u0-to-u40
training base remains the block-JEPA objective at 60 percent evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import torch
import torch.nn.functional as F

REPRESENTATION = "teacher/student cell_state"
RELATIONAL_DIMENSION = 160
EVIDENCE_LEVELS = (20, 40, 60, 80, 100)
TRAINABLE_EVIDENCE_LEVELS_PROSPECTIVE = (20, 40, 60, 80)
CURRENT_FROZEN_TRAINING_EVIDENCE_LEVEL = 60
DEFAULT_MIN_GROUP_SIZE = 4


@dataclass(frozen=True)
class RelationalLossWeights:
    normalized_distance: float = 0.5
    angle: float = 0.5

    def validate(self) -> None:
        if self.normalized_distance < 0 or self.angle < 0:
            raise ValueError("relational loss weights must be non-negative")
        if self.normalized_distance + self.angle != 1.0:
            raise ValueError("relational loss weights must sum exactly to 1")


@dataclass(frozen=True)
class CollapseCalibration:
    """Externally frozen lower ratios relative to rich-teacher geometry.

    Numerical ratios are deliberately not defaulted here. Before relational
    training can become active they must be supplied by a separately reviewed,
    outcome-blind calibration artifact.
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
            if not 0.0 < float(value) <= 1.0:
                raise ValueError(f"{name} must lie in (0,1]")


def hidden_fraction_for_evidence(evidence_percent: int) -> float:
    evidence_percent = int(evidence_percent)
    if evidence_percent not in EVIDENCE_LEVELS:
        raise ValueError(f"unsupported evidence level: {evidence_percent}")
    return (100.0 - evidence_percent) / 100.0


def validate_cell_states(teacher: torch.Tensor, student: torch.Tensor) -> None:
    if teacher.ndim != 2 or student.ndim != 2:
        raise ValueError("teacher and student cell_state must be [cells, width]")
    if teacher.shape != student.shape:
        raise ValueError("teacher/student cell_state shapes differ")
    if teacher.shape[1] != RELATIONAL_DIMENSION:
        raise ValueError(f"expected {RELATIONAL_DIMENSION}-D cell_state")
    if not teacher.is_floating_point() or not student.is_floating_point():
        raise ValueError("cell_state must be floating point")
    if not bool(torch.isfinite(teacher).all()) or not bool(torch.isfinite(student).all()):
        raise ValueError("cell_state contains nonfinite values")


def group_pair_mask(
    group_ids: torch.Tensor, *, min_group_size: int = DEFAULT_MIN_GROUP_SIZE
) -> torch.Tensor:
    """Return upper-triangular within-group pair mask."""
    if group_ids.ndim != 1:
        raise ValueError("group_ids must be one-dimensional")
    if min_group_size < 3:
        raise ValueError("min_group_size must be at least 3")
    same = group_ids[:, None].eq(group_ids[None, :])
    counts = same.sum(dim=1)
    eligible = counts.ge(min_group_size)
    mask = same & eligible[:, None] & eligible[None, :]
    return torch.triu(mask, diagonal=1)


def _center_by_group(states: torch.Tensor, group_ids: torch.Tensor) -> torch.Tensor:
    centered = torch.empty_like(states)
    for group in torch.unique(group_ids, sorted=True):
        take = group_ids.eq(group)
        centered[take] = states[take] - states[take].mean(dim=0, keepdim=True)
    return centered


def _pair_geometry(
    states: torch.Tensor,
    group_ids: torch.Tensor,
    pair_mask: torch.Tensor,
    *,
    distance_scale: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    centered = _center_by_group(states, group_ids)
    norms = centered.norm(dim=1, keepdim=True)
    unit = centered / norms.clamp_min(torch.finfo(centered.dtype).eps)
    cosine = unit @ unit.T
    distance = torch.cdist(centered, centered, p=2)
    selected = distance[pair_mask]
    if distance_scale is None:
        if selected.numel() == 0:
            raise ValueError("no eligible relational pairs")
        positive = selected[selected > 0]
        if positive.numel() == 0:
            raise ValueError("teacher relational geometry has zero pairwise spread")
        distance_scale = positive.median()
    if not bool(torch.isfinite(distance_scale)) or float(distance_scale) <= 0:
        raise ValueError("relational distance scale must be finite and positive")
    return distance / distance_scale, cosine, distance_scale


def relational_geometry_loss(
    teacher_cell_state: torch.Tensor,
    student_cell_state: torch.Tensor,
    group_ids: torch.Tensor,
    *,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
    weights: RelationalLossWeights = RelationalLossWeights(),
) -> dict[str, torch.Tensor]:
    """Match rich-teacher and partial-student within-stratum geometry.

    V1 uses direct 160-D cell_state with no learned projection. The teacher
    sets the distance scale. Distance and angle terms are evaluated only on
    within-group upper-triangular pairs. Neighborhood ranks are excluded from
    the differentiable loss and reported separately.
    """
    weights.validate()
    validate_cell_states(teacher_cell_state, student_cell_state)
    if group_ids.device != teacher_cell_state.device:
        group_ids = group_ids.to(teacher_cell_state.device)
    if len(group_ids) != len(teacher_cell_state):
        raise ValueError("group_ids length differs from cell_state batch")

    pair_mask = group_pair_mask(group_ids, min_group_size=min_group_size)
    if not bool(pair_mask.any()):
        raise ValueError("no relational group meets minimum group size")

    teacher_distance, teacher_cosine, scale = _pair_geometry(
        teacher_cell_state.detach(), group_ids, pair_mask
    )
    student_distance, student_cosine, _ = _pair_geometry(
        student_cell_state, group_ids, pair_mask, distance_scale=scale
    )
    distance_loss = F.smooth_l1_loss(
        student_distance[pair_mask], teacher_distance[pair_mask], reduction="mean"
    )
    angle_loss = F.smooth_l1_loss(
        student_cosine[pair_mask], teacher_cosine[pair_mask], reduction="mean"
    )
    total = (
        weights.normalized_distance * distance_loss
        + weights.angle * angle_loss
    )
    return {
        "loss": total,
        "normalized_distance_loss": distance_loss,
        "angle_loss": angle_loss,
        "pair_count": pair_mask.sum(),
        "teacher_distance_scale": scale.detach(),
    }


def effective_rank(states: torch.Tensor) -> torch.Tensor:
    """Entropy effective rank of centered cell-state covariance."""
    if states.ndim != 2 or len(states) < 2:
        raise ValueError("effective_rank requires [cells,width] with at least 2 cells")
    centered = states - states.mean(dim=0, keepdim=True)
    singular = torch.linalg.svdvals(centered.float())
    power = singular.square()
    total = power.sum()
    if not bool(torch.isfinite(total)) or float(total) <= 0:
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
    if states.ndim != 2 or not bool(torch.isfinite(states).all()):
        raise ValueError("states must be finite [cells,width]")
    group_ids = group_ids.to(states.device)
    pair_mask = group_pair_mask(group_ids, min_group_size=min_group_size)
    if not bool(pair_mask.any()):
        raise ValueError("no eligible relational pairs")
    centered = _center_by_group(states, group_ids)
    variance = centered.float().square().mean()
    pair_distance = torch.cdist(centered.float(), centered.float(), p=2)[pair_mask]
    spread = pair_distance.median()
    rank = effective_rank(centered)
    return {
        "variance": variance,
        "pairwise_spread": spread,
        "effective_rank": rank,
        "pair_count": pair_mask.sum(),
    }


def enforce_collapse_calibration(
    teacher_health: dict[str, torch.Tensor],
    student_health: dict[str, torch.Tensor],
    calibration: CollapseCalibration,
) -> dict[str, float]:
    """Fail closed if student geometry falls below frozen teacher-relative ratios."""
    calibration.validate()
    ratios: dict[str, float] = {}
    mapping = (
        ("variance", calibration.min_variance_ratio),
        ("pairwise_spread", calibration.min_spread_ratio),
        ("effective_rank", calibration.min_effective_rank_ratio),
    )
    for key, threshold in mapping:
        t = float(teacher_health[key])
        s = float(student_health[key])
        if not (torch.isfinite(torch.tensor(t)) and torch.isfinite(torch.tensor(s))):
            raise RuntimeError(f"nonfinite collapse metric: {key}")
        if t <= 0 or s <= 0:
            raise RuntimeError(f"collapsed or invalid geometry: {key}")
        ratio = s / t
        ratios[key] = ratio
        if ratio < threshold:
            raise RuntimeError(
                f"relational collapse gate rejected {key}: ratio={ratio} threshold={threshold}"
            )
    return ratios


def neighborhood_overlap(
    teacher_cell_state: torch.Tensor,
    student_cell_state: torch.Tensor,
    group_ids: torch.Tensor,
    *,
    k: int = 3,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
) -> torch.Tensor:
    """Non-differentiable same-group kNN overlap diagnostic in [0,1]."""
    validate_cell_states(teacher_cell_state, student_cell_state)
    if k < 1:
        raise ValueError("k must be positive")
    overlaps: list[float] = []
    for group in torch.unique(group_ids, sorted=True):
        idx = torch.nonzero(group_ids.eq(group), as_tuple=False).flatten()
        if len(idx) < max(min_group_size, k + 1):
            continue
        t = teacher_cell_state[idx].detach().float()
        s = student_cell_state[idx].detach().float()
        td = torch.cdist(t, t)
        sd = torch.cdist(s, s)
        td.fill_diagonal_(float("inf"))
        sd.fill_diagonal_(float("inf"))
        tn = td.topk(k, dim=1, largest=False).indices
        sn = sd.topk(k, dim=1, largest=False).indices
        for row in range(len(idx)):
            overlap = len(set(tn[row].tolist()) & set(sn[row].tolist())) / k
            overlaps.append(overlap)
    if not overlaps:
        raise ValueError("no group large enough for neighborhood diagnostic")
    return torch.tensor(overlaps, dtype=torch.float32).mean()


def fine_matched_null_permutation(
    fine_stratum_ids: torch.Tensor,
    *,
    seed: int,
) -> torch.Tensor:
    """Deterministic within-stratum permutation for qualification only."""
    if fine_stratum_ids.ndim != 1:
        raise ValueError("fine_stratum_ids must be one-dimensional")
    ids = fine_stratum_ids.detach().cpu()
    generator = torch.Generator(device="cpu").manual_seed(int(seed))
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
    group_size: int = 16,
    groups_per_batch: int = 8,
) -> dict[str, object]:
    """Validate a prospective eight-by-sixteen donor-by-operator batch."""
    if group_size * groups_per_batch != 128:
        raise ValueError("relational batch must total exactly 128 cells")
    if len(donor_ids) != 128 or len(operator_ids) != 128:
        raise ValueError("relational batch must contain exactly 128 identities")
    counts: dict[tuple[str, str], int] = {}
    for donor, operator in zip(donor_ids, operator_ids):
        key = (str(donor), str(operator))
        counts[key] = counts.get(key, 0) + 1
    if len(counts) != groups_per_batch or any(v != group_size for v in counts.values()):
        raise RuntimeError(
            f"expected {groups_per_batch} donor-by-operator groups of {group_size}; got {counts}"
        )
    return {
        "cells": 128,
        "groups": groups_per_batch,
        "cells_per_group": group_size,
        "grouping": "canonical_donor_id x operator_id",
    }
