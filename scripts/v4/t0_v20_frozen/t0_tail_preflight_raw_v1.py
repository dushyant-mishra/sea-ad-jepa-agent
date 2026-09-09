from __future__ import annotations
import numpy as np
try:
    import scipy.sparse as sp
except Exception:
    sp=None
from t0_feature_authority_v1 import load_feature_authority
from t0_primary_membership_v1 import load_membership,validate_cells_against_membership
from t0_stable_cell_key_v1 import parse_stable_key_exact
from t0_tail_support_coherence_v1 import adjudicate_tail_support_coherence,MIN_TAIL_CELLS,MIN_REST_CELLS
from t0_tail_qc_randomization_v1 import tail_qc_veto_test

CHUNK=1024


def _norm_block(X,start,end,lib):
    if sp is not None and sp.issparse(X): B=X[:,start:end].toarray()
    else: B=np.asarray(X[:,start:end])
    B=np.asarray(B,dtype=np.float64)
    if not np.isfinite(B).all() or np.any(B<0) or np.any(np.floor(B)!=B): raise ValueError('invalid holdout raw counts')
    return np.log1p(10000.0*B/lib[:,None])


def discovery_holdout_scale(*,holdout_raw_counts,donor_id,stable_key,source_library):
    X=holdout_raw_counts; n,g=X.shape; d=np.asarray([str(x) for x in donor_id]); keys=np.asarray([parse_stable_key_exact(x) for x in stable_key],dtype=np.int64); lib=np.asarray(source_library,dtype=np.float64)
    if len(d)!=n or len(keys)!=n or lib.shape!=(n,) or np.any(lib<=0) or not np.isfinite(lib).all(): raise ValueError('discovery holdout input mismatch')
    donors=sorted(set(d),key=lambda x:x.encode('utf-8'))
    if len(donors)<2: raise ValueError('need >=2 discovery donors')
    out=np.zeros(g,dtype=np.float64)
    for start in range(0,g,CHUNK):
        end=min(g,start+CHUNK); B=_norm_block(X,start,end,lib); vars=[]
        for u in donors:
            ix=np.flatnonzero(d==u); ix=ix[np.argsort(keys[ix],kind='mergesort')]
            if len(ix)<2: raise ValueError('every scaling donor needs >=2 cells')
            vars.append(np.var(B[ix],axis=0,ddof=1))
        out[start:end]=np.sqrt(np.mean(np.vstack(vars),axis=0))
    tol=64*np.finfo(np.float64).eps*np.maximum(1.0,out)
    decision=np.isfinite(out)&(out>tol)
    if not np.any(decision): raise ValueError('no decision-capable holdout features')
    return out,decision


def confirmation_holdout_vectors(*,holdout_raw_counts,donor_id,stable_key,source_library,tail_masks_by_donor,scale,decision_mask):
    X=holdout_raw_counts; n,g=X.shape; d=np.asarray([str(x) for x in donor_id]); keys=np.asarray([parse_stable_key_exact(x) for x in stable_key],dtype=np.int64); lib=np.asarray(source_library,dtype=np.float64); scale=np.asarray(scale,float); mask=np.asarray(decision_mask)
    if len(d)!=n or len(keys)!=n or lib.shape!=(n,) or scale.shape!=(g,) or mask.shape!=(g,) or mask.dtype!=np.bool_: raise ValueError('confirmation holdout input mismatch')
    observed=set(d); donors=sorted(map(str,tail_masks_by_donor.keys()),key=lambda x:x.encode('utf-8')); vectors=[]; tcounts=[]; rcounts=[]
    if not donors or not set(donors).issubset(observed): raise ValueError('tail-measurable donor masks do not match confirmation rows')
    # Accumulate mean tail/rest differences chunk-wise for each donor.
    V=np.zeros((len(donors),g),dtype=np.float64)
    for j,u in enumerate(donors):
        ix=np.flatnonzero(d==u); ix=ix[np.argsort(keys[ix],kind='mergesort')]; tm=np.asarray(tail_masks_by_donor[u])
        if tm.dtype!=np.bool_ or len(tm)!=len(ix): raise ValueError('tail mask/holdout row mismatch')
        tcounts.append(int(tm.sum())); rcounts.append(int((~tm).sum()))
    for start in range(0,g,CHUNK):
        end=min(g,start+CHUNK); B=_norm_block(X,start,end,lib)
        for j,u in enumerate(donors):
            ix=np.flatnonzero(d==u); ix=ix[np.argsort(keys[ix],kind='mergesort')]; tm=np.asarray(tail_masks_by_donor[u])
            if tm.sum()>0 and (~tm).sum()>0:
                V[j,start:end]=(B[ix][tm].mean(0)-B[ix][~tm].mean(0))/np.where(scale[start:end]>0,scale[start:end],1.0)
    V[:,~mask]=0.0
    # Normalize only decision-capable vectors; non-decision rows remain zero for adjudicator filtering.
    for j in range(len(donors)):
        norm=float(np.linalg.norm(V[j,mask]));
        if np.isfinite(norm) and norm>0: V[j,mask]/=norm
        else: V[j,:]=0.0
    return donors,V,tcounts,rcounts


def raw_tail_preflight(*,discovery_holdout_raw_counts,discovery_donor_id,discovery_stable_key,discovery_source_library,confirmation_holdout_raw_counts,confirmation_donor_id,confirmation_stable_key,confirmation_source_library,confirmation_summaries):
    scale,mask=discovery_holdout_scale(holdout_raw_counts=discovery_holdout_raw_counts,donor_id=discovery_donor_id,stable_key=discovery_stable_key,source_library=discovery_source_library)
    donors,V,tc,rc=confirmation_holdout_vectors(holdout_raw_counts=confirmation_holdout_raw_counts,donor_id=confirmation_donor_id,stable_key=confirmation_stable_key,source_library=confirmation_source_library,tail_masks_by_donor=confirmation_summaries['tail_masks_by_donor'],scale=scale,decision_mask=mask)
    support=adjudicate_tail_support_coherence(V,tc,rc)
    if not support['support_ok']:
        return {'support':support,'qc':None,'qc_ok':False,'coherence_ok':False,'decision_donors':support['decision_donors'],'tail_measurable_donors':donors}
    decision_donors=[]; qc=[]; masks=[]; keys=[]
    for u,t,r,vec in zip(donors,tc,rc,V):
        if t>=MIN_TAIL_CELLS and r>=MIN_REST_CELLS and np.isfinite(vec).all() and np.linalg.norm(vec)>0:
            decision_donors.append(u); qc.append(confirmation_summaries['qc_by_donor'][u]); masks.append(confirmation_summaries['tail_masks_by_donor'][u]); keys.append(confirmation_summaries['stable_keys_by_donor'][u])
    qcr=tail_qc_veto_test(qc,masks,keys,decision_donors)
    return {'support':support,'qc':qcr,'qc_ok':bool(not qcr['veto']),'coherence_ok':bool(support['coherence_ok']),'decision_donors':support['decision_donors'],'tail_measurable_donors':donors,'holdout_decision_features':int(mask.sum())}
