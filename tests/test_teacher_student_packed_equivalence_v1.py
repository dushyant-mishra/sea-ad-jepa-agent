from __future__ import annotations
import torch
from sea_ad_jepa.v4.ipb_jepa import IPBEncoder, BlockPredictor, TargetBlocks, gather_block_states, block_jepa_loss
from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.data_first_geometry import pack_valid_tokens, mean_loss_weight

def _packed_teacher_blocks(blocks: TargetBlocks, measured_ids: torch.Tensor) -> TargetBlocks:
    local=torch.empty_like(blocks.indices)
    for row in range(len(measured_ids)):
        safe=blocks.indices[row].clamp_min(0)
        mapped=torch.searchsorted(measured_ids[row],safe)
        local[row]=torch.where(blocks.member_mask[row],mapped,torch.full_like(mapped,-1))
    return TargetBlocks(
        hidden_mask=torch.zeros((len(measured_ids),measured_ids.shape[1]),dtype=torch.bool),
        indices=local,
        member_mask=blocks.member_mask.clone(),
        fallback_counts=blocks.fallback_counts.clone(),
    )

def test_dense_and_packed_valid_outputs_and_block_loss_match_in_eval_mode():
    torch.manual_seed(41)
    vocab=64
    batch=2
    measured=torch.zeros((batch,vocab),dtype=torch.bool)
    measured[:, torch.tensor([0,1,2,3,5,7,8,10,12,13,14,17,19,22,24,26,29,31,34,37,40,44,47,51,55,58,60,63])] = True
    expression=torch.randn(batch,vocab)
    expression[~measured]=0
    keys=torch.tensor([101,202],dtype=torch.int64)
    blocks=sample_uniform_target_blocks(
        measured, production_seed=77, cell_indices=keys, sample_pass=2, view_index=1,
        mask_fraction=.40, block_count=4,
    )
    encoder=IPBEncoder(width=32,heads=4,blocks=2,ffn_width=64,dropout=.10,gradient_checkpointing=False,vocabulary_size=vocab).eval()
    predictor=BlockPredictor(identity_dim=48,width=32,heads=4).eval()
    ids=torch.arange(vocab,dtype=torch.int64).expand(batch,-1)
    with torch.no_grad():
        dense_t=encoder(ids,expression,measured,torch.zeros_like(measured),'target')
        dense_s=encoder(ids,expression,measured,blocks.hidden_mask,'student')
        dense_pred=predictor(encoder.tokenizer.gene_identity,blocks,dense_s.gene_states,dense_s.cell_state,measured & ~blocks.hidden_mask)
        dense_target=gather_block_states(dense_t.gene_states,blocks)
        dense_loss=block_jepa_loss(dense_pred,dense_target)

        pt=pack_valid_tokens(expression,measured)
        true_t=torch.ones_like(pt.canonical_gene_ids,dtype=torch.bool)
        packed_t=encoder(pt.canonical_gene_ids,pt.expression,true_t,torch.zeros_like(true_t),'target')
        visible=measured & ~blocks.hidden_mask
        ps=pack_valid_tokens(expression,visible)
        true_s=torch.ones_like(ps.canonical_gene_ids,dtype=torch.bool)
        packed_s=encoder(ps.canonical_gene_ids,ps.expression,true_s,torch.zeros_like(true_s),'student')
        packed_pred=predictor(encoder.tokenizer.gene_identity,blocks,packed_s.gene_states,packed_s.cell_state,true_s)
        pblocks=_packed_teacher_blocks(blocks,pt.canonical_gene_ids)
        packed_target=gather_block_states(packed_t.gene_states,pblocks)
        packed_loss=block_jepa_loss(packed_pred,packed_target)

    assert torch.allclose(dense_t.cell_state,packed_t.cell_state,atol=3e-6,rtol=3e-6)
    assert torch.allclose(dense_s.cell_state,packed_s.cell_state,atol=3e-6,rtol=3e-6)
    for row in range(batch):
        mids=pt.canonical_gene_ids[row]
        vids=ps.canonical_gene_ids[row]
        assert torch.allclose(dense_t.gene_states[row,mids],packed_t.gene_states[row],atol=3e-6,rtol=3e-6)
        assert torch.allclose(dense_s.gene_states[row,vids],packed_s.gene_states[row],atol=3e-6,rtol=3e-6)
    assert torch.allclose(dense_pred,packed_pred,atol=4e-6,rtol=4e-6)
    assert torch.allclose(dense_target,packed_target,atol=4e-6,rtol=4e-6)
    assert abs(float(dense_loss-packed_loss)) < 2e-6

def test_target_element_weighting_is_partition_invariant_for_unequal_microbatches():
    torch.manual_seed(9)
    values=torch.randn(23)
    full=values.square().mean()
    pieces=[values[:3],values[3:10],values[10:]]
    reconstructed=sum(
        p.square().mean()*mean_loss_weight(local_elements=p.numel(),total_elements=values.numel())
        for p in pieces
    )
    assert torch.allclose(full,reconstructed,atol=1e-7,rtol=1e-7)
    equal_microbatch_average=sum(p.square().mean() for p in pieces)/len(pieces)
    assert not torch.allclose(full,equal_microbatch_average,atol=1e-4,rtol=1e-4)
