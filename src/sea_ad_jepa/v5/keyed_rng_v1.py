from __future__ import annotations
from dataclasses import dataclass
from numbers import Integral
import torch

MODULUS = 2_147_483_647  # 2^31-1; square remains safely inside signed int64.


def _int(value: object, name: str, minimum: int = 0, maximum: int = MODULUS-1) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out=int(value)
    if out < minimum or out > maximum:
        raise ValueError(f"{name} must be in [{minimum},{maximum}]")
    return out


def _mix(h: torch.Tensor, x: torch.Tensor | int, salt: int) -> torch.Tensor:
    if not isinstance(x, torch.Tensor):
        x=torch.tensor(int(x),dtype=torch.int64,device=h.device)
    x=torch.remainder(x.to(dtype=torch.int64,device=h.device),MODULUS)
    h=torch.remainder(h*h + (104_729 + 2*salt)*x + 1_000_003 + salt, MODULUS)
    h=torch.remainder(h*h + (130_363 + 2*salt)*x + 1_000_033 + 3*salt, MODULUS)
    return h


@dataclass(frozen=True)
class KeyedDropoutSpec:
    dropout_numerator: int = 1
    dropout_denominator: int = 10

    def validate(self) -> None:
        num=_int(self.dropout_numerator,'dropout_numerator',0,1_000_000)
        den=_int(self.dropout_denominator,'dropout_denominator',1,1_000_000)
        if num >= den:
            raise ValueError('dropout probability must be in [0,1)')


def keyed_dropout_mask(
    canonical_token_ids: torch.Tensor,
    cell_keys: torch.Tensor,
    *,
    width: int,
    training_seed: int,
    update_index: int,
    view_index: int,
    site_id: int,
    spec: KeyedDropoutSpec = KeyedDropoutSpec(),
) -> torch.Tensor:
    """Stateless packing-invariant dropout mask over scientific token identity.

    canonical_token_ids is [batch,tokens]. Use -1 for the cell token and
    canonical 0..vocabulary-1 for genes. cell_keys is one stable nonnegative
    integer identity per row. site_id is an externally registered exact integer
    distinguishing every dropout site/layer.

    This is a V5 candidate RNG primitive, not V4 replay authority.
    """
    spec.validate()
    if canonical_token_ids.ndim != 2 or canonical_token_ids.dtype not in (torch.int32,torch.int64):
        raise ValueError('canonical_token_ids must be integer [batch,tokens]')
    if cell_keys.ndim != 1 or len(cell_keys)!=len(canonical_token_ids) or cell_keys.dtype not in (torch.int32,torch.int64):
        raise ValueError('cell_keys must be one integer per row')
    if bool((canonical_token_ids < -1).any()):
        raise ValueError('token IDs below -1 are forbidden')
    if bool((cell_keys < 0).any()):
        raise ValueError('cell_keys must be nonnegative')
    width=_int(width,'width',1,1_000_000)
    seed=_int(training_seed,'training_seed')
    update=_int(update_index,'update_index')
    view=_int(view_index,'view_index')
    site=_int(site_id,'site_id')
    device=canonical_token_ids.device
    b,t=canonical_token_ids.shape
    token=(canonical_token_ids.to(torch.int64)+1)[:,:,None]
    cell=cell_keys.to(device=device,dtype=torch.int64)[:,None,None]
    feat=torch.arange(width,device=device,dtype=torch.int64)[None,None,:]
    h=torch.full((b,t,width), seed % MODULUS,dtype=torch.int64,device=device)
    for salt,x in enumerate((update,view,site,cell,token,feat),start=1):
        h=_mix(h,x,salt)
    keep_num=spec.dropout_denominator-spec.dropout_numerator
    threshold=(MODULUS*keep_num)//spec.dropout_denominator
    return h < threshold


def keyed_dropout(x: torch.Tensor, mask: torch.Tensor, spec: KeyedDropoutSpec = KeyedDropoutSpec()) -> torch.Tensor:
    spec.validate()
    if mask.shape != x.shape or mask.dtype is not torch.bool:
        raise ValueError('mask must be boolean and match x shape')
    keep_num=spec.dropout_denominator-spec.dropout_numerator
    if keep_num <= 0:
        raise ValueError('zero keep probability is forbidden')
    return x * mask.to(x.dtype) * (spec.dropout_denominator/keep_num)
