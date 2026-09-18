#!/usr/bin/env python3
"""Freeze the final FULL104 masking source closure and run contract.

Run only after all source changes are committed and the machine worktree
checkpoint validates PASS on that exact HEAD. Outputs MUST live outside the Git
worktree, so writing the freeze artifacts cannot invalidate the checkpoint.
No terminal masking outcome is read or produced.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.agent.work_checkpoint import resolve_canonical_repo, validate_checkpoint
from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.masking_qualification_run_contract_v3 import (
    DECISION_RULE_ID,
    EXECUTION_SOURCE_ROLE_ID,
    FREEZE_POLICY_ID,
    STRICT_SUPPORT_POLICY_ID,
    TERMINAL_UNIVERSE_ID,
    MaskingQualificationRunContractV3,
)

FULL104_MANIFEST="66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
OBSERVATION_STATE="852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"

SOURCE_PATHS=(
    "src/sea_ad_jepa/v5/full104_census_receipt_v2.py",
    "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py",
    "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
    "src/sea_ad_jepa/v5/masking_qualification_parameters_authority_v2.py",
    "src/sea_ad_jepa/v5/target_evidence_budget_authority_v2.py",
    "src/sea_ad_jepa/v5/masking_burden_ladder_authority_v2.py",
    "src/sea_ad_jepa/v5/outer_split_authority_v1.py",
    "src/sea_ad_jepa/v5/target_panel_sizing_authority_v1.py",
    "src/sea_ad_jepa/v5/target_panel_selector_v2.py",
    "src/sea_ad_jepa/v5/target_panel_authority_v2.py",
    "src/sea_ad_jepa/v5/address_universe_ladder_authority_v1.py",
    "src/sea_ad_jepa/v5/precision_authority_v2.py",
    "src/sea_ad_jepa/v5/precision_authority_v4.py",
    "src/sea_ad_jepa/v5/masking_rng_replay_authority_v2.py",
    "src/sea_ad_jepa/v5/masking_target_semantics_authority_v1.py",
    "src/sea_ad_jepa/v5/masking_qualification_design_authority_v2.py",
    "src/sea_ad_jepa/v5/masking_donor_evidence_v1.py",
    "src/sea_ad_jepa/v5/masking_control_executor_v1.py",
    "src/sea_ad_jepa/v5/masking_nonlinear_challenge_authority_v2.py",
    "src/sea_ad_jepa/v5/masking_nonlinear_challenge_executor_v1.py",
    "src/sea_ad_jepa/v5/masking_nonlinear_orchestrator_v1.py",
    "src/sea_ad_jepa/v5/masking_nonlinear_challenge_receipt_v1.py",
    "src/sea_ad_jepa/v5/masking_structural_controls_v1.py",
    "src/sea_ad_jepa/v5/masking_evidence_assembler_v1.py",
    "src/sea_ad_jepa/v5/masking_qualification_decision_v1.py",
    "src/sea_ad_jepa/v5/masking_qualification_decision_v2.py",
    "src/sea_ad_jepa/v5/masking_qualification_decision_v3.py",
    "src/sea_ad_jepa/v5/masking_qualification_execution_authority_v5.py",
    "src/sea_ad_jepa/v5/masking_qualification_run_contract_v3.py",
    "tests/test_v5_full104_masking_anti_spillover_v2.py",
)


def _outside(path: Path, worktree: Path) -> None:
    target=path.resolve()
    root=worktree.resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return
    raise SystemExit(f"freeze output must be outside Git worktree: {target}")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _root(pack: dict, name: str) -> str:
    value=pack["roots"].get(name)
    if not isinstance(value,str) or len(value)!=64:
        raise SystemExit(f"preexecution pack root missing: {name}")
    if any(token in value.upper() for token in ("PLACEHOLDER","UNRESOLVED")):
        raise SystemExit(f"preexecution pack root is unresolved: {name}")
    return value


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--worktree",type=Path,required=True)
    p.add_argument("--preexecution-pack",type=Path,required=True)
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--out-source-manifest",type=Path,required=True)
    p.add_argument("--out-run-contract",type=Path,required=True)
    args=p.parse_args()

    _outside(args.out_source_manifest,args.worktree)
    _outside(args.out_run_contract,args.worktree)

    checkpoint=_load(args.checkpoint)
    errors=validate_checkpoint(
        checkpoint,
        args.worktree.resolve(),
        resolve_canonical_repo(args.worktree.resolve()),
    )
    if errors:
        raise SystemExit("machine checkpoint failed validation: "+"; ".join(errors))
    checkpoint_sha=checkpoint.get("checkpoint_semantic_sha256")
    if not isinstance(checkpoint_sha,str) or len(checkpoint_sha)!=64:
        raise SystemExit("checkpoint semantic SHA-256 is missing")

    pack=_load(args.preexecution_pack)
    if pack.get("schema")!="V5_FULL104_MASKING_PREEXECUTION_AUTHORITY_PACK_V1":
        raise SystemExit("preexecution pack schema mismatch")
    declared=pack.get("pack_sha256")
    semantic=dict(pack); semantic.pop("pack_sha256",None)
    if declared!=canonical_sha(semantic):
        raise SystemExit("preexecution pack digest mismatch")
    if pack.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("preexecution pack indicates terminal outcomes were inspected")
    if pack.get("training_authorized") is not False:
        raise SystemExit("preexecution pack unexpectedly authorizes training")

    sources={}
    for relative in SOURCE_PATHS:
        path=args.repo / relative
        if not path.is_file():
            raise SystemExit(f"source-closure path missing: {relative}")
        sources[relative]=sha256_file(path)
    source_manifest={
        "schema":"V5_FULL104_MASKING_SOURCE_CLOSURE_MANIFEST_V1",
        "terminal_masking_outcomes_inspected":False,
        "training_authorized":False,
        "sources":dict(sorted(sources.items())),
    }
    source_manifest["manifest_sha256"]=canonical_sha(source_manifest)
    source_manifest_sha=source_manifest["manifest_sha256"]

    role_paths={
        "canonical_reference_source_sha256":"src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py",
        "full104_streaming_execution_source_sha256":"src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
        "precision_evaluator_source_sha256":"src/sea_ad_jepa/v5/precision_authority_v4.py",
        "donor_evidence_source_sha256":"src/sea_ad_jepa/v5/masking_donor_evidence_v1.py",
        "control_executor_source_sha256":"src/sea_ad_jepa/v5/masking_control_executor_v1.py",
        "nonlinear_executor_source_sha256":"src/sea_ad_jepa/v5/masking_nonlinear_challenge_executor_v1.py",
        "nonlinear_receipt_source_sha256":"src/sea_ad_jepa/v5/masking_nonlinear_challenge_receipt_v1.py",
        "structural_control_source_sha256":"src/sea_ad_jepa/v5/masking_structural_controls_v1.py",
        "evidence_assembler_source_sha256":"src/sea_ad_jepa/v5/masking_evidence_assembler_v1.py",
        "nonlinear_orchestrator_source_sha256":"src/sea_ad_jepa/v5/masking_nonlinear_orchestrator_v1.py",
        "decision_evaluator_source_sha256":"src/sea_ad_jepa/v5/masking_qualification_decision_v3.py",
        "execution_authority_source_sha256":"src/sea_ad_jepa/v5/masking_qualification_execution_authority_v5.py",
        "anti_spillover_test_source_sha256":"tests/test_v5_full104_masking_anti_spillover_v2.py",
    }
    role_hashes={field:sources[path] for field,path in role_paths.items()}

    contract=MaskingQualificationRunContractV3(
        authority_id="JEPA_V5_FULL104_MASKING_RUN_CONTRACT_V3",
        qualification_design_authority_sha256=_root(pack,"masking_design_authority_sha256"),
        qualification_parameters_authority_sha256=_root(pack,"masking_parameters_authority_sha256"),
        full104_block_manifest_sha256=FULL104_MANIFEST,
        observation_state_sha256=OBSERVATION_STATE,
        support_estimability_authority_sha256=_root(pack,"support_estimability_authority_sha256"),
        census_authority_sha256=_root(pack,"census_authority_sha256"),
        target_evidence_budget_template_sha256=_root(pack,"target_evidence_budget_template_sha256"),
        burden_ladder_authority_sha256=_root(pack,"burden_ladder_authority_sha256"),
        outer_split_authority_sha256=_root(pack,"outer_split_authority_sha256"),
        target_panel_authority_sha256=_root(pack,"target_panel_authority_sha256"),
        precision_authority_sha256=_root(pack,"precision_authority_sha256"),
        nonlinear_challenge_authority_sha256=_root(pack,"nonlinear_challenge_authority_sha256"),
        rng_replay_authority_sha256=_root(pack,"rng_replay_authority_sha256"),
        machine_worktree_checkpoint_sha256=checkpoint_sha,
        source_closure_manifest_sha256=source_manifest_sha,
        **role_hashes,
        execution_source_role_id=EXECUTION_SOURCE_ROLE_ID,
        decision_rule_id=DECISION_RULE_ID,
        freeze_policy_id=FREEZE_POLICY_ID,
        support_state_policy_id=STRICT_SUPPORT_POLICY_ID,
        terminal_universe_id=TERMINAL_UNIVERSE_ID,
    )
    contract.validate()

    args.out_source_manifest.parent.mkdir(parents=True,exist_ok=True)
    args.out_run_contract.parent.mkdir(parents=True,exist_ok=True)
    args.out_source_manifest.write_text(json.dumps(source_manifest,indent=2)+"\n",encoding="utf-8")
    payload={
        "schema":"V5_MASKING_QUALIFICATION_RUN_CONTRACT_V3",
        **contract.__dict__,
        "run_contract_authority_sha256":contract.canonical_digest(),
        "preexecution_pack_sha256":declared,
        "source_closure_manifest_sha256":source_manifest_sha,
        "terminal_masking_outcomes_inspected":False,
        "training_authorized":False,
    }
    args.out_run_contract.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(payload["run_contract_authority_sha256"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
