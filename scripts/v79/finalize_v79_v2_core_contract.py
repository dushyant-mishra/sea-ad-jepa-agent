#!/usr/bin/env python3
"""Finalize the controller-ratified V79 V2_CORE qualification authority.

This does not generate worlds. It treats the controller-accepted V2 draft as an
immutable required-input payload and emits only the small final launch-authority
envelope plus its SHA-256 sidecar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FINAL_REL = "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
FINAL_STATUS = "FROZEN_PROSPECTIVE_LAUNCH_AUTHORITY__NO_QUALIFICATION_FIT_RUN"
CONTROLLER_RULING_COMMENT = 6114753697
CONTROLLER_MODEL_DECISION = "FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY"
DRAFT_REL = "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json"
DRAFT_SHA256 = "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"
V1_REL = "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json"
V1_SHA256 = "70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540"
MASK_SHA256 = "12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab"

REQUIRED_INPUTS = {
    "s174_design_only": ("results/v79/v2_core_qualification/inputs/V79_S174_DESIGN_ONLY_V1.npz", "10e3c472543d948d673d91f7dadd15dbd77809a7b0d15f528eb9fd38d0c85a62"),
    "s174_design_only_record": ("results/v79/v2_core_qualification/inputs/V79_S174_DESIGN_ONLY_V1.json", "1a1295c34157b2d8629732a36cf1fe6592f6181872b41bd7d19151092b413fbb"),
    "planting_calibration_masked": ("results/v79/development/v2_core_planting_calibration/V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json", "49379ee09fcf7496919e570f83710ee772ca407ca0d20268a9af1f4e132f533c"),
    "structural_support_dev": ("results/v79/development/v2_core_planting_calibration/V79_G500_STRUCTURAL_SUPPORT_DEV.json", "d70781af34ec5263d515ee1ad7f9410b426a6516cd7a7d46e0a69c32ae6f41c2"),
    "structural_support_v1_record": ("results/v79/development/s174_structure_replay_v4_masked/V79_G500_STRUCTURAL_SUPPORT_V1.json", "a6023902d953f98fb0fbd2a22d53361627f9b6a299c8730ef2ba7b9776a9f286"),
    "masked_replay": ("results/v79/development/s174_structure_replay_v4_masked/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED.json", "caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683"),
    "masking_audit": ("results/v79/development/s174_structure_replay_v4_masked/V79_S174_REPLAY_MASKING_AUDIT_V1.json", "6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41"),
    "env_lock": ("results/v79/v2_core_qualification/inputs/V79_BAYES_ENV_PIP_FREEZE.txt", "5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782"),
}

EXPECTED_LIMITS = {
    ("Q01_WEAK_DONOR", "detection", "BIAS_DONOR_SD"),
    ("Q01_WEAK_DONOR", "positive", "BIAS_DONOR_SD"),
    ("Q08_SPARSE_DETECTION", "positive", "BIAS_DONOR_SD"),
    ("Q09_POSITIVE_TAIL", "positive", "BIAS_DONOR_SD"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_payload(root: Path) -> dict:
    draft_path = root / DRAFT_REL
    if sha256(draft_path) != DRAFT_SHA256:
        raise SystemExit("STOP: V2 draft payload SHA mismatch")
    if sha256(root / V1_REL) != V1_SHA256:
        raise SystemExit("STOP: historical V1 SHA mismatch")
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    if draft.get("status") != "PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION" or draft.get("launch_authority") is not False:
        raise SystemExit("STOP: V2 draft no longer has historical non-launch semantics")

    mult = draft["gates"]["multiplicity"]
    counts = mult["gate_counts"]
    if (mult["n_hard_statistical_gates"], counts["hard_rule"], counts["limit_statistical"]) != (260, 28, 4):
        raise SystemExit("STOP: frozen gate arithmetic changed")
    if abs(float(mult["alpha_per_gate"]) - (0.05 / 260.0)) > 1e-15:
        raise SystemExit("STOP: frozen alpha changed")
    if draft["worlds"]["genes_per_world"] != 44 or len(draft["worlds"]["world_list"]) != 12:
        raise SystemExit("STOP: frozen world/G definition changed")
    limits = {(g["world"], g["part"], g["gate"]) for g in draft["gates"]["list"] if g["verdict_class"] == "LIMIT"}
    if limits != EXPECTED_LIMITS:
        raise SystemExit(f"STOP: LIMIT set changed: {limits}")
    if any(g["verdict_class"] != "FAIL" for g in draft["gates"]["list"] if g["world"] == "Q11_OMITTED_OPERATOR"):
        raise SystemExit("STOP: every Q11 gate must remain HARD FAIL")
    if draft["terminal_logic"]["post_terminal_label"] != "POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION":
        raise SystemExit("STOP: post-terminal label changed")

    for key, (rel, expected) in REQUIRED_INPUTS.items():
        p = root / rel
        if sha256(p) != expected:
            raise SystemExit(f"STOP: required input SHA mismatch: {key}")
        if draft["inputs"][key]["sha256"] != expected:
            raise SystemExit(f"STOP: V2 draft input binding changed: {key}")
    join = draft["structural_support_join_reproduced"]
    if set(join.values()) != {MASK_SHA256}:
        raise SystemExit("STOP: structural-support mask binding changed")
    return draft


def build_final_contract(root: Path) -> dict:
    _load_payload(root)
    return {
        "schema": "V79_V2_CORE_QUALIFICATION_CONTRACT_V2_FINAL_AUTHORITY",
        "name": "V79_V2_CORE_FROZEN_MODEL_AND_PROSPECTIVE_SYNTHETIC_QUALIFICATION_CONTRACT",
        "status": FINAL_STATUS,
        "launch_authority": True,
        "world_generation_authorized": False,
        "qualification_fits_run": 0,
        "controller_authority": {
            "ruling_pr": 288,
            "ruling_comment": CONTROLLER_RULING_COMMENT,
            "model_decision": CONTROLLER_MODEL_DECISION,
            "source_interpretation": "predictive/acquisition-source structure among estimable measured comparisons; not universal causal source biology",
            "single_source_gene_rule": "cross-source estimand undefined/unevaluable; do not count as source-effect evidence",
        },
        "required_inputs": {
            "qualification_payload": {
                "path": DRAFT_REL,
                "sha256": DRAFT_SHA256,
                "status": "PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION",
                "role": "immutable controller-accepted prospective qualification payload",
            },
            "historical_v1": {
                "path": V1_REL,
                "sha256": V1_SHA256,
                "role": "historical pre-controller draft; never launch authority",
            },
            **{k: {"path": p, "sha256": s} for k, (p, s) in REQUIRED_INPUTS.items()},
            "structural_support_mask_sha256": MASK_SHA256,
        },
        "accepted_qualification_arithmetic": {
            "worlds": 12,
            "genes_per_world": 44,
            "planned_fits": 1056,
            "hard_statistical_gates": 260,
            "hard_rule_gates": 28,
            "limit_statistical_gates": 4,
            "familywise_false_fail": 0.05,
            "alpha_per_gate": 0.05 / 260.0,
        },
        "accepted_gate_policy": {
            "limit_gates": [
                "Q01_WEAK_DONOR/detection/BIAS_DONOR_SD",
                "Q01_WEAK_DONOR/positive/BIAS_DONOR_SD",
                "Q08_SPARSE_DETECTION/positive/BIAS_DONOR_SD",
                "Q09_POSITIVE_TAIL/positive/BIAS_DONOR_SD",
            ],
            "q11_all_gates": "HARD_FAIL",
            "first_scientific_fail_terminal": "V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED",
            "post_terminal_label": "POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION",
            "infrastructure_hash_custody_poison_failure": "STOP_IMMEDIATELY",
        },
        "boundaries": {
            "training_authorized": False,
            "real_train_posterior_inference": False,
            "factorial_science": False,
            "test_split": False,
            "morabito": False,
            "pathology": False,
            "target_discovery": False,
            "world_generation_before_controller_prelaunch_review": False,
        },
        "generated_outputs_scope": [
            "this final authority envelope",
            "its SHA-256 sidecar",
            "finalizer/validator code and tests",
            "CI/regeneration evidence",
            "updated controller/audit/handoff state",
        ],
        "explicitly_not_generated": [
            "Q00-Q11 realized worlds",
            "truth tables",
            "world manifests",
            "benchmark outputs",
            "qualification fits",
            "posterior samples",
            "corrected-TRAIN posterior inference",
            "factorial scientific outputs",
            "JEPA checkpoints",
        ],
    }


def serialize_contract(contract: dict) -> bytes:
    return (json.dumps(contract, indent=1, sort_keys=False) + "\n").encode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    out = a.root / FINAL_REL
    expected = serialize_contract(build_final_contract(a.root))
    digest = hashlib.sha256(expected).hexdigest()
    sidecar = out.with_suffix(".sha256")
    if a.check:
        if out.read_bytes() != expected:
            raise SystemExit("STOP: committed final V2 authority differs from deterministic rebuild")
        if sidecar.read_text(encoding="utf-8").strip() != f"{digest}  {out.name}":
            raise SystemExit("STOP: final V2 SHA sidecar mismatch")
        print(f"final V2 authority rebuild identical: {digest}")
        return
    out.write_bytes(expected)
    sidecar.write_text(f"{digest}  {out.name}\n", encoding="utf-8", newline="\n")
    print(digest)


if __name__ == "__main__":
    main()
