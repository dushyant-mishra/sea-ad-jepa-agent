"""Guarded successor for the inactive V5 one-update mechanics harness.

The historical inactive update remains provenance/mechanics code.  This wrapper
routes its optimizer mutation through the same arm -> step -> completion-proof
ordering required by the later qualified optimizer guard, while carrying no
scientific or production training authority.
"""
from __future__ import annotations

from typing import Any

from .inactive_runtime_step_guard_v1 import (
    CURSOR_KWARG,
    InactiveReferenceOptimizerStepGuardV1,
    install_inactive_reference_optimizer_guard_v1,
)
from .inactive_update_reference import V5ReferenceModules, run_inactive_reference_update


def execute_guarded_inactive_optimizer_step(
    optimizer: Any,
    guard: InactiveReferenceOptimizerStepGuardV1,
    *,
    schedule_cursor: int,
) -> dict[str, object]:
    """Perform exactly one mechanics-only optimizer step and prove completion."""
    guard.arm_for_step(schedule_cursor=schedule_cursor)
    try:
        optimizer.step(**{CURSOR_KWARG: schedule_cursor})
    except Exception:
        # If the underlying optimizer failed before consuming the authorization,
        # explicitly clear it.  If it failed after consumption, the guard stays
        # fail-closed and cannot be replayed as a successful step.
        if guard._armed == schedule_cursor and guard._consumed is None:
            guard.disarm_uncompleted_step(
                schedule_cursor=schedule_cursor,
                reason="optimizer step raised before completion",
            )
        raise
    return guard.assert_step_completed(schedule_cursor=schedule_cursor)


class _GuardedOptimizerProxy:
    """Small adapter used only while the inactive reference function executes."""

    def __init__(
        self,
        optimizer: Any,
        guard: InactiveReferenceOptimizerStepGuardV1,
        schedule_cursor: int,
    ) -> None:
        self._optimizer = optimizer
        self._guard = guard
        self._schedule_cursor = schedule_cursor

    @property
    def state(self):
        return self._optimizer.state

    def zero_grad(self, *args, **kwargs):
        return self._optimizer.zero_grad(*args, **kwargs)

    def step(self, *args, **kwargs):
        if args or kwargs:
            raise RuntimeError("inactive guarded proxy owns optimizer-step arguments")
        return execute_guarded_inactive_optimizer_step(
            self._optimizer,
            self._guard,
            schedule_cursor=self._schedule_cursor,
        )


def run_guarded_inactive_reference_update(
    modules: V5ReferenceModules,
    **kwargs: Any,
) -> dict[str, object]:
    """Run the inactive mechanics update with step proof completed before EMA.

    This function does not authorize training.  It only prevents the inactive
    mechanics harness from exercising an unguarded optimizer mutation.
    """
    if "update_index" not in kwargs:
        raise ValueError("update_index is required")
    schedule_cursor = kwargs["update_index"]
    optimizer = modules.optimizer
    guard = install_inactive_reference_optimizer_guard_v1(optimizer)
    proxy = _GuardedOptimizerProxy(optimizer, guard, schedule_cursor)
    modules.optimizer = proxy  # type: ignore[assignment]
    try:
        report = run_inactive_reference_update(modules, **kwargs)
    finally:
        modules.optimizer = optimizer
        guard.close()
        if getattr(optimizer, "_v5_inactive_reference_optimizer_guard_v1", None) is guard:
            delattr(optimizer, "_v5_inactive_reference_optimizer_guard_v1")
    report = dict(report)
    report["guarded_optimizer_step"] = True
    report["guard_kind"] = "INACTIVE_REFERENCE_MECHANICS_ONLY"
    report["training_authorized"] = False
    report["execution_authorized"] = False
    return report
