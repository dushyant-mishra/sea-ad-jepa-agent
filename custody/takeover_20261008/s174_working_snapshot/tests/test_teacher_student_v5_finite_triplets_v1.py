from __future__ import annotations

import itertools
import time

import pytest

from sea_ad_jepa.v5.finite_relational_sampling import (
    anchored_triplet_capacity,
    map_triplet_keys_to_rows,
    sample_finite_anchored_triplet_keys,
    unrank_anchored_triplet,
)


def test_triplet_unranking_exactly_matches_small_exhaustive_canonical_order():
    for n in range(3, 9):
        expected=[]
        for anchor in range(n):
            others=[x for x in range(n) if x != anchor]
            expected.extend((anchor,j,k) for j,k in itertools.combinations(others,2))
        observed=[unrank_anchored_triplet(rank,n) for rank in range(anchored_triplet_capacity(n))]
        assert observed == expected


def test_finite_triplet_sampler_is_order_invariant_unique_and_budgeted():
    cells=[81,4,17,55,2,99,101]
    a=sample_finite_anchored_triplet_keys(cells,triplet_budget=17,authority_seed=123,update_index=9,group_key='D1|O2')
    b=sample_finite_anchored_triplet_keys(list(reversed(cells)),triplet_budget=17,authority_seed=123,update_index=9,group_key='D1|O2')
    assert a == b
    assert a.realized_count == 17
    assert len(set(a.sampled_ranks)) == 17
    assert len(set(a.triplet_cell_keys)) == 17
    for i,j,k in a.triplet_cell_keys:
        assert len({i,j,k}) == 3
        assert j < k


def test_finite_sampler_changes_with_authority_identity_but_not_compute_order():
    cells=list(range(20))
    base=sample_finite_anchored_triplet_keys(cells,triplet_budget=32,authority_seed=7,update_index=1,group_key='D|O')
    assert base != sample_finite_anchored_triplet_keys(cells,triplet_budget=32,authority_seed=8,update_index=1,group_key='D|O')
    assert base != sample_finite_anchored_triplet_keys(cells,triplet_budget=32,authority_seed=7,update_index=2,group_key='D|O')
    assert base != sample_finite_anchored_triplet_keys(cells,triplet_budget=32,authority_seed=7,update_index=1,group_key='D|O2')


def test_finite_sampler_has_no_default_budget_and_handles_huge_capacity_without_enumeration():
    with pytest.raises(TypeError):
        sample_finite_anchored_triplet_keys([1,2,3],authority_seed=1,update_index=1,group_key='g')  # type: ignore[call-arg]
    cells=list(range(42_209))
    start=time.perf_counter()
    sample=sample_finite_anchored_triplet_keys(cells,triplet_budget=64,authority_seed=5,update_index=3,group_key='max')
    elapsed=time.perf_counter()-start
    assert sample.capacity == 37_597_098_110_352
    assert sample.realized_count == 64
    assert elapsed < 2.0


def test_triplet_key_mapping_is_compute_order_independent_and_v4_comparator_canonical():
    keys=[100,200,300,400]
    sampled=sample_finite_anchored_triplet_keys(keys,triplet_budget=7,authority_seed=2,update_index=4,group_key='g')
    rows_a=map_triplet_keys_to_rows(sampled.triplet_cell_keys,[100,200,300,400])
    rows_b=map_triplet_keys_to_rows(sampled.triplet_cell_keys,[400,100,300,200])
    assert len(rows_a)==len(rows_b)==7
    assert all(j<k for _,j,k in rows_a)
    assert all(j<k for _,j,k in rows_b)
    back_a={( [100,200,300,400][i], *sorted(([100,200,300,400][j],[100,200,300,400][k])) ) for i,j,k in rows_a}
    back_b={( [400,100,300,200][i], *sorted(([400,100,300,200][j],[400,100,300,200][k])) ) for i,j,k in rows_b}
    assert back_a == back_b == set(sampled.triplet_cell_keys)


def test_non_estimable_relational_group_returns_empty_not_global_failure():
    sample=sample_finite_anchored_triplet_keys([11,12],triplet_budget=64,authority_seed=2,update_index=1,group_key='tiny')
    assert sample.capacity==0 and sample.realized_count==0 and sample.triplet_cell_keys==()
