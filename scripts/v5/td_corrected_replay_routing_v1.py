"""Prospective metadata-only interpretation of corrected TD56/57B/57C/59.

This module never runs corrected replay. It preserves the frozen biological
interpretation states and only then projects them into the V3 relational route.
"""
from __future__ import annotations

import td_target_tournament_routing_v3 as V3


class CorrectedReplayRoutingError(ValueError):
    pass


SCHEMA = "JEPA_TD_CORRECTED_RELATIONAL_REPLAY_ROUTING_V1"
SPEC_PATH = "docs/superpowers/specs/2026-10-12-td-corrected-replay-routing-v1.md"
SPEC_GIT_BLOB_SHA = "c248444254901691a618e8d56977112db8989dff"
STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})

BROAD_MESO = "BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER"
BROAD_GLOBAL = "BROAD_GLOBAL_ONLY__CURRENT_C2_NOT_QUALIFIED"
TD56_FAIL = "RELATIONAL_PROMOTION_STOP__TD56_FAIL"
TD57B_FAIL = "NO_STRONGER_RECURRENT_SCALE_FREE_ORDER__TD57B_FAIL"
DIVERGENCE = "DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED"
SOURCE_FAIL = "SOURCE_DISAGREEMENT__UNIVERSAL_RELATIONAL_TARGET_NOT_QUALIFIED"

STATE_TO_V3 = {
    BROAD_MESO: "PASS",
    BROAD_GLOBAL: "FAIL",
    TD56_FAIL: "FAIL",
    TD57B_FAIL: "FAIL",
    DIVERGENCE: "NOT_ESTIMABLE",
    SOURCE_FAIL: "FAIL",
    "NOT_ESTIMABLE__TD56__NO_BIOLOGICAL_PASS": "NOT_ESTIMABLE",
    "NOT_ESTIMABLE__TD57B__NO_BIOLOGICAL_PASS": "NOT_ESTIMABLE",
    "NOT_ESTIMABLE__TD57C__NO_BIOLOGICAL_PASS": "NOT_ESTIMABLE",
    "NOT_ESTIMABLE__TD59__NO_BIOLOGICAL_PASS": "NOT_ESTIMABLE",
    "NOT_ESTIMABLE__UNIVERSAL_SOURCE_REPLICATION__NO_BIOLOGICAL_PASS": "NOT_ESTIMABLE",
}

NO_AUTHORITY = {
    "corrected_replay_authorized": False,
    "target_selected": False,
    "representation_selected": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _require_status(value: str, label: str) -> None:
    if value not in STATUS:
        raise CorrectedReplayRoutingError(f"{label} must be PASS/FAIL/NOT_ESTIMABLE, got {value!r}")


def _interpret_state(*, td56: str, td57b: str, td57c: str, td59: str, universal_source: str) -> str:
    # Universal source disagreement defeats a universal relational foundation target.
    if universal_source == "FAIL":
        return SOURCE_FAIL

    if td56 == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD56__NO_BIOLOGICAL_PASS"
    if td56 == "FAIL":
        return TD56_FAIL

    if td57b == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD57B__NO_BIOLOGICAL_PASS"
    if td57b == "FAIL":
        # TD59 is deliberately not consulted: it cannot rescue TD57B failure.
        return TD57B_FAIL

    if td57c == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD57C__NO_BIOLOGICAL_PASS"
    if td57c == "PASS":
        # A corrected TD57C PASS is a divergence that requires a new prospective
        # locality experiment. TD59 is deliberately not used as a rescue.
        return DIVERGENCE

    # Only TD56 PASS + TD57B PASS + TD57C FAIL reaches TD59.
    if td59 == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD59__NO_BIOLOGICAL_PASS"
    if td59 == "FAIL":
        return BROAD_GLOBAL

    # Favorable within-source evidence is still unresolved if universal source
    # replication itself could not be estimated.
    if universal_source == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__UNIVERSAL_SOURCE_REPLICATION__NO_BIOLOGICAL_PASS"
    return BROAD_MESO


def interpret_corrected_replay(
    *,
    td56: str,
    td57b: str,
    td57c: str,
    td59: str,
    universal_source: str,
) -> dict:
    """Interpret frozen corrected-replay statuses and route only C2/C4 dependency."""
    for label, value in (
        ("TD56", td56),
        ("TD57B", td57b),
        ("TD57C", td57c),
        ("TD59", td59),
        ("universal_source", universal_source),
    ):
        _require_status(value, label)

    state = _interpret_state(
        td56=td56,
        td57b=td57b,
        td57c=td57c,
        td59=td59,
        universal_source=universal_source,
    )
    try:
        v3_status = STATE_TO_V3[state]
    except KeyError as exc:
        raise CorrectedReplayRoutingError(f"unmapped frozen biological state: {state}") from exc
    route = V3.route_relational_replay(v3_status)
    return {
        "schema": SCHEMA,
        "spec_path": SPEC_PATH,
        "spec_git_blob_sha": SPEC_GIT_BLOB_SHA,
        "inputs": {
            "TD56": td56,
            "TD57B": td57b,
            "TD57C": td57c,
            "TD59": td59,
            "universal_source": universal_source,
        },
        "biological_state": state,
        "v3_relational_status": v3_status,
        "candidate_routes": route["candidate_routes"],
        "independently_testable": route["independently_testable"],
        "locality_experiment_required": state == DIVERGENCE,
        "source_averaging_rescue_allowed": False,
        **dict(NO_AUTHORITY),
    }
