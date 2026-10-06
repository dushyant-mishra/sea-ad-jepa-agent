"""Fail-closed optimizer-step guard for the inactive V5 mechanics harness.

This module deliberately carries *no* production training authority.  It mirrors
the proven sequencing behavior of the historical V4 optimizer guard so the
current inactive mechanics path cannot regress to an unguarded optimizer step.
It is test/reference machinery only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STOP = "STOP_V5_INACTIVE_REFERENCE_OPTIMIZER_AUTHORITY_NOT_ARMED"
CURSOR_KWARG = "v5_inactive_guard_schedule_cursor"


def _cursor(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("schedule_cursor must be a nonnegative int")
    return value


@dataclass
class InactiveReferenceOptimizerStepGuardV1:
    """Mechanics-only guard; never represents scientific/training permission."""

    optimizer: Any
    mechanics_only: bool = True
    training_authorized: bool = False

    def __post_init__(self) -> None:
        if self.mechanics_only is not True or self.training_authorized is not False:
            raise ValueError("inactive reference guard must remain mechanics-only and non-authorizing")
        self._armed: int | None = None
        self._consumed: int | None = None
        self._last: int | None = None
        self._closed = False
        self._pre = self.optimizer.register_step_pre_hook(self._pre_step)
        self._post = self.optimizer.register_step_post_hook(self._post_step)

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError(f"{STOP}: guard closed")

    def arm_for_step(self, *, schedule_cursor: int) -> dict[str, object]:
        self._ensure_open()
        cursor = _cursor(schedule_cursor)
        if self._armed is not None:
            raise RuntimeError(f"{STOP}: already armed")
        if self._consumed is not None:
            raise RuntimeError(f"{STOP}: prior step unacknowledged")
        if self._last is not None and cursor != self._last + 1:
            raise RuntimeError(
                f"{STOP}: nonsequential cursor expected {self._last + 1} got {cursor}"
            )
        self._armed = cursor
        return {
            "armed": True,
            "schedule_cursor": cursor,
            "step_cursor_kwarg": CURSOR_KWARG,
            "mechanics_only": True,
            "training_authorized": False,
        }

    def disarm_uncompleted_step(self, *, schedule_cursor: int, reason: str) -> dict[str, object]:
        self._ensure_open()
        cursor = _cursor(schedule_cursor)
        if self._armed != cursor or self._consumed is not None:
            raise RuntimeError(f"{STOP}: no uncompleted authorization")
        self._armed = None
        return {
            "disarmed": True,
            "schedule_cursor": cursor,
            "reason": str(reason),
            "training_authorized": False,
        }

    def _pre_step(self, optimizer: Any, args: tuple, kwargs: dict):
        self._ensure_open()
        if optimizer is not self.optimizer:
            raise RuntimeError(f"{STOP}: optimizer identity mismatch")
        if self._armed is None:
            raise RuntimeError(f"{STOP}: authority not armed")
        supplied = kwargs.pop(CURSOR_KWARG, None)
        if supplied != self._armed:
            expected = self._armed
            self._armed = None
            raise RuntimeError(
                f"{STOP}: cursor mismatch expected {expected} observed {supplied}"
            )
        if self._consumed is not None:
            raise RuntimeError(f"{STOP}: authorization replay")
        self._consumed = self._armed
        return args, kwargs

    def _post_step(self, optimizer: Any, args: tuple, kwargs: dict) -> None:
        self._ensure_open()
        if optimizer is not self.optimizer:
            raise RuntimeError(f"{STOP}: optimizer identity mismatch")
        if self._consumed is None:
            self._armed = None
            raise RuntimeError(f"{STOP}: step without consumed authority")
        self._armed = None

    def assert_step_completed(self, *, schedule_cursor: int) -> dict[str, object]:
        self._ensure_open()
        cursor = _cursor(schedule_cursor)
        if self._consumed != cursor or self._armed is not None:
            raise RuntimeError(f"{STOP}: expected guarded step did not complete")
        self._consumed = None
        self._last = cursor
        return {
            "guarded_optimizer_step": True,
            "schedule_cursor": cursor,
            "mechanics_only": True,
            "training_authorized": False,
        }

    def close(self) -> None:
        if not self._closed:
            self._pre.remove()
            self._post.remove()
            self._armed = None
            self._consumed = None
            self._closed = True


def install_inactive_reference_optimizer_guard_v1(
    optimizer: Any,
) -> InactiveReferenceOptimizerStepGuardV1:
    existing = getattr(optimizer, "_v5_inactive_reference_optimizer_guard_v1", None)
    if existing is not None:
        if not isinstance(existing, InactiveReferenceOptimizerStepGuardV1):
            raise RuntimeError(f"{STOP}: incompatible installed guard")
        existing._ensure_open()
        return existing
    guard = InactiveReferenceOptimizerStepGuardV1(optimizer=optimizer)
    setattr(optimizer, "_v5_inactive_reference_optimizer_guard_v1", guard)
    return guard
