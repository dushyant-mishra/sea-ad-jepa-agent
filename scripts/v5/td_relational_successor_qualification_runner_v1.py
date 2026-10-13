from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

import td_relational_successor_capability_reducer_v1 as R
import td_relational_successor_gate_v1 as G
import td_relational_successor_observed_executor_v1 as X
import td_relational_successor_synthetic_adapter_v1 as A
import td_test_of_test_controller_v1 as T
import td_test_qualification_package_v1 as P


class QualificationRunnerError(ValueError):
    pass


CONTROLLER_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V1"
RARE_CONTROL_CAPABILITIES = frozenset({
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_TECHNICAL_TWIN_NEGATIVE",
})
MANDATORY_CONTROL_ROLES = (
    "DONOR_MATCHED_COMMON",
    "DEPTH_DETECTED_SUM_MATCHED",
    "SOURCE_OPERATOR_MATCHED",
    "WRONG_CELL",
    "PSEUDO_RARE_TECHNICAL",
)
CONTROLLER_AUTHORITY_KEYS = frozenset({
    "synthetic_world_generation_authorized",
    "synthetic_world_regeneration_authorized",
    "real_execution_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
})
RUN_AUTHORITY_KEYS = frozenset({
    "real_execution_authorized",
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
})
_IDENTITY_FIELDS = (
    "qualified_gate_executor_sha256",
    "estimand_sha256",
    "decision_rule_sha256",
)
_ALLOWED_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})


@dataclass(frozen=True)
class BlindedFitReceipt:
    package_id: str
    package_sha256: str
    profiles: dict[str, G.RelationalProfileReceipt]
    controls: dict[str, dict[str, G.RelationalProfileReceipt]]
    authority: dict[str, bool]


@dataclass(frozen=True)
class RelationalQualificationRunReceipt:
    status: str
    package_id: str
    package_sha256: str
    capability_statuses: dict[str, str]
    rare_increment_receipts: dict[str, G.RareIncrementReceipt]
    gate_qualification: T.GateQualificationReceipt | None
    missing_requirements: tuple[str, ...]
    authority: dict[str, bool]


def canonical_sha256(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _all_false_authority(value: Mapping, keys: frozenset[str], label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise QualificationRunnerError(f"{label} authority keys do not match the frozen boundary")
    if any(v is not False for v in value.values()):
        raise QualificationRunnerError(f"{label} cannot carry execution or selection authority")


def _profile_summary(profile: G.RelationalProfileReceipt) -> dict:
    return {
        "source": profile.source,
        "panel_id": profile.panel_id,
        "profile_id": profile.profile_id,
        "focal_anchor_count": profile.focal_anchor_count,
        "scale_statuses": {label: result.status for label, result in profile.scale_results.items()},
        "scale_observed": {label: result.observed_statistic for label, result in profile.scale_results.items()},
        "scale_null_p95": {label: result.family_null_p95 for label, result in profile.scale_results.items()},
        "scale_donors": {label: result.n_observed_donors for label, result in profile.scale_results.items()},
    }


def _rare_summary(receipt: G.RareIncrementReceipt | None) -> dict | None:
    if receipt is None:
        return None
    return {
        "source": receipt.source,
        "panel_id": receipt.panel_id,
        "program_profile_id": receipt.program_profile_id,
        "scale_statuses": {label: result.status for label, result in receipt.scale_results.items()},
        "program_margins": {label: result.program_margin for label, result in receipt.scale_results.items()},
        "max_control_margins": {label: result.max_control_margin for label, result in receipt.scale_results.items()},
    }


def execute_blinded_fit(adapter: A.RelationalQualificationAdapterReceipt) -> BlindedFitReceipt:
    if not isinstance(adapter, A.RelationalQualificationAdapterReceipt):
        raise QualificationRunnerError("adapter must be a RelationalQualificationAdapterReceipt")
    if adapter.status != "READY":
        raise QualificationRunnerError("external qualification adapter is not READY")
    if adapter.missing_capabilities:
        raise QualificationRunnerError("READY adapter cannot contain missing capabilities")
    if adapter.controller_challenges.keys() != adapter.fit_inputs.keys():
        raise QualificationRunnerError("fit/controller opaque challenge sets differ")

    profiles: dict[str, G.RelationalProfileReceipt] = {}
    controls: dict[str, dict[str, G.RelationalProfileReceipt]] = {}
    for challenge_id, fit in adapter.fit_inputs.items():
        if not isinstance(fit, Mapping):
            raise QualificationRunnerError(f"invalid fit input: {challenge_id}")
        control_profiles = fit.get("control_profiles")
        if not isinstance(control_profiles, Mapping):
            raise QualificationRunnerError(f"control_profiles missing from fit input: {challenge_id}")

        context = X.prepare_observed_relational_context(
            source=fit["source"],
            panel_id=fit["panel_id"],
            z_values=fit["z_values"],
            x_values=fit["x_values"],
            y_values=fit["y_values"],
            z_measured=fit["z_measured"],
            x_measured=fit["x_measured"],
            y_measured=fit["y_measured"],
            z_feature_ids=fit["z_feature_ids"],
            x_feature_ids=fit["x_feature_ids"],
            y_feature_ids=fit["y_feature_ids"],
            donor_ids=fit["donor_ids"],
            operator_ids=fit["operator_ids"],
            global_rows=fit["global_rows"],
            source_library=fit["source_library"],
            detected_genes=fit["detected_genes"],
        )
        profiles[challenge_id] = X.evaluate_prepared_relational_profile(
            context,
            profile_id=fit["profile_id"],
            focal_mask=fit["focal_mask"],
            neighbor_pool_mask=fit["neighbor_pool_mask"],
            min_focal_anchors_per_donor=fit["min_focal_anchors_per_donor"],
        )
        local_controls: dict[str, G.RelationalProfileReceipt] = {}
        for control_id, control in control_profiles.items():
            if not isinstance(control, Mapping):
                raise QualificationRunnerError(f"invalid opaque control profile: {challenge_id}/{control_id}")
            local_controls[control_id] = X.evaluate_prepared_relational_profile(
                context,
                profile_id=f"{challenge_id}::{control_id}",
                focal_mask=control["focal_mask"],
                neighbor_pool_mask=control["neighbor_pool_mask"],
                min_focal_anchors_per_donor=control["min_focal_anchors_per_donor"],
            )
        controls[challenge_id] = local_controls

    return BlindedFitReceipt(
        package_id=adapter.package_id,
        package_sha256=adapter.package_sha256,
        profiles=profiles,
        controls=controls,
        authority={key: False for key in sorted(RUN_AUTHORITY_KEYS)},
    )


def _validate_controller_manifest(package: P.ValidatedExternalPackage, manifest: Mapping) -> Mapping[str, Mapping]:
    if not isinstance(manifest, Mapping):
        raise QualificationRunnerError("controller manifest must be a mapping")
    if set(manifest) != {"schema", "package_sha256", "claims", "authority"}:
        raise QualificationRunnerError("controller manifest fields differ from the frozen V1 schema")
    if manifest.get("schema") != CONTROLLER_SCHEMA:
        raise QualificationRunnerError("wrong controller manifest schema")
    if manifest.get("package_sha256") != package.package_sha256:
        raise QualificationRunnerError("controller manifest package SHA-256 mismatch")
    _all_false_authority(manifest.get("authority"), CONTROLLER_AUTHORITY_KEYS, "controller manifest")
    if canonical_sha256(manifest) != package.controller_truth_sha256:
        raise QualificationRunnerError("controller truth hash mismatch")
    claims = manifest.get("claims")
    if not isinstance(claims, Mapping) or set(claims) != set(A.MANDATORY_RELATIONAL_CAPABILITIES):
        raise QualificationRunnerError("controller claims must cover the exact nine relational capabilities")
    return claims


def _validate_gate_binding(gate_binding: Mapping) -> None:
    if not isinstance(gate_binding, Mapping):
        raise QualificationRunnerError("gate_binding must be a mapping")
    for field in _IDENTITY_FIELDS:
        if not _is_sha256(gate_binding.get(field)):
            raise QualificationRunnerError(f"invalid gate identity: {field}")
    if not isinstance(gate_binding.get("failure_scope"), str) or not gate_binding["failure_scope"]:
        raise QualificationRunnerError("gate failure_scope must be a nonempty string")
    capabilities = gate_binding.get("required_capabilities")
    if not isinstance(capabilities, list) or tuple(capabilities) != A.MANDATORY_RELATIONAL_CAPABILITIES:
        raise QualificationRunnerError("gate binding must require the exact nine capabilities in frozen order")


def adjudicate_blinded_qualification(
    *,
    package: P.ValidatedExternalPackage,
    fit_receipt: BlindedFitReceipt,
    controller_manifest: Mapping,
    gate_binding: Mapping,
) -> RelationalQualificationRunReceipt:
    if not isinstance(package, P.ValidatedExternalPackage):
        raise QualificationRunnerError("package must be a ValidatedExternalPackage")
    if not isinstance(fit_receipt, BlindedFitReceipt):
        raise QualificationRunnerError("fit_receipt must be a BlindedFitReceipt")
    if fit_receipt.package_id != package.package_id or fit_receipt.package_sha256 != package.package_sha256:
        raise QualificationRunnerError("fit receipt package identity mismatch")
    _all_false_authority(fit_receipt.authority, RUN_AUTHORITY_KEYS, "blinded fit receipt")
    expected_challenges = {package.capabilities[cap]["challenge_id"] for cap in A.MANDATORY_RELATIONAL_CAPABILITIES}
    if set(fit_receipt.profiles) != expected_challenges or set(fit_receipt.controls) != expected_challenges:
        raise QualificationRunnerError("blinded fit receipt must cover the exact mandatory challenge set")

    claims = _validate_controller_manifest(package, controller_manifest)
    _validate_gate_binding(gate_binding)

    missing: list[str] = []
    rare_receipts: dict[str, G.RareIncrementReceipt] = {}
    capability_statuses: dict[str, str] = {}
    expected_status_by_capability: dict[str, str] = {}
    gate_outputs: dict[str, dict] = {}

    for capability_id in A.MANDATORY_RELATIONAL_CAPABILITIES:
        capability = package.capabilities[capability_id]
        challenge_id = capability["challenge_id"]
        claim = claims[capability_id]
        if not isinstance(claim, Mapping) or set(claim) != {"challenge_id", "control_roles", "expected_status"}:
            raise QualificationRunnerError(f"invalid controller claim shape: {capability_id}")
        if claim.get("challenge_id") != challenge_id:
            raise QualificationRunnerError(f"controller challenge binding mismatch: {capability_id}")
        roles = claim.get("control_roles")
        if not isinstance(roles, Mapping):
            raise QualificationRunnerError(f"control_roles must be a mapping: {capability_id}")

        primary = fit_receipt.profiles[challenge_id]
        rare_increment = None
        if capability_id in RARE_CONTROL_CAPABILITIES:
            selected: dict[str, G.RelationalProfileReceipt] = {}
            for role in MANDATORY_CONTROL_ROLES:
                ids = roles.get(role)
                if not isinstance(ids, list) or not ids:
                    missing.append(f"{capability_id}:{role}")
                    continue
                for control_id in ids:
                    if not isinstance(control_id, str) or not control_id:
                        raise QualificationRunnerError(f"invalid control ID in role {role}: {capability_id}")
                    control = fit_receipt.controls[challenge_id].get(control_id)
                    if control is None:
                        missing.append(f"{capability_id}:{role}:{control_id}")
                    else:
                        selected[f"{role}:{control_id}"] = control
            extra_roles = set(roles) - set(MANDATORY_CONTROL_ROLES)
            if extra_roles:
                raise QualificationRunnerError(f"unknown controller control roles for {capability_id}: {sorted(extra_roles)}")
            if not any(item.startswith(f"{capability_id}:") for item in missing):
                rare_increment = G.adjudicate_rare_increment(primary, selected)
                rare_receipts[capability_id] = rare_increment
        elif roles:
            raise QualificationRunnerError(f"non-rare capability cannot carry rare control roles: {capability_id}")

        expected = claim.get("expected_status")
        if capability_id == "REL_SOURCE_VISIBILITY_STRESS":
            if expected not in _ALLOWED_STATUS:
                raise QualificationRunnerError("source-visibility stress requires controller-only expected status")
            expected_status_by_capability[capability_id] = expected
        elif expected is not None:
            raise QualificationRunnerError(f"only source-visibility stress may carry explicit expected_status: {capability_id}")

        if capability_id in RARE_CONTROL_CAPABILITIES and rare_increment is None:
            continue
        reduced = R.reduce_capability_status(capability_id, primary, rare_increment=rare_increment)
        capability_statuses[capability_id] = reduced
        evidence = {
            "capability_id": capability_id,
            "challenge_id": challenge_id,
            "reduced_status": reduced,
            "profile": _profile_summary(primary),
            "rare_increment": _rare_summary(rare_increment),
        }
        gate_outputs[challenge_id] = {
            "qualified_gate_executor_sha256": gate_binding["qualified_gate_executor_sha256"],
            "estimand_sha256": gate_binding["estimand_sha256"],
            "decision_rule_sha256": gate_binding["decision_rule_sha256"],
            "status": reduced,
            "evidence_payload_sha256": canonical_sha256(evidence),
            "raw_sufficient_statistics": evidence,
        }

    if missing:
        return RelationalQualificationRunReceipt(
            status="INCOMPLETE",
            package_id=package.package_id,
            package_sha256=package.package_sha256,
            capability_statuses=capability_statuses,
            rare_increment_receipts=rare_receipts,
            gate_qualification=None,
            missing_requirements=tuple(sorted(set(missing))),
            authority={key: False for key in sorted(RUN_AUTHORITY_KEYS)},
        )

    try:
        gate_qualification = T.adjudicate_gate_qualification(
            candidate_id="C2_RELATIONAL_SHARED",
            gate_id="R_RELATIONAL_SUCCESSOR_TEST_OF_TEST_V1",
            gate_binding=gate_binding,
            package=package,
            gate_outputs=gate_outputs,
            expected_status_by_capability=expected_status_by_capability,
        )
    except T.GateQualificationError as exc:
        raise QualificationRunnerError(str(exc)) from exc

    return RelationalQualificationRunReceipt(
        status=gate_qualification.qualification_status,
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        capability_statuses=capability_statuses,
        rare_increment_receipts=rare_receipts,
        gate_qualification=gate_qualification,
        missing_requirements=tuple(),
        authority={key: False for key in sorted(RUN_AUTHORITY_KEYS)},
    )
