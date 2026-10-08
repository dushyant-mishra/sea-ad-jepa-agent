#!/usr/bin/env python3
"""Prospective V75 promotion gate from the exact 2K smoke to 100K only.

This validator cannot authorize 500K, full-scale materialization, real JEPA training,
Stage-4 correspondence, Morabito, or recoverability TEST.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL_FREEZE = ROOT / "results/v75/V75_CONTROL_TWIN_FREEZE_V1.json"
CONTRACT = ROOT / "results/v75/V75_100K_ARCHITECTURE_QUALIFICATION_CONTRACT_V1.json"


def validate(legacy: dict, controls: dict, boundary: dict, resource: dict) -> dict:
    freeze = json.loads(CONTROL_FREEZE.read_text())
    contract = json.loads(CONTRACT.read_text())
    checks = {}
    blockers = []

    def check(name: str, holds: bool, blocker: str) -> None:
        checks[name] = bool(holds)
        if not holds and blocker not in blockers:
            blockers.append(blocker)

    check(
        "prospective_contract_frozen",
        contract.get("status") == "FROZEN_PROSPECTIVE__NO_100K_OUTCOME_INSPECTED",
        "V75_CONTRACT_NOT_FROZEN",
    )
    check(
        "control_freeze_prospective",
        freeze.get("status") == "FROZEN_PROSPECTIVE__BEFORE_CONTROL_OUTCOME_INSPECTION",
        "CONTROL_FREEZE_INVALID",
    )
    check(
        "legacy_v74_ready_for_100k_only",
        legacy.get("status") == "READY_FOR_100K_STRESS_ONLY"
        and legacy.get("authorized_scale") == "100K_STRESS_ONLY"
        and not legacy.get("blockers"),
        "V74_READINESS_FAILED",
    )
    check(
        "control_worlds_materialized",
        controls.get("status") == "SYNTHETIC_CONTROL_MATERIALIZED__NO_MODEL_QUALIFICATION",
        "CONTROL_MATERIALIZATION_FAILED",
    )
    check(
        "smoke_scale_exact",
        controls.get("n_cells_per_world") == contract.get("smoke_scale") == 2000,
        "WRONG_SMOKE_SCALE",
    )

    null_freeze = freeze["measurement_null"]
    pos_freeze = freeze["biology_positive"]
    null = controls.get("measurement_null", {})
    pos = controls.get("biology_positive", {})
    check("truth_seed_frozen", controls.get("truth_seed") == freeze.get("truth_seed") == 7302, "TRUTH_SEED_DRIFT")
    check("measurement_seed_a_frozen", null.get("world_a_measurement_seed") == null_freeze.get("world_a_measurement_seed") == 8501, "MEASUREMENT_SEED_A_DRIFT")
    check("measurement_seed_b_frozen", null.get("world_b_measurement_seed") == null_freeze.get("world_b_measurement_seed") == 8502, "MEASUREMENT_SEED_B_DRIFT")
    check("positive_measurement_seed_matched", pos.get("measurement_seed") == pos_freeze.get("measurement_seed") == 8501, "POSITIVE_MEASUREMENT_SEED_DRIFT")
    check("positive_target_modulo_frozen", pos.get("target_modulo") == pos_freeze.get("target_modulo") == 4, "POSITIVE_TARGET_MODULO_DRIFT")
    check("positive_target_remainder_frozen", pos.get("target_remainder") == pos_freeze.get("target_remainder") == 0, "POSITIVE_TARGET_REMAINDER_DRIFT")
    check("positive_delta_frozen", float(pos.get("delta_z_global_0", float("nan"))) == float(pos_freeze.get("delta_z_global_0")) == 1.0, "POSITIVE_DELTA_DRIFT")
    claim = controls.get("claim_boundary", {})
    check("no_learned_160d_claim", claim.get("learned_160d_jepa_evaluated") is False, "UNSUPPORTED_160D_CLAIM")
    check("no_biological_claim", claim.get("biological_claim_qualified") is False, "UNSUPPORTED_BIOLOGICAL_CLAIM")

    check(
        "protected_boundaries_machine_validated",
        boundary.get("status") == "PASS__PROTECTED_BOUNDARIES_HOLD" and not boundary.get("blockers"),
        "PROTECTED_BOUNDARY_VALIDATION_FAILED",
    )

    est = resource.get("estimate", {})
    measured = resource.get("measured", {})
    proj = resource.get("calibrated_projection", {})
    check("resource_target_is_100k", est.get("n_cells") == 100000, "RESOURCE_TARGET_NOT_100K")
    check("resource_has_measured_2k_calibration", measured.get("n_cells") == 2000 and measured.get("fragment_bytes_per_cell", 0) > 0, "RESOURCE_2K_CALIBRATION_MISSING")
    check("resource_calibration_scoped", proj.get("calibration_is_ci_scale_only") is True, "RESOURCE_SCOPE_INVALID")
    check("resource_requires_100k_before_500k", proj.get("requires_100k_measurement_before_500k_promotion") is True, "RESOURCE_PROMOTION_GUARD_MISSING")
    check("full_ecosystem_not_falsely_estimated", est.get("full_ecosystem_total_is_not_yet_estimated") is True, "RESOURCE_SCOPE_OVERCLAIM")

    status = "READY_FOR_100K_MEASUREMENT_ARCHITECTURE_STRESS_ONLY" if not blockers else "BLOCKED"
    return {
        "schema": "V75_100K_PROMOTION_READINESS_V1",
        "status": status,
        "authorized_scale": "100K_STRESS_ONLY" if not blockers else "CI_ONLY",
        "learned_160d_jepa_state_qualified": False,
        "explicitly_not_authorized": [
            "500K_STRESS",
            "FULL_4553407",
            "REAL_JEPA_TRAINING",
            "MULTIMODAL_TRAINING",
            "STAGE4_REAL_CORRESPONDENCE",
            "RECOVERABILITY_TEST",
            "MORABITO_OPENING",
        ],
        "checks": checks,
        "blockers": blockers,
        "claim_scope": "100K synthetic population/measurement architecture stress only; no learned 160-D state or biological qualification",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy-readiness", required=True)
    ap.add_argument("--controls", required=True)
    ap.add_argument("--boundary", required=True)
    ap.add_argument("--resource", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    inputs = [json.loads(Path(p).read_text()) for p in [a.legacy_readiness, a.controls, a.boundary, a.resource]]
    result = validate(*inputs)
    text = json.dumps(result, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text, end="")
    return 0 if result["status"].startswith("READY") else 2


if __name__ == "__main__":
    raise SystemExit(main())
