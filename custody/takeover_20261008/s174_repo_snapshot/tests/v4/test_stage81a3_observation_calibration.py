from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import pytest
import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(PROJECT / "scripts" / "v4"))

import stage81a3_rbb_core_simplification_audit as audit  # noqa: E402
from sea_ad_jepa.v4.observation_calibration import (  # noqa: E402
    apply_observation_calibration, fit_conditional_only_scale,
)


def fixture():
    conditional = torch.tensor([[4.0, 9.0]])
    low_rank = torch.tensor([[[1.0], [2.0]]])
    noise = torch.tensor([[0.5, 1.5]])
    return conditional, low_rank, noise


def test_ordinary_requires_unit_scale():
    with pytest.raises(ValueError, match="ordinary regime"):
        apply_observation_calibration(*fixture(), regime="ordinary_raw", scale=.5)


def test_ordinary_preserves_raw_total_exactly():
    result = apply_observation_calibration(*fixture(), regime="ordinary_raw", scale=1.0)
    assert torch.equal(result.raw_total_diagonal, result.calibrated_total_diagonal)
    assert torch.equal(result.raw_total_low_rank, result.calibrated_total_low_rank)


def test_historical_scalar_scales_total_covariance():
    result = apply_observation_calibration(*fixture(), regime="historical_total_scalar", scale=.25)
    assert torch.equal(result.calibrated_total_diagonal, .25 * result.raw_total_diagonal)
    assert torch.equal(result.calibrated_total_low_rank, .5 * result.raw_total_low_rank)


def test_conditional_scalar_preserves_noise_floor():
    conditional, low_rank, noise = fixture()
    result = apply_observation_calibration(conditional, low_rank, noise, regime="conditional_only_scalar", scale=.25)
    assert torch.equal(result.calibrated_total_diagonal, noise + .25 * conditional)
    assert torch.equal(result.calibrated_total_low_rank, .5 * low_rank)


@pytest.mark.parametrize("scale", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_scales_rejected(scale):
    with pytest.raises(ValueError, match="positive and finite"):
        apply_observation_calibration(*fixture(), regime="conditional_only_scalar", scale=scale)


def test_unknown_regime_rejected():
    with pytest.raises(ValueError, match="unknown calibration regime"):
        apply_observation_calibration(*fixture(), regime="mystery", scale=1.0)


def test_raw_decomposition_is_never_erased():
    conditional, low_rank, noise = fixture()
    result = apply_observation_calibration(conditional, low_rank, noise, regime="conditional_only_scalar", scale=.4)
    assert torch.equal(result.raw_conditional_diagonal, conditional)
    assert torch.equal(result.measurement_noise_diagonal, noise)
    assert torch.equal(result.raw_total_diagonal, conditional + noise)


def test_calibration_has_no_mean_argument():
    assert "mean" not in inspect.signature(apply_observation_calibration).parameters


def test_conditional_fit_is_deterministic_and_positive():
    residual = torch.tensor([[1.0, -2.0], [.5, 1.5]])
    conditional, low_rank, noise = fixture()
    batch = (residual, conditional.expand(2, -1), low_rank.expand(2, -1, -1), noise.expand(2, -1))
    first = fit_conditional_only_scale([batch], iterations=24)
    second = fit_conditional_only_scale([batch], iterations=24)
    assert first == second and math.isfinite(first[0]) and first[0] > 0


def test_fit_method_is_golden_section_log_scale():
    residual = torch.zeros(1, 2); conditional, low_rank, noise = fixture()
    _, metadata = fit_conditional_only_scale([(residual, conditional, low_rank, noise)], iterations=4)
    assert metadata["method"] == "deterministic_golden_section_log_scale"


def test_historical_scalar_is_loaded_not_refit():
    source = inspect.getsource(audit.main)
    assert 'panel_report["scalar_recalibration"]' in source
    assert '"refitted_in_this_task": False' in source


def test_conditional_fit_uses_validation_indices_only():
    source = inspect.getsource(audit.fit_conditional_scale)
    assert 'selected = arrays["validation"]' in source
    assert '"fit_split": "VALIDATION"' in source


@pytest.mark.parametrize("family", ["RANDOM_STRUCTURAL", "COHERENT_STRUCTURAL"])
def test_conditional_fit_uses_both_families(family):
    assert family in audit.structural.FAMILIES
    assert "for family in structural.FAMILIES" in inspect.getsource(audit.fit_conditional_scale)


@pytest.mark.parametrize("panel", ["P80", "P60", "P40"])
def test_conditional_fit_uses_only_predeclared_fractions(panel):
    source = inspect.getsource(audit.fit_conditional_scale)
    assert 'for panel in ("P80", "P60", "P40")' in source
    assert panel in source


def test_conditional_scalar_is_one_shared_value():
    source = inspect.getsource(audit.fit_conditional_scale)
    assert source.count("fit_conditional_only_scale(batches)") == 1


def test_sealed_is_evaluation_only_not_fit_input():
    source = inspect.getsource(audit.fit_conditional_scale)
    assert 'arrays["sealed"]' not in source


def test_full_panel_remains_raw_during_structural_calibration():
    source = inspect.getsource(audit.structural_evaluation)
    assert 'panel != "FULL"' in source
    assert '("ordinary_raw", 1.0)' in source


def test_cross_panel_full_union_remains_raw():
    source = inspect.getsource(audit.cross_panel_audit)
    assert 'name != "FULL"' in source
    assert "FULL union remains raw scale 1" in source


def test_localization_gate_is_not_weakened():
    source = inspect.getsource(audit.main)
    assert "value > .50" in source


def test_calibration_and_localization_are_separate_gates():
    source = inspect.getsource(audit.main)
    assert '"structural_population_scale_calibration"' in source
    assert '"structural_cell_level_uncertainty_localization"' in source
