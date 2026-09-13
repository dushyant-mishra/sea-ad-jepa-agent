"""Fail-closed V5 teacher/student update entrypoint.

The historical V21 46-donor target receipt is retained elsewhere for forensic
and optimizer-guard mechanics replay only.  It is not the dataset-first V5
biological teacher authority.  Until a current V5 teacher-target authority is
established from authenticated FULL104 data, dimensions, schedule/packing,
production-geometry qualification and the bounded base-learning qualification
chain, this public entrypoint must reject the legacy receipt before installing
an optimizer guard or mutating parameters.

No historical V4 production configuration is selected implicitly.  A future
current-V5 authority path must provide its data-derived configuration explicitly.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from sea_ad_jepa.v4.teacher_student_runtime import production_update

from .qualified_optimizer_guard_v1 import (
    CURSOR_KWARG,
    install_qualified_optimizer_guard,
)
from .qualified_teacher_target_receipt_v1 import (
    LEGACY_T0_AUTHORITY_SCOPE,
    validate_qualified_teacher_target_receipt,
)

STOP = "STOP_V5_QUALIFIED_UPDATE_NOT_VALID"
CURRENT_V5_TEACHER_AUTHORITY_REQUIRED = "CURRENT_V5_DATASET_DERIVED_TEACHER_AUTHORITY_REQUIRED"


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def _resolve_observed_target_root(modules: Any, explicit: str | None) -> str:
    observed = explicit
    if observed is None:
        observed = getattr(modules, "qualified_target_package_root", None)
    if not observed:
        _fail("the target package root actually installed on the modules must be bound")
    return str(observed)


class _CursorInjectingScaler:
    """Temporary scaler proxy that presents the schedule cursor to optimizer.step."""

    def __init__(self, scaler: Any, *, optimizer: Any, schedule_cursor: int) -> None:
        self._scaler = scaler
        self._optimizer = optimizer
        self._schedule_cursor = int(schedule_cursor)

    def step(self, optimizer: Any, *args: Any, **kwargs: Any) -> Any:
        if optimizer is self._optimizer:
            kwargs[CURSOR_KWARG] = self._schedule_cursor
        return self._scaler.step(optimizer, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._scaler, name)


def qualified_production_update(
    modules: Any,
    *,
    expression: Any,
    measurement_mask: Any,
    stable_mask_keys: Any,
    schedule_cursor: int,
    target_receipt: Mapping[str, Any],
    expected_target_package_root: str,
    expected_v5_authority_roots: Mapping[str, str],
    observed_target_package_root: str | None = None,
    config: Any | None = None,
    _update_fn: Callable[..., dict[str, Any]] = production_update,
) -> dict[str, Any]:
    """Attempt one bounded V5 update, failing closed without current authority.

    Today the only receipt understood by ``validate_qualified_teacher_target_receipt``
    is the historical T0/V21 receipt.  Validation is still performed so corrupt
    forensic receipts are distinguished from valid-but-legacy receipts, but a
    valid legacy receipt is then quarantined before optimizer-guard installation.

    A future current-V5 teacher authority must be implemented as a distinct,
    dataset-derived authority path rather than widening this legacy schema.
    """
    verified = validate_qualified_teacher_target_receipt(
        target_receipt,
        expected_target_package_root=expected_target_package_root,
        expected_v5_authority_roots=expected_v5_authority_roots,
    )
    if verified.get("authority_scope") == LEGACY_T0_AUTHORITY_SCOPE:
        _fail(
            "legacy T0/V21 target is mechanics-only and cannot authorize a current V5 "
            f"base-learning update; {CURRENT_V5_TEACHER_AUTHORITY_REQUIRED}"
        )
    if verified.get("current_v5_teacher_authority") is not True:
        _fail(CURRENT_V5_TEACHER_AUTHORITY_REQUIRED)
    if config is None:
        _fail("current V5 data-derived runtime config must be supplied explicitly")

    observed_root = _resolve_observed_target_root(modules, observed_target_package_root)
    if observed_root != verified["target_package_root"]:
        _fail("installed target package root does not match the qualified receipt")

    cursor = int(schedule_cursor)
    if cursor < 0:
        raise ValueError("schedule_cursor must be nonnegative")
    if not hasattr(modules, "optimizer"):
        _fail("modules object must expose the optimizer to be guarded")

    guard = install_qualified_optimizer_guard(
        modules.optimizer,
        target_receipt,
        expected_target_package_root,
        expected_v5_authority_roots,
    )
    armed = guard.arm_for_step(schedule_cursor=cursor)
    original_scaler = getattr(modules, "scaler", None)
    proxied_scaler = original_scaler is not None
    if proxied_scaler:
        modules.scaler = _CursorInjectingScaler(
            original_scaler,
            optimizer=modules.optimizer,
            schedule_cursor=cursor,
        )
    try:
        result = _update_fn(
            modules,
            expression=expression,
            measurement_mask=measurement_mask,
            stable_mask_keys=stable_mask_keys,
            schedule_cursor=cursor,
            config=config,
        )
        if not isinstance(result, dict):
            _fail("qualified update function must return a dictionary receipt")
        completed = guard.assert_step_completed(schedule_cursor=cursor)
    except Exception:
        if guard.is_armed:
            guard.disarm_uncompleted_step(
                schedule_cursor=cursor,
                reason="qualified update did not complete",
            )
        raise
    finally:
        if proxied_scaler:
            modules.scaler = original_scaler

    if int(result.get("schedule_cursor", cursor)) != cursor:
        _fail("update receipt schedule cursor mismatch")
    result = dict(result)
    result["qualified_target_authority"] = verified
    result["qualified_optimizer_guard"] = {
        "armed": armed,
        "completed": completed,
        "resident_on_optimizer": True,
    }
    result["production_training_authorized"] = False
    return result
