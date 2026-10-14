"""Immutable scientific handoff from authenticated TD to downstream certification."""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping

from scripts.v5 import td_execution_manifest_v1 as M


class TargetBundleError(ValueError):
    pass


_POLICY_KEYS = {
    "canonical_addresses_sha256",
    "support_estimability_map_sha256",
    "evidence_right_ladder_sha256",
    "required_source_strata_sha256",
    "falsifier_policy_sha256",
    "nuisance_baseline_policy_sha256",
    "uncertainty_reference_policy_sha256",
    "relational_semantics_sha256",
    "observation_operator_contract_sha256",
}
_GATE_STATUSES = {"PASS", "FAIL", "NOT_ESTIMABLE", "NUMERICAL_FAILURE"}
_SELECTED_TERMINALS = {
    "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY",
}
_NONE_TERMINALS = {
    "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION",
    "FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY",
    "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY",
    "NUMERICAL_FAILURE__REPAIR_BEFORE_TD_ROUTING__NO_TARGET_AUTHORITY",
}
_AUTHORITY = {
    "target_selection": False,
    "representation_selection": False,
    "td60": False,
    "stage4": False,
    "real_training": False,
}


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _exact_nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\0" in value:
        raise TargetBundleError(f"{label} must be an exact nonempty trimmed NUL-free string")
    return value


def _validate_selection_terminal(selection: object, terminal: object) -> None:
    if selection == "SELECTED":
        if terminal not in _SELECTED_TERMINALS:
            raise TargetBundleError("SELECTED tournament selection is incoherent with tournament terminal")
    elif selection == "NONE":
        if terminal not in _NONE_TERMINALS:
            raise TargetBundleError("NONE tournament selection is incoherent with tournament terminal")
    else:
        raise TargetBundleError("tournament selection must be NONE or SELECTED")


def _canonical_payload(bundle: Mapping[str, object]) -> dict:
    payload = copy.deepcopy(dict(bundle))
    payload.pop("bundle_sha256", None)
    return payload


def compute_bundle_sha256(bundle: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _canonical_payload(bundle), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_policy_identities(policy_identities: Mapping[str, object]) -> dict:
    if not isinstance(policy_identities, Mapping) or set(policy_identities) != _POLICY_KEYS:
        raise TargetBundleError("policy identity set must exactly match frozen Target Qualification Bundle contract")
    for key, value in policy_identities.items():
        if not _is_sha256(value):
            raise TargetBundleError(f"policy identity must be exact SHA-256: {key}")
    return copy.deepcopy(dict(policy_identities))


def _validate_manifest(manifest: Mapping[str, object]) -> dict:
    try:
        return M.validate_execution_manifest(manifest)
    except M.ManifestError as exc:
        raise TargetBundleError(f"execution manifest authentication failed: {exc}") from exc


def _validate_gate_receipts(gate_receipts: Mapping[str, object], expected_gates: set[str]) -> dict:
    if not isinstance(gate_receipts, Mapping) or set(gate_receipts) != expected_gates:
        raise TargetBundleError("gate receipt set must exactly match execution manifest gate set")
    out = {}
    for gate_id, receipt in gate_receipts.items():
        if not isinstance(receipt, Mapping) or set(receipt) != {"gate_id", "status", "receipt_sha256"}:
            raise TargetBundleError(f"gate receipt malformed: {gate_id}")
        if receipt.get("gate_id") != gate_id or receipt.get("status") not in _GATE_STATUSES or not _is_sha256(receipt.get("receipt_sha256")):
            raise TargetBundleError(f"gate receipt identity/status invalid: {gate_id}")
        out[gate_id] = copy.deepcopy(dict(receipt))
    return out


def build_target_qualification_bundle(
    *,
    tournament_output: Mapping[str, object],
    execution_manifest: Mapping[str, object],
    gate_receipts: Mapping[str, object],
    policy_identities: Mapping[str, object],
    canonical_addresses: list[str],
    known_limitations: list[str],
) -> dict:
    if not isinstance(tournament_output, Mapping) or tournament_output.get("schema") != "JEPA_TD_AUTHENTICATED_TOURNAMENT_OUTPUT_V1":
        raise TargetBundleError("authenticated tournament output schema mismatch")
    selection = tournament_output.get("selection")
    terminal = _exact_nonempty(tournament_output.get("terminal"), "tournament terminal")
    _validate_selection_terminal(selection, terminal)
    if not _is_sha256(tournament_output.get("receipt_sha256")):
        raise TargetBundleError("tournament output receipt digest invalid")

    selected = tournament_output.get("candidate_id")
    if selection == "NONE":
        if selected is not None:
            raise TargetBundleError("NONE selection must have null candidate identity")
    else:
        if not isinstance(selected, str) or not selected or selected != selected.strip():
            raise TargetBundleError("selected target requires exact nonempty candidate identity")

    if not isinstance(canonical_addresses, list) or any(
        not isinstance(value, str) or not value or value != value.strip() for value in canonical_addresses
    ):
        raise TargetBundleError("canonical_addresses must be an exact string list")
    if len(canonical_addresses) != len(set(canonical_addresses)):
        raise TargetBundleError("canonical_addresses must be unique")
    if selection == "SELECTED" and not canonical_addresses:
        raise TargetBundleError("selected target requires canonical addresses")
    if selection == "NONE" and canonical_addresses:
        raise TargetBundleError("NONE selection cannot carry selected-target addresses")

    if not isinstance(known_limitations, list) or not known_limitations or any(
        not isinstance(value, str) or not value or value != value.strip() for value in known_limitations
    ):
        raise TargetBundleError("known limitations are mandatory and must be explicit")

    manifest = _validate_manifest(execution_manifest)
    receipts = _validate_gate_receipts(gate_receipts, set(manifest["gates"]))
    policies = _validate_policy_identities(policy_identities)

    bundle = {
        "schema": "JEPA_TD_TARGET_QUALIFICATION_BUNDLE_V1",
        "selection": selection,
        "selected_candidate": selected,
        "tournament_terminal": terminal,
        "canonical_addresses": list(canonical_addresses),
        "execution_mode": manifest["mode"],
        "registry_sha256": manifest["registry_sha256"],
        "execution_manifest": manifest,
        "tournament_receipt_sha256": tournament_output["receipt_sha256"],
        "gate_receipts": receipts,
        "policy_identities": policies,
        "known_limitations": list(known_limitations),
        "downstream_human_eligible": bool(manifest["mode"] == "HUMAN_TD" and selection == "SELECTED"),
        "authority": dict(_AUTHORITY),
    }
    bundle["bundle_sha256"] = compute_bundle_sha256(bundle)
    return validate_target_qualification_bundle(bundle)


def validate_target_qualification_bundle(bundle: Mapping[str, object]) -> dict:
    if not isinstance(bundle, Mapping) or bundle.get("schema") != "JEPA_TD_TARGET_QUALIFICATION_BUNDLE_V1":
        raise TargetBundleError("target qualification bundle schema mismatch")
    digest = bundle.get("bundle_sha256")
    if not _is_sha256(digest) or compute_bundle_sha256(bundle) != digest:
        raise TargetBundleError("target qualification bundle digest mismatch")
    terminal = _exact_nonempty(bundle.get("tournament_terminal"), "tournament terminal")
    selection = bundle.get("selection")
    _validate_selection_terminal(selection, terminal)
    selected = bundle.get("selected_candidate")
    addresses = bundle.get("canonical_addresses")
    if selection == "NONE":
        if selected is not None or addresses != []:
            raise TargetBundleError("NONE bundle cannot carry selected candidate or target addresses")
    else:
        if not isinstance(selected, str) or not selected or not isinstance(addresses, list) or not addresses:
            raise TargetBundleError("SELECTED bundle requires candidate identity and target addresses")

    manifest = _validate_manifest(bundle.get("execution_manifest"))
    if bundle.get("execution_mode") != manifest["mode"] or bundle.get("registry_sha256") != manifest["registry_sha256"]:
        raise TargetBundleError("target qualification bundle manifest binding mismatch")
    _validate_gate_receipts(bundle.get("gate_receipts"), set(manifest["gates"]))
    _validate_policy_identities(bundle.get("policy_identities"))
    if not isinstance(bundle.get("known_limitations"), list) or not bundle["known_limitations"]:
        raise TargetBundleError("target qualification bundle limitations missing")
    authority = bundle.get("authority")
    if not isinstance(authority, Mapping) or set(authority) != set(_AUTHORITY) or any(value is not False for value in authority.values()):
        raise TargetBundleError("target qualification bundle authority must remain closed")
    expected_human = bool(manifest["mode"] == "HUMAN_TD" and selection == "SELECTED")
    if bundle.get("downstream_human_eligible") is not expected_human:
        raise TargetBundleError("downstream human eligibility is incoherent with manifest mode and target selection")
    return copy.deepcopy(dict(bundle))
