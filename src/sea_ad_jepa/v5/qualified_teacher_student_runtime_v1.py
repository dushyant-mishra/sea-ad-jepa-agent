"""V5 qualified teacher/student update entrypoint.

This module is the production-facing bridge between a qualified V21 target receipt
and the historical v4 teacher/student runtime. It does not authorize training;
production_training_authorized remains false. It only makes bounded qualification
updates fail closed unless the optimizer has a resident deny-by-default guard and
that guard is armed by the exact 46-donor target receipt immediately before the
parameter-mutation boundary.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from sea_ad_jepa.v4.teacher_student_runtime import PRODUCTION_CONFIG, production_update

from .qualified_optimizer_guard_v1 import (
    CURSOR_KWARG,
    install_qualified_optimizer_guard,
)
from .qualified_teacher_target_receipt_v1 import validate_qualified_teacher_target_receipt

STOP = "STOP_V5_QUALIFIED_UPDATE_NOT_VALID"


def _fail(message: str) -> None:
    raise RuntimeError(f"{STOP}: {message}")


def _resolve_observed_target_root(modules: Any, explicit: str | None) -> str:
    """Return the target root actually installed on ``modules``.

    The module-bound value is authoritative. ``explicit`` is retained only as a
    compatibility witness: when supplied it must agree with the installed value
    and can never substitute for a missing or different installed root.
    """
    installed = getattr(modules, "qualified_target_package_root", None)
    if not installed:
        _fail("the target package root actually installed on the modules must be bound")
    installed = str(installed)
    if explicit is not None and str(explicit) != installed:
        _fail("caller-observed target package root does not match the installed target package root")
    return installed


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
    config: Any = PRODUCTION_CONFIG,
    _update_fn: Callable[..., dict[str, Any]] = production_update,
) -> dict[str, Any]:
    """Run one bounded-qualification update with a resident optimizer guard.

    The guard is installed directly on `modules.optimizer` and is intentionally
    left installed after this function returns. Subsequent direct optimizer calls
    therefore fail closed unless a future qualified call arms the same resident
    guard and presents the matching schedule cursor at step time. AMP calls are
    supported by temporarily proxying `modules.scaler.step(...)` so the cursor is
    passed to `optimizer.step(...)` and removed by the guard before the optimizer
    implementation sees it.
    """
    verified = validate_qualified_teacher_target_receipt(
        target_receipt,
        expected_target_package_root=expected_target_package_root,
        expected_v5_authority_roots=expected_v5_authority_roots,
    )
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
