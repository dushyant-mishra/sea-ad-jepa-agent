from __future__ import annotations

import importlib
import importlib.util
import math

import pytest


def _load():
    name = "scripts.v5.td_real_g2_content_decision_v2"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    return importlib.import_module(name)


def _rows(deltas, *, source="SEA_AD", endpoint="PRIMARY", baseline_ids=("B0", "B1")):
    rows = []
    # baseline=0 and margin=1 make candidate score = 1 + adjusted delta.
    for i, delta in enumerate(deltas):
        rows.append({
            "source": source,
            "endpoint": endpoint,
            "donor_id": f"D{i:02d}",
            "candidate_score": 1.0 + delta,
            "baseline_scores": {b: 0.0 for b in baseline_ids},
            "support_state": "SUPPORTED",
            "input_binding_sha256": "a" * 64,
        })
    return rows


def _reference(rows, *, margin=1.0):
    G = _load()
    return {
        "schema": G.REFERENCE_SCHEMA,
        "frozen": True,
        "qualified": True,
        "metric": G.METRIC,
        "orientation": G.ORIENTATION,
        "reference_kind": "U_MEASUREMENT",
        "input_binding_sha256": "a" * 64,
        "reference_receipt_sha256": "b" * 64,
        "producer_code_sha256": "c" * 64,
        "margins": {
            f'{r["source"]}::{r["endpoint"]}::{r["donor_id"]}': margin
            for r in rows if r["support_state"] == "SUPPORTED"
        },
    }


def _run(deltas, **kwargs):
    G = _load()
    rows = _rows(deltas)
    return G.adjudicate_g2_mechanics_v2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY")],
        diagnostic_baseline_ids=["B0", "B1"],
        reference_artifact=_reference(rows),
        **kwargs,
    )


def test_g2_alpha_is_frozen_one_sided_gate_constant_not_runtime_argument():
    G = _load()
    assert G.G2_GATE_ALPHA == 0.01
    assert G.minimum_donors_for_one_sided_resolution(G.G2_GATE_ALPHA) == 7
    with pytest.raises(TypeError):
        G.adjudicate_g2_mechanics_v2(
            rows=_rows([1.0] * 8),
            required_strata=[("SEA_AD", "PRIMARY")],
            diagnostic_baseline_ids=["B0", "B1"],
            reference_artifact=_reference(_rows([1.0] * 8)),
            alpha=0.5,
        )


def test_nine_of_ten_positive_but_not_significant_is_not_biological_fail():
    out = _run([1.0] * 9 + [-1.0])
    assert out["status"] == "NOT_ESTIMABLE"
    detail = out["stratum_details"]["SEA_AD::PRIMARY"]
    assert detail["reason"] == "DIRECTION_NOT_RESOLVED_AT_FROZEN_ALPHA"
    assert detail["one_sided_positive_p"] > 0.01


def test_significant_negative_recurrence_is_biological_fail():
    out = _run([-1.0] * 8)
    assert out["status"] == "FAIL"
    assert out["stratum_details"]["SEA_AD::PRIMARY"]["reason"] == "ESTIMABLY_NONPOSITIVE"


def test_exact_equal_to_margin_across_resolved_donors_is_nonpositive_fail_not_ne():
    out = _run([0.0] * 8)
    assert out["status"] == "FAIL"
    detail = out["stratum_details"]["SEA_AD::PRIMARY"]
    assert detail["reason"] == "ESTIMABLY_NONPOSITIVE"
    assert detail["n_tied_donors"] == 8


def test_zero_reference_margin_cannot_create_tiny_positive_pass():
    G = _load()
    rows = _rows([0.001] * 8)
    ref = _reference(rows, margin=0.0)
    out = G.adjudicate_g2_mechanics_v2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY")],
        diagnostic_baseline_ids=["B0", "B1"],
        reference_artifact=ref,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "NONDEGENERATE_SUBSTANTIVE_MARGIN_REQUIRED"


def test_nan_or_infinite_deciding_number_returns_numerical_failure_not_exception():
    G = _load()
    for bad in (float("nan"), float("inf"), -float("inf")):
        rows = _rows([1.0] * 8)
        rows[0]["candidate_score"] = bad
        out = G.adjudicate_g2_mechanics_v2(
            rows=rows,
            required_strata=[("SEA_AD", "PRIMARY")],
            diagnostic_baseline_ids=["B0", "B1"],
            reference_artifact=_reference(rows),
        )
        assert out["status"] == "NUMERICAL_FAILURE"
        assert out["failed_biology"] is False


def test_unsupported_rows_do_not_require_fabricated_numeric_candidate_or_baselines():
    G = _load()
    rows = [{
        "source": "SEA_AD", "endpoint": "PRIMARY", "donor_id": "D00",
        "candidate_score": None, "baseline_scores": {},
        "support_state": "UNSUPPORTED_STRUCTURAL",
        "input_binding_sha256": "a" * 64,
    }]
    out = G.adjudicate_g2_mechanics_v2(
        rows=rows,
        required_strata=[("SEA_AD", "PRIMARY")],
        diagnostic_baseline_ids=["B0", "B1"],
        reference_artifact=_reference(rows),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["stratum_details"]["SEA_AD::PRIMARY"]["reason"] == "NO_SUPPORTED_DECIDING_DONORS"


def test_extra_stratum_rows_are_rejected_not_silently_dropped():
    G = _load()
    rows = _rows([1.0] * 8)
    rows += _rows([1.0] * 8, source="HVS")
    with pytest.raises(G.G2DecisionV2Error, match="extra stratum"):
        G.adjudicate_g2_mechanics_v2(
            rows=rows,
            required_strata=[("SEA_AD", "PRIMARY")],
            diagnostic_baseline_ids=["B0", "B1"],
            reference_artifact=_reference(rows),
        )


def test_missing_baseline_cannot_rescue_candidate_in_diagnostic_mechanics():
    G = _load()
    rows = _rows([1.0] * 8)
    rows[0]["baseline_scores"].pop("B1")
    with pytest.raises(G.G2DecisionV2Error, match="baseline family"):
        G.adjudicate_g2_mechanics_v2(
            rows=rows,
            required_strata=[("SEA_AD", "PRIMARY")],
            diagnostic_baseline_ids=["B0", "B1"],
            reference_artifact=_reference(rows),
        )


def test_typed_policy_cannot_authorize_human_g2_until_static_policy_is_produced():
    G = _load()
    out = G.human_execution_readiness(
        policy_artifact={
            "schema": "JEPA_TD_REAL_G2_POLICY_V1",
            "qualified": True,
            "candidate_id": "C1_SHARED_EMERGENT",
            "baseline_ids": ["constant_train_mean"],
            "required_strata": [["SEA_AD", "PRIMARY"]],
        }
    )
    assert out["status"] == "BLOCKED_G2_STATIC_POLICY_NOT_PRODUCED_AND_QUALIFIED"
    assert out["caller_baseline_family_has_human_authority"] is False
    assert out["caller_required_strata_have_human_authority"] is False
    assert out["human_g2_adjudication_authorized"] is False


def test_g2_v2_authority_remains_closed():
    G = _load()
    out = G.human_execution_readiness(policy_artifact={})
    assert all(value is False for value in out["authority"].values())
