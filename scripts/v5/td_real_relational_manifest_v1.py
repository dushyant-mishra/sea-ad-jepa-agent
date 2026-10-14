"""Outcome-blind static relational-identity contract for real-TD R1.

The contract freezes the repaired-address scale-free triplet identities and
lawful comparison structure only. It does not compute recurrence, open human
candidate outcomes, or authorize real TD.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence


class RelationalManifestError(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_RELATIONAL_MANIFEST_V1"
CANDIDATE_ID = "C2_RELATIONAL_SHARED"
RELATION_FAMILY = "SCALE_FREE_TRIPLET_ORDER"
SCALE_CLASS = "GLOBAL_SCALE_FREE"
REQUIRED_SOURCES = ("HVS", "NPH52", "SEA_AD")
NULL_PERMUTATION_UNIT = "RELATION_ID_WITHIN_DONOR_SOURCE_SUPPORT_STRATUM"
ADDRESS_BINDING_STATE = "REPAIRED_41K_ADDRESS_BOUND"
SUPPORT_SEMANTICS = {
    "measured_zero": "VALID_MEASUREMENT",
    "unresolved_or_unsupported": "ABSTAIN",
    "imputation": "FORBIDDEN",
}
_ALLOWED_TOP = {
    "schema",
    "frozen",
    "candidate_id",
    "relation_family",
    "scale_class",
    "required_sources",
    "lawful_view_ids",
    "null_permutation_unit",
    "support_semantics",
    "relation_units",
}
_ALLOWED_RELATION = {"relation_id", "member_address_ids", "address_binding_state"}
NO_AUTHORITY = {
    "value_read_authorized": False,
    "real_tournament_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _token(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise RelationalManifestError(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def _token_list(value, label: str, *, minimum: int = 1) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) < minimum:
        raise RelationalManifestError(f"{label} must contain at least {minimum} nonempty strings")
    out = []
    for item in value:
        if not isinstance(item, str) or not item or item != item.strip() or "\0" in item:
            raise RelationalManifestError(f"{label} values must be nonempty strings")
        out.append(item)
    if len(set(out)) != len(out):
        raise RelationalManifestError(f"{label} values must be unique")
    return tuple(out)


def _relation_unit(raw: Mapping, index: int) -> dict:
    if not isinstance(raw, Mapping) or set(raw) != _ALLOWED_RELATION:
        raise RelationalManifestError(f"relation_units[{index}] fields differ from frozen schema")
    relation_id = _token(raw["relation_id"], f"relation_units[{index}].relation_id")
    raw_members = raw["member_address_ids"]
    if isinstance(raw_members, (str, bytes)) or not isinstance(raw_members, Sequence) or len(raw_members) != 3:
        raise RelationalManifestError("each scale-free triplet must bind exactly three unique member addresses")
    members_list = []
    for item in raw_members:
        if not isinstance(item, str) or not item or item != item.strip() or "\0" in item:
            raise RelationalManifestError("member_address_ids values must be nonempty strings")
        members_list.append(item)
    if len(set(members_list)) != 3:
        raise RelationalManifestError("each scale-free triplet must bind exactly three unique member addresses")
    members = tuple(members_list)
    binding = _token(raw["address_binding_state"], f"relation_units[{index}].address_binding_state")
    if binding != ADDRESS_BINDING_STATE:
        raise RelationalManifestError(
            "every relation unit must be REPAIRED_41K_ADDRESS_BOUND before current biological use"
        )
    return {
        "relation_id": relation_id,
        "member_address_ids": list(members),
        "address_binding_state": binding,
    }


def derive_relational_contract(manifest: Mapping) -> dict:
    if not isinstance(manifest, Mapping) or set(manifest) != _ALLOWED_TOP:
        raise RelationalManifestError("relational manifest fields differ from frozen schema")
    if manifest.get("schema") != SCHEMA:
        raise RelationalManifestError("relational manifest schema mismatch")
    if manifest.get("frozen") is not True:
        raise RelationalManifestError("relational manifest must be explicitly frozen")

    candidate_id = _token(manifest["candidate_id"], "candidate_id")
    if candidate_id != CANDIDATE_ID:
        raise RelationalManifestError("R1 V1 is restricted to C2_RELATIONAL_SHARED")

    relation_family = _token(manifest["relation_family"], "relation_family")
    if relation_family != RELATION_FAMILY:
        raise RelationalManifestError("R1 V1 relation_family must be SCALE_FREE_TRIPLET_ORDER")

    scale_class = _token(manifest["scale_class"], "scale_class")
    if scale_class != SCALE_CLASS:
        raise RelationalManifestError(
            "fine locality is closed in R1 V1; scale_class must remain GLOBAL_SCALE_FREE"
        )

    sources = _token_list(manifest["required_sources"], "required_sources")
    if sources != REQUIRED_SOURCES:
        raise RelationalManifestError("required_sources must be exactly HVS, NPH52, SEA_AD and noncompensating")

    raw_views = manifest["lawful_view_ids"]
    if isinstance(raw_views, (str, bytes)) or not isinstance(raw_views, Sequence) or len(raw_views) < 2:
        raise RelationalManifestError("at least two lawful views are required")
    views = _token_list(raw_views, "lawful_view_ids", minimum=2)

    null_unit = _token(manifest["null_permutation_unit"], "null_permutation_unit")
    if null_unit != NULL_PERMUTATION_UNIT:
        raise RelationalManifestError(
            "null permutation must preserve donor, source, and support strata while breaking relation identity"
        )

    if manifest["support_semantics"] != SUPPORT_SEMANTICS:
        raise RelationalManifestError("support semantics drift; abstention and imputation rules must remain exact")

    raw_units = manifest["relation_units"]
    if isinstance(raw_units, (str, bytes)) or not isinstance(raw_units, Sequence) or not raw_units:
        raise RelationalManifestError("relation_units must be a nonempty sequence")
    units = [_relation_unit(raw, i) for i, raw in enumerate(raw_units)]
    relation_ids = [unit["relation_id"] for unit in units]
    if len(set(relation_ids)) != len(relation_ids):
        raise RelationalManifestError("relation_id values must be unique")

    return {
        "schema": "JEPA_TD_REAL_RELATIONAL_CONTRACT_V1",
        "status": "RELATIONAL_MANIFEST_FROZEN",
        "candidate_id": candidate_id,
        "relation_family": relation_family,
        "scale_class": scale_class,
        "required_sources": list(sources),
        "lawful_view_ids": list(views),
        "null_permutation_unit": null_unit,
        "support_semantics": dict(SUPPORT_SEMANTICS),
        "relation_units": units,
        "relation_count": len(units),
        "fine_locality_authorized": False,
        "graph_topology_claim_authorized": False,
        "historical_scope": (
            "SCALE_FREE_RELATIONAL_INCUMBENT_PRESERVED__"
            "TD57C_FINE_LOCALITY_REMAINS_CLOSED__"
            "HISTORICAL_PANEL_VALUES_NOT_IMPORTED_AS_CURRENT_AUTHORITY"
        ),
        "claim_boundary": "STATIC_RELATIONAL_IDENTITY_ONLY__NO_R1_BIOLOGICAL_OUTCOME",
        "authority": dict(NO_AUTHORITY),
    }
