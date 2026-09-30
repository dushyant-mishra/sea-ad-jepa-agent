from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    ss_res = np.square(y_true - y_pred).sum(axis=0)
    centered = y_true - y_true.mean(axis=0, keepdims=True)
    ss_tot = np.square(centered).sum(axis=0)
    good = ss_tot > 0
    return float(np.mean(1.0 - ss_res[good] / ss_tot[good]))


def _fit_linear(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x1 = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(x1, y, rcond=None)
    return coef


def _predict_linear(x: np.ndarray, coef: np.ndarray) -> np.ndarray:
    x1 = np.column_stack([np.ones(len(x)), x])
    return x1 @ coef


def test_current_runtime_is_rna_to_rna_and_not_silently_multimodal():
    src = (ROOT / "src/sea_ad_jepa/v5/inactive_update_reference.py").read_text()
    assert "teacher_state=modules.teacher" in src
    assert "student_state=modules.online" in src
    assert "mb_expr=expression[ridx]" in src
    assert "visible=mb_measured & ~blocks.hidden_mask" in src
    # A future privileged teacher requires an explicit successor, not a silent reinterpretation.
    semantics = (ROOT / "src/sea_ad_jepa/v5/teacher_target_semantics_authority_v2.py").read_text()
    assert "BIOLOGICAL_CELLULAR_LATENT_STATE_V1" in semantics
    assert "PRIVILEGED_PRIVATE" not in semantics
    assert "RNA_RECOVERABLE" not in semantics


def test_privileged_runtime_audit_is_fail_closed():
    p = json.loads(
        (ROOT / "results/v64/V64_PRIVILEGED_INFORMATION_RUNTIME_AUDIT_V1.json").read_text()
    )
    assert p["governance"]["training"] == "OFF"
    assert p["governance"]["runtime_modified"] is False
    assert "must not be silently reinterpreted" in p["architectural_conclusion"]


def test_recoverability_contract_preserves_private_state():
    p = json.loads(
        (ROOT / "results/v64/V64_PRIVILEGED_STATE_RECOVERABILITY_CONTRACT_V1.json").read_text()
    )
    assert p["target_object"] == "ROTATION_AWARE_RECOVERABLE_SUBSPACE"
    assert p["minimum_scientific_split"] == "DONOR_DISJOINT_TRAIN_VALIDATION_TEST"
    assert p["cell_random_split_scientific_authority"] is False
    assert p["test_set_may_select_rank"] is False
    assert p["test_set_may_select_rotation"] is False
    assert p["private_residual_must_be_preserved"] is True
    assert p["rna_only_cells_private_target_policy"] == "NO_TARGET_NO_ZERO_FILL_NO_COMPULSORY_LOSS"
    assert set(p["classes"]) == {
        "RNA_RECOVERABLE",
        "PARTIALLY_RNA_RECOVERABLE",
        "PRIVILEGED_PRIVATE",
        "UNQUALIFIED",
    }


def test_promoter_universe_is_annotation_first_not_activity_gated():
    text = (ROOT / "docs/agent/V64_PROMOTER_TSS_CANDIDATE_UNIVERSE_CONTRACT_20260930.md").read_text()
    assert "GENCODE" in text
    assert "must not be defined by measured activity" in text
    assert "Measurement resources may add evidence" in text
    assert "not measured" in text.lower()


def test_common_support_contract_forbids_match_rescue_and_false_independence():
    text = (ROOT / "docs/agent/V64_COMMON_SUPPORT_AND_EVIDENCE_SENSITIVITY_CONTRACT_20260930.md").read_text()
    assert "trim it" in text
    assert "Do not progressively widen tolerances" in text
    assert "incremental support under observed adjustment" in text
    assert "SCARlink" in text and "SCENT" in text
    assert "It is not two independent biological confirmations" in text


def test_synthetic_smoke_shared_is_recoverable_private_is_not():
    # Software/architecture smoke only. This is deliberately not a biological threshold.
    rng = np.random.default_rng(20260930)
    n_train, n_test, p = 2400, 1200, 10
    shared_dim = private_dim = 4

    x_train = rng.normal(size=(n_train, p))
    x_test = rng.normal(size=(n_test, p))
    w = rng.normal(size=(p, shared_dim))

    shared_train = x_train @ w + 0.03 * rng.normal(size=(n_train, shared_dim))
    shared_test = x_test @ w + 0.03 * rng.normal(size=(n_test, shared_dim))

    # Privileged-private biology is intentionally independent of lawful RNA.
    private_train = rng.normal(size=(n_train, private_dim))
    private_test = rng.normal(size=(n_test, private_dim))

    # Equalize scale so full-state performance cannot hide private failure behind variance weighting.
    shared_sd = shared_train.std(axis=0, ddof=1)
    shared_train = shared_train / shared_sd
    shared_test = shared_test / shared_sd
    private_sd = private_train.std(axis=0, ddof=1)
    private_train = private_train / private_sd
    private_test = private_test / private_sd

    full_train = np.column_stack([shared_train, private_train])
    full_test = np.column_stack([shared_test, private_test])

    shared_hat = _predict_linear(x_test, _fit_linear(x_train, shared_train))
    private_hat = _predict_linear(x_test, _fit_linear(x_train, private_train))
    full_hat = _predict_linear(x_test, _fit_linear(x_train, full_train))

    r2_shared = _r2(shared_test, shared_hat)
    r2_private = _r2(private_test, private_hat)
    r2_full = _r2(full_test, full_hat)

    assert r2_shared > 0.98
    assert r2_private < 0.05
    # Forcing shared+private into one compulsory target necessarily obscures the recoverability boundary.
    assert r2_full < r2_shared - 0.20
    assert r2_full > r2_private + 0.20


def test_synthetic_smoke_private_failure_does_not_relabel_private_as_zero():
    rng = np.random.default_rng(64)
    private = rng.normal(size=(100, 3))
    measured = np.zeros(100, dtype=bool)
    # Missing privileged state is represented by a mask, not by zero-valued biology.
    stored = np.full(private.shape, np.nan)
    stored[measured] = private[measured]
    assert np.isnan(stored).all()
    assert not np.array_equal(stored, np.zeros_like(stored), equal_nan=False)
