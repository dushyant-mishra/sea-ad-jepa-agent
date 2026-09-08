from __future__ import annotations
import importlib
import random
import torch

import sea_ad_jepa.v5 as v5
from sea_ad_jepa.v5.finite_relational_sampling import (
    anchored_triplet_capacity,
    sample_finite_anchored_triplet_keys,
    unrank_anchored_triplet,
)
from sea_ad_jepa.v5.keyed_dropout_prototype import keyed_feature_dropout_reference
from sea_ad_jepa.v5.keyed_rng_reference import dropout_counter_words, philox4x32_10


def test_package_imports_only_live_canonical_modules():
    for name in (
        "data_first_geometry",
        "finite_relational_sampling",
        "keyed_rng_reference",
        "keyed_dropout_prototype",
        "schedule_authority_v1",
        "support_geometry_v1",
        "data_contract_v2",
    ):
        importlib.import_module(f"sea_ad_jepa.v5.{name}")
    assert hasattr(v5,"sample_finite_anchored_triplet_keys")
    assert hasattr(v5,"ProductionDataContractV2")


def test_philox_random123_known_answer_and_uint64_cell_identity():
    assert philox4x32_10((0,0,0,0),(0,0)) == (
        0x6627E8D5,0xE169C58D,0xBC57AC4C,0x9B00DBD8
    )
    lo=257_865_466_610
    hi=9_223_371_444_004_343_451
    assert dropout_counter_words(cell_key=lo,canonical_token_key=41_237,feature_index=159) != dropout_counter_words(cell_key=hi,canonical_token_key=41_237,feature_index=159)


def test_finite_sampler_handles_max_observed_group_without_enumeration():
    keys=list(range(1_000_000,1_000_000+42_209))
    a=sample_finite_anchored_triplet_keys(keys,triplet_budget=128,authority_seed=7,update_index=11,group_key="SEA_AD::MAX")
    random.Random(19).shuffle(keys)
    b=sample_finite_anchored_triplet_keys(keys,triplet_budget=128,authority_seed=7,update_index=11,group_key="SEA_AD::MAX")
    assert a.triplet_cell_keys==b.triplet_cell_keys
    assert a.sampled_ranks==b.sampled_ranks
    assert a.realized_count==128
    assert a.capacity==anchored_triplet_capacity(42_209)
    assert len(set(a.triplet_cell_keys))==128


def test_triplet_unranking_boundaries_are_valid():
    n=42_209
    cap=anchored_triplet_capacity(n)
    for rank in (0,1,cap//2,cap-2,cap-1):
        i,j,k=unrank_anchored_triplet(rank,n)
        assert 0<=i<n and 0<=j<k<n
        assert i not in (j,k)


def test_keyed_dropout_proof_is_packing_and_row_order_invariant():
    torch.manual_seed(3)
    x=torch.randn(2,5,8)
    token=torch.tensor([[-1,0,4,9,11],[-1,0,4,9,11]],dtype=torch.int64)
    cells=torch.tensor([257_865_466_610,9_223_371_444_004_343_451],dtype=torch.int64)
    full=keyed_feature_dropout_reference(x,cell_keys=cells,token_keys=token,probability=.1,run_seed=77,update_index=5,view_index=2,layer_index=1,site_index=0,training=True)
    select=torch.tensor([4,0,2])
    packed=keyed_feature_dropout_reference(x[:,select],cell_keys=cells,token_keys=token[:,select],probability=.1,run_seed=77,update_index=5,view_index=2,layer_index=1,site_index=0,training=True)
    assert torch.equal(packed,full[:,select])
    rerow=keyed_feature_dropout_reference(x.flip(0),cell_keys=cells.flip(0),token_keys=token.flip(0),probability=.1,run_seed=77,update_index=5,view_index=2,layer_index=1,site_index=0,training=True)
    assert torch.equal(rerow,full.flip(0))
