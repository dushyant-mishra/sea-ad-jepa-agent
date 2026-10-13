from __future__ import annotations
import inspect, sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))
import td_test_qualification_package_v1 as P
import td_relational_successor_synthetic_adapter_v1 as A


def _package(missing=()):
    caps={}
    fit={}
    for i,cap in enumerate(A.MANDATORY_RELATIONAL_CAPABILITIES):
        if cap in missing: continue
        cid=f'opaque-{i:02d}'
        fit[cid]=f'{i+1:064x}'[-64:]
        sem='STRESS_TRUTH' if cap=='REL_SOURCE_VISIBILITY_STRESS' else ('NEGATIVE_TRUTH' if 'NEGATIVE' in cap else ('UNDERIDENTIFIED_TRUTH' if cap=='REL_UNDERPOWERED_POSITIVE' else 'POSITIVE_TRUTH'))
        caps[cap]={'capability_id':cap,'challenge_id':cid,'semantic_class':sem}
    return P.ValidatedExternalPackage('pkg','a'*64,fit,'b'*64,caps)


def _payloads(pkg):
    n=3
    base={
        'source':'UNIT','panel_id':'P0',
        'z_distances':np.zeros((n,n)),'x_distances':np.zeros((n,n)),'y_distances':np.zeros((n,n)),
        'donor_ids':np.array(['D0','D0','D0']), 'operator_ids':np.array([0,0,0]), 'global_rows':np.arange(n),
        'focal_mask':np.ones(n,bool),'neighbor_pool_mask':np.ones(n,bool),
        'null_y_identity_maps':np.tile(np.arange(n),(64,1)),
        'min_focal_anchors_per_donor':1,
    }
    return {cid:{'authenticated_fit_view_sha256':sha,'executor_input':dict(base)} for cid,sha in pkg.fit_views.items()}


def test_complete_adapter_keeps_fit_side_blind_and_controller_map_separate():
    pkg=_package(); r=A.build_relational_qualification_adapter(pkg,_payloads(pkg))
    assert r.status=='READY'
    assert not r.missing_capabilities
    assert set(r.fit_inputs)==set(pkg.fit_views)
    assert set(r.controller_challenges)==set(pkg.fit_views)
    for cid,fit in r.fit_inputs.items():
        assert fit['profile_id']==cid
        text=repr(fit)
        assert 'REL_' not in text and 'POSITIVE_TRUTH' not in text and 'NEGATIVE_TRUTH' not in text
        assert 'expected_status' not in fit and 'controller_truth' not in fit
    assert all(v is False for v in r.authority.values())


def test_missing_mandatory_capability_is_incomplete_and_cannot_launch_partial_fit():
    pkg=_package(missing={'REL_MULTI_ISLAND_POSITIVE'})
    r=A.build_relational_qualification_adapter(pkg,_payloads(pkg))
    assert r.status=='INCOMPLETE'
    assert r.missing_capabilities==('REL_MULTI_ISLAND_POSITIVE',)
    assert r.fit_inputs=={}
    assert r.controller_challenges=={}


def test_fit_hash_drift_or_extra_mutable_generation_fields_fail_closed():
    pkg=_package(); payloads=_payloads(pkg); first=next(iter(payloads))
    payloads[first]['authenticated_fit_view_sha256']='f'*64
    with pytest.raises(A.RelationalAdapterError,match='fit-view SHA-256 mismatch'):
        A.build_relational_qualification_adapter(pkg,payloads)
    payloads=_payloads(pkg); payloads[first]['generate_on_demand']=True
    with pytest.raises(A.RelationalAdapterError,match='exactly authenticated_fit_view_sha256 and executor_input'):
        A.build_relational_qualification_adapter(pkg,payloads)


def test_executor_input_rejects_controller_or_semantic_fields():
    pkg=_package(); payloads=_payloads(pkg); first=next(iter(payloads))
    payloads[first]['executor_input']['expected_status']='PASS'
    with pytest.raises(A.RelationalAdapterError,match='executor_input fields'):
        A.build_relational_qualification_adapter(pkg,payloads)
    payloads=_payloads(pkg); payloads[first]['executor_input']['R']=np.array([1,0,0])
    with pytest.raises(A.RelationalAdapterError,match='executor_input fields'):
        A.build_relational_qualification_adapter(pkg,payloads)


def test_adapter_has_no_generator_dependency():
    src=inspect.getsource(A)
    forbidden=('generate_world','v79_rare_biology_generator','full_transcriptome_synthetic','synthetic generator')
    assert not any(token in src for token in forbidden)
