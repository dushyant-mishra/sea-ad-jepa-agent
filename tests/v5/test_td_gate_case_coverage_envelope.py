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
        'decision_family_size':1,
        'decision_family_registry_sha256':'a'*64,
        'alpha_eff':0.05,
        'minimum_nonzero_donors_for_sign_resolution':6,
        'minimum_permutation_draws_for_resolution':19,
        'tournament_contract_sha256':'b'*64,
        'null_seed_material':'seed',
        'case_resolution':[
            {
                'case_id':'c1',
                'candidate_id':'C1_RELATIONAL_SHARED',
                'gate_id':'G1_DONOR_PRIMARY',
                'source':'HVS',
                'analysis_tier':'discovery',
                'endpoint_id':'recurrence',
                'available_donors_upper_bound':10,
                'resolution_impossible_from_donor_upper_bound':False,
                'estimability_proven':False,
                'biological_result':'NOT_OPENED',
            }
        ],
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
    out = dict(core)
    out['manifest_sha256'] = canonical(core)
    return out


def receipts():
    return [{
        'case_id':'c1',
        'candidate_id':'C1_RELATIONAL_SHARED',
        'gate_id':'G1_DONOR_PRIMARY',
        'source':'HVS',
        'analysis_tier':'discovery',
        'endpoint_id':'recurrence',
        'status':'PASS',
        'evidence_sha256':'1'*64,
    }]


def rehash(manifest):
    core = dict(manifest)
    core.pop('manifest_sha256', None)
    manifest['manifest_sha256'] = canonical(core)
    return manifest


def audit(p):
    return cov.audit_gate_case_coverage(
        p,
        candidate_id='C1_RELATIONAL_SHARED',
        gate_id='G1_DONOR_PRIMARY',
        case_receipts=receipts(),
    )


def test_coverage_rejects_rehashed_prefreeze_with_shadow_claim_field():
    p = prefreeze(); p['target_selected'] = True; rehash(p)
    with pytest.raises(cov.CoverageError):
        audit(p)


def test_coverage_rejects_rehashed_prefreeze_with_true_authority():
    p = prefreeze(); p['authority']['target_selection_authorized'] = True; rehash(p)
    with pytest.raises(cov.CoverageError):
        audit(p)


def test_coverage_rejects_rehashed_prefreeze_with_opened_biological_result():
    p = prefreeze(); p['case_resolution'][0]['biological_result'] = 'PASS'; rehash(p)
    with pytest.raises(cov.CoverageError):
        audit(p)
