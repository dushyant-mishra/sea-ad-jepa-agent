"""Freeze one exact approved TD gate set for synthetic rehearsal or human TD.

The manifest contains custody and readiness identities only. It does not execute
biology, choose targets, or grant downstream/training authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping

from scripts.v5 import td_qualification_registry_v1 as R


class ManifestError(ValueError):
    pass


_ALLOWED_MODES = {"SYNTHETIC_REHEARSAL", "HUMAN_TD"}
_AUTHORITY = {
    "target_selection": False,
    "representation_selection": False,
    "td60": False,
    "stage4": False,
    "real_training": False,
}
_REQUIRED_GATE_KEYS = {
    "lifecycle_state",
    "executor",
    "producer",
    "metric",
    "support_universe",
    "statistical_law",
    "required_real_artifacts",
    "synthetic_qualification",
}


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_hex(value: object, n: int) -> bool:
    return isinstance(value, str) and len(value) == n and all(ch in "0123456789abcdef" for ch in value)


def _manifest_payload(manifest: Mapping[str, object]) -> dict:
    payload = copy.deepcopy(dict(manifest))
    payload.pop("manifest_sha256", None)
    return payload


def compute_manifest_sha256(manifest: Mapping[str, object]) -> str:
    return _canonical_sha256(_manifest_payload(manifest))


def validate_execution_manifest(manifest: Mapping[str, object]) -> dict:
    if not isinstance(manifest, Mapping):
        raise ManifestError("execution manifest must be a mapping")
    expected_keys = {"schema", "mode", "registry_sha256", "gates", "authority", "manifest_sha256"}
    if set(manifest) != expected_keys:
        raise ManifestError("execution manifest keys do not match frozen V1 schema")
    if manifest.get("schema") != "JEPA_TD_EXECUTION_MANIFEST_V1":
        raise ManifestError("execution manifest schema mismatch")
    if manifest.get("mode") not in _ALLOWED_MODES:
        raise ManifestError("execution manifest mode invalid")
    if not _is_hex(manifest.get("registry_sha256"), 64):
        raise ManifestError("execution manifest registry digest invalid")
    digest = manifest.get("manifest_sha256")
    if not _is_hex(digest, 64) or compute_manifest_sha256(manifest) != digest:
        raise ManifestError("execution manifest digest mismatch")

    authority = manifest.get("authority")
    if not isinstance(authority, Mapping) or set(authority) != set(_AUTHORITY) or any(v is not False for v in authority.values()):
        raise ManifestError("execution manifest authority must remain closed")

    gates = manifest.get("gates")
    if not isinstance(gates, Mapping) or not gates:
        raise ManifestError("execution manifest gate set missing")
    for gate_id, gate in gates.items():
        if not isinstance(gate_id, str) or not gate_id or not isinstance(gate, Mapping) or set(gate) != _REQUIRED_GATE_KEYS:
            raise ManifestError(f"execution manifest gate entry malformed: {gate_id!r}")
        if gate.get("lifecycle_state") not in R.LIFECYCLE:
            raise ManifestError(f"execution manifest lifecycle state invalid: {gate_id}")
        executor = gate.get("executor")
        if not isinstance(executor, Mapping) or set(executor) != {"commit_sha", "path"}:
            raise ManifestError(f"execution manifest executor identity malformed: {gate_id}")
        if not _is_hex(executor.get("commit_sha"), 40):
            raise ManifestError(f"execution manifest executor commit invalid: {gate_id}")
        if not isinstance(executor.get("path"), str) or not executor["path"].startswith("scripts/v5/"):
            raise ManifestError(f"execution manifest executor path invalid: {gate_id}")
        if not isinstance(gate.get("producer"), Mapping):
            raise ManifestError(f"execution manifest producer contract missing: {gate_id}")
        if not isinstance(gate.get("metric"), Mapping):
            raise ManifestError(f"execution manifest metric contract missing: {gate_id}")
        if not isinstance(gate.get("support_universe"), str) or not gate["support_universe"]:
            raise ManifestError(f"execution manifest support universe missing: {gate_id}")
        if not isinstance(gate.get("statistical_law"), str) or not gate["statistical_law"]:
            raise ManifestError(f"execution manifest statistical law missing: {gate_id}")
        if not isinstance(gate.get("required_real_artifacts"), list):
            raise ManifestError(f"execution manifest real artifact ledger missing: {gate_id}")
        if not isinstance(gate.get("synthetic_qualification"), Mapping):
            raise ManifestError(f"execution manifest synthetic qualification missing: {gate_id}")

    return copy.deepcopy(dict(manifest))


def build_execution_manifest(
    registry: Mapping[str, object], *, mode: str, requested_gates: list[str]
) -> dict:
    if mode not in _ALLOWED_MODES:
        raise ManifestError(f"invalid execution mode: {mode!r}")
    validated = R.validate_registry(registry)
    gates = validated["gates"]

    if not isinstance(requested_gates, list) or not requested_gates:
        raise ManifestError("requested_gates must be a nonempty list")
    if len(requested_gates) != len(set(requested_gates)):
        raise ManifestError("requested_gates must not contain duplicates")
    unknown = [gate_id for gate_id in requested_gates if gate_id not in gates]
    if unknown:
        raise ManifestError(f"unknown requested gate(s): {unknown}")

    selected: dict[str, dict] = {}
    min_synthetic = R.LIFECYCLE.index("SYNTHETIC_KNOWN_TRUTH_QUALIFIED")
    for gate_id in requested_gates:
        gate = gates[gate_id]
        state = gate["lifecycle_state"]
        if mode == "SYNTHETIC_REHEARSAL":
            if R.LIFECYCLE.index(state) < min_synthetic:
                raise ManifestError(
                    f"gate not eligible for synthetic rehearsal: {gate_id}: {state}"
                )
        else:
            readiness = R.human_readiness(gate)
            if state != "HUMAN_EXECUTABLE" or not readiness["ready"]:
                raise ManifestError(
                    f"gate blocked for human TD: {gate_id}: state={state}: blockers={readiness['blockers']}"
                )

        selected[gate_id] = {
            "lifecycle_state": state,
            "executor": copy.deepcopy(gate["executor"]),
            "producer": copy.deepcopy(gate["producer"]),
            "metric": copy.deepcopy(gate["metric"]),
            "support_universe": gate["support_universe"],
            "statistical_law": gate["statistical_law"],
            "required_real_artifacts": copy.deepcopy(gate["required_real_artifacts"]),
            "synthetic_qualification": copy.deepcopy(gate["synthetic_qualification"]),
        }

    manifest = {
        "schema": "JEPA_TD_EXECUTION_MANIFEST_V1",
        "mode": mode,
        "registry_sha256": _canonical_sha256(validated),
        "gates": selected,
        "authority": dict(_AUTHORITY),
    }
    manifest["manifest_sha256"] = compute_manifest_sha256(manifest)
    return validate_execution_manifest(manifest)
