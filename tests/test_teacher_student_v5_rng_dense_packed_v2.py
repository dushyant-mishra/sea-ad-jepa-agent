from __future__ import annotations
import torch
from sea_ad_jepa.v4.ipb_jepa import IPBEncoder
from sea_ad_jepa.v5.data_first_geometry import pack_valid_tokens
from sea_ad_jepa.v5.keyed_dropout_prototype_v2 import KeyedIPBEncoderV2Reference


def _make_case():
    torch.manual_seed(601)
    batch,vocab=2,24
    measured=torch.zeros((batch,vocab),dtype=torch.bool)
    measured[:,torch.tensor([0,1,3,4,7,9,11,13,16,19,21,23])]=True
    expression=torch.randn(batch,vocab); expression[~measured]=0
    ids=torch.arange(vocab,dtype=torch.int64).expand(batch,-1)
    cells=torch.tensor([7_001,9_223_371_444_004_343_451],dtype=torch.int64)
    return batch,vocab,measured,expression,ids,cells


def test_v2_reference_state_dict_is_v4_encoder_compatible():
    _,vocab,_,_,_,_=_make_case()
    v4=IPBEncoder(width=16,heads=4,blocks=1,ffn_width=24,dropout=.10,gradient_checkpointing=False,vocabulary_size=vocab)
    v5=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.10,vocabulary_size=vocab)
    assert v4.state_dict().keys()==v5.state_dict().keys()
    v5.load_state_dict(v4.state_dict(),strict=True)


def test_v2_exact_philox_reference_train_dense_packed_states_match():
    _,vocab,measured,expression,ids,cells=_make_case()
    dense=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.20,vocabulary_size=vocab).train()
    packed=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.20,vocabulary_size=vocab).train(); packed.load_state_dict(dense.state_dict(),strict=True)
    pt=pack_valid_tokens(expression,measured); true=torch.ones_like(pt.canonical_gene_ids,dtype=torch.bool)
    d=dense(ids,expression,measured,torch.zeros_like(measured),'target',cell_keys=cells,run_seed=8_113_002,update_index=7,view_index=0)
    p=packed(pt.canonical_gene_ids,pt.expression,true,torch.zeros_like(true),'target',cell_keys=cells,run_seed=8_113_002,update_index=7,view_index=0)
    assert torch.allclose(d.cell_state,p.cell_state,atol=3e-6,rtol=3e-6)
    for row in range(len(cells)):
        assert torch.allclose(d.gene_states[row,pt.canonical_gene_ids[row]],p.gene_states[row],atol=3e-6,rtol=3e-6)


def test_v2_exact_philox_reference_train_dense_packed_gradients_match():
    _,vocab,measured,expression,ids,cells=_make_case()
    dense=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.20,vocabulary_size=vocab).train()
    packed=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.20,vocabulary_size=vocab).train(); packed.load_state_dict(dense.state_dict(),strict=True)
    pt=pack_valid_tokens(expression,measured); true=torch.ones_like(pt.canonical_gene_ids,dtype=torch.bool)
    d=dense(ids,expression,measured,torch.zeros_like(measured),'target',cell_keys=cells,run_seed=8_113_002,update_index=9,view_index=0)
    p=packed(pt.canonical_gene_ids,pt.expression,true,torch.zeros_like(true),'target',cell_keys=cells,run_seed=8_113_002,update_index=9,view_index=0)
    loss_d=d.cell_state.square().mean()
    for row in range(len(cells)):
        loss_d=loss_d+d.gene_states[row,pt.canonical_gene_ids[row]].square().mean()/len(cells)
    loss_p=p.cell_state.square().mean()+p.gene_states.square().mean()
    loss_d.backward(); loss_p.backward()
    assert torch.allclose(loss_d.detach(),loss_p.detach(),atol=4e-6,rtol=4e-6)
    dg=dict(dense.named_parameters()); pg=dict(packed.named_parameters()); assert dg.keys()==pg.keys()
    for name in dg:
        assert dg[name].grad is not None and pg[name].grad is not None,name
        assert torch.allclose(dg[name].grad,pg[name].grad,atol=2e-5,rtol=2e-5),name


def _packed_teacher_blocks(blocks, measured_ids):
    from sea_ad_jepa.v4.ipb_jepa import TargetBlocks
    local=torch.empty_like(blocks.indices)
    for row in range(len(measured_ids)):
        safe=blocks.indices[row].clamp_min(0)
        mapped=torch.searchsorted(measured_ids[row],safe)
        local[row]=torch.where(blocks.member_mask[row],mapped,torch.full_like(mapped,-1))
    return TargetBlocks(
        hidden_mask=torch.zeros((len(measured_ids),measured_ids.shape[1]),dtype=torch.bool),
        indices=local,member_mask=blocks.member_mask.clone(),fallback_counts=blocks.fallback_counts.clone(),
    )


def test_v2_exact_philox_full_block_jepa_dense_packed_loss_and_gradients_match():
    from sea_ad_jepa.v4.ipb_jepa import BlockPredictor, gather_block_states, block_jepa_loss
    from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
    _,vocab,measured,expression,ids,cells=_make_case()
    blocks=sample_uniform_target_blocks(measured,production_seed=401,cell_indices=cells,sample_pass=1,view_index=1,mask_fraction=.40,block_count=3)
    teacher_d=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.10,vocabulary_size=vocab).eval()
    teacher_p=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.10,vocabulary_size=vocab).eval(); teacher_p.load_state_dict(teacher_d.state_dict(),strict=True)
    student_d=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.15,vocabulary_size=vocab).train()
    student_p=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=1,ffn_width=24,dropout=.15,vocabulary_size=vocab).train(); student_p.load_state_dict(student_d.state_dict(),strict=True)
    pred_d=BlockPredictor(identity_dim=48,width=16,heads=4).train(); pred_p=BlockPredictor(identity_dim=48,width=16,heads=4).train(); pred_p.load_state_dict(pred_d.state_dict(),strict=True)
    with torch.no_grad():
        td=teacher_d(ids,expression,measured,torch.zeros_like(measured),'target',cell_keys=cells,run_seed=8_113_002,update_index=12,view_index=0)
        pt=pack_valid_tokens(expression,measured); true_t=torch.ones_like(pt.canonical_gene_ids,dtype=torch.bool)
        tp=teacher_p(pt.canonical_gene_ids,pt.expression,true_t,torch.zeros_like(true_t),'target',cell_keys=cells,run_seed=8_113_002,update_index=12,view_index=0)
    sd=student_d(ids,expression,measured,blocks.hidden_mask,'student',cell_keys=cells,run_seed=8_113_002,update_index=12,view_index=1)
    visible=measured & ~blocks.hidden_mask
    ps=pack_valid_tokens(expression,visible); true_s=torch.ones_like(ps.canonical_gene_ids,dtype=torch.bool)
    sp=student_p(ps.canonical_gene_ids,ps.expression,true_s,torch.zeros_like(true_s),'student',cell_keys=cells,run_seed=8_113_002,update_index=12,view_index=1)
    pd=pred_d(student_d.tokenizer.gene_identity,blocks,sd.gene_states,sd.cell_state,visible)
    pp=pred_p(student_p.tokenizer.gene_identity,blocks,sp.gene_states,sp.cell_state,true_s)
    yd=gather_block_states(td.gene_states,blocks); yp=gather_block_states(tp.gene_states,_packed_teacher_blocks(blocks,pt.canonical_gene_ids))
    ld=block_jepa_loss(pd,yd); lp=block_jepa_loss(pp,yp)
    assert torch.allclose(ld.detach(),lp.detach(),atol=5e-6,rtol=5e-6)
    ld.backward(); lp.backward()
    for left,right in ((student_d,student_p),(pred_d,pred_p)):
        a=dict(left.named_parameters()); b=dict(right.named_parameters()); assert a.keys()==b.keys()
        for name in a:
            assert a[name].grad is not None and b[name].grad is not None,name
            assert torch.allclose(a[name].grad,b[name].grad,atol=3e-5,rtol=3e-5),name
