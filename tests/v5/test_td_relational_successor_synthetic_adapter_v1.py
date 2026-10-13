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
    values=np.zeros((n,512),dtype=float)
    measured=np.ones((n,512),dtype=bool)
    base={
        'source':'UNIT','panel_id':'P0',
        'z_values':values.copy(),'x_values':values.copy(),'y_values':values.copy(),
        'z_measured':measured.copy(),'x_measured':measured.copy(),'y_measured':measured.copy(),
        'z_feature_ids':[f'Z{i:04d}' for i in range(512)],
        'x_feature_ids':[f'X{i:04d}' for i in range(512)],
        'y_feature_ids':[f'Y{i:04d}' for i in range(512)],
        'donor_ids':np.array(['D0','D0','D0'],dtype=object),
        'operator_ids':np.array(['O0','O0','O0'],dtype=object),
        'global_rows':np.arange(n),
        'source_library':np.full(n,1000.0),
        'detected_genes':np.full(n,512,dtype=int),
        'focal_mask':np.ones(n,bool),'neighbor_pool_mask':np.ones(n,bool),
        'min_focal_anchors_per_donor':1,
        'control_profiles':{},
    }
    return {cid:{'authenticated_fit_view_sha256':sha,'executor_input':dict(base)} for cid,sha in pkg.fit_views.items()}


def test_complete_adapter_keeps_fit_side_blind_and_controller_map_separate():
    pkg=_package(); payloads=_payloads(pkg); first=next(iter(payloads))
    n=3
    payloads[first]['executor_input']['control_profiles']={
        'opaque-control-a':{
            'focal_mask':np.array([1,0,1],dtype=bool),
            'neighbor_pool_mask':np.ones(n,dtype=bool),
            'min_focal_anchors_per_donor':1,
        }
    }
    r=A.build_relational_qualification_adapter(pkg,payloads)
    assert r.status=='READY'
    assert not r.missing_capabilities
    assert set(r.fit_inputs)==set(pkg.fit_views)
    assert set(r.controller_challenges)==set(pkg.fit_views)
    assert 'opaque-control-a' in r.fit_inputs[first]['control_profiles']
    for cid,fit in r.fit_inputs.items():
        assert fit['profile_id']==cid
        text=repr({k:v for k,v in fit.items() if k not in {'z_values','x_values','y_values','z_measured','x_measured','y_measured','control_profiles'}})
        assert 'REL_' not in text and 'POSITIVE_TRUTH' not in text and 'NEGATIVE_TRUTH' not in text
        assert 'expected_status' not in fit and 'controller_truth' not in fit
        assert 'z_distances' not in fit and 'null_y_identity_maps' not in fit
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


def test_executor_input_rejects_controller_semantics_precomputed_distances_and_upstream_nulls():
    pkg=_package(); payloads=_payloads(pkg); first=next(iter(payloads))
    for field,value in (
        ('expected_status','PASS'),
        ('R',np.array([1,0,0])),
        ('z_distances',np.zeros((3,3))),
        ('null_y_identity_maps',np.tile(np.arange(3),(64,1))),
    ):
        bad=_payloads(pkg)
        bad[first]['executor_input'][field]=value
        with pytest.raises(A.RelationalAdapterError,match='executor_input fields'):
            A.build_relational_qualification_adapter(pkg,bad)


def test_control_profiles_must_be_opaque_and_contain_only_masks_and_support_minimum():
    pkg=_package(); first=next(iter(pkg.fit_views))
    bad=_payloads(pkg)
    bad[first]['executor_input']['control_profiles']={'WRONG_CELL':{'focal_mask':np.ones(3,bool),'neighbor_pool_mask':np.ones(3,bool),'min_focal_anchors_per_donor':1}}
    with pytest.raises(A.RelationalAdapterError,match='opaque'):
        A.build_relational_qualification_adapter(pkg,bad)
    bad=_payloads(pkg)
    bad[first]['executor_input']['control_profiles']={'opaque-c':{'focal_mask':np.ones(3,bool),'neighbor_pool_mask':np.ones(3,bool),'min_focal_anchors_per_donor':1,'expected_status':'FAIL'}}
    with pytest.raises(A.RelationalAdapterError,match='control profile fields'):
        A.build_relational_qualification_adapter(pkg,bad)


def test_adapter_has_no_generator_dependency():
    src=inspect.getsource(A)
    forbidden=('generate_world','v79_rare_biology_generator','full_transcriptome_synthetic','synthetic generator')
    assert not any(token in src for token in forbidden)
