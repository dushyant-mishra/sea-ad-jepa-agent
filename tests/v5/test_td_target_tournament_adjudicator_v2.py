import hashlib
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_contract_v2 as c2
import td_target_tournament_adjudicator_v2 as a2

CONTRACT_PATH = ROOT / 'custody' / 'takeover_20261011' / 'TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V2.json'
PREFREEZE_SHA = 'a' * 64


def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))


def manifest(cid, *, status='PASS', prefreeze_sha=PREFREEZE_SHA):
    gates = contract()['candidate_gate_sets'][cid]
    out = {
        'schema': a2.EVIDENCE_SCHEMA,
        'fixture_only': True,
        'candidate_id': cid,
        'prefreeze_manifest_sha256': prefreeze_sha,
        'gates': {
            gate: {
                'status': status,
                'evidence_schema': a2.expected_evidence_schema(gate),
                'evidence_sha256': hashlib.sha256(f'{cid}|{gate}'.encode()).hexdigest(),
            }
            for gate in gates
        },
        'authority': {key: False for key in a2.AUTHORITY_KEYS},
    }
    return out


def receipt(cid, *, gate_status='PASS', declared_status=None, prefreeze_sha=PREFREEZE_SHA):
    mf = manifest(cid, status=gate_status, prefreeze_sha=prefreeze_sha)
    if declared_status is None:
        declared_status = gate_status
    return mf, {
        'schema': a2.RECEIPT_SCHEMA,
        'fixture_only': True,
        'candidate_id': cid,
        'status': declared_status,
        'aggregate_score': 0.0,
        'prefreeze_manifest_sha256': prefreeze_sha,
        'evidence_manifest_sha256': a2.canonical_sha256(mf),
        'gates': {gate: gate_status == 'PASS' for gate in contract()['candidate_gate_sets'][cid]},
        'authority': {key: False for key in a2.AUTHORITY_KEYS},
    }


def adjudicate(rows):
    receipts=[]; manifests={}
    for cid, gate_status, declared_status in rows:
        mf, rec = receipt(cid, gate_status=gate_status, declared_status=declared_status)
        receipts.append(rec); manifests[cid]=mf
    return a2.adjudicate(
        contract(), receipts, manifests,
        expected_prefreeze_manifest_sha256=PREFREEZE_SHA,
    )


def test_v2_all_foundation_pass_become_individually_eligible_without_selecting_winner():
    rows=[(cid,'PASS','PASS') for cid in c2.FOUNDATION]
    out=adjudicate(rows)
    assert out['tournament_complete'] is True
    assert out['foundation_eligible'] == c2.FOUNDATION
    assert out['terminal'] == 'CANDIDATES_ELIGIBLE_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY'
    assert out['target_selected'] is False
    assert out['training_authorized'] is False


def test_missing_foundation_candidate_is_incomplete_not_redesign():
    rows=[(cid,'FAIL','FAIL') for cid in c2.FOUNDATION[:-1]]
    out=adjudicate(rows)
    assert out['tournament_complete'] is False
    assert out['missing_foundation_candidates'] == [c2.FOUNDATION[-1]]
    assert out['terminal'] == 'TOURNAMENT_INCOMPLETE__FOUNDATION_CANDIDATES_MISSING__NO_TARGET_AUTHORITY'


def test_not_estimable_is_distinct_from_fail_and_blocks_eligibility():
    rows=[]
    for cid in c2.FOUNDATION:
        status='NOT_ESTIMABLE' if cid=='C3_QUERY_MEASURED' else 'FAIL'
        rows.append((cid,status,status))
    out=adjudicate(rows)
    assert out['terminal'] == 'NO_TARGET_WINNER__FOUNDATION_EVIDENCE_NOT_ESTIMABLE__NO_TARGET_AUTHORITY'
    rec=out['rejected']['C3_QUERY_MEASURED']
    assert rec['failed_gates'] == []
    assert rec['not_estimable_gates'] == contract()['candidate_gate_sets']['C3_QUERY_MEASURED']


def test_declared_candidate_status_must_equal_gate_derived_status():
    mf, rec=receipt('C1_SHARED_EMERGENT', gate_status='FAIL', declared_status='PASS')
    with pytest.raises(a2.AdjudicationV2Error):
        a2.validate_candidate_receipt(
            rec, contract(), mf,
            expected_prefreeze_manifest_sha256=PREFREEZE_SHA,
        )


def test_external_prefreeze_pin_rejects_self_consistent_rewrite():
    altered='b'*64
    mf, rec=receipt('C1_SHARED_EMERGENT', prefreeze_sha=altered)
    with pytest.raises(a2.AdjudicationV2Error):
        a2.validate_candidate_receipt(
            rec, contract(), mf,
            expected_prefreeze_manifest_sha256=PREFREEZE_SHA,
        )


def test_evidence_manifest_rejects_shadow_claim_field():
    mf=manifest('C1_SHARED_EMERGENT'); mf['target_selected']=True
    with pytest.raises(a2.AdjudicationV2Error):
        a2.validate_evidence_manifest(
            mf, contract(),
            expected_prefreeze_manifest_sha256=PREFREEZE_SHA,
        )


def test_c4_cannot_rescue_failed_c2_even_when_c4_local_evidence_all_passes():
    rows=[]
    for cid in c2.FOUNDATION:
        status='FAIL' if cid=='C2_RELATIONAL_SHARED' else 'PASS'
        rows.append((cid,status,status))
    out=adjudicate(rows)
    assert 'C4_STRUCTURED_COMPOSITE' not in out['foundation_eligible']
    assert out['rejected']['C4_STRUCTURED_COMPOSITE']['blocked_by_constituents'] == ['C2_RELATIONAL_SHARED']


def test_c4_cannot_rescue_not_estimable_c3():
    rows=[]
    for cid in c2.FOUNDATION:
        status='NOT_ESTIMABLE' if cid=='C3_QUERY_MEASURED' else 'PASS'
        rows.append((cid,status,status))
    out=adjudicate(rows)
    assert 'C4_STRUCTURED_COMPOSITE' not in out['foundation_eligible']
    assert out['rejected']['C4_STRUCTURED_COMPOSITE']['blocked_by_constituents'] == ['C3_QUERY_MEASURED']


def test_specialist_never_changes_foundation_terminal():
    rows=[(cid,'FAIL','FAIL') for cid in c2.FOUNDATION]
    rows.append(('C5_REGULATORY_SPECIALIST','PASS','PASS'))
    out=adjudicate(rows)
    assert out['optional_specialists_eligible'] == ['C5_REGULATORY_SPECIALIST']
    assert out['terminal'] == 'NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION'


def test_receipt_score_and_envelope_are_fail_closed():
    mf, rec=receipt('C1_SHARED_EMERGENT')
    rec['aggregate_score']='0.0'
    with pytest.raises(a2.AdjudicationV2Error):
        a2.validate_candidate_receipt(rec, contract(), mf, expected_prefreeze_manifest_sha256=PREFREEZE_SHA)
    mf, rec=receipt('C1_SHARED_EMERGENT')
    rec['winner']=True
    with pytest.raises(a2.AdjudicationV2Error):
        a2.validate_candidate_receipt(rec, contract(), mf, expected_prefreeze_manifest_sha256=PREFREEZE_SHA)
