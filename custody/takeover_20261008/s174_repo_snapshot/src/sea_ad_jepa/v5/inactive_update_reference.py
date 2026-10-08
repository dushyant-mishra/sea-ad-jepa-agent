"""Inactive one-update V5 mechanics reference.

This module is a bounded CPU mechanics harness, not a training runtime. It
accepts an already-frozen scientific cell set, precomputed target-block views,
scientific cell weights, and an explicit compute token budget. It performs no
cell/donor/source selection and has no production schedule defaults.

Its purpose is to prove V5 invariants after support-aware packing:
  * compute packing cannot change the selected cells or scientific weights;
  * weighted accumulation is update-level, not equal-per-microbatch;
  * keyed dropout is addressed by scientific identity;
  * teacher gradients remain absent;
  * AdamW steps exactly once;
  * EMA follows only the proved optimizer step;
  * replay is deterministic for the same frozen inputs and initial state.
"""
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from numbers import Integral
from typing import Mapping, Sequence
import torch

from sea_ad_jepa.v4.ipb_jepa import BlockPredictor, TargetBlocks, gather_block_states
from .data_first_geometry import (
    operator_homogeneous_microbatch_plan,
    pack_valid_tokens,
    weighted_block_jepa_loss,
    weighted_loss_partition_weight,
)
from .keyed_dropout_prototype_v2 import KeyedIPBEncoderV2Reference


@dataclass
class V5ReferenceModules:
    online: KeyedIPBEncoderV2Reference
    teacher: KeyedIPBEncoderV2Reference
    predictor: BlockPredictor
    optimizer: torch.optim.Optimizer


def build_reference_modules(
    *,
    vocabulary_size:int,
    width:int,
    heads:int,
    blocks:int,
    ffn_width:int,
    dropout:float,
    learning_rate:float,
    betas:tuple[float,float],
    eps:float,
    weight_decay:float,
    init_seed:int,
)->V5ReferenceModules:
    torch.manual_seed(int(init_seed))
    online=KeyedIPBEncoderV2Reference(width=width,heads=heads,blocks=blocks,ffn_width=ffn_width,dropout=dropout,vocabulary_size=vocabulary_size)
    teacher=deepcopy(online).eval()
    for p in teacher.parameters(): p.requires_grad_(False)
    predictor=BlockPredictor(width=width,heads=heads)
    online.train(); predictor.train()
    optimizer=torch.optim.AdamW(list(online.parameters())+list(predictor.parameters()),lr=float(learning_rate),betas=betas,eps=float(eps),weight_decay=float(weight_decay))
    return V5ReferenceModules(online,teacher,predictor,optimizer)


def _slice_blocks(blocks:TargetBlocks,rows:Sequence[int])->TargetBlocks:
    idx=torch.tensor(list(rows),dtype=torch.int64,device=blocks.hidden_mask.device)
    return TargetBlocks(
        hidden_mask=blocks.hidden_mask[idx],
        indices=blocks.indices[idx],
        member_mask=blocks.member_mask[idx],
        fallback_counts=blocks.fallback_counts[idx],
    )


def _packed_teacher_blocks(blocks:TargetBlocks,measured_ids:torch.Tensor)->TargetBlocks:
    local=torch.empty_like(blocks.indices)
    for row in range(len(measured_ids)):
        safe=blocks.indices[row].clamp_min(0)
        mapped=torch.searchsorted(measured_ids[row],safe)
        # Every target-block member must be structurally measured and therefore present.
        in_range=mapped < measured_ids.shape[1]
        safe_mapped=mapped.clamp_max(measured_ids.shape[1]-1)
        present=in_range & measured_ids[row,safe_mapped].eq(safe)
        if bool((blocks.member_mask[row] & ~present).any()):
            raise RuntimeError('target block member absent from packed teacher support')
        local[row]=torch.where(blocks.member_mask[row],mapped,torch.full_like(mapped,-1))
    return TargetBlocks(
        hidden_mask=torch.zeros((len(measured_ids),measured_ids.shape[1]),dtype=torch.bool,device=measured_ids.device),
        indices=local,
        member_mask=blocks.member_mask.clone(),
        fallback_counts=blocks.fallback_counts.clone(),
    )


def _snapshot(module:torch.nn.Module)->dict[str,torch.Tensor]:
    return {k:v.detach().clone() for k,v in module.state_dict().items()}


def _optimizer_step_scalar(optimizer:torch.optim.Optimizer)->int:
    steps=[]
    for state in optimizer.state.values():
        if 'step' in state:
            raw=state['step']
            steps.append(int(raw.item()) if torch.is_tensor(raw) else int(raw))
    if not steps: return 0
    if len(set(steps))!=1: raise RuntimeError('optimizer parameter step counters diverged')
    return steps[0]


def _gradient_report(modules:V5ReferenceModules)->dict[str,object]:
    missing=[]; nonfinite=[]; exact_zero=[]; maximum=0.0
    for prefix,module in (('online',modules.online),('predictor',modules.predictor)):
        for name,p in module.named_parameters():
            full=f'{prefix}.{name}'
            if p.grad is None: missing.append(full); continue
            if not bool(torch.isfinite(p.grad).all()): nonfinite.append(full); continue
            maximum=max(maximum,float(p.grad.detach().abs().max()))
            if not bool((p.grad.detach()!=0).any()): exact_zero.append(full)
    teacher_grads=[name for name,p in modules.teacher.named_parameters() if p.grad is not None]
    if missing or nonfinite or exact_zero or teacher_grads:
        raise RuntimeError(f'V5 reference gradient gate failed: missing={missing[:4]} nonfinite={nonfinite[:4]} exact_zero={exact_zero[:4]} teacher_grads={teacher_grads[:4]}')
    return {'missing':0,'nonfinite':0,'exact_zero':0,'teacher_gradients':0,'max_abs_gradient':maximum}


def run_inactive_reference_update(
    modules:V5ReferenceModules,
    *,
    expression:torch.Tensor,
    measurement_mask:torch.Tensor,
    stable_cell_keys:torch.Tensor,
    operator_ids:Sequence[int],
    measured_tokens_by_operator:Mapping[int,int],
    scientific_cell_weights:torch.Tensor,
    target_block_views:Sequence[TargetBlocks],
    max_teacher_tokens_per_microbatch:int,
    run_seed:int,
    update_index:int,
    ema_momentum:float,
)->dict[str,object]:
    if expression.ndim!=2 or measurement_mask.shape!=expression.shape or measurement_mask.dtype!=torch.bool:
        raise ValueError('expression/measurement_mask must be aligned [cells,genes] with boolean mask')
    n=len(expression)
    if n<1 or stable_cell_keys.shape!=(n,) or stable_cell_keys.dtype!=torch.int64 or len(operator_ids)!=n:
        raise ValueError('stable keys/operator IDs must align to nonempty cells')
    if len(torch.unique(stable_cell_keys))!=n: raise ValueError('stable cell keys must be unique within update')
    if scientific_cell_weights.shape!=(n,) or not scientific_cell_weights.is_floating_point() or not bool(torch.isfinite(scientific_cell_weights).all()) or bool((scientific_cell_weights<=0).any()):
        raise ValueError('scientific cell weights must be finite positive [cells]')
    if not target_block_views: raise ValueError('at least one target-block view is required')
    for view in target_block_views:
        if view.hidden_mask.shape!=measurement_mask.shape: raise ValueError('target block view shape mismatch')
        if bool((view.hidden_mask & ~measurement_mask).any()): raise ValueError('target block outside measured support')
    if not 0.0<=float(ema_momentum)<1.0: raise ValueError('ema_momentum must lie in [0,1)')

    plan=operator_homogeneous_microbatch_plan(operator_ids,measured_tokens_by_operator,max_teacher_tokens_per_microbatch=max_teacher_tokens_per_microbatch)
    before_teacher=_snapshot(modules.teacher)
    step_before=_optimizer_step_scalar(modules.optimizer)
    modules.optimizer.zero_grad(set_to_none=True)
    total_mass=float(scientific_cell_weights.double().sum())
    loss_total=0.0

    for mb in plan:
        rows=list(mb); ridx=torch.tensor(rows,dtype=torch.int64)
        mb_expr=expression[ridx]; mb_measured=measurement_mask[ridx]; mb_cells=stable_cell_keys[ridx]; mb_w=scientific_cell_weights[ridx]
        pt=pack_valid_tokens(mb_expr,mb_measured); true_t=torch.ones_like(pt.canonical_gene_ids,dtype=torch.bool)
        with torch.no_grad():
            teacher_state=modules.teacher(pt.canonical_gene_ids,pt.expression,true_t,torch.zeros_like(true_t),'target',cell_keys=mb_cells,run_seed=run_seed,update_index=update_index,view_index=0)
        for view_index,full_blocks in enumerate(target_block_views, start=1):
            blocks=_slice_blocks(full_blocks,rows)
            visible=mb_measured & ~blocks.hidden_mask
            ps=pack_valid_tokens(mb_expr,visible); true_s=torch.ones_like(ps.canonical_gene_ids,dtype=torch.bool)
            student_state=modules.online(ps.canonical_gene_ids,ps.expression,true_s,torch.zeros_like(true_s),'student',cell_keys=mb_cells,run_seed=run_seed,update_index=update_index,view_index=view_index)
            prediction=modules.predictor(modules.online.tokenizer.gene_identity,blocks,student_state.gene_states,student_state.cell_state,true_s)
            teacher_blocks=gather_block_states(teacher_state.gene_states,_packed_teacher_blocks(blocks,pt.canonical_gene_ids))
            local=weighted_block_jepa_loss(prediction,teacher_blocks,mb_w)
            alpha=weighted_loss_partition_weight(local_weight_mass=float(mb_w.double().sum()),total_weight_mass=total_mass)/len(target_block_views)
            contribution=local*alpha
            contribution.backward()
            loss_total+=float(local.detach())*alpha

    gradient_report=_gradient_report(modules)
    modules.optimizer.step()
    step_after=_optimizer_step_scalar(modules.optimizer)
    if step_after!=step_before+1: raise RuntimeError(f'optimizer did not step exactly once: {step_before}->{step_after}')
    m=float(ema_momentum)
    with torch.no_grad():
        for teacher,online in zip(modules.teacher.parameters(),modules.online.parameters()):
            teacher.mul_(m).add_(online,alpha=1.0-m)
    # Exact EMA equation relative to pre-step teacher and post-step V5 online.
    online_state=modules.online.state_dict(); teacher_state=modules.teacher.state_dict()
    max_ema_error=0.0
    for name,before in before_teacher.items():
        if name not in dict(modules.teacher.named_parameters()):
            continue
        expected=before.clone()
        expected.mul_(m).add_(online_state[name],alpha=1.0-m)
        error=float((teacher_state[name]-expected).abs().max())
        max_ema_error=max(max_ema_error,error)
        if not torch.equal(teacher_state[name],expected):
            raise RuntimeError(f'EMA equation mismatch at {name}: {error}')
    return {
        'schema':'V5_INACTIVE_REFERENCE_UPDATE_V1',
        'cells':n,'views':len(target_block_views),'microbatches':len(plan),
        'microbatch_plan':plan,'scientific_weight_mass':total_mass,'loss':loss_total,
        'optimizer_step_before':step_before,'optimizer_step_after':step_after,
        'ema_max_abs_error':max_ema_error,'gradient_gate':gradient_report,
        'execution_authorized':False,'training_authorized':False,
    }

@dataclass(frozen=True)
class V5ReferenceCheckpoint:
    """In-memory proof checkpoint for the inactive V5 mechanics harness.

    This is not a production checkpoint schema.  It proves which state is
    mechanically necessary once dropout is keyed by scientific coordinates.
    """
    schema: str
    online_state: dict[str, torch.Tensor]
    teacher_state: dict[str, torch.Tensor]
    predictor_state: dict[str, torch.Tensor]
    optimizer_state: dict[str, object]
    next_update_index: int
    presentations_seen: int
    execution_authorized: bool = False
    training_authorized: bool = False


def capture_reference_checkpoint(
    modules: V5ReferenceModules,
    *,
    next_update_index: int,
    presentations_seen: int,
) -> V5ReferenceCheckpoint:
    if isinstance(next_update_index, bool) or not isinstance(next_update_index, Integral) or int(next_update_index) < 0:
        raise ValueError('next_update_index must be an exact nonnegative integer')
    if isinstance(presentations_seen, bool) or not isinstance(presentations_seen, Integral) or int(presentations_seen) < 0:
        raise ValueError('presentations_seen must be an exact nonnegative integer')
    update = int(next_update_index)
    presentations = int(presentations_seen)
    step = _optimizer_step_scalar(modules.optimizer)
    if step != update:
        raise ValueError(f'checkpoint cursor/optimizer step mismatch: next_update_index={update} optimizer_step={step}')
    return V5ReferenceCheckpoint(
        schema='V5_INACTIVE_REFERENCE_CHECKPOINT_V1',
        online_state=deepcopy(modules.online.state_dict()),
        teacher_state=deepcopy(modules.teacher.state_dict()),
        predictor_state=deepcopy(modules.predictor.state_dict()),
        optimizer_state=deepcopy(modules.optimizer.state_dict()),
        next_update_index=update,
        presentations_seen=presentations,
    )


def restore_reference_checkpoint(
    modules: V5ReferenceModules,
    checkpoint: V5ReferenceCheckpoint,
) -> tuple[int, int]:
    if not isinstance(checkpoint, V5ReferenceCheckpoint) or checkpoint.schema != 'V5_INACTIVE_REFERENCE_CHECKPOINT_V1':
        raise ValueError('unsupported V5 reference checkpoint')
    if checkpoint.execution_authorized or checkpoint.training_authorized:
        raise ValueError('reference checkpoint cannot contain execution authority')
    modules.online.load_state_dict(deepcopy(checkpoint.online_state), strict=True)
    modules.teacher.load_state_dict(deepcopy(checkpoint.teacher_state), strict=True)
    modules.predictor.load_state_dict(deepcopy(checkpoint.predictor_state), strict=True)
    modules.optimizer.load_state_dict(deepcopy(checkpoint.optimizer_state))
    modules.online.train(); modules.predictor.train(); modules.teacher.eval()
    for p in modules.teacher.parameters():
        p.requires_grad_(False)
        p.grad = None
    step = _optimizer_step_scalar(modules.optimizer)
    if step != checkpoint.next_update_index:
        raise RuntimeError('restored optimizer step does not match checkpoint cursor')
    return checkpoint.next_update_index, checkpoint.presentations_seen
