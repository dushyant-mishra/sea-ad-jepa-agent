"""Independent tiny fixtures; these do NOT authenticate physical FULL104 inputs."""
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'reader_fit_linear_lodo_v1.py'
spec = importlib.util.spec_from_file_location('reader_fit_linear_lodo_v1', MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def fixture(seed=17):
    r = np.random.default_rng(seed)
    donors = ['a','b','c','d']
    sizes = [8, 11, 14, 6]
    xs, ys, dc = [],[],[]
    truth = np.array([[.4,.2,-.3],[-.2,.8,.1],[.5,-.4,.9]])
    for i,n in enumerate(sizes):
        x = r.normal(size=(n,3)) + (i/5.)
        y = x@truth + r.normal(scale=.03,size=(n,3))
        xs.append(x);ys.append(y);dc.extend([i]*n)
    return donors,sizes,np.vstack(xs),np.vstack(ys),np.array(dc)


def moments():
    donors,sizes,X,Y,dc = fixture()
    out = {}
    for i,d in enumerate(donors):
        m = mod.Moments.empty(3)
        m.add_block(X[dc==i],Y[dc==i])
        out[d]=m
    return out


def direct_fit_train(moments, excluded, donor_uniform=True):
    _,_,X,Y,dc=fixture()
    train=[i for i in range(4) if chr(97+i)!=excluded]
    xx=np.vstack([X[dc==i] for i in train]); yy=np.vstack([Y[dc==i] for i in train])
    if donor_uniform:
        weights=np.concatenate([np.full(np.sum(dc==i),1/np.sum(dc==i)) for i in train])
    else:weights=np.ones(len(xx))
    weights/=weights.sum()
    xm=weights@xx; ym=weights@yy
    sd=np.maximum(np.sqrt(np.sum(weights[:,None]*(xx-xm)**2,axis=0)),1e-12)
    scaled=(xx-xm)/sd
    sol=np.linalg.solve(scaled.T@(weights[:,None]*scaled)+.01*np.eye(3),
                        scaled.T@(weights[:,None]*(yy-ym)))
    B=sol/sd[:,None]; b=ym-xm@B
    return B,b,ym


@pytest.mark.parametrize('donor_uniform',[True,False])
def test_independent_direct_weighted_solution(donor_uniform):
    m=moments()
    for d in sorted(m):
        train=[v for k,v in m.items() if k!=d]
        B,b=mod.fit_ridge(train,donor_uniform=donor_uniform)
        ref_B,ref_b,_=direct_fit_train(m,d,donor_uniform)
        np.testing.assert_allclose(B,ref_B,rtol=1e-10,atol=1e-10)
        np.testing.assert_allclose(b,ref_b,rtol=1e-10,atol=1e-10)


@pytest.mark.parametrize('donor_uniform',[True,False])
def test_score_quadratic_equals_direct(donor_uniform):
    m=moments();_,_,X,Y,dc=fixture()
    for i,d in enumerate(sorted(m)):
        train=[v for k,v in m.items() if k!=d]
        B,b=mod.fit_ridge(train,donor_uniform=donor_uniform)
        ym=mod.train_target_mean(train,donor_uniform)
        sse,sst=mod.score_moments(m[d],B,b,train_target_mean=ym)
        np.testing.assert_allclose(sse,np.sum((Y[dc==i]-(X[dc==i]@B+b))**2),rtol=1e-10)
        np.testing.assert_allclose(sst,np.sum((Y[dc==i]-ym)**2),rtol=1e-10)


def test_donor_order_does_not_change_macro_metrics():
    m=moments();x=mod.evaluate_donor_lodo(m)
    y=mod.evaluate_donor_lodo(dict(reversed(list(m.items()))))
    for field in ('cell_pooled_r2','donor_uniform_r2','donor_median_r2'):
        np.testing.assert_allclose(x[field],y[field],rtol=1e-12)
    assert x['n_donors']==4 and x['n_cells']==39


def test_visibility_decoy_not_used(monkeypatch):
    monkeypatch.setattr(mod,'WIDTH',3)
    _,_,X,Y,dc=fixture()
    n=len(dc);v0=np.hstack([X,np.full((n,3),1e9)])
    v1=np.hstack([Y,np.full((n,3),-1e9)])
    got=mod.gather_moments(v0,v1,dc,np.array(list('abcd')),chunk_rows=7)
    direct=moments()
    for d in got:
        np.testing.assert_allclose(got[d].xx,direct[d].xx,rtol=1e-12)
        np.testing.assert_allclose(got[d].xy,direct[d].xy,rtol=1e-12)


def test_nonfinite_rejected():
    x=np.eye(3);y=x.copy();y[0,0]=np.nan
    with pytest.raises(ValueError,match='nonfinite'):
        mod.Moments.empty(3).add_block(x,y)


def test_lodo_requires_three_donors():
    m=moments()
    with pytest.raises(ValueError,match='three'):
        mod.evaluate_donor_lodo({'a':m['a'],'b':m['b']})


def test_empty_train_rejected():
    with pytest.raises(ValueError,match='zero'):
        mod.sum_moments([mod.Moments.empty(3)],donor_uniform=True)


def test_duplicate_donor_rejected(monkeypatch):
    monkeypatch.setattr(mod,'WIDTH',3)
    x=np.ones((2,6)); y=x.copy()
    with pytest.raises(ValueError,match='duplicate'):
        mod.gather_moments(x,y,np.array([0,1]),np.array(['a','a']),chunk_rows=1)


def test_chunked_equals_unchunked(monkeypatch):
    monkeypatch.setattr(mod,'WIDTH',3)
    _,_,X,Y,dc=fixture()
    a=mod.gather_moments(X,Y,dc,np.array(list('abcd')),chunk_rows=1)
    b=mod.gather_moments(X,Y,dc,np.array(list('abcd')),chunk_rows=len(X))
    for d in a:
        np.testing.assert_allclose(a[d].xx,b[d].xx,atol=1e-12)
        np.testing.assert_allclose(a[d].xy,b[d].xy,atol=1e-12)


def test_wrong_physical_receipt_digest_refused(tmp_path):
    x=tmp_path/'receipt.json';x.write_text(json.dumps({'schema':'V5_FULL104_PASS1_PHYSICAL_BINDING_RECEIPT_V1'}))
    with pytest.raises(ValueError,match='SHA-256 mismatch'):
        mod.verify_binding_receipt(x,'0'*64)


def test_unsigned_receipt_refused(tmp_path):
    x=tmp_path/'receipt.json';x.write_text('{}')
    with pytest.raises(ValueError,match='pinned'):
        mod.verify_binding_receipt(x,'')


def test_no_overwrite_even_before_input_probe(tmp_path):
    x=tmp_path/'result.json';x.write_text('preserve')
    with pytest.raises(ValueError,match='already exists'):
        mod.run(pass1=tmp_path/'absent1',v0=tmp_path/'absent2',v1=tmp_path/'absent3',
                physical_receipt=tmp_path/'absent4',physical_receipt_sha='0'*64,out=x)
    assert x.read_text()=='preserve'
