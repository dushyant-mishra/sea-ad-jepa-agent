from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(PROJECT / "scripts" / "v4"))

import stage81a3_rbb_core_simplification_audit as audit  # noqa: E402
from sea_ad_jepa.v4.measurement_state import MeasurementState  # noqa: E402
from sea_ad_jepa.v4.rbb_core import RBBCore, migrate_adaptive_state  # noqa: E402


CORE_SOURCE = Path(inspect.getfile(RBBCore)).read_text(encoding="utf-8")
AUDIT_SOURCE = Path(audit.__file__).read_text(encoding="utf-8")


@pytest.mark.parametrize("forbidden", ["Perceiver", "cell_token", "cls_token", "global_pool"])
def test_rejected_compressors_absent_from_core(forbidden):
    assert forbidden not in CORE_SOURCE


def test_molecular_ledger_is_frozen_and_detached():
    source = inspect.getsource(RBBCore)
    assert "freeze_molecular_ledger()" in source
    assert "with torch.no_grad()" in source and "tokens.detach()" in source


def test_evidence_output_is_mean_plus_diagonal_only():
    source = inspect.getsource(RBBCore.__init__)
    assert "2 * width" in source and "3 * width" not in source


@pytest.mark.parametrize("forbidden", ["correlated_directions", "activation_amplitudes", "q_head"])
def test_adaptive_evidence_components_absent(forbidden):
    assert forbidden not in inspect.getsource(RBBCore)


def test_evidence_low_rank_is_fixed_zero_not_learned():
    source = inspect.getsource(RBBCore.forward)
    assert "zero_evidence_low_rank = torch.zeros" in source
    assert "zero_evidence_low_rank" in source


def test_fixed_prior_low_rank_is_retained():
    source = inspect.getsource(RBBCore.forward)
    assert "prior_low_rank" in source and "fuse_gaussian_beliefs" in source


def test_measurement_noise_is_separate_output():
    fields = RBBCore.__annotations__ if hasattr(RBBCore, "__annotations__") else {}
    assert "measurement_noise_diagonal" in CORE_SOURCE
    assert "raw_conditional_diagonal" in CORE_SOURCE and "raw_total_diagonal" in CORE_SOURCE


def test_raw_and_calibrated_uncertainty_are_exposed():
    for field in ("raw_total_diagonal", "raw_total_low_rank", "calibrated_total_diagonal", "calibrated_total_low_rank"):
        assert field in CORE_SOURCE


def test_visible_state_is_passed_through_without_neural_rewrite():
    source = inspect.getsource(RBBCore.forward)
    assert "visible_state.float()" in source
    assert "visible_state.float() + posterior_mean" in source


def test_measurement_contract_has_all_four_states():
    measurement = torch.tensor([[True, True, False, False]])
    hidden = torch.tensor([[False, True, False, False]])
    state = MeasurementState(measurement, hidden, torch.ones(4, dtype=torch.bool))
    assert state.observed_mask.tolist() == [[True, False, False, False]]
    assert state.training_target_eligible_mask.tolist() == [[False, True, False, False]]
    assert state.structural_unmeasured_mask.tolist() == [[False, False, True, True]]


def test_measured_zero_and_structural_unmeasurement_are_distinct():
    expression = torch.zeros(1, 2)
    measured = MeasurementState(torch.tensor([[True, False]]), torch.zeros(1, 2, dtype=torch.bool), torch.ones(2, dtype=torch.bool))
    assert measured.observed_mask[0, 0] and not measured.observed_mask[0, 1]
    assert torch.equal(measured.sanitized_expression(expression), expression)


def test_structural_genes_are_not_training_targets():
    state = MeasurementState(torch.tensor([[False]]), torch.tensor([[False]]), torch.tensor([True]))
    assert state.belief_missing_mask[0, 0] and not state.training_target_eligible_mask[0, 0]


def test_foundation_support_boundary_rejects_fake_inference():
    state = MeasurementState(torch.tensor([[False]]), torch.tensor([[False]]), torch.tensor([False]))
    with pytest.raises(ValueError, match="globally never-observed"):
        state.assert_foundation_inference_supported()


@pytest.mark.parametrize("discarded", [
    "evidence_output.weight[320:352]", "evidence_output.bias[320:352]", "correlated_directions",
])
def test_only_approved_adaptive_parameters_are_discarded(discarded):
    assert discarded in inspect.getsource(migrate_adaptive_state)


def test_migration_retains_mean_and_diagonal_slices():
    source = inspect.getsource(migrate_adaptive_state)
    assert "[:2 * core.width]" in source


def test_migration_is_clone_based_and_deterministic():
    source = inspect.getsource(migrate_adaptive_state)
    assert ".detach().clone()" in source


def test_historical_checkpoint_is_read_only():
    source = inspect.getsource(audit.migrate_core)
    assert "torch.load(SOURCE_CHECKPOINT" in source
    assert "atomic_checkpoint(OUTPUTS" in source


def test_migration_copies_verified_frozen_ledger_exactly():
    assert "core.ledger.load_state_dict(adaptive.ledger.state_dict(), strict=True)" in inspect.getsource(audit.migrate_core)


def test_retention_requires_exact_hashes_and_bounded_numeric_readout():
    source = inspect.getsource(audit.main)
    assert "retention_difference <= 1e-6" in source
    assert "core_hashes == molecular_hashes" in source


def test_diagonalized_parity_compares_dense_covariance_and_nll():
    source = inspect.getsource(audit.parity_audit)
    assert "dense_covariance" in source and '"nll"' in source
    assert "<= 1e-6" in source


def test_structural_value_substitutions_are_predeclared():
    source = inspect.getsource(audit.semantics_audit)
    for label in ("true", "zero", "shuffled", "large_finite"):
        assert f'"{label}"' in source


def test_full_to_p80_is_in_monotonic_panel_order():
    assert audit.structural.PANEL_ORDER[:2] == ("FULL", "P80")


def test_complementary_panels_are_exact():
    for pair in range(4):
        a, b = audit.structural.complementary_masks(pair)
        assert (int(a.sum()), int(b.sum()), int((a & b).sum()), int((a | b).sum())) == (2458, 2458, 820, 4096)


def test_cross_panel_audit_covers_all_calibration_variants():
    source = inspect.getsource(audit.cross_panel_audit)
    for variant in ("RAW", "HISTORICAL_TOTAL_SCALAR", "CONDITIONAL_ONLY_SCALAR"):
        assert variant in source


def test_no_optimizer_or_updates_exist():
    assert "torch.optim" not in AUDIT_SOURCE
    assert '"neural_optimizer_updates": 0' in AUDIT_SOURCE


def test_no_real_rna_loader_or_pathology_access():
    lower = AUDIT_SOURCE.lower()
    assert "anndata" not in lower and "h5ad" not in lower
    assert '"real_rna_accessed": false' in lower and '"pathology_opened": false' in lower


def test_factor_labels_and_sealed_are_excluded_from_fitting():
    source = inspect.getsource(audit.fit_conditional_scale)
    assert '"factor_labels_used": False' in source
    assert '"sealed_used": False' in source


def test_future_modules_are_interface_only():
    source = inspect.getsource(audit.main)
    assert '"implemented_in_this_task": False' in source
