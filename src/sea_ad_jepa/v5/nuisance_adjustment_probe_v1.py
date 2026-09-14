"""Outcome-blind, substrate-independent nuisance comparator mechanics for V5.

This probe measures how much feature variance is predictable from declared
technical covariates under cross-fitting.  It does not choose the final nuisance
model and does not authorize residualization as the production representation.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np


class NuisanceAdjustmentProbeStop(RuntimeError):
    pass


def _matrix(value: object, name: str) -> np.ndarray:
    out=np.asarray(value,dtype=np.float64)
    if out.ndim != 2 or out.shape[0] < 4 or out.shape[1] < 1:
        raise ValueError(f"{name} must be a finite 2-D matrix with >=4 rows")
    if not np.isfinite(out).all():
        raise ValueError(f"{name} must be finite")
    return out


def _ridge(value: object) -> float:
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError("ridge_lambda must be explicit finite nonnegative numeric")
    out=float(value)
    if not math.isfinite(out) or out < 0.0:
        raise ValueError("ridge_lambda must be explicit finite nonnegative numeric")
    return out


def crossfit_nuisance_adjustment_probe_v1(
    *,
    features: object,
    nuisance_covariates: object,
    fold_labels: Sequence[object],
    ridge_lambda: float,
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
        raise NuisanceAdjustmentProbeStop(f"STOP_NUISANCE_PROBE_FORBIDDEN:{','.join(bad)}")

    y=_matrix(features,"features")
    x=_matrix(nuisance_covariates,"nuisance_covariates")
    if len(y) != len(x):
        raise ValueError("feature and nuisance row counts differ")
    labels=tuple(str(v) for v in fold_labels)
    if len(labels) != len(y):
        raise ValueError("fold_labels row count differs")
    unique=tuple(sorted(set(labels)))
    if len(unique) < 2 or any(not label for label in unique):
        raise ValueError("fold_labels must define at least two nonempty folds")
    lam=_ridge(ridge_lambda)

    predictions=np.empty_like(y)
    fold_sizes={}
    for fold in unique:
        test=np.array([label == fold for label in labels],dtype=bool)
        train=~test
        n_test=int(test.sum()); n_train=int(train.sum())
        if n_test < 1 or n_train < 2:
            raise ValueError("each fold must have >=1 test row and >=2 training rows")
        fold_sizes[fold]={"train":n_train,"test":n_test}
        xtr=np.column_stack([np.ones(n_train),x[train]])
        xte=np.column_stack([np.ones(n_test),x[test]])
        penalty=np.eye(xtr.shape[1],dtype=np.float64)*lam
        penalty[0,0]=0.0
        gram=xtr.T@xtr + penalty
        coef=np.linalg.pinv(gram,rcond=1e-12) @ xtr.T @ y[train]
        predictions[test]=xte@coef

    residual=y-predictions
    centered=y-y.mean(axis=0,keepdims=True)
    sse=np.sum(residual*residual,axis=0)
    sst=np.sum(centered*centered,axis=0)
    r2=np.where(sst>0.0,1.0-sse/sst,0.0)
    feature_var=np.var(y,axis=0,ddof=0)
    residual_var=np.var(residual,axis=0,ddof=0)
    ratio=np.divide(residual_var,feature_var,out=np.zeros_like(residual_var),where=feature_var>0)

    return {
        "schema":"JEPA_V5_NUISANCE_ADJUSTMENT_PROBE_V1",
        "model_family":"LINEAR_RIDGE_NUISANCE_COMPARATOR_MECHANICS_V1",
        "population_count":len(y),
        "feature_count":y.shape[1],
        "nuisance_covariate_count":x.shape[1],
        "fold_count":len(unique),
        "fold_sizes":fold_sizes,
        "ridge_lambda":lam,
        "per_feature_crossfit_r2":[float(v) for v in r2],
        "median_crossfit_r2":float(np.median(r2)),
        "mean_crossfit_r2":float(np.mean(r2)),
        "per_feature_residual_variance_ratio":[float(v) for v in ratio],
        "median_residual_variance_ratio":float(np.median(ratio)),
        "authority_classification":"NUISANCE_COMPARATOR_MECHANICS_ONLY__NOT_PRODUCTION_REPRESENTATION",
        "residualized_representation_authorized":False,
        "v3_null_frozen":False,
        "d_shared_real_outcome_access_authorized":False,
        "training_authorized":False,
    }
