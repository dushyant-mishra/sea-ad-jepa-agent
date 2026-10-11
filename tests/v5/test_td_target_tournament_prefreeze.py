import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_target_tournament_prefreeze.py'
sys.path.insert(0, str(MOD.parent))
spec = importlib.util.spec_from_file_location('td_target_tournament_prefreeze', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def config(n=20):
    return {
        'schema': 'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_CONFIG_V1',
        'fixture_only': True,
        'family_alpha': 0.05,
        'multiplicity_method': 'BONFERRONI',
        'tournament_contract_sha256': 'a' * 64,
        'null_seed_material': 'fixture-seed',
        'decision_cases': [
            {'case_id': f'case_{i:02d}', 'available_donors_upper_bound': 10}
            for i in range(n)
        ],
        'authority': {
            'value_read_authorized': False,
            'real_tournament_authorized': False,
            'target_selection_authorized': False,
            'representation_selection_authorized': False,
            'td60_authorized': False,
            'stage4_authorized': False,
            'training_authorized': False,
        },
    }


def test_twenty_case_family_derives_resolution_without_outcomes():
    out = m.build_prefreeze_manifest(config(20))
    assert out['decision_family_size'] == 20
    assert out['alpha_eff'] == pytest.approx(0.0025)
    assert out['minimum_nonzero_donors_for_sign_resolution'] == 10
    assert out['minimum_permutation_draws_for_resolution'] == 399


def test_low_donor_upper_bound_is_proven_impossible_not_failed_biology():
    c = config(20)
    c['decision_cases'][0]['available_donors_upper_bound'] = 2
    out = m.build_prefreeze_manifest(c)
    row = out['case_resolution'][0]
    assert row['resolution_impossible_from_donor_upper_bound'] is True
    assert row['biological_result'] == 'NOT_OPENED'


def test_sufficient_upper_bound_does_not_claim_estimability():
    out = m.build_prefreeze_manifest(config(20))
    row = out['case_resolution'][0]
    assert row['resolution_impossible_from_donor_upper_bound'] is False
    assert row['estimability_proven'] is False


def test_duplicate_case_ids_rejected():
    c = config(2)
    c['decision_cases'][1]['case_id'] = c['decision_cases'][0]['case_id']
    with pytest.raises(m.PrefreezeError):
        m.build_prefreeze_manifest(c)


def test_authority_true_rejected():
    c = config(2)
    c['authority']['real_tournament_authorized'] = True
    with pytest.raises(m.PrefreezeError):
        m.build_prefreeze_manifest(c)


def test_empty_family_rejected():
    c = config(1)
    c['decision_cases'] = []
    with pytest.raises(m.PrefreezeError):
        m.build_prefreeze_manifest(c)


def test_manifest_hash_is_deterministic_and_outcome_free():
    a = m.build_prefreeze_manifest(config(3))
    b = m.build_prefreeze_manifest(config(3))
    assert a['manifest_sha256'] == b['manifest_sha256']
    assert 'outcome' not in str(a).lower()
