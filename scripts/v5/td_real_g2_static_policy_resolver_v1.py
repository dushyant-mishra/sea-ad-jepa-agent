"""Current-state G2 static-policy resolver.

This module does *not* invent the future human G2 policy. It authenticates the
frozen historical candidate/falsifier registry and the current G11/G12 support
contract, then proves that the current real state cannot yet yield an
applicable-baseline or required-strata policy. Baseline IDs are retained only as
candidate-specific provenance/catalog while support/evidence contracts remain
blocked.
"""
from __future__ import annotations

from collections.abc import Mapping

from scripts.v5 import td_real_tournament_contract_v1 as T


class G2StaticPolicyError(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_G2_STATIC_POLICY_RESOLUTION_V1"
TOURNAMENT_REGISTRY_SOURCE_COMMIT = "206167a1eb86f1dec5f8285db56accbcd469bce9"
SUPPORT_REGISTRY_SOURCE_COMMIT = "1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7"
COVERAGE_SCHEMA = "JEPA_TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V2"
FOUNDATION_CANDIDATES = {
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
}
SPECIALIST = "C5_REGULATORY_SPECIALIST"
_NO_AUTHORITY = {
    "real_tournament_authorized": False,
    "representation_selection_authorized": False,
    "stage4_authorized": False,
    "target_selection_authorized": False,
    "td60_authorized": False,
    "training_authorized": False,
    "value_read_authorized": False,
}
_EXPECTED_FOUNDATION_COUNTS = {
    "BLOCKED_EVIDENCE_CONTRACT": 2028,
    "SUPPORTED": 0,
    "UNSUPPORTED_STRUCTURAL": 0,
}
_EXPECTED_SPECIALIST_COUNTS = {
    "BLOCKED_EVIDENCE_CONTRACT": 0,
    "SUPPORTED": 0,
    "UNSUPPORTED_STRUCTURAL": 2028,
}
_EXPECTED_FOUNDATION_STATUS = "SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE"
_EXPECTED_SPECIALIST_STATUS = "NO_SUPPORTED_STRATA__NOT_ESTIMABLE"


def _validate_source_commits(*, tournament_registry_source_commit: str, support_registry_source_commit: str) -> None:
    if tournament_registry_source_commit != TOURNAMENT_REGISTRY_SOURCE_COMMIT:
        raise G2StaticPolicyError("tournament registry source commit mismatch")
    if support_registry_source_commit != SUPPORT_REGISTRY_SOURCE_COMMIT:
        raise G2StaticPolicyError("support registry source commit mismatch")


def _validate_coverage(contract: Mapping[str, object]) -> dict:
    required = {
        "authority", "candidate_support_state_counts", "claim_envelope_status",
        "claim_scope_rule", "donor_transfer_rule", "foundation_candidates",
        "mandatory_claim_envelopes", "schema", "specialist_candidate",
        "specialist_foundation_rescue_authorized", "status",
        "supported_partition_counts", "transfer_applicability",
    }
    if not isinstance(contract, Mapping) or set(contract) != required:
        raise G2StaticPolicyError("coverage contract drift: fields differ from frozen V2 schema")
    if contract.get("schema") != COVERAGE_SCHEMA:
        raise G2StaticPolicyError("coverage contract drift: schema mismatch")
    if contract.get("authority") != _NO_AUTHORITY:
        raise G2StaticPolicyError("coverage contract drift: authority mismatch")
    if contract.get("status") != "STATIC_CONTRACT_DERIVED__SPLIT_BOUND__NO_BIOLOGICAL_OUTCOME_AUTHORITY":
        raise G2StaticPolicyError("coverage contract drift: status mismatch")
    if set(contract.get("foundation_candidates", [])) != FOUNDATION_CANDIDATES:
        raise G2StaticPolicyError("coverage contract drift: foundation candidate set mismatch")
    if contract.get("specialist_candidate") != SPECIALIST:
        raise G2StaticPolicyError("coverage contract drift: specialist mismatch")
    if contract.get("specialist_foundation_rescue_authorized") is not False:
        raise G2StaticPolicyError("coverage contract drift: specialist rescue authority mismatch")
    if contract.get("claim_scope_rule") != "FOUNDATION_ENVELOPE_EQUALS_ALL_PHYSICALLY_SUPPORTED_FROZEN_STRATA__SPECIALIST_ENVELOPE_SUPPORT_LIMITED__NO_POSTHOC_SCOPE_SHRINKAGE":
        raise G2StaticPolicyError("coverage contract drift: claim scope rule mismatch")
    if contract.get("donor_transfer_rule") != "REQUIRES_SUPPORTED_READER_FIT_AND_SUPPORTED_HELDOUT_DONOR_STRATA":
        raise G2StaticPolicyError("coverage contract drift: donor transfer rule mismatch")

    counts = contract.get("candidate_support_state_counts")
    statuses = contract.get("claim_envelope_status")
    envelopes = contract.get("mandatory_claim_envelopes")
    if not isinstance(counts, Mapping) or not isinstance(statuses, Mapping) or not isinstance(envelopes, Mapping):
        raise G2StaticPolicyError("coverage contract drift: candidate support maps missing")
    expected_candidates = FOUNDATION_CANDIDATES | {SPECIALIST}
    if set(counts) != expected_candidates or set(statuses) != expected_candidates or set(envelopes) != expected_candidates:
        raise G2StaticPolicyError("coverage contract drift: candidate keys mismatch")
    for candidate_id in FOUNDATION_CANDIDATES:
        if counts[candidate_id] != _EXPECTED_FOUNDATION_COUNTS:
            raise G2StaticPolicyError(f"coverage contract drift: {candidate_id} support counts changed")
        if statuses[candidate_id] != _EXPECTED_FOUNDATION_STATUS:
            raise G2StaticPolicyError(f"coverage contract drift: {candidate_id} claim status changed")
        if envelopes[candidate_id] != []:
            raise G2StaticPolicyError(f"coverage contract drift: {candidate_id} envelope manufactured before support freeze")
    if counts[SPECIALIST] != _EXPECTED_SPECIALIST_COUNTS:
        raise G2StaticPolicyError("coverage contract drift: specialist support counts changed")
    if statuses[SPECIALIST] != _EXPECTED_SPECIALIST_STATUS or envelopes[SPECIALIST] != []:
        raise G2StaticPolicyError("coverage contract drift: specialist envelope/status changed")
    return dict(contract)


def resolve_current_g2_static_policy(
    *,
    candidate_id: str,
    tournament_contract,
    transfer_coverage_contract,
    tournament_registry_source_commit: str,
    support_registry_source_commit: str,
) -> dict:
    """Resolve only what is lawfully knowable from the current frozen registries.

    The current V2 coverage registry contains no supported candidate strata, so
    this function is intentionally incapable of returning an executable G2
    policy. A future support/endpoint overlay requires a new qualified resolver
    version rather than mutating this one after values are seen.
    """
    _validate_source_commits(
        tournament_registry_source_commit=tournament_registry_source_commit,
        support_registry_source_commit=support_registry_source_commit,
    )
    try:
        registry = T.validate_candidate_registry(tournament_contract)
    except Exception as exc:
        raise G2StaticPolicyError(f"tournament registry invalid: {exc}") from exc
    if candidate_id not in registry:
        raise G2StaticPolicyError(f"candidate absent from frozen tournament registry: {candidate_id}")
    coverage = _validate_coverage(transfer_coverage_contract)

    catalog = list(registry[candidate_id]["mandatory_falsifiers"])
    if candidate_id in FOUNDATION_CANDIDATES:
        reason = "CANDIDATE_SPECIFIC_EVIDENCE_SUPPORT_CONTRACT_NOT_FROZEN"
        upstream_state = _EXPECTED_FOUNDATION_STATUS
    elif candidate_id == SPECIALIST:
        reason = "NO_FOUNDATION_SUPPORTED_STRATA__SEPARATE_REGULATORY_CHROMATIN_REGISTRY_REQUIRED"
        upstream_state = _EXPECTED_SPECIALIST_STATUS
    else:  # defensive; registry validation above should make this unreachable
        raise G2StaticPolicyError(f"unsupported candidate class: {candidate_id}")

    return {
        "schema": SCHEMA,
        "status": "BLOCKED_DEPENDENCY",
        "reason": reason,
        "candidate_id": candidate_id,
        "baseline_catalog": catalog,
        "baseline_catalog_semantics": "FROZEN_CANDIDATE_PROVENANCE_ONLY__NOT_CURRENT_APPLICABILITY_POLICY",
        "applicable_baselines": [],
        "required_strata": [],
        "upstream_claim_envelope_status": upstream_state,
        "tournament_registry_source_commit": TOURNAMENT_REGISTRY_SOURCE_COMMIT,
        "support_registry_source_commit": SUPPORT_REGISTRY_SOURCE_COMMIT,
        "future_unlock_requires": [
            "CANDIDATE_SPECIFIC_EVIDENCE_ADDRESS_QUERY_SUPPORT_OVERLAY",
            "FROZEN_CANDIDATE_ENDPOINT_REGISTRY",
            "INDEPENDENT_QUALIFICATION_OF_APPLICABILITY_AND_REQUIRED_STRATA_DERIVATION",
        ],
        "candidate_outcomes_used": False,
        "human_g2_policy_authorized": False,
        "authority": dict(_NO_AUTHORITY),
    }
