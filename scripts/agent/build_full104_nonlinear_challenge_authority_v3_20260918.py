#!/usr/bin/env python3
"""Build final FULL104 nonlinear challenge authority V3 from current control calibration."""
from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_control_calibration_cache_evaluator_v1 import load_control_calibration_cache
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import ControlCapacityCalibrationReceiptV1
from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v3 import NonlinearMaskingChallengeAuthorityV3
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import MaskingQualificationParametersAuthorityV3
from sea_ad_jepa.v5.nonlinear_capacity_model_authority_v1 import NonlinearCapacityModelAuthorityV1
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import NonlinearCapControlVerdictV1
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v2 import (
    NonlinearSamplingCalibrationPlanV2,
    NonlinearSamplingCalibrationReceiptV2,
)
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4
from sea_ad_jepa.v5.target_panel_authority_v3 import TargetPanelAuthorityV3


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def typed(payload: dict, cls, digest_field: str, expected_schema: str):
    if payload.get("schema") != expected_schema:
        raise SystemExit(
            f"{cls.__name__} schema mismatch: expected {expected_schema}, "
            f"observed {payload.get('schema')!r}"
        )
    names = {f.name for f in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise SystemExit(f"{cls.__name__} missing fields: {sorted(missing)[:5]}")
    obj = cls(**{name: payload[name] for name in names})
    obj.validate()
    if payload.get(digest_field) != obj.canonical_digest():
        raise SystemExit(f"{cls.__name__} digest mismatch")
    return obj


def load_capacity_receipts(paths: list[Path]) -> dict[int, ControlCapacityCalibrationReceiptV1]:
    out: dict[int, ControlCapacityCalibrationReceiptV1] = {}
    names={f.name for f in fields(ControlCapacityCalibrationReceiptV1)}
    for path in paths:
        payload=load(path)
        if payload.get("schema")!="V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1":
            raise SystemExit(f"{path}: capacity receipt schema mismatch")
        obj=ControlCapacityCalibrationReceiptV1(**{name:payload[name] for name in names})
        obj.validate()
        if payload.get("receipt_sha256")!=obj.canonical_digest():
            raise SystemExit(f"{path}: capacity receipt digest mismatch")
        if obj.scope_id!="NONLINEAR_CAP_CAPACITY_CALIBRATION_V1":
            raise SystemExit(f"{path}: nonlinear capacity scope required")
        if obj.candidate_value in out:
            raise SystemExit("duplicate nonlinear capacity receipt")
        out[obj.candidate_value]=obj
    return dict(sorted(out.items()))


def load_verdicts(paths: list[Path]) -> dict[int, NonlinearCapControlVerdictV1]:
    out: dict[int, NonlinearCapControlVerdictV1] = {}
    names = {f.name for f in fields(NonlinearCapControlVerdictV1)}
    for path in paths:
        payload = load(path)
        if payload.get("schema") != "V5_NONLINEAR_CAP_CONTROL_VERDICT_V1":
            raise SystemExit(f"{path}: nonlinear cap verdict schema mismatch")
        obj = NonlinearCapControlVerdictV1(**{name: payload[name] for name in names})
        obj.validate()
        if payload.get("verdict_sha256") != obj.canonical_digest():
            raise SystemExit(f"{path}: nonlinear cap verdict digest mismatch")
        if obj.max_cells_per_donor in out:
            raise SystemExit("duplicate nonlinear cap verdict")
        out[obj.max_cells_per_donor] = obj
    return dict(sorted(out.items()))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache-dir", type=Path, required=True)
    p.add_argument("--parameters-authority", type=Path, required=True)
    p.add_argument("--model-capacity-authority", type=Path, required=True)
    p.add_argument("--target-panel-authority", type=Path, required=True)
    p.add_argument("--precision-authority", type=Path, required=True)
    p.add_argument("--outer-split-authority", type=Path, required=True)
    p.add_argument("--sampling-plan", type=Path, required=True)
    p.add_argument("--sampling-receipt", type=Path, required=True)
    p.add_argument("--capacity-receipt", type=Path, action="append", required=True)
    p.add_argument("--cap-verdict", type=Path, action="append", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    cache = load_control_calibration_cache(args.cache_dir)
    cache.manifest.assert_calibration_only()

    parameters = typed(load(args.parameters_authority), MaskingQualificationParametersAuthorityV3, "parameter_authority_sha256", "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3")
    model = typed(load(args.model_capacity_authority), NonlinearCapacityModelAuthorityV1, "authority_sha256", "V5_NONLINEAR_CAPACITY_MODEL_AUTHORITY_V1")
    model.bind_primary_parameters(parameters)

    panel = typed(load(args.target_panel_authority), TargetPanelAuthorityV3, "authority_sha256", "V5_TARGET_PANEL_AUTHORITY_V3")
    precision = typed(load(args.precision_authority), QualificationPrecisionAuthorityV4, "authority_sha256", "V5_QUALIFICATION_PRECISION_AUTHORITY_V4")
    outer = typed(load(args.outer_split_authority), OuterDonorSplitAuthorityV1, "authority_sha256", "V5_OUTER_DONOR_SPLIT_AUTHORITY_V1")
    if precision.target_panel_authority_sha256 != panel.canonical_digest():
        raise SystemExit("precision authority binds a different target panel")
    if precision.outer_split_authority_sha256 != outer.canonical_digest():
        raise SystemExit("precision authority binds a different outer split")
    if outer.fold_assignment_artifact_sha256 != cache.manifest.split_receipt_sha256:
        raise SystemExit("outer split and calibration cache use different fold receipts")

    plan_payload = load(args.sampling_plan)
    if plan_payload.get("schema") != "V5_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V2":
        raise SystemExit("nonlinear sampling calibration plan V2 is required")
    plan = typed(plan_payload, NonlinearSamplingCalibrationPlanV2, "authority_sha256", "V5_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V2")
    plan.bind_current_roots(
        panel=panel,
        precision=precision,
        outer_split=outer,
        parameters=parameters,
        model=model,
        cache_manifest=cache.manifest,
    )

    receipt_payload = load(args.sampling_receipt)
    if receipt_payload.get("schema") != "V5_NONLINEAR_SAMPLING_CALIBRATION_RECEIPT_V2":
        raise SystemExit("nonlinear sampling calibration receipt V2 is required")
    receipt_names = {f.name for f in fields(NonlinearSamplingCalibrationReceiptV2)}
    receipt = NonlinearSamplingCalibrationReceiptV2(
        **{
            name: (
                tuple(map(int, receipt_payload[name]))
                if name == "evaluated_caps"
                else {int(k): str(v) for k, v in receipt_payload[name].items()}
                if name == "verdict_digest_by_cap"
                else receipt_payload[name]
            )
            for name in receipt_names
        }
    )
    receipt.validate()
    if receipt_payload.get("receipt_sha256") != receipt.canonical_digest():
        raise SystemExit("nonlinear sampling calibration receipt digest mismatch")

    capacity_receipts = load_capacity_receipts(args.capacity_receipt)
    verdicts = load_verdicts(args.cap_verdict)
    if set(capacity_receipts)!=set(verdicts):
        raise SystemExit("nonlinear verdict and capacity-receipt rungs differ")
    for cap,verdict in verdicts.items():
        capacity=capacity_receipts[cap]
        if capacity.calibration_cache_manifest_sha256!=cache.manifest_sha256:
            raise SystemExit("nonlinear capacity receipt binds a different calibration cache")
        if capacity.precision_root_sha256!=precision.canonical_digest():
            raise SystemExit("nonlinear capacity receipt binds a different precision authority")
        if capacity.target_count!=panel.target_count:
            raise SystemExit("nonlinear capacity receipt target count disagrees with panel")
        verdict.bind_capacity_receipt(capacity)
    receipt.bind_verdicts(plan, verdicts)
    selected = receipt.selected_max_cells_per_donor
    if selected != plan.select(verdicts):
        raise SystemExit("selected nonlinear cap does not match mechanical calibration")

    authority = NonlinearMaskingChallengeAuthorityV3(
        authority_id="JEPA_V5_FULL104_NONLINEAR_CHALLENGE_AUTHORITY_V3",
        primary_parameters_authority_sha256=parameters.canonical_digest(),
        outer_split_authority_sha256=outer.canonical_digest(),
        target_panel_authority_sha256=panel.canonical_digest(),
        historical_nonlinear_script_sha256=model.historical_nonlinear_script_sha256,
        historical_nonlinear_summary_sha256=model.historical_nonlinear_summary_sha256,
        sampling_calibration_plan_sha256=plan.canonical_digest(),
        sampling_calibration_receipt_sha256=receipt.canonical_digest(),
        max_cells_per_donor=selected,
    )
    authority.bind_sampling_calibration(plan, receipt)

    model_shape = (
        model.feature_count,
        model.learning_rate_numerator,
        model.learning_rate_denominator,
        model.max_iter,
        model.max_leaf_nodes,
        model.min_samples_leaf,
        model.l2_regularization_numerator,
        model.l2_regularization_denominator,
        model.max_bins,
        model.early_stopping,
    )
    challenge_shape = (
        authority.feature_count,
        authority.learning_rate_numerator,
        authority.learning_rate_denominator,
        authority.max_iter,
        authority.max_leaf_nodes,
        authority.min_samples_leaf,
        authority.l2_regularization_numerator,
        authority.l2_regularization_denominator,
        authority.max_bins,
        authority.early_stopping,
    )
    if challenge_shape != model_shape:
        raise SystemExit("nonlinear V3 challenge shape disagrees with reauthorized model-capacity authority")

    payload = {
        "schema": "V5_NONLINEAR_MASKING_CHALLENGE_AUTHORITY_V3",
        **authority.__dict__,
        "random_seed": authority.random_seed,
        "authority_sha256": authority.canonical_digest(),
        "model_capacity_authority_sha256": model.canonical_digest(),
        "calibration_cache_manifest_sha256": cache.manifest_sha256,
        "historical_role": "MODEL_CAPACITY_PROVENANCE_ONLY__NO_DATA_TARGET_BURDEN_FOLD_SEED_OR_ROW_CAP_AUTHORITY",
        "terminal_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
