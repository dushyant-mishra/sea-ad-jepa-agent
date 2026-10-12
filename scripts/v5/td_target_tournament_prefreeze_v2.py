"""Outcome-blind V2 target-tournament prefreeze construction.

This module freezes governance identities only. It opens no biological data, does
not adjudicate outcomes, and creates no real-tournament or target authority.
"""
from __future__ import annotations

import hashlib
import json
import math

import td_target_tournament_contract_v2 as c2
from td_target_tournament_precision import (
    minimum_donors_for_sign_resolution,
    minimum_permutation_draws_for_resolution,
)


class PrefreezeV2Error(ValueError):
    pass


CONFIG_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_CONFIG_V2'
MANIFEST_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_MANIFEST_V2'
EXECUTION_CONTEXT_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_EXECUTION_CONTEXT_V2'

AUTHORITY_KEYS = tuple(sorted(c2.AUTHORITY_KEYS))

_CONFIG_FIELDS = {
    'schema', 'fixture_only', 'family_alpha', 'multiplicity_method',
    'tournament_contract', 'tournament_contract_sha256',
    'execution_context', 'execution_context_sha256', 'null_seed_material',
    'decision_cases', 'decision_family_registry_sha256', 'authority',
}
_EXECUTION_CONTEXT_FIELDS = {
    'schema', 'fixture_only', 'executor_code_identity_sha256',
    'gate_executor_registry_sha256', 'gate_estimand_registry_sha256',
    'gate_decision_rule_registry_sha256',
    'population_registry_sha256', 'donor_registry_sha256',
    'source_registry_sha256', 'operator_registry_sha256',
    'support_registry_sha256', 'teacher_student_evidence_rights_sha256',
    'split_registry_sha256', 'observation_descriptor_sha256',
    'corrected_replay_evidence_sha256',
}
_CASE_FIELDS = (
    'case_id', 'candidate_id', 'gate_id', 'source', 'analysis_tier',
    'endpoint_id', 'available_donors_upper_bound',
)
_ROLE_FIELDS = ('candidate_id', 'gate_id', 'source', 'analysis_tier', 'endpoint_id')


def _is_sha256(value) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in '0123456789abcdef' for ch in value)
    )


def canonical_json_sha256(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _validate_authority(authority):
    if not isinstance(authority, dict) or set(authority) != set(AUTHORITY_KEYS):
        raise PrefreezeV2Error('authority keys must exactly match V2 contract')
    if any(value is not False for value in authority.values()):
        raise PrefreezeV2Error('prefreeze V2 cannot carry authority')


def _validate_contract(contract):
    try:
        c2.validate_contract(contract)
    except c2.ContractV2Error as exc:
        raise PrefreezeV2Error(str(exc)) from exc
    return contract


def canonical_tournament_contract_sha256(contract) -> str:
    return canonical_json_sha256(_validate_contract(contract))


def _validate_execution_context(context):
    if not isinstance(context, dict) or set(context) != _EXECUTION_CONTEXT_FIELDS:
        raise PrefreezeV2Error('execution_context fields must exactly match V2 schema')
    if context.get('schema') != EXECUTION_CONTEXT_SCHEMA:
        raise PrefreezeV2Error('wrong V2 execution_context schema')
    if context.get('fixture_only') is not True:
        raise PrefreezeV2Error('current V2 execution_context must remain fixture_only=true')
    for key in sorted(_EXECUTION_CONTEXT_FIELDS - {'schema', 'fixture_only'}):
        if not _is_sha256(context.get(key)):
            raise PrefreezeV2Error(f'execution_context {key} must be lowercase SHA-256')
    return context


def canonical_execution_context_sha256(context) -> str:
    return canonical_json_sha256(_validate_execution_context(context))


def _validate_cases(cases, contract=None):
    if not isinstance(cases, list) or not cases:
        raise PrefreezeV2Error('nonempty decision_cases required')
    normalized = []
    seen_ids = set()
    seen_roles = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != set(_CASE_FIELDS):
            raise PrefreezeV2Error('decision case fields must exactly match V2 role schema')
        for key in _CASE_FIELDS[:-1]:
            if not isinstance(case[key], str) or not case[key]:
                raise PrefreezeV2Error(f'{key} must be nonempty string')
        upper = case['available_donors_upper_bound']
        if type(upper) is not int or upper < 0:
            raise PrefreezeV2Error('available_donors_upper_bound must be nonnegative integer')
        cid = case['case_id']
        if cid in seen_ids:
            raise PrefreezeV2Error('duplicate case_id')
        seen_ids.add(cid)
        role = tuple(case[key] for key in _ROLE_FIELDS)
        if role in seen_roles:
            raise PrefreezeV2Error('duplicate decision role tuple')
        seen_roles.add(role)
        if contract is not None:
            candidate = case['candidate_id']
            if candidate not in contract['candidate_gate_sets']:
                raise PrefreezeV2Error(f'case candidate absent from V2 contract: {candidate}')
            if case['gate_id'] not in contract['candidate_gate_sets'][candidate]:
                raise PrefreezeV2Error(
                    f'case gate not allowed for candidate by V2 contract: {candidate}: {case["gate_id"]}'
                )
        normalized.append({key: case[key] for key in _CASE_FIELDS})
    return sorted(normalized, key=lambda row: row['case_id'])


def canonical_decision_family_sha256(cases) -> str:
    return canonical_json_sha256(_validate_cases(cases))


def build_prefreeze_manifest(config):
    if not isinstance(config, dict) or set(config) != _CONFIG_FIELDS:
        raise PrefreezeV2Error('prefreeze V2 config fields must be exact')
    if config.get('schema') != CONFIG_SCHEMA:
        raise PrefreezeV2Error('wrong V2 prefreeze config schema')
    if config.get('fixture_only') is not True:
        raise PrefreezeV2Error('current V2 prefreeze must remain fixture_only=true')
    if config.get('multiplicity_method') != 'BONFERRONI':
        raise PrefreezeV2Error('only frozen BONFERRONI method supported')

    family_alpha = config.get('family_alpha')
    if isinstance(family_alpha, bool) or type(family_alpha) not in (int, float):
        raise PrefreezeV2Error('family_alpha must be an exact JSON numeric value')
    family_alpha = float(family_alpha)
    if not math.isfinite(family_alpha) or not (0.0 < family_alpha < 1.0):
        raise PrefreezeV2Error('family_alpha must be finite and in (0,1)')

    null_seed = config.get('null_seed_material')
    if not isinstance(null_seed, str) or not null_seed.strip() or '\0' in null_seed:
        raise PrefreezeV2Error('null_seed_material must be a nonempty NUL-free string')
    _validate_authority(config.get('authority'))

    contract = _validate_contract(config.get('tournament_contract'))
    contract_sha = config.get('tournament_contract_sha256')
    expected_contract_sha = canonical_tournament_contract_sha256(contract)
    if contract_sha != expected_contract_sha:
        raise PrefreezeV2Error('V2 tournament contract SHA mismatch')

    context = _validate_execution_context(config.get('execution_context'))
    context_sha = config.get('execution_context_sha256')
    expected_context_sha = canonical_execution_context_sha256(context)
    if context_sha != expected_context_sha:
        raise PrefreezeV2Error('V2 execution_context SHA mismatch')

    cases = _validate_cases(config.get('decision_cases'), contract=contract)
    registry_sha = config.get('decision_family_registry_sha256')
    expected_registry_sha = canonical_json_sha256(cases)
    if registry_sha != expected_registry_sha:
        raise PrefreezeV2Error('V2 decision family registry SHA mismatch')

    family_size = len(cases)
    alpha_eff = family_alpha / family_size
    min_donors = minimum_donors_for_sign_resolution(alpha_eff)
    min_perm = minimum_permutation_draws_for_resolution(alpha_eff)
    resolution = []
    for case in cases:
        upper = case['available_donors_upper_bound']
        resolution.append({
            'case_id': case['case_id'],
            'candidate_id': case['candidate_id'],
            'gate_id': case['gate_id'],
            'source': case['source'],
            'analysis_tier': case['analysis_tier'],
            'endpoint_id': case['endpoint_id'],
            'available_donors_upper_bound': upper,
            'resolution_impossible_from_donor_upper_bound': upper < min_donors,
            'estimability_proven': False,
            'biological_result': 'NOT_OPENED',
        })

    core = {
        'schema': MANIFEST_SCHEMA,
        'fixture_only': True,
        'family_alpha': family_alpha,
        'multiplicity_method': 'BONFERRONI',
        'decision_family_size': family_size,
        'decision_family_registry_sha256': expected_registry_sha,
        'alpha_eff': alpha_eff,
        'minimum_nonzero_donors_for_sign_resolution': min_donors,
        'minimum_permutation_draws_for_resolution': min_perm,
        'tournament_contract_sha256': expected_contract_sha,
        'execution_context_sha256': expected_context_sha,
        'null_seed_material': null_seed,
        'case_resolution': resolution,
        'authority': dict(config['authority']),
    }
    core['manifest_sha256'] = canonical_json_sha256(core)
    return core
