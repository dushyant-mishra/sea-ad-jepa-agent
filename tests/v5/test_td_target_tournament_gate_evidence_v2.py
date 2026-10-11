import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_adjudicator_v2 as a2
import td_target_tournament_gate_evidence_v2 as ge2


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


PREFREEZE = sha('prefreeze')
CONTEXT = sha('context')
COVERAGE = sha('coverage')
EXECUTOR = sha('executor')
ESTIMAND = sha('estimand')
RULE = sha('decision-rule')
PAYLOAD = sha('payload')


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


def test_candidate_manifest_builder_requires_exact_gate_artifact_set_and_hashes_artifacts():
    gate_ids = ['Q1_Q_SCALAR_STUDENT_ABSENT', 'Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR']
    coverage = {gate: sha(f'coverage-{gate}') for gate in gate_ids}
    executors = {gate: sha(f'executor-{gate}') for gate in gate_ids}
    estimands = {gate: sha(f'estimand-{gate}') for gate in gate_ids}
    rules = {gate: sha(f'rule-{gate}') for gate in gate_ids}
    artifacts = {
        gate: artifact(
            gate=gate, executor=executors[gate], estimand=estimands[gate], rule=rules[gate]
        )
        for gate in gate_ids
    }
    for gate in gate_ids:
        artifacts[gate]['coverage_audit_sha256'] = coverage[gate]
    manifest = ge2.build_candidate_evidence_manifest_v2(
        candidate_id='C3_QUERY_MEASURED',
        required_gates=gate_ids,
        gate_artifacts=artifacts,
        expected_prefreeze_manifest_sha256=PREFREEZE,
        expected_execution_context_sha256=CONTEXT,
        expected_coverage_audit_sha256_by_gate=coverage,
        expected_qualified_gate_executor_sha256_by_gate=executors,
        expected_estimand_sha256_by_gate=estimands,
        expected_decision_rule_sha256_by_gate=rules,
    )
    assert manifest['schema'] == a2.EVIDENCE_SCHEMA
    assert list(manifest['gates']) == gate_ids
    for gate in gate_ids:
        assert manifest['gates'][gate]['status'] == 'PASS'
        assert manifest['gates'][gate]['evidence_schema'] == a2.expected_evidence_schema(gate)
        assert manifest['gates'][gate]['evidence_sha256'] == ge2.canonical_sha256(artifacts[gate])


def test_candidate_manifest_builder_rejects_missing_gate_artifact():
    gate_ids = ['Q1_Q_SCALAR_STUDENT_ABSENT', 'Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR']
    coverage = {gate: sha(f'coverage-{gate}') for gate in gate_ids}
    executors = {gate: sha(f'executor-{gate}') for gate in gate_ids}
    estimands = {gate: sha(f'estimand-{gate}') for gate in gate_ids}
    rules = {gate: sha(f'rule-{gate}') for gate in gate_ids}
    artifacts = {
        'Q1_Q_SCALAR_STUDENT_ABSENT': artifact(
            executor=executors['Q1_Q_SCALAR_STUDENT_ABSENT'],
            estimand=estimands['Q1_Q_SCALAR_STUDENT_ABSENT'],
            rule=rules['Q1_Q_SCALAR_STUDENT_ABSENT'],
        )
    }
    artifacts['Q1_Q_SCALAR_STUDENT_ABSENT']['coverage_audit_sha256'] = coverage['Q1_Q_SCALAR_STUDENT_ABSENT']
    with pytest.raises(ge2.GateEvidenceV2Error):
        ge2.build_candidate_evidence_manifest_v2(
            candidate_id='C3_QUERY_MEASURED', required_gates=gate_ids,
            gate_artifacts=artifacts,
            expected_prefreeze_manifest_sha256=PREFREEZE,
            expected_execution_context_sha256=CONTEXT,
            expected_coverage_audit_sha256_by_gate=coverage,
            expected_qualified_gate_executor_sha256_by_gate=executors,
            expected_estimand_sha256_by_gate=estimands,
            expected_decision_rule_sha256_by_gate=rules,
        )
