"""Deliberate historical regressions: old collapse and dead C2 gradients must STOP."""
from __future__ import annotations

import numpy as np
import pytest
import torch

from scripts.v5 import jepa_synth2048_collapse_sentinel_v1 as guard
from sea_ad_jepa.v5.inactive_update_reference import build_reference_modules


def _states():
    rng = np.random.default_rng(711)
    return rng.normal(size=(16, 8)).astype(np.float32)


def _modules(blocks=6):
    return build_reference_modules(
        vocabulary_size=32, width=16, heads=4, blocks=blocks, ffn_width=24,
        dropout=.10, learning_rate=3e-4, betas=(.9, .999), eps=1e-8,
        weight_decay=.01, init_seed=8113002,
    )


def _record():
    return {
        "step_before": 0, "step_after": 1, "ema_updates": 1,
        "teacher_gradients": 0, "mandatory_gradient_gate": True,
        "adam_moment_gate": True, "student_cell_states": _states(),
        "train_jepa_loss": 2.0, "hidden_anchor_weight": 0.0,
    }


def test_healthy_init_is_only_unqualified_telemetry():
    r = guard.geometry_diagnostic(_states())
    assert r.status == "UNQUALIFIED_GEOMETRY_TELEMETRY_ONLY"
    assert r.cell_state_effective_rank is not None
    assert 1.0 < r.cell_state_effective_rank <= 8.0
    assert 0 < r.top_singular_energy_fraction < 1.0
    assert r.qualified_biological_representation is False



def test_two_cell_u0_is_not_misreported_as_real_rank_one_collapse():
    tiny = np.vstack([np.arange(8), np.arange(8) + 0.2])
    report = guard.geometry_diagnostic(tiny)
    assert report.status == "NOT_ESTIMABLE_TOO_FEW_CELLS_FOR_GEOMETRY"
    assert report.cell_state_effective_rank is None
    assert report.top_singular_energy_fraction is None
    assert report.qualified_biological_representation is False


def test_identical_cell_states_stop_even_if_loss_decreases():
    collapsed = np.repeat(np.arange(8, dtype=float)[None, :], 16, axis=0)
    with pytest.raises(guard.CollapseStop, match="exactly constant"):
        guard.geometry_diagnostic(collapsed)
    r = _record()
    r["train_jepa_loss"] = 0.000001
    r["student_cell_states"] = collapsed
    with pytest.raises(guard.CollapseStop, match="exactly constant"):
        guard.evaluate_training_record(r)


def test_nonfinite_and_missing_geometry_stop():
    x = _states()
    x[0, 0] = np.nan
    with pytest.raises(guard.CollapseStop, match="nonfinite"):
        guard.geometry_diagnostic(x)
    with pytest.raises(guard.CollapseStop, match="requires"):
        guard.geometry_diagnostic(np.zeros((1, 8)))


def test_real_one_factor_biology_cannot_be_automatically_killed_as_collapse():
    factor = np.linspace(-1, 1, 16)
    rank1_biology = np.outer(factor, np.ones(8))
    r = guard.geometry_diagnostic(rank1_biology)
    assert r.cell_state_effective_rank is not None
    assert r.qualified_biological_representation is False
    assert r.status == "UNQUALIFIED_GEOMETRY_TELEMETRY_ONLY"
    assert r.top_singular_energy_fraction == pytest.approx(1.0)



def test_real_token_diversity_is_unqualified_not_a_fabricated_C_pass():
    rng = np.random.default_rng(812)
    tokens = rng.normal(size=(6, 12, 16))
    report = guard.token_geometry_diagnostic(tokens)
    assert report["exact_token_collapsed_cells"] == 0
    assert report["qualified_biological_representation"] is False
    assert report["within_cell_feature_std_median"] > 0


def test_gene_token_collapse_stops_even_when_cell_embeddings_differ():
    # Cell token can vary while every molecular token within a cell is identical.
    across_cells = np.random.default_rng(813).normal(size=(6, 16))
    all_tokens_equal_per_cell = np.broadcast_to(
        across_cells[:, None, :], (6, 12, 16)
    ).copy()
    with pytest.raises(guard.CollapseStop, match="identical gene-token"):
        guard.token_geometry_diagnostic(all_tokens_equal_per_cell)
    altered = np.random.default_rng(813).normal(size=(6, 12, 16))
    altered[3, :, :] = 7.0
    with pytest.raises(guard.CollapseStop, match="identical gene-token"):
        guard.token_geometry_diagnostic(altered)


def test_nonfinite_gene_token_stops():
    tokens = np.random.default_rng(814).normal(size=(6, 12, 16))
    tokens[0, 0, 0] = float("inf")
    with pytest.raises(guard.CollapseStop, match="nonfinite gene-token"):
        guard.token_geometry_diagnostic(tokens)


def test_original_48_protected_names_on_actual_six_block_encoder():
    modules = _modules(6)
    receipt = guard.check_encoder_gradient_registry(modules.online)
    assert receipt["count"] == 48
    assert receipt["status"].endswith("NO_GRADIENT_STEP")


def test_five_block_mutation_does_not_silently_shrink_protected_gate():
    modules = _modules(5)
    with pytest.raises(RuntimeError, match="mandatory registry mismatch"):
        guard.check_encoder_gradient_registry(modules.online)


def test_live_subnormal_is_nonzero_and_zero_gradient_is_rejected():
    modules = _modules()
    for p in modules.online.parameters():
        p.grad = torch.ones_like(p)
    for p in modules.predictor.parameters():
        p.grad = torch.ones_like(p)
    result = guard.enforce_live_update_gradients(
        modules.online, modules.predictor, modules.teacher
    )
    assert result["protected_encoder"] == 48
    name, p = next(
        (name, p) for name, p in modules.online.named_parameters()
        if "attention.query.weight" in name
    )
    p.grad.zero_()
    with pytest.raises(RuntimeError, match="mandatory gradient gate rejected"):
        guard.enforce_live_update_gradients(modules.online, modules.predictor,
                                            modules.teacher)
    tiny = torch.nextafter(torch.tensor(0.0), torch.tensor(1.0))
    p.grad.zero_()
    p.grad.flatten()[0] = tiny
    assert guard.enforce_live_update_gradients(
        modules.online, modules.predictor, modules.teacher
    )["protected_encoder"] == 48


def test_predictor_dead_grad_and_teacher_gradient_stop():
    modules = _modules()
    for p in modules.online.parameters(): p.grad = torch.ones_like(p)
    for p in modules.predictor.parameters(): p.grad = torch.ones_like(p)
    p = next(modules.predictor.parameters())
    p.grad.zero_()
    with pytest.raises(guard.CollapseStop, match="predictor gradient"):
        guard.enforce_live_update_gradients(
            modules.online, modules.predictor, modules.teacher)
    p.grad.fill_(1)
    teacher_p = next(modules.teacher.parameters())
    teacher_p.grad = torch.ones_like(teacher_p)
    with pytest.raises(guard.CollapseStop, match="EMA teacher"):
        guard.enforce_live_update_gradients(
            modules.online, modules.predictor, modules.teacher)


@pytest.mark.parametrize("anchor", [0.001, 1.0, float("nan"), float("inf"), True, "0"])
def test_historical_rejected_hidden_gene_anchor_stays_off(anchor):
    with pytest.raises(guard.CollapseStop, match="anchor"):
        guard.check_anchor_loss_weight(anchor)


@pytest.mark.parametrize("key,value,pattern", [
    ("step_after",0,"optimizer->EMA"),
    ("step_after",2,"optimizer->EMA"),
    ("ema_updates",0,"optimizer->EMA"),
    ("teacher_gradients",1,"EMA teacher gradient"),
    ("mandatory_gradient_gate",False,"48-parameter"),
    ("adam_moment_gate",False,"Adam"),
    ("train_jepa_loss",float("nan"),"loss"),
    ("hidden_anchor_weight",0.1,"anchor"),
])
def test_historical_training_record_rejects_mutations(key,value,pattern):
    r = _record()
    r[key] = value
    with pytest.raises(guard.CollapseStop, match=pattern):
        guard.evaluate_training_record(r)


def test_fake_positive_mechanics_flags_never_issue_biology_pass():
    report = guard.evaluate_training_record(_record())
    assert report["status"] == "MECHANICS_VALIDATION_ONLY__NO_BIOLOGICAL_PASS"
    assert report["masked_student_biology_qualified"] is False
    assert report["all_six_C_candidates"] == "UNASSESSED"
    assert not guard.synthetic_training_readiness()["synthetic_training_ready"]


def test_false_jeparun_cannot_hide_missing_telemetry():
    r = _record()
    del r["adam_moment_gate"]
    with pytest.raises(guard.CollapseStop, match="telemetry"):
        guard.evaluate_training_record(r)


def test_biology_below_visible_rna_or_wrong_cell_fails():
    check = guard.check_biology_endpoint
    common = {"genuine_donor_heldout": True, "externally_authenticated": True}
    assert check(masked_student_score=.2, visible_rna_score=.3, wrong_cell_score=.1,
                 **common) == "FAIL__STUDENT_NOT_BETTER_THAN_VISIBLE_RNA"
    assert check(masked_student_score=.3, visible_rna_score=.2, wrong_cell_score=.4,
                 **common) == "FAIL__STUDENT_NOT_BETTER_THAN_WRONG_CELL"


def test_uncertain_biology_abstains_not_passed():
    check = guard.check_biology_endpoint
    assert check(masked_student_score=.8, visible_rna_score=.1, wrong_cell_score=.1,
                 genuine_donor_heldout=False, externally_authenticated=True).startswith("NOT_ESTIMABLE")
    assert check(masked_student_score=.8, visible_rna_score=.1, wrong_cell_score=.1,
                 genuine_donor_heldout=True, externally_authenticated=True).startswith("NOT_ESTIMABLE")
    assert check(masked_student_score=None, visible_rna_score=.1, wrong_cell_score=.1,
                 genuine_donor_heldout=True, externally_authenticated=True).startswith("STOP")
