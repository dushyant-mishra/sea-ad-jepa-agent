"""Outcome-blind target-tournament prefreeze manifest construction."""
import hashlib
import json
import math

from td_target_tournament_precision import (
    minimum_donors_for_sign_resolution,
    minimum_permutation_draws_for_resolution,
)

SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_CONFIG_V1'
EXPECTED_AUTHORITY_KEYS = {
    'value_read_authorized',
    'real_tournament_authorized',
    'target_selection_authorized',
    'representation_selection_authorized',
    'td60_authorized',
    'stage4_authorized',
    'training_authorized',
}
CASE_FIELDS = (
    'case_id',
    'candidate_id',
    'gate_id',
    'source',
    'analysis_tier',
    'endpoint_id',
    'available_donors_upper_bound',
)
ROLE_FIELDS = (
    'candidate_id',
    'gate_id',
    'source',
    'analysis_tier',
    'endpoint_id',
)
CONTRACT_SCHEMA = 'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1'
CONTRACT_CLAIM_BOUNDARY = 'SYNTHETIC_SCAFFOLD_ONLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY'
CONTRACT_FIELDS = {
    'schema', 'fixture_only', 'authority', 'candidate_ids',
    'foundation_candidate_ids', 'optional_specialist_ids', 'mandatory_gates',
    'claim_boundary', 'candidate_specific_gates',
}
CONTRACT_AUTHORITY_KEYS = {
    'value_read_authorized',
    'target_selection_authorized',
    'representation_selection_authorized',
    'td60_authorized',
    'stage4_authorized',
    'training_authorized',
}


class PrefreezeError(ValueError):
    pass


def _canonical_sha(obj):
    raw = json.dumps(
        obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _validate_tournament_contract(contract):
    if not isinstance(contract, dict) or set(contract) != CONTRACT_FIELDS:
        raise PrefreezeError('tournament contract fields must be exact')
    if contract.get('schema') != CONTRACT_SCHEMA:
        raise PrefreezeError('invalid tournament contract schema')
    if contract.get('fixture_only') is not True:
        raise PrefreezeError('tournament contract must remain fixture_only=true')
    if contract.get('claim_boundary') != CONTRACT_CLAIM_BOUNDARY:
        raise PrefreezeError('tournament contract claim_boundary mismatch')
    auth=contract.get('authority')
    if (
        not isinstance(auth,dict)
        or set(auth) != CONTRACT_AUTHORITY_KEYS
        or any(v is not False for v in auth.values())
    ):
        raise PrefreezeError('tournament contract authority must be exact and false')
    candidates=contract.get('candidate_ids')
    foundation=contract.get('foundation_candidate_ids')
    specialists=contract.get('optional_specialist_ids')
    common=contract.get('mandatory_gates')
    specific=contract.get('candidate_specific_gates')
    if (
        not isinstance(candidates,list) or not candidates
        or len(set(candidates)) != len(candidates)
        or any(not isinstance(x,str) or not x for x in candidates)
    ):
        raise PrefreezeError('invalid tournament candidate_ids')
    if (
        not isinstance(foundation,list) or not isinstance(specialists,list)
        or set(foundation) & set(specialists)
        or set(foundation) | set(specialists) != set(candidates)
    ):
        raise PrefreezeError('foundation/specialist candidate partition mismatch')
    if (
        not isinstance(common,list) or not common
        or len(set(common)) != len(common)
        or any(not isinstance(x,str) or not x for x in common)
    ):
        raise PrefreezeError('invalid mandatory_gates')
    if not isinstance(specific,dict) or set(specific) != set(candidates):
        raise PrefreezeError('candidate_specific_gates must cover exact candidates')
    for cid,gates in specific.items():
        if (
            not isinstance(gates,list)
            or len(set(gates)) != len(gates)
            or any(not isinstance(x,str) or not x for x in gates)
        ):
            raise PrefreezeError(f'invalid candidate-specific gates: {cid}')
    return contract


def canonical_tournament_contract_sha256(contract):
    return _canonical_sha(_validate_tournament_contract(contract))


def _validate_cases(cases):
    if not isinstance(cases, list) or not cases:
        raise PrefreezeError('nonempty decision_cases required')
    ids=[]
    roles=set()
    normalized=[]
    for case in cases:
        if not isinstance(case, dict) or set(case) != set(CASE_FIELDS):
            raise PrefreezeError('decision case fields must exactly match frozen role schema')
        for key in CASE_FIELDS[:-1]:
            if not isinstance(case[key], str) or not case[key]:
                raise PrefreezeError(f'{key} must be nonempty string')
        n=case['available_donors_upper_bound']
        if type(n) is not int or n < 0:
            raise PrefreezeError(
                'available_donors_upper_bound must be nonnegative integer'
            )
        ids.append(case['case_id'])
        role=tuple(case[k] for k in ROLE_FIELDS)
        if role in roles:
            raise PrefreezeError('duplicate decision role tuple')
        roles.add(role)
        normalized.append({k:case[k] for k in CASE_FIELDS})
    if len(set(ids)) != len(ids):
        raise PrefreezeError('case_id values must be unique nonempty strings')
    return sorted(normalized, key=lambda x:x['case_id'])


def canonical_decision_family_sha256(cases):
    return _canonical_sha(_validate_cases(cases))


def build_prefreeze_manifest(config):
    if config.get('schema') != SCHEMA:
        raise PrefreezeError('wrong schema')
    if config.get('fixture_only') is not True:
        raise PrefreezeError('current prefreeze scaffold must remain fixture_only=true')
    if config.get('multiplicity_method') != 'BONFERRONI':
        raise PrefreezeError('only frozen BONFERRONI method supported')
    family_alpha = config.get('family_alpha')
    if isinstance(family_alpha, bool) or type(family_alpha) not in (int, float):
        raise PrefreezeError('family_alpha must be an exact JSON numeric value')
    family_alpha = float(family_alpha)
    if not math.isfinite(family_alpha):
        raise PrefreezeError('family_alpha must be finite')
    if not (0.0 < family_alpha < 1.0):
        raise PrefreezeError('family_alpha must be in (0,1)')
    sha = config.get('tournament_contract_sha256', '')
    if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
        raise PrefreezeError('tournament_contract_sha256 must be lowercase SHA-256')
    if not str(config.get('null_seed_material', '')).strip():
        raise PrefreezeError('null_seed_material required')
    auth = config.get('authority')
    if (
        not isinstance(auth, dict)
        or set(auth) != EXPECTED_AUTHORITY_KEYS
        or any(v is not False for v in auth.values())
    ):
        raise PrefreezeError('authority must contain exact frozen keys, all false')

    contract = config.get('tournament_contract')
    _validate_tournament_contract(contract)
    expected_contract_sha = canonical_tournament_contract_sha256(contract)
    if sha != expected_contract_sha:
        raise PrefreezeError('tournament contract SHA mismatch')

    cases = config.get('decision_cases')
    normalized = _validate_cases(cases)
    common_gates=set(contract['mandatory_gates'])
    specific=contract['candidate_specific_gates']
    for case in normalized:
        cid=case['candidate_id']
        if cid not in specific:
            raise PrefreezeError(f'case candidate absent from tournament contract: {cid}')
        allowed=common_gates | set(specific[cid])
        if case['gate_id'] not in allowed:
            raise PrefreezeError(
                f'case gate not allowed for candidate by tournament contract: {cid}: {case["gate_id"]}'
            )

    registry_sha = config.get('decision_family_registry_sha256', '')
    if (
        not isinstance(registry_sha, str)
        or len(registry_sha) != 64
        or any(c not in '0123456789abcdef' for c in registry_sha)
    ):
        raise PrefreezeError('decision_family_registry_sha256 must be lowercase SHA-256')
    actual_registry_sha = _canonical_sha(normalized)
    if registry_sha != actual_registry_sha:
        raise PrefreezeError('decision family registry SHA mismatch')

    family_size = len(normalized)
    alpha_eff = family_alpha / family_size
    min_donors = minimum_donors_for_sign_resolution(alpha_eff)
    min_perm = minimum_permutation_draws_for_resolution(alpha_eff)
    resolution = []
    for case in normalized:
        upper = case['available_donors_upper_bound']
        resolution.append(
            {
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
            }
        )

    core = {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_MANIFEST_V1',
        'fixture_only': True,
        'family_alpha': family_alpha,
        'multiplicity_method': 'BONFERRONI',
        'decision_family_size': family_size,
        'decision_family_registry_sha256': actual_registry_sha,
        'alpha_eff': alpha_eff,
        'minimum_nonzero_donors_for_sign_resolution': min_donors,
        'minimum_permutation_draws_for_resolution': min_perm,
        'tournament_contract_sha256': sha,
        'null_seed_material': config['null_seed_material'],
        'case_resolution': resolution,
        'authority': dict(auth),
    }
    core['manifest_sha256'] = _canonical_sha(core)
    return core
