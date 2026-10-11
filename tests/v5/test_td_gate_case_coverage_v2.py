import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_gate_case_coverage_v2 as g2
import td_target_tournament_contract_v2 as c2
import td_target_tournament_prefreeze_v2 as p2

CONTRACT_PATH = ROOT / 'custody' / 'takeover_20261011' / 'TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V2.json'


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))


def execution_context():
    return {
        'schema': p2.EXECUTION_CONTEXT_SCHEMA,
        'fixture_only': True,
        'executor_code_identity_sha256': sha('code'),
        'population_registry_sha256': sha('population'),
        'donor_registry_sha256': sha('donors'),
        'source_registry_sha256': sha('sources'),
        'operator_registry_sha256': sha('operators'),
        'support_registry_sha256': sha('support'),
        'teacher_student_evidence_rights_sha256': sha('rights'),
        'split_registry_sha256': sha('splits'),
        'observation_descriptor_sha256': sha('observation'),
        'corrected_replay_evidence_sha256': sha('corrected'),
    }


def cases():
    return [
        {
            'case_id': 'c1',
            'candidate_id': 'C2_RELATIONAL_SHARED',
            'gate_id': 'R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            'source': 'HVS',
            'analysis_tier': 'PRIMARY',
            'endpoint_id': 'relational',
            'available_donors_upper_bound': 12,
        },
        {
            'case_id': 'c2',
            'candidate_id': 'C2_RELATIONAL_SHARED',
            'gate_id': 'R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            'source': 'SEA_AD',
            'analysis_tier': 'PRIMARY',
            'endpoint_id': 'relational',
            'available_donors_upper_bound': 20,
        },
    ]


def manifest():
    con = contract(); ctx = execution_context(); dcases = cases()
    cfg = {
        'schema': p2.CONFIG_SCHEMA,
        'fixture_only': True,
        'family_alpha': 0.05,
        'multiplicity_method': 'BONFERRONI',
        'tournament_contract': con,
        'tournament_contract_sha256': p2.canonical_tournament_contract_sha256(con),
        'execution_context': ctx,
        'execution_context_sha256': p2.canonical_execution_context_sha256(ctx),
        'null_seed_material': 'v2-coverage-seed',
        'decision_cases': dcases,
        'decision_family_registry_sha256': p2.canonical_decision_family_sha256(dcases),
        'authority': {key: False for key in p2.AUTHORITY_KEYS},
    }
    return p2.build_prefreeze_manifest(cfg)


def receipts():
    return [
        {
            'case_id': 'c1',
            'candidate_id': 'C2_RELATIONAL_SHARED',
            'gate_id': 'R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            'source': 'HVS',
            'analysis_tier': 'PRIMARY',
            'endpoint_id': 'relational',
            'status': 'PASS',
            'evidence_sha256': sha('e1'),
        },
        {
            'case_id': 'c2',
            'candidate_id': 'C2_RELATIONAL_SHARED',
            'gate_id': 'R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            'source': 'SEA_AD',
            'analysis_tier': 'PRIMARY',
            'endpoint_id': 'relational',
            'status': 'NOT_ESTIMABLE',
            'evidence_sha256': sha('e2'),
        },
    ]


def test_v2_coverage_binds_external_prefreeze_and_execution_context():
    pf = manifest()
    out = g2.audit_gate_case_coverage_v2(
        pf,
        expected_prefreeze_manifest_sha256=pf['manifest_sha256'],
        candidate_id='C2_RELATIONAL_SHARED',
        gate_id='R1_SCALE_FREE_RELATIONAL_RECURRENCE',
        case_receipts=receipts(),
    )
    assert out['schema'] == g2.COVERAGE_SCHEMA
    assert out['prefreeze_manifest_sha256'] == pf['manifest_sha256']
    assert out['execution_context_sha256'] == pf['execution_context_sha256']
    assert out['coverage_complete'] is True
    assert out['status_counts'] == {'PASS': 1, 'FAIL': 0, 'NOT_ESTIMABLE': 1}
    assert out['gate_status_not_adjudicated'] is True


def test_v2_coverage_rejects_wrong_external_prefreeze_pin():
    pf = manifest()
    with pytest.raises(g2.CoverageV2Error):
        g2.audit_gate_case_coverage_v2(
            pf,
            expected_prefreeze_manifest_sha256=sha('wrong'),
            candidate_id='C2_RELATIONAL_SHARED',
            gate_id='R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            case_receipts=receipts(),
        )


def test_v2_coverage_rejects_missing_or_extra_case_receipts():
    pf = manifest()
    with pytest.raises(g2.CoverageV2Error):
        g2.audit_gate_case_coverage_v2(
            pf, expected_prefreeze_manifest_sha256=pf['manifest_sha256'],
            candidate_id='C2_RELATIONAL_SHARED', gate_id='R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            case_receipts=receipts()[:1],
        )
    extra = receipts() + [dict(receipts()[0], case_id='extra')]
    with pytest.raises(g2.CoverageV2Error):
        g2.audit_gate_case_coverage_v2(
            pf, expected_prefreeze_manifest_sha256=pf['manifest_sha256'],
            candidate_id='C2_RELATIONAL_SHARED', gate_id='R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            case_receipts=extra,
        )


def test_v2_coverage_preserves_not_estimable_and_does_not_adjudicate_gate():
    pf = manifest(); recs = receipts()
    out = g2.audit_gate_case_coverage_v2(
        pf, expected_prefreeze_manifest_sha256=pf['manifest_sha256'],
        candidate_id='C2_RELATIONAL_SHARED', gate_id='R1_SCALE_FREE_RELATIONAL_RECURRENCE',
        case_receipts=recs,
    )
    assert out['status_counts']['NOT_ESTIMABLE'] == 1
    assert 'status' not in out
    assert out['gate_status_not_adjudicated'] is True


def test_v2_coverage_rejects_case_role_mismatch_even_with_same_case_id():
    pf = manifest(); recs = receipts(); recs[0]['source'] = 'NPH52'
    with pytest.raises(g2.CoverageV2Error):
        g2.audit_gate_case_coverage_v2(
            pf, expected_prefreeze_manifest_sha256=pf['manifest_sha256'],
            candidate_id='C2_RELATIONAL_SHARED', gate_id='R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            case_receipts=recs,
        )


def test_v2_coverage_rejects_v1_manifest():
    pf = manifest(); pf['schema'] = 'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_MANIFEST_V1'
    core = dict(pf); core.pop('manifest_sha256')
    pf['manifest_sha256'] = p2.canonical_json_sha256(core)
    with pytest.raises(g2.CoverageV2Error):
        g2.audit_gate_case_coverage_v2(
            pf, expected_prefreeze_manifest_sha256=pf['manifest_sha256'],
            candidate_id='C2_RELATIONAL_SHARED', gate_id='R1_SCALE_FREE_RELATIONAL_RECURRENCE',
            case_receipts=receipts(),
        )
