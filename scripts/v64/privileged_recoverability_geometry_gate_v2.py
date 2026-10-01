#!/usr/bin/env python3
"""V65 permutation-calibrated recoverability geometry gate.

Software implementation of the prospective V2 geometry contract.
No real data are loaded by this module itself.
"""
from __future__ import annotations

import hashlib
import numpy as np

DEFAULT_PERMUTATIONS=10_000
NULL_QUANTILE=0.99


def permutation_seed_uint64(donor_id: str) -> int:
    msg=f"V65_RECOVERABILITY_PERMUTATION|{donor_id}".encode("utf-8")
    digest=hashlib.sha256(msg).digest()
    return int.from_bytes(digest[:8],byteorder="big",signed=False)


def permutation_indices(donor_id: str, n_rows: int, n_perm: int=DEFAULT_PERMUTATIONS) -> np.ndarray:
    if n_rows < 2:
        raise ValueError("need at least two rows")
    if n_perm < 1:
        raise ValueError("n_perm must be positive")
    rng=np.random.Generator(np.random.PCG64(permutation_seed_uint64(donor_id)))
    return np.stack([rng.permutation(n_rows) for _ in range(n_perm)],axis=0)


def _center_rank(x: np.ndarray):
    x=np.asarray(x,dtype=np.float64)
    if x.ndim!=2:
        raise ValueError("expected 2-D state matrix")
    xc=x-x.mean(axis=0,keepdims=True)
    rank=int(np.linalg.matrix_rank(xc))
    return xc,rank


def _orthonormal_basis(z: np.ndarray) -> np.ndarray:
    zc,rank=_center_rank(z)
    k=zc.shape[1]
    if rank<k:
        raise ValueError("rank-deficient projected state")
    q,_=np.linalg.qr(zc,mode="reduced")
    return q


def _canonical_from_bases(q_true: np.ndarray, q_pred: np.ndarray) -> np.ndarray:
    vals=np.linalg.svd(q_true.T@q_pred,compute_uv=False)
    if not np.isfinite(vals).all():
        raise ValueError("non-finite canonical correlation")
    return vals


def canonical_correlations(z_true: np.ndarray, z_pred: np.ndarray) -> np.ndarray:
    if np.asarray(z_true).shape!=np.asarray(z_pred).shape:
        raise ValueError("true/predicted shared states must have identical shape")
    return _canonical_from_bases(_orthonormal_basis(z_true),_orthonormal_basis(z_pred))


def median_canonical_correlation(z_true: np.ndarray, z_pred: np.ndarray) -> float:
    return float(np.median(canonical_correlations(z_true,z_pred)))


def pairwise_distance_matrix(z: np.ndarray) -> np.ndarray:
    z=np.asarray(z,dtype=np.float64)
    if z.ndim!=2:
        raise ValueError("expected 2-D state matrix")
    if len(z)<3:
        raise ValueError("need at least three rows for relational geometry")
    sq=np.square(z).sum(axis=1)
    d2=sq[:,None]+sq[None,:]-2.0*(z@z.T)
    np.maximum(d2,0.0,out=d2)
    d=np.sqrt(d2)
    if not np.isfinite(d).all():
        raise ValueError("non-finite pairwise distance")
    return d


def pairwise_distance_vector(z: np.ndarray) -> np.ndarray:
    d=pairwise_distance_matrix(z)
    out=d[np.triu_indices(len(d),1)]
    if float(out.std())==0.0:
        raise ValueError("degenerate pairwise-distance vector")
    return out


def relational_geometry_correlation(z_true: np.ndarray, z_pred: np.ndarray) -> float:
    if np.asarray(z_true).shape!=np.asarray(z_pred).shape:
        raise ValueError("true/predicted shared states must have identical shape")
    a=pairwise_distance_vector(z_true)
    b=pairwise_distance_vector(z_pred)
    r=float(np.corrcoef(a,b)[0,1])
    if not np.isfinite(r):
        raise ValueError("non-finite relational-geometry correlation")
    return r


def _higher_quantile(x: np.ndarray, q: float=NULL_QUANTILE) -> float:
    return float(np.quantile(np.asarray(x,dtype=np.float64),q,method="higher"))


def donor_geometry_gate(
    z_true: np.ndarray,
    z_pred: np.ndarray,
    donor_id: str,
    *,
    permutations: np.ndarray | None=None,
    n_perm: int=DEFAULT_PERMUTATIONS,
) -> dict[str,object]:
    a=np.asarray(z_true,dtype=np.float64)
    b=np.asarray(z_pred,dtype=np.float64)
    if a.shape!=b.shape or a.ndim!=2:
        raise ValueError("true/predicted shared states must be aligned 2-D arrays")
    # Fail closed before generating the null, then precompute all invariant
    # quantities so the 10,000 permutations only relabel rows.
    q_true=_orthonormal_basis(a)
    q_pred=_orthonormal_basis(b)
    obs_cc=float(np.median(_canonical_from_bases(q_true,q_pred)))

    d_true=pairwise_distance_matrix(a)
    d_pred=pairwise_distance_matrix(b)
    iu=np.triu_indices(len(a),1)
    true_vec=d_true[iu]
    pred_vec=d_pred[iu]
    if float(true_vec.std())==0.0 or float(pred_vec.std())==0.0:
        raise ValueError("degenerate pairwise-distance vector")
    tc=true_vec-true_vec.mean()
    pc=pred_vec-pred_vec.mean()
    rg_denom=float(np.linalg.norm(tc)*np.linalg.norm(pc))
    if rg_denom==0.0:
        raise ValueError("degenerate relational-geometry denominator")
    obs_rg=float(np.dot(tc,pc)/rg_denom)

    perms=permutation_indices(donor_id,len(a),n_perm) if permutations is None else np.asarray(permutations)
    if perms.ndim!=2 or perms.shape[1]!=len(a):
        raise ValueError("permutation array has wrong shape")
    if len(perms)!=n_perm:
        raise ValueError("permutation count disagrees with n_perm")

    cc_null=np.empty(n_perm,dtype=np.float64)
    rg_null=np.empty(n_perm,dtype=np.float64)
    i0,i1=iu
    # Pairwise-distance mean/norm are invariant under row relabelling.
    true_mean=float(true_vec.mean())
    true_norm=float(np.linalg.norm(tc))
    pred_norm=float(np.linalg.norm(pc))
    for i,p in enumerate(perms):
        cc_null[i]=float(np.median(_canonical_from_bases(q_true[p],q_pred)))
        perm_true=d_true[p[i0],p[i1]]
        rg_null[i]=float(np.dot(perm_true-true_mean,pc)/(true_norm*pred_norm))

    cc_thr=_higher_quantile(cc_null)
    rg_thr=_higher_quantile(rg_null)
    cc_pass=bool(obs_cc>cc_thr)
    rg_pass=bool(obs_rg>rg_thr)
    return {
        "donor_id":str(donor_id),
        "n_rows":int(len(a)),
        "rank":int(a.shape[1]),
        "n_permutations":int(n_perm),
        "seed_uint64":permutation_seed_uint64(str(donor_id)),
        "canonical":{
            "observed":obs_cc,
            "null_q99_higher":cc_thr,
            "pass":cc_pass,
        },
        "relational_geometry":{
            "observed":obs_rg,
            "null_q99_higher":rg_thr,
            "pass":rg_pass,
        },
        "pass":bool(cc_pass and rg_pass),
    }
