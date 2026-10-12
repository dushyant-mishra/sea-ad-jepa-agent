"""V2 gate-evidence custody and candidate-manifest construction.

Gate-specific executors remain responsible for estimands and decision rules. This
module authenticates their output envelope and binds it to the exact V2
prefreeze, execution context, coverage audit, frozen gate-governance registry,
and its executor/estimand/decision-rule identities before a candidate manifest
is constructed. It opens no biology and creates no authority.
"""
from __future__ import annotations

import hashlib
import json

import td_target_tournament_adjudicator_v2 as a2
import td_target_tournament_gate_registry_v2 as gr2
import td_target_tournament_prefreeze_v2 as p2


class GateEvidenceV2Error(ValueError):
    pass


AUTHORITY_KEYS = tuple(sorted(a2.AUTHORITY_KEYS))
ALLOWED_STATUS = {'PASS', 'FAIL', 'NOT_ESTIMABLE'}
_ARTIFACT_FIELDS = {
    'schema', 'fixture_only', 'candidate_id', 'gate_id',
    'prefreeze_manifest_sha256', 'execution_context_sha256',
    'coverage_audit_sha256', 'qualified_gate_executor_sha256',
    'estimand_sha256', 'decision_rule_sha256', 'status',
    'evidence_payload_sha256', 'authority',
}


def _is_sha256(value) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in '0123456789abcdef' for ch in value)
    )


def canonical_sha256(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _validate_authority(authority):
    if not isinstance(authority, dict) or set(authority) != set(AUTHORITY_KEYS):
        raise GateEvidenceV2Error('gate-evidence authority keys must exactly match V2')
    if any(value is not False for value in authority.values()):
        raise GateEvidenceV2Error('gate evidence cannot carry authority')


def validate_gate_evidence_artifact_v2(
    artifact,
    *,
    expected_candidate_id,
    expected_gate_id,
    expected_prefreeze_manifest_sha256,
    expected_execution_context_sha256,
    expected_coverage_audit_sha256,
    expected_qualified_gate_executor_sha256,
    expected_estimand_sha256,
    expected_decision_rule_sha256,
):
    for label, value in (
        ('expected prefreeze SHA', expected_prefreeze_manifest_sha256),
        ('expected execution-context SHA', expected_execution_context_sha256),
        ('expected coverage-audit SHA', expected_coverage_audit_sha256),
        ('expected qualified gate-executor SHA', expected_qualified_gate_executor_sha256),
        ('expected estimand SHA', expected_estimand_sha256),
        ('expected decision-rule SHA', expected_decision_rule_sha256),
    ):
        if not _is_sha256(value):
            raise GateEvidenceV2Error(f'{label} must be lowercase SHA-256')
    if not isinstance(expected_candidate_id, str) or not expected_candidate_id:
        raise GateEvidenceV2Error('expected_candidate_id must be nonempty string')
    if not isinstance(expected_gate_id, str) or not expected_gate_id:
        raise GateEvidenceV2Error('expected_gate_id must be nonempty string')

    if not isinstance(artifact, dict) or set(artifact) != _ARTIFACT_FIELDS:
        raise GateEvidenceV2Error('gate-evidence artifact fields must exactly match V2 envelope')
    if artifact.get('schema') != a2.expected_evidence_schema(expected_gate_id):
        raise GateEvidenceV2Error('gate-evidence schema does not match gate role')
    if artifact.get('fixture_only') is not True:
        raise GateEvidenceV2Error('current gate-evidence artifact must remain fixture_only=true')
    if artifact.get('candidate_id') != expected_candidate_id:
        raise GateEvidenceV2Error('gate-evidence candidate binding mismatch')
    if artifact.get('gate_id') != expected_gate_id:
        raise GateEvidenceV2Error('gate-evidence gate binding mismatch')
    if artifact.get('prefreeze_manifest_sha256') != expected_prefreeze_manifest_sha256:
        raise GateEvidenceV2Error('gate-evidence prefreeze binding mismatch')
    if artifact.get('execution_context_sha256') != expected_execution_context_sha256:
        raise GateEvidenceV2Error('gate-evidence execution-context binding mismatch')
    if artifact.get('coverage_audit_sha256') != expected_coverage_audit_sha256:
        raise GateEvidenceV2Error('gate-evidence coverage-audit binding mismatch')
    if artifact.get('qualified_gate_executor_sha256') != expected_qualified_gate_executor_sha256:
        raise GateEvidenceV2Error('gate-evidence executor binding mismatch')
    if artifact.get('estimand_sha256') != expected_estimand_sha256:
        raise GateEvidenceV2Error('gate-evidence estimand binding mismatch')
    if artifact.get('decision_rule_sha256') != expected_decision_rule_sha256:
        raise GateEvidenceV2Error('gate-evidence decision-rule binding mismatch')
    if not _is_sha256(artifact.get('evidence_payload_sha256')):
        raise GateEvidenceV2Error('gate-evidence evidence_payload_sha256 must be lowercase SHA-256')
    if artifact.get('status') not in ALLOWED_STATUS:
        raise GateEvidenceV2Error('gate-evidence status must be PASS, FAIL, or NOT_ESTIMABLE')
    _validate_authority(artifact.get('authority'))
    return canonical_sha256(artifact)


def _validate_coverage_map(value, required_gates):
    if not isinstance(value, dict) or set(value) != set(required_gates):
        raise GateEvidenceV2Error('coverage-audit SHA map must cover the exact required gate set')
    for gate in required_gates:
        if not _is_sha256(value[gate]):
            raise GateEvidenceV2Error(
                f'coverage-audit SHA map.{gate} must be lowercase SHA-256'
            )


def build_candidate_evidence_manifest_v2(
    *,
    candidate_id,
    required_gates,
    gate_artifacts,
    expected_prefreeze_manifest_sha256,
    execution_context,
    gate_governance_registry,
    tournament_contract,
    expected_coverage_audit_sha256_by_gate,
):
    if not isinstance(candidate_id, str) or not candidate_id:
        raise GateEvidenceV2Error('candidate_id must be nonempty string')
    if not _is_sha256(expected_prefreeze_manifest_sha256):
        raise GateEvidenceV2Error('expected prefreeze SHA must be lowercase SHA-256')

    try:
        p2.canonical_execution_context_sha256(execution_context)
        bindings = gr2.bind_registry_to_execution_context(
            gate_governance_registry, tournament_contract, execution_context
        )
    except (p2.PrefreezeV2Error, gr2.GateRegistryV2Error) as exc:
        raise GateEvidenceV2Error(str(exc)) from exc

    if candidate_id not in tournament_contract.get('candidate_gate_sets', {}):
        raise GateEvidenceV2Error('candidate absent from frozen V2 tournament contract')
    frozen_gates = list(tournament_contract['candidate_gate_sets'][candidate_id])
    if required_gates != frozen_gates:
        raise GateEvidenceV2Error('required_gates must exactly equal frozen candidate gate set')
    if not isinstance(gate_artifacts, dict) or set(gate_artifacts) != set(frozen_gates):
        raise GateEvidenceV2Error('gate_artifacts must cover the exact frozen candidate gate set')
    _validate_coverage_map(expected_coverage_audit_sha256_by_gate, frozen_gates)

    expected_context_sha = p2.canonical_execution_context_sha256(execution_context)
    candidate_bindings = bindings[candidate_id]
    records = {}
    for gate in frozen_gates:
        bound = candidate_bindings[gate]
        artifact = gate_artifacts[gate]
        artifact_sha = validate_gate_evidence_artifact_v2(
            artifact,
            expected_candidate_id=candidate_id,
            expected_gate_id=gate,
            expected_prefreeze_manifest_sha256=expected_prefreeze_manifest_sha256,
            expected_execution_context_sha256=expected_context_sha,
            expected_coverage_audit_sha256=expected_coverage_audit_sha256_by_gate[gate],
            expected_qualified_gate_executor_sha256=bound['qualified_gate_executor_sha256'],
            expected_estimand_sha256=bound['estimand_sha256'],
            expected_decision_rule_sha256=bound['decision_rule_sha256'],
        )
        records[gate] = {
            'status': artifact['status'],
            'evidence_schema': artifact['schema'],
            'evidence_sha256': artifact_sha,
        }

    return {
        'schema': a2.EVIDENCE_SCHEMA,
        'fixture_only': True,
        'candidate_id': candidate_id,
        'prefreeze_manifest_sha256': expected_prefreeze_manifest_sha256,
        'gates': records,
        'authority': {key: False for key in a2.AUTHORITY_KEYS},
    }
