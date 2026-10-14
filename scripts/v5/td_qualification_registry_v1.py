"""Machine-readable qualification registry for TD producer/executor custody."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Mapping


class RegistryError(ValueError):
    pass


LIFECYCLE = (
    "SEMANTICS_ONLY",
    "FIXTURE_SAME_INTERFACE",
    "SAME_CODE_PATH",
    "SYNTHETIC_KNOWN_TRUTH_QUALIFIED",
    "REAL_REFERENCE_READY",
    "HUMAN_EXECUTABLE",
)

_EXPECTED_GATES = {"R1", "G2", "G6", "G7", "G8", "G9_S1_S2", "R4_C6_C4"}
_AUTHORITY_KEYS = {"target_selection", "representation_selection", "td60", "stage4", "real_training"}
_PRODUCER_STATUS = {"NOT_REQUIRED", "REQUIRED_UNQUALIFIED", "QUALIFIED"}


def _is_hex(value: object, n: int) -> bool:
    return isinstance(value, str) and len(value) == n and all(ch in "0123456789abcdef" for ch in value)


def _authority_closed(value: object) -> bool:
    return isinstance(value, Mapping) and set(value) == _AUTHORITY_KEYS and all(v is False for v in value.values())


def _default_registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "results" / "target_discovery" / "qualification" / "TD_QUALIFICATION_REGISTRY_V1.json"


def load_registry(path: str | Path | None = None) -> dict:
    target = Path(path) if path is not None else _default_registry_path()
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def human_readiness(gate: Mapping[str, object]) -> dict:
    blockers: list[str] = []
    producer = gate.get("producer")
    if not isinstance(producer, Mapping):
        blockers.append("producer contract missing")
    elif producer.get("status") == "REQUIRED_UNQUALIFIED":
        blockers.append("qualified producer missing")
    elif producer.get("status") == "QUALIFIED":
        code = producer.get("code_identity")
        if not isinstance(code, Mapping) or not _is_hex(code.get("commit_sha"), 40) or not isinstance(code.get("path"), str):
            blockers.append("qualified producer exact code identity missing")

    artifacts = gate.get("required_real_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        blockers.append("required real reference artifacts missing")
    else:
        for artifact in artifacts:
            if not isinstance(artifact, Mapping) or artifact.get("status") != "QUALIFIED":
                aid = artifact.get("id") if isinstance(artifact, Mapping) else "UNKNOWN"
                blockers.append(f"real reference artifact not qualified: {aid}")

    prerequisites = gate.get("open_prerequisites")
    if not isinstance(prerequisites, list):
        blockers.append("open prerequisite ledger missing")
    elif prerequisites:
        blockers.extend(f"open prerequisite: {item}" for item in prerequisites)

    metric = gate.get("metric")
    if not isinstance(metric, Mapping) or not metric.get("id") or not metric.get("orientation"):
        blockers.append("metric contract missing")
    elif any(value == "OPEN" for value in metric.values()):
        blockers.append("metric/statistical contract remains open")

    return {"ready": not blockers, "blockers": blockers}


def validate_registry(registry: Mapping[str, object]) -> dict:
    if not isinstance(registry, Mapping) or registry.get("schema") != "JEPA_TD_QUALIFICATION_REGISTRY_V1":
        raise RegistryError("registry schema mismatch")
    if not _authority_closed(registry.get("authority")):
        raise RegistryError("registry authority must remain closed")

    system = registry.get("system_qualification")
    if not isinstance(system, Mapping):
        raise RegistryError("system qualification receipt missing")
    if system.get("pr") != 369 or system.get("workflow_run_id") != 38577104444 or not _is_hex(system.get("head_sha"), 40):
        raise RegistryError("system qualification identity mismatch")

    gates = registry.get("gates")
    if not isinstance(gates, Mapping) or set(gates) != _EXPECTED_GATES:
        raise RegistryError("registry gate set mismatch")

    for gate_id, gate in gates.items():
        if not isinstance(gate, Mapping) or gate.get("gate_id") != gate_id:
            raise RegistryError(f"gate identity mismatch: {gate_id}")
        state = gate.get("lifecycle_state")
        if state not in LIFECYCLE:
            raise RegistryError(f"invalid lifecycle state: {gate_id}")

        executor = gate.get("executor")
        if not isinstance(executor, Mapping) or set(executor) != {"commit_sha", "path"}:
            raise RegistryError(f"executor identity malformed: {gate_id}")
        if not _is_hex(executor.get("commit_sha"), 40):
            raise RegistryError(f"executor commit must be immutable 40-hex SHA: {gate_id}")
        path = executor.get("path")
        if not isinstance(path, str) or not path.startswith("scripts/v5/"):
            raise RegistryError(f"executor path invalid: {gate_id}")

        producer = gate.get("producer")
        if not isinstance(producer, Mapping) or producer.get("status") not in _PRODUCER_STATUS:
            raise RegistryError(f"producer status invalid: {gate_id}")
        if producer.get("status") == "QUALIFIED":
            code = producer.get("code_identity")
            if not isinstance(code, Mapping) or not _is_hex(code.get("commit_sha"), 40) or not isinstance(code.get("path"), str):
                raise RegistryError(f"qualified producer code identity invalid: {gate_id}")

        metric = gate.get("metric")
        if not isinstance(metric, Mapping) or not isinstance(metric.get("id"), str) or not isinstance(metric.get("orientation"), str):
            raise RegistryError(f"metric identity malformed: {gate_id}")
        if not isinstance(gate.get("support_universe"), str) or not gate.get("support_universe"):
            raise RegistryError(f"support universe missing: {gate_id}")
        if not isinstance(gate.get("statistical_law"), str) or not gate.get("statistical_law"):
            raise RegistryError(f"statistical law missing: {gate_id}")

        artifacts = gate.get("required_real_artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise RegistryError(f"required real artifacts missing: {gate_id}")
        for artifact in artifacts:
            if not isinstance(artifact, Mapping) or set(artifact) != {"id", "status"} or artifact.get("status") not in {"MISSING", "QUALIFIED"}:
                raise RegistryError(f"real artifact entry malformed: {gate_id}")

        challenges = gate.get("required_challenge_families")
        if not isinstance(challenges, list) or not challenges or len(challenges) != len(set(challenges)):
            raise RegistryError(f"challenge family contract malformed: {gate_id}")

        sq = gate.get("synthetic_qualification")
        if not isinstance(sq, Mapping):
            raise RegistryError(f"synthetic qualification missing: {gate_id}")
        if (
            sq.get("system_pr") != 369
            or sq.get("system_head_sha") != "651d7a5a1d4f4047d5ac875cc603f9151c2fed36"
            or sq.get("workflow_run_id") != 38577104444
            or sq.get("status") != "PASS_SYSTEM_MECHANICS_FIREWALLS"
        ):
            raise RegistryError(f"synthetic qualification exact receipt mismatch: {gate_id}")

        if not isinstance(gate.get("open_prerequisites"), list):
            raise RegistryError(f"open prerequisites malformed: {gate_id}")
        if not _authority_closed(gate.get("authority")):
            raise RegistryError(f"gate authority must remain closed: {gate_id}")

        readiness = human_readiness(gate)
        if state == "HUMAN_EXECUTABLE" and not readiness["ready"]:
            raise RegistryError(f"human executable lifecycle has unresolved blockers: {gate_id}: {readiness['blockers']}")
        state_index = LIFECYCLE.index(state)
        if state_index >= LIFECYCLE.index("REAL_REFERENCE_READY"):
            unresolved_refs = [a for a in artifacts if a.get("status") != "QUALIFIED"]
            if unresolved_refs:
                raise RegistryError(f"real-reference-ready lifecycle has missing references: {gate_id}")

    return copy.deepcopy(dict(registry))


def gate_state(registry: Mapping[str, object], gate_id: str) -> str:
    validated = validate_registry(registry)
    try:
        return validated["gates"][gate_id]["lifecycle_state"]
    except KeyError as exc:
        raise RegistryError(f"unknown gate_id: {gate_id}") from exc
