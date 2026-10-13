from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import td_test_qualification_package_v2 as P


class RelationalAdapterError(ValueError):
    pass


MANDATORY_RELATIONAL_CAPABILITIES = (
    "REL_BROAD_MESO_POSITIVE",
    "REL_FINE_RECURRENT_POSITIVE",
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_SOURCE_VISIBILITY_STRESS",
    "REL_TECHNICAL_TWIN_NEGATIVE",
    "REL_NULL_NEGATIVE",
    "REL_UNDERPOWERED_POSITIVE",
)
OPAQUE_CONTROL_PROFILE_COUNT = 5

_EXECUTOR_INPUT_FIELDS = frozenset({
    "source", "panel_id",
    "z_values", "x_values", "y_values",
    "z_measured", "x_measured", "y_measured",
    "z_feature_ids", "x_feature_ids", "y_feature_ids",
    "donor_ids", "operator_ids", "global_rows",
    "source_library", "detected_genes",
    "focal_mask", "neighbor_pool_mask", "min_focal_anchors_per_donor",
    "control_profiles",
})
_CONTROL_PROFILE_FIELDS = frozenset({"focal_mask", "neighbor_pool_mask", "min_focal_anchors_per_donor"})
_FORBIDDEN_UPSTREAM_TD_FIELDS = frozenset({
    "z_distances", "x_distances", "y_distances", "null_y_identity_maps",
    "pair_coordinates", "pair_signs", "observed_statistic", "null_statistics",
    "expected_status", "controller_truth", "R", "pseudo_rare", "challenge_kind",
    "semantic_class", "capability_id", "control_roles",
})
_FORBIDDEN_CONTROL_ID_TOKENS = (
    "REL_", "DONOR_MATCHED_COMMON", "DEPTH_DETECTED_SUM_MATCHED", "SOURCE_OPERATOR_MATCHED",
    "WRONG_CELL", "PSEUDO_RARE_TECHNICAL", "POSITIVE_TRUTH", "NEGATIVE_TRUTH",
    "UNDERIDENTIFIED_TRUTH", "STRESS_TRUTH", "RARE", "NULL", "TECHNICAL",
)
_PAYLOAD_FIELDS = frozenset({"authenticated_fit_view_sha256", "executor_input"})
_AUTHORITY = {
    "synthetic_world_generation_authorized": False,
    "synthetic_world_regeneration_authorized": False,
    "real_execution_authorized": False,
    "target_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


@dataclass(frozen=True)
class RelationalQualificationAdapterReceipt:
    status: str
    package_id: str
    package_sha256: str
    fit_inputs: dict[str, dict]
    authority: dict[str, bool]


def _validate_control_profiles(value, challenge_id: str) -> dict:
    if not isinstance(value, Mapping):
        raise RelationalAdapterError(f"control_profiles must be a mapping: {challenge_id}")
    if len(value) != OPAQUE_CONTROL_PROFILE_COUNT:
        raise RelationalAdapterError(
            f"every blinded challenge must carry exactly {OPAQUE_CONTROL_PROFILE_COUNT} opaque control profiles: {challenge_id}"
        )
    out = {}
    for control_id, rec in value.items():
        if not isinstance(control_id, str) or not control_id:
            raise RelationalAdapterError(f"control IDs must be opaque nonempty strings: {challenge_id}")
        if any(token in control_id.upper() for token in _FORBIDDEN_CONTROL_ID_TOKENS):
            raise RelationalAdapterError(f"control IDs must be opaque: {challenge_id}")
        if not isinstance(rec, Mapping) or set(rec) != _CONTROL_PROFILE_FIELDS:
            raise RelationalAdapterError(
                f"control profile fields must exactly match focal/neighbor masks and support minimum: {challenge_id}"
            )
        minimum = rec.get("min_focal_anchors_per_donor")
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
            raise RelationalAdapterError(f"control min_focal_anchors_per_donor must be positive: {challenge_id}")
        out[control_id] = dict(rec)
    return out


def build_relational_qualification_adapter(
    package: P.ValidatedExternalPackage,
    challenge_payloads: Mapping[str, Mapping],
) -> RelationalQualificationAdapterReceipt:
    if not isinstance(package, P.ValidatedExternalPackage):
        raise RelationalAdapterError("package must be a V2 ValidatedExternalPackage")
    if not isinstance(challenge_payloads, Mapping):
        raise RelationalAdapterError("challenge_payloads must be a mapping")
    if len(package.fit_views) != len(MANDATORY_RELATIONAL_CAPABILITIES):
        raise RelationalAdapterError("V2 package must contain exactly nine opaque challenges")
    if set(challenge_payloads) != set(package.fit_views):
        raise RelationalAdapterError("challenge_payloads must cover the exact opaque challenge set")

    fit_inputs = {}
    for challenge_id in sorted(package.fit_views):
        payload = challenge_payloads[challenge_id]
        if not isinstance(payload, Mapping) or set(payload) != _PAYLOAD_FIELDS:
            raise RelationalAdapterError(
                "each challenge payload must contain exactly authenticated_fit_view_sha256 and executor_input"
            )
        expected_sha = package.fit_views[challenge_id]
        if payload.get("authenticated_fit_view_sha256") != expected_sha:
            raise RelationalAdapterError(f"fit-view SHA-256 mismatch: {challenge_id}")
        inp = payload.get("executor_input")
        if not isinstance(inp, Mapping):
            raise RelationalAdapterError(f"executor_input must be a mapping: {challenge_id}")
        fields = set(inp)
        leaked = sorted(fields & _FORBIDDEN_UPSTREAM_TD_FIELDS)
        if leaked or fields != _EXECUTOR_INPUT_FIELDS:
            raise RelationalAdapterError(f"executor_input fields must exactly match the blinded TD V2 schema: {challenge_id}")
        fit = dict(inp)
        fit["control_profiles"] = _validate_control_profiles(inp.get("control_profiles"), challenge_id)
        fit["profile_id"] = challenge_id
        fit_inputs[challenge_id] = fit

    return RelationalQualificationAdapterReceipt(
        status="READY",
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        fit_inputs=fit_inputs,
        authority=dict(_AUTHORITY),
    )
