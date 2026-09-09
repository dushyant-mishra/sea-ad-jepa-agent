from __future__ import annotations
import math, random
import pytest, torch
from sea_ad_jepa.v5.keyed_rng_contract_v2 import keyed_dropout_u32, keyed_dropout_keep, philox4x32_10
from sea_ad_jepa.v5.keyed_rng_device_v1 import (
    dropout_threshold_u32,
    keyed_dropout_u32_tensor,
    keyed_dropout_u32_words_tensor,
    keyed_feature_dropout_device,
    philox4x32_10_words,
    split_signed_cell_keys,
)


def scalar_kw(cell, token, feature, **site):
    return dict(cell_key=cell, canonical_token_key=token, feature_index=feature, **site)


def base_site():
    return dict(run_seed=8_113_002, update_index=7, domain_index=2, view_index=4, layer_index=6, site_index=3)


def test_known_answer_matches_frozen_scalar_reference():
    z=torch.tensor(0,dtype=torch.int64)
    out=philox4x32_10_words(z,z,z,z,key0=0,key1=0)
    got=tuple(int(x) for x in out)
    assert got==philox4x32_10((0,0,0,0),(0,0))==(0x6627E8D5,0xE169C58D,0xBC57AC4C,0x9B00DBD8)


def test_randomized_signed_reader_fit_coordinate_parity():
    rng=random.Random(917)
    for _ in range(200):
        cells=[rng.randrange(0,2**63) for _ in range(rng.randrange(1,5))]
        toks=[[rng.randrange(-1,41238) for _ in range(rng.randrange(1,7))] for _ in cells]
        width=len(toks[0])
        if any(len(x)!=width for x in toks):
            toks=[x[:width] if len(x)>=width else x+[0]*(width-len(x)) for x in toks]
        f=rng.randrange(1,25)
        site=dict(run_seed=rng.randrange(2**32),update_index=rng.randrange(2**32),domain_index=rng.randrange(256),view_index=rng.randrange(256),layer_index=rng.randrange(256),site_index=rng.randrange(256))
        ct=torch.tensor(cells,dtype=torch.int64); tt=torch.tensor(toks,dtype=torch.int64)
        got=keyed_dropout_u32_tensor(cell_keys=ct,token_keys=tt,feature_count=f,**site)
        expected=torch.empty_like(got)
        for i,cell in enumerate(cells):
            for j,token in enumerate(toks[i]):
                for k in range(f): expected[i,j,k]=keyed_dropout_u32(**scalar_kw(cell,token,k,**site))
        assert torch.equal(got,expected)


def test_full_uint64_explicit_word_path_matches_scalar_reference():
    cells=[0,2**63-1,2**63,2**64-1,0x123456789ABCDEF0]
    lo=torch.tensor([x & 0xffffffff for x in cells],dtype=torch.int64)
    hi=torch.tensor([(x>>32)&0xffffffff for x in cells],dtype=torch.int64)
    tokens=torch.tensor([[-1,0,41237,65534]]*len(cells),dtype=torch.int64)
    site=base_site(); got=keyed_dropout_u32_words_tensor(cell_key_lo=lo,cell_key_hi=hi,token_keys=tokens,feature_count=4,**site)
    for i,cell in enumerate(cells):
        for j,token in enumerate(tokens[i].tolist()):
            for f in range(4): assert int(got[i,j,f])==keyed_dropout_u32(**scalar_kw(cell,token,f,**site))


def test_reader_fit_upper_key_is_safe_signed_int64():
    hi=9_223_371_444_004_343_451
    assert hi < 2**63
    x=torch.tensor([hi],dtype=torch.int64)
    lo,hh=split_signed_cell_keys(x)
    assert int(lo[0])==hi&0xffffffff and int(hh[0])==(hi>>32)&0xffffffff


def test_probability_threshold_is_exact_against_scalar_keep_decision_boundaries():
    words=[0,1,2,2**31-1,2**31,2**32-2,2**32-1]
    probs=[0.0,0.1,0.2,0.5,0.9999999999999999]
    # Include exact open-unit values and immediate representable neighbors.
    for w in words:
        u=(w+0.5)/2**32
        probs.extend([u,math.nextafter(u,0.0),math.nextafter(u,1.0)])
    for p in probs:
        if not 0.0<=p<1.0: continue
        t=dropout_threshold_u32(p)
        for w in words:
            assert (w>=t)==(((w+0.5)/2**32)>=p), (p,w,t)


def test_device_dropout_mask_and_values_match_scalar_reference_cpu():
    torch.manual_seed(11)
    values=torch.randn(3,5,7,dtype=torch.float64)
    cells=torch.tensor([91,12,9_223_371_444_004_343_451],dtype=torch.int64)
    tokens=torch.tensor([[-1,0,2,41237,17]]*3,dtype=torch.int64)
    site=base_site(); p=.137
    out=keyed_feature_dropout_device(values,cell_keys=cells,token_keys=tokens,probability=p,**site)
    exp=torch.empty_like(values)
    for i,cell in enumerate(cells.tolist()):
        for j,token in enumerate(tokens[i].tolist()):
            for f in range(values.shape[2]):
                keep=keyed_dropout_keep(probability=p,**scalar_kw(cell,token,f,**site))
                exp[i,j,f]=values[i,j,f]*(1.0 if keep else 0.0)/(1.0-p)
    assert torch.equal(out,exp)


def test_row_and_token_packing_invariance_is_exact():
    torch.manual_seed(12)
    v=torch.randn(4,6,9)
    cells=torch.tensor([88,11,999,5],dtype=torch.int64)
    tokens=torch.tensor([[-1,0,2,5,17,41]]*4,dtype=torch.int64)
    site=base_site(); p=.2
    full=keyed_feature_dropout_device(v,cell_keys=cells,token_keys=tokens,probability=p,**site)
    rows=torch.tensor([3,0,2]); cols=torch.tensor([5,0,3])
    packed=keyed_feature_dropout_device(v[rows][:,cols],cell_keys=cells[rows],token_keys=tokens[rows][:,cols],probability=p,**site)
    assert torch.equal(packed,full[rows][:,cols])


def test_gradient_is_exactly_mask_scaled_and_packing_invariant():
    torch.manual_seed(13)
    v=torch.randn(3,5,8,requires_grad=True)
    cells=torch.tensor([17,23,31],dtype=torch.int64); tokens=torch.tensor([[-1,0,1,5,8]]*3,dtype=torch.int64)
    site=base_site(); p=.25
    out=keyed_feature_dropout_device(v,cell_keys=cells,token_keys=tokens,probability=p,**site); out.sum().backward(); grad=v.grad.clone()
    rows=torch.tensor([2,0]); cols=torch.tensor([4,1,3]); vp=v.detach()[rows][:,cols].clone().requires_grad_(True)
    op=keyed_feature_dropout_device(vp,cell_keys=cells[rows],token_keys=tokens[rows][:,cols],probability=p,**site); op.sum().backward()
    assert torch.equal(vp.grad,grad[rows][:,cols])


def test_noop_modes_match_reference_validation_order_for_coordinates():
    v=torch.ones(1,1,1); cells=torch.tensor([1],dtype=torch.int64); tokens=torch.tensor([[65535]],dtype=torch.int64)
    site=base_site()
    # Frozen scalar tensor reference does not inspect coordinate ranges when no mask is sampled.
    assert keyed_feature_dropout_device(v,cell_keys=cells,token_keys=tokens,probability=0.0,**site) is v
    assert keyed_feature_dropout_device(v,cell_keys=cells,token_keys=tokens,probability=.5,training=False,**site) is v


def test_invalid_active_coordinates_fail_closed():
    v=torch.ones(1,1,1); site=base_site()
    with pytest.raises(ValueError): keyed_feature_dropout_device(v,cell_keys=torch.tensor([-1]),token_keys=torch.tensor([[0]]),probability=.1,**site)
    with pytest.raises(ValueError): keyed_feature_dropout_device(v,cell_keys=torch.tensor([1]),token_keys=torch.tensor([[65535]]),probability=.1,**site)
    with pytest.raises(ValueError): keyed_dropout_u32_words_tensor(cell_key_lo=torch.tensor([2**32]),cell_key_hi=torch.tensor([0]),token_keys=torch.tensor([[0]]),feature_count=1,**site)
    with pytest.raises(ValueError): keyed_dropout_u32_words_tensor(cell_key_lo=torch.tensor([0]),cell_key_hi=torch.tensor([0]),token_keys=torch.tensor([[0]]),feature_count=65537,**site)


def test_probability_rejects_nan_inf_and_one():
    for p in [float('nan'),float('inf'),-0.1,1.0]:
        with pytest.raises(ValueError): dropout_threshold_u32(p)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA qualification requires a real CUDA device")
def test_cuda_exact_word_and_mask_parity_against_cpu_scalar_reference():
    device=torch.device('cuda')
    cells=torch.tensor([1,91,9_223_371_444_004_343_451],dtype=torch.int64,device=device)
    tokens=torch.tensor([[-1,0,17,41237]]*3,dtype=torch.int64,device=device)
    values=torch.arange(3*4*13,dtype=torch.float32,device=device).reshape(3,4,13)/17
    site=base_site(); p=.17
    words=keyed_dropout_u32_tensor(cell_keys=cells,token_keys=tokens,feature_count=13,**site).cpu()
    for i,cell in enumerate(cells.cpu().tolist()):
        for j,token in enumerate(tokens.cpu()[i].tolist()):
            for f in range(13): assert int(words[i,j,f])==keyed_dropout_u32(**scalar_kw(cell,token,f,**site))
    out=keyed_feature_dropout_device(values,cell_keys=cells,token_keys=tokens,probability=p,**site).cpu()
    ref=keyed_feature_dropout_device(values.cpu(),cell_keys=cells.cpu(),token_keys=tokens.cpu(),probability=p,**site)
    assert torch.equal(out,ref)
