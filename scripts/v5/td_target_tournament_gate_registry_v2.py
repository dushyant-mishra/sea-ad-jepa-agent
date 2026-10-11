"""Authenticated gate-governance registry for Target Tournament V2.

The registry prospectively binds every candidate×gate role to one qualified
executor identity, one estimand identity, and one decision-rule identity. It is
synthetic/metadata-only and creates no biological or target authority.
"""
from __future__ import annotations

import hashlib
import json

import td_target_tournament_contract_v2 as c2
import td_target_tournament_prefreeze_v2 as p2


class GateRegistryV2Error(ValueError):
    pass


REGISTRY_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_GATE_GOVERNANCE_REGISTRY_V2'
AUTHORITY_KEYS = tuple(sorted(c2.AUTHORITY_KEYS))
_REGISTRY_FIELDS = {'schema', 'fixture_only', 'records', 'authority'}
_RECORD_FIELDS = {
    'candidate_id', 'gate_id', 'qualified_gate_executor_sha256',
    'estimand_sha256', 'decision_rule_sha256',
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
        raise GateRegistryV2Error('gate registry authority keys must exactly match V2 contract')
    if any(value is not False for value in authority.values()):
        raise GateRegistryV2Error('gate registry cannot carry authority')


def _expected_roles(contract):
    try:
        c2.validate_contract(contract)
    except c2.ContractV2Error as exc:
        raise GateRegistryV2Error(str(exc)) from exc
    return {
        (candidate_id, gate_id)
        for candidate_id in contract['candidate_ids']
        for gate_id in contract['candidate_gate_sets'][candidate_id]
    }


def validate_gate_registry_v2(registry, contract):
    expected_roles = _expected_roles(contract)
    if not isinstance(registry, dict) or set(registry) != _REGISTRY_FIELDS:
        raise GateRegistryV2Error('gate registry fields must exactly match V2 schema')
    if registry.get('schema') != REGISTRY_SCHEMA:
        raise GateRegistryV2Error('wrong V2 gate registry schema')
    if registry.get('fixture_only') is not True:
        raise GateRegistryV2Error('current V2 gate registry must remain fixture_only=true')
    _validate_authority(registry.get('authority'))

    records = registry.get('records')
    if not isinstance(records, list) or not records:
        raise GateRegistryV2Error('nonempty gate registry records required')

    by_role = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
            raise GateRegistryV2Error('gate registry record fields must be exact')
        candidate_id = record.get('candidate_id')
        gate_id = record.get('gate_id')
        if not isinstance(candidate_id, str) or not candidate_id:
            raise GateRegistryV2Error('registry candidate_id must be nonempty string')
        if not isinstance(gate_id, str) or not gate_id:
            raise GateRegistryV2Error('registry gate_id must be nonempty string')
        role = (candidate_id, gate_id)
        if role in by_role:
            raise GateRegistryV2Error(f'duplicate gate registry role: {candidate_id}: {gate_id}')
        for key in (
            'qualified_gate_executor_sha256', 'estimand_sha256', 'decision_rule_sha256'
        ):
            if not _is_sha256(record.get(key)):
                raise GateRegistryV2Error(f'{key} must be lowercase SHA-256')
        by_role[role] = dict(record)

    actual_roles = set(by_role)
    missing = sorted(expected_roles - actual_roles)
    extra = sorted(actual_roles - expected_roles)
    if missing or extra:
        raise GateRegistryV2Error(
            f'gate registry must cover exact V2 candidate×gate roles; missing={missing} extra={extra}'
        )

    return {
        candidate_id: {
            gate_id: by_role[(candidate_id, gate_id)]
            for gate_id in contract['candidate_gate_sets'][candidate_id]
        }
        for candidate_id in contract['candidate_ids']
    }


def registry_projection_hashes(registry, contract):
    bindings = validate_gate_registry_v2(registry, contract)
    executor_rows = []
    estimand_rows = []
    rule_rows = []
    for candidate_id in contract['candidate_ids']:
        for gate_id in contract['candidate_gate_sets'][candidate_id]:
            record = bindings[candidate_id][gate_id]
            base = {'candidate_id': candidate_id, 'gate_id': gate_id}
            executor_rows.append({
                **base,
                'qualified_gate_executor_sha256': record['qualified_gate_executor_sha256'],
            })
            estimand_rows.append({
                **base,
                'estimand_sha256': record['estimand_sha256'],
            })
            rule_rows.append({
                **base,
                'decision_rule_sha256': record['decision_rule_sha256'],
            })
    return {
        'gate_executor_registry_sha256': canonical_sha256(executor_rows),
        'gate_estimand_registry_sha256': canonical_sha256(estimand_rows),
        'gate_decision_rule_registry_sha256': canonical_sha256(rule_rows),
    }


def bind_registry_to_execution_context(registry, contract, execution_context):
    bindings = validate_gate_registry_v2(registry, contract)
    try:
        p2.canonical_execution_context_sha256(execution_context)
    except p2.PrefreezeV2Error as exc:
        raise GateRegistryV2Error(str(exc)) from exc
    expected = registry_projection_hashes(registry, contract)
    for key, value in expected.items():
        if execution_context.get(key) != value:
            raise GateRegistryV2Error(f'execution context {key} does not bind supplied gate registry')
    return bindings
