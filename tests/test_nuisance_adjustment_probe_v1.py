import numpy as np
import pytest

from sea_ad_jepa.v5.nuisance_adjustment_probe_v1 import crossfit_nuisance_adjustment_probe_v1


def test_crossfit_nuisance_probe_detects_strong_technical_structure_without_authority_escalation():
    rng=np.random.default_rng(19)
    n=240
    x=rng.normal(size=(n,2))
    beta=np.array([[2.0,-1.0,0.5],[1.0,1.5,-2.0]])
    y=x@beta + 0.15*rng.normal(size=(n,3))
    folds=np.arange(n)%6
    out=crossfit_nuisance_adjustment_probe_v1(
        features=y,nuisance_covariates=x,fold_labels=folds,ridge_lambda=0.01,
    )
    assert out["population_count"] == n
    assert out["fold_count"] == 6
    assert out["median_crossfit_r2"] > 0.95
    assert out["authority_classification"] == "NUISANCE_COMPARATOR_MECHANICS_ONLY__NOT_PRODUCTION_REPRESENTATION"
    assert out["residualized_representation_authorized"] is False
    assert out["d_shared_real_outcome_access_authorized"] is False


def test_crossfit_nuisance_probe_does_not_manufacture_explanatory_power_on_noise():
    rng=np.random.default_rng(23)
    n=300
    x=rng.normal(size=(n,3))
    y=rng.normal(size=(n,5))
    folds=np.arange(n)%5
    out=crossfit_nuisance_adjustment_probe_v1(
        features=y,nuisance_covariates=x,fold_labels=folds,ridge_lambda=1.0,
    )
    assert out["median_crossfit_r2"] < 0.15


def test_probe_requires_true_crossfit_and_aligned_finite_inputs():
    y=np.ones((8,2)); x=np.ones((8,1))
    with pytest.raises(ValueError,match="fold"):
        crossfit_nuisance_adjustment_probe_v1(features=y,nuisance_covariates=x,fold_labels=[0]*8,ridge_lambda=1.0)
    with pytest.raises(ValueError,match="row"):
        crossfit_nuisance_adjustment_probe_v1(features=y,nuisance_covariates=x[:7],fold_labels=np.arange(8)%2,ridge_lambda=1.0)
    bad=y.copy(); bad[0,0]=np.nan
    with pytest.raises(ValueError,match="finite"):
        crossfit_nuisance_adjustment_probe_v1(features=bad,nuisance_covariates=x,fold_labels=np.arange(8)%2,ridge_lambda=1.0)


def test_probe_rejects_implicit_or_invalid_ridge_values():
    y=np.arange(24,dtype=float).reshape(12,2)
    x=np.arange(12,dtype=float).reshape(12,1)
    folds=np.arange(12)%3
    for value in (-1.0,float("nan"),True):
        with pytest.raises(ValueError,match="ridge_lambda"):
            crossfit_nuisance_adjustment_probe_v1(features=y,nuisance_covariates=x,fold_labels=folds,ridge_lambda=value)


def test_probe_rejects_outcome_feedback_and_training_authority():
    y=np.arange(24,dtype=float).reshape(12,2)
    x=np.arange(12,dtype=float).reshape(12,1)
    folds=np.arange(12)%3
    for field in ("d_shared_outcomes_used","protected_data_used","pathology_used","training_authorized"):
        with pytest.raises(RuntimeError,match="STOP_NUISANCE_PROBE_FORBIDDEN"):
            crossfit_nuisance_adjustment_probe_v1(
                features=y,nuisance_covariates=x,fold_labels=folds,ridge_lambda=1.0,**{field:True}
            )
