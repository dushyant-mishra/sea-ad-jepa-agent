"""Outcome-blind G11/G12 static transfer/coverage contract V2.

V2 binds the frozen reader partition for every stratum and only declares donor
transfer structurally available when supported fit and held-out donor strata
both exist. It reads no biological outcomes and grants no execution authority.
"""
from __future__ import annotations

from collections import Counter, defaultdict
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
DIMENSIONS = ("DONOR", "SOURCE", "OPERATOR_MATRIX", "STUDY_FAMILY", "TECHNOLOGY")
_DIMENSION_FIELDS = {
    "DONOR": "donor_id",
    "SOURCE": "source",
    "OPERATOR_MATRIX": "operator_matrix",
    "STUDY_FAMILY": "study_family",
    "TECHNOLOGY": "technology",
}
PARTITIONS = ("reader_fit", "reader_validation", "reader_oracle")
HELDOUT_PARTITIONS = frozenset({"reader_validation", "reader_oracle"})
_ALLOWED_TOP = {"schema", "frozen", "candidate_transfer_claims", "strata"}
_ALLOWED_STRATUM = {
    "stratum_id", "donor_id", "source", "operator_matrix", "study_family",
    "technology", "reader_partition", "candidate_support_state",
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
SUPPORT_STATES = frozenset({"SUPPORTED", "UNSUPPORTED_STRUCTURAL", "BLOCKED_EVIDENCE_CONTRACT"})


def _require_nonempty_string(value, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise StaticContractError(f"{field} must be a nonempty string")
    return value


def _validate_claims(value) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, Mapping) or set(value) != set(CANDIDATES):
        raise StaticContractError("candidate_transfer_claims must cover exact candidate set")
    out = {}
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


def _validate_support_state(value, stratum_id: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != set(CANDIDATES):
        raise StaticContractError(f"candidate_support_state for {stratum_id} must cover exact candidate set")
    out = {}
    for candidate in CANDIDATES:
        state = value[candidate]
        if state not in SUPPORT_STATES:
            raise StaticContractError(f"invalid candidate_support_state for {stratum_id}/{candidate}: {state}")
        out[candidate] = state
    return out


def _validate_strata(value) -> list[dict]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise StaticContractError("strata must be a nonempty sequence")
    rows, seen = [], set()
    donor_partitions: dict[str, set[str]] = defaultdict(set)
    for raw in value:
        if not isinstance(raw, Mapping):
            raise StaticContractError("each stratum must be a mapping")
        extra = set(raw) - _ALLOWED_STRATUM
        missing = _ALLOWED_STRATUM - set(raw)
        if extra:
            raise StaticContractError(f"unexpected stratum fields: {sorted(extra)}")
        if missing:
            raise StaticContractError(f"missing stratum fields: {sorted(missing)}")
        row = {k: _require_nonempty_string(raw[k], k) for k in _ALLOWED_STRATUM - {"candidate_support_state"}}
        if row["reader_partition"] not in PARTITIONS:
            raise StaticContractError(f"invalid reader_partition: {row['reader_partition']}")
        if row["stratum_id"] in seen:
            raise StaticContractError(f"duplicate stratum_id: {row['stratum_id']}")
        seen.add(row["stratum_id"])
        donor_partitions[row["donor_id"]].add(row["reader_partition"])
        row["candidate_support_state"] = _validate_support_state(raw["candidate_support_state"], row["stratum_id"])
        rows.append(row)
    offenders = sorted(d for d, parts in donor_partitions.items() if len(parts) > 1)
    if offenders:
        raise StaticContractError(f"donor appears in multiple reader partitions: {offenders}")
    rows.sort(key=lambda r: r["stratum_id"])
    return rows


def _dimension_status(candidate: str, dimension: str, claims: Mapping[str, tuple[str, ...]], supported: list[dict]) -> str:
    if dimension not in claims[candidate]:
        return "NOT_APPLICABLE_STRUCTURAL"
    if not supported:
        return "BLOCKED_DEPENDENCY"
    if dimension == "DONOR":
        fit_donors = {r["donor_id"] for r in supported if r["reader_partition"] == "reader_fit"}
        held_donors = {r["donor_id"] for r in supported if r["reader_partition"] in HELDOUT_PARTITIONS}
        return "REQUIRED" if fit_donors and held_donors else "BLOCKED_DEPENDENCY"
    field = _DIMENSION_FIELDS[dimension]
    return "REQUIRED" if len({r[field] for r in supported}) >= 2 else "BLOCKED_DEPENDENCY"


def derive_static_contract(registry: Mapping) -> dict:
    if not isinstance(registry, Mapping):
        raise StaticContractError("registry must be a mapping")
    extra, missing = set(registry) - _ALLOWED_TOP, _ALLOWED_TOP - set(registry)
    if extra:
        raise StaticContractError(f"unexpected registry fields: {sorted(extra)}")
    if missing:
        raise StaticContractError(f"missing registry fields: {sorted(missing)}")
    if registry.get("schema") != "JEPA_TD_REAL_STATIC_POPULATION_SUPPORT_REGISTRY_V2":
        raise StaticContractError("registry schema mismatch")
    if registry.get("frozen") is not True:
        raise StaticContractError("registry must be explicitly frozen before derivation")

    claims = _validate_claims(registry["candidate_transfer_claims"])
    strata = _validate_strata(registry["strata"])
    envelopes, envelope_status, applicability, partition_counts = {}, {}, {}, {}
    for candidate in CANDIDATES:
        supported = [row for row in strata if row["candidate_support_state"][candidate] == "SUPPORTED"]
        blocked = [row for row in strata if row["candidate_support_state"][candidate] == "BLOCKED_EVIDENCE_CONTRACT"]
        envelopes[candidate] = [row["stratum_id"] for row in supported]
        if blocked:
            envelope_status[candidate] = "SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE"
            applicability[candidate] = {
                dim: ("NOT_APPLICABLE_STRUCTURAL" if dim not in claims[candidate] else "BLOCKED_DEPENDENCY")
                for dim in DIMENSIONS
            }
        else:
            envelope_status[candidate] = "SUPPORTED_ENVELOPE_FROZEN" if supported else "NO_SUPPORTED_STRATA__NOT_ESTIMABLE"
            applicability[candidate] = {dim: _dimension_status(candidate, dim, claims, supported) for dim in DIMENSIONS}
        counts = Counter(row["reader_partition"] for row in supported)
        partition_counts[candidate] = {p: counts.get(p, 0) for p in PARTITIONS}

    return {
        "schema": "JEPA_TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V2",
        "status": "STATIC_CONTRACT_DERIVED__SPLIT_BOUND__NO_BIOLOGICAL_OUTCOME_AUTHORITY",
        "transfer_applicability": applicability,
        "mandatory_claim_envelopes": envelopes,
        "claim_envelope_status": envelope_status,
        "supported_partition_counts": partition_counts,
        "candidate_support_state_counts": {
            candidate: {state: sum(1 for row in strata if row["candidate_support_state"][candidate] == state) for state in sorted(SUPPORT_STATES)}
            for candidate in CANDIDATES
        },
        "foundation_candidates": sorted(FOUNDATION),
        "specialist_candidate": SPECIALIST,
        "specialist_foundation_rescue_authorized": False,
        "claim_scope_rule": (
            "FOUNDATION_ENVELOPE_EQUALS_ALL_PHYSICALLY_SUPPORTED_FROZEN_STRATA__"
            "SPECIALIST_ENVELOPE_SUPPORT_LIMITED__NO_POSTHOC_SCOPE_SHRINKAGE"
        ),
        "donor_transfer_rule": "REQUIRES_SUPPORTED_READER_FIT_AND_SUPPORTED_HELDOUT_DONOR_STRATA",
        "authority": dict(NO_AUTHORITY),
    }
