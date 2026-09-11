"""One-shot optimizer-bound V5 target-authority guard.

The hook is attached directly to the optimizer.  Therefore both AMP
`scaler.step(optimizer)` and a direct `optimizer.step()` encounter the same
fail-closed check immediately before optimizer mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .qualified_teacher_target_receipt_v1 import (
    validate_qualified_teacher_target_receipt,
)

STOP = "STOP_V5_OPTIMIZER_TARGET_AUTHORITY_NOT_ARMED"


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
        self._pre_handle = self.optimizer.register_step_pre_hook(self._pre_step)
        self._post_handle = self.optimizer.register_step_post_hook(self._post_step)

    def arm_for_step(self, *, schedule_cursor: int) -> dict[str, Any]:
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
            "target_receipt_digest": self._verified["receipt_digest"],
        }

    def _pre_step(
        self,
        optimizer: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ):
        if optimizer is not self.optimizer:
            raise RuntimeError(f"{STOP}: optimizer identity mismatch")
        if self._armed_cursor is None:
            raise RuntimeError(
                f"{STOP}: qualified target receipt was not armed for this optimizer step"
            )
        if self._consumed_cursor is not None:
            raise RuntimeError(f"{STOP}: authorization already consumed")
        self._consumed_cursor = self._armed_cursor
        return args, kwargs

    def _post_step(
        self,
        optimizer: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        if self._consumed_cursor is None:
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
        self._pre_handle.remove()
        self._post_handle.remove()
