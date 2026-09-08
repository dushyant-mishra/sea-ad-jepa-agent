#!/usr/bin/env python3
"""Mechanics-only u40->u205 continuation for the unified healthy teacher.

This runner cannot authorize itself.  It requires a frozen execution-binding
overlay, a hash-bound u40 qualification result/checkpoint, an independent PASS
over that exact u40 evidence, and a distinct continuation execution authority.
No biological/readout data are imported or consulted.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

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
from sea_ad_jepa.v4.teacher_student_runtime import (
    F1B_ATTACK_AUTHORITY_ROOT,
    HEALTHY_TEACHER_BASE_ROOT,
    POPULATION_ACCESS_ROOT,
    PREDICTOR_REGISTRY_SHA256,
    PRODUCTION_CONFIG,
    build_teacher_student_components,
    production_update,
)

FINAL_UPDATE = 205
CHECKPOINT_UPDATES = {50, 100, 200, 205}


def _hex(value: Any, length: int) -> bool:
    text = str(value)
    return len(text) == length and all(ch in "0123456789abcdef" for ch in text)


def validate_continuation_authority(
    payload: dict[str, Any],
    *,
    overlay_sha256: str,
    u40_checkpoint_sha256: str,
    u40_qualification_sha256: str,
) -> None:
    if payload.get("schema") != "HEALTHY_TEACHER_U40_U205_CONTINUATION_AUTHORITY_V1":
        raise RuntimeError("continuation execution authority schema mismatch")
    if payload.get("authorized") is not True:
        raise RuntimeError("u40->u205 continuation is not explicitly authorized")
    if payload.get("phase") != "U40_TO_U205" or payload.get("final_update") != FINAL_UPDATE:
        raise RuntimeError("continuation authority phase/horizon mismatch")
    if payload.get("execution_binding_overlay_sha256") != overlay_sha256:
        raise RuntimeError("continuation authority does not bind supplied overlay")
    if payload.get("healthy_teacher_base_root") != HEALTHY_TEACHER_BASE_ROOT:
        raise RuntimeError("continuation authority base root mismatch")
    if payload.get("u40_checkpoint_sha256") != u40_checkpoint_sha256:
        raise RuntimeError("continuation authority u40 checkpoint mismatch")
    if payload.get("u40_qualification_sha256") != u40_qualification_sha256:
        raise RuntimeError("continuation authority u40 qualification mismatch")

    review = payload.get("u40_independent_review") or {}
    if not str(review.get("terminal", "")).startswith(
        "PASS_HEALTHY_TEACHER_U40_INDEPENDENT_REVIEW"
    ):
        raise RuntimeError("independent u40 review PASS absent")
    if not _hex(review.get("artifact_sha256"), 64):
        raise RuntimeError("u40 independent-review artifact SHA invalid")
    if review.get("reviewed_checkpoint_sha256") != u40_checkpoint_sha256:
        raise RuntimeError("u40 review did not bind exact continuation checkpoint")
    if review.get("reviewed_qualification_sha256") != u40_qualification_sha256:
        raise RuntimeError("u40 review did not bind exact qualification result")

    if not str(payload.get("authorization_id", "")).strip():
        raise RuntimeError("continuation authorization_id absent")
    if payload.get("terminal") != (
        "AUTHORIZE_HEALTHY_TEACHER_U40_TO_U205_MECHANICS_CONTINUATION"
    ):
        raise RuntimeError("continuation authority terminal mismatch")


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--continuation-authority", type=Path, required=True)
    parser.add_argument("--u40-checkpoint", type=Path, required=True)
    parser.add_argument("--u40-qualification", type=Path, required=True)
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

    u40_sha = sha256_file(args.u40_checkpoint)
    qualification_sha = sha256_file(args.u40_qualification)
    qualification = json.loads(args.u40_qualification.read_text(encoding="utf-8"))
    if qualification.get("schema") != "HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION_V1":
        raise RuntimeError("u40 qualification schema mismatch")
    if qualification.get("terminal") != (
        "PASS_HEALTHY_TEACHER_U40_MECHANICAL_QUALIFICATION__FULL_CONTINUATION_STILL_UNAUTHORIZED"
    ):
        raise RuntimeError("u40 mechanical qualification is not PASS")
    if qualification.get("updates") != 40 or qualification.get("biology_opened") is not False:
        raise RuntimeError("u40 qualification scope/biology firewall mismatch")
    if qualification.get("automatic_continuation_authorized") is not False:
        raise RuntimeError("u40 result incorrectly self-authorizes continuation")
    if qualification.get("overlay_sha256") != overlay_sha:
        raise RuntimeError("u40 result does not bind supplied execution overlay")
    if qualification.get("u40_checkpoint", {}).get("sha256") != u40_sha:
        raise RuntimeError("u40 qualification does not bind supplied checkpoint")

    authority = json.loads(args.continuation_authority.read_text(encoding="utf-8"))
    validate_continuation_authority(
        authority,
        overlay_sha256=overlay_sha,
        u40_checkpoint_sha256=u40_sha,
        u40_qualification_sha256=qualification_sha,
    )

    if not torch.cuda.is_available():
        raise RuntimeError("healthy-teacher continuation requires CUDA")
    if args.run_dir.exists() and any(args.run_dir.iterdir()):
        raise RuntimeError("continuation run directory must be new/empty")
    args.run_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)

    modules = build_teacher_student_components(device=torch.device("cuda"))
    authorities = {
        "healthy_teacher_base_root": HEALTHY_TEACHER_BASE_ROOT,
        "population_access_root": POPULATION_ACCESS_ROOT,
        "f1b_attack_authority_root": F1B_ATTACK_AUTHORITY_ROOT,
        "integrated_successor_source_root": overlay["integrated_successor"]["source_manifest_root"],
        "integrated_successor_commit": overlay["integrated_successor"]["commit"],
        "predictor_mandatory_registry_sha256": PREDICTOR_REGISTRY_SHA256,
        "movement_adjudicator_source_sha256": overlay["movement_adjudicator_source_sha256"],
    }
    masking = torch.Generator(device="cpu").manual_seed(PRODUCTION_CONFIG.masking_seed)
    checkpoint = load_checkpoint_verified(args.u40_checkpoint, expected_sha256=u40_sha)
    restored = restore_checkpoint(
        checkpoint,
        modules,
        config=PRODUCTION_CONFIG,
        expected_authorities=authorities,
        masking_generator=masking,
        expected_schedule_cursor=40,
    )
    if restored["global_update_step"] != 40 or restored["ema_update_count"] != 40:
        raise RuntimeError("continuation did not restore exact u40 state")

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
    for update in range(41, FINAL_UPDATE + 1):
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
            raise RuntimeError("optimizer step counter diverged from continuation update")
        trajectory.append(
            {
                "update": update,
                "loss": result["loss"],
                "mask_sha256": result["mask_sha256"],
                "events": result["events"],
                "gradient_gate": result["gradient_gate"],
                "adam_moments": result["adam_moments"],
                "ema_equation": result["ema_equation"],
                "wall_seconds": time.perf_counter() - started,
                "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved()),
                "batch_provenance": provenance,
            }
        )
        _write_json_atomic(
            args.run_dir / "continuation_trajectory.json",
            {
                "schema": "HEALTHY_TEACHER_U205_CONTINUATION_TRAJECTORY_V1",
                "overlay_sha256": overlay_sha,
                "continuation_authorization_id": authority["authorization_id"],
                "updates": trajectory,
            },
        )

        if update in CHECKPOINT_UPDATES:
            payload = capture_checkpoint(
                modules,
                config=PRODUCTION_CONFIG,
                schedule_cursor=update,
                accumulation_position=0,
                masking_generator=masking,
                authority_bindings=authorities,
                phase="CONTINUATION",
            )
            info = save_checkpoint_atomic(
                args.run_dir / f"healthy_teacher_u{update:04d}.pt", payload
            )
            checkpoint_manifest.append({"update": update, **info})
            _write_json_atomic(
                args.run_dir / "checkpoint_manifest.json",
                {
                    "schema": "HEALTHY_TEACHER_CONTINUATION_CHECKPOINT_MANIFEST_V1",
                    "checkpoints": checkpoint_manifest,
                },
            )

    final_checkpoint = next(
        row for row in checkpoint_manifest if int(row["update"]) == FINAL_UPDATE
    )
    terminal = {
        "schema": "HEALTHY_TEACHER_U205_TRAINING_COMPLETE_V1",
        "updates": FINAL_UPDATE,
        "start_checkpoint_sha256": u40_sha,
        "u40_qualification_sha256": qualification_sha,
        "final_checkpoint": final_checkpoint,
        "overlay_sha256": overlay_sha,
        "continuation_authority_id": authority["authorization_id"],
        "biology_opened": False,
        "d1_authorized": False,
        "terminal": (
            "TRAINING_COMPLETE_U205__CHECKPOINT_MUST_BE_FROZEN_AND_INDEPENDENTLY_QUALIFIED_BEFORE_D1"
        ),
    }
    _write_json_atomic(args.run_dir / "U205_TRAINING_COMPLETE.json", terminal)
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
                    run_dir / "U205_CONTINUATION_STOP.json",
                    {
                        "schema": "HEALTHY_TEACHER_U205_CONTINUATION_STOP_V1",
                        "status": "STOP",
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "time": time.time(),
                        "d1_authorized": False,
                    },
                )
            except Exception:
                pass
        raise


if __name__ == "__main__":
    raise SystemExit(guarded_main())
