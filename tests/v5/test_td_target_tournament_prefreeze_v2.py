import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

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
        'gate_executor_registry_sha256': sha('gate-executors'),
        'gate_estimand_registry_sha256': sha('gate-estimands'),
        'gate_decision_rule_registry_sha256': sha('gate-decision-rules'),
        'population_registry_sha256': sha('population'),
        'donor_registry_sha256': sha('donors'),
        'source_registry_sha256': sha('sources'),
        'operator_registry_sha256': sha('operators'),
        'support_registry_sha256': sha('support'),
        'teacher_student_evidence_rights_sha256': sha('rights'),
        'split_registry_sha256': sha('splits'),
        'observation_descriptor_sha256': sha('observation'),
        'corrected_replay_evidence_sha256': sha('corrected-replay'),
    }


def decision_cases():
    return [
        {
            'case_id': 'C1_G1_HVS_primary',
            'candidate_id': 'C1_SHARED_EMERGENT',
            'gate_id': 'G1_INTEGRITY_LINEAGE',
            'source': 'HVS',
            'analysis_tier': 'PRIMARY',
            'endpoint_id': 'integrity',
            'available_donors_upper_bound': 12,
        },
        {
            'case_id': 'C3_Q1_SEA_primary',
            'candidate_id': 'C3_QUERY_MEASURED',
            'gate_id': 'Q1_Q_SCALAR_STUDENT_ABSENT',
            'source': 'SEA_AD',
            'analysis_tier': 'PRIMARY',
            'endpoint_id': 'q_scalar_absent',
            'available_donors_upper_bound': 20,
        },
    ]


def config():
    con = contract()
    ctx = execution_context()
    cases = decision_cases()
    return {
        'schema': p2.CONFIG_SCHEMA,
        'fixture_only': True,
        'family_alpha': 0.05,
        'multiplicity_method': 'BONFERRONI',
        'tournament_contract': con,
        'tournament_contract_sha256': p2.canonical_tournament_contract_sha256(con),
        'execution_context': ctx,
        'execution_context_sha256': p2.canonical_execution_context_sha256(ctx),
        'null_seed_material': 'td-v2-test-seed',
        'decision_cases': cases,
        'decision_family_registry_sha256': p2.canonical_decision_family_sha256(cases),
        'authority': {key: False for key in p2.AUTHORITY_KEYS},
    }


def test_v2_prefreeze_binds_exact_v2_contract_and_execution_context():
    out = p2.build_prefreeze_manifest(config())
    assert out['schema'] == p2.MANIFEST_SCHEMA
    assert out['fixture_only'] is True
    assert out['tournament_contract_sha256'] == config()['tournament_contract_sha256']
    assert out['execution_context_sha256'] == config()['execution_context_sha256']
    assert out['decision_family_size'] == 2
    assert out['authority'] == {key: False for key in p2.AUTHORITY_KEYS}
    assert all(row['biological_result'] == 'NOT_OPENED' for row in out['case_resolution'])


def test_v2_prefreeze_rejects_v1_contract():
    cfg = config()
    cfg['tournament_contract'] = {'schema': 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1'}
    cfg['tournament_contract_sha256'] = sha('fake-v1')
    with pytest.raises(p2.PrefreezeV2Error):
        p2.build_prefreeze_manifest(cfg)


def test_execution_context_is_exact_and_shadow_claims_fail_closed():
    cfg = config()
    cfg['execution_context']['winner'] = 'C4'
    cfg['execution_context_sha256'] = p2.canonical_json_sha256(cfg['execution_context'])
    with pytest.raises(p2.PrefreezeV2Error):
        p2.build_prefreeze_manifest(cfg)


def test_execution_context_hash_cannot_be_self_consistently_rewritten_without_config_pin_update():
    cfg = config()
    cfg['execution_context']['support_registry_sha256'] = sha('different-support')
    with pytest.raises(p2.PrefreezeV2Error):
        p2.build_prefreeze_manifest(cfg)


def test_execution_context_freezes_gate_executor_estimand_and_decision_rule_registries():
    ctx = execution_context()
    assert ctx['gate_executor_registry_sha256'] == sha('gate-executors')
    assert ctx['gate_estimand_registry_sha256'] == sha('gate-estimands')
    assert ctx['gate_decision_rule_registry_sha256'] == sha('gate-decision-rules')
    cfg = config()
    cfg['execution_context']['gate_decision_rule_registry_sha256'] = 'not-a-sha'
    with pytest.raises(p2.PrefreezeV2Error):
        p2.build_prefreeze_manifest(cfg)


def test_v2_case_gate_must_be_allowed_for_exact_candidate():
    cfg = config()
    cfg['decision_cases'][1]['gate_id'] = 'G9_LEARNED_TEACHER_CONTINUITY'
    cfg['decision_family_registry_sha256'] = p2.canonical_decision_family_sha256(cfg['decision_cases'])
    with pytest.raises(p2.PrefreezeV2Error):
        p2.build_prefreeze_manifest(cfg)


def test_v2_prefreeze_rejects_true_authority():
    cfg = config()
    cfg['authority']['real_tournament_authorized'] = True
    with pytest.raises(p2.PrefreezeV2Error):
        p2.build_prefreeze_manifest(cfg)


def test_manifest_sha_is_deterministic_and_context_sensitive():
    out1 = p2.build_prefreeze_manifest(config())
    cfg2 = config()
    cfg2['execution_context']['operator_registry_sha256'] = sha('operators-v2')
    cfg2['execution_context_sha256'] = p2.canonical_execution_context_sha256(cfg2['execution_context'])
    out2 = p2.build_prefreeze_manifest(cfg2)
    assert out1['manifest_sha256'] != out2['manifest_sha256']
