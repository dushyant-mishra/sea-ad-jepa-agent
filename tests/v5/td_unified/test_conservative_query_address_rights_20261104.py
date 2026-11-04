"""Prospective V9 fail-closed regression from original PR513 alias-rights evidence.

This is synthetic-only and source-read-free. Historical original #514/#515
negative fixtures remain preserved in their old immutable PR commits. No alias
identity, external source issuer, biological teacher or training is certified.
"""
from copy import deepcopy

import pytest

from scripts.v5.td_unified import observation_d1_base_only_student_v2c_fixture_v1 as P
from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C


def _safe_policy():
    return {
        "query_address_id": "ENSG_Q",
        "base_evidence_rights": ["RNA:BASE"],
        "address_rights": {"ENSG_A": "RNA:BASE", "ENSG_Q": "RNA:QUERY"},
        "operator_states": {
            "OP_A": {"ENSG_A": C._MS, "ENSG_Q": C._MS}
        },
        "cell_roster": [{
            "cell_id": "CELL_A", "donor_id": "DONOR_A",
            "source_id": "SOURCE_A", "operator_id": "OP_A",
        }],
    }


def _obs():
    return [{"cell_id": "CELL_A", "base_counts": {"ENSG_A": 3}}]


def _rename_query(policy, new_q):
    policy = deepcopy(policy)
    old_q = policy["query_address_id"]
    policy["query_address_id"] = new_q
    policy["address_rights"][new_q] = policy["address_rights"].pop(old_q)
    for states in policy["operator_states"].values():
        states[new_q] = states.pop(old_q)
    return policy


def _forge_consistent_view(safe_view, blocked_q):
    view = deepcopy(safe_view)
    original_q = view["query_address_id"]
    view["query_address_id"] = blocked_q
    for row in view["rows"]:
        if row["address_id"] == original_q:
            row["address_id"] = blocked_q
    view["observable_sha256"] = C._sha({
        k: v for k, v in view.items() if k != "observable_sha256"
    })
    return view


BLOCKED_QUERY_IDS = (
    "ENSG00000235481",  # UBE2R2-AS1
    "ENSG00000233776",  # legacy LINC01251/RP11-384P7.6
    "ENSG00000257612",  # MIR4307HG
    "ENSG00000257842",  # LINC02588
    "ENSG00000258081",  # ambiguous chr14 legacy holder
)


@pytest.mark.parametrize("query", BLOCKED_QUERY_IDS + tuple(x + ".12" for x in BLOCKED_QUERY_IDS))
def test_d1_producer_refuses_conservative_source_query_rights(query):
    policy = _rename_query(_safe_policy(), query)
    with pytest.raises(C.StudentV2CRefusal, match="unresolved alias/operator rights"):
        P.produce_d1_base_only_student_v2c_fixture(
            base_observations=_obs(), expected_policy=policy)


@pytest.mark.parametrize("query", BLOCKED_QUERY_IDS + tuple(x + ".12" for x in BLOCKED_QUERY_IDS))
def test_student_gate_rejects_even_rehashed_consistent_untrusted_alias_view(query):
    safe_policy = _safe_policy()
    lawful = P.produce_d1_base_only_student_v2c_fixture(
        base_observations=_obs(), expected_policy=safe_policy)
    forged_policy = _rename_query(safe_policy, query)
    forged_view = _forge_consistent_view(lawful, query)
    # The standalone verifier must independently refuse; producer refusal
    # alone does not prevent a manually rehashed counterfeit student view.
    with pytest.raises(C.StudentV2CRefusal, match="unresolved alias/operator rights"):
        C.validate_student_v2c(student_view=forged_view, expected_policy=forged_policy)


def test_unrelated_query_keeps_fixture_consistency_without_source_authentication():
    p = _safe_policy()
    view = P.produce_d1_base_only_student_v2c_fixture(
        base_observations=_obs(), expected_policy=p)
    receipt = C.validate_student_v2c(student_view=view, expected_policy=p)
    assert receipt["status"] == "STUDENT_ONLY_CONTENT_POLICY_CONSISTENT_NO_AUTHORITY"
    for flag in (
        "source_rights_issuer_authenticated",
        "source_feature_alias_closure_authenticated",
        "teacher_issuance_authenticated",
        "g7_content_v2_authorized",
        "real_training_authorized",
    ):
        assert receipt[flag] is False
