from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
import numpy as np
import pytest

SCRIPT=Path("scripts/v64/nihcard_realism_calibrated_qualification_v2.py")

def load():
    spec=importlib.util.spec_from_file_location("realism_v2",SCRIPT)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def test_average_rank_handles_ties_exactly():
    m=load()
    r=m.average_rank(np.array([1,1,1,2,4,4],float))
    assert np.allclose(r,[2,2,2,4,5.5,5.5])

def test_copula_rank_reordering_preserves_exact_marginal_multiset():
    m=load()
    rng=np.random.default_rng(7)
    x1=np.array([1,1,1,2,2,5,9,9,29],float)
    x2=np.array([10,10,20,20,30,40,50,60,70],float)
    X=np.column_stack([x1,x2])
    fit=m.fit_copula(X,lambda _:None)
    Y=m.sample_copula_exact_marginals(fit,rng)
    assert Y.shape==X.shape
    for j in range(X.shape[1]):
        assert np.array_equal(np.sort(Y[:,j]),np.sort(X[:,j]))

def test_realism_receipt_uses_tie_aware_spearman_and_reports_exact_multisets():
    m=load()
    X=np.array([[1,0],[1,1],[2,1],[2,3],[5,3]],float)
    fit=m.fit_copula(X,lambda _:None)
    Y=m.sample_copula_exact_marginals(fit,np.random.default_rng(11))
    r=m.realism_receipt(X,Y,["a","b"],lambda _:None,method="test")
    assert r["method"]=="test"
    assert all(v["exact_empirical_multiset_preserved"] for v in r["per_variable"].values())
    assert np.isfinite(r["worst_abs_pairwise_SPEARMAN_discrepancy"])

def test_row_resampling_is_whole_row_only():
    m=load()
    X=np.arange(60,dtype=float).reshape(20,3)
    Y=m.sample_rows(X,np.random.default_rng(3))
    rows={tuple(r) for r in X}
    assert all(tuple(r) in rows for r in Y)

def test_stage3_receipt_must_bind_exact_feature_digest(tmp_path):
    m=load()
    f=tmp_path/"features.npz"
    np.savez(f,X=np.zeros((2,14)),names=np.array([str(i) for i in range(14)]))
    d=sha(f)
    receipt=tmp_path/"receipt.json"
    receipt.write_text(json.dumps({"outcome_blind_feature_artifact":{"sha256":d}}))
    out=m.bind_stage3_feature_provenance(str(receipt),str(f),d)
    assert out["real_feature_artifact_sha256"]==d

    bad=tmp_path/"bad.json"
    bad.write_text(json.dumps({"outcome_blind_feature_artifact":{"sha256":"0"*64}}))
    with pytest.raises(SystemExit,match="DOES_NOT_BIND"):
        m.bind_stage3_feature_provenance(str(bad),str(f),d)

def test_feature_digest_mismatch_fails_before_receipt_credit(tmp_path):
    m=load()
    f=tmp_path/"features.npz"
    np.savez(f,X=np.zeros((2,14)),names=np.array([str(i) for i in range(14)]))
    receipt=tmp_path/"receipt.json"; receipt.write_text("{}")
    with pytest.raises(SystemExit,match="SHA256_MISMATCH"):
        m.bind_stage3_feature_provenance(str(receipt),str(f),"0"*64)
