import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_contract_v2 as c2
import td_target_tournament_gate_registry_v2 as gr2
import td_target_tournament_prefreeze_v2 as p2

CONTRACT_PATH = ROOT / 'custody' / 'takeover_20261011' / 'TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V2.json'


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))


def registry():
    records=[]
    for cid in c2.CANDIDATES:
        for gate in c2.CANDIDATE_GATE_SETS[cid]:
            role=f'{cid}|{gate}'
            records.append({
                'candidate_id': cid,
                'gate_id': gate,
                'qualified_gate_executor_sha256': sha(f'executor|{role}'),
                'estimand_sha256': sha(f'estimand|{role}'),
                'decision_rule_sha256': sha(f'rule|{role}'),
            })
    return {
        'schema': gr2.REGISTRY_SCHEMA,
        'fixture_only': True,
        'records': records,
        'authority': {key: False for key in gr2.AUTHORITY_KEYS},
    }


def context_for(reg):
    hashes=gr2.registry_projection_hashes(reg, contract())
    return {
        'schema': p2.EXECUTION_CONTEXT_SCHEMA,
        'fixture_only': True,
        'executor_code_identity_sha256': sha('code'),
        'gate_executor_registry_sha256': hashes['gate_executor_registry_sha256'],
        'gate_estimand_registry_sha256': hashes['gate_estimand_registry_sha256'],
        'gate_decision_rule_registry_sha256': hashes['gate_decision_rule_registry_sha256'],
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


def test_registry_requires_exact_candidate_gate_coverage_and_produces_three_projection_hashes():
    reg=registry(); hashes=gr2.registry_projection_hashes(reg, contract())
    assert set(hashes) == {
        'gate_executor_registry_sha256',
        'gate_estimand_registry_sha256',
        'gate_decision_rule_registry_sha256',
    }
    assert all(len(value)==64 for value in hashes.values())


def test_registry_rejects_missing_extra_duplicate_or_shadow_records():
    reg=registry(); reg['records']=reg['records'][:-1]
    with pytest.raises(gr2.GateRegistryV2Error):
        gr2.validate_gate_registry_v2(reg, contract())
    reg=registry(); reg['records'].append(dict(reg['records'][0]))
    with pytest.raises(gr2.GateRegistryV2Error):
        gr2.validate_gate_registry_v2(reg, contract())
    reg=registry(); reg['winner']='C4'
    with pytest.raises(gr2.GateRegistryV2Error):
        gr2.validate_gate_registry_v2(reg, contract())


def test_registry_rejects_true_authority():
    reg=registry(); reg['authority']['target_selection_authorized']=True
    with pytest.raises(gr2.GateRegistryV2Error):
        gr2.validate_gate_registry_v2(reg, contract())


def test_registry_binding_rejects_posthoc_registry_substitution_against_frozen_context():
    reg=registry(); ctx=context_for(reg)
    gr2.bind_registry_to_execution_context(reg, contract(), ctx)
    altered=registry(); altered['records'][0]['decision_rule_sha256']=sha('posthoc-rule')
    with pytest.raises(gr2.GateRegistryV2Error):
        gr2.bind_registry_to_execution_context(altered, contract(), ctx)


def test_registry_binding_returns_exact_per_gate_values_for_candidate():
    reg=registry(); ctx=context_for(reg)
    bindings=gr2.bind_registry_to_execution_context(reg, contract(), ctx)
    gate='Q1_Q_SCALAR_STUDENT_ABSENT'
    row=bindings['C3_QUERY_MEASURED'][gate]
    assert row['qualified_gate_executor_sha256'] == sha(f'executor|C3_QUERY_MEASURED|{gate}')
    assert row['estimand_sha256'] == sha(f'estimand|C3_QUERY_MEASURED|{gate}')
    assert row['decision_rule_sha256'] == sha(f'rule|C3_QUERY_MEASURED|{gate}')


def test_context_registry_hashes_are_context_sensitive():
    reg=registry(); ctx=context_for(reg)
    base=p2.canonical_execution_context_sha256(ctx)
    altered=registry(); altered['records'][0]['estimand_sha256']=sha('different-estimand')
    altered_ctx=context_for(altered)
    assert p2.canonical_execution_context_sha256(altered_ctx) != base
