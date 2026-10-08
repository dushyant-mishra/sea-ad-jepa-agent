from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(PROJECT / "scripts" / "v4"))

import stage81a3_rbb_uncertainty_localization_identifiability as uli  # noqa: E402


SOURCE = Path(uli.__file__).read_text(encoding="utf-8")


def test_zero_core_optimizer_updates_and_no_optimizer():
    assert "torch.optim" not in SOURCE
    assert '"core_neural_optimizer_updates": 0' in SOURCE


def test_frozen_hashes_and_checkpoint_are_reverified():
    source = inspect.getsource(uli.load_frozen_core)
    assert "frozen.frozen_hashes(core)" in source
    assert "sha256(CORE_CHECKPOINT)" in source


def test_exactly_32_target_replicates():
    assert uli.TARGET_REPLICATES == 32


def test_target_replicate_rng_is_deterministic_and_distinct():
    rates = torch.full((8, 5), 3.0)
    first = uli.generate_target_replicate(rates, 1)
    second = uli.generate_target_replicate(rates, 1)
    other = uli.generate_target_replicate(rates, 2)
    assert torch.equal(first, second) and not torch.equal(first, other)


def test_target_rng_derivation_is_declared():
    assert uli.target_replicate_seed(1) == uli.SEED + 1_000_003
    assert uli.target_replicate_seed(32) == uli.SEED + 32_000_096


def test_target_replicates_never_enter_model_forward():
    assert "forward_condition(core, target_expression" not in SOURCE
    assert "target_expression = generate_target_replicate" in SOURCE


def test_target_replicates_are_not_diagnostic_features():
    source = inspect.getsource(uli.main)
    feature_block = source[source.index("base_features[name]"):source.index("train_x_base")]
    assert "target_expression" not in feature_block and "errors" not in feature_block


def test_visible_xa_is_fixed_for_base_forward():
    source = inspect.getsource(uli.main)
    assert "core, fixture.x_a, item" in source


def test_risk_formulas_are_exact():
    errors = torch.arange(32 * 3, dtype=torch.float32).reshape(32, 3)
    noise = errors + 1; cross = errors - 2
    biological = torch.tensor([[1.0, 2.0], [2.0, 0.0], [3.0, 4.0]])
    result = uli.assemble_risk_objects(errors, noise, cross, biological)
    assert torch.equal(result["single"], errors[0])
    assert torch.equal(result["total"], errors.mean(0))
    assert torch.equal(result["bio"], biological.square().mean(1))
    assert torch.equal(result["noise"], noise.mean(0))
    assert torch.equal(result["cross"], cross.mean(0))


def test_split_half_replicate_sets_are_exact_16_16():
    errors = torch.arange(32, dtype=torch.float32)[:, None]
    result = uli.assemble_risk_objects(errors, errors, errors, torch.ones(1, 2))
    assert result["total_a"] == errors[:16].mean() and result["total_b"] == errors[16:].mean()


def test_risk_decomposition_is_explicitly_checked():
    source = inspect.getsource(uli.main)
    assert 'values["total"] - values["bio"] - values["noise"] - values["cross"]' in source
    assert "decomposition_max_absolute_error" in source


def test_ordinary_control_indices_are_fixed():
    assert uli.ORDINARY_INDICES == (0, 32, 64, 96)


def test_four_structural_views_are_reused():
    source = inspect.getsource(uli.condition_definitions)
    assert "for view in range(4)" in source
    assert '["P60"]' in source


def test_eight_jackknife_groups_remove_123_each_and_are_disjoint():
    measured = torch.zeros(4096, dtype=torch.bool); measured[:2458] = True
    masks = uli.jackknife_masks(measured, 0, 0)
    assert len(masks) == 8
    removed = [measured & ~mask for mask in masks]
    assert all(int(values.sum()) == 123 for values in removed)
    assert int(torch.stack(removed).sum(0).gt(1).sum()) == 0
    assert all(int(mask.sum()) == 2335 for mask in masks)


@pytest.mark.parametrize("forbidden", ["expression", "fixture.factors", "risk", "error"])
def test_jackknife_construction_is_blind(forbidden):
    assert forbidden not in inspect.getsource(uli.jackknife_masks)


def test_jackknife_preserves_base_structural_absence():
    measured = torch.zeros(4096, dtype=torch.bool); measured[500:2958] = True
    for mask in uli.jackknife_masks(measured, 1, 1):
        assert torch.all(~mask[~measured])


def test_jackknife_scoring_formulas():
    means = torch.arange(8 * 3 * 2, dtype=torch.float32).reshape(8, 3, 2)
    traces = torch.arange(8 * 3, dtype=torch.float32).reshape(8, 3)
    base_mean = torch.zeros(3, 2); base_trace = torch.zeros(3)
    result = uli.jackknife_scores(means, traces, base_mean, base_trace)
    shifts = means.square().mean(2)
    assert torch.equal(result["fragility"], shifts.mean(0))
    assert torch.equal(result["maximum"], shifts.max(0).values)
    assert torch.equal(result["coordinate_variance"], means.var(0, unbiased=False).sum(1))
    assert torch.equal(result["mean_delta"], traces.mean(0))
    assert torch.equal(result["max_delta"], traces.max(0).values)


def test_jackknife_requires_exactly_eight_groups():
    with pytest.raises(ValueError, match="exactly eight"):
        uli.jackknife_scores(torch.zeros(7, 2, 3), torch.zeros(7, 2), torch.zeros(2, 3), torch.zeros(2))


def test_replicate_disagreement_uses_same_cell_without_roll():
    source = inspect.getsource(uli.main)
    assert 'delta = a["belief"] - b["belief"]' in source


def test_negative_control_uses_next_cell_shift():
    source = inspect.getsource(uli.main)
    assert '.roll(-1)' in source and "rho_shifted_cell_negative_control" in source


def test_ridge_alpha_is_exactly_fixed():
    assert uli.RIDGE_ALPHA == 1e-3
    assert SOURCE.count("ridge_fit(") == 2


def test_no_ridge_hyperparameter_search():
    lower = SOURCE.lower()
    assert "gridsearch" not in lower and "alpha_search" not in lower


def test_ridge_standardization_is_train_only():
    source = inspect.getsource(uli.main)
    assert "train_x_base" in source and "ridge_fit(train_x_base" in source
    assert "ridge_fit(validation" not in source and "ridge_fit(sealed" not in source


def test_validation_and_sealed_are_evaluation_only():
    source = inspect.getsource(uli.main)
    assert '(("VALIDATION", validation_idx), ("SEALED", sealed_idx))' in source
    assert '"validation_fit": False' in source and '"sealed_fit": False' in source


@pytest.mark.parametrize("forbidden", ["fixture.lambda_norm", "fixture.factors", "target_expression", "hidden expression"])
def test_forbidden_values_absent_from_diagnostic_feature_block(forbidden):
    source = inspect.getsource(uli.main)
    block = source[source.index("base_features[name]"):source.index("train_x_base")]
    assert forbidden not in block


def test_diagnostic_models_are_not_checkpointed():
    source = inspect.getsource(uli.main)
    assert "torch.save(base_model" not in source and "torch.save(stability_model" not in source
    assert '"models_persisted": False' in source


def test_raw_uncalibrated_core_outputs_are_used():
    source = inspect.getsource(uli.forward_condition)
    assert "raw_conditional_diagonal" in source and "raw_total_diagonal" in source
    assert "calibrated_total" not in source


def test_target_replicate_count_guard():
    with pytest.raises(ValueError, match="exactly 32"):
        uli.assemble_risk_objects(torch.zeros(31, 2), torch.zeros(31, 2), torch.zeros(31, 2), torch.zeros(2, 3))


def test_original_localization_threshold_remains_point_five():
    source = inspect.getsource(uli.main)
    assert source.count("> .50") >= 5


def test_historical_localization_target_is_audited_from_code():
    result = uli.historical_localization_target_audit()
    assert result["historical_target"] == "EXPECTED_BIOLOGICAL_STATE_FROM_LAMBDA_NORM"
    assert result["historical_target_was_single_stochastic_realization"] is False


def test_uncovered_risk_decomposition_cannot_be_forced_into_a_to_e():
    source = inspect.getsource(uli.main)
    assert "taxonomy_conflict" in source
    assert 'classification = "ENGINEERING / NUMERICAL FAILURE"' in source


def test_no_real_rna_access_surface():
    lower = SOURCE.lower()
    assert "anndata" not in lower and "h5ad" not in lower and "scanpy" not in lower
    assert '"real_rna_accessed": false' in lower


def test_pathology_is_governance_only():
    lower = SOURCE.lower()
    assert '"pathology_opened": false' in lower
    assert "amyloid" not in lower and "braak" not in lower and "cerad" not in lower


def test_factor_labels_are_evaluation_only():
    source = inspect.getsource(uli.main)
    feature_block = source[source.index("base_features[name]"):source.index("train_x_base")]
    assert "fixture.factors" not in feature_block
    assert '"factor_labels_as_features": False' in source


def test_lambda_is_evaluation_only():
    source = inspect.getsource(uli.main)
    assert "expected_targets" in source
    assert '"lambda_as_features": False' in source


def test_no_seed_or_hyperparameter_sweep():
    assert '"hyperparameter_sweep": False' in SOURCE and '"seed_sweep": False' in SOURCE
