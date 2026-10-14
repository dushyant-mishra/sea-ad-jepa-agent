from __future__ import annotations

import importlib
import importlib.util

import pytest


def _load():
    name = "scripts.v5.td_real_r1_executor_v3"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required repair module missing: {name}"
    return importlib.import_module(name)


def test_exact_pair_order_distance_and_tie_semantics_do_not_need_float_tolerance():
    R = _load()
    # Each distance is represented as an exact numerator/denominator pair.
    dij = R.concordance_distance([1, 0, -1, 1], [1, 1, -1, -1], minimum_informative=3)
    dik = R.concordance_distance([1, 0, -1, 1], [-1, 0, -1, 1], minimum_informative=3)
    assert dij == (3, 8)
    assert dik == (2, 6)
    assert R.anchored_triplet_order_exact(dij, dij) == 0
    assert R.anchored_triplet_order_exact(dij, dik) == 1
    assert R.TIE_SEMANTICS == "EXACT_RATIONAL_DISTANCE_TIE_IS_UNRESOLVED"


def test_view_contract_is_disjoint_and_digest_bound():
    R = _load()
    a = R.freeze_view_contract(
        view_x_pairs=[("g1", "g2"), ("g3", "g4")],
        view_y_pairs=[("g5", "g6"), ("g7", "g8")],
    )
    b = R.freeze_view_contract(
        view_x_pairs=[("g1", "g2"), ("g3", "g4")],
        view_y_pairs=[("g5", "g6"), ("g7", "g8")],
    )
    assert a["view_contract_sha256"] == b["view_contract_sha256"]
    assert len(a["view_contract_sha256"]) == 64
    with pytest.raises(R.R1ExecutorV3Error, match="disjoint"):
        R.freeze_view_contract(
            view_x_pairs=[("g1", "g2")],
            view_y_pairs=[("g2", "g3")],
        )


def test_matched_null_key_restores_historical_depth_and_detection_matching():
    R = _load()
    base = dict(donor_id="D1", source="HVS", operator="OP1", support_stratum="S")
    k1 = R.matched_null_block_key(**base, depth_block="Q1", detection_block="K1")
    k2 = R.matched_null_block_key(**base, depth_block="Q2", detection_block="K1")
    k3 = R.matched_null_block_key(**base, depth_block="Q1", detection_block="K2")
    assert k1 != k2
    assert k1 != k3
    assert R.MATCHED_NULL_PRESERVES == (
        "DONOR", "SOURCE", "OPERATOR", "SUPPORT_STRATUM", "DEPTH_BLOCK", "DETECTION_BLOCK"
    )


def test_depth_detection_matched_null_removes_pure_block_confounding():
    R = _load()
    # Agreement is entirely a block property: global shuffling would mix A/B and
    # manufacture an apparent relation effect, but within-block shifting cannot.
    rows = []
    for block, q in (("LOW", -1), ("HIGH", 1)):
        for i in range(8):
            rows.append({
                "relation_id": f"{block}-{i}", "donor_id": "D1", "source": "SEA_AD",
                "operator": "OP", "support_stratum": "S", "depth_block": block,
                "detection_block": block, "q_x": q, "q_y": q,
            })
    out = R.matched_relation_null_diagnostic(rows, nonzero_shifts=7)
    assert out["observed_agreement"] == 1.0
    assert out["matched_null_max"] == 1.0
    assert out["observed_minus_matched_null_max"] == 0.0
    assert out["technical_only_negative_passes"] is False


def test_planted_within_block_relation_identity_beats_matched_null():
    R = _load()
    rows = []
    pattern = [-1, -1, 1, 1, -1, 1, -1, 1]
    for block in ("LOW", "HIGH"):
        for i, q in enumerate(pattern):
            rows.append({
                "relation_id": f"{block}-{i}", "donor_id": "D1", "source": "SEA_AD",
                "operator": "OP", "support_stratum": "S", "depth_block": block,
                "detection_block": block, "q_x": q, "q_y": q,
            })
    out = R.matched_relation_null_diagnostic(rows, nonzero_shifts=7)
    assert out["observed_agreement"] == 1.0
    assert out["observed_minus_matched_null_max"] > 0.0


def test_known_truth_qualification_requires_technical_negative_and_planted_positive():
    R = _load()
    q = R.qualify_r1_v3_mechanics()
    assert q["worlds"]["TECHNICAL_BLOCK_CONFOUNDING"] == "PASS"
    assert q["worlds"]["PLANTED_WITHIN_BLOCK_RELATION"] == "PASS"
    assert q["status"] == "PASS_R1_V3_MECHANICS_KNOWN_TRUTH"
    assert q["human_r1_adjudication_authorized"] is False


def test_typed_null_receipt_cannot_authorize_human_r1():
    R = _load()
    out = R.human_execution_readiness(
        producer_receipt={"schema": "R1_PRODUCER", "qualified": True, "sha256": "a" * 64}
    )
    assert out["status"] == "BLOCKED_R1_CELL_IDENTITY_NULL_PRODUCER_NOT_QUALIFIED"
    assert out["caller_relation_null_has_human_authority"] is False
    assert out["human_r1_adjudication_authorized"] is False


def test_r1_v3_authority_remains_closed():
    R = _load()
    out = R.human_execution_readiness(producer_receipt={})
    assert all(value is False for value in out["authority"].values())
