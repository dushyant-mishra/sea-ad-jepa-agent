import hashlib, importlib.util, json, sys
from pathlib import Path
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


def raw_cases(n=20):
    candidates=['C1_RELATIONAL_SHARED','C2_QUERY_MEASURED','C3_LEARNED_SHARED','C4_STRUCTURED_COMPOSITE']
    sources=['HVS','NPH52','SEA_AD']
    return [{
        'case_id':f'case_{i:02d}',
        'candidate_id':candidates[i%4],
        'gate_id':f'G{i%7+1}_FIXTURE',
        'source':sources[i%3],
        'analysis_tier':f'tier_{i//12}',
        'endpoint_id':f'endpoint_{i}',
        'available_donors_upper_bound':10,
    } for i in range(n)]


def config(n=20):
    cases=raw_cases(n)
    return {
        'schema':'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_CONFIG_V1',
        'fixture_only':True,
        'family_alpha':0.05,
        'multiplicity_method':'BONFERRONI',
        'tournament_contract_sha256':'a'*64,
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
