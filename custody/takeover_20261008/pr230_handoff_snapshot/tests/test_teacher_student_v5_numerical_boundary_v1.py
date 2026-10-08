from __future__ import annotations
import pytest
import torch
from sea_ad_jepa.v4.ipb_jepa import IPBEncoder
from sea_ad_jepa.v5.data_first_geometry import pack_valid_tokens


def test_ordinary_train_dropout_is_not_packing_invariant_negative_control():
    torch.manual_seed(123)
    vocab=48
    measured=torch.zeros((2,vocab),dtype=torch.bool)
    measured[:,torch.tensor([0,1,3,4,7,8,10,13,16,20,23,27,31,35,39,42,46])]=True
    expression=torch.randn(2,vocab); expression[~measured]=0
    dense=IPBEncoder(width=32,heads=4,blocks=2,ffn_width=64,dropout=.10,gradient_checkpointing=False,vocabulary_size=vocab).train()
    packed=IPBEncoder(width=32,heads=4,blocks=2,ffn_width=64,dropout=.10,gradient_checkpointing=False,vocabulary_size=vocab).train(); packed.load_state_dict(dense.state_dict())
    ids=torch.arange(vocab,dtype=torch.int64).expand(2,-1)
    pt=pack_valid_tokens(expression,measured); valid=torch.ones_like(pt.canonical_gene_ids,dtype=torch.bool)
    torch.manual_seed(999); d=dense(ids,expression,measured,torch.zeros_like(measured),'target')
    torch.manual_seed(999); p=packed(pt.canonical_gene_ids,pt.expression,valid,torch.zeros_like(valid),'target')
    assert float((d.cell_state-p.cell_state).abs().max().detach()) > 1e-3


def test_adamw_can_amplify_near_zero_gradient_sign_difference():
    left=torch.nn.Parameter(torch.tensor([0.0])); right=torch.nn.Parameter(torch.tensor([0.0]))
    ol=torch.optim.AdamW([left],lr=1e-4,betas=(.9,.999),eps=1e-8,weight_decay=.01)
    or_=torch.optim.AdamW([right],lr=1e-4,betas=(.9,.999),eps=1e-8,weight_decay=.01)
    left.grad=torch.tensor([1e-10]); right.grad=torch.tensor([-1e-10])
    assert abs(float(left.grad-right.grad))==pytest.approx(2e-10)
    ol.step(); or_.step()
    assert abs(float((left-right).detach()))>1e-6
