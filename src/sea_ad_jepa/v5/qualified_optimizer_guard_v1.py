"""Resident optimizer-bound V5 target-authority guard.

The hook is attached directly to the optimizer. Therefore both AMP
`scaler.step(optimizer, ...)` and a direct `optimizer.step(...)` encounter the
same fail-closed check immediately before optimizer mutation. The guard is
intended to remain installed for the optimizer lifetime; closing it is only for
explicit teardown in tests or disposal.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .qualified_teacher_target_receipt_v1 import (
    validate_qualified_teacher_target_receipt,
)

STOP = "STOP_V5_OPTIMIZER_TARGET_AUTHORITY_NOT_ARMED"
CURSOR_KWARG = "v5_guard_schedule_cursor"


@dataclass
class QualifiedOptimizerStepGuard:
    optimizer: Any
    receipt: Mapping[str, Any]
    expected_target_package_root: str
    expected_v5_authority_roots: Mapping[str, str]

    def __post_init__(self) -> None:
        self._verified = validate_qualified_teacher_target_receipt(
            self.receipt,
            expected_target_package_root=self.expected_target_package_root,
            expected_v5_authority_roots=self.expected_v5_authority_roots,
        )
        self._armed_cursor: int | None = None
        self._consumed_cursor: int | None = None
        self._closed = False
        self._pre_handle = self.optimizer.register_step_pre_hook(self._pre_step)
        self._post_handle = self.optimizer.register_step_post_hook(self._post_step)

    @property
    def receipt_digest(self) -> str:
        return self._verified["receipt_digest"]

    @property
    def target_package_root(self) -> str:
        return self._verified["target_package_root"]

    @property
    def is_armed(self) -> bool:
        return self._armed_cursor is not None

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError(f"{STOP}: guard has been closed")

    def arm_for_step(self, *, schedule_cursor: int) -> dict[str, Any]:
        """Arm exactly one optimizer mutation for `schedule_cursor`.

        The cursor must also be presented at optimizer-step time through the
        private keyword named by `CURSOR_KWARG`. This prevents an authorization
        left live by an AMP skipped step from being consumed by a later ordinary
        optimizer step that did not present the current schedule cursor.
        """
        self._ensure_open()
        cursor = int(schedule_cursor)
        if cursor < 0:
            raise ValueError("schedule_cursor must be nonnegative")
        if self._armed_cursor is not None:
            raise RuntimeError(f"{STOP}: guard is already armed")
        self._armed_cursor = cursor
        self._consumed_cursor = None
        return {
            "armed": True,
            "schedule_cursor": cursor,
            "step_cursor_kwarg": CURSOR_KWARG,
            "target_receipt_digest": self._verified["receipt_digest"],
        }

    def disarm_uncompleted_step(self, *, schedule_cursor: int, reason: str) -> dict[str, Any]:
        """Clear an authorization when a step attempt did not call optimizer.step()."""
        cursor = int(schedule_cursor)
        if self._armed_cursor != cursor or self._consumed_cursor is not None:
            raise RuntimeError(f"{STOP}: no uncompleted authorization for cursor {cursor}")
        self._armed_cursor = None
        return {"disarmed": True, "schedule_cursor": cursor, "reason": str(reason)}

    def _pre_step(
        self,
        optimizer: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ):
        self._ensure_open()
        if optimizer is not self.optimizer:
            self._armed_cursor = None
            raise RuntimeError(f"{STOP}: optimizer identity mismatch")
        if self._armed_cursor is None:
            raise RuntimeError(
                f"{STOP}: qualified target receipt was not armed for this optimizer step"
            )
        supplied = kwargs.pop(CURSOR_KWARG, None)
        if supplied != self._armed_cursor:
            expected = self._armed_cursor
            self._armed_cursor = None
            raise RuntimeError(
                f"{STOP}: schedule cursor not presented at optimizer step "
                f"(expected {expected}, observed {supplied})"
            )
        if self._consumed_cursor is not None:
            self._armed_cursor = None
            raise RuntimeError(f"{STOP}: authorization already consumed")
        self._consumed_cursor = self._armed_cursor
        return args, kwargs

    def _post_step(
        self,
        optimizer: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        self._ensure_open()
        if self._consumed_cursor is None:
            self._armed_cursor = None
            raise RuntimeError(
                f"{STOP}: optimizer stepped without consuming authorization"
            )
        self._armed_cursor = None

    def assert_step_completed(self, *, schedule_cursor: int) -> dict[str, Any]:
        cursor = int(schedule_cursor)
        if self._consumed_cursor != cursor or self._armed_cursor is not None:
            raise RuntimeError(
                f"{STOP}: expected guarded optimizer step did not complete"
            )
        return {
            "guarded_optimizer_step": True,
            "schedule_cursor": cursor,
            "target_receipt_digest": self._verified["receipt_digest"],
            "target_package_root": self._verified["target_package_root"],
        }

    def close(self) -> None:
        if self._closed:
            return
        self._pre_handle.remove()
        self._post_handle.remove()
        self._armed_cursor = None
        self._closed = True


def install_qualified_optimizer_guard(
    optimizer: Any,
    receipt: Mapping[str, Any],
    expected_target_package_root: str,
    expected_v5_authority_roots: Mapping[str, str],
) -> QualifiedOptimizerStepGuard:
    """Install or reuse the resident deny-by-default guard on an optimizer."""
    existing = getattr(optimizer, "_v5_qualified_optimizer_guard", None)
    if existing is not None:
        if existing.receipt_digest != validate_qualified_teacher_target_receipt(
            receipt,
            expected_target_package_root=expected_target_package_root,
            expected_v5_authority_roots=expected_v5_authority_roots,
        )["receipt_digest"]:
            raise RuntimeError(f"{STOP}: installed guard receipt mismatch")
        return existing
    guard = QualifiedOptimizerStepGuard(
        optimizer,
        receipt,
        expected_target_package_root,
        expected_v5_authority_roots,
    )
    setattr(optimizer, "_v5_qualified_optimizer_guard", guard)
    return guard
