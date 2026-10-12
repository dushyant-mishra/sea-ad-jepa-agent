"""Bundle candidate gate receipts into exact routing-v4 statuses."""
from __future__ import annotations

from typing import Mapping

import td_target_tournament_routing_v4 as R


class BundleError(ValueError):
    pass


_FOUNDATION = (
    "C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE", "C4_STRUCTURED_COMPOSITE",
)
_SPECIALIST = "C5_REGULATORY_SPECIALIST"
_ALLOWED_REPLAY = {"PASS", "FAIL", "NOT_ESTIMABLE"}


def _project(status: str) -> str:
    if status == "PASS":
        return "ELIGIBLE"
    if status == "FAIL":
        return "ELIMINATED"
    if status == "NOT_ESTIMABLE":
        return "UNRESOLVED"
    raise BundleError(f"invalid candidate receipt status: {status!r}")


def validate_bundle(candidate_receipts: Mapping[str, object], *, corrected_relational_replay_status: str) -> dict:
    if corrected_relational_replay_status not in _ALLOWED_REPLAY:
        raise BundleError("corrected_relational_replay_status must be PASS/FAIL/NOT_ESTIMABLE")
    if not isinstance(candidate_receipts, Mapping):
        raise BundleError("candidate_receipts must be a mapping")

    if corrected_relational_replay_status == "PASS":
        required = set(_FOUNDATION)
    else:
        required = {"C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE"}
    present_foundation = set(candidate_receipts) & set(_FOUNDATION)
    if present_foundation != required:
        raise BundleError(f"required candidate receipts mismatch: expected={sorted(required)} actual={sorted(present_foundation)}")
    if set(candidate_receipts) - set(_FOUNDATION) - {_SPECIALIST}:
        raise BundleError("unknown candidate receipt present")

    statuses = {}
    for candidate in _FOUNDATION:
        receipt = candidate_receipts.get(candidate)
        if receipt is not None:
            if getattr(receipt, "candidate_id", None) != candidate:
                raise BundleError(f"candidate receipt identity mismatch: {candidate}")
            auth = getattr(receipt, "authority", None)
            if not isinstance(auth, dict) or any(v is not False for v in auth.values()):
                raise BundleError(f"candidate receipt carries authority: {candidate}")
            statuses[candidate] = _project(getattr(receipt, "status", None))
            continue
        if candidate == "C2_RELATIONAL_SHARED":
            statuses[candidate] = "ELIMINATED" if corrected_relational_replay_status == "FAIL" else "UNRESOLVED"
        elif candidate == "C4_STRUCTURED_COMPOSITE":
            statuses[candidate] = "BLOCKED_BY_CONSTITUENT" if corrected_relational_replay_status == "FAIL" else "UNRESOLVED_BY_CONSTITUENT"
        else:
            raise BundleError(f"missing independently testable candidate receipt: {candidate}")

    specialist_status = None
    if _SPECIALIST in candidate_receipts:
        receipt = candidate_receipts[_SPECIALIST]
        if getattr(receipt, "candidate_id", None) != _SPECIALIST:
            raise BundleError("specialist receipt identity mismatch")
        auth = getattr(receipt, "authority", None)
        if not isinstance(auth, dict) or any(v is not False for v in auth.values()):
            raise BundleError("specialist receipt carries authority")
        specialist_status = _project(getattr(receipt, "status", None))

    routed = R.adjudicate_survivors(statuses, specialist_status=specialist_status)
    return {
        "schema": "JEPA_TD_REAL_TOURNAMENT_BUNDLE_V1",
        "corrected_relational_replay_status": corrected_relational_replay_status,
        **routed,
    }
