"""Scalable, outcome-blind structure-preservation mechanics for V5.

This probe compares distances for a caller-supplied, prospectively frozen set
of row pairs before and after a candidate adjustment. It does not choose the
pairs, define biological truth, or authorize D_shared/training. Its purpose is
to detect overcorrection or geometry destruction without requiring O(N^2)
pairwise distances on the full population.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.stats import rankdata


class StructurePreservationStop(RuntimeError):
    pass


def _sha64(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return value.lower()


def _matrix(value: object, name: str) -> np.ndarray:
    out=np.asarray(value,dtype=np.float64)
    if out.ndim != 2 or out.shape[0] < 2 or out.shape[1] < 1:
        raise ValueError(f"{name} must be a finite 2-D matrix with >=2 rows")
    if not np.isfinite(out).all():
        raise ValueError(f"{name} must be finite")
    return out


def _pairs(value: Sequence[object], n: int) -> tuple[tuple[int,int], ...]:
    if not isinstance(value, Sequence) or isinstance(value,(str,bytes)) or len(value) < 1:
        raise ValueError("pair_indices must contain at least one pair")
    out=[]
    seen=set()
    for raw in value:
        if not isinstance(raw, Sequence) or isinstance(raw,(str,bytes)) or len(raw) != 2:
            raise ValueError("pair_indices entries must be length-2 pairs")
        a,b=raw
        if isinstance(a,bool) or isinstance(b,bool) or not isinstance(a,(int,np.integer)) or not isinstance(b,(int,np.integer)):
            raise ValueError("pair_indices must contain integer indices")
        a=int(a); b=int(b)
        if a == b:
            raise ValueError("pair_indices must use distinct row indices")
        if not (0 <= a < n and 0 <= b < n):
            raise ValueError("pair_indices row index out of range")
        key=(min(a,b),max(a,b))
        if key in seen:
            raise ValueError("duplicate undirected pair in pair_indices")
        seen.add(key)
        out.append((a,b))
    return tuple(out)


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra=rankdata(a,method="average")
    rb=rankdata(b,method="average")
    sa=float(np.std(ra)); sb=float(np.std(rb))
    if sa == 0.0 and sb == 0.0:
        return 1.0 if np.array_equal(ra,rb) else 0.0
    if sa == 0.0 or sb == 0.0:
        return 0.0
    return float(np.corrcoef(ra,rb)[0,1])


def audit_pair_structure_preservation_v1(
    *,
    baseline_representation: object,
    candidate_representation: object,
    pair_indices: Sequence[object],
    pair_plan_sha256: str,
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
        raise StructurePreservationStop(f"STOP_STRUCTURE_PRESERVATION_FORBIDDEN:{','.join(bad)}")

    base=_matrix(baseline_representation,"baseline_representation")
    cand=_matrix(candidate_representation,"candidate_representation")
    if base.shape != cand.shape:
        raise ValueError("baseline and candidate representation shapes differ")
    pairs=_pairs(pair_indices,len(base))
    pair_plan=_sha64(pair_plan_sha256,"pair_plan_sha256")
    parent=_sha64(parent_sha256,"parent_sha256")

    idx_a=np.fromiter((a for a,_ in pairs),dtype=np.int64,count=len(pairs))
    idx_b=np.fromiter((b for _,b in pairs),dtype=np.int64,count=len(pairs))
    d0=np.linalg.norm(base[idx_a]-base[idx_b],axis=1)
    d1=np.linalg.norm(cand[idx_a]-cand[idx_b],axis=1)
    if not np.isfinite(d0).all() or not np.isfinite(d1).all():
        raise ValueError("pair distances must be finite")
    rel=np.abs(d1-d0)/np.maximum(d0,1e-12)
    exact_zero_base=d0 == 0.0
    exact_zero_candidate=d1 == 0.0

    return {
        "schema":"JEPA_V5_STRUCTURE_PRESERVATION_PROBE_V1",
        "parent_sha256":parent,
        "pair_plan_sha256":pair_plan,
        "population_count":len(base),
        "feature_count":base.shape[1],
        "pair_count":len(pairs),
        "distance_spearman":_spearman(d0,d1),
        "median_relative_distance_change":float(np.median(rel)),
        "p95_relative_distance_change":float(np.quantile(rel,0.95)),
        "baseline_zero_distance_pairs":int(exact_zero_base.sum()),
        "candidate_zero_distance_pairs":int(exact_zero_candidate.sum()),
        "zero_distance_status_changed_pairs":int(np.sum(exact_zero_base != exact_zero_candidate)),
        "thresholds_applied":False,
        "authority_classification":"STRUCTURE_PRESERVATION_MECHANICS_ONLY__NOT_BIOLOGICAL_AUTHORITY",
        "d_shared_real_outcome_access_authorized":False,
        "training_authorized":False,
    }
