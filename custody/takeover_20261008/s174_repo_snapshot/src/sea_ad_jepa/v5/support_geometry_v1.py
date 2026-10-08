from __future__ import annotations
from numbers import Integral


def _int(value: object, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out=int(value)
    if out<minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return out


def fixed_visible_evidence(*, measured_count:int, visible_genes:int, vocabulary_size:int)->dict[str,float|int]:
    """Describe an absolute visible-gene evidence dose without choosing one."""
    measured=_int(measured_count,"measured_count",1)
    visible=_int(visible_genes,"visible_genes",1)
    vocab=_int(vocabulary_size,"vocabulary_size",1)
    if measured>vocab:
        raise ValueError("measured_count exceeds vocabulary_size")
    if visible>measured:
        raise ValueError("visible_genes exceeds measured support")
    hidden=measured-visible
    return {
        "measured_count":measured,
        "visible_count":visible,
        "hidden_count":hidden,
        "visible_fraction_within_measured":visible/measured,
        "visible_fraction_of_universe":visible/vocab,
        "hidden_fraction_within_measured":hidden/measured,
    }


def balanced_block_sizes(*, hidden_count:int, target_genes_per_block:int)->tuple[int,...]:
    """Derive block count from hidden molecular support, with no default budget."""
    hidden=_int(hidden_count,"hidden_count",1)
    target=_int(target_genes_per_block,"target_genes_per_block",1)
    block_count=(hidden+target-1)//target
    quotient,remainder=divmod(hidden,block_count)
    sizes=tuple(quotient+(index<remainder) for index in range(block_count))
    if sum(sizes)!=hidden or max(sizes)>target or min(sizes)<1:
        raise RuntimeError("balanced block geometry invariant failed")
    return sizes
