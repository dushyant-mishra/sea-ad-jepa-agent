#!/usr/bin/env python3
"""Run exactly one FULL104 target-panel capacity-calibration rung.

This driver is deliberately incapable of opening terminal masking-policy
outcomes. It uses only:
  * the authenticated FULL104 Level-4 substrate,
  * the authenticated current canonical address registry,
  * current census/split/target-eligibility receipts,
  * the explicitly re-authorized primary attacker, and
  * burden-free planted-vs-within-donor-shuffled controls.

A first execution writes raw evidence and exits REPLAY_REQUIRED. A second
execution must reproduce the raw matrices exactly before any rung verdict can
be issued. If a rung qualifies, higher target-count rungs are forbidden.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from sea_ad_jepa.v5.control_calibration_precision_authority_v1 import (
    ControlCalibrationPrecisionPlanV1,
)
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import (
    ControlCapacityCalibrationReceiptV1,
)
from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import Full104ManifestStreamV1
from sea_ad_jepa.v5.masking_control_executor_v1 import (
    run_planted_proxy_detection_fold,
    run_shuffled_null_detection_fold,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v2 import (
    MaskingQualificationParametersAuthorityV2,
)
from sea_ad_jepa.v5.target_panel_selector_v2 import select_target_cols
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import (
    TargetPanelControlVerdictV2,
    TargetPanelSizingPlanAuthorityV2,
    TargetPanelSizingReceiptV2,
)

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
EXPECTED_REGISTRY_ROWS = 41238
EXPECTED_CELLS = 4553407
EXPECTED_DONORS = 104
EXPECTED_ELIGIBLE_TARGETS = 17053
CAPACITY_SEED_NAMESPACE = "V5_FULL104_PANEL_CAPACITY_CONTROL_V1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_receipt(payload: dict[str, Any], schema: str, path: Path) -> str:
    if payload.get("schema") != schema:
        raise SystemExit(f"{path}: expected schema {schema}")
    digest = payload.get("receipt_sha256")
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    if digest != canonical_sha(semantic):
        raise SystemExit(f"{path}: receipt digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit(f"{path}: terminal masking outcomes must remain unopened")
    return str(digest)


def load_registry(path: Path) -> tuple[np.ndarray, np.ndarray]:
    if sha256_file(path) != EXPECTED_REGISTRY_SHA256:
        raise SystemExit("canonical address registry hash mismatch")
    import csv
    indices: list[int] = []
    ids: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        names = set(reader.fieldnames or ())
        required = {"molecular_address_index", "molecular_address_id"}
        if not required.issubset(names):
            raise SystemExit("canonical registry is missing model-facing identity fields")
        for row in reader:
            indices.append(int(row["molecular_address_index"]))
            ids.append(str(row["molecular_address_id"]))
    if len(indices) != EXPECTED_REGISTRY_ROWS:
        raise SystemExit("canonical registry row count mismatch")
    expected = np.arange(EXPECTED_REGISTRY_ROWS, dtype=np.int64)
    observed = np.asarray(indices, dtype=np.int64)
    if not np.array_equal(observed, expected):
        raise SystemExit("canonical registry index ordering invariant failed")
    if len(set(ids)) != len(ids) or any(not value for value in ids):
        raise SystemExit("canonical registry molecular_address_id invariant failed")
    return observed, np.asarray(ids, dtype=object)


def load_parameters(path: Path) -> MaskingQualificationParametersAuthorityV2:
    payload = load_json(path)
    if payload.get("schema") != "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V2":
        raise SystemExit("parameter authority schema mismatch")
    allowed = {field.name for field in fields(MaskingQualificationParametersAuthorityV2)}
    kwargs = {name: payload[name] for name in allowed}
    authority = MaskingQualificationParametersAuthorityV2(**kwargs)
    authority.validate()
    declared = payload.get("parameter_authority_sha256")
    if declared != authority.canonical_digest():
        raise SystemExit("parameter authority digest mismatch")
    return authority


def load_prior_verdicts(paths: list[Path]) -> dict[int, TargetPanelControlVerdictV2]:
    out: dict[int, TargetPanelControlVerdictV2] = {}
    for path in paths:
        payload = load_json(path)
        if payload.get("schema") != "V5_TARGET_PANEL_CONTROL_VERDICT_V2":
            raise SystemExit(f"{path}: target-panel verdict schema mismatch")
        names = {field.name for field in fields(TargetPanelControlVerdictV2)}
        verdict = TargetPanelControlVerdictV2(**{name: payload[name] for name in names})
        verdict.validate()
        declared = payload.get("verdict_sha256")
        if declared != verdict.canonical_digest():
            raise SystemExit(f"{path}: target-panel verdict digest mismatch")
        out[verdict.target_count] = verdict
    return dict(sorted(out.items()))


def control_seed(precision_root: str, target_count: int) -> int:
    raw = f"{CAPACITY_SEED_NAMESPACE}|{precision_root}|{target_count}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=False)


def matrix_sha(path: Path) -> str:
    return sha256_file(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def assemble_capacity_matrices(
    *,
    stream: Full104ManifestStreamV1,
    parameters: MaskingQualificationParametersAuthorityV2,
    selected_cols: tuple[int, ...],
    selected_ids: tuple[str, ...],
    eligible_proxy_cols: np.ndarray,
    global_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    n_targets = len(selected_cols)
    planted = np.full((n_targets, EXPECTED_DONORS), np.nan, dtype=np.float64)
    shuffled = np.full((n_targets, EXPECTED_DONORS), np.nan, dtype=np.float64)
    folds = tuple(sorted(set(map(int, stream.fold_by_donor))))

    for target_index, (target_col, target_id) in enumerate(zip(selected_cols, selected_ids)):
        for fold_index in folds:
            positive = run_planted_proxy_detection_fold(
                stream=stream,
                fold_index=fold_index,
                parameters=parameters,
                target_col=int(target_col),
                target_id=target_id,
                eligible_proxy_cols=eligible_proxy_cols,
            )
            negative = run_shuffled_null_detection_fold(
                stream=stream,
                fold_index=fold_index,
                parameters=parameters,
                target_col=int(target_col),
                target_id=target_id,
                global_seed=int(global_seed),
            )
            for donor, score in positive["donor_scores"]:
                if np.isfinite(planted[target_index, int(donor)]):
                    raise SystemExit("duplicate planted donor evidence")
                planted[target_index, int(donor)] = float(score)
            for donor, score in negative["donor_scores"]:
                if np.isfinite(shuffled[target_index, int(donor)]):
                    raise SystemExit("duplicate shuffled donor evidence")
                shuffled[target_index, int(donor)] = float(score)
    if not np.all(np.isfinite(planted)) or not np.all(np.isfinite(shuffled)):
        raise SystemExit("capacity evidence did not cover every target x donor unit")
    return planted, shuffled


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level4-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--census-authority", type=Path, required=True)
    parser.add_argument("--split-receipt", type=Path, required=True)
    parser.add_argument("--target-eligibility", type=Path, required=True)
    parser.add_argument("--support-authority", type=Path, required=True)
    parser.add_argument("--parameters-authority", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--prior-verdict", type=Path, action="append", default=[])
    parser.add_argument("--replay-planted", type=Path)
    parser.add_argument("--replay-shuffled", type=Path)
    args = parser.parse_args()

    manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if sha256_file(manifest) != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 block manifest mismatch")

    _, registry_ids = load_registry(args.registry)
    census = load_json(args.census_authority)
    if census.get("schema") != "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise SystemExit("census V2 authority is required")
    if census.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("census authority indicates terminal outcome access")
    census_root = str(census.get("census_authority_sha256", ""))
    if len(census_root) != 64:
        raise SystemExit("census authority digest is missing")

    split = load_json(args.split_receipt)
    split_root = verify_receipt(
        split, "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1", args.split_receipt
    )
    eligibility = load_json(args.target_eligibility)
    eligibility_root = verify_receipt(
        eligibility, "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1", args.target_eligibility
    )
    if eligibility.get("split_receipt_sha256") != split_root:
        raise SystemExit("target eligibility is bound to a different split")
    eligible_cols = np.asarray(eligibility["eligible_target_cols_all_folds"], dtype=np.int64)
    strict_core = np.asarray(eligibility["strict_core_cols"], dtype=np.int64)
    if eligible_cols.size != EXPECTED_ELIGIBLE_TARGETS:
        raise SystemExit("eligible target count mismatch")

    support = load_json(args.support_authority)
    if support.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    if support.get("full104_substrate_sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("support authority is bound to a different substrate")
    support_root = sha256_file(args.support_authority)

    parameters = load_parameters(args.parameters_authority)
    source_names = tuple(map(str, split["source_names"]))
    donor_source_code = np.asarray(split["donor_source_code"], dtype=np.int64)
    donor_ids = tuple(map(str, split["donor_ids"]))
    fold_by_donor = np.asarray(split["fold_by_donor"], dtype=np.int64)
    if len(donor_ids) != EXPECTED_DONORS or donor_source_code.size != EXPECTED_DONORS:
        raise SystemExit("split donor registry does not contain exactly 104 donors")
    source_by_donor = np.asarray(
        [source_names[int(code)] for code in donor_source_code], dtype=object
    )
    donor_id_to_code = {donor_id: i for i, donor_id in enumerate(donor_ids)}

    plan = TargetPanelSizingPlanAuthorityV2(
        authority_id="JEPA_V5_FULL104_TARGET_PANEL_SIZING_PLAN_V2",
        census_authority_sha256=census_root,
        target_eligibility_receipt_sha256=eligibility_root,
        independent_donor_count=EXPECTED_DONORS,
        eligible_target_count=EXPECTED_ELIGIBLE_TARGETS,
    )
    plan.validate()
    prior = load_prior_verdicts(args.prior_verdict)
    target_count = plan.next_target_count(prior)

    selected_cols = select_target_cols(
        eligible_cols,
        target_count=target_count,
        eligibility_receipt_sha256=eligibility_root,
    )
    selected_ids = tuple(str(registry_ids[int(col)]) for col in selected_cols)
    if len(set(selected_ids)) != len(selected_ids):
        raise SystemExit("selected canonical target IDs are not unique")

    precision = ControlCalibrationPrecisionPlanV1(
        authority_id="JEPA_V5_FULL104_CONTROL_CALIBRATION_PRECISION_V1",
        census_authority_sha256=census_root,
        support_estimability_authority_sha256=support_root,
        target_eligibility_receipt_sha256=eligibility_root,
        outer_split_authority_sha256=split_root,
    )
    precision.validate()
    precision_root = precision.canonical_digest()
    seed = control_seed(precision_root, target_count)

    stream = Full104ManifestStreamV1(
        manifest_path=manifest,
        block_root=args.level4_root,
        expected_manifest_sha256=EXPECTED_BLOCK_MANIFEST_SHA256,
        donor_id_to_code=donor_id_to_code,
        source_by_donor=source_by_donor,
        fold_by_donor=fold_by_donor,
        universe_cols=strict_core,
        target_cols=np.asarray(selected_cols, dtype=np.int64),
        target_ids=np.asarray(selected_ids, dtype=object),
        expected_cell_count=EXPECTED_CELLS,
        verify_block_hashes=True,
    )
    stream.validate_layout()

    planted, shuffled = assemble_capacity_matrices(
        stream=stream,
        parameters=parameters,
        selected_cols=selected_cols,
        selected_ids=selected_ids,
        eligible_proxy_cols=eligible_cols,
        global_seed=seed,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"target_panel_{target_count}"
    planted_path = args.out_dir / f"{prefix}.planted_f64.npy"
    shuffled_path = args.out_dir / f"{prefix}.shuffled_f64.npy"
    np.save(planted_path, planted, allow_pickle=False)
    np.save(shuffled_path, shuffled, allow_pickle=False)

    base_status = {
        "schema": "V5_TARGET_PANEL_CAPACITY_CALIBRATION_RUN_V1",
        "target_count": target_count,
        "selected_target_cols": list(map(int, selected_cols)),
        "selected_target_ids": list(selected_ids),
        "planted_matrix_sha256": matrix_sha(planted_path),
        "shuffled_matrix_sha256": matrix_sha(shuffled_path),
        "precision_plan_sha256": precision_root,
        "split_receipt_sha256": split_root,
        "eligibility_receipt_sha256": eligibility_root,
        "parameters_authority_sha256": parameters.canonical_digest(),
        "terminal_masking_policy_outcomes_inspected": False,
        "training_authorized": False,
    }

    if (args.replay_planted is None) != (args.replay_shuffled is None):
        raise SystemExit("both replay matrices must be supplied together")
    if args.replay_planted is None:
        base_status["status"] = "REPLAY_REQUIRED_BEFORE_CAPACITY_VERDICT"
        write_json(args.out_dir / f"{prefix}.status.json", base_status)
        print(json.dumps(base_status, sort_keys=True))
        return 3

    replay_planted = np.load(args.replay_planted, allow_pickle=False)
    replay_shuffled = np.load(args.replay_shuffled, allow_pickle=False)
    if not np.array_equal(planted, replay_planted) or not np.array_equal(shuffled, replay_shuffled):
        raise SystemExit("capacity calibration replay mismatch")

    difference = planted - shuffled
    interval = precision.interval(
        difference,
        donor_source_code,
        target_count=target_count,
    )
    capacity = ControlCapacityCalibrationReceiptV1(
        scope_id="TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1",
        candidate_value=target_count,
        raw_planted_evidence_sha256=matrix_sha(planted_path),
        raw_shuffled_evidence_sha256=matrix_sha(shuffled_path),
        precision_root_sha256=precision_root,
        planted_minus_shuffled_mean=float(interval.mean),
        planted_minus_shuffled_lower_one_sided=float(interval.lower_one_sided),
        donor_count=EXPECTED_DONORS,
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
        donor_coverage_complete=True,
        bootstrap_finite=bool(np.isfinite(interval.mean) and np.isfinite(interval.lower_one_sided)),
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
            verdict_digest_by_count={count: value.canonical_digest() for count, value in combined.items()},
        )
        receipt.bind_verdicts(plan, combined)
        receipt_payload = {
            "schema": "V5_TARGET_PANEL_SIZING_RECEIPT_V2",
            **receipt.__dict__,
            "evaluated_counts": list(receipt.evaluated_counts),
            "verdict_digest_by_count": {str(k): v for k, v in receipt.verdict_digest_by_count.items()},
            "receipt_sha256": receipt.canonical_digest(),
        }
        write_json(args.out_dir / "target_panel_sizing_receipt_v2.json", receipt_payload)
        base_status["status"] = "TARGET_PANEL_CAPACITY_QUALIFIED__STOP_HIGHER_RUNGS"
        base_status["selected_target_count"] = selected
    else:
        base_status["status"] = "TARGET_PANEL_CAPACITY_NOT_YET_QUALIFIED__NEXT_RUNG_REQUIRED"
        base_status["next_target_count"] = plan.next_target_count(combined)

    write_json(args.out_dir / f"{prefix}.status.json", base_status)
    print(json.dumps(base_status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
