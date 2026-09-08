"""Successor-bound production checkpoint schema for the unified teacher/student runtime."""
from __future__ import annotations

import copy
import hashlib
import os
import platform
import random
import tempfile
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch

from .ema import EMAOptimizerStepController
from .teacher_student_runtime import TeacherStudentConfig, TeacherStudentModules

CHECKPOINT_SCHEMA = "JEPA_HEALTHY_TEACHER_CHECKPOINT_V1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def environment_fingerprint() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cudnn": None if not torch.backends.cudnn.is_available() else torch.backends.cudnn.version(),
        "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "cuda_devices": [
            torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
        ] if torch.cuda.is_available() else [],
        "tf32_matmul": bool(torch.backends.cuda.matmul.allow_tf32),
        "tf32_cudnn": bool(torch.backends.cudnn.allow_tf32),
        "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
    }


def _gradient_state(module: torch.nn.Module) -> dict[str, torch.Tensor | None]:
    return {
        name: None if p.grad is None else p.grad.detach().clone()
        for name, p in module.named_parameters()
    }


def _restore_gradients(
    module: torch.nn.Module, gradients: Mapping[str, torch.Tensor | None]
) -> None:
    parameters = dict(module.named_parameters())
    if set(parameters) != set(gradients):
        raise RuntimeError("checkpoint gradient structure does not match module")
    for name, gradient in gradients.items():
        parameters[name].grad = (
            None if gradient is None else gradient.clone().to(parameters[name])
        )


def capture_checkpoint(
    modules: TeacherStudentModules,
    *,
    config: TeacherStudentConfig,
    schedule_cursor: int,
    accumulation_position: int,
    masking_generator: torch.Generator | None,
    authority_bindings: Mapping[str, str],
    phase: str,
) -> dict[str, Any]:
    if schedule_cursor < 0 or accumulation_position < 0:
        raise ValueError("checkpoint counters must be non-negative")
    if phase not in {"U0", "QUALIFICATION", "CONTINUATION"}:
        raise ValueError("invalid checkpoint phase")
    required = {
        "healthy_teacher_base_root",
        "population_access_root",
        "f1b_attack_authority_root",
        "integrated_successor_source_root",
    }
    missing = sorted(required - set(authority_bindings))
    if missing:
        raise RuntimeError("checkpoint authority bindings missing: " + ", ".join(missing))
    for key, value in authority_bindings.items():
        if len(str(value)) != 64:
            raise RuntimeError(f"checkpoint authority binding is not SHA-256: {key}")

    return {
        "schema": CHECKPOINT_SCHEMA,
        "phase": phase,
        "config": copy.deepcopy(config.__dict__),
        "config_sha256": config.digest(),
        "authority_bindings": dict(sorted(authority_bindings.items())),
        "environment": environment_fingerprint(),
        "online_encoder": copy.deepcopy(modules.online.state_dict()),
        "teacher": copy.deepcopy(modules.teacher.state_dict()),
        "predictor": copy.deepcopy(modules.predictor.state_dict()),
        "optimizer": copy.deepcopy(modules.optimizer.state_dict()),
        "grad_scaler": copy.deepcopy(modules.scaler.state_dict()),
        "online_gradients": _gradient_state(modules.online),
        "predictor_gradients": _gradient_state(modules.predictor),
        "global_update_step": int(modules.ema_controller.global_update_step),
        "ema_update_count": int(modules.ema_controller.ema_update_count),
        "schedule_cursor": int(schedule_cursor),
        "accumulation_position": int(accumulation_position),
        "python_rng_state": random.getstate(),
        "numpy_rng_state": np.random.get_state(),
        "torch_cpu_rng_state": torch.get_rng_state().clone(),
        "torch_cuda_rng_states": (
            [state.clone() for state in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else None
        ),
        "masking_rng_state": (
            masking_generator.get_state().clone()
            if masking_generator is not None
            else None
        ),
    }


def validate_checkpoint_header(
    payload: Mapping[str, Any],
    *,
    config: TeacherStudentConfig,
    expected_authorities: Mapping[str, str],
    expected_schedule_cursor: int | None = None,
) -> None:
    if payload.get("schema") != CHECKPOINT_SCHEMA:
        raise RuntimeError("checkpoint schema mismatch")
    if payload.get("config_sha256") != config.digest():
        raise RuntimeError("checkpoint config mismatch")
    observed = payload.get("authority_bindings")
    if not isinstance(observed, Mapping):
        raise RuntimeError("checkpoint authority bindings absent")
    for key, expected in expected_authorities.items():
        if observed.get(key) != expected:
            raise RuntimeError(f"checkpoint authority mismatch: {key}")
    if expected_schedule_cursor is not None and int(payload.get("schedule_cursor", -1)) != int(expected_schedule_cursor):
        raise RuntimeError("checkpoint schedule cursor mismatch")
    global_step = int(payload.get("global_update_step", -1))
    ema_count = int(payload.get("ema_update_count", -1))
    if global_step < 0 or ema_count < 0 or global_step != ema_count:
        raise RuntimeError("checkpoint optimizer/EMA counters invalid")


def restore_checkpoint(
    payload: Mapping[str, Any],
    modules: TeacherStudentModules,
    *,
    config: TeacherStudentConfig,
    expected_authorities: Mapping[str, str],
    masking_generator: torch.Generator | None,
    expected_schedule_cursor: int | None = None,
) -> dict[str, int]:
    validate_checkpoint_header(
        payload,
        config=config,
        expected_authorities=expected_authorities,
        expected_schedule_cursor=expected_schedule_cursor,
    )
    modules.online.load_state_dict(payload["online_encoder"])
    modules.teacher.load_state_dict(payload["teacher"])
    modules.predictor.load_state_dict(payload["predictor"])
    modules.optimizer.load_state_dict(payload["optimizer"])
    modules.scaler.load_state_dict(payload["grad_scaler"])
    _restore_gradients(modules.online, payload["online_gradients"])
    _restore_gradients(modules.predictor, payload["predictor_gradients"])

    random.setstate(payload["python_rng_state"])
    np.random.set_state(payload["numpy_rng_state"])
    torch.set_rng_state(payload["torch_cpu_rng_state"])
    if torch.cuda.is_available() and payload.get("torch_cuda_rng_states") is not None:
        torch.cuda.set_rng_state_all(payload["torch_cuda_rng_states"])
    if payload.get("masking_rng_state") is not None:
        if masking_generator is None:
            raise RuntimeError("checkpoint has masking RNG but no generator was supplied")
        masking_generator.set_state(payload["masking_rng_state"])

    global_step = int(payload["global_update_step"])
    ema_count = int(payload["ema_update_count"])
    modules.ema_controller.load_bookkeeping(
        global_update_step=global_step,
        ema_update_count=ema_count,
    )
    modules.teacher.eval()
    for parameter in modules.teacher.parameters():
        parameter.requires_grad_(False)
    return {
        "global_update_step": global_step,
        "ema_update_count": ema_count,
        "schedule_cursor": int(payload["schedule_cursor"]),
        "accumulation_position": int(payload["accumulation_position"]),
    }


def save_checkpoint_atomic(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Write once, atomically. Existing checkpoint paths are immutable."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite immutable checkpoint: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp_path = Path(temporary)
    try:
        torch.save(dict(payload), temp_path)
        with temp_path.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "schema": CHECKPOINT_SCHEMA,
    }


def load_checkpoint_verified(path: Path, *, expected_sha256: str) -> dict[str, Any]:
    path = Path(path)
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise RuntimeError(
            f"checkpoint SHA-256 mismatch: expected={expected_sha256} actual={actual}"
        )
    return torch.load(path, map_location="cpu", weights_only=False)
