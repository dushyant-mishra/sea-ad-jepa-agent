#!/usr/bin/env python3
"""Validate current FULL104 masking preflight authority/root closure."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.full104_masking_gpu_preflight_v1 import (
    load_json,
    typed,
    validate_calibration_files,
    validate_terminal_bindings,
)
from sea_ad_jepa.v5.masking_qualification_run_contract_v4 import MaskingQualificationRunContractV4
from scripts.agent.work_checkpoint import semantic_sha256

SOURCE_ROLES = {
    "canonical_reference_live_sha256": "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py",
    "full104_streaming_execution_live_sha256": "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
    "target_panel_sizing_live_sha256": "src/sea_ad_jepa/v5/target_panel_sizing_authority_v2.py",
    "control_calibration_precision_live_sha256": "src/sea_ad_jepa/v5/control_calibration_precision_authority_v2.py",
    "control_capacity_calibration_live_sha256": "src/sea_ad_jepa/v5/control_capacity_calibration_receipt_v1.py",
    "control_calibration_cache_builder_live_sha256": "scripts/agent/build_full104_control_calibration_cache_v1.py",
    "control_calibration_cache_evaluator_live_sha256": "src/sea_ad_jepa/v5/full104_control_calibration_cache_evaluator_v1.py",
    "target_panel_authority_live_sha256": "src/sea_ad_jepa/v5/target_panel_authority_v3.py",
    "precision_evaluator_live_sha256": "src/sea_ad_jepa/v5/precision_authority_v4.py",
    "donor_evidence_live_sha256": "src/sea_ad_jepa/v5/masking_donor_evidence_v1.py",
    "control_executor_live_sha256": "src/sea_ad_jepa/v5/masking_control_executor_v1.py",
    "nonlinear_sampling_calibration_live_sha256": "src/sea_ad_jepa/v5/nonlinear_sampling_calibration_authority_v2.py",
    "nonlinear_authority_live_sha256": "src/sea_ad_jepa/v5/masking_nonlinear_challenge_authority_v3.py",
    "nonlinear_executor_live_sha256": "src/sea_ad_jepa/v5/masking_nonlinear_challenge_executor_v1.py",
    "decision_evaluator_live_sha256": "src/sea_ad_jepa/v5/masking_qualification_decision_v2.py",
    "execution_authority_live_sha256": "src/sea_ad_jepa/v5/masking_qualification_execution_authority_v4.py",
    "anti_spillover_test_live_sha256": "tests/test_v5_full104_masking_anti_spillover_v2.py",
}


def require_terminal_path(args: argparse.Namespace, name: str) -> Path:
    value = getattr(args, name)
    if value is None:
        raise SystemExit(f"--{name.replace('_','-')} is required in terminal mode")
    return value


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("calibration", "terminal"), required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--observation-state", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--registry-authority", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--parameters-authority", type=Path, required=True)
    p.add_argument("--census-authority", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--target-eligibility", type=Path, required=True)
    p.add_argument("--cache-dir", type=Path, required=True)
    p.add_argument("--target-panel-authority", type=Path)
    p.add_argument("--precision-authority", type=Path)
    p.add_argument("--outer-split-authority", type=Path)
    p.add_argument("--nonlinear-authority", type=Path)
    p.add_argument("--rng-authority", type=Path)
    p.add_argument("--run-contract", type=Path)
    p.add_argument("--machine-checkpoint", type=Path)
    args = p.parse_args()

    roots = validate_calibration_files(
        level4_root=args.level4_root,
        observation_state=args.observation_state,
        registry_file=args.registry,
        registry_authority_file=args.registry_authority,
        support_authority_file=args.support_authority,
        parameters_authority_file=args.parameters_authority,
        census_authority_file=args.census_authority,
        split_receipt_file=args.split_receipt,
        target_eligibility_file=args.target_eligibility,
        cache_dir=args.cache_dir,
    )
    result = {"mode": args.mode, "calibration": roots}

    if args.mode == "terminal":
        panel_path = require_terminal_path(args, "target_panel_authority")
        precision_path = require_terminal_path(args, "precision_authority")
        outer_path = require_terminal_path(args, "outer_split_authority")
        nonlinear_path = require_terminal_path(args, "nonlinear_authority")
        rng_path = require_terminal_path(args, "rng_authority")
        contract_path = require_terminal_path(args, "run_contract")
        checkpoint_path = require_terminal_path(args, "machine_checkpoint")
        terminal = validate_terminal_bindings(
            calibration_roots=roots,
            target_panel_payload=load_json(panel_path),
            precision_payload=load_json(precision_path),
            outer_split_payload=load_json(outer_path),
            nonlinear_payload=load_json(nonlinear_path),
            rng_payload=load_json(rng_path),
            run_contract_payload=load_json(contract_path),
        )
        contract = typed(
            load_json(contract_path),
            MaskingQualificationRunContractV4,
            ("run_contract_sha256", "authority_sha256"),
            "V5_MASKING_QUALIFICATION_RUN_CONTRACT_V4",
        )
        live_sources = {}
        for role, relative in SOURCE_ROLES.items():
            path = args.repo / relative
            if not path.is_file():
                raise SystemExit(f"missing live source role {role}: {path}")
            live_sources[role] = sha256_file(path)
        contract.bind_execution_sources(**live_sources)
        checkpoint_payload = load_json(checkpoint_path)
        declared_checkpoint_semantic = str(checkpoint_payload.get("checkpoint_semantic_sha256", ""))
        if declared_checkpoint_semantic != semantic_sha256(checkpoint_payload):
            raise SystemExit("machine/worktree checkpoint semantic digest mismatch")
        contract.bind_machine_checkpoint_semantic(checkpoint_payload)
        result["terminal"] = {
            **terminal,
            "machine_worktree_checkpoint_semantic_sha256": declared_checkpoint_semantic,
        }

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
