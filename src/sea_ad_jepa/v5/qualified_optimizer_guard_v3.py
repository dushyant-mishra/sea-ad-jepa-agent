"""Current optimizer guard V3 bound to V2 receipt plus explicit training authority."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .current_teacher_target_receipt_v2 import validate_current_teacher_target_receipt_v2
from .current_training_authority_v1 import CurrentTrainingAuthorityV1

STOP = "STOP_V5_CURRENT_OPTIMIZER_V3_AUTHORITY_NOT_ARMED"
CURSOR_KWARG = "v5_current_guard_schedule_cursor"


def _cursor(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("schedule_cursor must be a nonnegative integer")
    return value


@dataclass
class CurrentOptimizerStepGuardV3:
    optimizer: Any
    receipt: Mapping[str, Any]
    training_authority: CurrentTrainingAuthorityV1
    expected_target_package_root: str
    expected_authority_roots: Mapping[str, str]
    expected_closure_v2_sha256: str

    def __post_init__(self) -> None:
        self.training_authority.validate()
        verified = validate_current_teacher_target_receipt_v2(
            self.receipt,
            expected_target_package_root=self.expected_target_package_root,
            expected_authority_roots=self.expected_authority_roots,
            expected_closure_v2_sha256=self.expected_closure_v2_sha256,
        )
        if self.training_authority.receipt_v2_sha256 != verified["receipt_digest"]:
            raise ValueError("training authority receipt root mismatch")
        if self.training_authority.target_package_root != verified["target_package_root"]:
            raise ValueError("training authority target package mismatch")
        if self.training_authority.closure_v2_sha256 != verified["closure_v2_sha256"]:
            raise ValueError("training authority closure root mismatch")
        pre_root = verified["authority_roots"]["preexecution_authority_sha256"]
        if self.training_authority.preexecution_authority_sha256 != pre_root:
            raise ValueError("training authority preexecution root mismatch")
        self._receipt_digest = verified["receipt_digest"]
        self._target_package_root = verified["target_package_root"]
        self._training_authority_digest = self.training_authority.canonical_digest()
        self._armed_cursor = None
        self._consumed_cursor = None
        self._closed = False
        self._pre_handle = self.optimizer.register_step_pre_hook(self._pre_step)
        self._post_handle = self.optimizer.register_step_post_hook(self._post_step)

    @property
    def receipt_digest(self) -> str:
        return self._receipt_digest

    @property
    def training_authority_digest(self) -> str:
        return self._training_authority_digest

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError(f"{STOP}: guard has been closed")

    def _assert_authorities_unchanged(self) -> None:
        try:
            self.training_authority.validate()
            verified = validate_current_teacher_target_receipt_v2(
                self.receipt,
                expected_target_package_root=self.expected_target_package_root,
                expected_authority_roots=self.expected_authority_roots,
                expected_closure_v2_sha256=self.expected_closure_v2_sha256,
            )
        except Exception as exc:
            raise RuntimeError(f"{STOP}: authority chain is no longer valid") from exc
        if verified["receipt_digest"] != self._receipt_digest:
            raise RuntimeError(f"{STOP}: receipt changed after guard installation")
        if self.training_authority.canonical_digest() != self._training_authority_digest:
            raise RuntimeError(f"{STOP}: training authority changed after guard installation")

    def arm_for_step(self, *, schedule_cursor: int) -> dict[str, Any]:
        self._ensure_open()
        self._assert_authorities_unchanged()
        cursor = _cursor(schedule_cursor)
        if self._armed_cursor is not None:
            raise RuntimeError(f"{STOP}: guard is already armed")
        self._armed_cursor = cursor
        self._consumed_cursor = None
        return {
            "armed": True,
            "schedule_cursor": cursor,
            "step_cursor_kwarg": CURSOR_KWARG,
            "target_receipt_digest": self._receipt_digest,
            "training_authority_digest": self._training_authority_digest,
        }

    def disarm_uncompleted_step(self, *, schedule_cursor: int, reason: str) -> dict[str, Any]:
        cursor = _cursor(schedule_cursor)
        if self._armed_cursor != cursor or self._consumed_cursor is not None:
            raise RuntimeError(f"{STOP}: no uncompleted authorization for cursor {cursor}")
        self._armed_cursor = None
        return {"disarmed": True, "schedule_cursor": cursor, "reason": str(reason)}

    def _pre_step(self, optimizer: Any, args: tuple[Any, ...], kwargs: dict[str, Any]):
        self._ensure_open()
        self._assert_authorities_unchanged()
        if optimizer is not self.optimizer:
            self._armed_cursor = None
            raise RuntimeError(f"{STOP}: optimizer identity mismatch")
        if self._armed_cursor is None:
            raise RuntimeError(f"{STOP}: explicit training authority was not armed for this optimizer step")
        supplied = kwargs.pop(CURSOR_KWARG, None)
        if supplied != self._armed_cursor:
            expected = self._armed_cursor
            self._armed_cursor = None
            raise RuntimeError(f"{STOP}: schedule cursor mismatch expected {expected} observed {supplied}")
        if self._consumed_cursor is not None:
            self._armed_cursor = None
            raise RuntimeError(f"{STOP}: authorization already consumed")
        self._consumed_cursor = self._armed_cursor
        return args, kwargs

    def _post_step(self, optimizer: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        self._ensure_open()
        if self._consumed_cursor is None:
            self._armed_cursor = None
            raise RuntimeError(f"{STOP}: optimizer stepped without consuming authorization")
        self._armed_cursor = None

    def assert_step_completed(self, *, schedule_cursor: int) -> dict[str, Any]:
        cursor = _cursor(schedule_cursor)
        if self._consumed_cursor != cursor or self._armed_cursor is not None:
            raise RuntimeError(f"{STOP}: expected guarded optimizer step did not complete")
        return {
            "guarded_optimizer_step": True,
            "schedule_cursor": cursor,
            "target_receipt_digest": self._receipt_digest,
            "target_package_root": self._target_package_root,
            "training_authority_digest": self._training_authority_digest,
        }

    def close(self) -> None:
        if self._closed:
            return
        self._pre_handle.remove()
        self._post_handle.remove()
        self._armed_cursor = None
        self._closed = True


def install_current_optimizer_guard_v3(optimizer: Any, receipt: Mapping[str, Any], *, training_authority: CurrentTrainingAuthorityV1, expected_target_package_root: str, expected_authority_roots: Mapping[str, str], expected_closure_v2_sha256: str) -> CurrentOptimizerStepGuardV3:
    if not isinstance(training_authority, CurrentTrainingAuthorityV1):
        raise ValueError("optimizer V3 requires CurrentTrainingAuthorityV1")
    guard = CurrentOptimizerStepGuardV3(
        optimizer=optimizer,
        receipt=receipt,
        training_authority=training_authority,
        expected_target_package_root=expected_target_package_root,
        expected_authority_roots=expected_authority_roots,
        expected_closure_v2_sha256=expected_closure_v2_sha256,
    )
    existing = getattr(optimizer, "_v5_current_optimizer_guard_v3", None)
    if existing is not None:
        if existing.receipt_digest != guard.receipt_digest or existing.training_authority_digest != guard.training_authority_digest:
            guard.close()
            raise RuntimeError(f"{STOP}: installed guard authority mismatch")
        guard.close()
        existing._assert_authorities_unchanged()
        return existing
    setattr(optimizer, "_v5_current_optimizer_guard_v3", guard)
    return guard
