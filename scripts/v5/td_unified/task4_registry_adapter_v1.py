"""Task 4 adapter over the frozen Task 3 registry facade.

This module never promotes a registry unit.  It provides validation and
non-authorizing diagnostics for Task 4 consumers while keeping the frozen Task
0-3 implementation unchanged.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Mapping

from . import registry_v1 as registry
from .authority_v1 import ActiveLineageStatus, AuthorityError, AuthorityRecord, QualificationStage, validate_authority_record


class Task4RegistryAdapterError(ValueError):
    pass


def _enum(enum_type, value):
    if isinstance(value, enum_type):
        return value
    return enum_type(value)


def build_validated_registry_unit(payload: Mapping[str, object]):
    """Construct a RegistryUnit only after applying frozen Task 1 authority law."""
    try:
        stage = _enum(QualificationStage, payload["qualification_stage"])
        lineage = _enum(ActiveLineageStatus, payload.get("active_lineage_status", "ACTIVE"))
        restrictions = tuple(payload.get("authority_restrictions", ()))
        record = AuthorityRecord(
            unit_id=str(payload["unit_id"]),
            qualification_stage=stage,
            active_lineage_status=lineage,
            authority_scope=str(payload["authority_scope"]),
            authority_restrictions=restrictions,
        )
        validate_authority_record(record)
    except (KeyError, ValueError, TypeError, AuthorityError) as exc:
        raise Task4RegistryAdapterError(f"RegistryUnit violates frozen Task 1 authority law: {exc}") from exc

    kwargs = dict(payload)
    kwargs.pop("object_role", None)
    kwargs["qualification_stage"] = stage
    kwargs["active_lineage_status"] = lineage
    kwargs["authority_restrictions"] = restrictions
    try:
        return registry.RegistryUnit(**kwargs)
    except Exception as exc:
        raise Task4RegistryAdapterError(f"invalid current RegistryUnit payload: {exc}") from exc


def walk_authority_prerequisite_units(registry_snapshot, unit_id: str, gate: str) -> tuple[str, ...]:
    if unit_id not in registry_snapshot.units_by_id():
        raise Task4RegistryAdapterError(f"unknown unit_id: {unit_id}")
    reachable = {unit_id}
    changed = True
    while changed:
        changed = False
        for p in registry_snapshot.prerequisites:
            if p.gate == gate and p.dependent_unit_id in reachable and p.prerequisite_unit_id not in reachable:
                reachable.add(p.prerequisite_unit_id)
                changed = True
    return tuple(sorted(reachable))


def validate_registry_snapshot_for_task4(
    registry_snapshot,
    *,
    history_custody,
    authority_object_resolver=None,
    dependency_verifier=None,
) -> None:
    if not isinstance(history_custody, registry.RegistryHistoryCustody):
        raise Task4RegistryAdapterError("Task 4 registry snapshot requires current Task 3 history custody")
    try:
        history_custody.validate_current(registry_snapshot)
    except Exception as exc:
        raise Task4RegistryAdapterError(f"Task 3 history custody validation failed: {exc}") from exc


def _task4_python_files(path: Path):
    if path.is_file():
        yield path
        return
    if not path.exists():
        return
    for candidate in path.rglob("*.py"):
        name = candidate.name
        if name.startswith("task4_") or name.startswith("challenge_custody_v1"):
            yield candidate


def assert_no_legacy_registry_dependency(paths: tuple[Path, ...]) -> None:
    """Reject direct/indirect Task 4 imports of the historical registry module."""
    for root in paths:
        for path in _task4_python_files(Path(root)):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except OSError as exc:
                raise Task4RegistryAdapterError(f"cannot inspect Task 4 import surface: {path}") from exc
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""] + [a.name for a in node.names]
                else:
                    continue
                if any("registry_v1_legacy" in name for name in names):
                    raise Task4RegistryAdapterError(f"Task 4 legacy registry dependency forbidden: {path}")


def diagnostic_real_reference_ready(unit_id, registry_snapshot, **kwargs) -> Mapping[str, object]:
    """Return readiness mechanics with an explicit zero-authority label."""
    ready = False
    reason = "UNAVAILABLE"
    if unit_id is not None and registry_snapshot is not None:
        try:
            ready = bool(registry.derive_real_reference_ready(unit_id, registry_snapshot, **kwargs))
            reason = "DERIVED"
        except Exception as exc:
            reason = type(exc).__name__
    return {"ready": ready, "reason": reason, "authority_effect": "NONE"}
