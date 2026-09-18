#!/usr/bin/env python3
"""Evaluate exactly one target-panel capacity rung from the calibration-only cache."""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.control_calibration_precision_authority_v1 import (
    ControlCalibrationPrecisionPlanV1,
)
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import (
    ControlCapacityCalibrationReceiptV1,
)
from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.full104_control_calibration_cache_evaluator_v1 import (
    evaluate_linear_capacity_rung,
    load_control_calibration_cache,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v2 import (
    MaskingQualificationParametersAuthorityV2,
)
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import (
    TargetPanelControlVerdictV2,
    TargetPanelSizingPlanAuthorityV2,
    TargetPanelSizingReceiptV2,
)

SEED_NAMESPACE = "JEPA_V5_FULL104_PANEL_CAPACITY_CACHE_SHUFFLE_V1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_parameters(path: Path) -> MaskingQualificationParametersAuthorityV2:
    payload = load_json(path)
    if payload.get("schema") != "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V2":
        raise SystemExit("parameter authority schema mismatch")
    names = {field.name for field in fields(MaskingQualificationParametersAuthorityV2)}
    authority = MaskingQualificationParametersAuthorityV2(
        **{name: payload[name] for name in names}
    )
    authority.validate()
    declared = payload.get("parameter_authority_sha256")
    if declared != authority.canonical_digest():
        raise SystemExit("parameter authority digest mismatch")
    return authority


def load_prior_verdicts(paths: list[Path]) -> dict[int, TargetPanelControlVerdictV2]:
    out: dict[int, TargetPanelControlVerdictV2] = {}
    names = {field.name for field in fields(TargetPanelControlVerdictV2)}
    for path in paths:
        payload = load_json(path)
        if payload.get("schema") != "V5_TARGET_PANEL_CONTROL_VERDICT_V2":
            raise SystemExit(f"{path}: target-panel verdict schema mismatch")
        verdict = TargetPanelControlVerdictV2(
            **{name: payload[name] for name in names}
        )
        verdict.validate()
        if payload.get("verdict_sha256") != verdict.canonical_digest():
            raise SystemExit(f"{path}: target-panel verdict digest mismatch")
        if verdict.target_count in out:
            raise SystemExit("duplicate target-panel verdict rung")
        out[verdict.target_count] = verdict
    return dict(sorted(out.items()))


def seed_from_cache(cache_manifest_sha256: str) -> int:
    raw = f"{SEED_NAMESPACE}|{cache_manifest_sha256}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=False)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache-dir", type=Path, required=True)
    p.add_argument("--parameters-authority", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--workers", type=int, required=True)
    p.add_argument("--prior-verdict", type=Path, action="append", default=[])
    p.add_argument("--replay-planted", type=Path)
    p.add_argument("--replay-shuffled", type=Path)
    args = p.parse_args()

    cache = load_control_calibration_cache(args.cache_dir)
    cache.manifest.assert_calibration_only()
    parameters = load_parameters(args.parameters_authority)
    prior = load_prior_verdicts(args.prior_verdict)

    plan = TargetPanelSizingPlanAuthorityV2(
        authority_id="JEPA_V5_FULL104_TARGET_PANEL_SIZING_PLAN_V2",
        census_authority_sha256=cache.manifest.census_authority_sha256,
        target_eligibility_receipt_sha256=cache.manifest.target_eligibility_receipt_sha256,
        independent_donor_count=104,
        eligible_target_count=17053,
    )
    plan.validate()
    target_count = plan.next_target_count(prior)

    precision = ControlCalibrationPrecisionPlanV1(
        authority_id="JEPA_V5_FULL104_CONTROL_CALIBRATION_PRECISION_V1",
        census_authority_sha256=cache.manifest.census_authority_sha256,
        support_estimability_authority_sha256=cache.manifest.support_estimability_authority_sha256,
        target_eligibility_receipt_sha256=cache.manifest.target_eligibility_receipt_sha256,
        outer_split_authority_sha256=cache.manifest.split_receipt_sha256,
    )
    precision.validate()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"target_panel_{target_count}"
    global_seed = seed_from_cache(cache.manifest_sha256)
    planted, shuffled = evaluate_linear_capacity_rung(
        cache,
        target_count=target_count,
        ridge_alpha=float(parameters.ridge_alpha),
        global_seed=global_seed,
        workers=args.workers,
    )
    planted_path = args.out_dir / f"{prefix}.planted_f64.npy"
    shuffled_path = args.out_dir / f"{prefix}.shuffled_f64.npy"
    np.save(planted_path, planted, allow_pickle=False)
    np.save(shuffled_path, shuffled, allow_pickle=False)

    status = {
        "schema": "V5_TARGET_PANEL_CAPACITY_CALIBRATION_CACHE_RUN_V1",
        "cache_manifest_sha256": cache.manifest_sha256,
        "cache_role_id": cache.manifest.cache_role_id,
        "target_count": target_count,
        "parameters_authority_sha256": parameters.canonical_digest(),
        "precision_plan_sha256": precision.canonical_digest(),
        "planted_matrix_sha256": sha256_file(planted_path),
        "shuffled_matrix_sha256": sha256_file(shuffled_path),
        "workers": args.workers,
        "terminal_masking_policy_outcomes_inspected": False,
        "terminal_masking_qualification_authorized": False,
        "training_authorized": False,
    }

    if (args.replay_planted is None) != (args.replay_shuffled is None):
        raise SystemExit("both replay matrices must be supplied together")
    if args.replay_planted is None:
        status["status"] = "REPLAY_REQUIRED_BEFORE_CAPACITY_VERDICT"
        write_json(args.out_dir / f"{prefix}.status.json", status)
        print(json.dumps(status, sort_keys=True))
        return 3

    replay_planted = np.load(args.replay_planted, allow_pickle=False)
    replay_shuffled = np.load(args.replay_shuffled, allow_pickle=False)
    if not np.array_equal(planted, replay_planted):
        raise SystemExit("planted capacity replay mismatch")
    if not np.array_equal(shuffled, replay_shuffled):
        raise SystemExit("shuffled capacity replay mismatch")

    difference = planted - shuffled
    interval = precision.interval(
        difference,
        cache.donor_source_code,
        target_count=target_count,
    )
    capacity = ControlCapacityCalibrationReceiptV1(
        scope_id="TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1",
        candidate_value=target_count,
        calibration_cache_manifest_sha256=cache.manifest_sha256,
        calibration_cache_role_id=cache.manifest.cache_role_id,
        raw_planted_evidence_sha256=sha256_file(planted_path),
        raw_shuffled_evidence_sha256=sha256_file(shuffled_path),
        precision_root_sha256=precision.canonical_digest(),
        planted_minus_shuffled_mean=float(interval.mean),
        planted_minus_shuffled_lower_one_sided=float(interval.lower_one_sided),
        donor_count=104,
        target_count=target_count,
        bootstrap_replicates=precision.bootstrap_replicates,
        confidence_level_numerator=precision.confidence_level_numerator,
        confidence_level_denominator=precision.confidence_level_denominator,
        replay_exact=True,
    )
    capacity.validate()
    capacity_payload = {
        "schema": "V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1",
        **capacity.__dict__,
        "detects_planted_shortcut": capacity.detects_planted_shortcut,
        "receipt_sha256": capacity.canonical_digest(),
    }
    write_json(args.out_dir / f"{prefix}.capacity_receipt.json", capacity_payload)

    verdict = TargetPanelControlVerdictV2(
        target_count=target_count,
        capacity_receipt_sha256=capacity.canonical_digest(),
        planted_minus_shuffled_lower_one_sided=float(interval.lower_one_sided),
        replay_exact=True,
        donor_coverage_complete=bool(np.all(np.isfinite(difference))),
        bootstrap_finite=bool(
            np.isfinite(interval.mean)
            and np.isfinite(interval.lower_one_sided)
            and np.isfinite(interval.upper_one_sided)
        ),
    )
    verdict.bind_capacity_receipt(capacity)
    verdict_payload = {
        "schema": "V5_TARGET_PANEL_CONTROL_VERDICT_V2",
        **verdict.__dict__,
        "qualified": verdict.qualified,
        "verdict_sha256": verdict.canonical_digest(),
    }
    write_json(args.out_dir / f"{prefix}.verdict.json", verdict_payload)

    combined = dict(prior)
    combined[target_count] = verdict
    selected = plan.select(combined)
    if selected is not None:
        receipt = TargetPanelSizingReceiptV2(
            plan_authority_sha256=plan.canonical_digest(),
            selected_target_count=selected,
            evaluated_counts=tuple(combined),
            verdict_digest_by_count={
                count: value.canonical_digest() for count, value in combined.items()
            },
        )
        receipt.bind_verdicts(plan, combined)
        payload = {
            "schema": "V5_TARGET_PANEL_SIZING_RECEIPT_V2",
            **receipt.__dict__,
            "evaluated_counts": list(receipt.evaluated_counts),
            "verdict_digest_by_count": {
                str(k): v for k, v in receipt.verdict_digest_by_count.items()
            },
            "receipt_sha256": receipt.canonical_digest(),
        }
        write_json(args.out_dir / "target_panel_sizing_receipt_v2.json", payload)
        status["status"] = "TARGET_PANEL_CAPACITY_QUALIFIED__STOP_HIGHER_RUNGS"
        status["selected_target_count"] = selected
    else:
        status["status"] = "TARGET_PANEL_CAPACITY_NOT_YET_QUALIFIED__NEXT_RUNG_REQUIRED"
        status["next_target_count"] = plan.next_target_count(combined)

    write_json(args.out_dir / f"{prefix}.status.json", status)
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
