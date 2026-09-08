"""Injective Philox4x32-10 dropout addressing contract for prospective V5.

This is a CPU/reference contract only.  It removes the V1 site's truncated
hashing from the random address.  Within the declared coordinate ranges, every
scientific dropout element maps injectively to one (Philox counter, key) pair.
No tensor position, microbatch ordinal, device ordinal, or packing shape enters.

Nothing in this module is execution authority and no GPU kernel is authorized.
"""
from __future__ import annotations
from numbers import Integral
import torch

_MASK32=0xFFFFFFFF
_M0=0xD2511F53
_M1=0xCD9E8D57
_W0=0x9E3779B9
_W1=0xBB67AE85


def _bounded(value:object,name:str,upper:int)->int:
    if isinstance(value,bool) or not isinstance(value,Integral):
        raise ValueError(f'{name} must be an exact integer')
    out=int(value)
    if out<0 or out>upper:
        raise ValueError(f'{name} must lie in [0,{upper}]')
    return out


def _mulhilo32(a:int,b:int)->tuple[int,int]:
    product=(int(a)*int(b)) & 0xFFFFFFFFFFFFFFFF
    return (product>>32)&_MASK32, product&_MASK32


def philox4x32_10(counter:tuple[int,int,int,int],key:tuple[int,int])->tuple[int,int,int,int]:
    if len(counter)!=4 or len(key)!=2:
        raise ValueError('Philox4x32 requires four counter words and two key words')
    c=[_bounded(v,f'counter[{i}]',_MASK32) for i,v in enumerate(counter)]
    k=[_bounded(v,f'key[{i}]',_MASK32) for i,v in enumerate(key)]
    for round_index in range(10):
        hi0,lo0=_mulhilo32(_M0,c[0]); hi1,lo1=_mulhilo32(_M1,c[2])
        c=[(hi1^c[1]^k[0])&_MASK32,lo1,(hi0^c[3]^k[1])&_MASK32,lo0]
        if round_index!=9:
            k[0]=(k[0]+_W0)&_MASK32; k[1]=(k[1]+_W1)&_MASK32
    return tuple(c)  # type: ignore[return-value]


def dropout_philox_address(
    *,
    run_seed:int,
    update_index:int,
    domain_index:int,
    view_index:int,
    layer_index:int,
    site_index:int,
    cell_key:int,
    canonical_token_key:int,
    feature_index:int,
)->tuple[tuple[int,int,int,int],tuple[int,int]]:
    """Encode one dropout element injectively into Philox input words.

    Exact allocation:
      key[0]    = uint32 run_seed
      key[1]    = uint32 update_index
      counter0  = stable_cell_key low32
      counter1  = stable_cell_key high32
      counter2  = (feature_uint16 << 16) | (canonical_token_key + 1)_uint16
      counter3  = domain_uint8<<24 | site_uint8<<16 | layer_uint8<<8 | view_uint8

    token -1 is reserved for the cell token. Gene IDs 0..41,237 fit the uint16
    token field. Feature coordinates up to 65,535 are supported.  The declared
    model width/FFN widths are therefore far below the contract bound.
    """
    seed=_bounded(run_seed,'run_seed',_MASK32)
    update=_bounded(update_index,'update_index',_MASK32)
    domain=_bounded(domain_index,'domain_index',0xFF)
    view=_bounded(view_index,'view_index',0xFF)
    layer=_bounded(layer_index,'layer_index',0xFF)
    site=_bounded(site_index,'site_index',0xFF)
    cell=_bounded(cell_key,'cell_key',0xFFFFFFFFFFFFFFFF)
    if isinstance(canonical_token_key,bool) or not isinstance(canonical_token_key,Integral):
        raise ValueError('canonical_token_key must be an exact integer')
    token=int(canonical_token_key)
    if token < -1 or token > 65_534:
        raise ValueError('canonical_token_key must lie in [-1,65534]')
    feature=_bounded(feature_index,'feature_index',0xFFFF)
    c0=cell&_MASK32
    c1=(cell>>32)&_MASK32
    c2=((feature&0xFFFF)<<16)|((token+1)&0xFFFF)
    c3=(domain<<24)|(site<<16)|(layer<<8)|view
    return (c0,c1,c2,c3),(seed,update)


def keyed_dropout_u32(**kwargs:int)->int:
    counter,key=dropout_philox_address(**kwargs)
    return philox4x32_10(counter,key)[0]


def u32_open_unit(value:int)->float:
    word=_bounded(value,'value',_MASK32)
    return (word+0.5)/4294967296.0


def keyed_dropout_keep(*,probability:float,**kwargs:int)->bool:
    p=float(probability)
    if not 0.0<=p<1.0:
        raise ValueError('probability must lie in [0,1)')
    return u32_open_unit(keyed_dropout_u32(**kwargs))>=p


def keyed_feature_dropout_reference(
    values:torch.Tensor,
    *,
    cell_keys:torch.Tensor,
    token_keys:torch.Tensor,
    probability:float,
    run_seed:int,
    update_index:int,
    domain_index:int,
    view_index:int,
    layer_index:int,
    site_index:int,
    training:bool=True,
)->torch.Tensor:
    """Slow exact CPU-reference tensor dropout using the injective address map.

    It is intentionally unsuitable as the production GPU kernel.  Its purpose
    is to make dense/packed mechanics independently testable against exact V2
    bit semantics before any optimized kernel exists.
    """
    if values.ndim!=3 or not values.is_floating_point() or not bool(torch.isfinite(values).all()):
        raise ValueError('values must be finite floating [cells,tokens,features]')
    if cell_keys.ndim!=1 or len(cell_keys)!=len(values) or cell_keys.dtype!=torch.int64:
        raise ValueError('cell_keys must be int64 [cells]')
    if token_keys.shape!=values.shape[:2] or token_keys.dtype!=torch.int64:
        raise ValueError('token_keys must be int64 [cells,tokens]')
    p=float(probability)
    if not 0.0<=p<1.0:
        raise ValueError('probability must lie in [0,1)')
    if not training or p==0.0:
        return values
    cells=cell_keys.detach().cpu().tolist(); tokens=token_keys.detach().cpu().tolist()
    mask=torch.empty(values.shape,dtype=torch.bool,device='cpu')
    for row,cell in enumerate(cells):
        for col,token in enumerate(tokens[row]):
            for feature in range(values.shape[2]):
                mask[row,col,feature]=keyed_dropout_keep(
                    probability=p,run_seed=run_seed,update_index=update_index,
                    domain_index=domain_index,view_index=view_index,layer_index=layer_index,
                    site_index=site_index,cell_key=cell,canonical_token_key=token,feature_index=feature,
                )
    return values * mask.to(device=values.device,dtype=values.dtype) / (1.0-p)
