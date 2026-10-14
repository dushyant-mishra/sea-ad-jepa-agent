"""Outcome-blind runtime guard for the frozen G12 claim envelope.

The static G11/G12 contract derives each candidate's mandatory claim envelope
from all prospectively supported frozen strata. This module only authenticates
that contract and prevents later post-outcome scope shrinkage or expansion. It
does not read candidate outcomes and does not adjudicate biological G12.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence


class G12EnvelopeError(ValueError):
    pass


_SCHEMA = "JEPA_TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V2"
_STATUS = "STATIC_CONTRACT_DERIVED__SPLIT_BOUND__NO_BIOLOGICAL_OUTCOME_AUTHORITY"
_SCOPE_RULE = (
    "FOUNDATION_ENVELOPE_EQUALS_ALL_PHYSICALLY_SUPPORTED_FROZEN_STRATA__"
    "SPECIALIST_ENVELOPE_SUPPORT_LIMITED__NO_POSTHOC_SCOPE_SHRINKAGE"
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _canonical_sha256(payload: Mapping) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_proposed_strata(value: Sequence[str]) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise G12EnvelopeError("proposed_strata must be a sequence")
    rows = list(value)
    if any(not isinstance(row, str) or not row for row in rows):
        raise G12EnvelopeError("proposed_strata must contain nonempty strings")
    if len(set(rows)) != len(rows):
        raise G12EnvelopeError("duplicate proposed stratum")
    return rows


def _validate_static_contract(static_contract: Mapping, expected_contract_sha256: str) -> tuple[dict, str]:
    if not isinstance(static_contract, Mapping):
        raise G12EnvelopeError("static contract must be a mapping")
    if not isinstance(expected_contract_sha256, str) or _HEX64.fullmatch(expected_contract_sha256) is None:
        raise G12EnvelopeError("expected contract binding must be a lowercase SHA-256")
    actual_sha = _canonical_sha256(static_contract)
    if actual_sha != expected_contract_sha256:
        raise G12EnvelopeError("static contract binding mismatch")
    if static_contract.get("schema") != _SCHEMA:
        raise G12EnvelopeError("static contract schema mismatch")
    if static_contract.get("status") != _STATUS:
        raise G12EnvelopeError("static contract status mismatch")
    if static_contract.get("claim_scope_rule") != _SCOPE_RULE:
        raise G12EnvelopeError("claim scope rule mismatch")
    if static_contract.get("authority") != _NO_AUTHORITY:
        raise G12EnvelopeError("static contract authority mismatch")
    envelopes = static_contract.get("mandatory_claim_envelopes")
    statuses = static_contract.get("claim_envelope_status")
    if not isinstance(envelopes, Mapping) or not isinstance(statuses, Mapping):
        raise G12EnvelopeError("static contract claim-envelope maps required")
    return dict(static_contract), actual_sha


def guard_claim_envelope(
    *,
    static_contract: Mapping,
    expected_contract_sha256: str,
    candidate_id: str,
    proposed_strata: Sequence[str],
) -> dict:
    contract, contract_sha = _validate_static_contract(static_contract, expected_contract_sha256)
    if not isinstance(candidate_id, str) or not candidate_id:
        raise G12EnvelopeError("candidate_id must be a nonempty string")
    envelopes = contract["mandatory_claim_envelopes"]
    statuses = contract["claim_envelope_status"]
    if candidate_id not in envelopes or candidate_id not in statuses:
        raise G12EnvelopeError("candidate missing from frozen claim envelope")

    proposed = _validate_proposed_strata(proposed_strata)
    mandatory_raw = envelopes[candidate_id]
    if isinstance(mandatory_raw, (str, bytes)) or not isinstance(mandatory_raw, Sequence):
        raise G12EnvelopeError("mandatory claim envelope must be a sequence")
    mandatory = list(mandatory_raw)
    if any(not isinstance(row, str) or not row for row in mandatory):
        raise G12EnvelopeError("mandatory claim envelope contains invalid stratum")
    if len(set(mandatory)) != len(mandatory):
        raise G12EnvelopeError("mandatory claim envelope contains duplicate stratum")

    envelope_status = statuses[candidate_id]
    common = {
        "schema": "JEPA_TD_REAL_G12_CLAIM_ENVELOPE_GUARD_V1",
        "candidate_id": candidate_id,
        "static_contract_sha256": contract_sha,
        "mandatory_claim_envelope": sorted(mandatory),
        "g12_biological_adjudication_authorized": False,
        "authority": dict(_NO_AUTHORITY),
    }

    if envelope_status == "SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE":
        if proposed:
            raise G12EnvelopeError("support registry incomplete; proposed execution scope is premature")
        return {
            **common,
            "status": "BLOCKED_G12_SUPPORT_REGISTRY_INCOMPLETE",
            "biological_fail": False,
        }

    if envelope_status == "NO_SUPPORTED_STRATA__NOT_ESTIMABLE":
        if proposed:
            raise G12EnvelopeError("no supported strata exist in frozen envelope")
        return {
            **common,
            "status": "NOT_ESTIMABLE_G12_NO_SUPPORTED_STRATA",
            "biological_fail": False,
        }

    if envelope_status != "SUPPORTED_ENVELOPE_FROZEN":
        raise G12EnvelopeError(f"unknown claim envelope status: {envelope_status}")

    mandatory_set = set(mandatory)
    proposed_set = set(proposed)
    missing = sorted(mandatory_set - proposed_set)
    extra = sorted(proposed_set - mandatory_set)
    if missing:
        raise G12EnvelopeError(f"post-hoc scope shrinkage forbidden; missing frozen strata: {missing}")
    if extra:
        raise G12EnvelopeError(f"proposed strata outside frozen envelope: {extra}")

    return {
        **common,
        "status": "FROZEN_CLAIM_ENVELOPE_READY_FOR_LATER_G12_EXECUTION",
        "proposed_claim_envelope": sorted(proposed),
        "biological_fail": False,
    }
