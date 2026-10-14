from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))

import td_test_qualification_package_v1 as P
import td_relational_successor_gate_v1 as G
import td_relational_successor_synthetic_adapter_v1 as A
import td_relational_successor_qualification_runner_v1 as Q

ROLES=(
    'DONOR_MATCHED_COMMON','DEPTH_DETECTED_SUM_MATCHED','SOURCE_OPERATOR_MATCHED','WRONG_CELL','PSEUDO_RARE_TECHNICAL'
)


def _scale(label,status,obs=.72,null=.55):
    a,b=map(int,label.split('/'))
    if status=='NOT_ESTIMABLE': obs=null=None
    return G.ScaleResult(label,a,b,status,status,obs,null,5,{}, {}, tuple([.5]*64),64,tuple(f'D{i}' for i in range(5)))


def _profile(pid,kind):
    statuses={label:'FAIL' for label in G.SCALE_LABELS}
    if kind=='broad': statuses['1/2']='PASS'
    elif kind=='fine': statuses['1/4']='PASS'
    elif kind=='rare': statuses['1/4']='PASS'
    elif kind=='stress': statuses['1/2']='PASS'
    elif kind=='under': statuses={label:'NOT_ESTIMABLE' for label in G.SCALE_LABELS}
    results={label:_scale(label,statuses[label],.78 if kind=='rare' and statuses[label]=='PASS' else .72,.55) for label in G.SCALE_LABELS}
    return G.RelationalProfileReceipt('S','P0',pid,results,tuple(),20,'SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY',{k:False for k in ('target_selection_authorized','td60_authorized','stage4_authorized','training_authorized')})


def _control(pid,high=False):
    results={label:_scale(label,'PASS' if label=='1/4' else 'FAIL',.82 if high and label=='1/4' else (.60 if label=='1/4' else .50),.55) for label in G.SCALE_LABELS}
    return G.RelationalProfileReceipt('S','P0',pid,results,tuple(),20,'SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY',{k:False for k in ('target_selection_authorized','td60_authorized','stage4_authorized','training_authorized')})


def _semantic(cap):
    if cap=='REL_SOURCE_VISIBILITY_STRESS': return 'STRESS_TRUTH'
    if cap in {'REL_TECHNICAL_TWIN_NEGATIVE','REL_NULL_NEGATIVE'}: return 'NEGATIVE_TRUTH'
    if cap=='REL_UNDERPOWERED_POSITIVE': return 'UNDERIDENTIFIED_TRUTH'
    return 'POSITIVE_TRUTH'


def _fixture(*,bad_under=False,high_tech=False,drop_role=None):
    caps={}; fit_views={}; profiles={}; controls={}; claims={}
    for i,cap in enumerate(A.MANDATORY_RELATIONAL_CAPABILITIES):
        cid=f'opaque-{i:02d}'
        caps[cap]={'capability_id':cap,'challenge_id':cid,'semantic_class':_semantic(cap)}
        fit_views[cid]=f'{i+1:064x}'[-64:]
        if cap=='REL_BROAD_MESO_POSITIVE': kind='broad'
        elif cap=='REL_FINE_RECURRENT_POSITIVE': kind='fine'
        elif cap in {'REL_RARE_LOCAL_ISLAND_POSITIVE','REL_MULTI_ISLAND_POSITIVE','REL_DONOR_RESTRICTED_POSITIVE'}: kind='rare'
        elif cap=='REL_SOURCE_VISIBILITY_STRESS': kind='stress'
        elif cap=='REL_UNDERPOWERED_POSITIVE': kind='null' if bad_under else 'under'
        else: kind='null'
        profiles[cid]=_profile(cid,kind)
        role_map={}
        controls[cid]={}
        if cap in Q.RARE_CONTROL_CAPABILITIES:
            for r,role in enumerate(ROLES):
                control_id=f'c{i}-{r}'
                controls[cid][control_id]=_control(control_id,high=(high_tech and cap=='REL_TECHNICAL_TWIN_NEGATIVE'))
                if role!=drop_role: role_map[role]=[control_id]
        claims[cap]={'challenge_id':cid,'control_roles':role_map,'expected_status':'PASS' if cap=='REL_SOURCE_VISIBILITY_STRESS' else None}
    manifest={
        'schema':Q.CONTROLLER_SCHEMA,
        'package_sha256':'a'*64,
        'claims':claims,
        'authority':{k:False for k in Q.CONTROLLER_AUTHORITY_KEYS},
    }
    controller_sha=Q.canonical_sha256(manifest)
    package=P.ValidatedExternalPackage('pkg','a'*64,fit_views,controller_sha,caps)
    fit=Q.BlindedFitReceipt(package_id='pkg',package_sha256='a'*64,profiles=profiles,controls=controls,authority={k:False for k in Q.RUN_AUTHORITY_KEYS})
    binding={
        'qualified_gate_executor_sha256':'1'*64,
        'estimand_sha256':'2'*64,
        'decision_rule_sha256':'3'*64,
        'failure_scope':'TEST_QUALIFICATION_ONLY',
        'required_capabilities':list(A.MANDATORY_RELATIONAL_CAPABILITIES),
    }
    return package,fit,manifest,binding


def test_complete_controller_adjudication_qualifies_correct_behavior():
    package,fit,manifest,binding=_fixture(high_tech=True)
    receipt=Q.adjudicate_blinded_qualification(package=package,fit_receipt=fit,controller_manifest=manifest,gate_binding=binding)
    assert receipt.status=='QUALIFIED'
    assert receipt.gate_qualification is not None
    assert receipt.capability_statuses['REL_BROAD_MESO_POSITIVE']=='PASS'
    assert receipt.capability_statuses['REL_FINE_RECURRENT_POSITIVE']=='PASS'
    assert receipt.capability_statuses['REL_TECHNICAL_TWIN_NEGATIVE']=='FAIL'
    assert receipt.capability_statuses['REL_NULL_NEGATIVE']=='FAIL'
    assert receipt.capability_statuses['REL_UNDERPOWERED_POSITIVE']=='NOT_ESTIMABLE'
    assert all(v is False for v in receipt.authority.values())


def test_underpowered_truth_called_fail_is_not_qualified():
    package,fit,manifest,binding=_fixture(bad_under=True,high_tech=True)
    receipt=Q.adjudicate_blinded_qualification(package=package,fit_receipt=fit,controller_manifest=manifest,gate_binding=binding)
    assert receipt.status=='NOT_QUALIFIED'


def test_missing_any_required_rare_control_role_is_incomplete_not_silently_dropped():
    package,fit,manifest,binding=_fixture(high_tech=True,drop_role='WRONG_CELL')
    receipt=Q.adjudicate_blinded_qualification(package=package,fit_receipt=fit,controller_manifest=manifest,gate_binding=binding)
    assert receipt.status=='INCOMPLETE'
    assert any('WRONG_CELL' in item for item in receipt.missing_requirements)
    assert receipt.gate_qualification is None


def test_controller_manifest_hash_and_package_binding_fail_closed():
    package,fit,manifest,binding=_fixture(high_tech=True)
    manifest=dict(manifest); manifest['package_sha256']='f'*64
    try:
        Q.adjudicate_blinded_qualification(package=package,fit_receipt=fit,controller_manifest=manifest,gate_binding=binding)
    except Q.QualificationRunnerError as exc:
        assert 'package' in str(exc).lower() or 'controller' in str(exc).lower()
    else:
        raise AssertionError('controller/package mismatch must fail closed')


def test_gate_binding_requires_exact_nine_capabilities():
    package,fit,manifest,binding=_fixture(high_tech=True)
    binding=dict(binding); binding['required_capabilities']=binding['required_capabilities'][:-1]
    try:
        Q.adjudicate_blinded_qualification(package=package,fit_receipt=fit,controller_manifest=manifest,gate_binding=binding)
    except Q.QualificationRunnerError as exc:
        assert 'capabilit' in str(exc).lower()
    else:
        raise AssertionError('partial gate binding must fail closed')
