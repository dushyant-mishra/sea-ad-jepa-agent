from __future__ import annotations

import importlib.util

BASELINES = ("constant_train_mean", "technical_operator_only")
STRATA = (("HVS", "PRIMARY"),)


def _load(name: str):
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required G2 V2 repair module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _contract(**updates):
    out = {
        "schema": "JEPA_TD_REAL_G2_DECISION_CONTRACT_V2",
        "candidate_id": "C1",
        "metric": "HELD_OUT_DONOR_PRIMARY_ENDPOINT_SCORE",
        "orientation": "LARGER_IS_BETTER",
        "metric_manifest_sha256": "1" * 64,
        "input_binding_sha256": "a" * 64,
        "baseline_ids": list(BASELINES),
        "required_strata": [[s, e] for s, e in STRATA],
        "comparator_rule": "ALL_FROZEN_BASELINES_SEPARATELY_NONCOMPENSATING",
        "family_alpha": 0.01,
        "support_envelope_receipt_sha256": "2" * 64,
        "contract_receipt_sha256": "3" * 64,
        "frozen_before_values": True,
    }
    out.update(updates)
    return out


def _support(donors=None):
    donors = donors or [f"D{i:02d}" for i in range(10)]
    return {
        "schema": "JEPA_TD_REAL_G2_SUPPORT_ENVELOPE_V2",
        "receipt_sha256": "2" * 64,
        "frozen_before_values": True,
        "source_endpoint_donor_status": {
            "HVS::PRIMARY": {d: "SUPPORTED" for d in donors},
        },
    }


def _qual():
    return {
        "schema": "JEPA_TD_REAL_G2_DECISION_QUALIFICATION_RECEIPT_V2",
        "status": "PASS_KNOWN_TRUTH_G2_DECISION_V2",
        "producer_code_sha256": "4" * 64,
        "qualification_worlds_sha256": "5" * 64,
        "receipt_sha256": "6" * 64,
        "human_semantics_qualified": True,
    }


def _reference(donors=None, margin=0.10):
    donors = donors or [f"D{i:02d}" for i in range(10)]
    margins = {}
    for donor in donors:
        for baseline in BASELINES:
            margins[f"HVS::PRIMARY::{donor}::{baseline}"] = float(margin)
    return {
        "schema": "JEPA_TD_REAL_G2_REFERENCE_MARGIN_V2",
        "frozen": True,
        "qualified": True,
        "metric": "HELD_OUT_DONOR_PRIMARY_ENDPOINT_SCORE",
        "orientation": "LARGER_IS_BETTER",
        "metric_manifest_sha256": "1" * 64,
        "input_binding_sha256": "a" * 64,
        "decision_contract_receipt_sha256": "3" * 64,
        "support_envelope_receipt_sha256": "2" * 64,
        "reference_receipt_sha256": "7" * 64,
        "producer_code_sha256": "8" * 64,
        "producer_qualification_receipt_sha256": "9" * 64,
        "margin_units_sha256": "b" * 64,
        "margin_is_non_degenerate": margin > 0.0,
        "margins": margins,
    }


def _rows(deltas_by_baseline=None, donors=None, extra_stratum=False, nonfinite=False):
    donors = donors or [f"D{i:02d}" for i in range(10)]
    if deltas_by_baseline is None:
        deltas_by_baseline = {b: [0.5] * len(donors) for b in BASELINES}
    rows = []
    for i, donor in enumerate(donors):
        baseline_scores = {b: 0.20 for b in BASELINES}
        # Candidate score is shared. Tests that need distinct baseline deltas use
        # baseline-specific baseline scores below.
        candidate = 0.20 + max(deltas_by_baseline[b][i] for b in BASELINES)
        for b in BASELINES:
            baseline_scores[b] = candidate - deltas_by_baseline[b][i]
        if nonfinite and i == 0:
            candidate = float("nan")
        rows.append({
            "source": "HVS", "endpoint": "PRIMARY", "donor_id": donor,
            "candidate_score": candidate, "baseline_scores": baseline_scores,
            "input_binding_sha256": "a" * 64,
        })
    if extra_stratum:
        rows.append({
            "source": "SEA_AD", "endpoint": "EXTRA", "donor_id": "X00",
            "candidate_score": 1.0,
            "baseline_scores": {b: 0.0 for b in BASELINES},
            "input_binding_sha256": "a" * 64,
        })
    return rows


def test_baseline_family_is_frozen_in_contract_and_subset_cannot_rescue():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    bad = _contract(baseline_ids=[BASELINES[0]])
    out = G.adjudicate_g2_v2(rows=_rows(), decision_contract=bad, support_envelope=_support(), reference_artifact=_reference(), decision_qualification_receipt=_qual())
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "DECISION_CONTRACT_NOT_AUTHENTICATED"


def test_missing_or_extra_required_stratum_cannot_shrink_or_expand_scope():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    out = G.adjudicate_g2_v2(rows=_rows(extra_stratum=True), decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(), decision_qualification_receipt=_qual())
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "UNDECLARED_STRATUM_ROWS_PRESENT"
    empty_support = _support(); empty_support["source_endpoint_donor_status"] = {}
    out2 = G.adjudicate_g2_v2(rows=[], decision_contract=_contract(), support_envelope=empty_support, reference_artifact=_reference(), decision_qualification_receipt=_qual())
    assert out2["status"] == "NOT_ESTIMABLE"


def test_support_envelope_is_authority_not_caller_row_label():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    support = _support(); support["receipt_sha256"] = "c" * 64
    out = G.adjudicate_g2_v2(rows=_rows(), decision_contract=_contract(), support_envelope=support, reference_artifact=_reference(), decision_qualification_receipt=_qual())
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "SUPPORT_ENVELOPE_NOT_AUTHENTICATED"


def test_zero_only_margin_cannot_reduce_g2_to_direction_only():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    out = G.adjudicate_g2_v2(rows=_rows(), decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(margin=0.0), decision_qualification_receipt=_qual())
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "NON_DEGENERATE_SUBSTANTIVE_MARGIN_REQUIRED"


def test_nine_of_ten_positive_but_not_significant_is_inconclusive_not_biological_fail():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    deltas = [0.5] * 9 + [-0.5]
    rows = _rows({b: deltas for b in BASELINES})
    out = G.adjudicate_g2_v2(rows=rows, decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(margin=0.0 + 0.1), decision_qualification_receipt=_qual())
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "INCONCLUSIVE_DONOR_RECURRENCE_AT_FROZEN_ALPHA"


def test_candidate_equal_or_worse_than_all_baselines_is_estimable_fail_not_ne():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    rows = _rows({b: [0.0] * 10 for b in BASELINES})
    out = G.adjudicate_g2_v2(rows=rows, decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(margin=0.1), decision_qualification_receipt=_qual())
    assert out["status"] == "FAIL"


def test_every_frozen_baseline_is_noncompensating():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    rows = _rows({BASELINES[0]: [0.5] * 10, BASELINES[1]: [-0.5] * 10})
    out = G.adjudicate_g2_v2(rows=rows, decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(margin=0.1), decision_qualification_receipt=_qual())
    assert out["status"] == "FAIL"
    assert out["component_status"]["HVS::PRIMARY::technical_operator_only"] == "FAIL"


def test_nonfinite_input_returns_numerical_failure_not_exception_or_biological_fail():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    out = G.adjudicate_g2_v2(rows=_rows(nonfinite=True), decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(), decision_qualification_receipt=_qual())
    assert out["status"] == "NUMERICAL_FAILURE"


def test_alpha_is_frozen_and_not_caller_tunable():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    assert G.FAMILY_ALPHA == 0.01
    try:
        G.adjudicate_g2_v2(rows=_rows(), decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(), decision_qualification_receipt=_qual(), alpha=0.05)
    except TypeError:
        pass
    else:
        raise AssertionError("G2 V2 must not expose caller-tunable alpha")


def test_typed_qualification_token_without_hash_custody_is_not_sufficient():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    fake = {"schema": "JEPA_TD_REAL_G2_DECISION_QUALIFICATION_RECEIPT_V2", "status": "PASS_KNOWN_TRUTH_G2_DECISION_V2", "human_semantics_qualified": True}
    out = G.adjudicate_g2_v2(rows=_rows(), decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(), decision_qualification_receipt=fake)
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "DECISION_QUALIFICATION_RECEIPT_NOT_AUTHENTICATED"


def test_authority_remains_closed():
    G = _load("scripts.v5.td_real_g2_content_decision_v2")
    out = G.adjudicate_g2_v2(rows=_rows(), decision_contract=_contract(), support_envelope=_support(), reference_artifact=_reference(), decision_qualification_receipt=_qual())
    assert all(v is False for v in out["authority"].values())
