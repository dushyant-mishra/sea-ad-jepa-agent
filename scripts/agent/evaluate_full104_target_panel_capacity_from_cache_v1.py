#!/usr/bin/env python3
"""Evaluate exactly one target-panel capacity rung from the calibration-only cache."""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.control_calibration_precision_authority_v2 import (
    ControlCalibrationPrecisionPlanV2,
)
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import (
    ControlCapacityCalibrationReceiptV1,
)
from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.full104_control_calibration_cache_evaluator_v1 import (
    evaluate_linear_capacity_rung,
    load_control_calibration_cache,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import (
    MaskingQualificationParametersAuthorityV3,
)
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import (
    TargetPanelControlVerdictV2,
    TargetPanelSizingPlanAuthorityV2,
    TargetPanelSizingReceiptV2,
)

SEED_NAMESPACE = "JEPA_V5_FULL104_PANEL_CAPACITY_CACHE_SHUFFLE_V1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_parameters(path: Path) -> MaskingQualificationParametersAuthorityV3:
    payload = load_json(path)
    if payload.get("schema") != "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3":
        raise SystemExit("parameter authority schema mismatch")
    names = {field.name for field in fields(MaskingQualificationParametersAuthorityV3)}
    authority = MaskingQualificationParametersAuthorityV3(
        **{name: payload[name] for name in names}
    )
    authority.validate()
    declared = payload.get("parameter_authority_sha256")
    if declared != authority.canonical_digest():
        raise SystemExit("parameter authority digest mismatch")
    return authority


def _load_capacity_receipt(path: Path) -> ControlCapacityCalibrationReceiptV1:
    payload = load_json(path)
    if payload.get("schema") != "V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1":
        raise SystemExit(f"{path}: capacity receipt schema mismatch")
    names = {field.name for field in fields(ControlCapacityCalibrationReceiptV1)}
    receipt = ControlCapacityCalibrationReceiptV1(
        **{name: payload[name] for name in names}
    )
    receipt.validate()
    if payload.get("receipt_sha256") != receipt.canonical_digest():
        raise SystemExit(f"{path}: capacity receipt digest mismatch")
    if receipt.scope_id != "TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1":
        raise SystemExit(f"{path}: target-panel capacity scope required")
    return receipt


def load_prior_evidence(
    *,
    verdict_paths: list[Path],
    capacity_paths: list[Path],
    planted_paths: list[Path],
    shuffled_paths: list[Path],
    replay_planted_paths: list[Path],
    replay_shuffled_paths: list[Path],
    cache,
    precision: ControlCalibrationPrecisionPlanV2,
) -> dict[int, TargetPanelControlVerdictV2]:
    counts = {
        len(verdict_paths),
        len(capacity_paths),
        len(planted_paths),
        len(shuffled_paths),
        len(replay_planted_paths),
        len(replay_shuffled_paths),
    }
    if len(counts) != 1:
        raise SystemExit(
            "every prior target-panel rung requires verdict, capacity receipt, "
            "raw planted/shuffled matrices, and exact replay planted/shuffled matrices"
        )

    verdict_names = {field.name for field in fields(TargetPanelControlVerdictV2)}
    out: dict[int, TargetPanelControlVerdictV2] = {}
    for verdict_path, capacity_path, planted_path, shuffled_path, replay_planted_path, replay_shuffled_path in zip(
        verdict_paths,
        capacity_paths,
        planted_paths,
        shuffled_paths,
        replay_planted_paths,
        replay_shuffled_paths,
    ):
        payload = load_json(verdict_path)
        if payload.get("schema") != "V5_TARGET_PANEL_CONTROL_VERDICT_V2":
            raise SystemExit(f"{verdict_path}: target-panel verdict schema mismatch")
        verdict = TargetPanelControlVerdictV2(
            **{name: payload[name] for name in verdict_names}
        )
        verdict.validate()
        if payload.get("verdict_sha256") != verdict.canonical_digest():
            raise SystemExit(f"{verdict_path}: target-panel verdict digest mismatch")

        capacity = _load_capacity_receipt(capacity_path)
        verdict.bind_capacity_receipt(capacity)
        count = int(verdict.target_count)
        if capacity.candidate_value != count or capacity.target_count != count:
            raise SystemExit("prior target-panel capacity count mismatch")
        if capacity.calibration_cache_manifest_sha256 != cache.manifest_sha256:
            raise SystemExit("prior target-panel capacity binds a different calibration cache")
        if capacity.precision_root_sha256 != precision.canonical_digest():
            raise SystemExit("prior target-panel capacity binds a different precision plan")

        for raw_path, replay_path, expected_sha, label in (
            (planted_path, replay_planted_path, capacity.raw_planted_evidence_sha256, "planted"),
            (shuffled_path, replay_shuffled_path, capacity.raw_shuffled_evidence_sha256, "shuffled"),
        ):
            if sha256_file(raw_path) != expected_sha:
                raise SystemExit(f"prior {label} matrix hash mismatch")
            if sha256_file(replay_path) != expected_sha:
                raise SystemExit(f"prior {label} replay hash mismatch")
            raw = np.load(raw_path, allow_pickle=False)
            replay = np.load(replay_path, allow_pickle=False)
            if raw.shape != (count, 104) or replay.shape != (count, 104):
                raise SystemExit(f"prior {label} matrix shape mismatch")
            if not np.array_equal(raw, replay):
                raise SystemExit(f"prior {label} replay is not exact")
            if not np.all(np.isfinite(raw)):
                raise SystemExit(f"prior {label} matrix contains non-finite values")

        planted = np.load(planted_path, allow_pickle=False)
        shuffled = np.load(shuffled_path, allow_pickle=False)
        difference = planted - shuffled
        interval = precision.interval(
            difference,
            cache.donor_source_code,
            target_count=count,
        )
        if float(interval.mean) != float(capacity.planted_minus_shuffled_mean):
            raise SystemExit("prior target-panel capacity mean does not rederive from raw matrices")
        if float(interval.lower_one_sided) != float(capacity.planted_minus_shuffled_lower_one_sided):
            raise SystemExit("prior target-panel capacity lower bound does not rederive from raw matrices")
        if verdict.planted_minus_shuffled_lower_one_sided != float(interval.lower_one_sided):
            raise SystemExit("prior target-panel verdict statistic does not rederive from raw matrices")
        if verdict.replay_exact is not True or capacity.replay_exact is not True:
            raise SystemExit("prior target-panel rung lacks exact replay proof")
        if count in out:
            raise SystemExit("duplicate target-panel verdict rung")
        out[count] = verdict
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
    p.add_argument("--prior-capacity-receipt", type=Path, action="append", default=[])
    p.add_argument("--prior-planted", type=Path, action="append", default=[])
    p.add_argument("--prior-shuffled", type=Path, action="append", default=[])
    p.add_argument("--prior-replay-planted", type=Path, action="append", default=[])
    p.add_argument("--prior-replay-shuffled", type=Path, action="append", default=[])
    p.add_argument("--replay-planted", type=Path)
    p.add_argument("--replay-shuffled", type=Path)
    args = p.parse_args()

    raise SystemExit(
        "STOP_H3_EQUIVALENCE_POWER_OPEN: the V2 planted-shortcut capacity ladder "
        "cannot select or freeze a FULL104 target panel. Preserve these helpers for "
        "positive-control calibration only; implement and freeze the successor "
        "equivalence-power/precision design tied to a prospectively justified G5 "
        "margin before any target-panel rung is executed."
    )

    cache = load_control_calibration_cache(args.cache_dir)
    cache.manifest.assert_calibration_only()
    parameters = load_parameters(args.parameters_authority)

    plan = TargetPanelSizingPlanAuthorityV2(
        authority_id="JEPA_V5_FULL104_TARGET_PANEL_SIZING_PLAN_V2",
        census_authority_sha256=cache.manifest.census_authority_sha256,
        target_eligibility_receipt_sha256=cache.manifest.target_eligibility_receipt_sha256,
        independent_donor_count=104,
        eligible_target_count=17053,
    )
    plan.validate()

    precision = ControlCalibrationPrecisionPlanV2(
        authority_id="JEPA_V5_FULL104_CONTROL_CALIBRATION_PRECISION_V2",
        census_authority_sha256=cache.manifest.census_authority_sha256,
        support_estimability_authority_sha256=cache.manifest.support_estimability_authority_sha256,
        target_eligibility_receipt_sha256=cache.manifest.target_eligibility_receipt_sha256,
        fold_assignment_artifact_sha256=cache.manifest.split_receipt_sha256,
        calibration_cache_manifest_sha256=cache.manifest_sha256,
    )
    precision.bind_calibration_cache(cache.manifest)

    prior = load_prior_evidence(
        verdict_paths=args.prior_verdict,
        capacity_paths=args.prior_capacity_receipt,
        planted_paths=args.prior_planted,
        shuffled_paths=args.prior_shuffled,
        replay_planted_paths=args.prior_replay_planted,
        replay_shuffled_paths=args.prior_replay_shuffled,
        cache=cache,
        precision=precision,
    )
    target_count = plan.next_target_count(prior)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "target_panel_sizing_plan_v2.json", {
        "schema": "V5_TARGET_PANEL_SIZING_PLAN_AUTHORITY_V2",
        **plan.__dict__,
        "panel_count_ladder": list(plan.panel_count_ladder),
        "authority_sha256": plan.canonical_digest(),
        "terminal_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    })
    write_json(args.out_dir / "control_calibration_precision_plan_v2.json", {
        "schema": "V5_CONTROL_CALIBRATION_PRECISION_PLAN_V2",
        **precision.__dict__,
        "authority_sha256": precision.canonical_digest(),
        "terminal_policy_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    })
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
