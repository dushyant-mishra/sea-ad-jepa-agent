#!/usr/bin/env python3
"""Validate HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1.

The overlay binds a reviewed integrated implementation and successor-bound u0 to
the immutable healthy-teacher base. It is deliberately NOT permission to run.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sea_ad_jepa.v4.teacher_student_movement import source_sha256 as movement_source_sha256

BASE_ROOT = "9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534"
PREDICTOR_REGISTRY_SHA256 = "43922a62a885cbedee22c06363a8355c6561dad43c95f0a43147fc2f4cbe3592"


def _sha(value: Any) -> bool:
    value = str(value)
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _commit(value: Any) -> bool:
    value = str(value)
    return len(value) == 40 and all(ch in "0123456789abcdef" for ch in value)


def validate_overlay(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if payload.get("schema") != "HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1":
        failures.append("schema mismatch")
    if payload.get("healthy_teacher_base_package_root") != BASE_ROOT:
        failures.append("healthy-teacher base root mismatch")
    if payload.get("may_modify_base_contract") is not False:
        failures.append("overlay may not modify frozen base")
    if payload.get("overlay_itself_is_execution_authority") is not False:
        failures.append("overlay may not authorize execution")

    successor = payload.get("integrated_successor", {})
    if not _commit(successor.get("commit")):
        failures.append("integrated successor commit invalid")
    if not _sha(successor.get("source_manifest_root")):
        failures.append("integrated successor source root invalid")

    review = payload.get("independent_review", {})
    if not str(review.get("terminal", "")).startswith(
        "PASS_HEALTHY_TEACHER_INTEGRATED_SUCCESSOR_INDEPENDENT_REVIEW"
    ):
        failures.append("integrated successor independent PASS absent")
    if not _sha(review.get("artifact_sha256")):
        failures.append("independent review artifact SHA invalid")
    if review.get("reviewed_commit") != successor.get("commit"):
        failures.append("external review commit does not equal integrated successor")

    init = payload.get("successor_u0", {})
    if not str(init.get("path", "")):
        failures.append("successor u0 path absent")
    for key in ("sha256", "materialization_attestation_sha256"):
        if not _sha(init.get(key)):
            failures.append(f"successor u0 {key} invalid")
    if init.get("schedule_cursor") != 0:
        failures.append("successor u0 schedule cursor must be zero")
    if init.get("global_update_step") != 0 or init.get("ema_update_count") != 0:
        failures.append("successor u0 optimizer/EMA counters must be zero")
    if init.get("frozen_before_u1") is not True:
        failures.append("successor u0 must freeze before u1")

    if payload.get("predictor_mandatory_registry_sha256") != PREDICTOR_REGISTRY_SHA256:
        failures.append("predictor registry SHA mismatch")
    movement_sha = payload.get("movement_adjudicator_source_sha256")
    if not _sha(movement_sha):
        failures.append("movement adjudicator source SHA invalid")
    elif movement_sha != movement_source_sha256():
        failures.append("movement adjudicator source SHA does not match executing source bytes")

    if payload.get("execution_authorized") is not False:
        failures.append("binding overlay must keep execution_authorized=false")
    if payload.get("terminal") != (
        "PASS_HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY__EXECUTION_STILL_UNAUTHORIZED"
    ):
        failures.append("overlay terminal mismatch")

    return {
        "schema": "healthy-teacher-execution-binding-overlay-validation-v1",
        "failures": failures,
        "terminal": (
            "PASS_HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY__EXECUTION_STILL_UNAUTHORIZED"
            if not failures
            else "STOP_HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_INVALID"
        ),
    }


def canonical_overlay_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.overlay.read_text(encoding="utf-8"))
    result = validate_overlay(payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["terminal"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
