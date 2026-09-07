#!/usr/bin/env python3
"""Prospective F1-B/C3 training-successor mechanics, generation v2.

This module is downstream of frozen F1-B attack authority package root
daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b.
It must not rewrite those attacks to obtain a pass.

The implementation is mechanics-only and data-blind. Real F1, real T0,
DEV/SEALED/pathology/reader-oracle and fresh T1/C3 execution remain unauthorized.

The CUDA update carries the C2 repair explicitly: forward may use fp16 autocast,
but scaled backward executes inside autocast(enabled=False). The optimizer is
unscaled before mandatory-gradient adjudication, both Adam moments are checked,
the optimizer step is proved, and only then is EMA advanced.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

FROZEN_UPDATES = 40
MOVEMENT_OVER_DECAY_MARGIN = 2.0
REGISTERED_G5_ENDPOINTS = ("l2__broad_common", "l2__local")
ATTACK_AUTHORITY_PACKAGE_ROOT = (
    "daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b"
)

MANDATORY_BACKBONE_ROLES = (
    "attention_norm",
    "attention.query",
    "attention.key",
    "attention.value",
)
FROZEN_MANDATORY_BACKBONE = tuple(
    "blocks.%d.%s.%s" % (block, role, suffix)
    for block in range(6)
    for role in MANDATORY_BACKBONE_ROLES
    for suffix in ("weight", "bias")
)


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _finite_nonzero(value: Any) -> bool:
    return _finite(value) and float(value) != 0.0


# ---------------------------------------------------------------------------
# Frozen-attack behavioural seams
# ---------------------------------------------------------------------------

def gate_mandatory_gradients(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Reject missing/nonfinite/exact-zero backbone or predictor mechanics."""
    protected: dict[str, Any] = {}
    protected.update(dict(payload.get("backbone") or {}))
    protected.update(dict(payload.get("predictor") or {}))
    if not protected:
        raise RuntimeError("no mandatory gradient tensors supplied")

    rejected = sorted(name for name, value in protected.items() if not _finite_nonzero(value))
    if rejected:
        raise RuntimeError("mandatory gradient rejected: " + ", ".join(rejected[:8]))

    for name, moments in dict(payload.get("moments") or {}).items():
        if not isinstance(moments, Mapping):
            raise RuntimeError("invalid Adam moment payload for " + str(name))
        for field in ("exp_avg", "exp_avg_sq"):
            if field not in moments or not _finite_nonzero(moments[field]):
                raise RuntimeError("dead %s for %s" % (field, name))

    return {"checked": sorted(protected), "passed": True}


def movement_gate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Per-tensor movement only; pooled means can never rescue a dead tensor."""
    rel = dict(payload.get("relative_movement") or {})
    absolute = dict(payload.get("absolute_movement") or {})
    baseline = dict(payload.get("baseline_norm") or {})
    decay = float(payload["decay_only_prediction"])
    failures: list[str] = []

    for name in rel:
        base = float(baseline.get(name, 1.0))
        if base == 0.0:
            if not _finite(absolute.get(name)) or float(absolute.get(name, 0.0)) <= 0.0:
                failures.append(name)
            continue
        value = rel.get(name)
        if (value is None or not _finite(value)
                or float(value) <= decay * MOVEMENT_OVER_DECAY_MARGIN):
            failures.append(name)

    if failures:
        raise RuntimeError("per-tensor movement failed: " + ", ".join(sorted(failures)[:8]))
    return {"checked": sorted(rel), "passed": True}


def routing_report(weights: Sequence[Sequence[float]],
                   valid_support: Sequence[int]) -> list[float]:
    """Return entropy effective support independently for every cell."""
    if len(weights) != len(valid_support):
        raise RuntimeError("per-cell routing/support length mismatch")
    out: list[float] = []
    for row, support in zip(weights, valid_support):
        support = int(support)
        if support <= 0 or support > len(row):
            raise RuntimeError("invalid per-cell support")
        mass = [max(float(x), 0.0) for x in row[:support]]
        total = sum(mass)
        if total <= 0.0:
            raise RuntimeError("zero routing mass")
        p = [x / total for x in mass]
        out.append(math.exp(-sum(x * math.log(x + 1e-30) for x in p)))
    return out


def routing_metrics(weights: Sequence[Sequence[float]],
                    masks: Sequence[Sequence[bool]]) -> dict[str, Any]:
    """Compute mask-respecting per-query entropy and participation effective support."""
    if len(weights) != len(masks) or not weights:
        raise RuntimeError("query support mismatch")
    width = max(len(row) for row in weights)
    entropy: list[float] = []
    participation: list[float] = []
    top1: list[float] = []
    valid_keys: list[int] = []
    full: list[list[float]] = []

    for row, mask in zip(weights, masks):
        if len(row) != len(mask):
            raise RuntimeError("weight/mask length mismatch")
        kept = [max(float(x), 0.0) for x, keep in zip(row, mask) if keep]
        if not kept:
            raise RuntimeError("no valid keys")
        total = sum(kept)
        if total <= 0.0:
            raise RuntimeError("zero routing mass")
        p = [x / total for x in kept]
        entropy.append(math.exp(-sum(x * math.log(x + 1e-30) for x in p)))
        participation.append(1.0 / sum(x * x for x in p))
        top1.append(max(p))
        valid_keys.append(len(p))

        vector = [0.0] * width
        j = 0
        for index, keep in enumerate(mask):
            if keep:
                vector[index] = p[j]
                j += 1
        full.append(vector)

    if len(full) == 1:
        query_map_cosine = 1.0
    else:
        cosines: list[float] = []
        for i in range(len(full)):
            for j in range(i + 1, len(full)):
                dot = sum(a * b for a, b in zip(full[i], full[j]))
                ni = math.sqrt(sum(a * a for a in full[i]))
                nj = math.sqrt(sum(b * b for b in full[j]))
                cosines.append(dot / max(ni * nj, 1e-30))
        query_map_cosine = sum(cosines) / len(cosines)

    return {
        "N_eff_entropy": entropy,
        "N_eff_participation": participation,
        "top1_mass": top1,
        "valid_keys": valid_keys,
        "query_map_cosine": query_map_cosine,
    }


def refit_g5_probe(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministic donor-held-out refit mechanic; no biological G5 claim."""
    fit_donors = list(payload.get("fit_donors") or ())
    eval_donors = list(payload.get("eval_donors") or ())
    fit_values = [float(x) for x in payload.get("fit_values") or ()]
    eval_values = list(payload.get("eval_values") or ())
    if not fit_values or len(fit_values) != len(fit_donors):
        raise RuntimeError("invalid fit split")
    if set(fit_donors) & set(eval_donors):
        raise RuntimeError("fit/eval donor overlap")
    fitted_mean = sum(fit_values) / len(fit_values)
    return {
        "predictions": [fitted_mean for _ in eval_values],
        "fit_mean": fitted_mean,
        "fit_donors_used": fit_donors,
    }


def enforce_frozen_horizon(updates: int) -> dict[str, int]:
    updates = int(updates)
    if updates != FROZEN_UPDATES:
        raise RuntimeError("frozen horizon is %d; refused %d" % (FROZEN_UPDATES, updates))
    return {"updates": FROZEN_UPDATES}


def directional_claim(payload: Mapping[str, float]) -> dict[str, Any]:
    """Withhold structural claim if CELL-only or identity-only explains the effect."""
    observed = float(payload["observed"])
    cell = float(payload.get("cell_only_control", 0.0))
    identity = float(payload.get("identity_only_control", 0.0))
    explained = max(abs(cell), abs(identity)) >= 0.5 * abs(observed)
    return {
        "structural": not explained,
        "explained_by_control": explained,
        "claim_scope": (
            "query-local structure remains after both controls"
            if not explained else
            "structural claim withheld because a restricted control explains the effect"
        ),
    }


def target_equivalence(singleton_q: Sequence[float],
                       all_q: Sequence[float]) -> dict[str, Any]:
    if len(singleton_q) != len(all_q):
        raise RuntimeError("target length mismatch")
    worst = max(
        (abs(float(a) - float(b)) for a, b in zip(singleton_q, all_q)),
        default=0.0,
    )
    return {"equivalent": worst <= 1e-9, "max_abs_difference": worst}


def _execute_amp_sequence(harness: Any) -> dict[str, str]:
    """Single orchestration authority shared by smoke and torch production update."""
    with harness.autocast():
        harness.forward()
    harness.scaler_scale_backward()
    harness.scaler_unscale()
    harness.gradient_gate()
    harness.optimizer_step()
    harness.ema_step()
    return {"status": "executed"}


def production_amp_smoke(harness: Any) -> dict[str, str]:
    """The frozen finding-13 attack hits the same sequence used in production."""
    return _execute_amp_sequence(harness)


def protected_update(payload: Mapping[str, Any]) -> dict[str, bool]:
    """Rejected gradients cannot mutate optimizer state."""
    gradients = dict(payload.get("mandatory_gradients") or {})
    if not gradients:
        raise RuntimeError("no mandatory gradients")
    rejected = [name for name, value in gradients.items() if not _finite_nonzero(value)]
    if rejected:
        raise RuntimeError("dead mandatory gradients before step: " + str(sorted(rejected)))
    ledger = payload["ledger"]
    ledger["stepped"] = True
    ledger["optimizer_state_entries"] = len(gradients)
    return {"stepped": True}


def select_g5_endpoints(keys: Sequence[str]) -> list[str]:
    missing = [name for name in REGISTERED_G5_ENDPOINTS if name not in set(keys)]
    if missing:
        raise RuntimeError("registered endpoint absent: " + str(missing))
    return [name for name in keys if name in REGISTERED_G5_ENDPOINTS]


# ---------------------------------------------------------------------------
# Torch production-update mechanics
# ---------------------------------------------------------------------------

def _torch_classify_gradient(grad: Any) -> str:
    import torch
    if grad is None:
        return "MISSING"
    detached = grad.detach()
    if not bool(torch.isfinite(detached).all()):
        return "NONFINITE"
    if not bool((detached != 0).any()):
        return "EXACT_ZERO"
    return "LIVE"


def protected_parameter_names(online: Any, predictor: Any) -> tuple[list[str], list[str]]:
    online_names = set(dict(online.named_parameters()))
    missing = sorted(set(FROZEN_MANDATORY_BACKBONE) - online_names)
    if missing:
        raise RuntimeError("mandatory backbone registry mismatch: " + str(missing[:8]))
    predictor_names = sorted(
        name for name, parameter in predictor.named_parameters() if parameter.requires_grad
    )
    if not predictor_names:
        raise RuntimeError("predictor exposes no trainable parameters")
    return list(FROZEN_MANDATORY_BACKBONE), predictor_names


def enforce_unscaled_gradients(online: Any, predictor: Any) -> dict[str, Any]:
    """Call only after scaler.unscale_ and before scaler.step."""
    import torch
    backbone_names, predictor_names = protected_parameter_names(online, predictor)
    statuses: dict[str, str] = {}
    online_map = dict(online.named_parameters())
    predictor_map = dict(predictor.named_parameters())

    for name in backbone_names:
        statuses["backbone." + name] = _torch_classify_gradient(online_map[name].grad)
    for name in predictor_names:
        statuses["predictor." + name] = _torch_classify_gradient(predictor_map[name].grad)

    rejected = sorted(name for name, status in statuses.items() if status != "LIVE")
    if rejected:
        raise RuntimeError("mandatory unscaled gradient gate rejected: " + str(rejected[:8]))

    nonfinite_elsewhere: list[str] = []
    for prefix, module in (("backbone", online), ("predictor", predictor)):
        for name, parameter in module.named_parameters():
            if not parameter.requires_grad or parameter.grad is None:
                continue
            if not bool(torch.isfinite(parameter.grad.detach()).all()):
                nonfinite_elsewhere.append(prefix + "." + name)
    if nonfinite_elsewhere:
        raise RuntimeError(
            "nonfinite trainable gradient outside protected set: "
            + str(nonfinite_elsewhere[:8])
        )
    return {
        "passed": True,
        "protected_backbone": len(backbone_names),
        "protected_predictor": len(predictor_names),
        "statuses": statuses,
    }


def _optimizer_step_value(optimizer: Any, parameter: Any) -> int:
    state = optimizer.state.get(parameter, {})
    value = state.get("step", 0)
    try:
        return int(value.item())
    except AttributeError:
        return int(value)


def enforce_adam_moments(optimizer: Any, online: Any, predictor: Any) -> dict[str, Any]:
    """Both exp_avg and exp_avg_sq are independently finite and nonzero."""
    import torch
    backbone_names, predictor_names = protected_parameter_names(online, predictor)
    online_map = dict(online.named_parameters())
    predictor_map = dict(predictor.named_parameters())
    checks = (
        [("backbone." + name, online_map[name]) for name in backbone_names]
        + [("predictor." + name, predictor_map[name]) for name in predictor_names]
    )
    rejected: list[str] = []
    for name, parameter in checks:
        state = optimizer.state.get(parameter, {})
        for field in ("exp_avg", "exp_avg_sq"):
            value = state.get(field)
            if value is None:
                rejected.append(name + ":" + field + ":MISSING")
                continue
            detached = value.detach()
            if not bool(torch.isfinite(detached).all()):
                rejected.append(name + ":" + field + ":NONFINITE")
            elif not bool((detached != 0).any()):
                rejected.append(name + ":" + field + ":EXACT_ZERO")
    if rejected:
        raise RuntimeError("Adam moment gate rejected: " + str(rejected[:8]))
    return {"passed": True, "tensors": len(checks), "moment_fields_per_tensor": 2}


def movement_report_per_tensor(module: Any,
                               baseline: Mapping[str, Any],
                               learning_rate: float,
                               weight_decay: float,
                               steps: int) -> dict[str, Any]:
    """Adjudicate each of the 48 protected tensors separately."""
    params = dict(module.named_parameters())
    decay = 1.0 - (1.0 - learning_rate * weight_decay) ** max(int(steps), 1)
    rows: dict[str, dict[str, Any]] = {}
    failed: list[str] = []
    for name in FROZEN_MANDATORY_BACKBONE:
        if name not in params or name not in baseline:
            failed.append(name)
            continue
        before = baseline[name].detach().float()
        after = params[name].detach().float()
        delta = after - before
        base_norm = float(before.norm())
        absolute = float(delta.norm())
        relative = None if base_norm == 0.0 else absolute / base_norm
        if base_norm == 0.0:
            passed = math.isfinite(absolute) and absolute > 0.0
        else:
            passed = (
                relative is not None
                and math.isfinite(relative)
                and relative > decay * MOVEMENT_OVER_DECAY_MARGIN
            )
        if not passed:
            failed.append(name)
        rows[name] = {
            "baseline_norm": base_norm,
            "absolute_movement": absolute,
            "relative_movement": relative,
            "decay_only_prediction": decay,
            "passed": passed,
        }
    return {
        "rows": rows,
        "failed": sorted(set(failed)),
        "passed": not failed,
        "terminal": "PASS_PER_TENSOR_MOVEMENT" if not failed else "STOP_PER_TENSOR_MOVEMENT",
    }


def ema_update_exact(teacher: Any, online: Any, decay: float) -> None:
    import torch
    with torch.no_grad():
        for teacher_parameter, online_parameter in zip(
                teacher.parameters(), online.parameters(), strict=True):
            teacher_parameter.mul_(decay).add_(
                online_parameter.detach(), alpha=1.0 - decay
            )


class _TorchAmpHarness:
    """Adapter from real torch objects to the frozen production AMP sequence."""

    def __init__(self, *, online: Any, predictor: Any, teacher: Any, optimizer: Any,
                 scaler: Any, loss_closure: Any, device: Any, ema_decay: float):
        import torch
        self.torch = torch
        self.online = online
        self.predictor = predictor
        self.teacher = teacher
        self.optimizer = optimizer
        self.scaler = scaler
        self.loss_closure = loss_closure
        self.device = device
        self.device_type = getattr(device, "type", str(device))
        self.ema_decay = float(ema_decay)
        self.loss = None
        self.gradient_report = None
        self.moment_report = None
        self.step_before = None
        self.step_after = None
        self.ema_updated = False
        self.optimizer.zero_grad(set_to_none=True)

    def autocast(self):
        return self.torch.autocast(
            device_type=self.device_type,
            dtype=self.torch.float16 if self.device_type == "cuda" else None,
            enabled=self.device_type == "cuda",
        )

    def forward(self) -> None:
        self.loss = self.loss_closure()
        if not bool(self.torch.isfinite(self.loss.detach())):
            raise RuntimeError("nonfinite successor loss")

    def scaler_scale_backward(self) -> None:
        if self.loss is None:
            raise RuntimeError("backward before forward")
        # C2 repair: backward explicitly outside fp16 autocast.
        with self.torch.autocast(device_type=self.device_type, enabled=False):
            self.scaler.scale(self.loss).backward()

    def scaler_unscale(self) -> None:
        self.scaler.unscale_(self.optimizer)

    def gradient_gate(self) -> None:
        self.gradient_report = enforce_unscaled_gradients(self.online, self.predictor)

    def optimizer_step(self) -> None:
        backbone_names, _ = protected_parameter_names(self.online, self.predictor)
        sentinel = dict(self.online.named_parameters())[backbone_names[0]]
        self.step_before = _optimizer_step_value(self.optimizer, sentinel)
        self.scaler.step(self.optimizer)
        self.scaler.update()
        self.step_after = _optimizer_step_value(self.optimizer, sentinel)
        if self.step_after != self.step_before + 1:
            raise RuntimeError(
                "optimizer step not proved: before=%d after=%d"
                % (self.step_before, self.step_after)
            )
        self.moment_report = enforce_adam_moments(
            self.optimizer, self.online, self.predictor
        )

    def ema_step(self) -> None:
        if self.step_after is None:
            raise RuntimeError("EMA before optimizer step")
        ema_update_exact(self.teacher, self.online, self.ema_decay)
        self.ema_updated = True


def production_amp_update(*,
                          online: Any,
                          predictor: Any,
                          teacher: Any,
                          optimizer: Any,
                          scaler: Any,
                          loss_closure: Any,
                          device: Any,
                          ema_decay: float) -> dict[str, Any]:
    """One repaired update driven by the exact sequence exercised by finding 13."""
    harness = _TorchAmpHarness(
        online=online,
        predictor=predictor,
        teacher=teacher,
        optimizer=optimizer,
        scaler=scaler,
        loss_closure=loss_closure,
        device=device,
        ema_decay=ema_decay,
    )
    _execute_amp_sequence(harness)
    return {
        "loss": float(harness.loss.detach()),
        "optimizer_step_before": harness.step_before,
        "optimizer_step_after": harness.step_after,
        "gradient_gate": harness.gradient_report,
        "adam_moments": harness.moment_report,
        "ema_updated": harness.ema_updated,
        "backward_autocast_disabled": True,
    }
