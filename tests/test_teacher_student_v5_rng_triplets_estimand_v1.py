from __future__ import annotations
import itertools
import random
import pytest
import torch

from sea_ad_jepa.v5.keyed_rng_v1 import KeyedDropoutSpec, keyed_dropout_mask
from sea_ad_jepa.v5.finite_triplets_v1 import (
    anchored_triplet_capacity,
    sample_finite_anchored_triplets,
    unrank_anchored_triplet,
)
from sea_ad_jepa.v5.scientific_estimand_v1 import (
    EstimandPolicy,
    GroupCount,
    group_masses,
    importance_diagnostics,
)


def test_keyed_rng_is_packing_and_row_order_invariant():
    ids=torch.tensor([[-1,0,4,9,11],[-1,0,4,9,11]],dtype=torch.int64)
    keys=torch.tensor([123456,987654],dtype=torch.int64)
    full=keyed_dropout_mask(ids,keys,width=32,training_seed=77,update_index=5,view_index=2,site_id=19)
    select=torch.tensor([4,0,2])
    packed=keyed_dropout_mask(ids[:,select],keys,width=32,training_seed=77,update_index=5,view_index=2,site_id=19)
    assert torch.equal(packed,full[:,select])
    rerow=keyed_dropout_mask(ids.flip(0),keys.flip(0),width=32,training_seed=77,update_index=5,view_index=2,site_id=19)
    assert torch.equal(rerow,full.flip(0))


def test_keyed_rng_changes_on_authority_coordinates():
    ids=torch.tensor([[-1,1,2,3]],dtype=torch.int64)
    keys=torch.tensor([42],dtype=torch.int64)
    baseline=keyed_dropout_mask(ids,keys,width=64,training_seed=7,update_index=1,view_index=0,site_id=3)
    variants=[
        keyed_dropout_mask(ids,keys,width=64,training_seed=7,update_index=2,view_index=0,site_id=3),
        keyed_dropout_mask(ids,keys,width=64,training_seed=7,update_index=1,view_index=1,site_id=3),
        keyed_dropout_mask(ids,keys,width=64,training_seed=7,update_index=1,view_index=0,site_id=4),
    ]
    assert all(not torch.equal(baseline,v) for v in variants)


def test_keyed_rng_frequency_and_local_correlation_sanity():
    batch,tokens,width=128,64,32
    ids=torch.arange(tokens,dtype=torch.int64).repeat(batch,1)
    keys=torch.arange(1000,1000+batch,dtype=torch.int64)
    mask=keyed_dropout_mask(ids,keys,width=width,training_seed=8113002,update_index=91,view_index=3,site_id=17)
    keep=float(mask.float().mean())
    assert abs(keep-.9)<.004
    x=mask[:,:,:-1].float().reshape(-1)
    y=mask[:,:,1:].float().reshape(-1)
    corr=float(torch.corrcoef(torch.stack([x,y]))[0,1])
    assert abs(corr)<.02


def test_keyed_rng_fail_closed_inputs():
    with pytest.raises(ValueError):
        keyed_dropout_mask(torch.tensor([[-2]]),torch.tensor([1]),width=1,training_seed=1,update_index=1,view_index=1,site_id=1)
    with pytest.raises(ValueError):
        KeyedDropoutSpec(1,1).validate()


def test_triplet_unranking_matches_exhaustive_small_groups():
    for n in range(3,11):
        ids=list(range(10,10+n))
        expected=[]
        for anchor in ids:
            rest=[x for x in ids if x!=anchor]
            expected.extend((anchor,j,k) for j,k in itertools.combinations(rest,2))
        observed=[unrank_anchored_triplet(ids,r) for r in range(anchored_triplet_capacity(n))]
        assert observed==expected


def test_finite_triplet_sampler_large_group_is_permutation_invariant():
    ids=list(range(42_209))
    a=sample_finite_anchored_triplets(ids,max_triplets=64,seed=99,group_key='SEA_AD::x')
    random.Random(3).shuffle(ids)
    b=sample_finite_anchored_triplets(ids,max_triplets=64,seed=99,group_key='SEA_AD::x')
    assert a==b
    assert len(a)==64
    assert len(set(a))==64
    assert all(j<k and anchor not in (j,k) for anchor,j,k in a)


def test_finite_triplet_sampler_complete_when_capacity_below_budget():
    got=sample_finite_anchored_triplets([30,10,20],max_triplets=99,seed=7,group_key='g')
    assert got==((10,20,30),(20,10,30),(30,10,20))


def test_finite_triplet_sampler_authority_and_guardrails():
    ids=list(range(100))
    a=sample_finite_anchored_triplets(ids,max_triplets=32,seed=1,group_key='a')
    assert a!=sample_finite_anchored_triplets(ids,max_triplets=32,seed=2,group_key='a')
    assert a!=sample_finite_anchored_triplets(ids,max_triplets=32,seed=1,group_key='b')
    with pytest.raises(TypeError):
        sample_finite_anchored_triplets([1,2,3],seed=1,group_key='x')  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        sample_finite_anchored_triplets([1,1,2],max_triplets=3,seed=1,group_key='x')


def _rows():
    return [
        GroupCount('A','a1',0,10),
        GroupCount('A','a1',1,30),
        GroupCount('A','a2',2,60),
        GroupCount('B','b1',3,100),
    ]


def test_estimand_candidates_are_normalized_but_none_is_implicitly_selected():
    for policy in EstimandPolicy:
        assert sum(group_masses(_rows(),policy))==pytest.approx(1.0)


def test_estimand_candidate_semantics():
    rows=_rows()
    assert group_masses(rows,EstimandPolicy.CELL_UNIFORM)==pytest.approx((.05,.15,.30,.50))
    donor=group_masses(rows,EstimandPolicy.DONOR_UNIFORM)
    assert donor[0]==pytest.approx(1/12)
    assert donor[1]==pytest.approx(1/4)
    source_donor=group_masses(rows,EstimandPolicy.SOURCE_DONOR_UNIFORM)
    assert source_donor[0]==pytest.approx(1/16)
    assert source_donor[1]==pytest.approx(3/16)
    assert source_donor[3]==pytest.approx(.5)
    source_donor_operator=group_masses(rows,EstimandPolicy.SOURCE_DONOR_OPERATOR_UNIFORM)
    assert source_donor_operator[0]==pytest.approx(1/8)
    assert source_donor_operator[1]==pytest.approx(1/8)


def test_importance_diagnostics_identity_and_mismatch():
    for policy in EstimandPolicy:
        d=importance_diagnostics(_rows(),target=policy,proposal=policy)
        assert d['relative_ess']==pytest.approx(1.0)
        assert d['weight_range_ratio']==pytest.approx(1.0)
    d=importance_diagnostics(
        _rows(),
        target=EstimandPolicy.SOURCE_DONOR_UNIFORM,
        proposal=EstimandPolicy.CELL_UNIFORM,
    )
    assert d['expected_weight']==pytest.approx(1.0)
    assert d['relative_ess']<1.0
    assert d['weight_range_ratio']>1.0
