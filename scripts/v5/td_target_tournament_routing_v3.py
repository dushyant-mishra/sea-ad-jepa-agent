"""Prospective target-discovery routing V3.

This module fixes two routing errors without rewriting historical V2 evidence:
(1) relational replay gates only C2 and relational-dependent C4, never C1/C3;
(2) zero/one/multiple surviving foundation candidates have distinct terminals.

Metadata only. It creates no corrected-replay, biological, target-selection,
representation-selection, TD60, Stage4, or training authority.
"""
from __future__ import annotations


class RoutingV3Error(ValueError):
    pass


SCHEMA = "JEPA_TD_TARGET_TOURNAMENT_ROUTING_V3"
SPEC_PATH = "docs/superpowers/specs/2026-10-12-td-target-tournament-routing-v3.md"
SPEC_GIT_BLOB_SHA = "29682976085036ce3d39825f64d6c25ec500fd5c"

FOUNDATION = (
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C4_STRUCTURED_COMPOSITE",
)
SPECIALISTS = ("C5_REGULATORY_SPECIALIST",)
RELATIONAL_DEPENDENT = frozenset({"C2_RELATIONAL_SHARED", "C4_STRUCTURED_COMPOSITE"})
RELATIONAL_INDEPENDENT = frozenset({"C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"})
RELATIONAL_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})
CANDIDATE_STATUS = frozenset({"ELIGIBLE", "ELIMINATED", "UNRESOLVED", "BLOCKED_BY_CONSTITUENT"})
SPECIALIST_STATUS = frozenset({"ELIGIBLE", "ELIMINATED", "UNRESOLVED"})

NO_AUTHORITY = {
    "corrected_replay_authorized": False,
    "target_selected": False,
    "representation_selected": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _authority_projection() -> dict:
    return dict(NO_AUTHORITY)


def route_relational_replay(status: str) -> dict:
    """Route corrected relational evidence only to candidates that depend on it."""
    if status not in RELATIONAL_STATUS:
        raise RoutingV3Error(f"invalid corrected relational replay status: {status!r}")

    routes = {
        "C1_SHARED_EMERGENT": "ACTIVE",
        "C2_RELATIONAL_SHARED": "ACTIVE",
        "C3_QUERY_MEASURED": "ACTIVE",
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
        if routes[cid] in {"ACTIVE", "ACTIVE_SUBJECT_TO_C2_C3"}
    ]
    return {
        "schema": SCHEMA,
        "spec_path": SPEC_PATH,
        "spec_git_blob_sha": SPEC_GIT_BLOB_SHA,
        "corrected_relational_replay_status": status,
        "candidate_routes": routes,
        "independently_testable": independently_testable,
        **_authority_projection(),
    }


def _validate_candidate_statuses(candidate_statuses: dict) -> dict:
    if not isinstance(candidate_statuses, dict) or set(candidate_statuses) != set(FOUNDATION):
        raise RoutingV3Error("candidate_statuses must contain exactly C1-C4")
    if any(value not in CANDIDATE_STATUS for value in candidate_statuses.values()):
        raise RoutingV3Error("invalid foundation candidate status")
    return dict(candidate_statuses)


def adjudicate_survivors(candidate_statuses: dict, specialist_status: str | None = None) -> dict:
    """Apply the prospectively frozen zero/one/multiple/unresolved survivor law.

    C4 can survive only if both C2 and C3 survive. C5 is reported separately and
    never changes the foundation terminal.
    """
    statuses = _validate_candidate_statuses(candidate_statuses)
    if specialist_status is not None and specialist_status not in SPECIALIST_STATUS:
        raise RoutingV3Error("invalid specialist status")

    if statuses["C4_STRUCTURED_COMPOSITE"] == "ELIGIBLE":
        if statuses["C2_RELATIONAL_SHARED"] != "ELIGIBLE" or statuses["C3_QUERY_MEASURED"] != "ELIGIBLE":
            statuses["C4_STRUCTURED_COMPOSITE"] = "BLOCKED_BY_CONSTITUENT"

    eligible = [cid for cid in FOUNDATION if statuses[cid] == "ELIGIBLE"]
    unresolved = [cid for cid in FOUNDATION if statuses[cid] == "UNRESOLVED"]

    if unresolved:
        terminal = "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"
    elif not eligible:
        terminal = "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    elif len(eligible) == 1:
        terminal = "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"
    else:
        terminal = "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"

    specialists = ["C5_REGULATORY_SPECIALIST"] if specialist_status == "ELIGIBLE" else []
    return {
        "schema": "JEPA_TD_TARGET_TOURNAMENT_SURVIVOR_ADJUDICATION_V3",
        "spec_path": SPEC_PATH,
        "spec_git_blob_sha": SPEC_GIT_BLOB_SHA,
        "candidate_statuses": statuses,
        "eligible_foundation_candidates": eligible,
        "unresolved_foundation_candidates": unresolved,
        "optional_specialists_eligible": specialists,
        "terminal": terminal,
        **_authority_projection(),
    }
