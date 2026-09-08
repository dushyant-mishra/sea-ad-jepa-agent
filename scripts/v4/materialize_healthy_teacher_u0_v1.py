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
from pathlib import Path
from typing import Any

import torch

from sea_ad_jepa.v4.teacher_student_checkpoint import (
    capture_checkpoint,
    save_checkpoint_atomic,
    sha256_file,
)
from sea_ad_jepa.v4.teacher_student_runtime import (
    F1B_ATTACK_AUTHORITY_ROOT,
    HEALTHY_TEACHER_BASE_ROOT,
    POPULATION_ACCESS_ROOT,
    PRODUCTION_CONFIG,
    build_teacher_student_components,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-u0", type=Path, required=True)
    parser.add_argument("--integrated-source-root", required=True)
    parser.add_argument("--output-checkpoint", type=Path, required=True)
    parser.add_argument("--attestation", type=Path, required=True)
    args = parser.parse_args()

    if len(args.integrated_source_root) != 64:
        raise RuntimeError("integrated source root must be SHA-256")
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

    device = torch.device("cuda")
    modules = build_teacher_student_components(device=device)
    modules.online.load_state_dict(historical["online_encoder"], strict=True)
    modules.teacher.load_state_dict(historical["target_encoder"], strict=True)
    modules.predictor.load_state_dict(historical["predictor"], strict=True)
    modules.optimizer.load_state_dict(historical["optimizer"])
    modules.scaler.load_state_dict(historical["scaler"])
    modules.ema_controller.load_bookkeeping(global_update_step=0, ema_update_count=0)

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
    }
    if not all(checks.values()):
        raise RuntimeError(f"historical u0 compatibility failure: {checks}")

    masking = torch.Generator(device="cpu").manual_seed(PRODUCTION_CONFIG.masking_seed)
    authority_bindings = {
        "healthy_teacher_base_root": HEALTHY_TEACHER_BASE_ROOT,
        "population_access_root": POPULATION_ACCESS_ROOT,
        "f1b_attack_authority_root": F1B_ATTACK_AUTHORITY_ROOT,
        "integrated_successor_source_root": args.integrated_source_root,
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
