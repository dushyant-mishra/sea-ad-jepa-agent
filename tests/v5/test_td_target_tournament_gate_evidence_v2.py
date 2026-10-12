import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_adjudicator_v2 as a2
import td_target_tournament_contract_v2 as c2
import td_target_tournament_gate_evidence_v2 as ge2
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


def execution_context(reg=None):
    reg=registry() if reg is None else reg
    hashes=gr2.registry_projection_hashes(reg, contract())
    return {
        'schema': p2.EXECUTION_CONTEXT_SCHEMA,
        'fixture_only': True,
        'executor_code_identity_sha256': sha('code'),
        **hashes,
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


PREFREEZE = sha('prefreeze')
COVERAGE = sha('coverage')
EXECUTOR = sha('executor')
ESTIMAND = sha('estimand')
RULE = sha('decision-rule')
PAYLOAD = sha('payload')
CONTEXT = sha('context')


def artifact(
    gate='Q1_Q_SCALAR_STUDENT_ABSENT', status='PASS',
    executor=EXECUTOR, estimand=ESTIMAND, rule=RULE,
):
    return {
        'schema': a2.expected_evidence_schema(gate),
        'fixture_only': True,
        'candidate_id': 'C3_QUERY_MEASURED',
        'gate_id': gate,
        'prefreeze_manifest_sha256': PREFREEZE,
        'execution_context_sha256': CONTEXT,
        'coverage_audit_sha256': COVERAGE,
        'qualified_gate_executor_sha256': executor,
        'estimand_sha256': estimand,
        'decision_rule_sha256': rule,
        'status': status,
        'evidence_payload_sha256': PAYLOAD,
        'authority': {key: False for key in ge2.AUTHORITY_KEYS},
    }


def validate(
    art, *, gate='Q1_Q_SCALAR_STUDENT_ABSENT', coverage=COVERAGE,
    executor=EXECUTOR, estimand=ESTIMAND, rule=RULE,
):
    return ge2.validate_gate_evidence_artifact_v2(
        art,
        expected_candidate_id='C3_QUERY_MEASURED',
        expected_gate_id=gate,
        expected_prefreeze_manifest_sha256=PREFREEZE,
        expected_execution_context_sha256=CONTEXT,
        expected_coverage_audit_sha256=coverage,
        expected_qualified_gate_executor_sha256=executor,
        expected_estimand_sha256=estimand,
        expected_decision_rule_sha256=rule,
    )


def test_gate_evidence_binds_prefreeze_context_coverage_executor_estimand_rule_and_payload():
    art = artifact()
    assert validate(art) == ge2.canonical_sha256(art)


def test_gate_evidence_preserves_not_estimable():
    art = artifact(status='NOT_ESTIMABLE')
    validate(art)
    assert art['status'] == 'NOT_ESTIMABLE'


def test_gate_evidence_rejects_self_consistent_coverage_substitution():
    art = artifact(); art['coverage_audit_sha256'] = sha('other-coverage')
    with pytest.raises(ge2.GateEvidenceV2Error):
        validate(art)


def test_gate_evidence_rejects_posthoc_executor_estimand_or_decision_rule_substitution():
    with pytest.raises(ge2.GateEvidenceV2Error):
        validate(artifact(executor=sha('posthoc-executor')))
    with pytest.raises(ge2.GateEvidenceV2Error):
        validate(artifact(estimand=sha('posthoc-estimand')))
    with pytest.raises(ge2.GateEvidenceV2Error):
        validate(artifact(rule=sha('posthoc-rule')))


def test_gate_evidence_rejects_wrong_gate_specific_schema():
    art = artifact(); art['schema'] = a2.expected_evidence_schema('Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR')
    with pytest.raises(ge2.GateEvidenceV2Error):
        validate(art)


def test_gate_evidence_rejects_shadow_claim_and_true_authority():
    art = artifact(); art['winner'] = True
    with pytest.raises(ge2.GateEvidenceV2Error):
        validate(art)
    art = artifact(); art['authority']['target_selection_authorized'] = True
    with pytest.raises(ge2.GateEvidenceV2Error):
        validate(art)


def candidate_fixture():
    cid='C3_QUERY_MEASURED'
    con=contract()
    gate_ids=list(con['candidate_gate_sets'][cid])
    reg=registry(); ctx=execution_context(reg)
    bindings=gr2.bind_registry_to_execution_context(reg, con, ctx)[cid]
    context_sha=p2.canonical_execution_context_sha256(ctx)
    coverage={gate: sha(f'coverage-{gate}') for gate in gate_ids}
    artifacts={}
    for gate in gate_ids:
        row=bindings[gate]
        art=artifact(
            gate=gate,
            executor=row['qualified_gate_executor_sha256'],
            estimand=row['estimand_sha256'],
            rule=row['decision_rule_sha256'],
        )
        art['execution_context_sha256']=context_sha
        art['coverage_audit_sha256']=coverage[gate]
        artifacts[gate]=art
    return cid, gate_ids, reg, ctx, coverage, artifacts


def test_candidate_manifest_builder_derives_gate_identities_from_authenticated_registry():
    cid, gate_ids, reg, ctx, coverage, artifacts=candidate_fixture()
    manifest=ge2.build_candidate_evidence_manifest_v2(
        candidate_id=cid,
        required_gates=gate_ids,
        gate_artifacts=artifacts,
        expected_prefreeze_manifest_sha256=PREFREEZE,
        execution_context=ctx,
        gate_governance_registry=reg,
        tournament_contract=contract(),
        expected_coverage_audit_sha256_by_gate=coverage,
    )
    assert manifest['schema'] == a2.EVIDENCE_SCHEMA
    assert list(manifest['gates']) == gate_ids
    for gate in gate_ids:
        assert manifest['gates'][gate]['status'] == 'PASS'
        assert manifest['gates'][gate]['evidence_sha256'] == ge2.canonical_sha256(artifacts[gate])


def test_candidate_manifest_builder_rejects_registry_substitution_against_frozen_context():
    cid, gate_ids, reg, ctx, coverage, artifacts=candidate_fixture()
    altered=registry()
    for row in altered['records']:
        if row['candidate_id']==cid and row['gate_id']==gate_ids[0]:
            row['decision_rule_sha256']=sha('posthoc-rule')
            break
    with pytest.raises(ge2.GateEvidenceV2Error):
        ge2.build_candidate_evidence_manifest_v2(
            candidate_id=cid, required_gates=gate_ids, gate_artifacts=artifacts,
            expected_prefreeze_manifest_sha256=PREFREEZE,
            execution_context=ctx,
            gate_governance_registry=altered,
            tournament_contract=contract(),
            expected_coverage_audit_sha256_by_gate=coverage,
        )


def test_candidate_manifest_builder_rejects_incomplete_required_gate_set_even_if_artifacts_match_subset():
    cid, gate_ids, reg, ctx, coverage, artifacts=candidate_fixture()
    subset=gate_ids[:-1]
    with pytest.raises(ge2.GateEvidenceV2Error):
        ge2.build_candidate_evidence_manifest_v2(
            candidate_id=cid,
            required_gates=subset,
            gate_artifacts={gate: artifacts[gate] for gate in subset},
            expected_prefreeze_manifest_sha256=PREFREEZE,
            execution_context=ctx,
            gate_governance_registry=reg,
            tournament_contract=contract(),
            expected_coverage_audit_sha256_by_gate={gate: coverage[gate] for gate in subset},
        )


def test_candidate_manifest_builder_rejects_missing_gate_artifact():
    cid, gate_ids, reg, ctx, coverage, artifacts=candidate_fixture()
    artifacts.pop(gate_ids[-1])
    with pytest.raises(ge2.GateEvidenceV2Error):
        ge2.build_candidate_evidence_manifest_v2(
            candidate_id=cid, required_gates=gate_ids, gate_artifacts=artifacts,
            expected_prefreeze_manifest_sha256=PREFREEZE,
            execution_context=ctx,
            gate_governance_registry=reg,
            tournament_contract=contract(),
            expected_coverage_audit_sha256_by_gate=coverage,
        )
