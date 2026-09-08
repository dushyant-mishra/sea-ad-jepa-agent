#!/usr/bin/env python3
"""Mechanics-only u0->u40 healthy-teacher qualification runner.

The runner cannot authorize itself. It requires:
1. a valid immutable execution-binding overlay; and
2. a separate explicit u0->u40 execution authority binding that overlay.

It never imports reader-validation/oracle biology, pathology, D1, F1 outcomes,
or any biological early-stopping logic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from scripts.agent.validate_healthy_teacher_execution_binding_overlay_v1 import (
    canonical_overlay_sha256,
    validate_overlay,
)
from scripts.v4.healthy_teacher_batch_source_v1 import FrozenHealthyTeacherBatchSource
from scripts.v4.healthy_teacher_loader_adapter_v1 import load_frozen_production_loader
from sea_ad_jepa.v4.teacher_student_checkpoint import (
    capture_checkpoint,
    load_checkpoint_verified,
    restore_checkpoint,
    save_checkpoint_atomic,
    sha256_file,
)
from sea_ad_jepa.v4.teacher_student_movement import enforce_module_movement
from sea_ad_jepa.v4.teacher_student_runtime import (
    F1B_ATTACK_AUTHORITY_ROOT,
    FROZEN_BACKBONE_REGISTRY,
    FROZEN_PREDICTOR_REGISTRY,
    HEALTHY_TEACHER_BASE_ROOT,
    POPULATION_ACCESS_ROOT,
    PRODUCTION_CONFIG,
    PREDICTOR_REGISTRY_SHA256,
    build_teacher_student_components,
    configure_deterministic_cuda_environment,
    production_update,
)

QUALIFICATION_UPDATES = 40
CHECKPOINT_UPDATES = {10, 25, 40}


def _sha(value: Any) -> bool:
    value = str(value)
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def validate_execution_authority(
    payload: dict[str, Any],
    *,
    overlay_sha256: str,
) -> None:
    if payload.get("schema") != "HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1":
        raise RuntimeError("qualification execution authority schema mismatch")
    if payload.get("authorized") is not True:
        raise RuntimeError("u0->u40 execution is not explicitly authorized")
    if payload.get("phase") != "U0_TO_U40" or payload.get("final_update") != 40:
        raise RuntimeError("qualification authority phase/horizon mismatch")
    if payload.get("execution_binding_overlay_sha256") != overlay_sha256:
        raise RuntimeError("qualification authority does not bind the supplied overlay")
    if payload.get("healthy_teacher_base_root") != HEALTHY_TEACHER_BASE_ROOT:
        raise RuntimeError("qualification authority base root mismatch")
    if not str(payload.get("authorization_id", "")).strip():
        raise RuntimeError("qualification authority authorization_id absent")
    if payload.get("terminal") != "AUTHORIZE_HEALTHY_TEACHER_U0_TO_U40_MECHANICAL_QUALIFICATION":
        raise RuntimeError("qualification authority terminal mismatch")


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _snapshot(parameters: dict[str, torch.nn.Parameter], names: tuple[str, ...]) -> dict[str, torch.Tensor]:
    return {name: parameters[name].detach().clone() for name in names}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--execution-authority", type=Path, required=True)
    parser.add_argument("--u0", type=Path, required=True)
    parser.add_argument("--u0-attestation", type=Path, required=True)
    parser.add_argument("--loader-source", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--authority-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--reader-split", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()

    overlay = json.loads(args.overlay.read_text(encoding="utf-8"))
    overlay_result = validate_overlay(overlay)
    if not overlay_result["terminal"].startswith("PASS_"):
        raise RuntimeError(f"invalid execution-binding overlay: {overlay_result}")
    overlay_sha = canonical_overlay_sha256(overlay)
    execution = json.loads(args.execution_authority.read_text(encoding="utf-8"))
    validate_execution_authority(execution, overlay_sha256=overlay_sha)

    if not torch.cuda.is_available():
        raise RuntimeError("healthy-teacher mechanical qualification requires CUDA")
    if args.run_dir.exists() and any(args.run_dir.iterdir()):
        raise RuntimeError("qualification run directory must be new/empty")
    args.run_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(PRODUCTION_CONFIG.training_seed)
    np.random.seed(PRODUCTION_CONFIG.training_seed)
    torch.manual_seed(PRODUCTION_CONFIG.training_seed)
    torch.cuda.manual_seed_all(PRODUCTION_CONFIG.training_seed)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)

    device = torch.device("cuda")
    modules = build_teacher_student_components(device=device)
    source_root = overlay["integrated_successor"]["source_manifest_root"]
    authorities = {
        "healthy_teacher_base_root": HEALTHY_TEACHER_BASE_ROOT,
        "population_access_root": POPULATION_ACCESS_ROOT,
        "f1b_attack_authority_root": F1B_ATTACK_AUTHORITY_ROOT,
        "integrated_successor_source_root": source_root,
        "integrated_successor_commit": overlay["integrated_successor"]["commit"],
        "predictor_mandatory_registry_sha256": PREDICTOR_REGISTRY_SHA256,
        "movement_adjudicator_source_sha256": overlay["movement_adjudicator_source_sha256"],
    }
    expected_u0_sha = overlay["successor_u0"]["sha256"]
    expected_attestation_sha = overlay["successor_u0"]["materialization_attestation_sha256"]
    if sha256_file(args.u0_attestation) != expected_attestation_sha:
        raise RuntimeError("successor u0 materialization attestation SHA-256 mismatch")
    attestation = json.loads(args.u0_attestation.read_text(encoding="utf-8"))
    if attestation.get("schema") != "HEALTHY_TEACHER_U0_MATERIALIZATION_ATTESTATION_V1":
        raise RuntimeError("successor u0 materialization attestation schema mismatch")
    if attestation.get("terminal") != "PASS_SUCCESSOR_U0_MATERIALIZATION__TRAINING_STILL_UNAUTHORIZED":
        raise RuntimeError("successor u0 materialization terminal mismatch")
    if attestation.get("training_updates_executed") != 0:
        raise RuntimeError("successor u0 materialization executed training")
    state_checks = attestation.get("state_equivalence")
    if not isinstance(state_checks, dict) or not state_checks or not all(state_checks.values()):
        raise RuntimeError("u0 materialization state-equivalence checks are incomplete")
    rng_checks = attestation.get("rng_equivalence")
    if not isinstance(rng_checks, dict) or not rng_checks or not all(rng_checks.values()):
        raise RuntimeError("u0 materialization RNG-equivalence checks are incomplete")
    if attestation.get("new_checkpoint", {}).get("sha256") != expected_u0_sha:
        raise RuntimeError("u0 attestation does not bind the overlay checkpoint SHA")
    if attestation.get("authority_bindings") != authorities:
        raise RuntimeError("u0 attestation authority bindings do not match execution overlay")
    u0_payload = load_checkpoint_verified(args.u0, expected_sha256=expected_u0_sha)
    masking = torch.Generator(device="cpu").manual_seed(PRODUCTION_CONFIG.masking_seed)
    restored = restore_checkpoint(
        u0_payload,
        modules,
        config=PRODUCTION_CONFIG,
        expected_authorities=authorities,
        masking_generator=masking,
        expected_schedule_cursor=0,
    )
    if restored["global_update_step"] != 0 or restored["ema_update_count"] != 0:
        raise RuntimeError("qualification did not start from successor u0")

    online_at_u0 = _snapshot(
        dict(modules.online.named_parameters()), FROZEN_BACKBONE_REGISTRY
    )
    predictor_at_u0 = _snapshot(
        dict(modules.predictor.named_parameters()), FROZEN_PREDICTOR_REGISTRY
    )

    loader = load_frozen_production_loader(
        loader_source=args.loader_source,
        project_root=args.project_root,
        authority_root=args.authority_root,
    )
    batches = FrozenHealthyTeacherBatchSource(
        loader=loader,
        inventory_path=args.inventory,
        schedule_path=args.schedule,
        reader_split_path=args.reader_split,
    )

    trajectory: list[dict[str, Any]] = []
    checkpoint_manifest: list[dict[str, Any]] = []
    for update in range(1, QUALIFICATION_UPDATES + 1):
        expression, measured, keys, provenance = batches.materialize(update)
        started = time.perf_counter()
        result = production_update(
            modules,
            expression=expression,
            measurement_mask=measured,
            stable_mask_keys=keys,
            schedule_cursor=update - 1,
        )
        if result["optimizer_step_after"] != update:
            raise RuntimeError("optimizer step counter diverged from update")
        row = {
            "update": update,
            "loss": result["loss"],
            "mask_sha256": result["mask_sha256"],
            "events": result["events"],
            "gradient_gate": result["gradient_gate"],
            "adam_moments": result["adam_moments"],
            "ema_equation": result["ema_equation"],
            "wall_seconds": time.perf_counter() - started,
            "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
            "batch_provenance": provenance,
        }
        trajectory.append(row)
        _write_json_atomic(args.run_dir / "qualification_trajectory.json", {
            "schema": "HEALTHY_TEACHER_U40_TRAJECTORY_V1",
            "overlay_sha256": overlay_sha,
            "execution_authority": execution["authorization_id"],
            "updates": trajectory,
        })

        if update in CHECKPOINT_UPDATES:
            payload = capture_checkpoint(
                modules,
                config=PRODUCTION_CONFIG,
                schedule_cursor=update,
                accumulation_position=0,
                masking_generator=masking,
                authority_bindings=authorities,
                phase="QUALIFICATION",
            )
            info = save_checkpoint_atomic(
                args.run_dir / f"healthy_teacher_u{update:04d}.pt", payload
            )
            checkpoint_manifest.append({"update": update, **info})
            _write_json_atomic(
                args.run_dir / "checkpoint_manifest.json",
                {
                    "schema": "HEALTHY_TEACHER_QUALIFICATION_CHECKPOINT_MANIFEST_V1",
                    "checkpoints": checkpoint_manifest,
                },
            )

    backbone_movement = enforce_module_movement(
        modules.online,
        online_at_u0,
        names=FROZEN_BACKBONE_REGISTRY,
        learning_rate=PRODUCTION_CONFIG.learning_rate,
        weight_decay=PRODUCTION_CONFIG.weight_decay,
        valid_steps=40,
    )
    predictor_movement = enforce_module_movement(
        modules.predictor,
        predictor_at_u0,
        names=FROZEN_PREDICTOR_REGISTRY,
        learning_rate=PRODUCTION_CONFIG.learning_rate,
        weight_decay=PRODUCTION_CONFIG.weight_decay,
        valid_steps=40,
    )

    u40_checkpoint = next(
        row for row in checkpoint_manifest if int(row["update"]) == 40
    )
    terminal = {
        "schema": "HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION_V1",
        "updates": 40,
        "u40_checkpoint": u40_checkpoint,
        "backbone_movement": backbone_movement,
        "predictor_movement": predictor_movement,
        "predictor_registry_sha256": PREDICTOR_REGISTRY_SHA256,
        "overlay_sha256": overlay_sha,
        "execution_authority_id": execution["authorization_id"],
        "biology_opened": False,
        "automatic_continuation_authorized": False,
        "terminal": "PASS_HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION__FULL_CONTINUATION_STILL_UNAUTHORIZED",
    }
    _write_json_atomic(args.run_dir / "U40_MECHANICAL_QUALIFICATION.json", terminal)
    print(json.dumps(terminal, indent=2, sort_keys=True))
    return 0


def guarded_main() -> int:
    try:
        return main()
    except Exception as error:
        import sys
        run_dir = None
        if "--run-dir" in sys.argv:
            index = sys.argv.index("--run-dir")
            if index + 1 < len(sys.argv):
                run_dir = Path(sys.argv[index + 1])
        if run_dir is not None:
            try:
                run_dir.mkdir(parents=True, exist_ok=True)
                _write_json_atomic(
                    run_dir / "U40_MECHANICAL_QUALIFICATION_STOP.json",
                    {
                        "schema": "HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION_STOP_V1",
                        "status": "STOP",
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "time": time.time(),
                        "automatic_continuation_authorized": False,
                    },
                )
            except Exception:
                pass
        raise


if __name__ == "__main__":
    raise SystemExit(guarded_main())
