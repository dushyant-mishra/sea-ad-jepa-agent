#!/usr/bin/env python3
"""V65 within-donor R2 pairing-permutation gate.

Implements Section 8 of the prospective V2 recoverability contract.
No data are loaded automatically.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
GEOM=HERE/"privileged_recoverability_geometry_gate_v2.py"


def _load_geometry():
    spec=importlib.util.spec_from_file_location("v65_recoverability_geometry",GEOM)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load geometry permutation authority")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


G=_load_geometry()
DEFAULT_PERMUTATIONS=G.DEFAULT_PERMUTATIONS


def r2_multi(z_true: np.ndarray, z_pred: np.ndarray, train_reference_mean: np.ndarray) -> float:
    y=np.asarray(z_true,dtype=np.float64)
    p=np.asarray(z_pred,dtype=np.float64)
    mu=np.asarray(train_reference_mean,dtype=np.float64)
    if y.shape!=p.shape or y.ndim!=2:
        raise ValueError("true/predicted states must be aligned 2-D arrays")
    if mu.ndim!=1 or mu.shape[0]!=y.shape[1]:
        raise ValueError("TRAIN reference mean has wrong shape")
    num=float(np.square(y-p).sum())
    den=float(np.square(y-mu).sum())
    if not np.isfinite(num) or not np.isfinite(den) or den<=0:
        raise ValueError("invalid R2 denominator")
    out=1.0-num/den
    if not np.isfinite(out):
        raise ValueError("non-finite R2")
    return float(out)


def pairing_r2_gate(
    z_true: np.ndarray,
    z_pred: np.ndarray,
    train_reference_mean: np.ndarray,
    donor_id: str,
    *,
    permutations: np.ndarray | None=None,
    n_perm: int=DEFAULT_PERMUTATIONS,
) -> dict[str,object]:
    y=np.asarray(z_true,dtype=np.float64)
    p=np.asarray(z_pred,dtype=np.float64)
    observed=r2_multi(y,p,train_reference_mean)

    perms=G.permutation_indices(str(donor_id),len(y),n_perm) if permutations is None else np.asarray(permutations)
    if perms.ndim!=2 or perms.shape!=(n_perm,len(y)):
        raise ValueError("permutation array has wrong shape")

    null=np.empty(n_perm,dtype=np.float64)
    for i,idx in enumerate(perms):
        null[i]=r2_multi(y[idx],p,train_reference_mean)

    threshold=float(np.quantile(null,0.99,method="higher"))
    return {
        "donor_id":str(donor_id),
        "n_rows":int(len(y)),
        "n_permutations":int(n_perm),
        "seed_uint64":G.permutation_seed_uint64(str(donor_id)),
        "observed_r2":observed,
        "null_q99_higher":threshold,
        "pass":bool(observed>threshold),
    }
