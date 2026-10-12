"""Candidate-specific field firewalls for the real target tournament."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import td_real_tournament_contract_v1 as C


class CandidateAdapterError(ValueError):
    pass


@dataclass(frozen=True)
class CandidateRecord:
    case_id: str
    cell_id: str
    donor_id: str
    source: str
    operator: str
    support_state: str
    query_id: str | None
    values: dict


@dataclass(frozen=True)
class CandidatePayload:
    candidate_id: str
    foundation: bool
    foundation_rescue: bool
    allowed_fields: tuple[str, ...]
    records: tuple[CandidateRecord, ...]
    replay_context: dict | None


_ALLOWED = {
    "C1_SHARED_EMERGENT": ("shared_target", "shared_student"),
    "C2_RELATIONAL_SHARED": ("shared_target", "shared_student", "relational_target", "relational_student"),
    "C3_QUERY_MEASURED": ("query_target", "query_student"),
    "C6_SHARED_QUERY_COMPOSITE": ("shared_target", "shared_student", "query_target", "query_student"),
    "C4_STRUCTURED_COMPOSITE": ("shared_target", "shared_student", "relational_target", "relational_student", "query_target", "query_student"),
    "C5_REGULATORY_SPECIALIST": ("regulatory_target", "regulatory_student", "regulatory_support"),
}
_QUERY_CANDIDATES = {"C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE", "C4_STRUCTURED_COMPOSITE"}
_RELATIONAL_CANDIDATES = {"C2_RELATIONAL_SHARED", "C4_STRUCTURED_COMPOSITE"}
_FOUNDATION = set(C.CANDIDATE_IDS) - {"C5_REGULATORY_SPECIALIST"}


def _validate_replay(candidate_id: str, replay_context: Mapping | None) -> dict | None:
    if candidate_id not in _RELATIONAL_CANDIDATES:
        return None
    if not isinstance(replay_context, Mapping) or replay_context.get("relational_status") != "PASS":
        raise CandidateAdapterError("relational replay context must be active PASS for relational candidates")
    receipt = replay_context.get("receipt_sha256")
    if not isinstance(receipt, str) or len(receipt) != 64:
        raise CandidateAdapterError("relational replay context must bind a 64-char receipt_sha256")
    return dict(replay_context)


def build_candidate_payload(candidate_id: str, case_ledger, observations: Mapping[str, Mapping], replay_context=None) -> CandidatePayload:
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    if candidate_id not in registry or candidate_id not in _ALLOWED:
        raise CandidateAdapterError(f"unknown candidate_id: {candidate_id}")
    allowed = _ALLOWED[candidate_id]
    replay = _validate_replay(candidate_id, replay_context)
    records = []
    for row in case_ledger.rows:
        obs = observations.get(row.cell_id)
        if not isinstance(obs, Mapping):
            raise CandidateAdapterError(f"missing observation for cell_id={row.cell_id}")
        if candidate_id in _QUERY_CANDIDATES and "query_scalar_student" in obs:
            raise CandidateAdapterError("query_scalar_student is forbidden for q-conditioned student payloads")
        values = {key: obs[key] for key in allowed if key in obs}
        missing = [key for key in allowed if key not in obs]
        if missing:
            raise CandidateAdapterError(f"missing required candidate fields for {candidate_id}: {missing}")
        records.append(CandidateRecord(
            case_id=row.case_id, cell_id=row.cell_id, donor_id=row.donor_id,
            source=row.source, operator=row.operator, support_state=row.support_state,
            query_id=row.query_id, values=values,
        ))
    return CandidatePayload(
        candidate_id=candidate_id,
        foundation=candidate_id in _FOUNDATION,
        foundation_rescue=False,
        allowed_fields=allowed,
        records=tuple(records),
        replay_context=replay,
    )
