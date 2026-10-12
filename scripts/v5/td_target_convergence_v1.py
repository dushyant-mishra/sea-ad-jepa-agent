"""Final metadata-only convergence law for target discovery.

This module consumes already-thresholded candidate statuses and protected pairwise
metadata. It opens no biological values and creates no target/training authority.
"""
from __future__ import annotations

import td_protected_head_to_head_v2 as H2H
import td_target_tournament_routing_v4 as V4


class TargetConvergenceError(ValueError):
    pass


SCHEMA = "JEPA_TD_TARGET_CONVERGENCE_V1"
SPEC_PATH = "docs/superpowers/specs/2026-10-12-td-target-convergence-v1.md"
FOUNDATION = V4.FOUNDATION
CONFIRMATION_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})
NO_AUTHORITY = {
    "value_read_authorized": False,
    "corrected_replay_authorized": False,
    "target_selected": False,
    "representation_selected": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _confirmation_terminal(status: str) -> str:
    if status == "PASS":
        return "TARGET_CANDIDATE_CONFIRMED__OWNER_SELECTION_DECISION_REQUIRED__NO_TARGET_AUTHORITY"
    if status == "FAIL":
        return "PROTECTED_CONFIRMATION_FAILED__NO_TARGET_WINNER__REDESIGN"
    return "PROTECTED_CONFIRMATION_NOT_ESTIMABLE__NO_TARGET_AUTHORITY"


def converge(
    candidate_statuses: dict,
    *,
    specialist_status: str | None = None,
    comparisons: list[dict] | None = None,
    protected_confirmation: str | None = None,
) -> dict:
    """Converge zero/one/multiple candidate outcomes without manufacturing a winner."""
    try:
        survivor = V4.adjudicate_survivors(candidate_statuses, specialist_status=specialist_status)
    except V4.RoutingV4Error as exc:
        raise TargetConvergenceError(str(exc)) from exc

    statuses = survivor["candidate_statuses"]
    eligible = survivor["eligible_foundation_candidates"]
    unresolved = survivor["unresolved_foundation_candidates"]
    finalist = None
    head_to_head = None

    if unresolved:
        terminal = "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY"
    elif not eligible:
        terminal = "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    elif len(eligible) == 1:
        finalist = eligible[0]
        terminal = "PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY"
    else:
        try:
            head_to_head = H2H.adjudicate(eligible, [] if comparisons is None else comparisons)
        except H2H.HeadToHeadError as exc:
            raise TargetConvergenceError(str(exc)) from exc
        if head_to_head["terminal"] == "UNIQUE_HEAD_TO_HEAD_LEADER__PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY":
            finalist = head_to_head["leader"]
            terminal = "PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY"
        elif head_to_head["terminal"] == "MULTIPLE_QUALIFIED_TARGETS__INCOMPARABLE__NO_TARGET_AUTHORITY":
            terminal = head_to_head["terminal"]
        else:
            terminal = "HEAD_TO_HEAD_UNRESOLVED__NO_TARGET_AUTHORITY"

    if protected_confirmation is not None:
        if protected_confirmation not in CONFIRMATION_STATUS:
            raise TargetConvergenceError("protected confirmation must be PASS/FAIL/NOT_ESTIMABLE")
        if finalist is None:
            raise TargetConvergenceError("protected confirmation is forbidden without one frozen finalist")
        terminal = _confirmation_terminal(protected_confirmation)

    return {
        "schema": SCHEMA,
        "spec_path": SPEC_PATH,
        "candidate_statuses": statuses,
        "eligible_foundation_candidates": eligible,
        "unresolved_foundation_candidates": unresolved,
        "optional_specialists_eligible": survivor["optional_specialists_eligible"],
        "head_to_head": head_to_head,
        "finalist": finalist,
        "protected_confirmation": protected_confirmation,
        "terminal": terminal,
        **dict(NO_AUTHORITY),
    }
