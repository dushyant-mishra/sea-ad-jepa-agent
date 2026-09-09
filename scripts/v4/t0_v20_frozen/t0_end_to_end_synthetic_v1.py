#!/usr/bin/env python3
"""Small end-to-end synthetic audit of the JEPA T0 discovery/confirmation hierarchy."""
from __future__ import annotations
import hashlib
import numpy as np
from t0_target_learner_v1 import fit_t0_target, score_expression
from t0_weighted_quantile_v1 import equal_donor_cell_quantile
from t0_fl_permutation_authority_v1 import permutation
from t0_studentized_fl_v1 import studentized_freedman_lane
from t0_holdout_preprocess_v1 import equal_donor_within_scale, tail_rest_vector
from t0_coherence_statistic_v1 import loo_coherence
from t0_coherence_exact_v1 import exact_common_direction_test


def nuisance(age, sex):
    age=np.asarray(age,float); sex=np.asarray(sex,float)
    ac=age-age.mean()
    return np.c_[np.ones(len(age)),ac,ac**2,sex]


def perms(donors, B=399):
    base=sorted(map(str,donors))
    # inference arrays use donor-sorted order in this audit
    return np.asarray([permutation(base,r) for r in range(B)],dtype=int)


def _hash_fit(fit):
    h=hashlib.sha256()
    for k in ('beta','mu','sigma'):
        h.update(np.ascontiguousarray(fit[k],dtype='<f8').tobytes())
    h.update(np.asarray([fit['selected_multiplier_exponent']],dtype='<f8').tobytes())
    return h.hexdigest()


def make_world(seed=7, state_effect=2.5, tail_effect=0.0, null=False):
    r=np.random.default_rng(seed)
    nd,nc=28,18; g=8; gh=16; cells=400
    n=nd+nc
    donors=np.array([f'd{i:02d}' for i in range(n)])
    age=r.normal(78,6,n); sex=np.array(([0,1]*(n//2))[:n],float)
    z=r.normal(size=n)
    # donor-specific excess-tail propensity, independent of z
    q=r.normal(size=n)
    w=r.normal(size=g); w/=np.linalg.norm(w)
    wh=r.normal(size=gh); wh/=np.linalg.norm(wh)
    Xcells=[]; Hcells=[]; means=[]; true_tail=[]
    for i in range(n):
        # 5--25% shifted cells depending on q; mean-centered tail structure remains.
        frac=1/(1+np.exp(-(-2.2+0.9*q[i])))
        is_tail=r.random(cells)<frac
        x=r.normal(scale=.45,size=(cells,g)) + z[i]*w
        # Mean-preserving tail-shape perturbation: q changes skew/tail prevalence,
        # not the donor mean along w. This is the estimand the incremental tail gate targets.
        n_tail=int(is_tail.sum()); n_rest=cells-n_tail
        if n_tail>0 and n_rest>0:
            a=5.0
            x[is_tail]+=a*w
            x[~is_tail]-=(a*n_tail/n_rest)*w
        h=r.normal(scale=.65,size=(cells,gh))
        if n_tail>0 and n_rest>0:
            a_h=2.5
            h[is_tail]+=a_h*wh
            h[~is_tail]-=(a_h*n_tail/n_rest)*wh
        Xcells.append(x); Hcells.append(h); means.append(x.mean(axis=0)); true_tail.append(frac)
    means=np.vstack(means); true_tail=np.asarray(true_tail)
    ac=age-age.mean()
    base=.08*ac+.002*ac**2+.2*sex
    if null:
        y=base+r.normal(scale=1.2,size=n)
    else:
        y=base+state_effect*z+tail_effect*q+r.normal(scale=.55,size=n)
    return dict(donors=donors,age=age,sex=sex,y=y,means=means,Xcells=Xcells,Hcells=Hcells,true_tail=true_tail,true_w=w,true_wh=wh,true_q=q,true_z=z)


def run_world(world, B=399):
    donors=world['donors']; y=world['y']; Z=nuisance(world['age'],world['sex'])
    di=np.arange(28); ci=np.arange(28,46)
    fit=fit_t0_target(world['means'][di],y[di],world['age'][di],world['sex'][di],donors[di])
    fit_hash=_hash_fit(fit)
    # Cell scores and discovery threshold.
    d_scores=[score_expression(world['Xcells'][i],fit) for i in di]
    centered=[s-s.mean() for s in d_scores]
    threshold=equal_donor_cell_quantile(centered,.95)
    # Confirmation donor-sorted order is already d28..d45.
    c_scores=[score_expression(world['Xcells'][i],fit) for i in ci]
    state=np.asarray([s.mean() for s in c_scores])
    tail=np.asarray([np.mean((s-s.mean())>threshold) for s in c_scores])
    P=perms(donors[ci],B)
    state_test=studentized_freedman_lane(y[ci],Z[ci],state,P)
    # Tail is only formally interpreted after state support, but compute for audit.
    Ztail=np.c_[Z[ci],state]
    tail_test=studentized_freedman_lane(y[ci],Ztail,tail,P)
    # Orthogonal holdout coherence among confirmation tail/rest cells.
    disc_H=np.vstack([world['Hcells'][i] for i in di])
    disc_d=np.concatenate([[donors[i]]*len(world['Hcells'][i]) for i in di])
    scale,mask=equal_donor_within_scale(disc_H,disc_d)
    vec=[]
    for k,i in enumerate(ci):
        tm=(c_scores[k]-c_scores[k].mean())>threshold
        if tm.sum()>=2 and (~tm).sum()>=2:
            vec.append(tail_rest_vector(world['Hcells'][i],tm,scale,mask))
    if len(vec)>=3:
        VV=np.vstack(vec); coh=loo_coherence(VV); coh_exact=exact_common_direction_test(VV)
    else:
        coh=None; coh_exact=None
    return dict(fit=fit,fit_hash=fit_hash,threshold=threshold,state=state,tail=tail,state_test=state_test,tail_test=tail_test,coherence=coh,coherence_exact=coh_exact)


if __name__=='__main__':
    for name,kw in [
        ('null',dict(null=True)),
        ('state_only',dict(state_effect=3.0,tail_effect=0.0)),
        ('state_plus_tail',dict(state_effect=2.0,tail_effect=2.0)),
    ]:
        out=run_world(make_world(**kw),B=399)
        print(name, out['state_test']['p_upper'], out['tail_test']['p_upper'], out['coherence']['loo_mean_cosine'])
