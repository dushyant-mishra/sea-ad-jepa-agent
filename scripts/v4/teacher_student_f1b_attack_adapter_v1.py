#!/usr/bin/env python3
"""Expose the canonical teacher/student runtime to the frozen F1-B attacks.

Training-critical seams are probed through canonical runtime/movement code.
Non-training diagnostic seams delegate to the already-reviewed C3 successor
helpers instead of being reimplemented a third time.
"""
from __future__ import annotations

from typing import Any, Mapping

import torch

from scripts.v4.f1b_c3_training_successor_v2 import (
    directional_claim,
    enforce_frozen_horizon,
    refit_g5_probe,
    routing_metrics,
    routing_report,
    select_g5_endpoints,
    target_equivalence,
)
from scripts.v4.f1b_successor_attack_suite_v1 import Candidate
from sea_ad_jepa.v4.ema import EMAOptimizerStepController, create_ema_target
from sea_ad_jepa.v4.ipb_jepa import BlockPredictor, IPBEncoder
from sea_ad_jepa.v4.teacher_student_movement import adjudicate_tensor
from sea_ad_jepa.v4.teacher_student_runtime import (
    F1B_ATTACK_AUTHORITY_ROOT,
    FROZEN_BACKBONE_REGISTRY,
    FROZEN_PREDICTOR_REGISTRY,
    TeacherStudentModules,
    enforce_adam_moments,
    enforce_unscaled_gradient_gates,
    production_amp_smoke,
)


def _probe_modules() -> TeacherStudentModules:
    """Small-vocabulary CPU fixture with the exact protected module topology."""
    online = IPBEncoder(
        vocabulary_size=64,
        width=160,
        heads=4,
        blocks=6,
        gradient_checkpointing=False,
    )
    teacher = create_ema_target(online)
    predictor = BlockPredictor(width=160, heads=4)
    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=1e-4,
        weight_decay=0.01,
    )
    scaler = torch.amp.GradScaler("cuda", enabled=False)
    controller = EMAOptimizerStepController(online, teacher)
    return TeacherStudentModules(
        online=online,
        teacher=teacher,
        predictor=predictor,
        optimizer=optimizer,
        scaler=scaler,
        ema_controller=controller,
        device=torch.device("cpu"),
    )


def _set_gradient(parameter: torch.nn.Parameter, value: Any) -> None:
    scalar = float(value)
    parameter.grad = torch.full_like(parameter, scalar)


def _apply_gradient_payload(
    modules: TeacherStudentModules,
    payload: Mapping[str, Any],
) -> None:
    online = dict(modules.online.named_parameters())
    predictor = dict(modules.predictor.named_parameters())
    for name in FROZEN_BACKBONE_REGISTRY:
        _set_gradient(online[name], 1.0)
    for name in FROZEN_PREDICTOR_REGISTRY:
        _set_gradient(predictor[name], 1.0)

    for name, value in dict(payload.get("backbone") or {}).items():
        if name not in online:
            raise RuntimeError(f"unknown backbone probe parameter: {name}")
        _set_gradient(online[name], value)
    for name, value in dict(payload.get("predictor") or {}).items():
        local = str(name).removeprefix("predictor.")
        if local not in predictor:
            raise RuntimeError(f"unknown predictor probe parameter: {name}")
        _set_gradient(predictor[local], value)


def _seed_live_moments(modules: TeacherStudentModules) -> None:
    online = dict(modules.online.named_parameters())
    predictor = dict(modules.predictor.named_parameters())
    for parameter in (
        [online[name] for name in FROZEN_BACKBONE_REGISTRY]
        + [predictor[name] for name in FROZEN_PREDICTOR_REGISTRY]
    ):
        modules.optimizer.state[parameter]["exp_avg"] = torch.ones_like(parameter)
        modules.optimizer.state[parameter]["exp_avg_sq"] = torch.ones_like(parameter)


def gate_mandatory_gradients(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Attack seam backed by the canonical tensor gates and Adam-moment gate."""
    modules = _probe_modules()
    _apply_gradient_payload(modules, payload)
    gradients = enforce_unscaled_gradient_gates(modules)
    _seed_live_moments(modules)

    online = dict(modules.online.named_parameters())
    predictor = dict(modules.predictor.named_parameters())
    for name, fields in dict(payload.get("moments") or {}).items():
        local = str(name).removeprefix("backbone.").removeprefix("predictor.")
        if local in online:
            parameter = online[local]
        elif local in predictor:
            parameter = predictor[local]
        else:
            raise RuntimeError(f"unknown moment probe parameter: {name}")
        state = modules.optimizer.state[parameter]
        for field in ("exp_avg", "exp_avg_sq"):
            if field not in fields:
                state.pop(field, None)
            else:
                state[field] = torch.full_like(parameter, float(fields[field]))

    moments = enforce_adam_moments(modules)
    return {"gradient_gate": gradients, "adam_moments": moments, "passed": True}


def movement_gate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Translate the frozen scalar attack fixture into real production adjudications."""
    relative = dict(payload.get("relative_movement") or {})
    absolute = dict(payload.get("absolute_movement") or {})
    baseline_norm = dict(payload.get("baseline_norm") or {})
    decay = float(payload["decay_only_prediction"])
    failures: list[str] = []
    rows: dict[str, Any] = {}

    for name, rel in relative.items():
        base_value = float(baseline_norm.get(name, 0.0))
        baseline = torch.tensor([base_value], dtype=torch.float64)
        if base_value == 0.0:
            observed = baseline.clone()
            observed[0] = float(absolute.get(name, 0.0))
        else:
            if rel is None:
                raise RuntimeError(f"relative movement absent for nonzero baseline: {name}")
            observed = baseline.clone()
            observed.mul_(1.0 - float(rel))
        row = adjudicate_tensor(
            baseline,
            observed,
            learning_rate=decay,
            weight_decay=1.0,
            valid_steps=1,
        )
        rows[name] = row
        if not row["passed"]:
            failures.append(name)

    if failures:
        raise RuntimeError("canonical movement gate rejected: " + ", ".join(failures))
    return {"passed": True, "rows": rows}


def protected_update(payload: Mapping[str, Any]) -> dict[str, bool]:
    """Prove that the canonical tensor gate precedes an optimizer step."""
    modules = _probe_modules()
    gradient_payload = {"backbone": {}, "predictor": {}}
    for name, value in dict(payload.get("mandatory_gradients") or {}).items():
        local = str(name).removeprefix("backbone.").removeprefix("predictor.")
        if local in FROZEN_PREDICTOR_REGISTRY:
            gradient_payload["predictor"][local] = value
        else:
            gradient_payload["backbone"][local] = value
    _apply_gradient_payload(modules, gradient_payload)
    enforce_unscaled_gradient_gates(modules)

    ledger = payload["ledger"]
    modules.optimizer.step()
    ledger["stepped"] = True
    ledger["optimizer_state_entries"] = len(modules.optimizer.state)
    return {"stepped": True}


def canonical_candidate() -> Candidate:
    return Candidate(
        name="CanonicalTeacherStudentRuntimeV1",
        gate_mandatory_gradients=gate_mandatory_gradients,
        movement_gate=movement_gate,
        routing_report=routing_report,
        routing_metrics=routing_metrics,
        refit=refit_g5_probe,
        frozen_horizon=enforce_frozen_horizon,
        directional_claim=directional_claim,
        target_equivalence=target_equivalence,
        amp_smoke=production_amp_smoke,
        protected_update=protected_update,
        select_endpoints=select_g5_endpoints,
        metadata={
            "generation": "unified-v1",
            "attack_authority_package_root": F1B_ATTACK_AUTHORITY_ROOT,
            "real_execution_authorized": False,
            "training_critical_attack_seams": (
                "canonical tensor gradient/moment gates; canonical movement; "
                "canonical shared AMP protocol; canonical pre-step gate"
            ),
        },
    )
