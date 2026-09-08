"""Prospective relational teacher/student mechanics V2.

V2 is not called by production_update. It supersedes the prospective V1
adjunct after adversarial review found two fail-open boundaries in V1:
configurable 8x16 batch geometry and pooled collapse health across relational
groups. V2 freezes exact batch geometry and enforces collapse health per group.
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
RELATIONAL_GROUP_SIZE = 16
RELATIONAL_GROUPS_PER_BATCH = 8
RELATIONAL_BATCH_SIZE = RELATIONAL_GROUP_SIZE * RELATIONAL_GROUPS_PER_BATCH
_INTEGER_DTYPES = {
    torch.int8,
    torch.int16,
    torch.int32,
    torch.int64,
    torch.uint8,
}


@dataclass(frozen=True)
class RelationalLossWeights:
    normalized_distance: float = 0.5
    angle: float = 0.5

    def validate(self) -> None:
        values = (float(self.normalized_distance), float(self.angle))
        if not all(torch.isfinite(torch.tensor(v)) for v in values):
            raise ValueError("relational loss weights must be finite")
        if values != (0.5, 0.5):
            raise ValueError("relational loss weights are frozen exactly at 0.5/0.5")


@dataclass(frozen=True)
class CollapseCalibration:
    """Externally frozen per-group lower ratios relative to teacher geometry."""

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
            if not torch.isfinite(torch.tensor(value)) or not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be finite and lie in (0,1]")


def hidden_fraction_for_evidence(evidence_percent: int) -> float:
    if type(evidence_percent) is not int:
        raise TypeError("evidence level must be an exact integer percent")
    if evidence_percent not in EVIDENCE_LEVELS:
        raise ValueError(f"unsupported evidence level: {evidence_percent}")
    return (100.0 - evidence_percent) / 100.0


def _validate_group_ids(group_ids: torch.Tensor, *, expected_cells: int | None = None) -> None:
    if group_ids.ndim != 1:
        raise ValueError("group_ids must be one-dimensional")
    if group_ids.dtype not in _INTEGER_DTYPES:
        raise ValueError("group_ids must use an integer tensor dtype")
    if expected_cells is not None and len(group_ids) != expected_cells:
        raise ValueError("group_ids length differs from cell_state batch")


def _validate_single_cell_states(states: torch.Tensor) -> None:
    if states.ndim != 2:
        raise ValueError("cell_state must be [cells,width]")
    if states.shape[1] != RELATIONAL_DIMENSION:
        raise ValueError(f"expected {RELATIONAL_DIMENSION}-D cell_state")
    if not states.is_floating_point():
        raise ValueError("cell_state must be floating point")
    if not bool(torch.isfinite(states).all()):
        raise ValueError("cell_state contains nonfinite values")


def validate_cell_states(teacher: torch.Tensor, student: torch.Tensor) -> None:
    _validate_single_cell_states(teacher)
    _validate_single_cell_states(student)
    if teacher.shape != student.shape:
        raise ValueError("teacher/student cell_state shapes differ")


def group_pair_mask(
    group_ids: torch.Tensor, *, min_group_size: int = DEFAULT_MIN_GROUP_SIZE
) -> torch.Tensor:
    """Return upper-triangular pairs only for groups meeting the frozen minimum."""
    _validate_group_ids(group_ids)
    if type(min_group_size) is not int or min_group_size < 3:
        raise ValueError("min_group_size must be an integer at least 3")
    same = group_ids[:, None].eq(group_ids[None, :])
    counts = same.sum(dim=1)
    eligible = counts.ge(min_group_size)
    return torch.triu(same & eligible[:, None] & eligible[None, :], diagonal=1)


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
    require_each_group_teacher_spread: bool = False,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    centered = _center_by_group(states, group_ids)
    norms = centered.norm(dim=1)
    eligible_cells = pair_mask.any(dim=0) | pair_mask.any(dim=1)
    eps = torch.finfo(centered.dtype).eps
    if bool((norms[eligible_cells] <= eps).any()):
        raise ValueError("centered relational cell_state has zero norm; angle is undefined")
    unit = centered / norms[:, None]
    cosine = unit @ unit.T
    distance = torch.cdist(centered, centered, p=2)
    selected = distance[pair_mask]
    if selected.numel() == 0:
        raise ValueError("no eligible relational pairs")

    if require_each_group_teacher_spread:
        for group in torch.unique(group_ids, sorted=True):
            take = group_ids.eq(group)
            local_mask = pair_mask & take[:, None] & take[None, :]
            if not bool(local_mask.any()):
                continue
            local = distance[local_mask]
            if not bool((local > 0).any()):
                raise ValueError("teacher relational group has zero pairwise spread")

    if distance_scale is None:
        positive = selected[selected > 0]
        if positive.numel() == 0:
            raise ValueError("teacher relational geometry has zero pairwise spread")
        distance_scale = positive.median()
    if not bool(torch.isfinite(distance_scale)) or float(distance_scale.detach()) <= 0:
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
    """Match direct 160-D teacher/student geometry within relational groups only."""
    weights.validate()
    validate_cell_states(teacher_cell_state, student_cell_state)
    _validate_group_ids(group_ids, expected_cells=len(teacher_cell_state))
    group_ids = group_ids.to(teacher_cell_state.device)
    pair_mask = group_pair_mask(group_ids, min_group_size=min_group_size)
    if not bool(pair_mask.any()):
        raise ValueError("no relational group meets minimum group size")

    teacher_distance, teacher_cosine, scale = _pair_geometry(
        teacher_cell_state.detach(),
        group_ids,
        pair_mask,
        require_each_group_teacher_spread=True,
    )
    student_distance, student_cosine, _ = _pair_geometry(
        student_cell_state, group_ids, pair_mask, distance_scale=scale
    )
    distance_loss = F.smooth_l1_loss(
        student_distance[pair_mask],
        teacher_distance[pair_mask],
        reduction="mean",
        beta=1.0,
    )
    angle_loss = F.smooth_l1_loss(
        student_cosine[pair_mask],
        teacher_cosine[pair_mask],
        reduction="mean",
        beta=1.0,
    )
    total = weights.normalized_distance * distance_loss + weights.angle * angle_loss
    return {
        "loss": total,
        "normalized_distance_loss": distance_loss,
        "angle_loss": angle_loss,
        "pair_count": pair_mask.sum(),
        "teacher_distance_scale": scale.detach(),
    }


def effective_rank(states: torch.Tensor) -> torch.Tensor:
    """Entropy effective rank of centered cell-state singular-value power."""
    if states.ndim != 2 or len(states) < 2:
        raise ValueError("effective_rank requires [cells,width] with at least 2 cells")
    if not states.is_floating_point() or not bool(torch.isfinite(states).all()):
        raise ValueError("effective_rank states must be finite floating point")
    centered = states - states.mean(dim=0, keepdim=True)
    singular = torch.linalg.svdvals(centered.float())
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
) -> dict[int, dict[str, torch.Tensor]]:
    """Return collapse metrics separately for every eligible relational group."""
    _validate_single_cell_states(states)
    _validate_group_ids(group_ids, expected_cells=len(states))
    group_ids = group_ids.to(states.device)
    if type(min_group_size) is not int or min_group_size < 3:
        raise ValueError("min_group_size must be an integer at least 3")
    out: dict[int, dict[str, torch.Tensor]] = {}
    for group in torch.unique(group_ids, sorted=True):
        idx = torch.nonzero(group_ids.eq(group), as_tuple=False).flatten()
        if len(idx) < min_group_size:
            continue
        local = states[idx]
        centered = local - local.mean(dim=0, keepdim=True)
        variance = centered.float().square().mean()
        distances = torch.cdist(centered.float(), centered.float(), p=2)
        upper = torch.triu(
            torch.ones(len(idx), len(idx), dtype=torch.bool, device=states.device),
            diagonal=1,
        )
        spread = distances[upper].median()
        rank = effective_rank(centered)
        out[int(group.item())] = {
            "variance": variance,
            "pairwise_spread": spread,
            "effective_rank": rank,
            "pair_count": upper.sum(),
        }
    if not out:
        raise ValueError("no relational group meets minimum group size")
    return out


def enforce_collapse_calibration(
    teacher_health: dict[int, dict[str, torch.Tensor]],
    student_health: dict[int, dict[str, torch.Tensor]],
    calibration: CollapseCalibration,
) -> dict[int, dict[str, float]]:
    """Fail closed per group; rich groups cannot rescue a collapsed group."""
    calibration.validate()
    if set(teacher_health) != set(student_health):
        raise RuntimeError("teacher/student collapse-health group sets differ")
    ratios: dict[int, dict[str, float]] = {}
    mapping = (
        ("variance", float(calibration.min_variance_ratio)),
        ("pairwise_spread", float(calibration.min_spread_ratio)),
        ("effective_rank", float(calibration.min_effective_rank_ratio)),
    )
    for group in sorted(teacher_health):
        ratios[group] = {}
        for key, threshold in mapping:
            if key not in teacher_health[group] or key not in student_health[group]:
                raise RuntimeError(f"missing collapse metric: group={group} metric={key}")
            t = float(teacher_health[group][key].detach())
            s = float(student_health[group][key].detach())
            if not (torch.isfinite(torch.tensor(t)) and torch.isfinite(torch.tensor(s))):
                raise RuntimeError(f"nonfinite collapse metric: group={group} metric={key}")
            if t <= 0 or s <= 0:
                raise RuntimeError(f"collapsed or invalid geometry: group={group} metric={key}")
            ratio = s / t
            ratios[group][key] = ratio
            if ratio < threshold:
                raise RuntimeError(
                    f"relational collapse gate rejected group={group} {key}: ratio={ratio} threshold={threshold}"
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
    _validate_group_ids(group_ids, expected_cells=len(teacher_cell_state))
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    group_ids = group_ids.to(teacher_cell_state.device)
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
            overlaps.append(len(set(tn[row].tolist()) & set(sn[row].tolist())) / k)
    if not overlaps:
        raise ValueError("no group large enough for neighborhood diagnostic")
    return torch.tensor(overlaps, dtype=torch.float32).mean()


def fine_matched_null_permutation(
    fine_stratum_ids: torch.Tensor,
    *,
    seed: int,
) -> torch.Tensor:
    """Deterministic within-stratum no-fixed-point permutation for qualification only."""
    _validate_group_ids(fine_stratum_ids)
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
) -> dict[str, object]:
    """Require exactly eight donor×operator groups of exactly sixteen cells."""
    if len(donor_ids) != RELATIONAL_BATCH_SIZE or len(operator_ids) != RELATIONAL_BATCH_SIZE:
        raise ValueError("relational batch must contain exactly 128 identities")
    counts: dict[tuple[str, str], int] = {}
    for donor, operator in zip(donor_ids, operator_ids):
        if not isinstance(donor, str) or not donor.strip():
            raise ValueError("canonical donor identity must be a non-empty string")
        if not isinstance(operator, str) or not operator.strip():
            raise ValueError("operator identity must be a non-empty string")
        key = (donor, operator)
        counts[key] = counts.get(key, 0) + 1
    if len(counts) != RELATIONAL_GROUPS_PER_BATCH or any(
        count != RELATIONAL_GROUP_SIZE for count in counts.values()
    ):
        raise RuntimeError(
            f"expected {RELATIONAL_GROUPS_PER_BATCH} donor-by-operator groups of "
            f"{RELATIONAL_GROUP_SIZE}; got {counts}"
        )
    return {
        "cells": RELATIONAL_BATCH_SIZE,
        "groups": RELATIONAL_GROUPS_PER_BATCH,
        "cells_per_group": RELATIONAL_GROUP_SIZE,
        "grouping": "canonical_donor_id x operator_id",
    }
