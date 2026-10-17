"""Outcome-blind static G11 transfer / G12 claim-envelope contract.

This module consumes only a frozen population/evidence/support registry. It does
not read candidate scores or biological outcomes and cannot authorize real TD.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence


class StaticContractError(ValueError):
    pass


CANDIDATES = (
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
    "C5_REGULATORY_SPECIALIST",
)
FOUNDATION = frozenset(CANDIDATES[:-1])
SPECIALIST = "C5_REGULATORY_SPECIALIST"
DIMENSIONS = (
    "DONOR",
    "SOURCE",
    "OPERATOR_MATRIX",
    "STUDY_FAMILY",
    "TECHNOLOGY",
)
_DIMENSION_FIELDS = {
    "DONOR": "donor_id",
    "SOURCE": "source",
    "OPERATOR_MATRIX": "operator_matrix",
    "STUDY_FAMILY": "study_family",
    "TECHNOLOGY": "technology",
}
_ALLOWED_TOP = {"schema", "frozen", "candidate_transfer_claims", "strata"}
_ALLOWED_STRATUM = {
    "stratum_id", "donor_id", "source", "operator_matrix", "study_family",
    "technology", "candidate_support",
}
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _require_nonempty_string(value, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise StaticContractError(f"{field} must be a nonempty string")
    return value


def _validate_claims(value) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, Mapping):
        raise StaticContractError("candidate_transfer_claims must be a mapping")
    if set(value) != set(CANDIDATES):
        raise StaticContractError("candidate_transfer_claims must cover exact candidate set")
    out: dict[str, tuple[str, ...]] = {}
    for candidate in CANDIDATES:
        dims = value[candidate]
        if not isinstance(dims, Sequence) or isinstance(dims, (str, bytes)):
            raise StaticContractError(f"transfer claims for {candidate} must be a sequence")
        dims = tuple(dims)
        if any(not isinstance(dim, str) or not dim for dim in dims):
            raise StaticContractError(f"transfer claims for {candidate} must be nonempty strings")
        if len(set(dims)) != len(dims):
            raise StaticContractError(f"duplicate transfer claim for {candidate}")
        unknown = set(dims) - set(DIMENSIONS)
        if unknown:
            raise StaticContractError(f"unknown transfer dimensions for {candidate}: {sorted(unknown)}")
        out[candidate] = dims
    return out


def _validate_support(value, stratum_id: str) -> dict[str, bool]:
    if not isinstance(value, Mapping) or set(value) != set(CANDIDATES):
        raise StaticContractError(f"candidate_support for {stratum_id} must cover exact candidate set")
    out: dict[str, bool] = {}
    for candidate in CANDIDATES:
        flag = value[candidate]
        if type(flag) is not bool:
            raise StaticContractError(f"candidate_support for {stratum_id}/{candidate} must be boolean")
        out[candidate] = flag
    return out


def _validate_strata(value) -> list[dict]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise StaticContractError("strata must be a nonempty sequence")
    rows: list[dict] = []
    seen: set[str] = set()
    for raw in value:
        if not isinstance(raw, Mapping):
            raise StaticContractError("each stratum must be a mapping")
        extra = set(raw) - _ALLOWED_STRATUM
        missing = _ALLOWED_STRATUM - set(raw)
        if extra:
            raise StaticContractError(f"unexpected stratum fields: {sorted(extra)}")
        if missing:
            raise StaticContractError(f"missing stratum fields: {sorted(missing)}")
        row = {
            "stratum_id": _require_nonempty_string(raw["stratum_id"], "stratum_id"),
            "donor_id": _require_nonempty_string(raw["donor_id"], "donor_id"),
            "source": _require_nonempty_string(raw["source"], "source"),
            "operator_matrix": _require_nonempty_string(raw["operator_matrix"], "operator_matrix"),
            "study_family": _require_nonempty_string(raw["study_family"], "study_family"),
            "technology": _require_nonempty_string(raw["technology"], "technology"),
        }
        if row["stratum_id"] in seen:
            raise StaticContractError(f"duplicate stratum_id: {row['stratum_id']}")
        seen.add(row["stratum_id"])
        row["candidate_support"] = _validate_support(raw["candidate_support"], row["stratum_id"])
        rows.append(row)
    rows.sort(key=lambda r: r["stratum_id"])
    return rows


def derive_static_contract(registry: Mapping) -> dict:
    if not isinstance(registry, Mapping):
        raise StaticContractError("registry must be a mapping")
    extra = set(registry) - _ALLOWED_TOP
    missing = _ALLOWED_TOP - set(registry)
    if extra:
        raise StaticContractError(f"unexpected registry fields: {sorted(extra)}")
    if missing:
        raise StaticContractError(f"missing registry fields: {sorted(missing)}")
    if registry.get("schema") != "JEPA_TD_REAL_STATIC_POPULATION_SUPPORT_REGISTRY_V1":
        raise StaticContractError("registry schema mismatch")
    if registry.get("frozen") is not True:
        raise StaticContractError("registry must be explicitly frozen before derivation")

    claims = _validate_claims(registry["candidate_transfer_claims"])
    strata = _validate_strata(registry["strata"])

    envelopes: dict[str, list[str]] = {}
    envelope_status: dict[str, str] = {}
    applicability: dict[str, dict[str, str]] = {}

    for candidate in CANDIDATES:
        supported = [row for row in strata if row["candidate_support"][candidate] is True]
        envelopes[candidate] = [row["stratum_id"] for row in supported]
        envelope_status[candidate] = (
            "SUPPORTED_ENVELOPE_FROZEN" if supported else "NO_SUPPORTED_STRATA__NOT_ESTIMABLE"
        )
        applicability[candidate] = {}
        for dimension in DIMENSIONS:
            if dimension not in claims[candidate]:
                applicability[candidate][dimension] = "NOT_APPLICABLE_STRUCTURAL"
                continue
            field = _DIMENSION_FIELDS[dimension]
            levels = {row[field] for row in supported}
            applicability[candidate][dimension] = (
                "REQUIRED" if len(levels) >= 2 else "BLOCKED_DEPENDENCY"
            )

    return {
        "schema": "JEPA_TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V1",
        "status": "STATIC_CONTRACT_DERIVED__NO_BIOLOGICAL_OUTCOME_AUTHORITY",
        "transfer_applicability": applicability,
        "mandatory_claim_envelopes": envelopes,
        "claim_envelope_status": envelope_status,
        "foundation_candidates": sorted(FOUNDATION),
        "specialist_candidate": SPECIALIST,
        "specialist_foundation_rescue_authorized": False,
        "claim_scope_rule": (
            "FOUNDATION_ENVELOPE_EQUALS_ALL_PHYSICALLY_SUPPORTED_FROZEN_STRATA__"
            "SPECIALIST_ENVELOPE_SUPPORT_LIMITED__NO_POSTHOC_SCOPE_SHRINKAGE"
        ),
        "authority": dict(NO_AUTHORITY),
    }
