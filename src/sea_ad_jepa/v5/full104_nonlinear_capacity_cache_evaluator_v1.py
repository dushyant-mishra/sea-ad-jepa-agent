"""Cached nonlinear capacity evaluator for current FULL104 controls."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from typing import Any

import numpy as np

from .full104_control_calibration_cache_evaluator_v1 import LoadedControlCalibrationCacheV1
from .masking_control_executor_v1 import deterministic_within_donor_shuffle

_EPS=1e-12
SEED_NAMESPACE="V5_FULL104_NONLINEAR_CAPACITY_CACHE_V1"


def derive_nonlinear_capacity_seeds(plan_sha256:str)->tuple[int,int]:
    if not isinstance(plan_sha256,str) or len(plan_sha256)!=64:
        raise ValueError("plan_sha256 must be a SHA-256 digest")
    base=f"{SEED_NAMESPACE}|{plan_sha256}".encode("utf-8")
    digest=hashlib.sha256(base).digest()
    model_seed=int.from_bytes(digest[:4],"big",signed=False)
    shuffle_seed=int.from_bytes(digest[4:12],"big",signed=False)
    return model_seed,shuffle_seed


def _rows_for_donor(cache:LoadedControlCalibrationCacheV1,donor:int,cap:int)->np.ndarray:
    ix=np.flatnonzero((cache.donor_code==int(donor)) & (cache.row_rank<int(cap)))
    expected=min(int(cap),int(cache.retained_count_by_donor[int(donor)]))
    if ix.size!=expected or ix.size<1:
        raise ValueError(f"nonlinear cached row selection mismatch for donor {donor}")
    return ix


def _standardize_for_donors(
    cache:LoadedControlCalibrationCacheV1,
    *,
    feature_ix:np.ndarray,
    y:np.ndarray,
    y_stat_ix:int,
    donors:np.ndarray,
    cap:int,
    include_weights:bool,
)->tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray|None]:
    xs=[]; ys=[]; ds=[]; ws=[]
    for raw_donor in donors:
        donor=int(raw_donor)
        rows=_rows_for_donor(cache,donor,cap)
        n_full=int(cache.full_donor_n[donor])
        mean_x=cache.full_donor_sum[donor,feature_ix]/n_full
        var_x=np.maximum(cache.full_donor_sumsq[donor,feature_ix]/n_full-mean_x*mean_x,0.0)
        sd_x=np.where(np.sqrt(var_x)>_EPS,np.sqrt(var_x),1.0)
        mean_y=float(cache.full_donor_sum[donor,int(y_stat_ix)])/n_full
        local_x=(np.asarray(cache.X[rows][:,feature_ix],dtype=np.float64)-mean_x)/sd_x
        local_y=np.asarray(y[rows],dtype=np.float64)-mean_y
        xs.append(local_x); ys.append(local_y); ds.append(np.full(rows.size,donor,dtype=np.int64))
        if include_weights:
            ws.append(np.full(rows.size,1.0/rows.size,dtype=np.float64))
    X=np.vstack(xs); Y=np.concatenate(ys); D=np.concatenate(ds)
    W=np.concatenate(ws) if include_weights else None
    if not np.all(np.isfinite(X)) or not np.all(np.isfinite(Y)):
        raise ValueError("nonlinear standardized cache data contain non-finite values")
    return X,Y,D,W


def _donor_r2(y:np.ndarray,pred:np.ndarray,donor:np.ndarray)->dict[int,float]:
    out={}
    for raw_d in np.unique(donor):
        d=int(raw_d); ix=donor==d
        yy=y[ix]-float(np.mean(y[ix])); pp=pred[ix]-float(np.mean(pred[ix]))
        den=float(np.sqrt(float(yy@yy)*float(pp@pp)))
        r=0.0 if den<=_EPS else float((yy@pp)/den)
        out[d]=r*r
    return out


def _fit_one_fold(
    cache:LoadedControlCalibrationCacheV1,
    *,
    feature_ix:np.ndarray,
    y:np.ndarray,
    y_stat_ix:int,
    fold:int,
    cap:int,
    model_authority:Any,
    model_seed:int,
)->dict[int,float]:
    train=np.flatnonzero(cache.fold_by_donor!=int(fold)).astype(np.int64)
    held=np.flatnonzero(cache.fold_by_donor==int(fold)).astype(np.int64)
    if train.size==0 or held.size==0:
        raise ValueError("nonlinear calibration fold lacks train or heldout donors")
    xtr,ytr,dtr,wtr=_standardize_for_donors(
        cache,feature_ix=feature_ix,y=y,y_stat_ix=y_stat_ix,donors=train,cap=cap,include_weights=True
    )
    xva,yva,dva,_=_standardize_for_donors(
        cache,feature_ix=feature_ix,y=y,y_stat_ix=y_stat_ix,donors=held,cap=cap,include_weights=False
    )
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for nonlinear calibration") from exc
    model=HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=float(model_authority.learning_rate),
        max_iter=int(model_authority.max_iter),
        max_leaf_nodes=int(model_authority.max_leaf_nodes),
        max_depth=None,
        min_samples_leaf=int(model_authority.min_samples_leaf),
        l2_regularization=float(model_authority.l2_regularization),
        max_bins=int(model_authority.max_bins),
        categorical_features=None,
        monotonic_cst=None,
        interaction_cst=None,
        warm_start=False,
        early_stopping=False,
        random_state=int(model_seed),
        verbose=0,
    )
    model.fit(xtr,ytr,sample_weight=wtr)
    return _donor_r2(yva,model.predict(xva),dva)


def _score_target(
    cache:LoadedControlCalibrationCacheV1,
    target_index:int,
    *,
    cap:int,
    model_authority:Any,
    model_seed:int,
    shuffle_seed:int,
)->tuple[int,np.ndarray,np.ndarray]:
    col_to_local={int(col):i for i,col in enumerate(cache.cache_cols)}
    target_col=int(cache.target_cols[target_index])
    proxy_col=int(cache.proxy_cols[target_index])
    feature_cols=(proxy_col,*map(int,cache.distractor_cols))
    if len(feature_cols)!=int(model_authority.feature_count) or len(set(feature_cols))!=len(feature_cols):
        raise ValueError("nonlinear capacity control feature set does not match frozen model capacity")
    feature_ix=np.asarray([col_to_local[col] for col in feature_cols],dtype=np.int64)
    target_ix=int(col_to_local[target_col]); proxy_ix=int(col_to_local[proxy_col])
    planted=np.asarray(cache.X[:,proxy_ix],dtype=np.float64)
    raw_target=np.asarray(cache.X[:,target_ix],dtype=np.float64)
    shuffled=deterministic_within_donor_shuffle(
        raw_target,cache.donor_code,target_id=cache.target_ids[target_index],global_seed=int(shuffle_seed)
    )
    planted_scores=np.full(104,np.nan,dtype=np.float64)
    shuffled_scores=np.full(104,np.nan,dtype=np.float64)
    for fold in sorted(set(map(int,cache.fold_by_donor))):
        for donor,score in _fit_one_fold(
            cache,feature_ix=feature_ix,y=planted,y_stat_ix=proxy_ix,fold=fold,cap=cap,
            model_authority=model_authority,model_seed=model_seed
        ).items():
            planted_scores[donor]=score
        for donor,score in _fit_one_fold(
            cache,feature_ix=feature_ix,y=shuffled,y_stat_ix=target_ix,fold=fold,cap=cap,
            model_authority=model_authority,model_seed=model_seed
        ).items():
            shuffled_scores[donor]=score
    if not np.all(np.isfinite(planted_scores)) or not np.all(np.isfinite(shuffled_scores)):
        raise ValueError("nonlinear capacity score did not cover all 104 donors")
    return target_index,planted_scores,shuffled_scores


def evaluate_nonlinear_capacity_rung(
    cache:LoadedControlCalibrationCacheV1,
    *,
    target_count:int,
    cap:int,
    model_authority:Any,
    plan_sha256:str,
    workers:int,
)->tuple[np.ndarray,np.ndarray]:
    cache.validate(); model_authority.validate()
    if target_count not in (128,256,512,1024):
        raise ValueError("target_count must be a calibrated target-panel rung")
    if cap not in (64,128,256,512,1024):
        raise ValueError("cap must be a frozen nonlinear calibration rung")
    if target_count>cache.target_cols.size:
        raise ValueError("target_count exceeds authenticated cache target envelope")
    if isinstance(workers,bool) or not isinstance(workers,int) or workers<1:
        raise ValueError("workers must be a positive integer")
    model_seed,shuffle_seed=derive_nonlinear_capacity_seeds(plan_sha256)
    planted=np.full((target_count,104),np.nan,dtype=np.float64)
    shuffled=np.full((target_count,104),np.nan,dtype=np.float64)

    def task(index:int):
        return _score_target(
            cache,index,cap=cap,model_authority=model_authority,
            model_seed=model_seed,shuffle_seed=shuffle_seed
        )
    if workers==1:
        results=map(task,range(target_count))
        for index,p,s in results:
            planted[index]=p; shuffled[index]=s
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for index,p,s in pool.map(task,range(target_count)):
                planted[index]=p; shuffled[index]=s
    if not np.all(np.isfinite(planted)) or not np.all(np.isfinite(shuffled)):
        raise ValueError("nonlinear capacity matrices contain non-finite values")
    return planted,shuffled
