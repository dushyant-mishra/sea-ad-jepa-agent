from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v79'))
import build_td_relational_synthetic_package_v1 as G

EXPECTED={c[0] for c in G.CAPABILITIES}
FIT_FIELDS={'source','panel_id','z_distances','x_distances','y_distances','donor_ids','operator_ids','global_rows','focal_mask','neighbor_pool_mask','null_y_identity_maps','min_focal_anchors_per_donor'}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

@pytest.fixture(scope='module')
def pkg(tmp_path_factory):
    root=tmp_path_factory.mktemp('pkg')
    G.main(str(root))
    return root

def load(path): return json.loads(path.read_text())

def test_all_nine_capabilities_are_distinct_and_bound(pkg):
    b=load(pkg/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json')
    caps={r['capability_id']:r for r in b['capabilities']}
    assert set(caps)==EXPECTED
    assert len({r['challenge_id'] for r in caps.values()})==9
    assert all(v is False for v in b['authority'].values())

def test_fit_views_exactly_match_td316_blinded_input_surface(pkg):
    b=load(pkg/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json')
    for rec in b['fit_views']:
        path=pkg/'fit_views'/f"{rec['challenge_id']}.json"
        assert sha(path)==rec['sha256']
        fit=load(path)
        assert set(fit)==FIT_FIELDS
        text=path.read_text()
        for forbidden in ('REL_','expected_status','controller_truth','pseudo_rare','technical_twin','biological_relational_truth_present'):
            assert forbidden not in text
        n=len(fit['donor_ids'])
        assert len(set(fit['global_rows']))==n
        assert all((not f) or p for f,p in zip(fit['focal_mask'],fit['neighbor_pool_mask']))
        for key in ('z_distances','x_distances','y_distances'):
            a=np.asarray(fit[key])
            assert a.shape==(n,n)
            assert np.array_equal(a,a.T)
            assert np.all(np.diag(a)==0)
        maps=np.asarray(fit['null_y_identity_maps'],int)
        assert maps.shape==(64,n)
        donor=np.asarray(fit['donor_ids'],object); op=np.asarray(fit['operator_ids'],object)
        for m in maps:
            assert np.array_equal(np.sort(m),np.arange(n))
            assert np.all(donor[m]==donor) and np.all(op[m]==op)

def test_controller_truth_is_separate_explicit_and_hash_bound(pkg):
    b=load(pkg/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json')
    assert sha(pkg/'controller_truth.json')==b['controller_truth_sha256']
    c=load(pkg/'controller_truth.json')
    assert set(c['truth'])=={r['challenge_id'] for r in b['fit_views']}
    for rec in c['truth'].values():
        t=rec['planted_truth']
        assert 'latent_coordinates' in t
        assert 'biological_distance_matrix_sha256' in t
        assert len(t['biological_distance_matrix_sha256'])==64
        assert 'biological_relational_truth_present' in t

def test_source_visibility_stress_keeps_identical_latent_biology(pkg):
    b=load(pkg/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json')
    c=load(pkg/'controller_truth.json')
    cap={r['capability_id']:r['challenge_id'] for r in b['capabilities']}
    broad=c['truth'][cap['REL_BROAD_MESO_POSITIVE']]
    stress=c['truth'][cap['REL_SOURCE_VISIBILITY_STRESS']]
    assert broad['planted_truth']['latent_coordinates']==stress['planted_truth']['latent_coordinates']
    assert broad['paired_latent_truth_sha256']==stress['paired_latent_truth_sha256']
    assert broad['fit_view_sha256']!=stress['fit_view_sha256']

def test_donor_restricted_truth_has_five_active_and_exact_zero_donor(pkg):
    b=load(pkg/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json')
    c=load(pkg/'controller_truth.json')
    cap={r['capability_id']:r['challenge_id'] for r in b['capabilities']}
    t=c['truth'][cap['REL_DONOR_RESTRICTED_POSITIVE']]['planted_truth']
    assert len(t['active_donors'])==5
    assert len(t['zero_prevalence_donors'])>=1
    assert all(t['donor_prevalence'][d]==0 for d in t['zero_prevalence_donors'])

def test_technical_twin_and_null_have_no_biological_relational_truth(pkg):
    b=load(pkg/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json')
    c=load(pkg/'controller_truth.json')
    cap={r['capability_id']:r['challenge_id'] for r in b['capabilities']}
    tech=c['truth'][cap['REL_TECHNICAL_TWIN_NEGATIVE']]['planted_truth']
    null=c['truth'][cap['REL_NULL_NEGATIVE']]['planted_truth']
    assert tech['biological_relational_truth_present'] is False
    assert any(tech['pseudo_rare']) and not any(tech['rare_state'])
    assert null['biological_relational_truth_present'] is False

def test_underpowered_truth_is_real_but_below_five_donor_minimum(pkg):
    b=load(pkg/'TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json')
    c=load(pkg/'controller_truth.json')
    cap={r['capability_id']:r['challenge_id'] for r in b['capabilities']}
    cid=cap['REL_UNDERPOWERED_POSITIVE']
    t=c['truth'][cid]['planted_truth']
    fit=load(pkg/'fit_views'/f'{cid}.json')
    assert t['biological_relational_truth_present'] is True
    assert len(set(fit['donor_ids']))==4
    assert c['truth'][cid]['expected_status']=='NOT_ESTIMABLE'

def test_capability_ledger_does_not_overclaim_existing_worlds(pkg):
    ledger=load(pkg/'capability_ledger.json')
    assert {r['capability_id'] for r in ledger['capabilities']}==EXPECTED
    assert all(r['coverage_status']=='SATISFIED_NEW_PROSPECTIVE_WORLD' for r in ledger['capabilities'])
    assert all('explicit' in r['why_not_existing_world'].lower() for r in ledger['capabilities'])

def test_generation_is_byte_deterministic(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; G.main(str(a)); G.main(str(b))
    af={str(p.relative_to(a)):hashlib.sha256(p.read_bytes()).hexdigest() for p in a.rglob('*') if p.is_file()}
    bf={str(p.relative_to(b)):hashlib.sha256(p.read_bytes()).hexdigest() for p in b.rglob('*') if p.is_file()}
    assert af==bf
