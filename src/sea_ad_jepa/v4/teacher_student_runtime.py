"""Canonical production teacher/student runtime for JEPA v4.

This module consolidates the previously fragmented Stage81A3/C2/F1-B training
mechanics into one production-facing API. Historical scripts remain preserved
for forensic replay, but new training code should import this module.

No function here authorizes training. Execution authority is external and must
bind the frozen healthy-teacher base contract, this implementation, a
successor-bound u0 checkpoint, the predictor registry, and the movement
adjudicator before u1 is legal.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import torch

from .ema import EMAOptimizerStepController, create_ema_target, ema_target_module
from .ipb_jepa import (
    BlockPredictor,
    IPBEncoder,
    TargetBlocks,
    block_jepa_loss,
    gather_block_states,
)
from .masking import keyed_mask_seed

F1B_ATTACK_AUTHORITY_ROOT = "daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b"
POPULATION_ACCESS_ROOT = "e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7"
HEALTHY_TEACHER_BASE_ROOT = "9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534"

MANDATORY_BACKBONE_ROLES = (
    "attention_norm",
    "attention.query",
    "attention.key",
    "attention.value",
)
FROZEN_BACKBONE_REGISTRY = tuple(
    f"blocks.{block}.{role}.{suffix}"
    for block in range(6)
    for role in MANDATORY_BACKBONE_ROLES
    for suffix in ("weight", "bias")
)
FROZEN_PREDICTOR_REGISTRY = (
    "block_mask",
    "identity_projection.weight",
    "identity_projection.bias",
    "cross_attention.in_proj_weight",
    "cross_attention.in_proj_bias",
    "cross_attention.out_proj.weight",
    "cross_attention.out_proj.bias",
    "norm.weight",
    "norm.bias",
    "ffn.0.weight",
    "ffn.0.bias",
    "ffn.2.weight",
    "ffn.2.bias",
    "output_norm.weight",
    "output_norm.bias",
)


def registry_sha256(names: Sequence[str]) -> str:
    payload = "".join(f"{name}\n" for name in names).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


PREDICTOR_REGISTRY_SHA256 = registry_sha256(FROZEN_PREDICTOR_REGISTRY)
BACKBONE_REGISTRY_SHA256 = registry_sha256(FROZEN_BACKBONE_REGISTRY)


@dataclass(frozen=True)
class TeacherStudentConfig:
    vocabulary_size: int = 41_238
    width: int = 160
    heads: int = 4
    blocks: int = 6
    gradient_checkpointing: bool = True
    effective_batch: int = 128
    microbatch: int = 8
    views: int = 4
    mask_fraction: float = 0.40
    target_blocks: int = 16
    learning_rate: float = 1e-4
    betas: tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    weight_decay: float = 0.01
    ema_momentum: float = 0.996
    scaler_init_scale: float = 65_536.0
    scaler_growth_factor: float = 2.0
    scaler_backoff_factor: float = 0.5
    scaler_growth_interval: int = 2_000
    training_seed: int = 8_113_002
    masking_seed: int = 8_813_003

    def digest(self) -> str:
        payload = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


PRODUCTION_CONFIG = TeacherStudentConfig()


def validate_production_config(config: TeacherStudentConfig) -> dict[str, Any]:
    expected = asdict(PRODUCTION_CONFIG)
    observed = asdict(config)
    mismatches = {
        key: {"expected": expected[key], "observed": observed[key]}
        for key in expected
        if observed[key] != expected[key]
    }
    if mismatches:
        raise RuntimeError(f"production teacher/student configuration drift: {mismatches}")
    if config.effective_batch % config.microbatch:
        raise RuntimeError("effective batch must be divisible by microbatch")
    return {"passed": True, "config_sha256": config.digest()}


@dataclass
class TeacherStudentModules:
    online: IPBEncoder
    teacher: torch.nn.Module
    predictor: BlockPredictor
    optimizer: torch.optim.Optimizer
    scaler: torch.amp.GradScaler
    ema_controller: EMAOptimizerStepController
    device: torch.device


def _validate_exact_registry(module: torch.nn.Module, expected: Sequence[str], label: str) -> None:
    observed = tuple(name for name, p in module.named_parameters() if p.requires_grad)
    if label == "backbone":
        present = tuple(name for name in expected if name in dict(module.named_parameters()))
        missing = sorted(set(expected) - set(present))
        if missing:
            raise RuntimeError(f"missing protected backbone parameters: {missing[:8]}")
        return
    if observed != tuple(expected):
        missing = sorted(set(expected) - set(observed))
        unexpected = sorted(set(observed) - set(expected))
        raise RuntimeError(
            f"{label} registry mismatch: missing={missing[:8]} unexpected={unexpected[:8]}"
        )


def build_teacher_student_components(
    *,
    device: torch.device,
    config: TeacherStudentConfig = PRODUCTION_CONFIG,
) -> TeacherStudentModules:
    validate_production_config(config)
    torch.manual_seed(config.training_seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(config.training_seed)

    online = IPBEncoder(
        vocabulary_size=config.vocabulary_size,
        width=config.width,
        heads=config.heads,
        blocks=config.blocks,
        gradient_checkpointing=config.gradient_checkpointing,
    ).to(device)
    teacher = create_ema_target(online).to(device)
    predictor = BlockPredictor(width=config.width, heads=config.heads).to(device)
    online.train()
    predictor.train()
    teacher.eval()

    _validate_exact_registry(online, FROZEN_BACKBONE_REGISTRY, "backbone")
    _validate_exact_registry(predictor, FROZEN_PREDICTOR_REGISTRY, "predictor")

    optimizer = torch.optim.AdamW(
        list(online.parameters()) + list(predictor.parameters()),
        lr=config.learning_rate,
        betas=config.betas,
        eps=config.eps,
        weight_decay=config.weight_decay,
        amsgrad=False,
        maximize=False,
    )
    scaler = torch.amp.GradScaler(
        "cuda",
        init_scale=config.scaler_init_scale,
        growth_factor=config.scaler_growth_factor,
        backoff_factor=config.scaler_backoff_factor,
        growth_interval=config.scaler_growth_interval,
        enabled=device.type == "cuda",
    )
    controller = EMAOptimizerStepController(online, teacher)
    return TeacherStudentModules(
        online=online,
        teacher=teacher,
        predictor=predictor,
        optimizer=optimizer,
        scaler=scaler,
        ema_controller=controller,
        device=device,
    )


def _block_sizes(hidden_count: int, block_count: int) -> list[int]:
    quotient, remainder = divmod(hidden_count, block_count)
    return [quotient + (index < remainder) for index in range(block_count)]


def sample_uniform_target_blocks(
    measurement_mask: torch.Tensor,
    *,
    production_seed: int,
    cell_indices: torch.Tensor,
    sample_pass: int,
    view_index: int,
    mask_fraction: float = 0.40,
    block_count: int = 16,
) -> TargetBlocks:
    """Exact graph-free Stage81B masking semantics used by the frozen training base."""
    if measurement_mask.dtype is not torch.bool or measurement_mask.ndim != 2:
        raise ValueError("measurement_mask must be boolean [cells, genes]")
    if cell_indices.ndim != 1 or len(cell_indices) != len(measurement_mask):
        raise ValueError("cell_indices must contain one index per cell")
    if block_count < 1 or not 0.0 <= mask_fraction <= 1.0:
        raise ValueError("invalid block_count or mask_fraction")
    device = measurement_mask.device
    measured_cpu = measurement_mask.cpu()
    hidden = torch.zeros_like(measured_cpu)
    row_blocks: list[list[list[int]]] = []
    maximum_size = 0
    for row in range(len(measured_cpu)):
        measured = torch.nonzero(measured_cpu[row], as_tuple=False).flatten()
        hidden_count = int(math.floor(mask_fraction * len(measured)))
        sizes = _block_sizes(hidden_count, block_count)
        maximum_size = max(maximum_size, max(sizes, default=0))
        generator = torch.Generator(device="cpu").manual_seed(
            keyed_mask_seed(
                production_seed=production_seed,
                cell_index=int(cell_indices[row]),
                sample_pass=sample_pass,
                view_index=view_index,
            )
        )
        ranking = measured[torch.randperm(len(measured), generator=generator)]
        cursor = 0
        blocks: list[list[int]] = []
        for size in sizes:
            block = ranking[cursor : cursor + size].tolist()
            blocks.append(block)
            if block:
                hidden[row, block] = True
            cursor += size
        if cursor != hidden_count:
            raise RuntimeError("uniform target blocks do not match exact hidden count")
        row_blocks.append(blocks)
    indices = torch.full(
        (len(row_blocks), block_count, maximum_size), -1, dtype=torch.int64
    )
    members = torch.zeros_like(indices, dtype=torch.bool)
    for row, blocks_for_row in enumerate(row_blocks):
        for block_index, block in enumerate(blocks_for_row):
            if block:
                indices[row, block_index, : len(block)] = torch.tensor(block)
                members[row, block_index, : len(block)] = True
    return TargetBlocks(
        hidden.to(device),
        indices.to(device),
        members.to(device),
        torch.zeros(len(row_blocks), dtype=torch.int64, device=device),
    )


def _slice_blocks(
    blocks: TargetBlocks, start: int, end: int, device: torch.device
) -> TargetBlocks:
    return TargetBlocks(
        blocks.hidden_mask[start:end].to(device),
        blocks.indices[start:end].to(device),
        blocks.member_mask[start:end].to(device),
        blocks.fallback_counts[start:end].to(device),
    )


def _classify_gradient(gradient: torch.Tensor | None) -> str:
    if gradient is None:
        return "MISSING"
    detached = gradient.detach()
    if not bool(torch.isfinite(detached).all()):
        return "NONFINITE"
    if not bool((detached != 0).any()):
        return "EXACT_ZERO"
    return "LIVE"


def _gate_named_gradients(
    module: torch.nn.Module, names: Sequence[str], *, label: str
) -> dict[str, Any]:
    by_name = dict(module.named_parameters())
    missing_names = sorted(set(names) - set(by_name))
    if missing_names:
        raise RuntimeError(f"{label} registry missing parameters: {missing_names[:8]}")
    statuses = {name: _classify_gradient(by_name[name].grad) for name in names}
    rejected = sorted(name for name, status in statuses.items() if status != "LIVE")
    if rejected:
        raise RuntimeError(
            f"{label} mandatory unscaled gradient gate rejected: "
            + ", ".join(f"{name}={statuses[name]}" for name in rejected[:8])
        )
    return {"count": len(names), "statuses": statuses, "passed": True}


def enforce_unscaled_gradient_gates(
    modules: TeacherStudentModules,
) -> dict[str, Any]:
    backbone = _gate_named_gradients(
        modules.online, FROZEN_BACKBONE_REGISTRY, label="backbone"
    )
    predictor = _gate_named_gradients(
        modules.predictor, FROZEN_PREDICTOR_REGISTRY, label="predictor"
    )
    target_grads = [
        name
        for name, parameter in modules.teacher.named_parameters()
        if parameter.grad is not None
    ]
    if target_grads:
        raise RuntimeError(f"EMA teacher received gradients: {target_grads[:8]}")
    nonfinite_elsewhere: list[str] = []
    for prefix, module in (("online", modules.online), ("predictor", modules.predictor)):
        for name, parameter in module.named_parameters():
            if not parameter.requires_grad or parameter.grad is None:
                continue
            if not bool(torch.isfinite(parameter.grad.detach()).all()):
                nonfinite_elsewhere.append(f"{prefix}.{name}")
    if nonfinite_elsewhere:
        raise RuntimeError(
            "nonfinite trainable gradient outside mandatory registry: "
            + str(nonfinite_elsewhere[:8])
        )
    return {"backbone": backbone, "predictor": predictor, "target_gradients": []}


def _optimizer_step_value(optimizer: torch.optim.Optimizer, parameter: torch.Tensor) -> int:
    value = optimizer.state.get(parameter, {}).get("step", 0)
    try:
        return int(value.item())
    except AttributeError:
        return int(value)


def enforce_adam_moments(modules: TeacherStudentModules) -> dict[str, Any]:
    checks: list[tuple[str, torch.Tensor]] = []
    online = dict(modules.online.named_parameters())
    predictor = dict(modules.predictor.named_parameters())
    checks.extend((f"backbone.{name}", online[name]) for name in FROZEN_BACKBONE_REGISTRY)
    checks.extend((f"predictor.{name}", predictor[name]) for name in FROZEN_PREDICTOR_REGISTRY)
    rejected: list[str] = []
    for name, parameter in checks:
        state = modules.optimizer.state.get(parameter, {})
        for field in ("exp_avg", "exp_avg_sq"):
            value = state.get(field)
            if value is None:
                rejected.append(f"{name}:{field}:MISSING")
                continue
            detached = value.detach()
            if not bool(torch.isfinite(detached).all()):
                rejected.append(f"{name}:{field}:NONFINITE")
            elif not bool((detached != 0).any()):
                rejected.append(f"{name}:{field}:EXACT_ZERO")
    if rejected:
        raise RuntimeError("Adam moment gate rejected: " + ", ".join(rejected[:8]))
    return {"passed": True, "tensor_count": len(checks), "fields": ["exp_avg", "exp_avg_sq"]}


def _snapshot_state(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def _verify_ema_equation(
    *,
    before: Mapping[str, torch.Tensor],
    online: torch.nn.Module,
    teacher: torch.nn.Module,
    momentum: float,
) -> dict[str, Any]:
    actual = ema_target_module(teacher).state_dict()
    online_state = online.state_dict()
    failures: list[str] = []
    for name, old in before.items():
        now = actual[name]
        source = online_state[name]
        if old.is_floating_point() or old.is_complex():
            expected = old.clone()
            expected.mul_(momentum).add_(source, alpha=1.0 - momentum)
        else:
            expected = source
        if not torch.equal(expected, now):
            failures.append(name)
    if failures:
        raise RuntimeError("EMA equation mismatch: " + ", ".join(failures[:8]))
    return {"passed": True, "checked_state_items": len(before)}


def _mask_sha256(mask: torch.Tensor) -> str:
    return hashlib.sha256(mask.detach().cpu().numpy().tobytes()).hexdigest()


def execute_scaled_backward(harness: Any) -> None:
    """Execute the scaled-backward seam used by production and F1-B attack 13."""
    harness.scaler_scale_backward()


def execute_post_backward_protocol(harness: Any) -> None:
    """One fail-closed post-accumulation protocol shared with the attack harness."""
    harness.scaler_unscale()
    harness.gradient_gate()
    harness.optimizer_step()
    harness.ema_step()


def production_amp_smoke(harness: Any) -> dict[str, str]:
    """Behavioral F1-B seam: exercise the same backward/post-backward protocol."""
    with harness.autocast():
        harness.forward()
    execute_scaled_backward(harness)
    execute_post_backward_protocol(harness)
    return {"status": "executed"}


class _ScaledLossBackwardHarness:
    def __init__(self, *, scaler: Any, loss: torch.Tensor, device_type: str) -> None:
        self.scaler = scaler
        self.loss = loss
        self.device_type = device_type

    def scaler_scale_backward(self) -> None:
        # C2 repair: scaled backward is explicitly outside fp16 autocast.
        with torch.autocast(device_type=self.device_type, enabled=False):
            self.scaler.scale(self.loss).backward()


class _ProductionPostBackwardHarness:
    """Real optimizer/EMA adapter for the shared post-backward protocol."""

    def __init__(
        self,
        *,
        modules: TeacherStudentModules,
        teacher_before: Mapping[str, torch.Tensor],
        config: TeacherStudentConfig,
    ) -> None:
        self.modules = modules
        self.teacher_before = teacher_before
        self.config = config
        self.gradient_report: dict[str, Any] | None = None
        self.moment_report: dict[str, Any] | None = None
        self.ema_report: dict[str, Any] | None = None
        self.step_before: int | None = None
        self.step_after: int | None = None

    def scaler_unscale(self) -> None:
        self.modules.scaler.unscale_(self.modules.optimizer)

    def gradient_gate(self) -> None:
        self.gradient_report = enforce_unscaled_gradient_gates(self.modules)

    def optimizer_step(self) -> None:
        sentinel = dict(self.modules.online.named_parameters())[FROZEN_BACKBONE_REGISTRY[0]]
        self.step_before = _optimizer_step_value(self.modules.optimizer, sentinel)
        self.modules.scaler.step(self.modules.optimizer)
        self.modules.scaler.update()
        self.step_after = _optimizer_step_value(self.modules.optimizer, sentinel)
        if self.step_after != self.step_before + 1:
            raise RuntimeError(
                f"optimizer step not proved: before={self.step_before} after={self.step_after}"
            )
        self.moment_report = enforce_adam_moments(self.modules)

    def ema_step(self) -> None:
        if self.step_after is None:
            raise RuntimeError("EMA before proved optimizer step")
        self.modules.ema_controller.after_successful_optimizer_step(
            momentum=self.config.ema_momentum
        )
        if self.modules.ema_controller.global_update_step != self.step_after:
            raise RuntimeError("EMA/global optimizer step counter mismatch")
        if self.modules.ema_controller.ema_update_count != self.step_after:
            raise RuntimeError("EMA update count mismatch")
        self.ema_report = _verify_ema_equation(
            before=self.teacher_before,
            online=self.modules.online,
            teacher=self.modules.teacher,
            momentum=self.config.ema_momentum,
        )


def validate_training_batch(
    expression: torch.Tensor,
    measurement_mask: torch.Tensor,
    stable_mask_keys: torch.Tensor,
    *,
    config: TeacherStudentConfig,
) -> None:
    if expression.ndim != 2 or expression.shape != measurement_mask.shape:
        raise ValueError("expression and measurement_mask must be aligned [batch,genes]")
    if expression.shape != (config.effective_batch, config.vocabulary_size):
        raise ValueError(
            f"expected production batch {(config.effective_batch, config.vocabulary_size)}, "
            f"got {tuple(expression.shape)}"
        )
    if measurement_mask.dtype is not torch.bool:
        raise ValueError("measurement_mask must be boolean")
    if stable_mask_keys.shape != (config.effective_batch,) or stable_mask_keys.dtype != torch.int64:
        raise ValueError("stable_mask_keys must be int64 [effective_batch]")
    if len(torch.unique(stable_mask_keys)) != config.effective_batch:
        raise RuntimeError("same-update cell replay detected")
    if not bool(torch.isfinite(expression).all()):
        raise RuntimeError("nonfinite expression input")
    if bool((expression[~measurement_mask] != 0).any()):
        raise RuntimeError("numeric value outside MEASURED_SCALAR")


def production_update(
    modules: TeacherStudentModules,
    *,
    expression: torch.Tensor,
    measurement_mask: torch.Tensor,
    stable_mask_keys: torch.Tensor,
    schedule_cursor: int,
    config: TeacherStudentConfig = PRODUCTION_CONFIG,
) -> dict[str, Any]:
    """Execute one canonical repaired teacher/student optimizer update.

    Inputs are already the exact frozen schedule batch in slot order. This
    function performs no donor/cell selection and therefore cannot silently
    replace the frozen scheduler with a new sampler.
    """
    validate_production_config(config)
    validate_training_batch(
        expression, measurement_mask, stable_mask_keys, config=config
    )
    if modules.device.type != "cuda":
        raise RuntimeError("healthy-teacher qualification requires CUDA")
    if schedule_cursor < 0:
        raise ValueError("schedule_cursor must be non-negative")

    expression = expression.detach().cpu()
    measurement_mask = measurement_mask.detach().cpu()
    stable_mask_keys = stable_mask_keys.detach().cpu()

    views = [
        sample_uniform_target_blocks(
            measurement_mask,
            production_seed=config.training_seed,
            cell_indices=stable_mask_keys,
            sample_pass=schedule_cursor,
            view_index=view,
            mask_fraction=config.mask_fraction,
            block_count=config.target_blocks,
        )
        for view in range(config.views)
    ]
    if any(bool((view.hidden_mask & ~measurement_mask).any()) for view in views):
        raise RuntimeError("artificial target outside MEASURED_SCALAR")

    modules.online.train()
    modules.predictor.train()
    modules.teacher.eval()
    modules.optimizer.zero_grad(set_to_none=True)

    teacher_before = _snapshot_state(ema_target_module(modules.teacher))
    mask_hashes = [_mask_sha256(view.hidden_mask) for view in views]
    loss_total = 0.0
    microbatches = config.effective_batch // config.microbatch
    events: list[str] = []

    for begin in range(0, config.effective_batch, config.microbatch):
        end = begin + config.microbatch
        values = expression[begin:end].to(modules.device, non_blocking=True)
        measured = measurement_mask[begin:end].to(modules.device, non_blocking=True)
        gene_ids = torch.arange(
            config.vocabulary_size, device=modules.device, dtype=torch.int64
        ).expand(config.microbatch, -1)

        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
            events.append("forward_fp16_autocast")
            with torch.no_grad():
                teacher_state = modules.teacher(
                    gene_ids, values, measured, torch.zeros_like(measured), "target"
                )
            for view_index in range(config.views):
                block = _slice_blocks(views[view_index], begin, end, modules.device)
                student_state = modules.online(
                    gene_ids, values, measured, block.hidden_mask, "student"
                )
                prediction = modules.predictor(
                    modules.online.tokenizer.gene_identity,
                    block,
                    student_state.gene_states,
                    student_state.cell_state,
                    measured & ~block.hidden_mask,
                )
                teacher_blocks = gather_block_states(teacher_state.gene_states, block)
                raw_loss = block_jepa_loss(prediction, teacher_blocks)
                if not bool(torch.isfinite(raw_loss.detach())):
                    raise RuntimeError("nonfinite JEPA loss")
                scaled_loss = raw_loss / (config.views * microbatches)

                events.append("backward_autocast_disabled")
                execute_scaled_backward(
                    _ScaledLossBackwardHarness(
                        scaler=modules.scaler,
                        loss=scaled_loss,
                        device_type=modules.device.type,
                    )
                )

                loss_total += float(raw_loss.detach()) / (config.views * microbatches)
                del block, student_state, prediction, teacher_blocks, raw_loss, scaled_loss
            del teacher_state, values, measured, gene_ids

    post = _ProductionPostBackwardHarness(
        modules=modules,
        teacher_before=teacher_before,
        config=config,
    )
    execute_post_backward_protocol(post)
    events.extend([
        "optimizer_unscaled",
        "mandatory_gradient_gate",
        "optimizer_step_proved",
        "adam_moments_live",
        "ema_after_valid_step",
        "ema_equation_verified",
    ])
    gradient_report = post.gradient_report
    moment_report = post.moment_report
    ema_report = post.ema_report
    step_before = post.step_before
    step_after = post.step_after

    return {
        "schema": "teacher-student-update-v1",
        "schedule_cursor": int(schedule_cursor),
        "loss": loss_total,
        "mask_sha256": mask_hashes,
        "optimizer_step_before": step_before,
        "optimizer_step_after": step_after,
        "global_update_step": modules.ema_controller.global_update_step,
        "ema_update_count": modules.ema_controller.ema_update_count,
        "gradient_gate": gradient_report,
        "adam_moments": moment_report,
        "ema_equation": ema_report,
        "events": events,
        "config_sha256": config.digest(),
        "backbone_registry_sha256": BACKBONE_REGISTRY_SHA256,
        "predictor_registry_sha256": PREDICTOR_REGISTRY_SHA256,
        "attack_authority_root": F1B_ATTACK_AUTHORITY_ROOT,
        "healthy_teacher_base_root": HEALTHY_TEACHER_BASE_ROOT,
    }
