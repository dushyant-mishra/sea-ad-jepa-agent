"""Prospective data-first support/estimability mechanics for Teacher/Student V5.

This module is intentionally not imported by the V4 production runtime.  It
encodes only support-aware bookkeeping and deterministic planning primitives.
It does not authorize training and does not choose production token budgets,
mask fractions, block counts, triplet caps, null fallback hierarchies, or loss
weights.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from numbers import Integral, Real
from typing import Sequence

import torch

CANONICAL_VOCABULARY_SIZE = 41_238
TRIPLET_MIN_GROUP_SIZE = 3  # mathematical requirement for anchor+j+k, not a schedule choice


def _exact_int(value: object, *, name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer authority value")
    out = int(value)
    if minimum is not None and out < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return out


def _int_tensor(values: torch.Tensor, *, name: str, ndim: int = 1) -> torch.Tensor:
    if values.ndim != ndim:
        raise ValueError(f"{name} must be {ndim}-dimensional")
    if values.dtype not in (torch.int32, torch.int64):
        raise ValueError(f"{name} must use an integer dtype")
    return values.to(torch.int64)


@dataclass(frozen=True)
class EvidenceDose:
    measured_addresses: int
    hidden_addresses: int
    visible_addresses: int
    measured_fraction_of_universe: float
    hidden_fraction_of_measured: float
    visible_fraction_of_measured: float
    visible_fraction_of_universe: float


def evidence_dose(
    measured_addresses: int,
    hidden_addresses: int,
    *,
    vocabulary_size: int = CANONICAL_VOCABULARY_SIZE,
) -> EvidenceDose:
    """Describe evidence in both within-support and canonical-universe units."""
    measured = _exact_int(measured_addresses, name="measured_addresses", minimum=1)
    hidden = _exact_int(hidden_addresses, name="hidden_addresses", minimum=0)
    vocab = _exact_int(vocabulary_size, name="vocabulary_size", minimum=1)
    if measured > vocab:
        raise ValueError("measured_addresses exceeds canonical vocabulary")
    if hidden > measured:
        raise ValueError("hidden_addresses exceeds measured support")
    visible = measured - hidden
    return EvidenceDose(
        measured_addresses=measured,
        hidden_addresses=hidden,
        visible_addresses=visible,
        measured_fraction_of_universe=measured / vocab,
        hidden_fraction_of_measured=hidden / measured,
        visible_fraction_of_measured=visible / measured,
        visible_fraction_of_universe=visible / vocab,
    )


def evidence_dose_from_fraction(
    measured_addresses: int,
    hidden_fraction: float,
    *,
    vocabulary_size: int = CANONICAL_VOCABULARY_SIZE,
) -> EvidenceDose:
    """Apply an externally supplied within-support hidden fraction.

    The fraction is not given a production default.  This helper exists so an
    authority can state a within-support fraction without losing the actual
    canonical-universe evidence dose.
    """
    measured = _exact_int(measured_addresses, name="measured_addresses", minimum=1)
    if isinstance(hidden_fraction, bool) or not isinstance(hidden_fraction, Real):
        raise ValueError("hidden_fraction must be an explicit numeric authority value")
    fraction = float(hidden_fraction)
    if not torch.isfinite(torch.tensor(fraction)) or not 0.0 <= fraction <= 1.0:
        raise ValueError("hidden_fraction must be finite and in [0,1]")
    hidden = int(fraction * measured)
    return evidence_dose(measured, hidden, vocabulary_size=vocabulary_size)


@dataclass(frozen=True)
class StratifiedEvidenceCounts:
    core_measured: torch.Tensor
    core_hidden: torch.Tensor
    core_visible: torch.Tensor
    extension_measured: torch.Tensor
    extension_hidden: torch.Tensor
    extension_visible: torch.Tensor


def support_stratified_evidence_counts(
    measurement_mask: torch.Tensor,
    hidden_mask: torch.Tensor,
    universal_core_mask: torch.Tensor,
) -> StratifiedEvidenceCounts:
    """Report universal-core and operator-extension evidence separately."""
    if measurement_mask.ndim != 2 or measurement_mask.dtype is not torch.bool:
        raise ValueError("measurement_mask must be boolean [cells,genes]")
    if hidden_mask.shape != measurement_mask.shape or hidden_mask.dtype is not torch.bool:
        raise ValueError("hidden_mask must be boolean and align with measurement_mask")
    if universal_core_mask.ndim != 1 or len(universal_core_mask) != measurement_mask.shape[1] or universal_core_mask.dtype is not torch.bool:
        raise ValueError("universal_core_mask must be boolean [genes]")
    core = universal_core_mask.to(measurement_mask.device)[None, :].expand_as(measurement_mask)
    if bool((core & ~measurement_mask).any()):
        raise ValueError("universal core is not measured for every supplied cell")
    if bool((hidden_mask & ~measurement_mask).any()):
        raise ValueError("hidden target outside measured support")
    extension = measurement_mask & ~core
    return StratifiedEvidenceCounts(
        core_measured=core.sum(dim=1),
        core_hidden=(core & hidden_mask).sum(dim=1),
        core_visible=(core & ~hidden_mask).sum(dim=1),
        extension_measured=extension.sum(dim=1),
        extension_hidden=(extension & hidden_mask).sum(dim=1),
        extension_visible=(extension & ~hidden_mask).sum(dim=1),
    )


@dataclass(frozen=True)
class RaggedGroupPlan:
    group_ids: torch.Tensor
    group_keys: tuple[tuple[str, str], ...]
    unique_group_ids: torch.Tensor
    group_counts: torch.Tensor
    relationally_estimable_group_mask: torch.Tensor
    relationally_estimable_cell_mask: torch.Tensor
    total_groups: int
    estimable_groups: int
    total_cells: int
    estimable_cells: int


def ragged_donor_operator_groups(
    donor_ids: Sequence[str],
    operator_ids: Sequence[str],
) -> RaggedGroupPlan:
    """Build deterministic ragged donor×operator groups without equal-size demands."""
    if len(donor_ids) != len(operator_ids):
        raise ValueError("donor_ids and operator_ids lengths differ")
    if not donor_ids:
        raise ValueError("empty batch")
    if any(not isinstance(x, str) or not x for x in donor_ids):
        raise ValueError("donor_ids must be nonempty canonical strings")
    if any(not isinstance(x, str) or not x for x in operator_ids):
        raise ValueError("operator_ids must be nonempty canonical strings")

    keys = [(donor_ids[i], operator_ids[i]) for i in range(len(donor_ids))]
    ordered_unique = sorted(set(keys))
    mapping = {key: idx for idx, key in enumerate(ordered_unique)}
    group_ids = torch.tensor([mapping[key] for key in keys], dtype=torch.int64)
    counts = torch.bincount(group_ids, minlength=len(ordered_unique)).to(torch.int64)
    group_estimable = counts >= TRIPLET_MIN_GROUP_SIZE
    cell_estimable = group_estimable[group_ids]
    return RaggedGroupPlan(
        group_ids=group_ids,
        group_keys=tuple(ordered_unique),
        unique_group_ids=torch.arange(len(ordered_unique), dtype=torch.int64),
        group_counts=counts,
        relationally_estimable_group_mask=group_estimable,
        relationally_estimable_cell_mask=cell_estimable,
        total_groups=len(ordered_unique),
        estimable_groups=int(group_estimable.sum()),
        total_cells=len(keys),
        estimable_cells=int(cell_estimable.sum()),
    )


@dataclass(frozen=True)
class NullEstimability:
    stratum_counts: torch.Tensor
    estimable_stratum_mask: torch.Tensor
    estimable_cell_mask: torch.Tensor
    nonestimable_cell_mask: torch.Tensor
    estimable_strata: int
    nonestimable_strata: int


def fine_null_estimability(stratum_ids: torch.Tensor) -> NullEstimability:
    """Report fine-null support instead of failing the whole batch on singletons."""
    ids = _int_tensor(stratum_ids, name="stratum_ids")
    if len(ids) == 0:
        raise ValueError("stratum_ids is empty")
    _, inverse, counts = torch.unique(ids, sorted=True, return_inverse=True, return_counts=True)
    estimable_strata = counts >= 2
    cell_estimable = estimable_strata[inverse]
    return NullEstimability(
        stratum_counts=counts,
        estimable_stratum_mask=estimable_strata,
        estimable_cell_mask=cell_estimable,
        nonestimable_cell_mask=~cell_estimable,
        estimable_strata=int(estimable_strata.sum()),
        nonestimable_strata=int((~estimable_strata).sum()),
    )


def fine_matched_null_permutation_partial(
    stratum_ids: torch.Tensor,
    *,
    seed: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Derange only fine strata with structural support; mark others -1."""
    ids = _int_tensor(stratum_ids, name="stratum_ids")
    seed = _exact_int(seed, name="seed", minimum=0)
    report = fine_null_estimability(ids)
    out = torch.full((len(ids),), -1, dtype=torch.int64, device=ids.device)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    cpu_ids = ids.detach().cpu()
    for stratum in torch.unique(cpu_ids, sorted=True):
        idx = torch.nonzero(cpu_ids.eq(stratum), as_tuple=False).flatten()
        if len(idx) < 2:
            continue
        offset = int(torch.randint(1, len(idx), (1,), generator=generator).item())
        perm = idx.roll(offset)
        out[idx.to(out.device)] = perm.to(out.device)
    if bool((out[report.estimable_cell_mask] < 0).any()):
        raise RuntimeError("estimable fine-null cell was not assigned")
    return out, report.estimable_cell_mask


@dataclass(frozen=True)
class TokenBudgetPlan:
    microbatch_ranges: tuple[tuple[int, int], ...]
    microbatch_token_costs: tuple[int, ...]
    cells: int
    maximum_token_budget: int
    maximum_observed_cost: int


def plan_contiguous_token_budget_microbatches(
    per_cell_token_cost: torch.Tensor,
    *,
    maximum_token_budget: int,
) -> TokenBudgetPlan:
    """Pack an already scientifically ordered batch by compute cost only."""
    costs = _int_tensor(per_cell_token_cost, name="per_cell_token_cost")
    budget = _exact_int(maximum_token_budget, name="maximum_token_budget", minimum=1)
    if len(costs) == 0 or bool((costs <= 0).any()):
        raise ValueError("every cell token cost must be positive")
    if int(costs.max()) > budget:
        raise ValueError("one cell exceeds maximum token budget")

    ranges: list[tuple[int, int]] = []
    totals: list[int] = []
    begin = 0
    running = 0
    for i, raw in enumerate(costs.tolist()):
        cost = int(raw)
        if running and running + cost > budget:
            ranges.append((begin, i))
            totals.append(running)
            begin = i
            running = 0
        running += cost
    ranges.append((begin, len(costs)))
    totals.append(running)
    return TokenBudgetPlan(
        microbatch_ranges=tuple(ranges),
        microbatch_token_costs=tuple(totals),
        cells=len(costs),
        maximum_token_budget=budget,
        maximum_observed_cost=max(totals),
    )


def combined_teacher_student_token_cost(
    measured_counts: torch.Tensor,
    visible_counts_by_view: torch.Tensor,
) -> torch.Tensor:
    """Compute token work per cell without assuming a fixed view count."""
    measured = _int_tensor(measured_counts, name="measured_counts")
    visible = _int_tensor(visible_counts_by_view, name="visible_counts_by_view", ndim=2)
    if len(measured) != len(visible):
        raise ValueError("measured_counts and visible_counts_by_view lengths differ")
    if bool((measured <= 0).any()) or bool((visible <= 0).any()):
        raise ValueError("token counts must be positive")
    if bool((visible > measured[:, None]).any()):
        raise ValueError("visible support exceeds measured support")
    calls = 1 + visible.shape[1]
    return measured + visible.sum(dim=1) + calls


@dataclass(frozen=True)
class RaggedTripletSample:
    triplets: torch.Tensor
    triplet_group_ids: torch.Tensor
    group_capacities: torch.Tensor
    draws_per_group: torch.Tensor


def _anchored_triplet_capacity(n: int) -> int:
    return n * (n - 1) * (n - 2) // 2 if n >= TRIPLET_MIN_GROUP_SIZE else 0


def _uniform_below(material: bytes, counter: int, upper_exclusive: int) -> int:
    if upper_exclusive <= 0:
        raise ValueError("upper_exclusive must be positive")
    limit = (1 << 256) - ((1 << 256) % upper_exclusive)
    nonce = 0
    while True:
        digest = hashlib.sha256(
            material + counter.to_bytes(8, "big") + nonce.to_bytes(4, "big")
        ).digest()
        value = int.from_bytes(digest, "big")
        if value < limit:
            return value % upper_exclusive
        nonce += 1


def _sample_unique_offsets(capacity: int, draws: int, material: bytes) -> list[int]:
    """Floyd sampling without replacement in O(draws) memory/time."""
    if draws < 0 or draws > capacity:
        raise ValueError("triplet draws exceed group anchored-triplet capacity")
    selected: set[int] = set()
    counter = 0
    for j in range(capacity - draws, capacity):
        t = _uniform_below(material, counter, j + 1)
        counter += 1
        selected.add(j if t in selected else t)
    if len(selected) != draws:
        raise RuntimeError("unique-offset sampler cardinality failure")
    return sorted(selected)


def _pair_prefix(m: int, a: int) -> int:
    return a * (2 * m - a - 1) // 2


def _unrank_pair(m: int, rank: int) -> tuple[int, int]:
    """Unrank combinations(range(m),2) in lexicographic order."""
    capacity = m * (m - 1) // 2
    if rank < 0 or rank >= capacity:
        raise ValueError("pair rank out of range")
    lo, hi = 0, m - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if _pair_prefix(m, mid) <= rank:
            lo = mid
        else:
            hi = mid
    a = lo
    while a + 1 < m and _pair_prefix(m, a + 1) <= rank:
        a += 1
    offset = rank - _pair_prefix(m, a)
    b = a + 1 + offset
    if not (0 <= a < b < m):
        raise RuntimeError("pair unranking failure")
    return a, b


def _unrank_anchored_triplet(sorted_cells: list[int], rank: int) -> tuple[int, int, int]:
    n = len(sorted_cells)
    per_anchor = (n - 1) * (n - 2) // 2
    capacity = n * per_anchor
    if rank < 0 or rank >= capacity:
        raise ValueError("anchored triplet rank out of range")
    anchor_pos, pair_rank = divmod(rank, per_anchor)
    anchor = sorted_cells[anchor_pos]
    remaining = sorted_cells[:anchor_pos] + sorted_cells[anchor_pos + 1 :]
    a, b = _unrank_pair(n - 1, pair_rank)
    j, k = remaining[a], remaining[b]
    if j > k:
        j, k = k, j
    return anchor, j, k


def sample_ragged_anchored_triplets(
    plan: RaggedGroupPlan,
    draws_per_group: torch.Tensor,
    *,
    seed: int,
) -> RaggedTripletSample:
    """Sample exact unique anchored triplets from arbitrary ragged groups."""
    draws = _int_tensor(draws_per_group, name="draws_per_group")
    seed = _exact_int(seed, name="seed", minimum=0)
    if len(draws) != plan.total_groups:
        raise ValueError("draws_per_group must contain one value per ragged group")
    if bool((draws < 0).any()):
        raise ValueError("draws_per_group must be nonnegative")

    capacities = torch.tensor(
        [_anchored_triplet_capacity(int(n)) for n in plan.group_counts.tolist()],
        dtype=torch.int64,
    )
    if bool((draws[~plan.relationally_estimable_group_mask] != 0).any()):
        raise ValueError("non-estimable relational group must request zero triplet draws")
    if bool((draws > capacities).any()):
        raise ValueError("triplet draws exceed group anchored-triplet capacity")

    rows: list[tuple[int, int, int]] = []
    row_groups: list[int] = []
    for gid, ((donor, operator), requested, capacity) in enumerate(
        zip(plan.group_keys, draws.tolist(), capacities.tolist())
    ):
        if requested == 0:
            continue
        cells = torch.nonzero(plan.group_ids.eq(gid), as_tuple=False).flatten().tolist()
        cells.sort()
        material = f"V5_RAGGED_TRIPLET|{seed}|{donor}|{operator}".encode("utf-8")
        for offset in _sample_unique_offsets(capacity, int(requested), material):
            rows.append(_unrank_anchored_triplet(cells, offset))
            row_groups.append(gid)
    triplets = torch.tensor(rows, dtype=torch.int64) if rows else torch.empty((0, 3), dtype=torch.int64)
    groups = torch.tensor(row_groups, dtype=torch.int64) if row_groups else torch.empty((0,), dtype=torch.int64)
    return RaggedTripletSample(
        triplets=triplets,
        triplet_group_ids=groups,
        group_capacities=capacities,
        draws_per_group=draws.clone(),
    )


def contribution_weighted_mean(
    loss_numerators: torch.Tensor,
    contribution_counts: torch.Tensor,
) -> torch.Tensor:
    """Aggregate across compute chunks without weighting by chunk count."""
    if loss_numerators.ndim != 1 or not loss_numerators.is_floating_point():
        raise ValueError("loss_numerators must be floating [chunks]")
    counts = _int_tensor(contribution_counts, name="contribution_counts")
    if len(loss_numerators) != len(counts):
        raise ValueError("loss_numerators and contribution_counts lengths differ")
    if not bool(torch.isfinite(loss_numerators).all()):
        raise ValueError("loss_numerators contain nonfinite values")
    if bool((counts < 0).any()):
        raise ValueError("contribution_counts must be nonnegative")
    total = counts.sum()
    if int(total) <= 0:
        raise ValueError("no estimable contributions")
    return loss_numerators.sum() / total.to(loss_numerators.dtype)
