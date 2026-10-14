from __future__ import annotations

import importlib.util

import pytest

BINDING = "a" * 64
ENVELOPE_SHA = "b" * 64
REF_SHA = "c" * 64


def _load():
    name = "scripts.v5.td_real_g2_content_decision_v2"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    import scripts.v5.td_real_g2_content_decision_v2 as G
    return G


def _baseline_ids_c1():
    return (
        "constant_train_mean",
        "technical_operator_only",
        "address_support_operator",
        "matched_wrong_cell",
        "identity_support_only",
    )


def _envelope(*, support_state="SUPPORTED", donors=8, strata=(("SEA_AD", "PRIMARY"),)):
    units = []
    for source, endpoint in strata:
        for i in range(donors):
            units.append({
                "source": source,
                "endpoint": endpoint,
                "donor_id": f"{source}_D{i:02d}",
                "support_state": support_state,
            })
    return {
        "schema": "JEPA_TD_REAL_G2_CLAIM_ENVELOPE_V2",
        "candidate_id": "C1_SHARED_EMERGENT",
        "input_binding_sha256": BINDING,
        "claim_envelope_receipt_sha256": ENVELOPE_SHA,
        "frozen_before_values": True,
        "units": units,
    }


def _rows(*, candidate=0.8, donors=8, strata=(("SEA_AD", "PRIMARY"),), baseline_ids=None):
    baseline_ids = tuple(baseline_ids or _baseline_ids_c1())
    rows = []
    for source, endpoint in strata:
        for i in range(donors):
            rows.append({
                "source": source,
                "endpoint": endpoint,
                "donor_id": f"{source}_D{i:02d}",
                "candidate_score": float(candidate),
                "baseline_scores": {b: 0.2 for b in baseline_ids},
                "support_state": "SUPPORTED",
                "input_binding_sha256": BINDING,
            })
    return rows


def _reference(rows, *, margin=0.1):
    return {
        "schema": "JEPA_TD_REAL_G2_REFERENCE_MARGIN_V2",
        "frozen": True,
        "qualified": True,
        "metric": "HELD_OUT_DONOR_PRIMARY_ENDPOINT_SCORE",
        "orientation": "LARGER_IS_BETTER",
        "input_binding_sha256": BINDING,
        "reference_receipt_sha256": REF_SHA,
        "independent_non_degenerate_reference": True,
        "margins": {
            f'{r["source"]}::{r["endpoint"]}::{r["donor_id"]}': float(margin)
            for r in rows if r["support_state"] == "SUPPORTED"
        },
    }


def test_baseline_family_is_derived_from_candidate_registry_not_caller_selected():
    G = _load()
    assert G.baseline_ids_for_candidate("C1_SHARED_EMERGENT") == _baseline_ids_c1()
    rows = _rows(baseline_ids=["constant_train_mean"])
    with pytest.raises(G.G2DecisionV2Error, match="baseline family"):
        G.adjudicate_g2_v2(
            candidate_id="C1_SHARED_EMERGENT",
            rows=rows,
            claim_envelope=_envelope(),
            reference_artifact=_reference(rows),
            external_qualification_receipt_sha256=None,
        )


def test_required_strata_cannot_be_shrunk_by_dropping_a_failing_source():
    G = _load()
    strata = (("HVS", "PRIMARY"), ("SEA_AD", "PRIMARY"))
    rows = _rows(strata=strata)
    envelope = _envelope(strata=strata)
    dropped = [r for r in rows if r["source"] != "HVS"]
    with pytest.raises(G.G2DecisionV2Error, match="claim envelope|unit roster"):
        G.adjudicate_g2_v2(
            candidate_id="C1_SHARED_EMERGENT",
            rows=dropped,
            claim_envelope=envelope,
            reference_artifact=_reference(dropped),
            external_qualification_receipt_sha256=None,
        )


def test_support_relabel_cannot_turn_a_required_supported_donor_into_abstention():
    G = _load()
    rows = _rows()
    rows[0] = dict(rows[0], support_state="UNSUPPORTED_STRUCTURAL")
    with pytest.raises(G.G2DecisionV2Error, match="support state"):
        G.adjudicate_g2_v2(
            candidate_id="C1_SHARED_EMERGENT",
            rows=rows,
            claim_envelope=_envelope(),
            reference_artifact=_reference(rows),
            external_qualification_receipt_sha256=None,
        )


def test_zero_margin_cannot_reduce_g2_to_direction_only():
    G = _load()
    rows = _rows(candidate=0.201)
    out = G.adjudicate_g2_v2(
        candidate_id="C1_SHARED_EMERGENT",
        rows=rows,
        claim_envelope=_envelope(),
        reference_artifact=_reference(rows, margin=0.0),
        external_qualification_receipt_sha256=None,
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "NONDEGENERATE_SUBSTANTIVE_MARGIN_NOT_ESTABLISHED"


def test_nonsignificant_positive_pattern_is_inconclusive_not_biological_fail():
    G = _load()
    rows = _rows(candidate=0.8, donors=10)
    # 9 positive beyond margin; one negative. At alpha=.01 this is not recurrent.
    rows[-1] = dict(rows[-1], candidate_score=0.0)
    out = G.adjudicate_g2_v2(
        candidate_id="C1_SHARED_EMERGENT",
        rows=rows,
        claim_envelope=_envelope(donors=10),
        reference_artifact=_reference(rows, margin=0.1),
        external_qualification_receipt_sha256=None,
    )
    detail = out["stratum_details"]["SEA_AD::PRIMARY"]
    assert detail["diagnostic_status"] == "INCONCLUSIVE"
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["human_pass_fail_authorized"] is False


def test_recurrent_nonpositive_content_is_distinct_diagnostic_but_not_human_fail():
    G = _load()
    rows = _rows(candidate=0.1)
    out = G.adjudicate_g2_v2(
        candidate_id="C1_SHARED_EMERGENT",
        rows=rows,
        claim_envelope=_envelope(),
        reference_artifact=_reference(rows, margin=0.1),
        external_qualification_receipt_sha256=None,
    )
    assert out["stratum_details"]["SEA_AD::PRIMARY"]["diagnostic_status"] == "NONADVANTAGE_RECURRENT_BEYOND_MARGIN"
    assert out["status"] == "NOT_ESTIMABLE"


def test_nonfinite_value_is_numerical_failure_not_exception_or_biological_fail():
    G = _load()
    rows = _rows()
    rows[2] = dict(rows[2], candidate_score=float("nan"))
    out = G.adjudicate_g2_v2(
        candidate_id="C1_SHARED_EMERGENT",
        rows=rows,
        claim_envelope=_envelope(),
        reference_artifact=_reference(rows),
        external_qualification_receipt_sha256=None,
    )
    assert out["status"] == "NUMERICAL_FAILURE"
    assert out["human_pass_fail_authorized"] is False


def test_alpha_is_frozen_and_caller_cannot_change_it():
    G = _load()
    rows = _rows()
    with pytest.raises(G.G2DecisionV2Error, match="alpha"):
        G.adjudicate_g2_v2(
            candidate_id="C1_SHARED_EMERGENT",
            rows=rows,
            claim_envelope=_envelope(),
            reference_artifact=_reference(rows),
            external_qualification_receipt_sha256=None,
            alpha=0.05,
        )


def test_literal_external_token_cannot_unlock_human_pass_fail():
    G = _load()
    rows = _rows()
    out = G.adjudicate_g2_v2(
        candidate_id="C1_SHARED_EMERGENT",
        rows=rows,
        claim_envelope=_envelope(),
        reference_artifact=_reference(rows),
        external_qualification_receipt_sha256="f" * 64,
    )
    assert out["diagnostic_status"] == "PASS"
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "SEALED_G2_DECISION_QUALIFICATION_NOT_FROZEN"
    assert out["human_pass_fail_authorized"] is False


def test_authority_remains_closed():
    G = _load()
    rows = _rows()
    out = G.adjudicate_g2_v2(
        candidate_id="C1_SHARED_EMERGENT",
        rows=rows,
        claim_envelope=_envelope(),
        reference_artifact=_reference(rows),
        external_qualification_receipt_sha256=None,
    )
    assert all(v is False for v in out["authority"].values())
