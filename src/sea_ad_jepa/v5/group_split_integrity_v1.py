"""Outcome-blind split integrity audit for donor-level generalization mechanics.

The audit enforces row uniqueness and donor-disjoint train/validation/test
partitions. Source/operator overlap is reported, not interpreted as proof of
generalization. No split choice, biological claim, D_shared access, or training
authority is granted here.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Sequence


class GroupSplitIntegrityStop(RuntimeError):
    pass

_ALLOWED_SPLITS=("train","validation","test")


def _sha64(value: object, name: str) -> str:
    if not isinstance(value,str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value,16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _aligned_strings(value: Sequence[object], name: str, n: int | None=None, *, unique: bool=False) -> tuple[str,...]:
    if not isinstance(value,Sequence) or isinstance(value,(str,bytes)):
        raise ValueError(f"{name} must be a row-aligned sequence")
    out=tuple(str(x) for x in value)
    if not out or any(not x for x in out):
        raise ValueError(f"{name} must contain nonempty values")
    if n is not None and len(out) != n:
        raise ValueError(f"{name} row count differs")
    if unique and len(set(out)) != len(out):
        raise ValueError(f"{name} must be unique")
    return out


def _overlap_pairs(values: tuple[str,...], splits: tuple[str,...]) -> list[dict[str,object]]:
    by_split={s:set() for s in _ALLOWED_SPLITS}
    for v,s in zip(values,splits):
        by_split[s].add(v)
    out=[]
    for a,b in combinations(_ALLOWED_SPLITS,2):
        overlap=sorted(by_split[a] & by_split[b])
        if overlap:
            out.append({"split_a":a,"split_b":b,"overlap_count":len(overlap),"overlap_values":overlap})
    return out


def audit_group_split_integrity_v1(
    *,
    row_ids: Sequence[object],
    donor_ids: Sequence[object],
    source_ids: Sequence[object],
    operator_ids: Sequence[object],
    split_labels: Sequence[object],
    split_plan_sha256: str,
    parent_sha256: str,
    d_shared_outcomes_used: bool=False,
    protected_data_used: bool=False,
    pathology_used: bool=False,
    training_authorized: bool=False,
) -> dict[str,object]:
    forbidden={
        "d_shared_outcomes_used":d_shared_outcomes_used,
        "protected_data_used":protected_data_used,
        "pathology_used":pathology_used,
        "training_authorized":training_authorized,
    }
    bad=sorted(k for k,v in forbidden.items() if v is not False)
    if bad:
        raise GroupSplitIntegrityStop(f"STOP_SPLIT_INTEGRITY_FORBIDDEN:{','.join(bad)}")

    rows=_aligned_strings(row_ids,"row_ids",unique=True)
    n=len(rows)
    donors=_aligned_strings(donor_ids,"donor_ids",n)
    sources=_aligned_strings(source_ids,"source_ids",n)
    operators=_aligned_strings(operator_ids,"operator_ids",n)
    splits=_aligned_strings(split_labels,"split_labels",n)
    unknown=sorted(set(splits)-set(_ALLOWED_SPLITS))
    if unknown:
        raise ValueError(f"split_labels contain unsupported partitions: {unknown}")
    missing=sorted(set(_ALLOWED_SPLITS)-set(splits))
    if missing:
        raise GroupSplitIntegrityStop(f"STOP_SPLIT_INTEGRITY_MISSING_SPLIT:{','.join(missing)}")

    donor_overlap=_overlap_pairs(donors,splits)
    if donor_overlap:
        raise GroupSplitIntegrityStop("STOP_SPLIT_INTEGRITY_DONOR_LEAKAGE")

    rows_by_split={s:splits.count(s) for s in _ALLOWED_SPLITS}
    donors_by_split={s:len({d for d,sp in zip(donors,splits) if sp==s}) for s in _ALLOWED_SPLITS}

    return {
        "schema":"JEPA_V5_GROUP_SPLIT_INTEGRITY_V1",
        "parent_sha256":_sha64(parent_sha256,"parent_sha256"),
        "split_plan_sha256":_sha64(split_plan_sha256,"split_plan_sha256"),
        "population_count":n,
        "rows_by_split":dict(sorted(rows_by_split.items())),
        "donors_by_split":dict(sorted(donors_by_split.items())),
        "donor_overlap_pairs":[],
        "source_overlap_pairs":_overlap_pairs(sources,splits),
        "operator_overlap_pairs":_overlap_pairs(operators,splits),
        "row_identity_unique":True,
        "donor_disjoint":True,
        "authority_classification":"SPLIT_INTEGRITY_MECHANICS_ONLY__NOT_GENERALIZATION_PROOF",
        "d_shared_real_outcome_access_authorized":False,
        "training_authorized":False,
    }
