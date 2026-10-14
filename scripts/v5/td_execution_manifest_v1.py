"""Freeze one exact approved TD gate set for synthetic rehearsal or human TD.

The manifest contains custody and readiness identities only. It does not execute
biology, choose targets, or grant downstream/training authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Mapping

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


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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

    return {
        "schema": "JEPA_TD_EXECUTION_MANIFEST_V1",
        "mode": mode,
        "registry_sha256": _canonical_sha256(validated),
        "gates": selected,
        "authority": dict(_AUTHORITY),
    }
