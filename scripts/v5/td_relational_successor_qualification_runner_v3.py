from __future__ import annotations

from typing import Mapping

import td_relational_successor_qualification_runner_v2 as Q2
import td_test_qualification_package_v2 as P


class QualificationRunnerV3Error(ValueError):
    pass


CONTROLLER_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V3"
BLIND_NONCE_HEX_LENGTH = 64

# The biological executor and output dataclasses are intentionally unchanged.
BlindedFitReceipt = Q2.BlindedFitReceipt
RelationalQualificationRunReceipt = Q2.RelationalQualificationRunReceipt
execute_blinded_fit = Q2.execute_blinded_fit
canonical_sha256 = Q2.canonical_sha256
MANDATORY_CONTROL_ROLES = Q2.MANDATORY_CONTROL_ROLES
RARE_CONTROL_CAPABILITIES = Q2.RARE_CONTROL_CAPABILITIES
CONTROLLER_AUTHORITY_KEYS = Q2.CONTROLLER_AUTHORITY_KEYS
RUN_AUTHORITY_KEYS = Q2.RUN_AUTHORITY_KEYS
SEMANTIC_CLASSES = Q2.SEMANTIC_CLASSES


def _is_hex(value: object, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(ch in "0123456789abcdef" for ch in value)
    )


def _all_false_controller_authority(value: object) -> None:
    if not isinstance(value, Mapping) or set(value) != CONTROLLER_AUTHORITY_KEYS:
        raise QualificationRunnerV3Error("controller manifest authority keys do not match the frozen boundary")
    if any(item is not False for item in value.values()):
        raise QualificationRunnerV3Error("controller manifest cannot carry execution or selection authority")


def validate_controller_manifest_v3(package: P.ValidatedExternalPackage, manifest: Mapping) -> dict:
    """Authenticate the V3 controller manifest before any semantic adjudication.

    The controller-only 256-bit blind nonce converts the pre-fit SHA-256 from a
    low-entropy semantic-mapping oracle into a hiding commitment. The nonce is
    deliberately absent from the blinded package and fit custody.
    """
    if not isinstance(package, P.ValidatedExternalPackage):
        raise QualificationRunnerV3Error("package must be a V2 ValidatedExternalPackage")
    if not isinstance(manifest, Mapping):
        raise QualificationRunnerV3Error("controller manifest must be a mapping")
    required_top = {"schema", "package_sha256", "blind_nonce", "claims", "authority"}
    if set(manifest) != required_top:
        raise QualificationRunnerV3Error("controller manifest fields differ from the frozen V3 schema")
    if manifest.get("schema") != CONTROLLER_SCHEMA:
        raise QualificationRunnerV3Error("wrong controller manifest V3 schema")
    if manifest.get("package_sha256") != package.package_sha256:
        raise QualificationRunnerV3Error("controller manifest package SHA-256 mismatch")
    if not _is_hex(manifest.get("blind_nonce"), BLIND_NONCE_HEX_LENGTH):
        raise QualificationRunnerV3Error("blind_nonce must be a controller-only 256-bit lowercase hex value")
    _all_false_controller_authority(manifest.get("authority"))
    if canonical_sha256(manifest) != package.controller_truth_sha256:
        raise QualificationRunnerV3Error("controller truth hash mismatch")

    claims = manifest.get("claims")
    # Reuse the mature V2 semantic validator without weakening V3 commitment.
    v2_manifest = {
        "schema": Q2.CONTROLLER_SCHEMA,
        "package_sha256": package.package_sha256,
        "claims": claims,
        "authority": dict(manifest["authority"]),
    }
    proxy = P.ValidatedExternalPackage(
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        fit_views=dict(package.fit_views),
        controller_truth_sha256=canonical_sha256(v2_manifest),
        fit_view_fields=tuple(package.fit_view_fields),
    )
    try:
        normalized = Q2._validate_controller_manifest(proxy, v2_manifest)
    except Q2.QualificationRunnerError as exc:
        raise QualificationRunnerV3Error(str(exc)) from exc
    return normalized


def adjudicate_blinded_qualification(
    *,
    package: P.ValidatedExternalPackage,
    fit_receipt: BlindedFitReceipt,
    controller_manifest: Mapping,
    gate_binding: Mapping,
) -> RelationalQualificationRunReceipt:
    """Adjudicate using V3 hiding commitment while preserving frozen V2 science."""
    validate_controller_manifest_v3(package, controller_manifest)
    v2_manifest = {
        "schema": Q2.CONTROLLER_SCHEMA,
        "package_sha256": package.package_sha256,
        "claims": controller_manifest["claims"],
        "authority": dict(controller_manifest["authority"]),
    }
    proxy = P.ValidatedExternalPackage(
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        fit_views=dict(package.fit_views),
        controller_truth_sha256=canonical_sha256(v2_manifest),
        fit_view_fields=tuple(package.fit_view_fields),
    )
    try:
        return Q2.adjudicate_blinded_qualification(
            package=proxy,
            fit_receipt=fit_receipt,
            controller_manifest=v2_manifest,
            gate_binding=gate_binding,
        )
    except Q2.QualificationRunnerError as exc:
        raise QualificationRunnerV3Error(str(exc)) from exc
