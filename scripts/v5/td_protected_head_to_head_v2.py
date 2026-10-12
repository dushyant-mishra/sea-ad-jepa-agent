"""Fail-closed protected head-to-head V2 including C6 shared+query composite.

Consumes only prospectively thresholded pairwise metadata. No biological read,
target selection, or downstream authority is created.
"""
from __future__ import annotations

from itertools import combinations


class HeadToHeadError(ValueError):
    pass


SCHEMA = "JEPA_TD_PROTECTED_HEAD_TO_HEAD_V2"
SPEC_PATH = "docs/superpowers/specs/2026-10-12-td-protected-head-to-head-v2-c6.md"
SPEC_GIT_BLOB_SHA = "833eb0db67ef6fc418e579f790027592e416d31e"

FOUNDATION = (
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
)
COMPONENTS = {
    "C1_SHARED_EMERGENT": frozenset({"SHARED"}),
    "C2_RELATIONAL_SHARED": frozenset({"SHARED", "RELATIONAL"}),
    "C3_QUERY_MEASURED": frozenset({"QUERY"}),
    "C6_SHARED_QUERY_COMPOSITE": frozenset({"SHARED", "QUERY"}),
    "C4_STRUCTURED_COMPOSITE": frozenset({"SHARED", "RELATIONAL", "QUERY"}),
}
DIMENSIONS = (
    "BIOLOGICAL_INFORMATION",
    "DONOR_TRANSFER",
    "SOURCE_TRANSFER",
    "SHORTCUT_RESISTANCE",
    "COVERAGE_ABSTENTION",
    "UNCERTAINTY_BEHAVIOR",
    "MEASUREMENT_ROBUSTNESS",
)
DIMENSION_STATUS = frozenset({"BETTER", "NONINFERIOR", "WORSE", "NOT_ESTIMABLE"})
NO_AUTHORITY = {
    "value_read_authorized": False,
    "corrected_replay_authorized": False,
    "target_selected": False,
    "representation_selected": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _validate_candidate(candidate: str) -> None:
    if candidate not in FOUNDATION:
        raise HeadToHeadError(f"head-to-head candidate is not a foundation candidate: {candidate!r}")


def _validate_pair(record: dict) -> tuple[str, str, dict]:
    if not isinstance(record, dict) or set(record) != {"candidate_a", "candidate_b", "dimensions"}:
        raise HeadToHeadError("pair record must contain exactly candidate_a/candidate_b/dimensions")
    a = record.get("candidate_a")
    b = record.get("candidate_b")
    _validate_candidate(a)
    _validate_candidate(b)
    if a == b:
        raise HeadToHeadError("pair must compare two distinct candidates")
    dimensions = record.get("dimensions")
    if not isinstance(dimensions, dict) or tuple(dimensions) != DIMENSIONS:
        raise HeadToHeadError("pair dimensions must exactly match the frozen ordered dimension registry")
    bad = {name: value for name, value in dimensions.items() if value not in DIMENSION_STATUS}
    if bad:
        raise HeadToHeadError(f"invalid protected dimension status: {bad}")
    return a, b, dimensions


def compare_pair(record: dict) -> str:
    a, b, dimensions = _validate_pair(record)
    values = list(dimensions.values())
    if "NOT_ESTIMABLE" in values:
        return "UNRESOLVED"
    has_better = "BETTER" in values
    has_worse = "WORSE" in values
    if has_better and has_worse:
        return "INCOMPARABLE"
    if has_better:
        return "A_DOMINATES"
    if has_worse:
        return "B_DOMINATES"
    a_components = COMPONENTS[a]
    b_components = COMPONENTS[b]
    if a_components < b_components:
        return "A_DOMINATES_SIMPLER"
    if b_components < a_components:
        return "B_DOMINATES_SIMPLER"
    return "INCOMPARABLE"


def _pair_key(a: str, b: str) -> tuple[str, str]:
    order = {cid: i for i, cid in enumerate(FOUNDATION)}
    return (a, b) if order[a] < order[b] else (b, a)


def adjudicate(survivors: list[str], comparisons: list[dict]) -> dict:
    if not isinstance(survivors, list) or len(survivors) < 2:
        raise HeadToHeadError("protected head-to-head requires at least two foundation survivors")
    if len(survivors) != len(set(survivors)):
        raise HeadToHeadError("survivor list contains duplicates")
    for candidate in survivors:
        _validate_candidate(candidate)
    if not isinstance(comparisons, list):
        raise HeadToHeadError("comparisons must be a list")

    expected = {_pair_key(a, b) for a, b in combinations(survivors, 2)}
    seen = {}
    outcomes = {}
    wins = {candidate: set() for candidate in survivors}
    unresolved_pairs = []
    for record in comparisons:
        a, b, _ = _validate_pair(record)
        if a not in survivors or b not in survivors:
            raise HeadToHeadError("comparison contains a candidate outside the survivor set")
        key = _pair_key(a, b)
        if key in seen:
            raise HeadToHeadError(f"duplicate unordered pair comparison: {key}")
        outcome = compare_pair(record)
        seen[key] = outcome
        outcomes[f"{a}__VS__{b}"] = outcome
        if outcome == "UNRESOLVED":
            unresolved_pairs.append(list(key))
        elif outcome in {"A_DOMINATES", "A_DOMINATES_SIMPLER"}:
            wins[a].add(b)
        elif outcome in {"B_DOMINATES", "B_DOMINATES_SIMPLER"}:
            wins[b].add(a)

    missing = [list(pair) for pair in sorted(expected - set(seen))]
    leader = None
    if missing or unresolved_pairs:
        terminal = "HEAD_TO_HEAD_UNRESOLVED__NO_TARGET_AUTHORITY"
    else:
        dominators = [candidate for candidate in survivors if len(wins[candidate]) == len(survivors) - 1]
        if len(dominators) == 1:
            leader = dominators[0]
            terminal = "UNIQUE_HEAD_TO_HEAD_LEADER__PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY"
        else:
            terminal = "MULTIPLE_QUALIFIED_TARGETS__INCOMPARABLE__NO_TARGET_AUTHORITY"
    return {
        "schema": SCHEMA,
        "spec_path": SPEC_PATH,
        "spec_git_blob_sha": SPEC_GIT_BLOB_SHA,
        "survivors": list(survivors),
        "pair_outcomes": outcomes,
        "missing_pairs": missing,
        "unresolved_pairs": unresolved_pairs,
        "leader": leader,
        "terminal": terminal,
        **dict(NO_AUTHORITY),
    }
