from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'v5'))

import td_relational_successor_gate_v1 as G


def _null_maps(donors, operators, *, n_null=64, seed=11):
    rng = np.random.default_rng(seed)
    donors = np.asarray(donors)
    operators = np.asarray(operators)
    maps=[]
    for _ in range(n_null):
        m=np.arange(len(donors))
        for d in np.unique(donors):
            for o in np.unique(operators[donors==d]):
                idx=np.where((donors==d)&(operators==o))[0]
                m[idx]=rng.permutation(idx)
        maps.append(m)
    return np.asarray(maps, dtype=int)


def _aligned_fixture(*, donors_n=5, cells_per_donor=34, seed=7):
    rng=np.random.default_rng(seed)
    n=donors_n*cells_per_donor
    donors=np.repeat([f'D{i}' for i in range(donors_n)], cells_per_donor)
    operators=np.zeros(n, dtype=int)
    rows=np.arange(n, dtype=int)
    latent=np.empty(n, float)
    for d in range(donors_n):
        idx=np.where(donors==f'D{d}')[0]
        latent[idx]=np.linspace(-2,2,cells_per_donor)+rng.normal(0,0.01,cells_per_donor)
    def dist(v):
        return np.abs(v[:,None]-v[None,:])
    z=dist(latent)
    x=dist(latent + rng.normal(0,0.002,n))
    y=dist(latent + rng.normal(0,0.002,n))
    return dict(
        source='UNIT', panel_id='P0', profile_id='aligned',
        z_distances=z, x_distances=x, y_distances=y,
        donor_ids=donors, operator_ids=operators, global_rows=rows,
        focal_mask=np.ones(n,bool), neighbor_pool_mask=np.ones(n,bool),
        null_y_identity_maps=_null_maps(donors,operators,seed=seed+100),
        min_focal_anchors_per_donor=1,
    )


def test_positive_recurrence_evaluates_all_five_scales_without_early_stop():
    r=G.evaluate_relational_profile(**_aligned_fixture())
    assert tuple(r.scale_results) == ('1/8','1/6','1/4','1/3','1/2')
    assert all(v.status == 'PASS' for v in r.scale_results.values())
    assert 'FINE_SCALE_RELATION_ESTABLISHED' in r.characterization
    assert 'MESOSCALE_RELATION_ESTABLISHED' in r.characterization
    assert all(v.n_observed_donors >= 5 for v in r.scale_results.values())
    assert all(v is False for v in r.authority.values())


def test_null_relation_fails_scoped_claims_but_returns_every_scale():
    f=_aligned_fixture(seed=19)
    rng=np.random.default_rng(222)
    ylatent=rng.normal(size=len(f['donor_ids']))
    f['y_distances']=np.abs(ylatent[:,None]-ylatent[None,:])
    r=G.evaluate_relational_profile(**f)
    assert len(r.scale_results)==5
    estimable=[v for v in r.scale_results.values() if v.status!='NOT_ESTIMABLE']
    assert estimable
    assert all(v.status=='FAIL' for v in estimable)
    assert 'NO_RELATION_ESTABLISHED' in r.characterization
    assert r.failure_scope == 'SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY'


def test_underpowered_fine_scales_are_not_estimable_not_fail():
    f=_aligned_fixture(cells_per_donor=18, seed=31)
    r=G.evaluate_relational_profile(**f)
    assert r.scale_results['1/8'].status=='NOT_ESTIMABLE'
    assert r.scale_results['1/6'].status=='NOT_ESTIMABLE'
    assert r.scale_results['1/2'].status in {'PASS','FAIL','NOT_ESTIMABLE'}
    assert not any(v.status=='FAIL' and v.reason=='INSUFFICIENT_SUPPORT' for v in r.scale_results.values())


def test_disconnected_rare_anchor_islands_are_not_forced_into_one_component():
    f=_aligned_fixture(seed=43)
    donors=np.asarray(f['donor_ids'])
    focal=np.zeros(len(donors),bool)
    for d in np.unique(donors):
        idx=np.where(donors==d)[0]
        focal[idx[[2,3,4,29,30,31]]]=True
    f['focal_mask']=focal
    f['profile_id']='two_islands'
    f['min_focal_anchors_per_donor']=3
    r=G.evaluate_relational_profile(**f)
    assert any(v.status=='PASS' for v in r.scale_results.values())
    assert r.focal_anchor_count == 30


def test_rare_increment_requires_program_margin_to_exceed_all_matched_controls():
    program=G.evaluate_relational_profile(**_aligned_fixture(seed=51))
    weak=_aligned_fixture(seed=52)
    rng=np.random.default_rng(905)
    ylatent=rng.normal(size=len(weak['donor_ids']))
    weak['y_distances']=np.abs(ylatent[:,None]-ylatent[None,:])
    weak['profile_id']='technical_control'
    control=G.evaluate_relational_profile(**weak)
    rr=G.adjudicate_rare_increment(program, {'technical':control})
    assert any(v.status=='PASS' for v in rr.scale_results.values())
    assert rr.failure_scope=='RARE_RELATIONAL_INCREMENT_ONLY'

    rr2=G.adjudicate_rare_increment(program, {'matched_common':program})
    assert all(v.status!='PASS' for v in rr2.scale_results.values())
    assert any(v.reason=='CONTROL_MATCHES_OR_EXCEEDS_PROGRAM' for v in rr2.scale_results.values() if v.status=='FAIL')


def test_null_maps_must_preserve_donor_operator_matching():
    f=_aligned_fixture(seed=61)
    bad=f['null_y_identity_maps'].copy()
    bad[0,0],bad[0,40]=bad[0,40],bad[0,0]
    f['null_y_identity_maps']=bad
    try:
        G.evaluate_relational_profile(**f)
    except G.RelationalGateError as e:
        assert 'donor/operator' in str(e)
    else:
        raise AssertionError('cross-donor null map was accepted')


def test_scale_dependent_geometry_keeps_fine_failures_separate_from_mesoscale_pass():
    f=_aligned_fixture(seed=71)
    z=f['z_distances']; x=f['x_distances']
    rng=np.random.default_rng(991)
    random_d=rng.uniform(0,4,size=x.shape)
    random_d=(random_d+random_d.T)/2
    np.fill_diagonal(random_d,0)
    y=x.copy()
    mask=(z<0.25)&(~np.eye(len(z),dtype=bool))
    y[mask]=random_d[mask]
    y=(y+y.T)/2
    f['y_distances']=y
    r=G.evaluate_relational_profile(**f)
    assert r.scale_results['1/8'].status=='FAIL'
    assert r.scale_results['1/3'].status=='FAIL'
    assert r.scale_results['1/2'].status=='PASS'
    assert 'MESOSCALE_RELATION_ESTABLISHED' in r.characterization
    assert 'SCALE_DEPENDENT_RELATION_ESTABLISHED' in r.characterization


def test_donor_restricted_true_program_does_not_require_zero_prevalence_donors_to_pass():
    f=_aligned_fixture(donors_n=8, seed=81)
    donors=np.asarray(f['donor_ids'])
    focal=np.zeros(len(donors),bool)
    for d in ['D0','D1','D2','D3','D4']:
        idx=np.where(donors==d)[0]
        focal[idx[[2,3,4,29,30,31]]]=True
    f['focal_mask']=focal
    f['profile_id']='donor_restricted_true'
    f['min_focal_anchors_per_donor']=3
    r=G.evaluate_relational_profile(**f)
    assert any(v.status=='PASS' for v in r.scale_results.values())
    for v in r.scale_results.values():
        if v.status!='NOT_ESTIMABLE':
            assert set(v.eligible_donors)=={'D0','D1','D2','D3','D4'}
