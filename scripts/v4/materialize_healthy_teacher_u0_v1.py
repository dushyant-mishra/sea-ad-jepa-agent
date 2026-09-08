#!/usr/bin/env python3
"""Materialize the new successor-bound u0 from the clean historical u0 reference.

This performs no optimizer update. It requires exact state-schema compatibility
and proves equality for every imported model/optimizer/scaler state before
writing a new checkpoint bound to the unified production implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch

from sea_ad_jepa.v4.teacher_student_checkpoint import (
    capture_checkpoint,
    save_checkpoint_atomic,
    sha256_file,
)
from sea_ad_jepa.v4.teacher_student_movement import source_sha256 as movement_source_sha256
from sea_ad_jepa.v4.teacher_student_runtime import (
    F1B_ATTACK_AUTHORITY_ROOT,
    HEALTHY_TEACHER_BASE_ROOT,
    POPULATION_ACCESS_ROOT,
    PREDICTOR_REGISTRY_SHA256,
    PRODUCTION_CONFIG,
    build_teacher_student_components,
    configure_deterministic_cuda_environment,
)

HISTORICAL_U0_SHA256 = "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4"


def _state_equal(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    if set(expected) != set(observed):
        return False
    for key in expected:
        a, b = expected[key], observed[key]
        if isinstance(a, torch.Tensor):
            if not isinstance(b, torch.Tensor) or not torch.equal(a.cpu(), b.cpu()):
                return False
        elif isinstance(a, dict):
            if not isinstance(b, dict) or not _state_equal(a, b):
                return False
        elif isinstance(a, (list, tuple)):
            if type(a) is not type(b) or len(a) != len(b):
                return False
            for x, y in zip(a, b):
                if isinstance(x, torch.Tensor):
                    if not isinstance(y, torch.Tensor) or not torch.equal(x.cpu(), y.cpu()):
                        return False
                elif x != y:
                    return False
        elif a != b:
            return False
    return True


def _numpy_rng_equal(a: Any, b: Any) -> bool:
    if not isinstance(a, tuple) or not isinstance(b, tuple) or len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if isinstance(x, np.ndarray):
            if not isinstance(y, np.ndarray) or not np.array_equal(x, y):
                return False
        elif x != y:
            return False
    return True


def _gradient_state_equal(expected: dict[str, Any], module: torch.nn.Module) -> bool:
    observed = {name: p.grad for name, p in module.named_parameters()}
    if set(expected) != set(observed):
        return False
    for name, old in expected.items():
        new = observed[name]
        if old is None:
            if new is not None:
                return False
        elif new is None or not torch.equal(old.cpu(), new.detach().cpu()):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-u0", type=Path, required=True)
    parser.add_argument("--integrated-source-root", required=True)
    parser.add_argument("--integrated-commit", required=True)
    parser.add_argument("--movement-adjudicator-sha256", required=True)
    parser.add_argument("--output-checkpoint", type=Path, required=True)
    parser.add_argument("--attestation", type=Path, required=True)
    args = parser.parse_args()

    def _hex(value: str, length: int) -> bool:
        return len(value) == length and all(ch in "0123456789abcdef" for ch in value)

    if not _hex(args.integrated_source_root, 64):
        raise RuntimeError("integrated source root must be SHA-256")
    if not _hex(args.integrated_commit, 40):
        raise RuntimeError("integrated successor commit must be a full git SHA")
    if not _hex(args.movement_adjudicator_sha256, 64):
        raise RuntimeError("movement adjudicator source must be SHA-256")
    if args.movement_adjudicator_sha256 != movement_source_sha256():
        raise RuntimeError("movement adjudicator SHA does not match executing source bytes")
    if sha256_file(args.historical_u0) != HISTORICAL_U0_SHA256:
        raise RuntimeError("historical clean u0 SHA-256 mismatch")
    if not torch.cuda.is_available():
        raise RuntimeError("successor u0 must materialize in the CUDA qualification environment")

    historical = torch.load(args.historical_u0, map_location="cpu", weights_only=False)
    if int(historical.get("schedule_cursor", -1)) != 0:
        raise RuntimeError("historical u0 schedule cursor is not zero")
    if int(historical.get("global_update_step", -1)) != 0:
        raise RuntimeError("historical u0 global step is not zero")
    if int(historical.get("ema_update_count", -1)) != 0:
        raise RuntimeError("historical u0 EMA count is not zero")

    configure_deterministic_cuda_environment()

    device = torch.device("cuda")
    modules = build_teacher_student_components(device=device)
    modules.online.load_state_dict(historical["online_encoder"], strict=True)
    modules.teacher.load_state_dict(historical["target_encoder"], strict=True)
    modules.predictor.load_state_dict(historical["predictor"], strict=True)
    modules.optimizer.load_state_dict(historical["optimizer"])
    modules.scaler.load_state_dict(historical["scaler"])
    modules.ema_controller.load_bookkeeping(global_update_step=0, ema_update_count=0)

    # Historical u0 is a clean state source, including RNG state.  Component
    # construction consumes RNG, so restore the exact historical states only
    # after all module/state loading is complete and before successor u0 capture.
    random.setstate(historical["python_rng_state"])
    np.random.set_state(historical["numpy_rng_state"])
    torch.set_rng_state(historical["torch_cpu_rng_state"])
    historical_cuda_rng = historical.get("torch_cuda_rng_states")
    if historical_cuda_rng is None:
        raise RuntimeError("historical u0 CUDA RNG state absent")
    if len(historical_cuda_rng) != torch.cuda.device_count():
        raise RuntimeError("historical u0 CUDA RNG device-count mismatch")
    torch.cuda.set_rng_state_all(historical_cuda_rng)

    checks = {
        "online_encoder": _state_equal(
            historical["online_encoder"], modules.online.state_dict()
        ),
        "teacher": _state_equal(
            historical["target_encoder"], modules.teacher.state_dict()
        ),
        "predictor": _state_equal(
            historical["predictor"], modules.predictor.state_dict()
        ),
        "optimizer": _state_equal(
            historical["optimizer"], modules.optimizer.state_dict()
        ),
        "grad_scaler": historical["scaler"] == modules.scaler.state_dict(),
        "online_gradients": _gradient_state_equal(
            historical["online_gradients"], modules.online
        ),
        "predictor_gradients": _gradient_state_equal(
            historical["predictor_gradients"], modules.predictor
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"historical u0 compatibility failure: {checks}")

    masking = torch.Generator(device="cpu")
    masking.set_state(historical["masking_rng_state"])
    rng_checks = {
        "python_rng_state": random.getstate() == historical["python_rng_state"],
        "numpy_rng_state": _numpy_rng_equal(np.random.get_state(), historical["numpy_rng_state"]),
        "torch_cpu_rng_state": torch.equal(torch.get_rng_state(), historical["torch_cpu_rng_state"]),
        "torch_cuda_rng_states": all(
            torch.equal(a.cpu(), b.cpu())
            for a, b in zip(torch.cuda.get_rng_state_all(), historical_cuda_rng)
        ),
        "masking_rng_state": torch.equal(masking.get_state(), historical["masking_rng_state"]),
    }
    if not all(rng_checks.values()):
        raise RuntimeError(f"historical u0 RNG compatibility failure: {rng_checks}")
    authority_bindings = {
        "healthy_teacher_base_root": HEALTHY_TEACHER_BASE_ROOT,
        "population_access_root": POPULATION_ACCESS_ROOT,
        "f1b_attack_authority_root": F1B_ATTACK_AUTHORITY_ROOT,
        "integrated_successor_source_root": args.integrated_source_root,
        "integrated_successor_commit": args.integrated_commit,
        "predictor_mandatory_registry_sha256": PREDICTOR_REGISTRY_SHA256,
        "movement_adjudicator_source_sha256": args.movement_adjudicator_sha256,
    }
    payload = capture_checkpoint(
        modules,
        config=PRODUCTION_CONFIG,
        schedule_cursor=0,
        accumulation_position=0,
        masking_generator=masking,
        authority_bindings=authority_bindings,
        phase="U0",
    )
    written = save_checkpoint_atomic(args.output_checkpoint, payload)

    attestation = {
        "schema": "HEALTHY_TEACHER_U0_MATERIALIZATION_ATTESTATION_V1",
        "historical_u0_sha256": HISTORICAL_U0_SHA256,
        "new_checkpoint": written,
        "state_equivalence": checks,
        "rng_equivalence": rng_checks,
        "config_sha256": PRODUCTION_CONFIG.digest(),
        "authority_bindings": authority_bindings,
        "training_updates_executed": 0,
        "terminal": "PASS_SUCCESSOR_U0_MATERIALIZATION__TRAINING_STILL_UNAUTHORIZED",
    }
    if args.attestation.exists():
        raise FileExistsError("refusing to overwrite u0 materialization attestation")
    args.attestation.parent.mkdir(parents=True, exist_ok=True)
    args.attestation.write_text(
        json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(attestation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
