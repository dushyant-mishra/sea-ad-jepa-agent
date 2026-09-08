from __future__ import annotations
from dataclasses import MISSING, fields
import copy
import pytest
import torch

from sea_ad_jepa.v4.ipb_jepa import IPBEncoder
from sea_ad_jepa.v5.data_first_geometry import pack_valid_tokens
from sea_ad_jepa.v5.keyed_ipb_proof_v1 import KeyedIPBEncoderProofV1
from sea_ad_jepa.v5.schedule_authority_v1 import (
    QUALIFICATION_MECHANICS_V1,
    ProductionScheduleAuthorityV1,
)


def _models():
    torch.manual_seed(123)
    v4=IPBEncoder(
        width=32,heads=4,blocks=2,ffn_width=64,dropout=.10,
        gradient_checkpointing=False,vocabulary_size=64,
    )
    keyed=KeyedIPBEncoderProofV1(
        vocabulary_size=64,width=32,heads=4,blocks=2,ffn_width=64,
        dropout_numerator=1,dropout_denominator=10,
    )
    keyed.load_state_dict(v4.state_dict(),strict=True)
    return v4,keyed


def test_keyed_proof_encoder_is_parameter_state_compatible_with_v4():
    v4,keyed=_models()
    assert tuple(v4.state_dict())==tuple(keyed.state_dict())
    for name,value in v4.state_dict().items():
        assert torch.equal(value,keyed.state_dict()[name])


def test_train_mode_dense_and_packed_keyed_states_and_gradients_are_close():
    _,base=_models()
    dense=copy.deepcopy(base).train()
    packed=copy.deepcopy(base).train()

    batch,vocab=2,64
    measured=torch.zeros((batch,vocab),dtype=torch.bool)
    measured[:,torch.tensor([0,1,2,3,5,7,8,10,12,13,14,17,19,22,24,26,29,31,34,37,40,44,47,51,55,58,60,63])]=True
    hidden=torch.zeros_like(measured)
    hidden[0,torch.tensor([0,3,8,13,19,29,40,55])]=True
    hidden[1,torch.tensor([1,5,10,14,22,31,47,60])]=True
    expression=torch.randn(batch,vocab)
    expression[~measured]=0
    gene_ids=torch.arange(vocab,dtype=torch.int64).expand(batch,-1)
    keys=torch.tensor([1234567,7654321],dtype=torch.int64)

    out_dense=dense(
        gene_ids,expression,measured,hidden,'student',
        cell_keys=keys,training_seed=8113002,update_index=7,view_index=2,
    )
    visible=measured & ~hidden
    p=pack_valid_tokens(expression,visible)
    true=torch.ones_like(p.canonical_gene_ids,dtype=torch.bool)
    zero=torch.zeros_like(true)
    out_packed=packed(
        p.canonical_gene_ids,p.expression,true,zero,'student',
        cell_keys=keys,training_seed=8113002,update_index=7,view_index=2,
    )

    assert torch.allclose(out_dense.cell_state,out_packed.cell_state,atol=5e-6,rtol=5e-6)
    for row in range(batch):
        ids=p.canonical_gene_ids[row]
        assert torch.allclose(
            out_dense.gene_states[row,ids],out_packed.gene_states[row],
            atol=5e-6,rtol=5e-6,
        )

    dense_loss=out_dense.cell_state.square().mean()
    packed_loss=out_packed.cell_state.square().mean()
    dense_loss.backward()
    packed_loss.backward()
    dense_grads=dict(dense.named_parameters())
    packed_grads=dict(packed.named_parameters())
    for name in dense_grads:
        gd=dense_grads[name].grad
        gp=packed_grads[name].grad
        assert (gd is None)==(gp is None),name
        if gd is not None:
            assert torch.allclose(gd,gp,atol=6e-6,rtol=6e-5),name


def test_adamw_can_amplify_near_zero_gradient_sign_difference():
    left=torch.nn.Parameter(torch.tensor([0.0]))
    right=torch.nn.Parameter(torch.tensor([0.0]))
    opt_left=torch.optim.AdamW([left],lr=1e-4,betas=(.9,.999),eps=1e-8,weight_decay=.01)
    opt_right=torch.optim.AdamW([right],lr=1e-4,betas=(.9,.999),eps=1e-8,weight_decay=.01)
    left.grad=torch.tensor([1e-10])
    right.grad=torch.tensor([-1e-10])
    assert abs(float(left.grad-right.grad))==pytest.approx(2e-10)
    opt_left.step(); opt_right.step()
    assert abs(float(left-right))>1e-6


def test_production_schedule_schema_has_no_defaults():
    assert QUALIFICATION_MECHANICS_V1.effective_batch==128
    for field in fields(ProductionScheduleAuthorityV1):
        assert field.default is MISSING
        assert field.default_factory is MISSING


def test_production_schedule_requires_explicit_valid_values():
    with pytest.raises(TypeError):
        ProductionScheduleAuthorityV1()  # type: ignore[call-arg]
    bad=ProductionScheduleAuthorityV1(
        scientific_target_policy='SOURCE_DONOR_UNIFORM',
        proposal_policy='SOURCE_DONOR_UNIFORM',
        effective_cells_per_update=0,
        max_teacher_tokens_per_microbatch=1,
        masked_views_per_cell=1,
        evidence_policy_id='x',
        target_block_policy_id='y',
        training_presentations=1,
        ema_half_life_presentations=1,
        finite_relational_triplets_per_estimable_group=1,
        keyed_rng_authority_id='z',
    )
    with pytest.raises(ValueError):
        bad.validate()
