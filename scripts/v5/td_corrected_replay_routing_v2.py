"""C6-aware prospective interpretation of corrected TD56/57B/57C/59.

V2 preserves the V1 biological decision law and projects it into the V4 target
routing lattice. It never executes corrected replay or grants downstream authority.
"""
from __future__ import annotations

import td_target_tournament_routing_v4 as V4


class CorrectedReplayRoutingError(ValueError):
    pass


SCHEMA = "JEPA_TD_CORRECTED_RELATIONAL_REPLAY_ROUTING_V2"
SPEC_PATH = "docs/superpowers/specs/2026-10-12-td-corrected-replay-routing-v2-c6.md"
SPEC_GIT_BLOB_SHA = "918f9db1c7c26cbdb250e9b25dd78ca17ecee2bd"
STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})

BROAD_MESO = "BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER"
BROAD_GLOBAL = "BROAD_GLOBAL_ONLY__CURRENT_C2_NOT_QUALIFIED"
TD56_FAIL = "RELATIONAL_PROMOTION_STOP__TD56_FAIL"
TD57B_FAIL = "NO_STRONGER_RECURRENT_SCALE_FREE_ORDER__TD57B_FAIL"
DIVERGENCE = "DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED"
SOURCE_FAIL = "SOURCE_DISAGREEMENT__UNIVERSAL_RELATIONAL_TARGET_NOT_QUALIFIED"

STATE_TO_V4 = {
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
    if universal_source == "FAIL":
        return SOURCE_FAIL
    if td56 == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD56__NO_BIOLOGICAL_PASS"
    if td56 == "FAIL":
        return TD56_FAIL
    if td57b == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD57B__NO_BIOLOGICAL_PASS"
    if td57b == "FAIL":
        return TD57B_FAIL
    if td57c == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD57C__NO_BIOLOGICAL_PASS"
    if td57c == "PASS":
        return DIVERGENCE
    if td59 == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__TD59__NO_BIOLOGICAL_PASS"
    if td59 == "FAIL":
        return BROAD_GLOBAL
    if universal_source == "NOT_ESTIMABLE":
        return "NOT_ESTIMABLE__UNIVERSAL_SOURCE_REPLICATION__NO_BIOLOGICAL_PASS"
    return BROAD_MESO


def interpret_corrected_replay(*, td56: str, td57b: str, td57c: str, td59: str, universal_source: str) -> dict:
    for label, value in (
        ("TD56", td56), ("TD57B", td57b), ("TD57C", td57c),
        ("TD59", td59), ("universal_source", universal_source),
    ):
        _require_status(value, label)
    state = _interpret_state(
        td56=td56, td57b=td57b, td57c=td57c, td59=td59, universal_source=universal_source
    )
    try:
        v4_status = STATE_TO_V4[state]
    except KeyError as exc:
        raise CorrectedReplayRoutingError(f"unmapped frozen biological state: {state}") from exc
    route = V4.route_relational_replay(v4_status)
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
        "v4_relational_status": v4_status,
        "candidate_routes": route["candidate_routes"],
        "independently_testable": route["independently_testable"],
        "locality_experiment_required": state == DIVERGENCE,
        "source_averaging_rescue_allowed": False,
        **dict(NO_AUTHORITY),
    }
