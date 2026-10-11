"""Outcome-blind target-tournament prefreeze manifest construction."""
import hashlib
import json

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


class PrefreezeError(ValueError):
    pass


def _canonical_sha(obj):
    raw = json.dumps(
        obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def build_prefreeze_manifest(config):
    if config.get('schema') != SCHEMA:
        raise PrefreezeError('wrong schema')
    if config.get('fixture_only') is not True:
        raise PrefreezeError('current prefreeze scaffold must remain fixture_only=true')
    if config.get('multiplicity_method') != 'BONFERRONI':
        raise PrefreezeError('only frozen BONFERRONI method supported')
    try:
        family_alpha = float(config['family_alpha'])
    except Exception as exc:
        raise PrefreezeError('family_alpha required') from exc
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
    cases = config.get('decision_cases')
    if not isinstance(cases, list) or not cases:
        raise PrefreezeError('nonempty decision_cases required')
    ids = [c.get('case_id') for c in cases]
    if (
        any(not isinstance(x, str) or not x for x in ids)
        or len(set(ids)) != len(ids)
    ):
        raise PrefreezeError('case_id values must be unique nonempty strings')
    for case in cases:
        n = case.get('available_donors_upper_bound')
        if type(n) is not int or n < 0:
            raise PrefreezeError(
                'available_donors_upper_bound must be nonnegative integer'
            )

    family_size = len(cases)
    alpha_eff = family_alpha / family_size
    min_donors = minimum_donors_for_sign_resolution(alpha_eff)
    min_perm = minimum_permutation_draws_for_resolution(alpha_eff)
    resolution = []
    for case in cases:
        upper = case['available_donors_upper_bound']
        resolution.append(
            {
                'case_id': case['case_id'],
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
