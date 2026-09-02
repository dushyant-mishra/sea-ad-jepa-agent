from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch
import importlib

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.ema import create_ema_target  # noqa: E402
from sea_ad_jepa.v4.ipb_jepa import (  # noqa: E402
    BlockPredictor,
    CorrelationGraph,
    GeneAnchorDecoder,
    IPBEncoder,
    KernelLinearAttention,
    block_jepa_loss,
    build_train_pearson_graph,
    gather_block_states,
    gene_anchor_loss,
    hidden_gene_indices,
    sample_target_blocks,
)


def small_graph(genes: int = 20) -> CorrelationGraph:
    neighbors = []
    weights = []
    for gene in range(genes):
        row = sorted({(gene - 1) % genes, (gene + 1) % genes})
        neighbors.append(torch.tensor(row))
        weights.append(torch.tensor([1.0, 0.9]))
    return CorrelationGraph(tuple(neighbors), tuple(weights), 2, genes)


def small_blocks(batch: int = 2, genes: int = 20):
    measured = torch.ones(batch, genes, dtype=torch.bool)
    return sample_target_blocks(
        measured, small_graph(genes), production_seed=81,
        cell_indices=torch.arange(batch), sample_pass=3, view_index=0,
        mask_fraction=0.40, block_count=4,
    )


def test_linear_attention_output_shapes() -> None:
    module = KernelLinearAttention(width=8, heads=2)
    output, denominator = module(torch.randn(2, 7, 8), torch.ones(2, 7, dtype=torch.bool))
    assert output.shape == (2, 7, 8) and denominator.ndim == 0


def test_linear_attention_source_has_no_quadratic_score_tensor() -> None:
    source = inspect.getsource(KernelLinearAttention.forward)
    assert "bhnd,bhmd" not in source
    assert "transpose(-1, -2)" not in source
    assert "bhnd,bhne->bhde" in source


def test_linear_attention_matches_explicit_kernel_formula() -> None:
    torch.manual_seed(1)
    module = KernelLinearAttention(width=4, heads=1).eval()
    tokens = torch.randn(1, 3, 4)
    valid = torch.tensor([[True, True, False]])
    output, _ = module(tokens, valid)
    q = F.elu(module.query(tokens)) + 1
    k = (F.elu(module.key(tokens)) + 1) * valid[..., None]
    v = module.value(tokens) * valid[..., None]
    expected = []
    for query in q[0]:
        weights = torch.tensor([float(query @ key) for key in k[0]])
        expected.append((weights[:, None] * v[0]).sum(0) / weights.sum().clamp_min(1e-6))
    expected = module.output(torch.stack(expected)[None])
    torch.testing.assert_close(output, expected, rtol=1e-5, atol=1e-5)


def test_invalid_genes_have_zero_kv_influence() -> None:
    torch.manual_seed(2)
    module = KernelLinearAttention(width=8, heads=2).eval()
    valid = torch.tensor([[True, True, False, False]])
    first = torch.randn(1, 4, 8)
    second = first.clone()
    second[:, 2:] = 1000.0
    a, _ = module(first, valid)
    b, _ = module(second, valid)
    torch.testing.assert_close(a[:, :2], b[:, :2], rtol=0, atol=0)


def test_hidden_expression_cannot_change_student_visible_or_cell_state() -> None:
    torch.manual_seed(3)
    model = IPBEncoder(width=8, heads=2, blocks=1, ffn_width=16, dropout=0).eval()
    ids = torch.arange(6).repeat(1, 1)
    measured = torch.ones(1, 6, dtype=torch.bool)
    hidden = torch.tensor([[False, True, False, True, False, False]])
    first = torch.randn(1, 6)
    second = first.clone(); second[hidden] = 999.0
    a = model(ids, first, measured, hidden, "student")
    b = model(ids, second, measured, hidden, "student")
    torch.testing.assert_close(a.cell_state, b.cell_state, rtol=0, atol=0)
    torch.testing.assert_close(a.gene_states[:, ~hidden[0]], b.gene_states[:, ~hidden[0]], rtol=0, atol=0)


def test_measured_zero_remains_valid() -> None:
    model = IPBEncoder(width=8, heads=2, blocks=1, ffn_width=16, dropout=0).eval()
    ids = torch.arange(4).repeat(1, 1)
    output = model(ids, torch.zeros(1, 4), torch.ones(1, 4, dtype=torch.bool), torch.zeros(1, 4, dtype=torch.bool), "student")
    assert torch.isfinite(output.gene_states).all()


def test_cell_token_is_always_valid_even_when_some_genes_hidden() -> None:
    model = IPBEncoder(width=8, heads=2, blocks=1, ffn_width=16, dropout=0).eval()
    ids = torch.arange(4).repeat(1, 1)
    hidden = torch.tensor([[True, True, True, False]])
    output = model(ids, torch.rand(1, 4), torch.ones(1, 4, dtype=torch.bool), hidden, "student")
    assert output.cell_state.shape == (1, 8) and torch.isfinite(output.cell_state).all()


def test_target_has_no_gradients_and_online_is_finite() -> None:
    online = IPBEncoder(width=8, heads=2, blocks=1, ffn_width=16, dropout=0)
    target = create_ema_target(online)
    ids = torch.arange(5).repeat(2, 1); values = torch.rand(2, 5)
    measured = torch.ones(2, 5, dtype=torch.bool); hidden = torch.zeros_like(measured)
    student = online(ids, values, measured, hidden, "student").cell_state
    with torch.no_grad(): teacher = target(ids, values, measured, hidden, "target").cell_state
    (student - teacher.detach()).square().mean().backward()
    assert any(p.grad is not None and torch.isfinite(p.grad).all() for p in online.parameters())
    assert all(p.grad is None for p in target.parameters())


def test_block_query_is_identity_only_and_hidden_values_cannot_enter() -> None:
    encoder = IPBEncoder(width=8, heads=2, blocks=1, ffn_width=16, dropout=0)
    predictor = BlockPredictor(identity_dim=48, width=8, heads=2)
    blocks = small_blocks()
    first = predictor.block_queries(encoder.tokenizer.gene_identity, blocks)
    second = predictor.block_queries(encoder.tokenizer.gene_identity, blocks)
    torch.testing.assert_close(first, second, rtol=0, atol=0)
    assert set(inspect.signature(predictor.block_queries).parameters) == {"identity_embedding", "blocks"}


def test_block_targets_use_selected_teacher_gene_states_only() -> None:
    blocks = small_blocks()
    states = torch.randn(2, 20, 8)
    first = gather_block_states(states, blocks)
    changed = states.clone(); changed[~blocks.hidden_mask] += 1000
    second = gather_block_states(changed, blocks)
    torch.testing.assert_close(first, second, rtol=0, atol=0)


def test_graph_is_not_an_encoder_input() -> None:
    assert set(inspect.signature(IPBEncoder.forward).parameters) == {
        "self", "gene_ids", "expression", "measurement_mask", "hidden_target_mask", "view"
    }


def test_graph_builder_accepts_no_labels() -> None:
    assert set(inspect.signature(build_train_pearson_graph).parameters) == {
        "training_expression", "top_k", "chunk_genes"
    }


def test_graph_builder_is_symmetric_top_k_union() -> None:
    torch.manual_seed(4)
    graph = build_train_pearson_graph(torch.randn(30, 12), top_k=3, chunk_genes=4)
    for source, row in enumerate(graph.neighbors):
        for target in row.tolist():
            assert source in graph.neighbors[target].tolist()


def test_gene_anchor_loss_uses_only_supplied_hidden_tensors() -> None:
    shape = (2, 8)
    result = gene_anchor_loss(torch.zeros(shape), torch.zeros(shape), torch.ones(shape), torch.ones(shape))
    assert set(result) == {"value", "detection", "gene"}
    torch.testing.assert_close(result["gene"], 0.5 * result["value"] + 0.5 * result["detection"])


def test_anchor_decoder_api_reads_cell_state_not_contextual_tokens() -> None:
    assert set(inspect.signature(GeneAnchorDecoder.forward).parameters) == {
        "self", "cell_state", "identity_embedding", "hidden_gene_ids"
    }


def test_hidden_gene_indices_returns_exact_union() -> None:
    blocks = small_blocks()
    indices = hidden_gene_indices(blocks.hidden_mask)
    assert indices.shape == (2, 8)
    assert all(set(row.tolist()) == set(torch.nonzero(mask).flatten().tolist()) for row, mask in zip(indices, blocks.hidden_mask))


def test_target_blocks_are_deterministic() -> None:
    first = small_blocks(); second = small_blocks()
    assert torch.equal(first.hidden_mask, second.hidden_mask)
    assert torch.equal(first.indices, second.indices)


def test_target_blocks_have_exact_40_percent_hidden() -> None:
    blocks = small_blocks()
    assert torch.equal(blocks.hidden_mask.sum(1), torch.tensor([8, 8]))


def test_target_blocks_are_disjoint() -> None:
    blocks = small_blocks()
    for row in range(2):
        values = blocks.indices[row][blocks.member_mask[row]].tolist()
        assert len(values) == len(set(values))


def test_target_block_union_equals_hidden_set() -> None:
    blocks = small_blocks()
    for row in range(2):
        assert set(blocks.indices[row][blocks.member_mask[row]].tolist()) == set(torch.nonzero(blocks.hidden_mask[row]).flatten().tolist())


def test_integrated_ipb_objective_has_online_predictor_and_anchor_gradients_only() -> None:
    torch.manual_seed(11)
    online = IPBEncoder(width=8, heads=2, blocks=1, ffn_width=16, dropout=0)
    target = create_ema_target(online)
    predictor = BlockPredictor(identity_dim=48, width=8, heads=2)
    decoder = GeneAnchorDecoder(identity_dim=48, width=8)
    blocks = small_blocks(batch=2, genes=20)
    ids = torch.arange(20).repeat(2, 1)
    values = torch.rand(2, 20)
    measured = torch.ones(2, 20, dtype=torch.bool)
    student = online(ids, values, measured, blocks.hidden_mask, "student")
    hidden_ids = hidden_gene_indices(blocks.hidden_mask)
    value_hat, detection_hat = decoder(
        student.cell_state, online.tokenizer.gene_identity, hidden_ids
    )
    rows = torch.arange(2)[:, None]
    anchor = gene_anchor_loss(
        value_hat, detection_hat, values[rows, hidden_ids], values[rows, hidden_ids] > 0
    )
    with torch.no_grad():
        teacher = target(ids, values, measured, torch.zeros_like(measured), "target")
        teacher_blocks = gather_block_states(teacher.gene_states, blocks)
    predicted_blocks = predictor(
        online.tokenizer.gene_identity, blocks, student.gene_states,
        student.cell_state, measured & ~blocks.hidden_mask,
    )
    (anchor["gene"] + block_jepa_loss(predicted_blocks, teacher_blocks)).backward()
    assert any(p.grad is not None and torch.isfinite(p.grad).all() for p in online.parameters())
    assert any(p.grad is not None and torch.isfinite(p.grad).all() for p in predictor.parameters())
    assert any(p.grad is not None and torch.isfinite(p.grad).all() for p in decoder.parameters())
    assert all(p.grad is None for p in target.parameters())


def test_exact_six_block_candidate_and_no_perceiver_slots() -> None:
    model = IPBEncoder()
    assert len(model.blocks) == 6
    assert not hasattr(model, "latents") and not hasattr(model, "cross_attention")


def test_block_jepa_detaches_teacher_target() -> None:
    predicted = torch.randn(2, 4, 8, requires_grad=True)
    target = torch.randn(2, 4, 8, requires_grad=True)
    block_jepa_loss(predicted, target).backward()
    assert predicted.grad is not None and target.grad is None


def test_train_only_standardization_contract_is_frozen_in_config() -> None:
    text = (PROJECT / "configs/v4/stage81a3_ipb_jepa_feasibility.yaml").read_text()
    assert "synthetic_train_normalized_expression_only" in text
    assert "graph_model_input: false" in text
    assert "trajectories: 8" in text


def test_fp16_forward_finite_when_cuda_available() -> None:
    if not torch.cuda.is_available(): return
    model = IPBEncoder().cuda().eval()
    ids = torch.arange(128, device="cuda").repeat(2, 1)
    values = torch.rand(2, 128, device="cuda")
    measured = torch.ones(2, 128, dtype=torch.bool, device="cuda")
    hidden = torch.zeros_like(measured)
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16):
        output = model(ids, values, measured, hidden, "student")
    assert torch.isfinite(output.gene_states).all() and torch.isfinite(output.cell_state).all()


def test_fp16_full_vocabulary_accumulation_and_denominator_remain_finite() -> None:
    if not torch.cuda.is_available(): return
    model = IPBEncoder().cuda().eval()
    ids = torch.arange(4096, device="cuda").repeat(2, 1)
    values = torch.rand(2, 4096, device="cuda")
    measured = torch.ones(2, 4096, dtype=torch.bool, device="cuda")
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16):
        output = model(ids, values, measured, torch.zeros_like(measured), "target")
    assert torch.isfinite(output.gene_states).all()
    assert torch.isfinite(output.cell_state).all()
    assert torch.isfinite(output.minimum_denominator)
    assert output.minimum_denominator.dtype == torch.float32


def test_flattened_kernel_readout_uses_float64_accumulators() -> None:
    runner = importlib.import_module("scripts.v4.stage81a3_ipb_jepa_feasibility")
    source = inspect.getsource(runner.feature_kernel_readout)
    assert "dtype=torch.float64" in source
    assert ".double()" in source


# Local import keeps the source-level test above readable.
import torch.nn.functional as F  # noqa: E402
