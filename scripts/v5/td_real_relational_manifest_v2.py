"""Outcome-blind static relational contract for real-TD R1 V2.

This prospectively freezes the *molecular ruler* and the anchored-cell triplet
relation separately. Molecular pair coordinates are repaired 41K-address-bound;
R1 relations are q(i;j,k)=sign(d(i,j)-d(i,k)) over one anchor cell and two
comparison cells within a lawful donor/source/operator/support stratum.

No human candidate values are read and no biological PASS is authorized.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence


class RelationalManifestError(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_RELATIONAL_MANIFEST_V2"
CANDIDATE_ID = "C2_RELATIONAL_SHARED"
RELATION_FAMILY = "SCALE_FREE_TRIPLET_ORDER"
SCALE_CLASS = "GLOBAL_SCALE_FREE"
REQUIRED_SOURCES = ("HVS", "NPH52", "SEA_AD")
ADDRESS_BINDING_STATE = "REPAIRED_41K_ADDRESS_BOUND"
NULL_PERMUTATION_UNIT = "RELATION_ID_WITHIN_DONOR_SOURCE_OPERATOR_SUPPORT_STRATUM"
SUPPORT_SEMANTICS = {
    "measured_zero": "VALID_MEASUREMENT",
    "unresolved_or_unsupported": "ABSTAIN",
    "imputation": "FORBIDDEN",
}
RELATION_CONSTRUCTION = {
    "object": "ANCHORED_CELL_TRIPLET_ORDER",
    "distance_formula": "TIE_AWARE_PAIR_ORDER_CONCORDANCE",
    "anchor_comparator_rule": "SAME_DONOR_SOURCE_OPERATOR_SUPPORT_STRATUM",
    "comparator_pair_order": "UNORDERED_CANONICAL_CELL_ID_ORDER",
    "relation_formula": "SIGN_D_IJ_MINUS_D_IK",
    "relation_identity": "ANCHOR_CELL_ID_PLUS_CANONICAL_COMPARATOR_CELL_IDS",
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

_ALLOWED_TOP = {
    "schema",
    "frozen",
    "candidate_id",
    "relation_family",
    "scale_class",
    "required_sources",
    "lawful_views",
    "minimum_informative_pair_coordinates",
    "relation_construction",
    "null_permutation_unit",
    "support_semantics",
}
_ALLOWED_VIEW = {"view_id", "pair_coordinates"}
_ALLOWED_PAIR = {"pair_id", "member_address_ids", "address_binding_state"}


def _token(value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise RelationalManifestError(f"{label} must be a nonempty trimmed NUL-free string")
    return value


def _token_list(value, label: str, *, minimum: int = 1) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) < minimum:
        raise RelationalManifestError(f"{label} must contain at least {minimum} values")
    out = tuple(_token(item, label) for item in value)
    if len(set(out)) != len(out):
        raise RelationalManifestError(f"{label} values must be unique")
    return out


def _pair_coordinate(raw: Mapping, view_index: int, pair_index: int) -> dict:
    if not isinstance(raw, Mapping) or set(raw) != _ALLOWED_PAIR:
        raise RelationalManifestError(
            f"lawful_views[{view_index}].pair_coordinates[{pair_index}] fields differ from frozen schema"
        )
    pair_id = _token(raw["pair_id"], "pair_id")
    members = raw["member_address_ids"]
    if isinstance(members, (str, bytes)) or not isinstance(members, Sequence) or len(members) != 2:
        raise RelationalManifestError("each molecular pair coordinate must bind exactly two repaired addresses")
    a = _token(members[0], "member_address_ids")
    b = _token(members[1], "member_address_ids")
    if a == b:
        raise RelationalManifestError("each molecular pair coordinate must bind exactly two unique repaired addresses")
    binding = _token(raw["address_binding_state"], "address_binding_state")
    if binding != ADDRESS_BINDING_STATE:
        raise RelationalManifestError("every molecular pair coordinate must be REPAIRED_41K_ADDRESS_BOUND")
    return {
        "pair_id": pair_id,
        "member_address_ids": [a, b],
        "address_binding_state": binding,
    }


def _lawful_views(raw_views) -> tuple[list[dict], set[str]]:
    if isinstance(raw_views, (str, bytes)) or not isinstance(raw_views, Sequence) or len(raw_views) < 2:
        raise RelationalManifestError("at least two lawful views are required")
    views: list[dict] = []
    seen_view_ids: set[str] = set()
    address_sets: list[set[str]] = []
    for vi, raw in enumerate(raw_views):
        if not isinstance(raw, Mapping) or set(raw) != _ALLOWED_VIEW:
            raise RelationalManifestError(f"lawful_views[{vi}] fields differ from frozen schema")
        view_id = _token(raw["view_id"], f"lawful_views[{vi}].view_id")
        if view_id in seen_view_ids:
            raise RelationalManifestError("lawful view IDs must be unique")
        seen_view_ids.add(view_id)
        raw_pairs = raw["pair_coordinates"]
        if isinstance(raw_pairs, (str, bytes)) or not isinstance(raw_pairs, Sequence) or not raw_pairs:
            raise RelationalManifestError("each lawful view must contain at least one molecular pair coordinate")
        pairs = [_pair_coordinate(pair, vi, pi) for pi, pair in enumerate(raw_pairs)]
        pair_ids = [p["pair_id"] for p in pairs]
        if len(set(pair_ids)) != len(pair_ids):
            raise RelationalManifestError("pair_id values must be unique within each lawful view")
        addresses = {a for pair in pairs for a in pair["member_address_ids"]}
        address_sets.append(addresses)
        views.append({"view_id": view_id, "pair_coordinates": pairs})
    for i in range(len(address_sets)):
        for j in range(i + 1, len(address_sets)):
            if address_sets[i] & address_sets[j]:
                raise RelationalManifestError("lawful molecular views must be address-disjoint")
    return views, set().union(*address_sets)


def derive_relational_contract(manifest: Mapping) -> dict:
    if not isinstance(manifest, Mapping) or set(manifest) != _ALLOWED_TOP:
        raise RelationalManifestError("relational manifest fields differ from frozen V2 schema")
    if manifest.get("schema") != SCHEMA:
        raise RelationalManifestError("relational manifest schema mismatch")
    if manifest.get("frozen") is not True:
        raise RelationalManifestError("relational manifest must be explicitly frozen")

    candidate = _token(manifest["candidate_id"], "candidate_id")
    if candidate != CANDIDATE_ID:
        raise RelationalManifestError("R1 V2 is restricted to C2_RELATIONAL_SHARED")
    family = _token(manifest["relation_family"], "relation_family")
    if family != RELATION_FAMILY:
        raise RelationalManifestError("R1 V2 relation_family must be SCALE_FREE_TRIPLET_ORDER")
    scale = _token(manifest["scale_class"], "scale_class")
    if scale != SCALE_CLASS:
        raise RelationalManifestError("fine locality remains closed; scale_class must be GLOBAL_SCALE_FREE")

    sources = _token_list(manifest["required_sources"], "required_sources")
    if sources != REQUIRED_SOURCES:
        raise RelationalManifestError("required_sources must be exactly HVS, NPH52, SEA_AD and noncompensating")

    views, _ = _lawful_views(manifest["lawful_views"])
    minimum = manifest["minimum_informative_pair_coordinates"]
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum <= 0:
        raise RelationalManifestError("minimum_informative_pair_coordinates must be a positive integer")
    if any(minimum > len(view["pair_coordinates"]) for view in views):
        raise RelationalManifestError("minimum_informative_pair_coordinates exceeds a lawful view's coordinate count")

    relation = manifest["relation_construction"]
    if relation != RELATION_CONSTRUCTION:
        raise RelationalManifestError(
            "relation construction must remain the frozen anchored cell triplet q(i;j,k)=sign(d(i,j)-d(i,k))"
        )
    null_unit = _token(manifest["null_permutation_unit"], "null_permutation_unit")
    if null_unit != NULL_PERMUTATION_UNIT:
        raise RelationalManifestError(
            "null permutation must preserve donor, source, operator, and support strata while breaking relation identity"
        )
    if manifest["support_semantics"] != SUPPORT_SEMANTICS:
        raise RelationalManifestError("support semantics drift; measured zero/abstention/imputation rules must remain exact")

    return {
        "schema": "JEPA_TD_REAL_RELATIONAL_CONTRACT_V2",
        "status": "RELATIONAL_MANIFEST_V2_FROZEN",
        "candidate_id": candidate,
        "relation_family": family,
        "scale_class": scale,
        "required_sources": list(sources),
        "lawful_views": views,
        "minimum_informative_pair_coordinates": minimum,
        "relation_construction": dict(RELATION_CONSTRUCTION),
        "null_permutation_unit": null_unit,
        "support_semantics": dict(SUPPORT_SEMANTICS),
        "recurrence_statistic": "DONOR_MEAN_EXACT_TRIPLET_ORDER_AGREEMENT",
        "recurrence_orientation": "LARGER_IS_BETTER",
        "adverse_null_summary_rule": "PER_DONOR_UPPER_QUANTILE_AT_EXTERNALLY_FROZEN_GATE_ALPHA",
        "substantive_reference_rule": "SEPARATELY_QUALIFIED_SAME_METRIC_U_REFIT_REQUIRED",
        "decision_scope": (
            "R1_REQUIRES_OBSERVED_RECURRENCE_TO_DEFEAT_ADVERSE_NULL_AND_U_REFIT__"
            "DONOR_PRIMARY__SOURCE_NONCOMPENSATING__NO_FINE_LOCALITY_MINING"
        ),
        "historical_scope": (
            "TD57B_SCALE_FREE_OBJECT_PRESERVED__TD57C_FINE_LOCALITY_CLOSED__"
            "TD59_NEAREST_HALF_NOT_A_PRODUCTION_CONSTANT__NO_HISTORICAL_THRESHOLD_IMPORTED"
        ),
        "human_pass_authorized": False,
        "authority": dict(NO_AUTHORITY),
    }
