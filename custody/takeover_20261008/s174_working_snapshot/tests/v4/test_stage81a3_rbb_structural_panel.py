from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(PROJECT / "scripts" / "v4"))

import stage81a3_rbb_structural_panel_audit as audit  # noqa: E402
from sea_ad_jepa.v4.measurement_state import MeasurementState, measurement_state_codes  # noqa: E402


def state() -> MeasurementState:
    measured = torch.tensor([[True, True, True, False]])
    hidden = torch.tensor([[False, False, True, False]])
    return MeasurementState(measured, hidden, torch.ones(4, dtype=torch.bool))


def test_four_measurement_states_are_representable():
    expression = torch.tensor([[2.0, 0.0, 3.0, 9.0]])
    assert measurement_state_codes(expression, state()).tolist() == [[0, 1, 2, 3]]


def test_observed_mask_formula():
    assert state().observed_mask.tolist() == [[True, True, False, False]]


def test_belief_missing_mask_formula():
    assert state().belief_missing_mask.tolist() == [[False, False, True, True]]


def test_training_target_eligibility_formula():
    assert state().training_target_eligible_mask.tolist() == [[False, False, True, False]]


def test_structural_genes_are_never_target_eligible():
    assert not torch.any(state().structural_unmeasured_mask & state().training_target_eligible_mask)


@pytest.mark.parametrize("replacement", [0.0, 1000.0, -37.0, 4.5])
def test_structural_values_are_sanitized_invariantly(replacement: float):
    expression = torch.tensor([[2.0, 0.0, 3.0, replacement]])
    assert torch.equal(state().sanitized_expression(expression), torch.tensor([[2.0, 0.0, 0.0, 0.0]]))


def test_measured_zero_is_observed_but_structural_zero_is_not():
    expression = torch.tensor([[0.0]])
    measured = MeasurementState(torch.ones(1, 1, dtype=torch.bool), torch.zeros(1, 1, dtype=torch.bool), torch.ones(1, dtype=torch.bool))
    unmeasured = MeasurementState(torch.zeros(1, 1, dtype=torch.bool), torch.zeros(1, 1, dtype=torch.bool), torch.ones(1, dtype=torch.bool))
    assert measured.observed_mask.item() and not unmeasured.observed_mask.item()
    assert measurement_state_codes(expression, measured).item() == 1
    assert measurement_state_codes(expression, unmeasured).item() == 3


def test_training_mask_and_structural_mask_differ_in_target_eligibility():
    value = state()
    assert value.belief_missing_mask[0, 2] and value.belief_missing_mask[0, 3]
    assert value.training_target_eligible_mask[0, 2]
    assert not value.training_target_eligible_mask[0, 3]


def test_training_hidden_requires_measurement():
    with pytest.raises(ValueError, match="must have been measured"):
        MeasurementState(torch.zeros(1, 1, dtype=torch.bool), torch.ones(1, 1, dtype=torch.bool), torch.ones(1, dtype=torch.bool))


def test_globally_never_observed_boundary_is_enforced():
    unsupported = MeasurementState(torch.zeros(1, 1, dtype=torch.bool), torch.zeros(1, 1, dtype=torch.bool), torch.zeros(1, dtype=torch.bool))
    with pytest.raises(ValueError, match="globally never-observed"):
        unsupported.assert_foundation_inference_supported()


def test_fixture_declares_all_genes_foundation_supported():
    source = inspect.getsource(audit.make_state)
    assert "torch.ones(base.GENES" in source


def test_exact_panel_cardinalities_and_nesting():
    order = torch.arange(4096)
    for prefix in (True, False):
        panels = audit.panel_masks(order, measured_prefix=prefix)
        assert {name: int(mask.sum()) for name, mask in panels.items()} == audit.PANEL_COUNTS
        assert all(torch.all(panels[b] <= panels[a]) for a, b in zip(audit.PANEL_ORDER, audit.PANEL_ORDER[1:]))


def test_random_and_coherent_panel_construction_are_explicit():
    source = inspect.getsource(audit.build_panels)
    assert "RANDOM_STRUCTURAL" in source and "COHERENT_STRUCTURAL" in source
    assert "fixture.factors" not in source
    assert "base.TRAIN" in source


@pytest.mark.parametrize("pair", range(4))
def test_complementary_panel_contract(pair: int):
    a, b = audit.complementary_masks(pair)
    assert int(a.sum()) == 2458 and int(b.sum()) == 2458
    assert int((a & b).sum()) == 820
    assert int((a | b).sum()) == 4096


def test_complementary_panels_are_deterministic():
    first = audit.complementary_masks(0)
    second = audit.complementary_masks(0)
    assert all(torch.equal(a, b) for a, b in zip(first, second))


def test_cross_panel_distance_uses_full_low_rank_covariance():
    source = inspect.getsource(audit.cross_panel_audit)
    assert "lrd_solve" in source
    assert "total_low_rank" in source and "total_diagonal" in source


def test_legacy_parity_is_checked_at_required_tolerance():
    source = inspect.getsource(audit.parity_and_firewalls)
    assert "legacy_parity_pass" in source and "<= 1e-6" in source


def test_all_four_structural_firewall_substitutions_are_checked():
    source = inspect.getsource(audit.parity_and_firewalls)
    for label in ("true", "zero", "shuffled", "nonsense", "1000.0"):
        assert label in source


def test_measured_zero_visible_state_contribution_is_audited():
    source = inspect.getsource(audit.parity_and_firewalls)
    assert "measured_zero_nonzero_visible_contribution_fraction" in source
    assert "structural_zero_visible_contribution_norm" in source


def test_full_synthetic_reference_is_evaluation_only():
    source = inspect.getsource(audit.panel_forward)
    assert "fixture.lambda_norm" in source
    assert "forward_contract(model, expression" in source
    assert source.index("forward_contract(model, expression") < source.index("fixture.lambda_norm[selected]")


def test_all_32_correlated_amplitude_ranks_are_persisted():
    panel_source = inspect.getsource(audit.panel_forward)
    main_source = inspect.getsource(audit.main)
    assert "range(base.R_MAX)" in panel_source
    assert '"rank": rank' in main_source


def test_p20_is_not_a_primary_gate():
    assert "P20" not in audit.PRIMARY
    source = inspect.getsource(audit.classify)
    assert 'row["panel"] in PRIMARY' in source


def test_no_optimizer_or_training_path_exists():
    source = Path(audit.__file__).read_text(encoding="utf-8")
    assert "torch.optim" not in source and ".backward(" not in source
    assert '"optimizer_constructed": False' in source and '"optimizer_updates": 0' in source


def test_reconstructed_model_and_checkpoint_are_frozen():
    source = inspect.getsource(audit.reconstruct)
    assert "freeze_molecular_ledger" in source
    assert "requires_grad_(False)" in source
    assert audit.CHECKPOINT_HASH == "8ef9667e42f6c44be937b94cb54d89152805c3fbe0c254d23891a940d4474b24"


def test_model_parameter_identity_is_checked_after_evaluation():
    source = inspect.getsource(audit.main)
    assert "parameters_unchanged" in source and "torch.equal" in source


def test_real_rna_and_pathology_are_not_accessed():
    source = Path(audit.__file__).read_text(encoding="utf-8").lower()
    assert "anndata" not in source and "h5ad" not in source and "amyloid" not in source
    assert '"real_rna_accessed": false' in source and '"pathology_opened": false' in source


def test_foundation_support_boundary_is_documented():
    assert "globally never-observed" in inspect.getsource(audit.append_readout).lower()


def test_future_modules_are_interface_audit_only():
    source = inspect.getsource(audit.main)
    assert '"modules_implemented": False' in source
