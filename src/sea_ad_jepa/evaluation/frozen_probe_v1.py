"""Deterministic frozen-embedding quality probe for *planted continuous fixtures*.

Not a Bayesian JEPA model, RNA count likelihood, generative decoder, or
biological qualification engine. It never obtains a trainable encoder or EMA
object. An ordinary train-only ridge readout is fitted on fixture folds only.
Any caller-provided origin/provenance declaration is NOT external authentication.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import math

import numpy as np


class FrozenProbeError(ValueError):
    """The fixture-only diagnostic contract is not satisfied."""


def _matrix(value: np.ndarray, name: str, n: int | None = None) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.ndim != 2:
        raise FrozenProbeError(name + " must be a two-dimensional ndarray")
    if value.dtype.kind != "f" or (n is not None and len(value) != n):
        raise FrozenProbeError(name + " must be aligned finite real-valued floats")
    if not np.isfinite(value).all():
        raise FrozenProbeError(name + " contains nonfinite values")
    return np.array(value, dtype=np.float64, copy=True)


def _donors(value: np.ndarray, n: int) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.ndim != 1 or len(value) != n:
        raise FrozenProbeError("donor identities do not align with fixture rows")
    if value.dtype.kind not in "iu" or len(set(int(x) for x in value)) < 10:
        raise FrozenProbeError("at least ten distinct exact donor identities are needed for fixture")
    counts = Counter(int(x) for x in value)
    if min(counts.values()) < 2:
        raise FrozenProbeError("each biological donor needs repeated fixture observations")
    return np.asarray(value, dtype=np.int64).copy()


def _validate_folds(folds, donor_ids: np.ndarray) -> list[tuple[np.ndarray, np.ndarray, tuple[int,...]]]:
    if type(folds) is not list or len(folds) != 5:
        raise FrozenProbeError("expected exactly five independently held-donor fixture folds")
    all_donors = set(int(x) for x in donor_ids)
    held_once = Counter()
    checked = []
    for fold in folds:
        if type(fold) not in (tuple, list) or len(fold) != 2:
            raise FrozenProbeError("fold must have train and held donor lists")
        a,b=fold
        if type(a) is not list or type(b) is not list:
            raise FrozenProbeError("fold roster must be materialized exact lists")
        for values in (a,b):
            if not values or any(type(x) is not int for x in values):
                raise FrozenProbeError("fold identity types or sizes invalid")
            if len(values) != len(set(values)):
                raise FrozenProbeError("repeated donor identity in fold")
        train,held = set(a),set(b)
        if train & held or train | held != all_donors:
            raise FrozenProbeError("fold has donor overlap or incomplete population coverage")
        if len(held)<2 or len(train)<2:
            raise FrozenProbeError("each donor fold needs independent fit/held biological units")
        held_once.update(held)
        mask_fit=np.isin(donor_ids, list(train))
        mask_held=np.isin(donor_ids, list(held))
        if not mask_fit.any() or not mask_held.any() or np.any(mask_fit & mask_held):
            raise FrozenProbeError("unlawful biological unit overlap")
        checked.append((mask_fit,mask_held,tuple(sorted(held))))
    if set(held_once)!=all_donors or any(v!=1 for v in held_once.values()):
        raise FrozenProbeError("every biological donor must be held exactly once")
    return checked


def _fit_and_score(x: np.ndarray, y: np.ndarray, fit: np.ndarray,
                   held: np.ndarray, *, penalty: float) -> np.ndarray:
    # All means/scales and predictive residual variance use TRAIN only.
    mu = x[fit].mean(axis=0)
    sd = x[fit].std(axis=0)
    sd = np.where(sd > 1.e-10, sd, 1.)
    train = np.column_stack((np.ones(int(fit.sum())), (x[fit]-mu)/sd))
    test = np.column_stack((np.ones(int(held.sum())), (x[held]-mu)/sd))
    regularization = np.eye(train.shape[1], dtype=np.float64)*penalty
    regularization[0,0]=0.
    try:
        weights = np.linalg.solve(
            train.T@train + regularization, train.T@y[fit]
        )
    except np.linalg.LinAlgError as exc:
        raise FrozenProbeError("diagnostic linear fit singular") from exc
    residual = y[fit]-train@weights
    sigma2 = max(float(np.mean(residual**2)), 1.e-12)
    nll = .5*(np.log(2.*np.pi*sigma2)+(y[held]-test@weights)**2/sigma2)
    if not np.isfinite(nll).all():
        raise FrozenProbeError("nonfinite held-donor Gaussian predictive score")
    return nll


def _spectrum(embeddings: np.ndarray) -> dict[str,float | bool]:
    centered=embeddings-embeddings.mean(axis=0)
    singular = np.linalg.svd(centered, compute_uv=False)
    rank_zero = bool(np.linalg.norm(centered) <= 1.e-11)
    if rank_zero:
        return {"constant":True,"effective_rank":0.,"top_energy_fraction":1.}
    singular = np.maximum(singular,0.)
    p=singular / singular.sum()
    p=p[p>0]
    entropy=-float(np.sum(p*np.log(p)))
    return {
        "constant":False,
        "effective_rank":float(np.exp(entropy)),
        "top_energy_fraction":float(np.max(singular**2)/np.sum(singular**2)),
    }


def evaluate_frozen_probe(*, donor_ids: np.ndarray, baseline: np.ndarray,
                          embeddings: np.ndarray, target: np.ndarray, folds: list,
                          source_role: str, target_semantics: str,
                          query_leakage_provenance: str, ridge_penalty: float = 2.) -> dict:
    """Score a held-donor fixture, never adjudicate biological qualification.

    A single Gaussian predictive likelihood on *planted continuous* values.
    Caller role fields are strictly a fixture denial gate, not authentication.
    Passing the fixture permits NO real reading, scientific or training authority.
    """
    if (type(source_role) is not str or source_role != "PLANTED_SYNTHETIC_FIXED"
        or type(target_semantics) is not str or target_semantics != "CONTINUOUS_SYNTHETIC"
        or type(query_leakage_provenance) is not str
        or query_leakage_provenance != "EXCLUDED_BY_FIXTURE_CONSTRUCTION"):
        raise FrozenProbeError("only lawful planted continuous fixture may enter this readout")
    if type(ridge_penalty) not in (int,float) or not math.isfinite(ridge_penalty) or ridge_penalty<=0:
        raise FrozenProbeError("prospective fixed ridge penalty must be positive finite")
    if not isinstance(target,np.ndarray) or target.ndim!=1 or target.dtype.kind!="f":
        raise FrozenProbeError("target must be one-dimensional planted continuous float")
    y=np.array(target,dtype=np.float64,copy=True)
    if y.size<20 or not np.isfinite(y).all():
        raise FrozenProbeError("invalid or nonfinite continuous target")
    base=_matrix(baseline,"baseline",len(y))
    z=_matrix(embeddings,"frozen embeddings",len(y))
    if base.shape[1]<1 or z.shape[1]<1:
        raise FrozenProbeError("fixture needs baseline and frozen embedding coordinates")
    # Defeat the most blatant query-leakage forgery even when fixture metadata
    # is falsely asserted. Nontrivial deterministic descendants of q cannot
    # be ruled out from arrays alone; producer lineage authentication remains
    # mandatory before any real-data adapter is possible.
    if any(np.array_equal(base[:,j],y) for j in range(base.shape[1])) or any(
        np.array_equal(z[:,j],y) for j in range(z.shape[1])
    ):
        raise FrozenProbeError("queried target value directly included in permitted readout evidence")
    donors=_donors(donor_ids,len(y))
    valid_folds=_validate_folds(folds,donors)
    # Identity is diagnostic only; SHA over bytes is NOT external source custody.
    hash_input=hashlib.sha256()
    for name,arr in (("donor_ids",donors),("baseline",base),
                     ("embedding",z),("target",y)):
        hash_input.update(name.encode("ascii")+b"\\0")
        hash_input.update(str(arr.shape).encode("ascii")+b"\\0")
        hash_input.update(arr.astype("<f8" if arr.dtype.kind=="f" else "<i8").tobytes())
    identity=hash_input.hexdigest()
    combined=np.column_stack((base,z))
    donor_rows=[]
    fold_rows=[]
    for idx,(fit,held,held_donors) in enumerate(valid_folds):
        baseline_nll=_fit_and_score(base,y,fit,held,penalty=ridge_penalty)
        augmented_nll=_fit_and_score(combined,y,fit,held,penalty=ridge_penalty)
        gain=baseline_nll-augmented_nll
        held_donor=np.asarray(donors[held])
        for donor in held_donors:
            mask=held_donor==donor
            donor_rows.append({
                "donor":int(donor),
                "fold":idx,
                "cells":int(mask.sum()),
                "baseline_nll":float(baseline_nll[mask].mean()),
                "augmented_nll":float(augmented_nll[mask].mean()),
                "delta_nll":float(gain[mask].mean()),
            })
        fold_rows.append({
            "fold":idx,
            "n_fit_donors":len(set(donors[fit].tolist())),
            "n_held_donors":len(held_donors),
            "held_donors":list(held_donors),
            "mean_delta_nll":float(np.mean([
                row["delta_nll"] for row in donor_rows if row["fold"]==idx
            ])),
        })
    donor_rows.sort(key=lambda r:r["donor"])
    return {
        "schema":"JEPA_FROZEN_REPRESENTATION_FOUR_WORLD_DIAGNOSTIC_V1",
        "status":"NON_AUTHORIZING_PLANTED_FIXTURE_DIAGNOSTIC_ONLY",
        "score_family":"TRAIN_ONLY_GAUSSIAN_RIDGE_CONTINUOUS_FIXTURE",
        "fixture_content_sha256":identity,
        "source_authentication":"UNVERIFIED_CALLER_FIXTURE",
        "baseline_covariates":int(base.shape[1]),
        "embedding_width":int(z.shape[1]),
        "n_donors":len(donor_rows),
        "n_cells":len(y),
        "ridge_penalty":float(ridge_penalty),
        "mean_delta_nll":float(np.mean([row["delta_nll"] for row in donor_rows])),
        "geometry":_spectrum(z),
        "donor_rows":donor_rows,
        "folds":fold_rows,
        "fitted_encoder_updates":0,
        "fitted_ema_updates":0,
        "calibrated_biological_uncertainty":False,
        "authority_effect":"NONE",
    }
