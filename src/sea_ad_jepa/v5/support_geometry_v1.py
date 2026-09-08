from __future__ import annotations
from numbers import Integral
from typing import Sequence


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
        "measured_fraction_of_universe":measured/vocab,
        "visible_fraction_within_measured":visible/measured,
        "visible_fraction_of_universe":visible/vocab,
        "hidden_fraction_within_measured":hidden/measured,
    }


def max_fixed_visible_for_support(
    measured_counts: Sequence[int],
    *,
    minimum_hidden_target_genes: int,
) -> int:
    """Derive the largest common visible count that leaves target support everywhere.

    No visible dose or hidden-target requirement is defaulted.  The minimum
    measured operator is the binding support constraint, not an architecture
    constant.
    """
    if not measured_counts:
        raise ValueError("measured_counts cannot be empty")
    measured=tuple(_int(v,"measured_count",1) for v in measured_counts)
    hidden=_int(minimum_hidden_target_genes,"minimum_hidden_target_genes",1)
    limit=min(measured)-hidden
    if limit < 1:
        raise ValueError("required hidden target support leaves no visible evidence for at least one operator")
    return limit


def validate_fixed_visible_across_support(
    measured_counts: Sequence[int],
    *,
    visible_genes: int,
    minimum_hidden_target_genes: int,
) -> dict[str,int]:
    """Fail closed if a proposed evidence dose cannot support every operator."""
    visible=_int(visible_genes,"visible_genes",1)
    maximum=max_fixed_visible_for_support(
        measured_counts, minimum_hidden_target_genes=minimum_hidden_target_genes
    )
    if visible > maximum:
        raise ValueError("visible evidence dose violates minimum hidden-target support on at least one operator")
    minimum_measured=min(int(v) for v in measured_counts)
    return {
        "minimum_measured_support":minimum_measured,
        "minimum_hidden_target_genes":int(minimum_hidden_target_genes),
        "maximum_feasible_visible_genes":maximum,
        "proposed_visible_genes":visible,
        "minimum_realized_hidden_genes":minimum_measured-visible,
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
