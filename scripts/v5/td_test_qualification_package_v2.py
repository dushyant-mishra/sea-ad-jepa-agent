from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class PackageBindingError(ValueError):
    pass


EXPECTED_SCHEMA = "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2"
EXPECTED_CHALLENGE_COUNT = 9
AUTHORITY_KEYS = frozenset({
    "synthetic_world_generation_authorized",
    "synthetic_world_regeneration_authorized",
    "qualification_model_fitting_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
})
FORBIDDEN_BINDING_FIELDS = frozenset({
    "capabilities", "claims", "semantic_classes", "expected_statuses", "control_roles",
})
FORBIDDEN_FIT_VIEW_FIELDS = frozenset({
    "R", "pseudo_rare", "challenge_kind", "challenge_id_semantics", "expected_status",
    "controller_truth", "controller_truth_sha256", "world_kind", "regime", "capability_id",
    "semantic_class", "control_roles", "z_distances", "x_distances", "y_distances",
    "null_y_identity_maps", "pair_coordinates", "pair_signs", "observed_statistic", "null_statistics",
})


@dataclass(frozen=True)
class ValidatedExternalPackage:
    package_id: str
    package_sha256: str
    fit_views: dict[str, str]
    controller_truth_sha256: str
    fit_view_fields: tuple[str, ...]


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _require_nonempty_list(value, label: str) -> list:
    if not isinstance(value, list) or not value:
        raise PackageBindingError(f"{label} must be a nonempty list")
    return value


def validate_external_package_binding(binding: Mapping, *, authenticated_package_sha256: str) -> ValidatedExternalPackage:
    if not isinstance(binding, Mapping):
        raise PackageBindingError("binding must be a mapping")
    if binding.get("schema") != EXPECTED_SCHEMA:
        raise PackageBindingError("wrong external synthetic package binding schema")
    leaked_top = sorted(set(binding) & FORBIDDEN_BINDING_FIELDS)
    if leaked_top:
        raise PackageBindingError(f"controller-only semantic fields are forbidden pre-fit: {leaked_top}")
    required = {
        "schema", "package_id", "package_sha256", "controller_truth_sha256",
        "fit_view_fields", "fit_views", "authority",
    }
    if set(binding) != required:
        raise PackageBindingError("binding fields must exactly match the semantically blind V2 schema")

    package_id = binding.get("package_id")
    if not isinstance(package_id, str) or not package_id:
        raise PackageBindingError("package_id must be a nonempty string")
    package_sha256 = binding.get("package_sha256")
    if not _is_sha256(package_sha256) or not _is_sha256(authenticated_package_sha256):
        raise PackageBindingError("package SHA-256 must be lowercase SHA-256")
    if package_sha256 != authenticated_package_sha256:
        raise PackageBindingError("package SHA-256 mismatch against authenticated package")
    controller_truth_sha256 = binding.get("controller_truth_sha256")
    if not _is_sha256(controller_truth_sha256):
        raise PackageBindingError("controller_truth_sha256 must be lowercase SHA-256")

    authority = binding.get("authority")
    if not isinstance(authority, Mapping) or set(authority) != AUTHORITY_KEYS:
        raise PackageBindingError("authority keys must exactly match the TD read-only boundary")
    if any(value is not False for value in authority.values()):
        raise PackageBindingError("external package cannot carry execution or selection authority")

    fit_view_fields = _require_nonempty_list(binding.get("fit_view_fields"), "fit_view_fields")
    if any(not isinstance(field, str) or not field for field in fit_view_fields):
        raise PackageBindingError("fit_view_fields must contain nonempty strings")
    if len(fit_view_fields) != len(set(fit_view_fields)):
        raise PackageBindingError("fit_view_fields must be unique")
    leaked = sorted(set(fit_view_fields) & FORBIDDEN_FIT_VIEW_FIELDS)
    if leaked:
        raise PackageBindingError(f"controller/TD-estimand fields are forbidden in fit view: {leaked}")

    fit_views = {}
    for rec in _require_nonempty_list(binding.get("fit_views"), "fit_views"):
        if not isinstance(rec, Mapping) or set(rec) != {"challenge_id", "sha256"}:
            raise PackageBindingError("each fit_view record must contain only challenge_id and sha256")
        challenge_id = rec.get("challenge_id")
        sha = rec.get("sha256")
        if not isinstance(challenge_id, str) or not challenge_id:
            raise PackageBindingError("challenge_id must be an opaque nonempty string")
        if challenge_id in fit_views:
            raise PackageBindingError(f"duplicate challenge_id: {challenge_id}")
        if not _is_sha256(sha):
            raise PackageBindingError(f"fit-view sha256 must be lowercase SHA-256: {challenge_id}")
        fit_views[challenge_id] = sha
    if len(fit_views) != EXPECTED_CHALLENGE_COUNT:
        raise PackageBindingError(f"exactly {EXPECTED_CHALLENGE_COUNT} opaque fit challenges are required")

    return ValidatedExternalPackage(
        package_id=package_id,
        package_sha256=package_sha256,
        fit_views=fit_views,
        controller_truth_sha256=controller_truth_sha256,
        fit_view_fields=tuple(fit_view_fields),
    )
