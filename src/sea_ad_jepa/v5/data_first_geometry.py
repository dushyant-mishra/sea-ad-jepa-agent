"""Data-first execution primitives for a prospective Teacher/Student V5.

The dataset determines support.  These helpers do not invent a production
batch size, token budget, mask fraction, relational group size, or loss weight.
They turn externally frozen cell selections/support into deterministic execution
geometry while preserving canonical gene identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import Mapping, Sequence

import torch


def _exact_int(value: object, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out=int(value)
    if out < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return out


def evidence_telemetry(*, measured_count: int, hidden_count: int, vocabulary_size: int) -> dict[str, float | int]:
    """Describe evidence in both support-relative and universe-relative terms."""
    measured=_exact_int(measured_count,'measured_count',1)
    hidden=_exact_int(hidden_count,'hidden_count',0)
    vocab=_exact_int(vocabulary_size,'vocabulary_size',1)
    if measured > vocab:
        raise ValueError('measured_count exceeds vocabulary_size')
    if hidden > measured:
        raise ValueError('hidden_count exceeds measured_count')
    visible=measured-hidden
    if visible < 1:
        raise ValueError('at least one visible measured address is required')
    return {
        'measured_count':measured,
        'hidden_count':hidden,
        'visible_count':visible,
        'measured_fraction_of_universe':measured/vocab,
        'hidden_fraction_within_measured':hidden/measured,
        'visible_fraction_within_measured':visible/measured,
        'visible_fraction_of_universe':visible/vocab,
    }


def ragged_relational_support(
    donor_ids: Sequence[str],
    operator_ids: Sequence[str],
    *,
    minimum_triplet_group_size: int = 3,
) -> dict[str, object]:
    """Summarize ragged donor×operator support without demanding equal groups.

    Groups below three cells are mathematically non-estimable for anchored
    triplets, but they do not invalidate the whole batch and can still
    participate in the base JEPA objective.
    """
    minimum=_exact_int(minimum_triplet_group_size,'minimum_triplet_group_size',3)
    if len(donor_ids) != len(operator_ids) or not donor_ids:
        raise ValueError('donor/operator IDs must be nonempty aligned sequences')
    counts: dict[tuple[str,str],int]={}
    for donor,operator in zip(donor_ids,operator_ids):
        if not isinstance(donor,str) or not donor or not isinstance(operator,str) or not operator:
            raise ValueError('donor/operator IDs must be nonempty canonical strings')
        key=(donor,operator)
        counts[key]=counts.get(key,0)+1
    estimable={k:v for k,v in counts.items() if v>=minimum}
    estimable_cells=sum(estimable.values())
    return {
        'cells_total':len(donor_ids),
        'groups_total':len(counts),
        'groups_estimable':len(estimable),
        'groups_not_estimable':len(counts)-len(estimable),
        'cells_in_estimable_groups':estimable_cells,
        'cells_not_in_estimable_groups':len(donor_ids)-estimable_cells,
        'minimum_triplet_group_size':minimum,
        'group_counts':tuple(sorted((d,o,n) for (d,o),n in counts.items())),
    }


def anchored_triplet_capacity(group_size: int) -> int:
    """Number of ordered-anchor / unordered-comparator triplets without enumeration."""
    n=_exact_int(group_size,'group_size',0)
    if n < 3:
        return 0
    return n * ((n-1)*(n-2)//2)


def partial_fine_derangement(stratum_ids: torch.Tensor, *, seed: int) -> dict[str, torch.Tensor]:
    """Derange every estimable stratum; mark singleton strata NOT_ESTIMABLE.

    The returned permutation contains -1 for cells in non-estimable strata.
    No cross-stratum fallback is invented. A later authority may define an
    outcome-blind fallback hierarchy separately.
    """
    if stratum_ids.ndim != 1 or stratum_ids.dtype not in (torch.int32,torch.int64):
        raise ValueError('stratum_ids must be one-dimensional integer IDs')
    seed=_exact_int(seed,'seed',0)
    ids=stratum_ids.detach().cpu()
    gen=torch.Generator(device='cpu').manual_seed(seed)
    perm=torch.full((len(ids),),-1,dtype=torch.int64)
    estimable=torch.zeros((len(ids),),dtype=torch.bool)
    for group in torch.unique(ids,sorted=True):
        idx=torch.nonzero(ids.eq(group),as_tuple=False).flatten()
        if len(idx) < 2:
            continue
        order=idx[torch.randperm(len(idx),generator=gen)]
        perm[order]=order.roll(-1)
        estimable[idx]=True
    if bool((perm[estimable] == torch.arange(len(ids))[estimable]).any()):
        raise RuntimeError('estimable stratum was not deranged')
    if bool((ids[perm[estimable]] != ids[estimable]).any()):
        raise RuntimeError('derangement crossed a stratum')
    return {'permutation':perm.to(stratum_ids.device),'estimable_mask':estimable.to(stratum_ids.device)}


@dataclass(frozen=True)
class PackedValidTokens:
    canonical_gene_ids: torch.Tensor
    expression: torch.Tensor
    canonical_index_by_packed_position: torch.Tensor


def pack_valid_tokens(expression: torch.Tensor, valid_mask: torch.Tensor) -> PackedValidTokens:
    """Remove invalid query tokens while retaining exact canonical gene IDs.

    Each row may contain a different set of valid genes, but this tensorized
    representation requires the same *count* per row. Operator-homogeneous
    teacher batches and exact-fraction student views satisfy that condition.
    """
    if expression.ndim != 2 or valid_mask.shape != expression.shape:
        raise ValueError('expression/valid_mask must share [cells,genes] shape')
    if valid_mask.dtype is not torch.bool:
        raise ValueError('valid_mask must be boolean')
    if not expression.is_floating_point() or not bool(torch.isfinite(expression).all()):
        raise ValueError('expression must be finite floating point')
    counts=valid_mask.sum(dim=1)
    if bool((counts < 1).any()):
        raise ValueError('every cell must retain at least one valid gene')
    if not bool((counts == counts[0]).all()):
        raise ValueError('packed tensor requires equal valid-token count per row')
    ids=torch.arange(expression.shape[1],device=expression.device,dtype=torch.int64).expand(len(expression),-1)
    n=int(counts[0])
    packed_ids=torch.empty((len(expression),n),dtype=torch.int64,device=expression.device)
    packed_values=torch.empty((len(expression),n),dtype=expression.dtype,device=expression.device)
    for row in range(len(expression)):
        idx=torch.nonzero(valid_mask[row],as_tuple=False).flatten()
        packed_ids[row]=ids[row,idx]
        packed_values[row]=expression[row,idx]
    return PackedValidTokens(packed_ids,packed_values,packed_ids)


def operator_homogeneous_microbatch_plan(
    operator_ids: Sequence[int],
    measured_tokens_by_operator: Mapping[int,int],
    *,
    max_teacher_tokens_per_microbatch: int,
) -> tuple[tuple[int,...],...]:
    """Deterministically pack a frozen update cell set by actual support cost.

    Cell selection is untouched. Relative slot order is preserved within each
    operator. Operators are ordered by first appearance in the frozen update.
    The token budget has no default and must be separately authorized.
    """
    budget=_exact_int(max_teacher_tokens_per_microbatch,'max_teacher_tokens_per_microbatch',1)
    if not operator_ids:
        raise ValueError('operator_ids cannot be empty')
    groups: dict[int,list[int]]={}
    first: dict[int,int]={}
    for slot,raw in enumerate(operator_ids):
        op=_exact_int(raw,'operator_id',0)
        if op not in measured_tokens_by_operator:
            raise ValueError(f'missing measured-token support for operator {op}')
        tokens=_exact_int(measured_tokens_by_operator[op],f'measured_tokens_by_operator[{op}]',1)
        if tokens > budget:
            raise ValueError(f'operator {op} single-cell support exceeds token budget')
        groups.setdefault(op,[]).append(slot)
        first.setdefault(op,slot)
    plan=[]
    for op in sorted(groups,key=lambda x:first[x]):
        per_cell=int(measured_tokens_by_operator[op])
        capacity=max(1,budget//per_cell)
        slots=groups[op]
        for start in range(0,len(slots),capacity):
            plan.append(tuple(slots[start:start+capacity]))
    flat=[x for batch in plan for x in batch]
    if sorted(flat) != list(range(len(operator_ids))) or len(flat) != len(set(flat)):
        raise RuntimeError('packing plan lost or duplicated a frozen update slot')
    return tuple(plan)


def mean_loss_weight(*, local_elements: int, total_elements: int) -> float:
    """Exact accumulation weight for a local mean contributing to a global mean."""
    local=_exact_int(local_elements,'local_elements',1)
    total=_exact_int(total_elements,'total_elements',1)
    if local > total:
        raise ValueError('local_elements exceeds total_elements')
    return local/total


def weighted_block_jepa_loss(
    predicted: torch.Tensor,
    target: torch.Tensor,
    cell_weights: torch.Tensor,
) -> torch.Tensor:
    """Per-cell weighted block-JEPA MSE; compute packing cannot choose weights."""
    if predicted.shape != target.shape or predicted.ndim != 3:
        raise ValueError('predicted/target must share [cells,blocks,width] shape')
    if cell_weights.ndim != 1 or len(cell_weights) != len(predicted):
        raise ValueError('cell_weights must be one-dimensional and match cells')
    if not cell_weights.is_floating_point() or not bool(torch.isfinite(cell_weights).all()):
        raise ValueError('cell_weights must be finite floating point')
    if bool((cell_weights < 0).any()) or not bool((cell_weights > 0).any()):
        raise ValueError('cell_weights must be nonnegative with positive total mass')
    per_cell=(predicted.float()-target.detach().float()).square().mean(dim=(1,2))
    weights=cell_weights.float().to(per_cell.device)
    return (per_cell*weights).sum()/weights.sum()


def weighted_loss_partition_weight(*, local_weight_mass: float, total_weight_mass: float) -> float:
    """Weight a local weighted-mean loss into the exact update-level weighted mean."""
    local=float(local_weight_mass); total=float(total_weight_mass)
    if not (local > 0.0 and total > 0.0 and local <= total):
        raise ValueError('weight masses must satisfy 0 < local <= total')
    if not (torch.isfinite(torch.tensor(local)) and torch.isfinite(torch.tensor(total))):
        raise ValueError('weight masses must be finite')
    return local/total

_HASH_PRIME = 2_147_483_647
_HASH_MULTIPLIERS = (48271, 69621, 40699, 65537, 99991, 104729)


def _hash_fold_mod_prime(seed: torch.Tensor, value: torch.Tensor, multiplier: int) -> torch.Tensor:
    """Deterministic modular hash step with products bounded inside signed int64."""
    prime = _HASH_PRIME
    return (torch.remainder(seed, prime) * int(multiplier) + torch.remainder(value, prime)) % prime


def keyed_feature_dropout(
    values: torch.Tensor,
    *,
    cell_keys: torch.Tensor,
    token_keys: torch.Tensor,
    probability: float,
    update_index: int,
    view_index: int,
    layer_index: int,
    site_index: int,
    training: bool = True,
) -> torch.Tensor:
    """Packing/order-invariant prospective dropout keyed by scientific identity.

    Randomness is a pure function of stable update/view/layer/site, cell key,
    canonical token key, and feature coordinate.  No tensor position enters the
    key, so physically removing invalid tokens cannot change masks for retained
    canonical tokens.  This is a V5 proof primitive only; V4 runtime is unchanged.
    """
    if values.ndim != 3 or not values.is_floating_point():
        raise ValueError('values must be floating [cells,tokens,features]')
    if not bool(torch.isfinite(values).all()):
        raise ValueError('values must be finite')
    if cell_keys.ndim != 1 or len(cell_keys) != len(values) or cell_keys.dtype != torch.int64:
        raise ValueError('cell_keys must be int64 [cells]')
    if token_keys.shape != values.shape[:2] or token_keys.dtype != torch.int64:
        raise ValueError('token_keys must be int64 [cells,tokens]')
    p=float(probability)
    if not 0.0 <= p < 1.0:
        raise ValueError('probability must lie in [0,1)')
    update=_exact_int(update_index,'update_index',0)
    view=_exact_int(view_index,'view_index',0)
    layer=_exact_int(layer_index,'layer_index',0)
    site=_exact_int(site_index,'site_index',0)
    if not training or p == 0.0:
        return values
    device=values.device
    cells=cell_keys.to(device=device)[:,None,None].expand(values.shape)
    tokens=token_keys.to(device=device)[:,:,None].expand(values.shape)
    features=torch.arange(values.shape[2],device=device,dtype=torch.int64)[None,None,:].expand(values.shape)
    h=torch.full(values.shape, 1_234_567, dtype=torch.int64, device=device)
    components=(
        cells,
        tokens,
        features,
        torch.full_like(h,update),
        torch.full_like(h,view),
        torch.full_like(h,layer * 4099 + site),
    )
    for component,multiplier in zip(components,_HASH_MULTIPLIERS):
        h=_hash_fold_mod_prime(h,component,multiplier)
    # Two extra avalanching steps; still exact integer arithmetic on CPU/GPU.
    h=_hash_fold_mod_prime(h, h // 127 + 17, 130363)
    h=_hash_fold_mod_prime(h, h // 8191 + 31, 15485863)
    uniform=(h.to(torch.float64)+0.5)/float(_HASH_PRIME)
    keep=uniform.ge(p)
    return values * keep.to(values.dtype) / (1.0-p)


def scientific_target_cell_probability(
    mode: str,
    *,
    total_cells: int,
    donor_cells: int,
    total_donors: int,
    donors_in_source: int,
    total_sources: int,
) -> float:
    """Per-cell target probability for an explicitly named scientific estimand.

    This defines *p(cell)* only.  It says nothing about how cells are proposed
    or packed for compute.  A sampler with proposal q must separately bind the
    p/q importance correction unless q==p by construction.
    """
    n=_exact_int(total_cells,'total_cells',1)
    nd=_exact_int(donor_cells,'donor_cells',1)
    d=_exact_int(total_donors,'total_donors',1)
    ds=_exact_int(donors_in_source,'donors_in_source',1)
    s=_exact_int(total_sources,'total_sources',1)
    if nd > n or d < s or ds > d:
        raise ValueError('estimand count authority is inconsistent')
    if mode == 'cell_uniform':
        return 1.0/n
    if mode == 'donor_uniform':
        return 1.0/(d*nd)
    if mode == 'source_donor_uniform':
        return 1.0/(s*ds*nd)
    raise ValueError('unsupported scientific estimand; no default is permitted')


def importance_weight_from_probabilities(*, target_probability: float, proposal_probability: float) -> float:
    """Explicit p/q correction; compute packing is downstream and cannot alter it."""
    p=float(target_probability); q=float(proposal_probability)
    vals=torch.tensor([p,q],dtype=torch.float64)
    if not bool(torch.isfinite(vals).all()) or p <= 0.0 or q <= 0.0:
        raise ValueError('target/proposal probabilities must be finite positive values')
    return p/q
