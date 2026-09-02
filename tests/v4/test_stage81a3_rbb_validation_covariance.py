from __future__ import annotations

import inspect
import sys
from pathlib import Path

import torch

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from sea_ad_jepa.v4.oof_covariance import construct_lrd, lrd_gaussian_nll  # noqa: E402
from sea_ad_jepa.v4.validation_covariance import dense_gaussian_terms, oas_covariance  # noqa: E402

SCRIPT = PROJECT / "scripts/v4/stage81a3_rbb_validation_covariance_audit.py"


def test_full_train_predictor_uses_all_train_cells() -> None:
    text = SCRIPT.read_text()
    assert "all_train = torch.arange(TRAIN" in text
    assert "symmetric_prediction(" in text


def test_validation_is_excluded_from_conditional_mean_fitting() -> None:
    text = SCRIPT.read_text()
    assert "fitting=all_train" in text
    assert "validation_indices" not in text.split("fitting=all_train")[0]


def test_sealed_is_excluded_from_all_fitting_and_calibration() -> None:
    text = SCRIPT.read_text()
    assert '"sealed_used_for_fitting": False' in text
    assert '"sealed_used_for_rank_selection": False' in text


def test_sigma_val_uses_validation_residuals_only() -> None:
    text = SCRIPT.read_text()
    assert "sigma_val = covariance(validation_residual)" in text
    assert "oas_covariance(validation_residual)" in text


def test_architecture_rank_is_fixed_at_nine() -> None:
    text = SCRIPT.read_text()
    assert "ARCHITECTURE_RANK = 9" in text
    assert "construct_lrd(sigma_val, ARCHITECTURE_RANK)" in text


def test_classification_is_conservative_across_mask_families() -> None:
    text = SCRIPT.read_text()
    config = (PROJECT / "configs/v4/stage81a3_rbb_validation_covariance.yaml").read_text()
    assert "all(rank9_family_adequate.values())" in text
    assert "any(oas_exposes_underexpression.values())" in text
    assert "family_median_then_conservative_across_families" in config


def test_oas_matches_analytic_reference() -> None:
    torch.manual_seed(8)
    values = torch.randn(40, 6, dtype=torch.float64)
    actual, shrinkage, mu = oas_covariance(values)
    centered = values - values.mean(0)
    empirical = centered.T @ centered / len(values)
    expected_mu = torch.trace(empirical) / 6
    alpha = empirical.square().mean()
    expected_shrinkage = min(float((alpha + expected_mu.square()) / ((41) * (alpha - expected_mu.square() / 6))), 1.0)
    expected = (
        (1 - expected_shrinkage) * empirical
        + expected_shrinkage * expected_mu * torch.eye(6, dtype=torch.float64)
    )
    torch.testing.assert_close(actual, expected, rtol=1e-12, atol=1e-12)
    assert shrinkage == expected_shrinkage
    assert mu == float(expected_mu)


def test_oas_has_no_manual_shrinkage_parameter() -> None:
    assert set(inspect.signature(oas_covariance).parameters) == {"values"}


def test_rank_nine_lrd_is_positive_definite() -> None:
    values = torch.randn(512, 160)
    covariance = torch.cov(values.T)
    lrd = construct_lrd(covariance, 9)
    assert lrd["u"].shape == (160, 9)
    assert torch.linalg.eigvalsh(lrd["matrix"]).min() > 0


def test_woodbury_rank_nine_matches_dense_nll() -> None:
    torch.manual_seed(9)
    values = torch.randn(30, 12, dtype=torch.float64)
    covariance = torch.cov(torch.randn(100, 12, dtype=torch.float64).T)
    lrd = construct_lrd(covariance, 9)
    woodbury = lrd_gaussian_nll(values, lrd["diagonal"], lrd["u"])
    dense = dense_gaussian_terms(values, lrd["matrix"])[0]
    torch.testing.assert_close(woodbury, dense, rtol=1e-10, atol=1e-10)


def test_sealed_scoring_is_read_only() -> None:
    text = SCRIPT.read_text()
    score_position = text.index("sealed_residual =")
    assert "ridge_fit(" not in text[score_position:]
    assert "oas_covariance(" not in text[score_position:]


def test_factor_labels_are_absent_from_fitting() -> None:
    assert "fixture.factors" not in SCRIPT.read_text()


def test_lambda_norm_is_absent_from_fitting() -> None:
    assert "fixture.lambda_norm" not in SCRIPT.read_text()


def test_real_rna_is_inaccessible() -> None:
    text = SCRIPT.read_text().lower()
    assert "h5ad" not in text and "real_rna_accessed\": false" in text


def test_pathology_is_inaccessible() -> None:
    text = SCRIPT.read_text().lower()
    assert "data/pathology" not in text and "pathology_opened\": false" in text
