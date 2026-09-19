#!/usr/bin/env python3
"""Evaluate exactly one FULL104 nonlinear row-cap rung from the calibration cache."""
from __future__ import annotations

import argparse
from dataclasses import fields
import inspect
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import ControlCapacityCalibrationReceiptV1
from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.full104_control_calibration_cache_evaluator_v1 import load_control_calibration_cache
from sea_ad_jepa.v5 import full104_nonlinear_capacity_cache_evaluator_v1 as eval_impl
from sea_ad_jepa.v5.full104_nonlinear_capacity_cache_evaluator_v1 import evaluate_nonlinear_capacity_rung
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import MaskingQualificationParametersAuthorityV3
from sea_ad_jepa.v5.nonlinear_capacity_model_authority_v1 import NonlinearCapacityModelAuthorityV1
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import NonlinearCapControlVerdictV1
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v2 import (
    NonlinearSamplingCalibrationPlanV2,NonlinearSamplingCalibrationReceiptV2
)
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4
from sea_ad_jepa.v5.target_panel_authority_v3 import TargetPanelAuthorityV3
from sea_ad_jepa.v5.target_panel_selector_v2 import TargetPanelSelectionReceiptV2


def load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def typed(payload,cls,sha_field,expected_schema):
    if payload.get("schema") != expected_schema:
        raise SystemExit(
            f"{cls.__name__} schema mismatch: expected {expected_schema}, "
            f"observed {payload.get('schema')!r}"
        )
    names={f.name for f in fields(cls)}
    obj=cls(**{name:payload[name] for name in names})
    obj.validate()
    if payload.get(sha_field)!=obj.canonical_digest():
        raise SystemExit(f"{cls.__name__} digest mismatch")
    return obj


def _load_capacity_receipt(path:Path)->ControlCapacityCalibrationReceiptV1:
    payload=load(path)
    if payload.get("schema")!="V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1":
        raise SystemExit(f"{path}: capacity receipt schema mismatch")
    names={f.name for f in fields(ControlCapacityCalibrationReceiptV1)}
    receipt=ControlCapacityCalibrationReceiptV1(**{name:payload[name] for name in names})
    receipt.validate()
    if payload.get("receipt_sha256")!=receipt.canonical_digest():
        raise SystemExit(f"{path}: capacity receipt digest mismatch")
    if receipt.scope_id!="NONLINEAR_CAP_CAPACITY_CALIBRATION_V1":
        raise SystemExit(f"{path}: nonlinear capacity scope required")
    return receipt


def load_prior_evidence(
    *,
    verdict_paths:list[Path],
    capacity_paths:list[Path],
    planted_paths:list[Path],
    shuffled_paths:list[Path],
    replay_planted_paths:list[Path],
    replay_shuffled_paths:list[Path],
    cache,
    precision:QualificationPrecisionAuthorityV4,
    target_count:int,
)->dict[int,NonlinearCapControlVerdictV1]:
    counts={
        len(verdict_paths),len(capacity_paths),len(planted_paths),
        len(shuffled_paths),len(replay_planted_paths),len(replay_shuffled_paths)
    }
    if len(counts)!=1:
        raise SystemExit(
            "every prior nonlinear rung requires verdict, capacity receipt, "
            "raw planted/shuffled matrices, and exact replay planted/shuffled matrices"
        )
    names={f.name for f in fields(NonlinearCapControlVerdictV1)}
    out={}
    for verdict_path,capacity_path,planted_path,shuffled_path,replay_planted_path,replay_shuffled_path in zip(
        verdict_paths,capacity_paths,planted_paths,shuffled_paths,
        replay_planted_paths,replay_shuffled_paths
    ):
        payload=load(verdict_path)
        if payload.get("schema")!="V5_NONLINEAR_CAP_CONTROL_VERDICT_V1":
            raise SystemExit(f"{verdict_path}: nonlinear cap verdict schema mismatch")
        verdict=NonlinearCapControlVerdictV1(**{name:payload[name] for name in names})
        verdict.validate()
        if payload.get("verdict_sha256")!=verdict.canonical_digest():
            raise SystemExit(f"{verdict_path}: nonlinear cap verdict digest mismatch")
        capacity=_load_capacity_receipt(capacity_path)
        verdict.bind_capacity_receipt(capacity)
        cap=int(verdict.max_cells_per_donor)
        if capacity.candidate_value!=cap:
            raise SystemExit("prior nonlinear capacity cap mismatch")
        if capacity.target_count!=int(target_count):
            raise SystemExit("prior nonlinear capacity target count mismatch")
        if capacity.calibration_cache_manifest_sha256!=cache.manifest_sha256:
            raise SystemExit("prior nonlinear capacity binds a different calibration cache")
        if capacity.precision_root_sha256!=precision.canonical_digest():
            raise SystemExit("prior nonlinear capacity binds a different precision authority")

        for raw_path,replay_path,expected_sha,label in (
            (planted_path,replay_planted_path,capacity.raw_planted_evidence_sha256,"planted"),
            (shuffled_path,replay_shuffled_path,capacity.raw_shuffled_evidence_sha256,"shuffled"),
        ):
            if sha256_file(raw_path)!=expected_sha:
                raise SystemExit(f"prior nonlinear {label} matrix hash mismatch")
            if sha256_file(replay_path)!=expected_sha:
                raise SystemExit(f"prior nonlinear {label} replay hash mismatch")
            raw=np.load(raw_path,allow_pickle=False)
            replay=np.load(replay_path,allow_pickle=False)
            if raw.shape!=(int(target_count),104) or replay.shape!=(int(target_count),104):
                raise SystemExit(f"prior nonlinear {label} matrix shape mismatch")
            if not np.array_equal(raw,replay):
                raise SystemExit(f"prior nonlinear {label} replay is not exact")
            if not np.all(np.isfinite(raw)):
                raise SystemExit(f"prior nonlinear {label} matrix contains non-finite values")

        planted=np.load(planted_path,allow_pickle=False)
        shuffled=np.load(shuffled_path,allow_pickle=False)
        interval=precision.interval(planted-shuffled,cache.donor_source_code)
        if float(interval.mean)!=float(capacity.planted_minus_shuffled_mean):
            raise SystemExit("prior nonlinear capacity mean does not rederive from raw matrices")
        if float(interval.lower_one_sided)!=float(capacity.planted_minus_shuffled_lower_one_sided):
            raise SystemExit("prior nonlinear capacity lower bound does not rederive from raw matrices")
        if float(verdict.planted_minus_shuffled_lower_one_sided)!=float(interval.lower_one_sided):
            raise SystemExit("prior nonlinear verdict statistic does not rederive from raw matrices")
        if verdict.replay_exact is not True or capacity.replay_exact is not True:
            raise SystemExit("prior nonlinear rung lacks exact replay proof")
        if cap in out:
            raise SystemExit("duplicate nonlinear cap verdict")
        out[cap]=verdict
    return dict(sorted(out.items()))


def write(path:Path,payload:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache-dir",type=Path,required=True)
    p.add_argument("--parameters-authority",type=Path,required=True)
    p.add_argument("--model-capacity-authority",type=Path,required=True)
    p.add_argument("--target-panel-authority",type=Path,required=True)
    p.add_argument("--target-selection-receipt",type=Path,required=True)
    p.add_argument("--precision-authority",type=Path,required=True)
    p.add_argument("--outer-split-authority",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    p.add_argument("--workers",type=int,required=True)
    p.add_argument("--prior-verdict",type=Path,action="append",default=[])
    p.add_argument("--prior-capacity-receipt",type=Path,action="append",default=[])
    p.add_argument("--prior-planted",type=Path,action="append",default=[])
    p.add_argument("--prior-shuffled",type=Path,action="append",default=[])
    p.add_argument("--prior-replay-planted",type=Path,action="append",default=[])
    p.add_argument("--prior-replay-shuffled",type=Path,action="append",default=[])
    p.add_argument("--replay-planted",type=Path)
    p.add_argument("--replay-shuffled",type=Path)
    args=p.parse_args()

    cache=load_control_calibration_cache(args.cache_dir)
    cache.manifest.assert_calibration_only()

    pp=load(args.parameters_authority)
    parameters=typed(pp,MaskingQualificationParametersAuthorityV3,"parameter_authority_sha256","V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3")
    mp=load(args.model_capacity_authority)
    model=typed(mp,NonlinearCapacityModelAuthorityV1,"authority_sha256","V5_NONLINEAR_CAPACITY_MODEL_AUTHORITY_V1")
    model.bind_primary_parameters(parameters)

    panel_payload=load(args.target_panel_authority)
    panel=typed(panel_payload,TargetPanelAuthorityV3,"authority_sha256","V5_TARGET_PANEL_AUTHORITY_V3")
    selection_payload=load(args.target_selection_receipt)
    selection=typed(selection_payload,TargetPanelSelectionReceiptV2,"receipt_sha256","V5_TARGET_PANEL_SELECTION_RECEIPT_V2")
    if selection.target_count!=panel.target_count:
        raise SystemExit("target selection count disagrees with final target panel")
    if tuple(map(int,selection.selected_target_cols))!=tuple(map(int,cache.target_cols[:panel.target_count])):
        raise SystemExit("final target panel does not match authenticated cache target prefix")

    precision_payload=load(args.precision_authority)
    precision=typed(precision_payload,QualificationPrecisionAuthorityV4,"authority_sha256","V5_QUALIFICATION_PRECISION_AUTHORITY_V4")
    if precision.target_panel_authority_sha256!=panel.canonical_digest():
        raise SystemExit("precision authority is bound to a different target panel")
    precision.assert_sufficient(target_count=panel.target_count,donor_count=104,outer_fold_count=4)

    outer_payload=load(args.outer_split_authority)
    outer=typed(outer_payload,OuterDonorSplitAuthorityV1,"authority_sha256","V5_OUTER_DONOR_SPLIT_AUTHORITY_V1")
    if precision.outer_split_authority_sha256!=outer.canonical_digest():
        raise SystemExit("precision and nonlinear calibration use different outer split")
    if outer.fold_assignment_artifact_sha256!=cache.manifest.split_receipt_sha256:
        raise SystemExit("outer split and calibration cache use different fold receipt")

    evaluator_sha=sha256_file(Path(inspect.getfile(eval_impl)).resolve())
    plan=NonlinearSamplingCalibrationPlanV2(
        authority_id="JEPA_V5_FULL104_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V2",
        target_panel_authority_sha256=panel.canonical_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        outer_split_authority_sha256=outer.canonical_digest(),
        primary_parameters_authority_sha256=parameters.canonical_digest(),
        model_capacity_authority_sha256=model.canonical_digest(),
        calibration_cache_manifest_sha256=cache.manifest_sha256,
        calibration_evaluator_source_sha256=evaluator_sha,
    )
    plan.bind_current_roots(
        panel=panel,precision=precision,outer_split=outer,parameters=parameters,
        model=model,cache_manifest=cache.manifest
    )

    args.out_dir.mkdir(parents=True,exist_ok=True)
    write(args.out_dir/"nonlinear_sampling_calibration_plan_v2.json",{
        "schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_PLAN_V2",
        **plan.__dict__,
        "cap_ladder":list(plan.cap_ladder),
        "authority_sha256":plan.canonical_digest(),
        "terminal_outcomes_inspected_before_freeze":False,
        "training_authorized":False,
    })

    prior=load_prior_evidence(
        verdict_paths=args.prior_verdict,
        capacity_paths=args.prior_capacity_receipt,
        planted_paths=args.prior_planted,
        shuffled_paths=args.prior_shuffled,
        replay_planted_paths=args.prior_replay_planted,
        replay_shuffled_paths=args.prior_replay_shuffled,
        cache=cache,
        precision=precision,
        target_count=panel.target_count,
    )
    cap=plan.next_cap(prior)
    prefix=f"nonlinear_cap_{cap}"
    planted,shuffled=evaluate_nonlinear_capacity_rung(
        cache,target_count=panel.target_count,cap=cap,model_authority=model,
        plan_sha256=plan.canonical_digest(),workers=args.workers
    )
    planted_path=args.out_dir/f"{prefix}.planted_f64.npy"
    shuffled_path=args.out_dir/f"{prefix}.shuffled_f64.npy"
    np.save(planted_path,planted,allow_pickle=False); np.save(shuffled_path,shuffled,allow_pickle=False)
    status={
        "schema":"V5_NONLINEAR_CAPACITY_CALIBRATION_CACHE_RUN_V1",
        "plan_authority_sha256":plan.canonical_digest(),
        "calibration_cache_manifest_sha256":cache.manifest_sha256,
        "target_panel_authority_sha256":panel.canonical_digest(),
        "precision_authority_sha256":precision.canonical_digest(),
        "model_capacity_authority_sha256":model.canonical_digest(),
        "calibration_evaluator_source_sha256":evaluator_sha,
        "cap":cap,"target_count":panel.target_count,"workers":args.workers,
        "planted_matrix_sha256":sha256_file(planted_path),
        "shuffled_matrix_sha256":sha256_file(shuffled_path),
        "terminal_masking_policy_outcomes_inspected":False,
        "terminal_masking_qualification_authorized":False,
        "training_authorized":False,
    }
    if (args.replay_planted is None)!=(args.replay_shuffled is None):
        raise SystemExit("both replay matrices must be supplied together")
    if args.replay_planted is None:
        status["status"]="REPLAY_REQUIRED_BEFORE_NONLINEAR_CAPACITY_VERDICT"
        write(args.out_dir/f"{prefix}.status.json",status)
        print(json.dumps(status,sort_keys=True)); return 3
    if not np.array_equal(planted,np.load(args.replay_planted,allow_pickle=False)):
        raise SystemExit("nonlinear planted replay mismatch")
    if not np.array_equal(shuffled,np.load(args.replay_shuffled,allow_pickle=False)):
        raise SystemExit("nonlinear shuffled replay mismatch")

    difference=planted-shuffled
    interval=precision.interval(difference,cache.donor_source_code)
    capacity=ControlCapacityCalibrationReceiptV1(
        scope_id="NONLINEAR_CAP_CAPACITY_CALIBRATION_V1",
        candidate_value=cap,
        calibration_cache_manifest_sha256=cache.manifest_sha256,
        calibration_cache_role_id=cache.manifest.cache_role_id,
        raw_planted_evidence_sha256=sha256_file(planted_path),
        raw_shuffled_evidence_sha256=sha256_file(shuffled_path),
        precision_root_sha256=precision.canonical_digest(),
        planted_minus_shuffled_mean=float(interval.mean),
        planted_minus_shuffled_lower_one_sided=float(interval.lower_one_sided),
        donor_count=104,target_count=panel.target_count,
        bootstrap_replicates=precision.bootstrap_replicates,
        confidence_level_numerator=precision.confidence_level_numerator,
        confidence_level_denominator=precision.confidence_level_denominator,
        replay_exact=True,
    )
    capacity.validate()
    write(args.out_dir/f"{prefix}.capacity_receipt.json",{
        "schema":"V5_CONTROL_CAPACITY_CALIBRATION_RECEIPT_V1",**capacity.__dict__,
        "detects_planted_shortcut":capacity.detects_planted_shortcut,
        "receipt_sha256":capacity.canonical_digest(),
    })
    verdict=NonlinearCapControlVerdictV1(
        max_cells_per_donor=cap,capacity_receipt_sha256=capacity.canonical_digest(),
        planted_minus_shuffled_lower_one_sided=float(interval.lower_one_sided),
        replay_exact=True,all_donors_represented=bool(np.all(np.isfinite(difference))),
    )
    verdict.bind_capacity_receipt(capacity)
    write(args.out_dir/f"{prefix}.verdict.json",{
        "schema":"V5_NONLINEAR_CAP_CONTROL_VERDICT_V1",**verdict.__dict__,
        "qualified":verdict.qualified,"verdict_sha256":verdict.canonical_digest(),
    })

    combined=dict(prior); combined[cap]=verdict
    selected=plan.select(combined)
    if selected is not None:
        receipt=NonlinearSamplingCalibrationReceiptV2(
            plan_authority_sha256=plan.canonical_digest(),
            calibration_cache_manifest_sha256=cache.manifest_sha256,
            precision_authority_sha256=precision.canonical_digest(),
            model_capacity_authority_sha256=model.canonical_digest(),
            selected_max_cells_per_donor=selected,
            evaluated_caps=tuple(combined),
            verdict_digest_by_cap={k:v.canonical_digest() for k,v in combined.items()},
        )
        receipt.bind_verdicts(plan,combined)
        write(args.out_dir/"nonlinear_sampling_calibration_receipt_v2.json",{
            "schema":"V5_NONLINEAR_SAMPLING_CALIBRATION_RECEIPT_V2",**receipt.__dict__,
            "evaluated_caps":list(receipt.evaluated_caps),
            "verdict_digest_by_cap":{str(k):v for k,v in receipt.verdict_digest_by_cap.items()},
            "receipt_sha256":receipt.canonical_digest(),
        })
        status["status"]="NONLINEAR_CAPACITY_QUALIFIED__STOP_HIGHER_RUNGS"; status["selected_cap"]=selected
    else:
        status["status"]="NONLINEAR_CAPACITY_NOT_YET_QUALIFIED__NEXT_RUNG_REQUIRED"
        status["next_cap"]=plan.next_cap(combined)
    write(args.out_dir/f"{prefix}.status.json",status)
    print(json.dumps(status,sort_keys=True)); return 0


if __name__=="__main__":
    raise SystemExit(main())
