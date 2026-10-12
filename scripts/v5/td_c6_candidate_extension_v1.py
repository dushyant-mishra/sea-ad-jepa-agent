"""Prospective C6 shared+query composite candidate extension.

C6 is defined before corrected biological outcomes are opened.  It closes the
missing C1+C3-without-relational ablation in the frozen V2 candidate family.
This module is metadata-only and grants no execution or selection authority.
"""
from __future__ import annotations

import td_target_tournament_contract_v2 as V2


class C6ExtensionError(ValueError):
    pass


SCHEMA = "JEPA_TD_C6_SHARED_QUERY_COMPOSITE_EXTENSION_V1"
SPEC_PATH = "docs/superpowers/specs/2026-10-12-td-c6-shared-query-composite-v1.md"
SPEC_GIT_BLOB_SHA = "647cc693bd1771793b1fff3689f43c59c0f8eddf"
CANDIDATE_ID = "C6_SHARED_QUERY_COMPOSITE"
PARENTS = ("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED")
COMPONENTS = frozenset({"SHARED", "QUERY"})
RELATIONAL_DEPENDENT = False
INCREMENT_GATE = "C6_INCREMENT_OVER_C1_C3"
STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})

# Preserve the frozen V2 gate order: C1 first, then any C3-only gates, then the
# prospectively frozen C6 increment gate.
C6_GATES = list(dict.fromkeys(V2.C1_GATES + V2.C3_GATES + [INCREMENT_GATE]))

NO_AUTHORITY = {
    "corrected_replay_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _require(value: str, label: str) -> None:
    if value not in STATUS:
        raise C6ExtensionError(f"{label} must be PASS/FAIL/NOT_ESTIMABLE, got {value!r}")


def adjudicate_constituents(c1_status: str, c3_status: str, increment_status: str) -> str:
    """Apply C6 constituent and increment gates without aggregate-score rescue."""
    _require(c1_status, "C1")
    _require(c3_status, "C3")
    _require(increment_status, INCREMENT_GATE)

    if c1_status == "FAIL" or c3_status == "FAIL":
        return "BLOCKED_BY_CONSTITUENT"
    if c1_status == "NOT_ESTIMABLE" or c3_status == "NOT_ESTIMABLE":
        return "UNRESOLVED_BY_CONSTITUENT"
    if increment_status == "FAIL":
        return "ELIMINATED_INCREMENT_FAIL"
    if increment_status == "NOT_ESTIMABLE":
        return "UNRESOLVED_INCREMENT_NOT_ESTIMABLE"
    return "ELIGIBLE_PENDING_TARGET_SELECTION"
