import hashlib, importlib.util, json, sys
from pathlib import Path
import math
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_target_tournament_prefreeze.py'
sys.path.insert(0, str(MOD.parent))
spec = importlib.util.spec_from_file_location('td_target_tournament_prefreeze', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ROLE_FIELDS=('case_id','candidate_id','gate_id','source','analysis_tier','endpoint_id','available_donors_upper_bound')


def _registry_sha(cases):
    normalized=[{k:c[k] for k in ROLE_FIELDS} for c in sorted(cases,key=lambda x:x['case_id'])]
    raw=json.dumps(normalized,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def tournament_contract():
    return {
      'schema':'JEPA_TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1',
      'fixture_only':True,
      'authority':{
        'value_read_authorized':False,'target_selection_authorized':False,
        'representation_selection_authorized':False,'td60_authorized':False,
        'stage4_authorized':False,'training_authorized':False,
      },
      'candidate_ids':['C1_RELATIONAL_SHARED','C2_QUERY_MEASURED','C3_LEARNED_SHARED','C4_STRUCTURED_COMPOSITE','C5_REGULATORY_SPECIALIST'],
      'foundation_candidate_ids':['C1_RELATIONAL_SHARED','C2_QUERY_MEASURED','C3_LEARNED_SHARED','C4_STRUCTURED_COMPOSITE'],
      'optional_specialist_ids':['C5_REGULATORY_SPECIALIST'],
      'mandatory_gates':['G1_DONOR_PRIMARY','G2_SOURCE_REPLICATION','G3_SHORTCUT_DEFEAT','G4_INFORMATION_ASYMMETRY','G5_SUPPORT_ABSTENTION','G6_TRANSFER','G7_NO_POSTHOC'],
      'candidate_specific_gates':{
        'C1_RELATIONAL_SHARED':['R1_SCALE_FREE_RELATIONAL_RECURRENCE'],
        'C2_QUERY_MEASURED':['Q1_Q_SCALAR_STUDENT_ABSENT'],
        'C3_LEARNED_SHARED':['L1_LEARNED_TEACHER_VIEW_CONTINUITY'],
        'C4_STRUCTURED_COMPOSITE':['C4_INCREMENT_OVER_CONSTITUENTS'],
        'C5_REGULATORY_SPECIALIST':['M1_CIRCULARITY_CONTROL'],
      },
    }


def _contract_sha(contract):
    return hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def raw_cases(n=20):
    candidates=['C1_RELATIONAL_SHARED','C2_QUERY_MEASURED','C3_LEARNED_SHARED','C4_STRUCTURED_COMPOSITE']
    sources=['HVS','NPH52','SEA_AD']
    return [{
        'case_id':f'case_{i:02d}',
        'candidate_id':candidates[i%4],
        'gate_id':'G1_DONOR_PRIMARY',
        'source':sources[i%3],
        'analysis_tier':f'tier_{i//12}',
        'endpoint_id':f'endpoint_{i}',
        'available_donors_upper_bound':10,
    } for i in range(n)]


def config(n=20):
    cases=raw_cases(n)
    contract=tournament_contract()
    return {
        'schema':'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_CONFIG_V1',
        'fixture_only':True,
        'family_alpha':0.05,
        'multiplicity_method':'BONFERRONI',
        'tournament_contract':contract,
        'tournament_contract_sha256':_contract_sha(contract),
        'null_seed_material':'fixture-seed',
        'decision_cases':cases,
        'decision_family_registry_sha256':_registry_sha(cases),
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


def test_twenty_case_family_derives_resolution_without_outcomes():
    out=m.build_prefreeze_manifest(config(20))
    assert out['decision_family_size']==20
    assert out['alpha_eff']==pytest.approx(0.0025)
    assert out['minimum_nonzero_donors_for_sign_resolution']==10
    assert out['minimum_permutation_draws_for_resolution']==399


def test_registry_hash_bound_into_manifest():
    c=config(4); out=m.build_prefreeze_manifest(c)
    assert out['decision_family_registry_sha256']==c['decision_family_registry_sha256']


def test_role_change_after_registry_freeze_is_rejected():
    c=config(4)
    c['decision_cases'][0]['source']='SEA_AD' if c['decision_cases'][0]['source']!='SEA_AD' else 'HVS'
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_case_removal_after_registry_freeze_is_rejected():
    c=config(4); c['decision_cases']=c['decision_cases'][:-1]
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_duplicate_role_tuple_rejected_even_with_distinct_case_id():
    c=config(2); a=c['decision_cases'][0]; b=c['decision_cases'][1]
    for k in ('candidate_id','gate_id','source','analysis_tier','endpoint_id'): b[k]=a[k]
    b['case_id']='different_id'
    c['decision_family_registry_sha256']=_registry_sha(c['decision_cases'])
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_missing_role_field_rejected():
    c=config(2); del c['decision_cases'][0]['gate_id']
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_production_registry_hash_matches_frozen_test_canonicalization():
    c=config(4)
    assert m.canonical_decision_family_sha256(c['decision_cases']) == c['decision_family_registry_sha256']


def test_production_contract_hash_matches_test_canonicalization():
    c=config(3)
    assert m.canonical_tournament_contract_sha256(c['tournament_contract']) == c['tournament_contract_sha256']


def test_contract_change_after_hash_freeze_is_rejected():
    c=config(3)
    c['tournament_contract']['mandatory_gates']=list(c['tournament_contract']['mandatory_gates'])+['G8_FAKE']
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_unknown_candidate_role_rejected_even_with_rehashed_registry():
    c=config(3)
    c['decision_cases'][0]['candidate_id']='C9_NOT_FROZEN'
    c['decision_family_registry_sha256']=_registry_sha(c['decision_cases'])
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_gate_not_allowed_for_candidate_rejected_even_with_rehashed_registry():
    c=config(3)
    c['decision_cases'][0]['gate_id']='M1_CIRCULARITY_CONTROL'
    c['decision_family_registry_sha256']=_registry_sha(c['decision_cases'])
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_low_donor_upper_bound_is_proven_impossible_not_failed_biology():
    c=config(20); c['decision_cases'][0]['available_donors_upper_bound']=2
    c['decision_family_registry_sha256']=_registry_sha(c['decision_cases'])
    out=m.build_prefreeze_manifest(c); row=out['case_resolution'][0]
    assert row['resolution_impossible_from_donor_upper_bound'] is True
    assert row['biological_result']=='NOT_OPENED'


def test_sufficient_upper_bound_does_not_claim_estimability():
    assert m.build_prefreeze_manifest(config(20))['case_resolution'][0]['estimability_proven'] is False


def test_duplicate_case_ids_rejected():
    c=config(2); c['decision_cases'][1]['case_id']=c['decision_cases'][0]['case_id']
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_authority_true_rejected():
    c=config(2); c['authority']['real_tournament_authorized']=True
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_empty_family_rejected():
    c=config(1); c['decision_cases']=[]
    with pytest.raises(m.PrefreezeError): m.build_prefreeze_manifest(c)


def test_manifest_hash_is_deterministic_and_outcome_free():
    a=m.build_prefreeze_manifest(config(3)); b=m.build_prefreeze_manifest(config(3))
    assert a['manifest_sha256']==b['manifest_sha256']
    assert 'outcome' not in str(a).lower()


@pytest.mark.parametrize('bad_alpha', ['0.05', True, False, float('nan'), float('inf'), float('-inf')])
def test_family_alpha_must_be_exact_finite_json_numeric_not_coerced(bad_alpha):
    c=config(3); c['family_alpha']=bad_alpha
    with pytest.raises(m.PrefreezeError):
        m.build_prefreeze_manifest(c)
