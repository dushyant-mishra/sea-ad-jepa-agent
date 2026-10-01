#!/usr/bin/env python3
"""Synthetic audit of the V65 recoverability geometry-gate redundancy.

No real NIH-CARD values are read.

For centered matrices A and B, canonical correlations are the singular values of
Q_A^T Q_B where Q_A and Q_B are orthonormal bases for the centered column spaces.
Those singular values are also, by definition, the cosines of the principal angles
between those column spaces. Treating them as two independent gates is redundant.
"""
from __future__ import annotations

import json
import numpy as np


def _center(x):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2:
        raise ValueError("expected 2-D matrix")
    return x-x.mean(axis=0,keepdims=True)


def principal_angle_cosines(a,b):
    a=_center(a); b=_center(b)
    qa,_=np.linalg.qr(a,mode="reduced")
    qb,_=np.linalg.qr(b,mode="reduced")
    return np.linalg.svd(qa.T@qb,compute_uv=False)


def canonical_correlations(a,b,eps=1e-12):
    a=_center(a); b=_center(b)
    ca=a.T@a
    cb=b.T@b
    cab=a.T@b
    wa,ua=np.linalg.eigh(ca)
    wb,ub=np.linalg.eigh(cb)
    if wa.min()<=eps or wb.min()<=eps:
        raise ValueError("rank-deficient covariance")
    ia=ua@np.diag(1/np.sqrt(wa))@ua.T
    ib=ub@np.diag(1/np.sqrt(wb))@ub.T
    return np.linalg.svd(ia@cab@ib,compute_uv=False)


def relational_geometry_correlation(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if a.shape[0]!=b.shape[0]:
        raise ValueError("row counts differ")
    iu=np.triu_indices(a.shape[0],1)
    da=np.square(a[:,None,:]-a[None,:,:]).sum(axis=2)[iu]
    db=np.square(b[:,None,:]-b[None,:,:]).sum(axis=2)[iu]
    if da.std()==0 or db.std()==0:
        raise ValueError("degenerate pairwise-distance vector")
    return float(np.corrcoef(da,db)[0,1])


def run_audit(seed=65010):
    rng=np.random.default_rng(seed)
    n,k=80,4
    latent=rng.normal(size=(n,k))
    a=latent + .25*rng.normal(size=(n,k))
    mix=rng.normal(size=(k,k))
    b=latent@mix + .30*rng.normal(size=(n,k))

    cc=canonical_correlations(a,b)
    pa=principal_angle_cosines(a,b)
    rg=relational_geometry_correlation(a,b)
    max_abs=float(np.max(np.abs(cc-pa)))

    # A row permutation destroys correspondence while preserving each marginal cloud.
    perm=rng.permutation(n)
    cc_perm=canonical_correlations(a[perm],b)
    rg_perm=relational_geometry_correlation(a[perm],b)

    return {
      "schema":"V65_RECOVERABILITY_GEOMETRY_REDUNDANCY_AUDIT_V1",
      "status":"SYNTHETIC_MATHEMATICAL_AUDIT_ONLY",
      "seed":seed,
      "canonical_correlations":[float(x) for x in cc],
      "principal_angle_cosines":[float(x) for x in pa],
      "max_abs_difference":max_abs,
      "relational_geometry_correlation":rg,
      "permuted_median_canonical_correlation":float(np.median(cc_perm)),
      "permuted_relational_geometry_correlation":rg_perm,
      "redundancy_confirmed":bool(max_abs<1e-10),
      "conclusion":"Centered canonical correlations and principal-angle cosines of the same two column spaces are the same singular values; they cannot serve as two independent geometry gates.",
      "replacement_candidate":"Keep canonical correlation as subspace-alignment gate and use within-donor pairwise-squared-distance relational-geometry correlation as the distinct second permutation-calibrated gate.",
      "real_biology_used":False,
      "execution_authorized":False
    }


def main():
    out=run_audit()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["redundancy_confirmed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
