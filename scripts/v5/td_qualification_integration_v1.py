"""Sealed integration adapter for TD qualification rehearsal.

Normal PASS/FAIL/NOT_ESTIMABLE candidate states are routed through the inherited
PR #313 tournament bundle/controller code. NUMERICAL_FAILURE is intercepted
before biological routing and remains a distinct terminal state.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Mapping

from scripts.v5 import td_case_bundle_v1 as Case


class IntegrationError(ValueError):
    pass


_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import td_real_tournament_bundle_v1 as TournamentBundle  # noqa: E402
import td_real_tournament_contract_v1 as TournamentContract  # noqa: E402
import td_real_tournament_gates_v1 as TournamentGates  # noqa: E402


_FOUNDATION = (
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
)
_ALLOWED = {"PASS", "FAIL", "NOT_ESTIMABLE", "NUMERICAL_FAILURE"}
_AUTHORITY = {
    "target_selection": False,
    "representation_selection": False,
    "td60": False,
    "stage4": False,
    "real_training": False,
}
_NUMERICAL_TERMINAL = "NUMERICAL_FAILURE__REPAIR_BEFORE_TD_ROUTING__NO_TARGET_AUTHORITY"


def _sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prepare_controller_case(executor_case: Mapping[str, object], truth: Mapping[str, object]) -> dict:
    return Case.bind_controller_truth(executor_case, truth)


def _receipt(candidate_id: str, status: str) -> TournamentGates.CandidateGateReceipt:
    return TournamentGates.CandidateGateReceipt(
        candidate_id=candidate_id,
        gates={"sealed_integration_rehearsal": {"status": status}},
        status=status,
        authority={key: False for key in sorted(TournamentContract.AUTHORITY_KEYS)},
    )


def _authenticated_output(*, terminal: str, eligible: list[str], routing_payload: Mapping[str, object] | None,
                          rehearsal_selected_candidate: str | None, numerical_failures: list[str]) -> dict:
    selection = "NONE"
    candidate_id = None
    if terminal == "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY":
        if len(eligible) != 1:
            raise IntegrationError("single-candidate terminal must carry exactly one eligible candidate")
        if rehearsal_selected_candidate is not None:
            if rehearsal_selected_candidate != eligible[0]:
                raise IntegrationError("rehearsal selected candidate does not match sole eligible candidate")
            selection = "SELECTED"
            candidate_id = eligible[0]
    elif terminal == "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY":
        # A requested rehearsal selection cannot bypass the protected head-to-head law.
        selection = "NONE"
        candidate_id = None
    elif rehearsal_selected_candidate is not None:
        raise IntegrationError("rehearsal selection is only legal for a sole eligible candidate")

    receipt_payload = {
        "terminal": terminal,
        "eligible_foundation_candidates": list(eligible),
        "selection": selection,
        "candidate_id": candidate_id,
        "numerical_failure_candidates": list(numerical_failures),
        "routing_payload": dict(routing_payload) if routing_payload is not None else None,
    }
    return {
        "schema": "JEPA_TD_AUTHENTICATED_TOURNAMENT_OUTPUT_V1",
        "selection": selection,
        "candidate_id": candidate_id,
        "terminal": terminal,
        "receipt_sha256": _sha256(receipt_payload),
    }


def run_candidate_rehearsal(
    *,
    candidate_statuses: Mapping[str, str],
    corrected_relational_replay_status: str,
    rehearsal_selected_candidate: str | None = None,
) -> dict:
    if not isinstance(candidate_statuses, Mapping) or set(candidate_statuses) != set(_FOUNDATION):
        raise IntegrationError("candidate_statuses must contain exactly the five V4 foundation candidates")
    if any(status not in _ALLOWED for status in candidate_statuses.values()):
        raise IntegrationError("candidate status must be PASS/FAIL/NOT_ESTIMABLE/NUMERICAL_FAILURE")
    if corrected_relational_replay_status not in {"PASS", "FAIL", "NOT_ESTIMABLE"}:
        raise IntegrationError("corrected relational replay status invalid")

    numerical = sorted(cid for cid, status in candidate_statuses.items() if status == "NUMERICAL_FAILURE")
    if numerical:
        tournament_output = _authenticated_output(
            terminal=_NUMERICAL_TERMINAL,
            eligible=[],
            routing_payload=None,
            rehearsal_selected_candidate=None,
            numerical_failures=numerical,
        )
        return {
            "schema": "JEPA_TD_QUALIFICATION_REHEARSAL_RESULT_V1",
            "routing_invoked": False,
            "numerical_failure_candidates": numerical,
            "tournament_output": tournament_output,
            "authority": dict(_AUTHORITY),
        }

    if corrected_relational_replay_status == "PASS":
        receipt_ids = _FOUNDATION
    elif corrected_relational_replay_status == "FAIL":
        if candidate_statuses["C2_RELATIONAL_SHARED"] != "FAIL" or candidate_statuses["C4_STRUCTURED_COMPOSITE"] != "FAIL":
            raise IntegrationError("relational FAIL requires C2/C4 rehearsal statuses to agree with dependency state")
        receipt_ids = ("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE")
    else:
        if candidate_statuses["C2_RELATIONAL_SHARED"] != "NOT_ESTIMABLE" or candidate_statuses["C4_STRUCTURED_COMPOSITE"] != "NOT_ESTIMABLE":
            raise IntegrationError("relational NOT_ESTIMABLE requires C2/C4 rehearsal statuses to agree with dependency state")
        receipt_ids = ("C1_SHARED_EMERGENT", "C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE")

    receipts = {cid: _receipt(cid, candidate_statuses[cid]) for cid in receipt_ids}
    routed = TournamentBundle.validate_bundle(
        receipts,
        corrected_relational_replay_status=corrected_relational_replay_status,
    )
    terminal = routed["terminal"]
    eligible = list(routed["eligible_foundation_candidates"])
    tournament_output = _authenticated_output(
        terminal=terminal,
        eligible=eligible,
        routing_payload=routed,
        rehearsal_selected_candidate=rehearsal_selected_candidate,
        numerical_failures=[],
    )
    return {
        "schema": "JEPA_TD_QUALIFICATION_REHEARSAL_RESULT_V1",
        "routing_invoked": True,
        "numerical_failure_candidates": [],
        "routing_result": routed,
        "tournament_output": tournament_output,
        "authority": dict(_AUTHORITY),
    }
