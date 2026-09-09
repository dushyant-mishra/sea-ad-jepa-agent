"""Dataset-first support-family mechanics for prospective Teacher/Student V5.

The data define exactly two evidence families for every reader-fit operator:
  * COMMON_CORE: the 17,186 addresses measured as scalar in all 42 operators;
  * OPERATOR_NATIVE: the operator's measured-scalar addresses outside that core.

The teacher always receives the operator's complete lawful measured-scalar
support.  Only student evidence is family-specific.  Both families are evaluated
once per base presentation and combined with exact support-prevalence weights;
there is no equal-family biological mass and no inherited V4 40%/4-view rule.

The keyed half-mask implementation below is a slow, cross-version-stable CPU
reference for mechanics/review.  It is not a production GPU mask kernel and does
not authorize training.
"""
from __future__ import annotations
from fractions import Fraction
import hashlib
from numbers import Integral
from typing import Mapping, Sequence
import torch

_U64=(1<<64)-1
_DOMAIN=b'SEA_AD_JEPA_V5_SUPPORT_FAMILY_HALF_MASK_V3\0'
COMMON_CORE_FAMILY='COMMON_CORE'
OPERATOR_NATIVE_FAMILY='OPERATOR_NATIVE'
SUPPORT_FAMILIES=(COMMON_CORE_FAMILY,OPERATOR_NATIVE_FAMILY)


def _exact(value:object,name:str,minimum:int=0)->int:
    if isinstance(value,bool) or not isinstance(value,Integral):
        raise ValueError(f'{name} must be an exact integer')
    out=int(value)
    if out<minimum: raise ValueError(f'{name} must be >= {minimum}')
    return out


def support_family_counts(*,measured_count:int,common_core_count:int,vocabulary_size:int)->dict[str,dict[str,object]]:
    """Derive family geometry from actual operator support, with no schedule default."""
    m=_exact(measured_count,'measured_count',1)
    c=_exact(common_core_count,'common_core_count',2)
    v=_exact(vocabulary_size,'vocabulary_size',1)
    if not c<m<=v: raise ValueError('support counts must satisfy common_core < measured <= vocabulary')
    n=m-c
    out={
      COMMON_CORE_FAMILY:{
          'family_support_count':c,
          'target_count':c//2,
          'student_visible_count':c-c//2,
          'teacher_support_count':m,
          'family_loss_weight':Fraction(c,m),
      },
      OPERATOR_NATIVE_FAMILY:{
          'family_support_count':n,
          'target_count':n//2,
          'student_visible_count':c+(n-n//2),
          'teacher_support_count':m,
          'family_loss_weight':Fraction(n,m),
      },
    }
    if sum(x['family_loss_weight'] for x in out.values()) != Fraction(1,1):
        raise RuntimeError('support-family loss weights do not sum to one')
    for family,x in out.items():
        family_support=int(x['family_support_count'])
        target=int(x['target_count'])
        if target<1 or int(x['student_visible_count'])<1:
            raise ValueError(f'{family} support cannot form target/visible split')
        per=x['family_loss_weight']*Fraction(target,family_support)*Fraction(1,target)
        if per != Fraction(1,m):
            raise RuntimeError('support-family address mass invariant failed')
        if int(x['teacher_support_count'])!=m:
            raise RuntimeError('teacher must retain complete operator measured support')
    return out


def support_family_loss_weights(*,measured_count:int,common_core_count:int)->dict[str,Fraction]:
    x=support_family_counts(measured_count=measured_count,common_core_count=common_core_count,vocabulary_size=measured_count)
    return {family: value['family_loss_weight'] for family,value in x.items()}


def combine_stratified_family_losses(*,common_core_loss:torch.Tensor,operator_native_loss:torch.Tensor,measured_count:int,common_core_count:int)->torch.Tensor:
    """Exact two-family stratified estimator of the measured-address-uniform loss."""
    if common_core_loss.ndim!=0 or operator_native_loss.ndim!=0:
        raise ValueError('family losses must be scalar tensors')
    if not (common_core_loss.is_floating_point() and operator_native_loss.is_floating_point()):
        raise ValueError('family losses must be floating point')
    if common_core_loss.device!=operator_native_loss.device:
        raise ValueError('family losses must share a device')
    if not bool(torch.isfinite(torch.stack((common_core_loss,operator_native_loss))).all()):
        raise ValueError('family losses must be finite')
    w=support_family_loss_weights(measured_count=measured_count,common_core_count=common_core_count)
    wc=float(w[COMMON_CORE_FAMILY]); wn=float(w[OPERATOR_NATIVE_FAMILY])
    return common_core_loss*wc + operator_native_loss*wn


def _rank_score(*,masking_seed:int,presentation_index:int,cell_key:int,draw_index:int,family:str,address:int)->tuple[bytes,int]:
    seed=_exact(masking_seed,'masking_seed',0); presentation=_exact(presentation_index,'presentation_index',0)
    draw=_exact(draw_index,'draw_index',0); cell=_exact(cell_key,'cell_key',0); addr=_exact(address,'address',0)
    if max(seed,presentation,draw,cell)>_U64: raise ValueError('mask identity integers must fit uint64')
    if addr>0xFFFFFFFF: raise ValueError('canonical address must fit uint32')
    if family not in SUPPORT_FAMILIES: raise ValueError('unsupported support family')
    f=family.encode('utf-8')
    material=(
        _DOMAIN+seed.to_bytes(8,'little')+presentation.to_bytes(8,'little')+
        cell.to_bytes(8,'little')+draw.to_bytes(8,'little')+
        len(f).to_bytes(2,'little')+f+addr.to_bytes(4,'little')
    )
    return hashlib.sha256(material).digest(),addr


def sample_balanced_family_target_mask(
    family_support_mask:torch.Tensor,
    *,masking_seed:int,presentation_indices:torch.Tensor,stable_cell_keys:torch.Tensor,draw_index:int,family:str,
)->torch.Tensor:
    """Cross-version-stable reference exact-half mask keyed by scientific identity.

    Every eligible canonical address gets an independently reconstructed SHA256
    rank.  The lowest floor(n/2) addresses are hidden.  Tensor row, device, optimizer-update index,
    microbatch ordinal, and PyTorch RNG stream never enter the address. Biological view identity is keyed by the frozen base-presentation index.
    """
    if family_support_mask.dtype!=torch.bool or family_support_mask.ndim!=2:
        raise ValueError('family_support_mask must be boolean [cells,genes]')
    if stable_cell_keys.dtype!=torch.int64 or stable_cell_keys.ndim!=1 or len(stable_cell_keys)!=len(family_support_mask):
        raise ValueError('stable_cell_keys must be int64 [cells]')
    if presentation_indices.dtype!=torch.int64 or presentation_indices.ndim!=1 or len(presentation_indices)!=len(family_support_mask):
        raise ValueError('presentation_indices must be int64 [cells]')
    if presentation_indices.device!=stable_cell_keys.device:
        raise ValueError('presentation_indices and stable_cell_keys must share a device')
    if bool((presentation_indices<0).any()):
        raise ValueError('presentation_indices must be nonnegative')
    if bool((stable_cell_keys<0).any()):
        raise ValueError('signed stable_cell_keys must be nonnegative; full uint64 mask kernel needs explicit word authority')
    counts=family_support_mask.sum(1)
    if bool((counts<2).any()) or not bool((counts==counts[0]).all()):
        raise ValueError('family support count must be equal and >=2 within a reference batch')
    target_count=int(counts[0])//2
    cpu=family_support_mask.detach().cpu(); keys=stable_cell_keys.detach().cpu().tolist(); presentations=presentation_indices.detach().cpu().tolist(); out=torch.zeros_like(cpu)
    for r,(key,presentation) in enumerate(zip(keys,presentations)):
        idx=torch.nonzero(cpu[r],as_tuple=False).flatten().tolist()
        ranked=sorted((_rank_score(masking_seed=masking_seed,presentation_index=int(presentation),cell_key=int(key),draw_index=draw_index,family=family,address=int(g)) for g in idx))
        chosen=[address for _,address in ranked[:target_count]]
        out[r,torch.tensor(chosen,dtype=torch.int64)]=True
    return out.to(family_support_mask.device)


def support_family_microbatch_plan(
    operator_ids:Sequence[int],
    measured_tokens_by_operator:Mapping[int,int],
    *,max_teacher_tokens_per_microbatch:int,
)->tuple[tuple[int,...],...]:
    """Pack each frozen base cell once by actual full-teacher operator cost.

    Both support families are evaluated inside each operator-homogeneous
    microbatch.  Family does not duplicate or resample scientific cell slots.
    """
    budget=_exact(max_teacher_tokens_per_microbatch,'max_teacher_tokens_per_microbatch',1)
    if not operator_ids: raise ValueError('operator_ids cannot be empty')
    groups:dict[int,list[int]]={}; first:dict[int,int]={}
    for slot,raw_op in enumerate(operator_ids):
        op=_exact(raw_op,'operator_id',0)
        if op not in measured_tokens_by_operator: raise ValueError(f'missing measured-token support for operator {op}')
        cost=_exact(measured_tokens_by_operator[op],f'measured_tokens[{op}]',1)
        if cost>budget: raise ValueError(f'operator {op} single-cell teacher support exceeds token budget')
        groups.setdefault(op,[]).append(slot); first.setdefault(op,slot)
    out=[]
    for op in sorted(groups,key=lambda x:first[x]):
        cap=max(1,budget//int(measured_tokens_by_operator[op])); slots=groups[op]
        for start in range(0,len(slots),cap): out.append(tuple(slots[start:start+cap]))
    flat=[x for mb in out for x in mb]
    if sorted(flat)!=list(range(len(operator_ids))) or len(flat)!=len(set(flat)):
        raise RuntimeError('support-family packing lost or duplicated base slots')
    return tuple(out)
