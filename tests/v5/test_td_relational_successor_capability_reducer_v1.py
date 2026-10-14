from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))

import td_relational_successor_gate_v1 as G
import td_relational_successor_capability_reducer_v1 as R


def _scale(label,status):
    a,b=map(int,label.split('/'))
    return G.ScaleResult(label,a,b,status,status,0.7 if status!='NOT_ESTIMABLE' else None,0.55 if status!='NOT_ESTIMABLE' else None,5,{}, {}, tuple([0.5]*64),64,tuple(f'D{i}' for i in range(5)))


def _profile(statuses):
    return G.RelationalProfileReceipt('S','P0','opaque',{label:_scale(label,statuses.get(label,'FAIL')) for label in G.SCALE_LABELS},tuple(),10,'SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY',{k:False for k in ('target_selection_authorized','td60_authorized','stage4_authorized','training_authorized')})


def _rare(statuses):
    out={}
    for label in G.SCALE_LABELS:
        status=statuses.get(label,'FAIL')
        out[label]=G.RareIncrementScaleResult(label,status,status,0.1 if status!='NOT_ESTIMABLE' else None,0.0 if status!='NOT_ESTIMABLE' else None)
    return G.RareIncrementReceipt('S','P0','opaque',out,'RARE_RELATIONAL_INCREMENT_ONLY',{k:False for k in ('target_selection_authorized','td60_authorized','stage4_authorized','training_authorized')})


def test_broad_mesoscale_is_exactly_half_scale_not_any_scale():
    p=_profile({'1/3':'PASS','1/2':'FAIL'})
    assert R.reduce_capability_status('REL_BROAD_MESO_POSITIVE',p)=='FAIL'
    p=_profile({'1/2':'PASS'})
    assert R.reduce_capability_status('REL_BROAD_MESO_POSITIVE',p)=='PASS'


def test_fine_positive_uses_family_corrected_fine_scales_without_requiring_all_to_pass():
    p=_profile({'1/8':'NOT_ESTIMABLE','1/6':'FAIL','1/4':'PASS','1/3':'FAIL','1/2':'PASS'})
    assert R.reduce_capability_status('REL_FINE_RECURRENT_POSITIVE',p)=='PASS'
    p=_profile({'1/8':'NOT_ESTIMABLE','1/6':'NOT_ESTIMABLE','1/4':'NOT_ESTIMABLE','1/3':'NOT_ESTIMABLE'})
    assert R.reduce_capability_status('REL_FINE_RECURRENT_POSITIVE',p)=='NOT_ESTIMABLE'


def test_rare_capabilities_and_technical_twin_are_decided_by_rare_increment_not_raw_profile():
    raw=_profile({'1/4':'PASS','1/3':'PASS'})
    rare=_rare({'1/4':'FAIL','1/3':'FAIL'})
    for cap in ('REL_RARE_LOCAL_ISLAND_POSITIVE','REL_MULTI_ISLAND_POSITIVE','REL_DONOR_RESTRICTED_POSITIVE','REL_TECHNICAL_TWIN_NEGATIVE'):
        assert R.reduce_capability_status(cap,raw,rare_increment=rare)=='FAIL'
    rare=_rare({'1/4':'PASS'})
    assert R.reduce_capability_status('REL_RARE_LOCAL_ISLAND_POSITIVE',raw,rare_increment=rare)=='PASS'


def test_null_and_underpowered_reduce_without_manufacturing_a_positive():
    assert R.reduce_capability_status('REL_NULL_NEGATIVE',_profile({'1/2':'FAIL'}))=='FAIL'
    assert R.reduce_capability_status('REL_NULL_NEGATIVE',_profile({'1/3':'PASS'}))=='PASS'
    all_ne={label:'NOT_ESTIMABLE' for label in G.SCALE_LABELS}
    assert R.reduce_capability_status('REL_UNDERPOWERED_POSITIVE',_profile(all_ne))=='NOT_ESTIMABLE'
    assert R.reduce_capability_status('REL_NULL_NEGATIVE',_profile(all_ne))=='NOT_ESTIMABLE'


def test_source_visibility_stress_uses_any_supported_relation_but_expected_status_stays_controller_side():
    assert R.reduce_capability_status('REL_SOURCE_VISIBILITY_STRESS',_profile({'1/2':'PASS'}))=='PASS'
    all_ne={label:'NOT_ESTIMABLE' for label in G.SCALE_LABELS}
    assert R.reduce_capability_status('REL_SOURCE_VISIBILITY_STRESS',_profile(all_ne))=='NOT_ESTIMABLE'
