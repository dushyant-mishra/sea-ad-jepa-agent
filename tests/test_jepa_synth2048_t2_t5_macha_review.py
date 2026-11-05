"""Macha T2-T5 adversarial tests against #554 head b48fbb2d (tests only; code UNCHANGED).

T2  (LIMIT witnesses + design witnesses, all pass today). Uses the REAL V5 encoder
    (`build_reference_modules`) with its value encoder zeroed, i.e. token states that ignore
    expression values. #554's exact cross-cell check STOPs only when cells share an identical
    token set AND dropout is off (eval-mode, operator-homogeneous teacher batch). With
    different token sets (student views, mixed operators) attention context differs, and in
    train mode keyed dropout differs per cell, so a value-blind encoder is NOT detected.
    The design witness shows a same-cell expression counterfactual (permute values, keep
    token set) gives EXACTLY zero change for the value-blind encoder, a tiny change for a
    near-blind one, and a clear change for a healthy one, including one-factor biology.
T3  (RED) self-declared gradient/Adam booleans must not validate a training record.
T4  (RED) bare scalar scores without metric identity/direction/paired donors must not yield
    a positive diagnostic when the metric is a loss (lower is better).
T5  (RED) the restored address space must distinguish WITHHELD_BY_DESIGN q from
    STRUCTURALLY_UNMEASURED addresses in at least one output.

Synthetic arrays and an untrained tiny network only. No data, training, GPU or Stage 4.
TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED
"""
from __future__ import annotations

import numpy as np
import pytest
import torch

from scripts.v5 import jepa_synth2048_collapse_sentinel_v1 as guard
from scripts.v5 import jepa_synth2048_v5_readiness as readiness
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules

VOCAB, TOKENS = 32, 20


def _encoder(value_scale: float | None = None):
    m = build_reference_modules(
        vocabulary_size=VOCAB, width=16, heads=4, blocks=6, ffn_width=24,
        dropout=.10, learning_rate=3e-4, betas=(.9, .999), eps=1e-8,
        weight_decay=.01, init_seed=8113002,
    )
    enc = m.online
    if value_scale is not None:
        last = enc.tokenizer.value_encoder[-1]
        with torch.no_grad():
            last.weight.mul_(value_scale)
            last.bias.mul_(value_scale)
    return enc


def _forward(enc, ids, expr, *, train=False):
    enc.train(train)
    ids_t = torch.as_tensor(ids, dtype=torch.int64)
    x = torch.as_tensor(expr, dtype=torch.float32)
    ones = torch.ones_like(x, dtype=torch.bool)
    with torch.no_grad():
        out = enc(ids_t, x, ones, torch.zeros_like(ones), "target",
                  cell_keys=torch.arange(len(ids_t), dtype=torch.int64) + 11_000_000,
                  run_seed=8113002, update_index=0, view_index=0)
    return out.gene_states.numpy(), out.cell_state.numpy()


def _expr(cells, seed):
    return np.log1p(np.random.default_rng(seed).poisson(3.0, size=(cells, TOKENS))).astype(np.float32)


SAME_SETS = np.stack([np.arange(TOKENS)] * 2)
DIFFERENT_SETS = np.stack([np.arange(TOKENS), np.arange(1, TOKENS + 1)])  # 19 shared genes


# ---- T2: what #554 can and cannot see, on the real encoder ----

def test_t2_guard_value_blind_encoder_with_identical_token_sets_in_eval_stops():
    states, _ = _forward(_encoder(0.0), SAME_SETS, _expr(2, 1))
    with pytest.raises(guard.CollapseStop, match="identity-only"):
        guard.token_geometry_diagnostic(states, gene_ids=SAME_SETS)


def test_t2_limit_value_blind_encoder_with_different_token_sets_is_not_detected():
    states, _ = _forward(_encoder(0.0), DIFFERENT_SETS, _expr(2, 2))
    report = guard.token_geometry_diagnostic(states, gene_ids=DIFFERENT_SETS)
    assert report["shared_gene_ids_compared_across_cells"] == TOKENS - 1
    assert report["shared_gene_ids_with_cell_specific_states"] == TOKENS - 1  # LIMIT: all "vary"


def test_t2_limit_value_blind_encoder_in_train_mode_is_not_detected():
    states, _ = _forward(_encoder(0.0), SAME_SETS, _expr(2, 3), train=True)
    report = guard.token_geometry_diagnostic(states, gene_ids=SAME_SETS)
    assert report["shared_gene_ids_with_cell_specific_states"] == TOKENS  # LIMIT: dropout noise


def _counterfactual_delta(enc, ids, expr):
    base, _ = _forward(enc, ids, expr)
    perm = np.random.default_rng(99).permutation(TOKENS)
    shuffled, _ = _forward(enc, ids, expr[:, perm])
    return float(np.abs(base - shuffled).max())


@pytest.mark.parametrize("ids", [SAME_SETS, DIFFERENT_SETS], ids=["same_sets", "different_sets"])
def test_t2_design_same_cell_expression_counterfactual_separates_value_blind(ids):
    expr = _expr(2, 4)
    blind = _counterfactual_delta(_encoder(0.0), ids, expr)
    near_blind = _counterfactual_delta(_encoder(1e-6), ids, expr)
    healthy = _counterfactual_delta(_encoder(None), ids, expr)
    assert blind == 0.0                       # exact, threshold-free STOP is possible
    assert 0.0 < near_blind < 1e-3 * healthy  # near-collapse needs the U0/healthy reference
    assert healthy > 0.0


def test_t2_guard_one_factor_low_rank_biology_is_not_rejected():
    pattern = np.random.default_rng(5).gamma(2.0, 1.0, size=TOKENS)
    scale = np.array([[0.5], [2.0]])
    expr = np.log1p(scale * pattern).astype(np.float32)  # rank-one biology across cells
    enc = _encoder(None)
    states, _ = _forward(enc, SAME_SETS, expr)
    report = guard.token_geometry_diagnostic(states, gene_ids=SAME_SETS)
    assert report["qualified_biological_representation"] is False
    assert _counterfactual_delta(enc, SAME_SETS, expr) > 0.0


# ---- T3: physical gradient / Adam evidence, not caller booleans ----

def test_t3_red_self_declared_gate_booleans_must_not_validate_a_training_record():
    record = {
        "step_before": 0, "step_after": 1, "ema_updates": 1, "teacher_gradients": 0,
        "mandatory_gradient_gate": True, "adam_moment_gate": True,
        "student_cell_states": np.random.default_rng(6).normal(size=(16, 8)),
        "train_jepa_loss": 2.0, "hidden_anchor_weight": 0.0,
    }
    with pytest.raises(guard.CollapseStop):
        report = guard.evaluate_training_record(record)
        pytest.fail(f"bare booleans accepted as 48-gradient/Adam proof: {report['status']}")


# ---- T4: metric identity, direction, paired donors ----

def test_t4_red_bare_loss_scores_must_not_yield_a_positive_diagnostic():
    # Student MSE 2.0 is WORSE than visible-RNA MSE 1.0 and wrong-cell MSE 1.5.
    try:
        result = guard.check_biology_endpoint(
            masked_student_score=2.0, visible_rna_score=1.0, wrong_cell_score=1.5,
            genuine_donor_heldout=True, externally_authenticated=True,
        )
    except (TypeError, ValueError, guard.CollapseStop):
        return
    assert result.startswith(("FAIL", "STOP")), (
        f"undeclared-direction loss scores produced {result}")


# ---- T5: withheld-by-design vs structurally unmeasured ----

def test_t5_red_withheld_query_must_differ_from_structurally_unmeasured_address():
    q = readiness.Q
    addr = np.setdiff1d(np.arange(readiness.N_ADDRESSES), q).astype(np.int32)
    n = readiness.N_CELLS
    support = np.ones((n, len(addr)), dtype=np.bool_)
    support[:, 0] = False  # address 0 is structurally unmeasured in every cell
    student = {
        "rna_base_counts": np.zeros((n, len(addr)), dtype=np.int32),
        "rna_base_support": support,
        "rna_base_address_ids": addr,
        "projected_base_depth": np.zeros(n, dtype=np.int64),
    }
    outputs = readiness.restore_full_address_space(student)
    outputs = outputs if isinstance(outputs, tuple) else (outputs,)
    grids = [np.asarray(o) for o in outputs
             if np.asarray(o).ndim == 2 and np.asarray(o).shape[1] == readiness.N_ADDRESSES]
    assert grids
    assert any(not np.array_equal(g[:, q[0]], g[:, 0]) for g in grids), (
        "withheld query and structurally unmeasured address are encoded identically")
