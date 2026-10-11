import hashlib
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_target_tournament_prefreeze as pf


def contract():
    return {
        'schema':'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1',
        'fixture_only':True,
        'authority':{
            'value_read_authorized':False,
            'target_selection_authorized':False,
            'representation_selection_authorized':False,
            'td60_authorized':False,
            'stage4_authorized':False,
            'training_authorized':False,
        },
        'candidate_ids':['C1_RELATIONAL_SHARED'],
        'foundation_candidate_ids':['C1_RELATIONAL_SHARED'],
        'optional_specialist_ids':[],
        'mandatory_gates':['G1_DONOR_PRIMARY'],
        'claim_boundary':'SYNTHETIC_SCAFFOLD_ONLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY',
        'candidate_specific_gates':{'C1_RELATIONAL_SHARED':[]},
    }


def cases():
    return [{
        'case_id':'c1',
        'candidate_id':'C1_RELATIONAL_SHARED',
        'gate_id':'G1_DONOR_PRIMARY',
        'source':'HVS',
        'analysis_tier':'tier0',
        'endpoint_id':'e1',
        'available_donors_upper_bound':10,
    }]


def config():
    c = contract()
    rows = cases()
    contract_sha = pf.canonical_tournament_contract_sha256(c)
    registry_sha = pf.canonical_decision_family_sha256(rows)
    return {
        'schema':'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_CONFIG_V1',
        'fixture_only':True,
        'family_alpha':0.05,
        'multiplicity_method':'BONFERRONI',
        'tournament_contract':c,
        'tournament_contract_sha256':contract_sha,
        'null_seed_material':'fixture-seed',
        'decision_cases':rows,
        'decision_family_registry_sha256':registry_sha,
        'authority':{
            'value_read_authorized':False,
            'real_tournament_authorized':False,
            'target_selection_authorized':False,
            'representation_selection_authorized':False,
            'td60_authorized':False,
            'stage4_authorized':False,
            'training_authorized':False,
        },
    }


def test_prefreeze_config_rejects_extra_shadow_claim_field():
    c = config(); c['target_selected'] = True
    with pytest.raises(pf.PrefreezeError):
        pf.build_prefreeze_manifest(c)


@pytest.mark.parametrize('bad_seed', [7, True, None, ['seed']])
def test_null_seed_material_must_be_exact_nonempty_string(bad_seed):
    c = config(); c['null_seed_material'] = bad_seed
    with pytest.raises(pf.PrefreezeError):
        pf.build_prefreeze_manifest(c)
