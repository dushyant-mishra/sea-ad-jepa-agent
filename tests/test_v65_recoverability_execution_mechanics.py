from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def _load():
    p=ROOT/"scripts/v64/privileged_recoverability_execution_mechanics_smoke_v1.py"
    spec=importlib.util.spec_from_file_location("v65_mech",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def test_execution_mechanics_contract_freezes_exact_preprocessing():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_EXECUTION_MECHANICS_CONTRACT_20260930.md").read_text()
    assert "IDF_j = log(1 + N_train / (1 + df_j))" in t
    assert "No additional scale factor" in t
    assert "Z_priv_ATAC_V1 = (Z_raw - TRAIN_mean) / TRAIN_SD" in t
    assert "RNA_log1p10k_ig = log(1 + 10000 * RNA_ig / R_i)" in t
    assert "largest alpha" in t
    assert "No rank/shell-specific candidate fit is allowed" in t
    assert "No model or baseline may be refit for a rank or shell" in t
    assert "recoverability_execution_authorized=false" in t

def test_tfidf_is_train_fitted_and_formula_exact():
    m=_load()
    A=np.array([[1,0],[0,1],[1,1]],float)
    idf=m.fit_tfidf(A)
    # n=3, df=(2,2): log(1 + 3/(1+2)) = log(2)
    assert np.allclose(idf,np.log(2.0))
    held=np.array([[10,0]],float)
    got=m.transform_tfidf(held,idf)
    assert np.allclose(got,[[np.log(2.0),0]])

def test_zero_variance_rna_feature_is_preserved_as_zero():
    m=_load()
    X=np.array([[1.,5.],[2.,5.],[3.,5.]])
    mu,sd=m.fit_standardizer(X)
    out=m.apply_standardizer(X,mu,sd,zero_to_zero=True)
    assert sd[1]==0
    assert np.all(out[:,1]==0)
    assert out.shape==X.shape

def test_alpha_tie_chooses_largest_alpha():
    m=_load()
    scores={a:0.25 for a in m.ALPHAS}
    assert m.pick_alpha_from_scores(scores)==100.0

def test_svd_sign_and_boundary_rules_are_deterministic():
    m=_load()
    M=np.array([[3.,0.,1.],[0.,2.,1.],[1.,1.,4.],[2.,0.,2.]])
    B,s=m.svd_basis(M,2)
    for c in range(2):
        idx=int(np.flatnonzero(np.abs(B[:,c])==np.abs(B[:,c]).max())[0])
        assert B[idx,c]>0
    assert m._boundary_tied(np.array([3.,2.,2.]),2) is True

def test_synthetic_execution_mechanics_smoke_passes():
    out=_load().run_smoke()
    assert out["real_biology_used"] is False
    assert out["pass"] is True
