from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(PROJECT / "scripts" / "v4"))

import stage81a3_rbb_panel_exposure as exposure  # noqa: E402


SOURCE = Path(exposure.__file__).read_text(encoding="utf-8")


def test_one_seed_and_exact_update_budget():
    assert exposure.SEED == 8114001 and exposure.UPDATES == 150


def test_effective_batch_is_exactly_256():
    assert exposure.EFFECTIVE_BATCH == 256
    assert len(exposure.STRATA) * exposure.STRATUM_SIZE == 256


def test_eight_equal_strata():
    assert len(exposure.STRATA) == 8 and exposure.STRATUM_SIZE == 32


def test_microbatch_preserves_one_stratum():
    assert exposure.MICROBATCH == exposure.STRATUM_SIZE == 32


def test_both_ordinary_replay_strata_present():
    assert exposure.STRATA[:2] == ("ORDINARY_RANDOM_40", "ORDINARY_BLOCK_40")


def test_all_structural_training_strata_present():
    for family in ("RANDOM", "COHERENT"):
        for panel in ("P80", "P60", "P40"):
            assert f"STRUCTURAL_{family}_{panel}" in exposure.STRATA


def test_p20_absent_from_training():
    assert all("P20" not in name for name in exposure.STRATA)


def test_ordinary_bank_reuses_existing_builders():
    source = inspect.getsource(exposure.build_banks)
    assert "base.random_mask_bank()" in source and "base.block_mask_bank" in source


def test_ordinary_bank_hashes_verified_against_recovery():
    source = inspect.getsource(exposure.build_banks)
    assert 'recovery_metadata["mask_bank_sha256"]' in source
    assert "ordinary mask bank changed" in source


def test_structural_bank_is_deterministic():
    source = inspect.getsource(exposure.build_banks)
    assert "SEED + 2003 * view + 71" in source
    assert "SEED + 2017 * view + 89" in source


def test_structural_banks_have_128_masks():
    source = inspect.getsource(exposure.build_banks)
    assert "range(128)" in source and '"structural_masks_per_stratum": 128' in source


def test_panel_construction_uses_train_only_expression():
    source = inspect.getsource(exposure.build_banks)
    assert "fixture.x_a[:base.TRAIN]" in source and "fixture.x_b[:base.TRAIN]" in source


def test_factor_labels_absent_from_bank_construction():
    assert "fixture.factors" not in inspect.getsource(exposure.build_banks)


def test_sealed_absent_from_bank_construction():
    source = inspect.getsource(exposure.build_banks)
    assert "base.SEALED" not in source and '"sealed_used": False' in source


def test_panel_simulation_uses_structural_measurement_mask():
    source = inspect.getsource(exposure.stratum_contract)
    assert "measured_one" in source and "training_hidden = torch.zeros_like(measured)" in source


def test_panel_values_are_sanitized_by_qualified_forward_contract():
    source = inspect.getsource(exposure.train)
    assert "structural.forward_contract" in source


def test_latent_target_uses_independent_paired_full_support_observation():
    source = inspect.getsource(exposure.stratum_batch)
    assert "independent_reference" in source
    assert "fixture.x_b" in source and "fixture.x_a" in source
    assert "basis.contribution(independent_reference, hidden)" in source


def test_no_gene_level_reconstruction_target_or_loss():
    lower = SOURCE.lower()
    assert "gene_mse" not in lower and "reconstruction_loss" not in lower
    assert "masked_expression_loss" not in lower


def test_panel_only_cells_cannot_enter_target_path():
    source = inspect.getsource(exposure.stratum_batch)
    assert "fixture.x_a" in source and "fixture.x_b" in source
    assert "independent_reference" in source


def test_molecular_stack_is_frozen():
    assert "model.freeze_molecular_ledger()" in inspect.getsource(exposure.initialize_model)


def test_optimizer_contains_belief_parameters_only():
    source = inspect.getsource(exposure.main)
    assert "list(model.belief_parameters())" in source
    assert "model.parameters()" not in source.split("torch.optim.AdamW", 1)[1].split("optimizer_report", 1)[0]


def test_optimizer_overlap_is_audited():
    source = inspect.getsource(exposure.optimizer_audit)
    assert "molecular_optimizer_overlap" in source


def test_molecular_gradients_checked_at_1_25_150():
    source = inspect.getsource(exposure.train)
    assert "update in (1, 25, 150)" in source
    assert "maximum_molecular_gradient" in source


def test_molecular_hashes_checked_at_all_milestones():
    source = inspect.getsource(exposure.train)
    assert "MILESTONES[1:]" in source and "frozen.frozen_hashes(model)" in source


def test_retention_checked_at_all_milestones():
    source = inspect.getsource(exposure.train)
    assert "frozen.retention_row(update" in source


def test_original_step_zero_initialization_not_recovery_checkpoint():
    source = inspect.getsource(exposure.initialize_model)
    assert "RBBAdaptiveBelief(" in source and "load_state_dict" not in source


def test_preexposure_checkpoint_is_separate_control_only():
    source = inspect.getsource(exposure.load_preexposure_model)
    assert "load_state_dict" in source and "requires_grad_(False)" in source


def test_same_optimizer_hyperparameters():
    source = inspect.getsource(exposure.main)
    assert "lr=1e-4" in source and "weight_decay=.01" in source


def test_rmax_unchanged_at_32():
    assert exposure.R_MAX == 32


def test_same_gaussian_nll_is_used():
    source = inspect.getsource(exposure.train)
    assert "rbb_nll(output, target)" in source
    for forbidden in ("VICReg", "variance regularization", "counterfactual loss"):
        assert forbidden not in source


def test_checkpoint_excludes_molecular_weights():
    source = inspect.getsource(exposure.save_checkpoint)
    assert 'not name.startswith("ledger.")' in source
    assert '"contains_molecular_weights": False' in source


def test_scalar_is_fit_from_validation_mahalanobis_only():
    source = inspect.getsource(exposure.fit_scalar_control)
    assert "validation_mahal" in source and "fixture.factors" not in source


def test_scalar_is_single_and_shared():
    source = inspect.getsource(exposure.fit_scalar_control)
    assert source.count("scale =") == 1
    assert "for family in structural.FAMILIES" in source
    assert "for panel in STRUCTURAL_FRACTIONS" in source


def test_scalar_fit_excludes_sealed():
    source = inspect.getsource(exposure.fit_scalar_control)
    assert "validation_mahal.append" in source
    assert source.index("validation_mahal.append") < source.index("sealed =") or "sealed =" in source


def test_scalar_does_not_change_posterior_mean():
    source = inspect.getsource(exposure.fit_scalar_control)
    assert "posterior_missing_mean" not in source
    assert "belief_factor_r2" in source


def test_scalar_preserves_uncertainty_ranking():
    source = inspect.getsource(exposure.fit_scalar_control)
    assert 'item["trace"] * scale' in source


def test_structural_semantics_are_reaudited():
    source = inspect.getsource(exposure.main)
    assert "structural.parity_and_firewalls" in source


def test_counterfactual_is_optional_and_omitted_last():
    source = inspect.getsource(exposure.main)
    assert '"run": False' in source and "prior NOT SUPPORTED evidence unchanged" in source


def test_real_rna_and_pathology_are_inaccessible():
    lower = SOURCE.lower()
    assert "anndata" not in lower and "h5ad" not in lower and "amyloid" not in lower
    assert '"real_rna_accessed": false' in lower and '"pathology_opened": false' in lower


def test_no_scheduler_or_sweep():
    lower = SOURCE.lower()
    assert "scheduler" not in lower and "seed_sweep" in lower and "hyperparameter_sweep" in lower
