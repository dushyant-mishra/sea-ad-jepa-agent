"""Prospective target-discovery routing V4 with the C6 shared+query composite.

V4 preserves the V3 survivor law while extending the foundation candidate lattice
before corrected biological outcomes are opened. Metadata only; no authority.
"""
from __future__ import annotations


class RoutingV4Error(ValueError):
    pass


SCHEMA = "JEPA_TD_TARGET_TOURNAMENT_ROUTING_V4"
SPEC_PATH = "docs/superpowers/specs/2026-10-12-td-c6-shared-query-composite-v1.md"
SPEC_GIT_BLOB_SHA = "647cc693bd1771793b1fff3689f43c59c0f8eddf"
FOUNDATION = (
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
)
SPECIALISTS = ("C5_REGULATORY_SPECIALIST",)
RELATIONAL_DEPENDENT = frozenset({"C2_RELATIONAL_SHARED", "C4_STRUCTURED_COMPOSITE"})
RELATIONAL_INDEPENDENT = frozenset({"C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE"})
RELATIONAL_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})
CANDIDATE_STATUS = frozenset({
    "ELIGIBLE", "ELIMINATED", "UNRESOLVED", "BLOCKED_BY_CONSTITUENT", "UNRESOLVED_BY_CONSTITUENT"
})
SPECIALIST_STATUS = frozenset({"ELIGIBLE", "ELIMINATED", "UNRESOLVED"})

NO_AUTHORITY = {
    "corrected_replay_authorized": False,
    "target_selected": False,
    "representation_selected": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def route_relational_replay(status: str) -> dict:
    if status not in RELATIONAL_STATUS:
        raise RoutingV4Error(f"invalid corrected relational replay status: {status!r}")
    routes = {
        "C1_SHARED_EMERGENT": "ACTIVE",
        "C2_RELATIONAL_SHARED": "ACTIVE",
        "C3_QUERY_MEASURED": "ACTIVE",
        "C6_SHARED_QUERY_COMPOSITE": "ACTIVE_SUBJECT_TO_C1_C3",
        "C4_STRUCTURED_COMPOSITE": "ACTIVE_SUBJECT_TO_C2_C3",
    }
    if status == "FAIL":
        routes["C2_RELATIONAL_SHARED"] = "ELIMINATED_RELATIONAL_FAIL"
        routes["C4_STRUCTURED_COMPOSITE"] = "BLOCKED_BY_RELATIONAL_CONSTITUENT"
    elif status == "NOT_ESTIMABLE":
        routes["C2_RELATIONAL_SHARED"] = "UNRESOLVED_RELATIONAL_NOT_ESTIMABLE"
        routes["C4_STRUCTURED_COMPOSITE"] = "UNRESOLVED_RELATIONAL_CONSTITUENT"
    independently_testable = [
        cid for cid in FOUNDATION
        if routes[cid] in {"ACTIVE", "ACTIVE_SUBJECT_TO_C1_C3", "ACTIVE_SUBJECT_TO_C2_C3"}
    ]
    return {
        "schema": SCHEMA,
        "corrected_relational_replay_status": status,
        "candidate_routes": routes,
        "independently_testable": independently_testable,
        **dict(NO_AUTHORITY),
    }


def _validate(candidate_statuses: dict) -> dict:
    if not isinstance(candidate_statuses, dict) or set(candidate_statuses) != set(FOUNDATION):
        raise RoutingV4Error("candidate_statuses must contain exactly the five V4 foundation candidates")
    if any(status not in CANDIDATE_STATUS for status in candidate_statuses.values()):
        raise RoutingV4Error("invalid V4 foundation candidate status")
    return dict(candidate_statuses)


def _resolve_composite(statuses: dict, composite: str, parents: tuple[str, str]) -> None:
    if statuses[composite] != "ELIGIBLE":
        return
    parent_states = [statuses[parent] for parent in parents]
    if all(state == "ELIGIBLE" for state in parent_states):
        return
    if any(state in {"UNRESOLVED", "UNRESOLVED_BY_CONSTITUENT"} for state in parent_states):
        statuses[composite] = "UNRESOLVED_BY_CONSTITUENT"
    else:
        statuses[composite] = "BLOCKED_BY_CONSTITUENT"


def adjudicate_survivors(candidate_statuses: dict, specialist_status: str | None = None) -> dict:
    statuses = _validate(candidate_statuses)
    if specialist_status is not None and specialist_status not in SPECIALIST_STATUS:
        raise RoutingV4Error("invalid specialist status")

    _resolve_composite(statuses, "C6_SHARED_QUERY_COMPOSITE", ("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"))
    _resolve_composite(statuses, "C4_STRUCTURED_COMPOSITE", ("C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED"))

    eligible = [cid for cid in FOUNDATION if statuses[cid] == "ELIGIBLE"]
    unresolved = [cid for cid in FOUNDATION if statuses[cid] in {"UNRESOLVED", "UNRESOLVED_BY_CONSTITUENT"}]
    if unresolved:
        terminal = "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"
    elif not eligible:
        terminal = "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    elif len(eligible) == 1:
        terminal = "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"
    else:
        terminal = "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"

    return {
        "schema": "JEPA_TD_TARGET_TOURNAMENT_SURVIVOR_ADJUDICATION_V4",
        "candidate_statuses": statuses,
        "eligible_foundation_candidates": eligible,
        "unresolved_foundation_candidates": unresolved,
        "optional_specialists_eligible": ["C5_REGULATORY_SPECIALIST"] if specialist_status == "ELIGIBLE" else [],
        "terminal": terminal,
        **dict(NO_AUTHORITY),
    }
