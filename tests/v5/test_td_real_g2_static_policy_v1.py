from __future__ import annotations

import importlib.util

import pytest


def _load():
    name = "scripts.v5.td_real_g2_static_policy_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required G2 static-policy producer missing: {name}"
    import scripts.v5.td_real_g2_static_policy_v1 as P
    return P


CANDIDATE_SOURCE = {
    "commit": "206167a",
    "git_blob_sha": "e7912cd4530c49ee8159c0f8354fcfa04d587092",
}
TRANSFER_SOURCE = {
    "commit": "1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7",
    "git_blob_sha": "e1b8258822b2661670255e33b979bfd3de930878",
}


def _registry():
    return {
        "schema": "JEPA_TD_REAL_TARGET_TOURNAMENT_CONTRACT_V1",
        "mandatory_falsifiers": [
            "constant_train_mean", "technical_operator_only", "address_support_operator",
            "matched_wrong_cell", "fine_neighborhood_wrong_cell", "q_count_only",
            "q_address_only", "query_agnostic", "wrong_q", "technical_plus_q",
            "q_excluded_teacher", "identity_support_only",
        ],
        "candidates": {
            "C1_SHARED_EMERGENT": {
                "mandatory_falsifiers": [
                    "constant_train_mean", "technical_operator_only", "address_support_operator",
                    "matched_wrong_cell", "identity_support_only",
                ]
            },
            "C2_RELATIONAL_SHARED": {
                "mandatory_falsifiers": [
                    "constant_train_mean", "technical_operator_only", "address_support_operator",
                    "matched_wrong_cell", "fine_neighborhood_wrong_cell", "identity_support_only",
                ]
            },
            "C3_QUERY_MEASURED": {
                "mandatory_falsifiers": [
                    "constant_train_mean", "technical_operator_only", "address_support_operator",
                    "matched_wrong_cell", "q_count_only", "q_address_only", "query_agnostic",
                    "wrong_q", "technical_plus_q", "q_excluded_teacher",
                ]
            },
            "C6_SHARED_QUERY_COMPOSITE": {
                "mandatory_falsifiers": [
                    "constant_train_mean", "technical_operator_only", "address_support_operator",
                    "matched_wrong_cell", "identity_support_only", "q_count_only", "q_address_only",
                    "query_agnostic", "wrong_q", "technical_plus_q", "q_excluded_teacher",
                ]
            },
            "C4_STRUCTURED_COMPOSITE": {
                "mandatory_falsifiers": [
                    "constant_train_mean", "technical_operator_only", "address_support_operator",
                    "matched_wrong_cell", "fine_neighborhood_wrong_cell", "identity_support_only",
                    "q_count_only", "q_address_only", "query_agnostic", "wrong_q",
                    "technical_plus_q", "q_excluded_teacher",
                ]
            },
            "C5_REGULATORY_SPECIALIST": {
                "mandatory_falsifiers": [
                    "constant_train_mean", "technical_operator_only", "address_support_operator",
                    "matched_wrong_cell",
                ]
            },
        },
    }


def _transfer(*, c1_status="SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE", c1_envelope=None):
    empty = []
    env = {cid: list(empty) for cid in _registry()["candidates"]}
    env["C1_SHARED_EMERGENT"] = list(c1_envelope or [])
    statuses = {cid: "SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE" for cid in env}
    statuses["C5_REGULATORY_SPECIALIST"] = "NO_SUPPORTED_STRATA__NOT_ESTIMABLE"
    statuses["C1_SHARED_EMERGENT"] = c1_status
    return {
        "schema": "JEPA_TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V2",
        "claim_scope_rule": "FOUNDATION_ENVELOPE_EQUALS_ALL_PHYSICALLY_SUPPORTED_FROZEN_STRATA__SPECIALIST_ENVELOPE_SUPPORT_LIMITED__NO_POSTHOC_SCOPE_SHRINKAGE",
        "mandatory_claim_envelopes": env,
        "claim_envelope_status": statuses,
    }


def test_baseline_family_comes_from_candidate_record_not_global_catalog():
    P = _load()
    out = P.produce_g2_static_policy(
        candidate_id="C1_SHARED_EMERGENT",
        candidate_registry=_registry(), candidate_registry_source=CANDIDATE_SOURCE,
        transfer_contract=_transfer(), transfer_contract_source=TRANSFER_SOURCE,
    )
    assert out["applicable_baseline_ids"] == [
        "constant_train_mean", "technical_operator_only", "address_support_operator",
        "matched_wrong_cell", "identity_support_only",
    ]
    assert out["applicable_baseline_ids"] != _registry()["mandatory_falsifiers"]


def test_incomplete_support_contract_blocks_policy_without_inventing_strata():
    P = _load()
    out = P.produce_g2_static_policy(
        candidate_id="C1_SHARED_EMERGENT",
        candidate_registry=_registry(), candidate_registry_source=CANDIDATE_SOURCE,
        transfer_contract=_transfer(), transfer_contract_source=TRANSFER_SOURCE,
    )
    assert out["status"] == "BLOCKED_G2_STATIC_POLICY_SUPPORT_REGISTRY_INCOMPLETE"
    assert out["required_strata"] == []
    assert out["human_g2_execution_authorized"] is False


def test_no_supported_specialist_scope_is_not_estimable_not_fail():
    P = _load()
    out = P.produce_g2_static_policy(
        candidate_id="C5_REGULATORY_SPECIALIST",
        candidate_registry=_registry(), candidate_registry_source=CANDIDATE_SOURCE,
        transfer_contract=_transfer(), transfer_contract_source=TRANSFER_SOURCE,
    )
    assert out["status"] == "NOT_ESTIMABLE_G2_STATIC_POLICY_NO_SUPPORTED_STRATA"
    assert out["required_strata"] == []


def test_supported_frozen_envelope_is_preserved_exactly_order_insensitive():
    P = _load()
    strata = [
        {"partition":"reader_fit", "source":"SEA_AD", "operator_id":"OP2"},
        {"partition":"reader_fit", "source":"HVS", "operator_id":"OP1"},
    ]
    out = P.produce_g2_static_policy(
        candidate_id="C1_SHARED_EMERGENT",
        candidate_registry=_registry(), candidate_registry_source=CANDIDATE_SOURCE,
        transfer_contract=_transfer(c1_status="FROZEN_SUPPORTED_ENVELOPE", c1_envelope=strata),
        transfer_contract_source=TRANSFER_SOURCE,
    )
    assert out["status"] == "PASS_G2_STATIC_POLICY_PRODUCED__NO_HUMAN_EXECUTION_AUTHORITY"
    assert out["required_strata"] == [
        {"operator_id":"OP1", "partition":"reader_fit", "source":"HVS"},
        {"operator_id":"OP2", "partition":"reader_fit", "source":"SEA_AD"},
    ]


def test_source_identities_are_exact_and_wrong_registry_blob_is_rejected():
    P = _load()
    bad = dict(CANDIDATE_SOURCE, git_blob_sha="0"*40)
    with pytest.raises(P.G2StaticPolicyError, match="candidate registry source"):
        P.produce_g2_static_policy(
            candidate_id="C1_SHARED_EMERGENT",
            candidate_registry=_registry(), candidate_registry_source=bad,
            transfer_contract=_transfer(), transfer_contract_source=TRANSFER_SOURCE,
        )


def test_candidate_must_exist_in_both_frozen_inputs():
    P = _load()
    with pytest.raises(P.G2StaticPolicyError, match="candidate"):
        P.produce_g2_static_policy(
            candidate_id="C999",
            candidate_registry=_registry(), candidate_registry_source=CANDIDATE_SOURCE,
            transfer_contract=_transfer(), transfer_contract_source=TRANSFER_SOURCE,
        )


def test_authority_remains_closed():
    P = _load()
    out = P.produce_g2_static_policy(
        candidate_id="C1_SHARED_EMERGENT",
        candidate_registry=_registry(), candidate_registry_source=CANDIDATE_SOURCE,
        transfer_contract=_transfer(), transfer_contract_source=TRANSFER_SOURCE,
    )
    assert out["human_g2_execution_authorized"] is False
    assert all(v is False for v in out["authority"].values())
