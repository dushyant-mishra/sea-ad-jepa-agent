from __future__ import annotations

import importlib.util

SOURCES = ("HVS", "NPH52", "SEA_AD")
PATTERN = (1, 1, -1, 1, -1, -1, 1, -1, 1, 1, 1, -1)


def _load(name: str):
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required R1 V3 executor missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _contract():
    return {
        "schema": "JEPA_TD_REAL_R1_EXECUTION_CONTRACT_V3",
        "candidate_id": "C2_RELATIONAL_SHARED",
        "required_sources": list(SOURCES),
        "view_rule_sha256": "1" * 64,
        "tie_rule_sha256": "2" * 64,
        "tie_tolerance": 0.0,
        "null_stratum_fields": ["donor_id", "source", "operator_id", "support_stratum", "depth_detection_block"],
        "null_semantics": "RELATION_ID_PERMUTATION_WITHIN_DEPTH_DETECTION_MATCHED_STRATUM",
        "metric": "DONOR_MEAN_EXACT_TRIPLET_ORDER_AGREEMENT",
        "orientation": "LARGER_IS_BETTER",
        "family_alpha": 0.01,
        "null_draws_per_donor": 100,
        "frozen_before_values": True,
    }


def _qualification():
    return {
        "schema": "JEPA_TD_REAL_R1_DECISION_QUALIFICATION_RECEIPT_V3",
        "status": "PASS_KNOWN_TRUTH_R1_DEPTH_MATCHED_NULL_V3",
        "producer_code_sha256": "3" * 64,
        "qualification_worlds_sha256": "4" * 64,
        "receipt_sha256": "5" * 64,
        "technical_only_negative_passed": True,
        "planted_biology_positive_passed": True,
    }


def _donors(sources=SOURCES, n=8):
    return [f"{source}_D{i:02d}" for source in sources for i in range(n)]


def _reference(donors):
    return {
        "schema": "JEPA_TD_REAL_R1_REFERENCE_MARGIN_V3",
        "frozen": True,
        "qualified": True,
        "metric": "DONOR_MEAN_EXACT_TRIPLET_ORDER_AGREEMENT",
        "orientation": "LARGER_IS_BETTER",
        "input_binding_sha256": "a" * 64,
        "reference_receipt_sha256": "6" * 64,
        "producer_qualification_receipt_sha256": "7" * 64,
        "u_refit": {d: 0.01 for d in donors},
    }


def _rows(*, sources=SOURCES, donors_per_source=8, technical_only=False, biology=True):
    rows = []
    for source in sources:
        for di in range(donors_per_source):
            donor = f"{source}_D{di:02d}"
            for block in ("LOW_DEPTH", "HIGH_DEPTH"):
                # Twelve relation identities per block permit >=100 distinct
                # non-identity permutations. Technical-only concordance is wholly
                # block-driven; planted biology is identity-specific within block.
                for ri, planted in enumerate(PATTERN):
                    if technical_only:
                        x = 1 if block == "HIGH_DEPTH" else -1
                        y = x
                    elif biology:
                        x = planted
                        y = planted
                    else:
                        x = planted
                        y = -planted
                    rows.append({
                        "donor_id": donor,
                        "source": source,
                        "operator_id": f"{source}_OP1",
                        "support_stratum": "SUPPORTED",
                        "depth_detection_block": block,
                        "relation_id": f"{donor}:{block}:R{ri}",
                        "view_a_order": x,
                        "view_b_order": y,
                        "input_binding_sha256": "a" * 64,
                    })
    return rows


def test_null_contract_must_include_depth_detection_block():
    R = _load("scripts.v5.td_real_relational_executor_v3")
    bad = _contract(); bad["null_stratum_fields"] = ["donor_id", "source", "operator_id", "support_stratum"]
    out = R.adjudicate_r1_v3(
        rows=_rows(), contract=bad, decision_qualification_receipt=_qualification(),
        reference_artifact=_reference(_donors()), required_sources=list(SOURCES),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "NULL_STRATUM_CONTRACT_NOT_DEPTH_DETECTION_MATCHED"


def test_library_depth_only_world_cannot_pass_depth_matched_null():
    R = _load("scripts.v5.td_real_relational_executor_v3")
    out = R.adjudicate_r1_v3(
        rows=_rows(technical_only=True, biology=False), contract=_contract(),
        decision_qualification_receipt=_qualification(),
        reference_artifact=_reference(_donors()), required_sources=list(SOURCES),
    )
    assert out["status"] == "FAIL"
    assert all(out["source_details"][s]["technical_only_shortcut_rejected"] is True for s in SOURCES)


def test_planted_shared_relation_can_pass_same_depth_matched_null():
    R = _load("scripts.v5.td_real_relational_executor_v3")
    out = R.adjudicate_r1_v3(
        rows=_rows(technical_only=False, biology=True), contract=_contract(),
        decision_qualification_receipt=_qualification(),
        reference_artifact=_reference(_donors()), required_sources=list(SOURCES),
    )
    assert out["status"] == "PASS"


def test_view_and_tie_rules_are_hash_bound_and_tolerance_cannot_be_outcome_tuned():
    R = _load("scripts.v5.td_real_relational_executor_v3")
    bad = _contract(); bad["view_rule_sha256"] = "not-a-hash"
    out = R.adjudicate_r1_v3(
        rows=_rows(), contract=bad, decision_qualification_receipt=_qualification(),
        reference_artifact=_reference(_donors()), required_sources=list(SOURCES),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "R1_EXECUTION_CONTRACT_NOT_AUTHENTICATED"


def test_relation_values_are_exact_tie_aware_orders_only():
    R = _load("scripts.v5.td_real_relational_executor_v3")
    rows = _rows(); rows[0]["view_a_order"] = 0.25
    out = R.adjudicate_r1_v3(
        rows=rows, contract=_contract(), decision_qualification_receipt=_qualification(),
        reference_artifact=_reference(_donors()), required_sources=list(SOURCES),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "RELATION_ROWS_INVALID"


def test_required_sources_are_noncompensating():
    R = _load("scripts.v5.td_real_relational_executor_v3")
    rows = _rows(sources=("SEA_AD",), biology=True)
    out = R.adjudicate_r1_v3(
        rows=rows, contract=_contract(), decision_qualification_receipt=_qualification(),
        reference_artifact=_reference(_donors(("SEA_AD",))), required_sources=list(SOURCES),
    )
    assert out["status"] == "NOT_ESTIMABLE"
    assert out["reason"] == "REQUIRED_SOURCE_RELATIONAL_EVIDENCE_UNRESOLVED"


def test_known_truth_qualification_itself_contains_mandatory_technical_negative():
    R = _load("scripts.v5.td_real_relational_executor_v3")
    qual = R.qualify_r1_depth_matched_null_v3()
    assert qual["status"] == "PASS_KNOWN_TRUTH_R1_DEPTH_MATCHED_NULL_V3"
    assert qual["technical_only_negative"] == "FAIL"
    assert qual["planted_biology_positive"] == "PASS"
    assert all(v is False for v in qual["authority"].values())
