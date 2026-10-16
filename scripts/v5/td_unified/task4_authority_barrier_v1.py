"""Non-promoting C1-C9 preauthority barrier for Unified Task 4."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class Task4BarrierError(ValueError):
    pass


@dataclass(frozen=True)
class Task4BarrierStatus:
    overall: str
    checks: Mapping[str, str]
    authority_effect: str = "NONE"
    claim_scope: str = "POOLED_DONOR_LEVEL_ONLY"

    def __post_init__(self) -> None:
        if self.authority_effect != "NONE":
            raise Task4BarrierError("Task 4 barrier itself has no promotion authority")
        if self.claim_scope != "POOLED_DONOR_LEVEL_ONLY":
            raise Task4BarrierError("Task 4 must preserve pooled donor-level claim scope")


def require_task4_preauthority_barrier_green(status: Task4BarrierStatus) -> None:
    if not isinstance(status, Task4BarrierStatus):
        raise Task4BarrierError("structured Task4BarrierStatus required")
    if status.authority_effect != "NONE":
        raise Task4BarrierError("preauthority barrier cannot itself grant authority")
    if status.overall != "GREEN":
        raise Task4BarrierError("C1-C9 preauthority barrier is not GREEN")
    bad = {
        key: value
        for key, value in status.checks.items()
        if value not in {"PASS", "GREEN", "CLOSED", "PERSISTENT_EXTERNAL", "AUTHENTICATED_EXTERNAL"}
    }
    if bad:
        raise Task4BarrierError("C1-C9 preauthority barrier contains unresolved checks")


def evaluate_task4_preauthority_barrier(
    unit_id: str,
    registry,
    *,
    custody_store,
    expected_head,
    actor_context,
    authority_object_resolver=None,
    dependency_verifier=None,
    raw_resolver=None,
) -> Task4BarrierStatus:
    """Evaluate current preauthority conditions without calling registry promotion."""
    from .task4_registry_adapter_v1 import validate_registry_snapshot_for_task4

    checks: dict[str, str] = {}
    history_custody = actor_context.get("history_custody") if isinstance(actor_context, Mapping) else None
    try:
        validate_registry_snapshot_for_task4(
            registry,
            history_custody=history_custody,
            authority_object_resolver=authority_object_resolver,
            dependency_verifier=dependency_verifier,
        )
        checks["C3_CURRENT_REGISTRY"] = "PASS"
    except Exception:
        checks["C3_CURRENT_REGISTRY"] = "FAIL"

    try:
        replay = custody_store.replay()
        checks["C1_PERSISTENT_REVOCATION"] = "PERSISTENT_EXTERNAL" if replay.authoritative and replay.head == expected_head else "FAIL"
    except Exception:
        checks["C1_PERSISTENT_REVOCATION"] = "FAIL"

    actor_mode = actor_context.get("actor_attestation_mode") if isinstance(actor_context, Mapping) else None
    checks["C5_ACTOR_CREDENTIALS"] = "AUTHENTICATED_EXTERNAL" if actor_mode == "AUTHENTICATED_EXTERNAL" else "FAIL"
    checks["C6_REVOCATION_ACTOR_POLICY"] = "PASS" if isinstance(actor_context, Mapping) and actor_context.get("revocation_policy_current") is True else "FAIL"
    checks["C7_REQUIREMENT_CLASSES"] = "PASS" if isinstance(actor_context, Mapping) and actor_context.get("requirement_policy_current") is True else "FAIL"
    checks["C8_TASK1_CONSTRUCTION_LAW"] = "PASS" if isinstance(actor_context, Mapping) and actor_context.get("construction_law_current") is True else "FAIL"
    checks["C9_PROCESS_ISOLATION"] = "PASS" if isinstance(actor_context, Mapping) and actor_context.get("process_isolation") == "EXTERNAL_HARNESS" else "FAIL"
    checks["C4_DIAGNOSTIC_ONLY"] = "PASS"
    checks["R5_CLAIM_SCOPE"] = "PASS"

    overall = "GREEN" if all(v in {"PASS", "PERSISTENT_EXTERNAL", "AUTHENTICATED_EXTERNAL"} for v in checks.values()) else "RED"
    return Task4BarrierStatus(overall=overall, checks=checks)
