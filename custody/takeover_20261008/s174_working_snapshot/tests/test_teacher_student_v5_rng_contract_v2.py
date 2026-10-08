from __future__ import annotations
import itertools, random
import pytest, torch
from sea_ad_jepa.v5.keyed_rng_contract_v2 import (
    dropout_philox_address,keyed_dropout_keep,keyed_dropout_u32,
    keyed_feature_dropout_reference,philox4x32_10,
)


def test_philox_known_answer_zero_key_counter_v2():
    assert philox4x32_10((0,0,0,0),(0,0))==(0x6627E8D5,0xE169C58D,0xBC57AC4C,0x9B00DBD8)


def test_address_allocation_matches_declared_words():
    counter,key=dropout_philox_address(
        run_seed=8_113_002,update_index=40,domain_index=2,view_index=4,layer_index=6,site_index=3,
        cell_key=0x123456789ABCDEF0,canonical_token_key=41_237,feature_index=319,
    )
    assert key==(8_113_002,40)
    assert counter[0]==0x9ABCDEF0 and counter[1]==0x12345678
    assert counter[2]==(319<<16)|41_238
    assert counter[3]==(2<<24)|(3<<16)|(6<<8)|4


def test_address_is_injective_on_cartesian_attack_grid():
    seen=set()
    for update,domain,view,layer,site,cell,token,feature in itertools.product(
        (0,1),(0,1),(0,3),(0,5),(0,2),(11,2**63+17),(-1,0,41_237),(0,159,319)
    ):
        address=dropout_philox_address(
            run_seed=19,update_index=update,domain_index=domain,view_index=view,layer_index=layer,
            site_index=site,cell_key=cell,canonical_token_key=token,feature_index=feature,
        )
        assert address not in seen
        seen.add(address)


def test_actual_reader_fit_key_range_and_contract_bounds():
    lo=257_865_466_610; hi=9_223_371_444_004_343_451
    assert keyed_dropout_u32(run_seed=1,update_index=1,domain_index=0,view_index=0,layer_index=0,site_index=0,cell_key=lo,canonical_token_key=0,feature_index=0) != keyed_dropout_u32(run_seed=1,update_index=1,domain_index=0,view_index=0,layer_index=0,site_index=0,cell_key=hi,canonical_token_key=0,feature_index=0)
    with pytest.raises(ValueError):
        dropout_philox_address(run_seed=0,update_index=0,domain_index=0,view_index=0,layer_index=0,site_index=0,cell_key=0,canonical_token_key=65_535,feature_index=0)
    with pytest.raises(ValueError):
        dropout_philox_address(run_seed=0,update_index=0,domain_index=0,view_index=0,layer_index=0,site_index=0,cell_key=0,canonical_token_key=0,feature_index=65_536)


def test_reference_dropout_is_packing_and_row_order_invariant():
    torch.manual_seed(3)
    values=torch.randn(3,8,7)
    cells=torch.tensor([91,12,55],dtype=torch.int64)
    tokens=torch.tensor([[0,2,5,7,9,11,13,17]]*3,dtype=torch.int64)
    full=keyed_feature_dropout_reference(values,cell_keys=cells,token_keys=tokens,probability=.1,run_seed=77,update_index=4,domain_index=0,view_index=2,layer_index=1,site_index=2)
    keep_cols=torch.tensor([0,2,4,7])
    row_order=torch.tensor([2,0,1])
    packed=keyed_feature_dropout_reference(values[row_order][:,keep_cols],cell_keys=cells[row_order],token_keys=tokens[row_order][:,keep_cols],probability=.1,run_seed=77,update_index=4,domain_index=0,view_index=2,layer_index=1,site_index=2)
    assert torch.equal(packed,full[row_order][:,keep_cols])


def test_randomized_addresses_are_repeatable_and_coordinate_sensitive():
    rng=random.Random(41)
    for _ in range(1000):
        kw=dict(run_seed=rng.randrange(2**32),update_index=rng.randrange(2**20),domain_index=rng.randrange(4),view_index=rng.randrange(8),layer_index=rng.randrange(16),site_index=rng.randrange(8),cell_key=rng.randrange(2**63),canonical_token_key=rng.randrange(-1,41_238),feature_index=rng.randrange(320))
        assert keyed_dropout_u32(**kw)==keyed_dropout_u32(**kw)
        changed=dict(kw); changed['feature_index']=(kw['feature_index']+1)%320
        assert dropout_philox_address(**kw)!=dropout_philox_address(**changed)


def test_old_hash_rng_is_not_retained_as_competing_v5_authority():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    geometry=(root/'src/sea_ad_jepa/v5/data_first_geometry.py').read_text()
    assert '_HASH_PRIME' not in geometry
    assert 'def keyed_feature_dropout(' not in geometry
    contract=(root/'src/sea_ad_jepa/v5/keyed_rng_contract_v2.py').read_text()
    assert 'philox4x32_10' in contract
