from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_c6_candidate_extension_v1 as C6  # noqa: E402
import td_target_tournament_contract_v2 as V2  # noqa: E402


def test_c6_is_exact_union_of_c1_c3_plus_increment_and_has_no_relational_gate():
    expected = list(dict.fromkeys(V2.C1_GATES + V2.C3_GATES + ["C6_INCREMENT_OVER_C1_C3"]))
    assert C6.C6_GATES == expected
    assert not (set(C6.C6_GATES) & set(V2.RELATIONAL_GATES))
    assert set(V2.C1_GATES) <= set(C6.C6_GATES)
    assert set(V2.C3_GATES) <= set(C6.C6_GATES)


def test_c6_dependency_and_component_identity_are_frozen():
    assert C6.CANDIDATE_ID == "C6_SHARED_QUERY_COMPOSITE"
    assert C6.PARENTS == ("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED")
    assert C6.COMPONENTS == frozenset({"SHARED", "QUERY"})
    assert C6.RELATIONAL_DEPENDENT is False
    assert all(v is False for v in C6.NO_AUTHORITY.values())


def test_c6_requires_both_constituents_and_its_increment_gate():
    assert C6.adjudicate_constituents("PASS", "PASS", "PASS") == "ELIGIBLE_PENDING_TARGET_SELECTION"
    assert C6.adjudicate_constituents("FAIL", "PASS", "PASS") == "BLOCKED_BY_CONSTITUENT"
    assert C6.adjudicate_constituents("PASS", "FAIL", "PASS") == "BLOCKED_BY_CONSTITUENT"
    assert C6.adjudicate_constituents("PASS", "PASS", "FAIL") == "ELIMINATED_INCREMENT_FAIL"
    assert C6.adjudicate_constituents("NOT_ESTIMABLE", "PASS", "PASS") == "UNRESOLVED_BY_CONSTITUENT"
    assert C6.adjudicate_constituents("PASS", "PASS", "NOT_ESTIMABLE") == "UNRESOLVED_INCREMENT_NOT_ESTIMABLE"


def test_invalid_c6_status_fails_closed():
    with pytest.raises(C6.C6ExtensionError):
        C6.adjudicate_constituents("MAYBE", "PASS", "PASS")
