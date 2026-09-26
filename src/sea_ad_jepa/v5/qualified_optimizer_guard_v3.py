"""Current optimizer guard V3 bound to V2 receipt plus explicit training authority."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .current_teacher_target_receipt_v2 import validate_current_teacher_target_receipt_v2
from .current_training_authority_v1 import CurrentTrainingAuthorityV1, issue_training_authority_v1
from .current_trainer_preexecution_contract_v2 import CurrentTrainerPreexecutionAuthorityV2

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
    closure_v2: Mapping[str, Any]
    preexecution: CurrentTrainerPreexecutionAuthorityV2
    critical_test: Any
    runtime_source: Any
    closure_inputs: Mapping[str, Any]

    def _require_fresh_issuance(self) -> str:
        # A self-consistent public dataclass and matching receipt can be forged.
        # The guard must freshly execute the REAL issuer's full 32-role typed
        # graph validation, not merely inspect the presented token's hashes.
        if not isinstance(self.closure_inputs, Mapping):
            raise ValueError("optimizer V3 requires live closure_inputs")
        if not isinstance(self.preexecution, CurrentTrainerPreexecutionAuthorityV2):
            raise ValueError("optimizer V3 requires current typed preexecution")
        newly_issued = issue_training_authority_v1(
            closure_v2=self.closure_v2,
            preexecution=self.preexecution,
            receipt_v2=self.receipt,
            expected_target_package_root=self.expected_target_package_root,
            critical_test=self.critical_test,
            runtime_source=self.runtime_source,
            closure_inputs=self.closure_inputs,
        )
        presented = self.training_authority.canonical_digest()
        if newly_issued.canonical_digest() != presented:
            raise ValueError("optimizer V3 training authority was not authenticated by live issuance")
        if self.closure_v2["closure_digest"] != self.expected_closure_v2_sha256:
            raise ValueError("optimizer V3 submitted closure differs from expected closure")
        if self.preexecution.canonical_digest() != self.expected_authority_roots["preexecution_authority_sha256"]:
            raise ValueError("optimizer V3 preexecution root differs from receipt")
        return presented

    def __post_init__(self) -> None:
        self._issuer_verified_digest = self._require_fresh_issuance()
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
        # A completed optimizer hook is evidence for exactly one schedule cursor.
        # It must be acknowledged before the next cursor may be armed.
        self._last_asserted_cursor = None
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
            verified_issued_digest = self._require_fresh_issuance()
            verified = validate_current_teacher_target_receipt_v2(
                self.receipt,
                expected_target_package_root=self.expected_target_package_root,
                expected_authority_roots=self.expected_authority_roots,
                expected_closure_v2_sha256=self.expected_closure_v2_sha256,
            )
        except Exception as exc:
            raise RuntimeError(f"{STOP}: authority chain is no longer valid") from exc
        if verified_issued_digest != self._issuer_verified_digest:
            raise RuntimeError(f"{STOP}: live issuer authority changed after guard installation")
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
        if self._consumed_cursor is not None:
            raise RuntimeError(f"{STOP}: previous completed step has not been acknowledged")
        if self._last_asserted_cursor is not None and cursor != self._last_asserted_cursor + 1:
            raise RuntimeError(
                f"{STOP}: nonsequential schedule cursor; "
                f"expected {self._last_asserted_cursor + 1}, got {cursor}"
            )
        self._armed_cursor = cursor
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
        """Consume one post-hook receipt; this alone does NOT prove parameter movement."""
        self._ensure_open()
        cursor = _cursor(schedule_cursor)
        if self._consumed_cursor != cursor or self._armed_cursor is not None:
            raise RuntimeError(f"{STOP}: expected guarded optimizer step did not complete")
        self._consumed_cursor = None
        self._last_asserted_cursor = cursor
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
        self._consumed_cursor = None
        self._closed = True


def install_current_optimizer_guard_v3(
    optimizer: Any,
    receipt: Mapping[str, Any],
    *,
    training_authority: CurrentTrainingAuthorityV1,
    expected_target_package_root: str,
    expected_authority_roots: Mapping[str, str],
    expected_closure_v2_sha256: str,
    closure_v2: Mapping[str, Any] | None = None,
    preexecution: CurrentTrainerPreexecutionAuthorityV2 | None = None,
    critical_test: Any = None,
    runtime_source: Any = None,
    closure_inputs: Mapping[str, Any] | None = None,
) -> CurrentOptimizerStepGuardV3:
    if not isinstance(training_authority, CurrentTrainingAuthorityV1):
        raise ValueError("optimizer V3 requires CurrentTrainingAuthorityV1")
    # Legacy callers fail closed before registering any hooks. No synthetic
    # checksum-only authority may be installed on the production entrypoint.
    if not isinstance(closure_inputs, Mapping):
        raise ValueError("optimizer V3 requires live closure_inputs")
    if not isinstance(closure_v2, Mapping):
        raise ValueError("optimizer V3 requires live closure_v2")
    if not isinstance(preexecution, CurrentTrainerPreexecutionAuthorityV2):
        raise ValueError("optimizer V3 requires current typed preexecution")
    if critical_test is None or runtime_source is None:
        raise ValueError("optimizer V3 requires live critical and runtime authorities")
    existing = getattr(optimizer, "_v5_current_optimizer_guard_v3", None)
    if existing is not None:
        # Refuse a cross-session or caller-spliced live evidence replacement,
        # even if the caller supplies the same digest strings.
        if (
            existing.closure_v2 is not closure_v2
            or existing.closure_inputs is not closure_inputs
            or existing.preexecution is not preexecution
            or existing.critical_test is not critical_test
            or existing.runtime_source is not runtime_source
        ):
            raise ValueError("optimizer V3 live evidence changed since guard installation")
        if (
            existing.receipt_digest != receipt.get("receipt_digest")
            or existing.training_authority_digest != training_authority.canonical_digest()
        ):
            raise ValueError("optimizer V3 installed guard authority mismatch")
        existing._assert_authorities_unchanged()
        return existing
    guard = CurrentOptimizerStepGuardV3(
        optimizer=optimizer,
        receipt=receipt,
        training_authority=training_authority,
        expected_target_package_root=expected_target_package_root,
        expected_authority_roots=expected_authority_roots,
        expected_closure_v2_sha256=expected_closure_v2_sha256,
        closure_v2=closure_v2,
        preexecution=preexecution,
        critical_test=critical_test,
        runtime_source=runtime_source,
        closure_inputs=closure_inputs,
    )
    setattr(optimizer, "_v5_current_optimizer_guard_v3", guard)
    return guard
