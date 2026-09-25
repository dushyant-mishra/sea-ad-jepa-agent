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


# Independent red-team successor. Synthetic fixtures NEVER certify physical FULL104.
def _synthetic_physical_receipt():
    return {
        'schema': 'V5_FULL104_PASS1_PHYSICAL_BINDING_RECEIPT_V1',
        'pass1_npz_sha256': mod.FROZEN_PASS1_SHA256,
        'full104_block_manifest_sha256': mod.BLOCK_MANIFEST_SHA256,
        'canonical_registry_sha256': mod.CANONICAL_REGISTRY_SHA256,
        'observation_state_sha256': mod.OBSERVATION_STATE_SHA256,
        **{k: '1'*64 for k in (
            'cell_donor_semantic_sha256', 'cell_nnz_core_semantic_sha256',
            'donor_core_nnz_semantic_sha256', 'donor_ids_semantic_sha256',
            'donor_source_semantic_sha256', 'strict_core_cols_semantic_sha256')},
        'source_names': list(mod.SOURCE_NAMES), 'operator_count': 42,
        'address_count': 41238, 'strict_core_state_code': 2,
        'block_count': 8915, 'row_count': mod.EXPECTED_ROWS,
        'donor_count': mod.EXPECTED_DONORS,
        'terminal_masking_outcomes_inspected': False,
        'protected_outcomes_authorized': False, 'training_authorized': False,
    }


def _signed_fixture(tmp_path, payload):
    p = tmp_path / 'synthetic_receipt.json'
    p.write_text(json.dumps(payload, sort_keys=True))
    import hashlib
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def test_positive_synthetic_binding_receipt_structure(tmp_path):
    p, sha = _signed_fixture(tmp_path, _synthetic_physical_receipt())
    assert mod.verify_binding_receipt(p, sha)['donor_count'] == mod.EXPECTED_DONORS


@pytest.mark.parametrize('field,value', [
    ('full104_block_manifest_sha256', 'a'*64),
    ('canonical_registry_sha256', 'b'*64),
    ('observation_state_sha256', 'c'*64),
    ('source_names', ['SEA_AD', 'NPH52', 'HVS']),
    ('donor_source_semantic_sha256', 'INVALID'),
    ('terminal_masking_outcomes_inspected', True),
])
def test_internally_bad_but_sha_pinned_receipt_rejected(tmp_path, field, value):
    payload = _synthetic_physical_receipt()
    payload[field] = value
    p, sha = _signed_fixture(tmp_path, payload)
    with pytest.raises(ValueError, match='scope mismatch'):
        mod.verify_binding_receipt(p, sha)


def test_donor_code_negative_and_out_of_range_fail_before_indexing(monkeypatch):
    monkeypatch.setattr(mod, 'WIDTH', 3)
    x = np.ones((3, 6))
    y = x.copy()
    ids = np.array(['a', 'b', 'c'])
    for codes in [np.array([-1, 1, 2]), np.array([0, 1, 3])]:
        with pytest.raises(ValueError, match='outside authenticated roster'):
            mod.gather_moments(x, y, codes, ids, chunk_rows=2)
    with pytest.raises(ValueError, match='non-object strings'):
        mod.gather_moments(x, y, np.array([0, 1, 2]),
                           np.array(['a', 'b', 'c'], dtype=object), chunk_rows=2)


def test_large_offset_cancellation_fails_instead_of_perfect_r2():
    x = np.arange(30., dtype=np.float64).reshape(10, 3)
    y = 1e9 + np.arange(30., dtype=np.float64).reshape(10, 3)
    m = mod.Moments.empty(3)
    m.add_block(x, y)
    with pytest.raises(ValueError, match='SCORE_NUMERICALLY_UNRESOLVED'):
        mod.score_moments(m, np.zeros((3, 3)), np.full(3, 1e9),
                          train_target_mean=np.full(3, 1e9))


def test_postread_rehash_refuses_changed_input_without_receipt(tmp_path, monkeypatch):
    # Fake tiny geometry. Simulate source replacement AFTER the first valid
    # SHA read; require another digest check BEFORE result publication.
    monkeypatch.setattr(mod, 'EXPECTED_ROWS', 45)
    monkeypatch.setattr(mod, 'EXPECTED_DONORS', 9)
    monkeypatch.setattr(mod, 'EXPECTED_SHAPE', (45, 6))
    monkeypatch.setattr(mod, 'EXPECTED_SOURCE_COUNTS',
                        {'HVS': 3, 'NPH52': 3, 'SEA_AD': 3})
    monkeypatch.setattr(mod, 'WIDTH', 3)
    p = tmp_path / 'pass1.npz'
    np.savez(p, cell_donor=np.repeat(np.arange(9), 5),
             duniq=np.array([f'd{i}' for i in range(9)]),
             donor_src=np.repeat(np.arange(3), 3))
    rng = np.random.default_rng(34)
    X = rng.normal(size=(45, 6)).astype(np.float32)
    Y = np.zeros((45, 6), dtype=np.float32)
    Y[:, :3] = X[:, :3] @ np.array(
        [[.2, .3, .1], [-.1, .5, .2], [.4, .1, .7]],
        dtype=np.float32) + rng.normal(scale=.1, size=(45, 3))
    v0 = tmp_path / 'v0.npy'
    v1 = tmp_path / 'v1.npy'
    np.save(v0, X)
    np.save(v1, Y)
    monkeypatch.setattr(mod, 'verify_binding_receipt',
                        lambda *a, **kw: {'schema': 'V5_FULL104_PASS1_PHYSICAL_BINDING_RECEIPT_V1'})
    seen = []
    def synthetic_verifier(path, expected):
        seen.append(path.name)
        if len(seen) == 6:
            raise ValueError('SHA-256 mismatch: source changed after initial verification')
    monkeypatch.setattr(mod, 'require_exact_file', synthetic_verifier)
    out = tmp_path / 'must_not_exist.json'
    with pytest.raises(ValueError, match='changed after initial verification'):
        mod.run(pass1=p, v0=v0, v1=v1, physical_receipt=tmp_path/'fake',
                physical_receipt_sha='f'*64, out=out, chunk_rows=8)
    assert seen == [p.name, v0.name, v1.name, p.name, v0.name, v1.name]
    assert not out.exists()
