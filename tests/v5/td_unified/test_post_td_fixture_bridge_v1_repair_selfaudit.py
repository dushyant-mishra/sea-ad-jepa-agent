"""Author self-audit of the Macha bridge repair (F1-F5 from RED PR #450).

Attacks on the new code paths: fixture-label receipts, evidence-backed
TARGET_NONE, roster keys, the exact-int EMA unit and the relabelled
mode receipt. Synthetic fixtures only.
"""
from __future__ import annotations

import hashlib

import pytest

from scripts.v5.td_unified import post_td_fixture_bridge_v1 as bridge
from scripts.v5.td_unified.post_td_fixture_bridge_v1 import (
    FixtureBridgeError,
    stage_fixture_downstream,
)
from scripts.v5.td_unified.mode_equivalence_v1 import SCIENTIFIC_ROLES, FixtureStage


def _h(s: bytes) -> str:
    return hashlib.sha256(s).hexdigest()


def _case(case_id="PLANTED_FIT_ONLY", count=0):
    return {
        "schema": "KNOWN_TRUTH_CASEBUNDLE_V1",
        "case_id": case_id,
        "authority_scope": "FIXTURE_ONLY",
        "manifest_sha256": _h(b"dummy manifest"),
        "population_access_policy_sha256": _h(b"dummy policy"),
        "address_universe_sha256": _h(b"dummy universe"),
        "reader_partition": "reader_fit",
        "observations": [
            {"cell_id": "C1", "donor_id": "D1", "source_id": "SRC1",
             "operator_id": "OP1", "address_id": "ADDR1",
             "state": "MEASURED_SCALAR", "count": count, "library_size": 11,
             "evidence_right": "RNA:CORE"},
        ],
    }


def _stage(label):
    def run(payload):
        return {"stage": label, "previous": _h(repr(payload).encode())}
    return run


def _stages():
    return tuple(FixtureStage(role, _stage(role)) for role in SCIENTIFIC_ROLES)


def _run(**kw):
    return stage_fixture_downstream(case_payload=kw.pop("case", _case()), stages=_stages(), **kw)


def test_portfolio_hash_binds_the_case_bundle():
    a = _run(fixture_candidate="C1", fixture_qualifications={"C1": "PASS"})
    b = _run(case=_case("OTHER_CASE", count=3), fixture_candidate="C1",
             fixture_qualifications={"C1": "PASS"})
    assert a["casebundle_sha256"] != b["casebundle_sha256"]
    assert a["post_td_portfolio"]["portfolio_sha256"] != b["post_td_portfolio"]["portfolio_sha256"]


def test_every_recorded_qualification_keeps_fixture_provenance():
    q = {"C1": "PASS", "C2": "PASS", "C3": "PASS", "C4": "PASS", "C6": "PASS"}
    r = _run(fixture_candidate="C4", fixture_qualifications=q)
    recorded = r["post_td_portfolio"]["qualifications"]
    assert set(recorded) == set(q)
    for rec in recorded.values():
        assert rec["receipt_class"] == bridge.FIXTURE_LABEL_RECEIPT_CLASS
        assert rec["biological_qualification"] is False
    for block in r["post_td_portfolio"]["blocks"]:
        assert block["qualification_receipt"]["receipt_class"] == bridge.FIXTURE_LABEL_RECEIPT_CLASS


@pytest.mark.parametrize("receipt", [
    {"status": "PASS", "receipt_class": "TASK5_PLANTED_FIXTURE_LABEL",
     "biological_qualification": False, "casebundle_sha256": "0" * 64},
    {"status": "PASS", "biological_qualification": True},
])
def test_caller_cannot_supply_prewrapped_receipts(receipt):
    with pytest.raises(FixtureBridgeError):
        _run(fixture_candidate="C1", fixture_qualifications={"C1": receipt})


def test_evidence_backed_none_is_recorded_sorted():
    r = _run(fixture_qualifications={"C3": "FAIL", "C1": "NOT_ESTIMABLE"})
    assert r["target_candidate_fixture"] == "NONE"
    assert list(r["target_none_fixture_evidence"]) == ["C1", "C3"]
    assert r["post_td_portfolio"] is None and r["post_td_architecture_plan"] is None


def test_bare_none_records_no_evidence():
    for q in (None, {}):
        assert _run(fixture_qualifications=q)["target_none_fixture_evidence"] is None


class _S(str):
    pass


class _EmptyLooking(dict):
    def __len__(self):
        return 0

    def __ne__(self, other):
        return False

    def __eq__(self, other):
        return True


@pytest.mark.parametrize("q", [
    {"C1": "PASS"},
    {"C1": "FAIL", "C2": "PASS"},
    {"C1": "FAIL", "A7_SAME_CODE_PATH": "FAIL"},
    {"C1": _S("FAIL")},
    {_S("C1"): "FAIL"},
    {"C1": "fail"},
    {"C1": None},
    _EmptyLooking({"C1": "PASS"}),
    [("C1", "FAIL")],
])
def test_none_evidence_is_closed_roster_and_never_pass(q):
    with pytest.raises(FixtureBridgeError):
        _run(fixture_qualifications=q)


@pytest.mark.parametrize("bad", [True, False, 0, -1, 256.0, "256", None, 2 ** 0.5])
def test_ema_unit_must_be_positive_exact_int_on_every_path(bad):
    for kw in ({}, {"fixture_candidate": "C1", "fixture_qualifications": {"C1": "PASS"}}):
        with pytest.raises(FixtureBridgeError):
            _run(ema_half_life_presentations=bad, **kw)


def test_no_output_field_forwards_an_equivalence_claim():
    for kw in ({}, {"fixture_candidate": "C1", "fixture_qualifications": {"C1": "PASS"}}):
        r = _run(**kw)
        receipt = r["mode_path_receipt"]
        assert receipt["status"] == "SAME_PROCESS_SELF_COMPARISON__NOT_MODE_EQUIVALENCE_EVIDENCE"
        assert receipt["scientific_output_equivalence"] is None
        assert receipt["independent_human_sealed_execution"] is False
        assert "'scientific_output_equivalence': True" not in repr(r)
        assert "producer_identity_set" not in repr(r)


def test_c5_can_be_evidence_but_never_the_foundation_candidate():
    r = _run(fixture_candidate="C1", fixture_qualifications={"C1": "PASS", "C5": "FAIL"})
    assert r["post_td_portfolio"]["foundation_candidates"] == ["C1"]
    with pytest.raises(FixtureBridgeError):
        _run(fixture_candidate="C5", fixture_qualifications={"C5": "PASS"})
