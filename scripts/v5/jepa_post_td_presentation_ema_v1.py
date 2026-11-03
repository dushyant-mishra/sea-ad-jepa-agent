from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import re
import sys


MODULE_NAME = "jepa_post_td_harness_contract_v1"
if MODULE_NAME in sys.modules:
    C = sys.modules[MODULE_NAME]
else:
    module_path = Path(__file__).with_name(f"{MODULE_NAME}.py")
    spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    C = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = C
    spec.loader.exec_module(C)


class PresentationEMAError(ValueError):
    pass


_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class PresentationEMAState:
    half_life_presentations: int
    successful_presentations: int = 0
    ema_updates: int = 0

    def __post_init__(self):
        if type(self.half_life_presentations) is not int or self.half_life_presentations <= 0:
            raise PresentationEMAError("EMA half-life presentations must be a positive exact integer")
        if type(self.successful_presentations) is not int or self.successful_presentations < 0:
            raise PresentationEMAError("successful presentation count must be a nonnegative exact integer")
        if type(self.ema_updates) is not int or self.ema_updates < 0:
            raise PresentationEMAError("EMA update count must be a nonnegative exact integer")
        C.ema_momentum_for_presentations(1, self.half_life_presentations)


def validate_restart_binding(*, controller, state: PresentationEMAState) -> dict:
    global_step = getattr(controller, "global_update_step")
    ema_count = getattr(controller, "ema_update_count")
    if (type(global_step) is not int or type(ema_count) is not int
            or type(state) is not PresentationEMAState):
        raise PresentationEMAError("EMA restart counters and state must use exact runtime types")
    if global_step != ema_count or ema_count != state.ema_updates:
        raise PresentationEMAError(
            "EMA restart counter mismatch: "
            f"global_update_step={global_step} controller_ema_updates={ema_count} "
            f"state_ema_updates={state.ema_updates}"
        )
    return {
        "status": "PRESENTATION_EMA_RESTART_BINDING_PASS",
        "global_update_step": global_step,
        "ema_updates": ema_count,
        "successful_presentations": state.successful_presentations,
        "half_life_presentations": state.half_life_presentations,
    }


def advance_after_proved_optimizer_step(
    *,
    controller,
    state: PresentationEMAState,
    successful_presentations: int,
    proved_optimizer_advanced: bool,
) -> tuple[PresentationEMAState, dict]:
    if proved_optimizer_advanced is not True:
        raise PresentationEMAError("presentation EMA requires a proved optimizer step")
    if type(successful_presentations) is not int:
        raise PresentationEMAError("successful presentations must be an exact integer")
    count = successful_presentations
    if count <= 0:
        raise PresentationEMAError("successful presentations for an EMA update must be positive")
    validate_restart_binding(controller=controller, state=state)
    before_global = controller.global_update_step
    before_ema = controller.ema_update_count
    momentum = C.ema_momentum_for_presentations(count, state.half_life_presentations)
    controller.after_successful_optimizer_step(momentum=momentum)
    after_global = controller.global_update_step
    after_ema = controller.ema_update_count
    if type(after_global) is not int or type(after_ema) is not int:
        raise PresentationEMAError("EMA controller counters must remain exact integers")
    if after_global != before_global + 1 or after_ema != before_ema + 1 or after_global != after_ema:
        raise PresentationEMAError(
            "EMA controller did not advance exactly once after the proved optimizer step"
        )
    new_state = PresentationEMAState(
        half_life_presentations=state.half_life_presentations,
        successful_presentations=state.successful_presentations + count,
        ema_updates=state.ema_updates + 1,
    )
    if new_state.ema_updates != after_ema:
        raise PresentationEMAError("presentation EMA state/controller counter mismatch after update")
    return new_state, {
        "schema": "JEPA_POST_TD_PRESENTATION_EMA_UPDATE_V1",
        "native_unit": "SUCCESSFUL_BASE_CELL_PRESENTATIONS",
        "successful_presentations_this_update": count,
        "successful_presentations_total": new_state.successful_presentations,
        "half_life_presentations": new_state.half_life_presentations,
        "momentum": momentum,
        "ema_update_count": new_state.ema_updates,
        "proved_optimizer_advanced": True,
    }


def _validate_sha(value: str, label: str) -> None:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise PresentationEMAError(f"{label} must be lowercase SHA-256")


def build_checkpoint_overlay(
    *,
    base_checkpoint_sha256: str,
    portfolio_sha256: str,
    architecture_sha256: str,
    ema_state: PresentationEMAState,
) -> dict:
    _validate_sha(base_checkpoint_sha256, "base checkpoint SHA-256")
    _validate_sha(portfolio_sha256, "portfolio SHA-256")
    _validate_sha(architecture_sha256, "architecture SHA-256")
    return {
        "schema": "JEPA_POST_TD_CHECKPOINT_OVERLAY_V1",
        "base_checkpoint_sha256": base_checkpoint_sha256,
        "portfolio_sha256": portfolio_sha256,
        "architecture_sha256": architecture_sha256,
        "ema": {
            **asdict(ema_state),
            "native_unit": "SUCCESSFUL_BASE_CELL_PRESENTATIONS",
        },
        "authority": {
            "target_selection_authorized": False,
            "representation_selection_authorized": False,
            "training_authorized": False,
            "continuation_authorized": False,
        },
    }
