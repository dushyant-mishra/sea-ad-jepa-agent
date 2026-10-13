from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_quantitative_components_v1 as Q  # noqa: E402


def test_directional_donor_contrast_maps_frozen_sign_resolution_to_status():
    passed = Q.directional_donor_contrast(
        [{"donor_id": f"D{i}", "delta": 1.0} for i in range(1, 9)],
        alpha_eff=0.01,
    )
    assert passed["status"] == "NOT_ESTIMABLE"  # 8 donors cannot resolve two-sided 0.01
    assert passed["raw_sufficient_statistics"]["n_nonzero_donors"] == 8

    passed = Q.directional_donor_contrast(
        [{"donor_id": f"D{i}", "delta": 1.0} for i in range(1, 10)],
        alpha_eff=0.01,
    )
    assert passed["status"] == "PASS"
    assert passed["raw_sufficient_statistics"]["two_sided_p"] <= 0.01

    failed = Q.directional_donor_contrast(
        [
            {"donor_id": "D1", "delta": 1.0},
            {"donor_id": "D2", "delta": -1.0},
            {"donor_id": "D3", "delta": 1.0},
            {"donor_id": "D4", "delta": -1.0},
            {"donor_id": "D5", "delta": 1.0},
            {"donor_id": "D6", "delta": -1.0},
            {"donor_id": "D7", "delta": 1.0},
            {"donor_id": "D8", "delta": -1.0},
            {"donor_id": "D9", "delta": 1.0},
        ],
        alpha_eff=0.01,
    )
    assert failed["status"] == "FAIL"


def test_directional_donor_contrast_refuses_duplicate_donor_identity():
    with pytest.raises(Exception):
        Q.directional_donor_contrast(
            [{"donor_id": "D1", "delta": 1.0}, {"donor_id": "D1", "delta": 2.0}],
            alpha_eff=0.05,
        )


def test_noncompensating_status_preserves_fail_and_not_estimable():
    assert Q.noncompensating_status(["PASS", "PASS"]) == "PASS"
    assert Q.noncompensating_status(["PASS", "NOT_ESTIMABLE"]) == "NOT_ESTIMABLE"
    assert Q.noncompensating_status(["PASS", "NOT_ESTIMABLE", "FAIL"]) == "FAIL"
    with pytest.raises(Q.QuantitativeComponentError):
        Q.noncompensating_status([])
    with pytest.raises(Q.QuantitativeComponentError):
        Q.noncompensating_status(["PASS", "UNKNOWN"])


def test_required_strata_status_requires_exact_frozen_stratum_set():
    statuses = {"HVS": "PASS", "NPH52": "NOT_ESTIMABLE", "SEA_AD": "PASS"}
    out = Q.required_strata_status(statuses, required_strata=["HVS", "NPH52", "SEA_AD"])
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["strata"] == statuses

    with pytest.raises(Q.QuantitativeComponentError):
        Q.required_strata_status({"HVS": "PASS", "SEA_AD": "PASS"}, required_strata=["HVS", "NPH52", "SEA_AD"])
    with pytest.raises(Q.QuantitativeComponentError):
        Q.required_strata_status({"HVS": "PASS", "NPH52": "PASS", "SEA_AD": "PASS", "EXTRA": "PASS"}, required_strata=["HVS", "NPH52", "SEA_AD"])


def test_components_are_explicitly_not_gate_executors_or_authority():
    assert Q.CLAIM_BOUNDARY == "REUSABLE_STATISTICAL_COMPONENTS_ONLY__NOT_GATE_RULES__NO_REAL_TD_AUTHORITY"
    assert all(value is False for value in Q.NO_AUTHORITY.values())
