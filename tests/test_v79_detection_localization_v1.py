import json, sys
from pathlib import Path
import numpy as np
from scipy import sparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'/'v77'))
sys.path.insert(0,str(ROOT/'scripts'/'v79'))

import build_v77_topology_calibration as TC
import v77_matched_scoring as MS


def fixture_counts(n=140,g=90):
    rng=np.random.default_rng(7)
    lam=np.linspace(.2,5.0,g)
    x=rng.poisson(lam,size=(n,g)).astype(float)
    x[:,0]=1.0
    x[:,1]=0.0
    return x


def test_selection_matches_frozen_hvg_path():
    import v79_detection_localization as V
    x=fixture_counts(); universe=np.arange(x.shape[1])
    X=sparse.csr_matrix(x); lib=np.asarray(X.sum(1)).ravel()
    _,_,_,sel=TC.hvg_correlation(X,lib,universe,30)
    got=V.canonical_selection(x,universe,30)
    assert np.array_equal(got['selected_positions'],sel)
    assert got['selection_rule']==MS.RULE


def test_constant_detection_genes_preserve_shape_and_count():
    import v79_detection_localization as V
    x=fixture_counts(); universe=np.arange(x.shape[1])
    selected=np.array([0,1,2,3,4])
    got=V.detection_corr(x,universe,selected)
    assert got['corr'].shape==(5,5)
    assert got['selected_gene_count']==5
    assert got['constant_gene_count']>=2
    assert got['variable_gene_count']+got['constant_gene_count']==5
    assert np.isfinite(got['corr']).all()


def test_zero_negative_ratio_is_none_and_json_null():
    import v79_detection_localization as V
    C=np.eye(4)
    C[0,1]=C[1,0]=0.8
    got=V.summarize_corr(C)
    assert got['canonical']['pos_over_neg_ratio'] is None
    assert 'null' in json.dumps(got)


def test_fisher_one_identical_unequal_and_clip():
    import v79_detection_localization as V
    A=np.array([[1,.2,-.4],[.2,1,.1],[-.4,.1,1.0]])
    B=np.array([[1,.8,.2],[.8,1,-.2],[.2,-.2,1.0]])
    one=V.combine_corr_fisher_z([A],[10])
    assert np.allclose(one,A)
    same=V.combine_corr_fisher_z([A,A],[10,90])
    assert np.allclose(same,A)
    got=V.combine_corr_fisher_z([A,B],[1,3])
    exp=np.tanh((np.arctanh(np.clip(A,-.999999,.999999))*1+np.arctanh(np.clip(B,-.999999,.999999))*3)/4)
    np.fill_diagonal(exp,1.0)
    assert np.allclose(got,exp)
    C=A.copy(); C[0,1]=C[1,0]=1.0
    D=A.copy(); D[0,1]=D[1,0]=-1.0
    clipped=V.combine_corr_fisher_z([C,D],[1,1])
    assert np.isfinite(clipped).all()
    assert np.allclose(clipped,clipped.T)
    assert np.allclose(np.diag(clipped),1.0)
