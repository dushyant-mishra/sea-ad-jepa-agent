import hashlib
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts' / 'v5'
sys.path.insert(0, str(SCRIPTS))

import td_gate_case_coverage as cov


def canonical(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    ).hexdigest()


def prefreeze():
    core = {
        'schema':'JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_MANIFEST_V1',
        'fixture_only':True,
        'family_alpha':0.05,
        'multiplicity_method':'BONFERRONI',
        'decision_family_size':2,
        'decision_family_registry_sha256':'a'*64,
        'alpha_eff':0.025,
        'minimum_nonzero_donors_for_sign_resolution':7,
        'minimum_permutation_draws_for_resolution':39,
        'tournament_contract_sha256':'b'*64,
        'null_seed_material':'seed',
        'case_resolution':[
            {
                'case_id':'c_hvs','candidate_id':'C1_RELATIONAL_SHARED',
                'gate_id':'G1_DONOR_PRIMARY','source':'HVS',
                'analysis_tier':'discovery','endpoint_id':'recurrence',
                'available_donors_upper_bound':20,
                'resolution_impossible_from_donor_upper_bound':False,
                'estimability_proven':False,'biological_result':'NOT_OPENED',
            },
            {
                'case_id':'c_nph','candidate_id':'C1_RELATIONAL_SHARED',
                'gate_id':'G1_DONOR_PRIMARY','source':'NPH52',
                'analysis_tier':'discovery','endpoint_id':'recurrence',
                'available_donors_upper_bound':16,
                'resolution_impossible_from_donor_upper_bound':False,
                'estimability_proven':False,'biological_result':'NOT_OPENED',
            },
        ],
        'authority':{
            'value_read_authorized':False,'real_tournament_authorized':False,
            'target_selection_authorized':False,
            'representation_selection_authorized':False,'td60_authorized':False,
            'stage4_authorized':False,'training_authorized':False,
        },
    }
    out = dict(core)
    out['manifest_sha256'] = canonical(core)
    return out


def receipt(case_id, source):
    return {
        'case_id':case_id,'candidate_id':'C1_RELATIONAL_SHARED',
        'gate_id':'G1_DONOR_PRIMARY','source':source,
        'analysis_tier':'discovery','endpoint_id':'recurrence',
        'status':'PASS','evidence_sha256':'1'*64,
    }


def rehash(manifest):
    core = dict(manifest); core.pop('manifest_sha256', None)
    manifest['manifest_sha256'] = canonical(core)


def audit(manifest, expected_sha, receipts):
    return cov.audit_gate_case_coverage(
        manifest,
        expected_prefreeze_manifest_sha256=expected_sha,
        candidate_id='C1_RELATIONAL_SHARED',
        gate_id='G1_DONOR_PRIMARY',
        case_receipts=receipts,
    )


def test_external_pin_accepts_exact_frozen_manifest():
    p = prefreeze()
    out = audit(
        p, p['manifest_sha256'],
        [receipt('c_hvs','HVS'), receipt('c_nph','NPH52')]
    )
    assert out['coverage_complete'] is True


def test_external_pin_rejects_self_consistently_rehashed_case_removal():
    p = prefreeze(); frozen_sha = p['manifest_sha256']
    p['case_resolution'] = [p['case_resolution'][0]]
    p['decision_family_size'] = 1
    rehash(p)
    with pytest.raises(cov.CoverageError):
        audit(p, frozen_sha, [receipt('c_hvs','HVS')])


def test_external_pin_rejects_self_consistently_rehashed_role_change():
    p = prefreeze(); frozen_sha = p['manifest_sha256']
    p['case_resolution'][0]['source'] = 'SEA_AD'
    rehash(p)
    with pytest.raises(cov.CoverageError):
        audit(
            p, frozen_sha,
            [receipt('c_hvs','SEA_AD'), receipt('c_nph','NPH52')]
        )


def test_external_pin_must_be_lowercase_sha256():
    p = prefreeze()
    with pytest.raises(cov.CoverageError):
        audit(p, 'not-a-sha', [receipt('c_hvs','HVS'), receipt('c_nph','NPH52')])
