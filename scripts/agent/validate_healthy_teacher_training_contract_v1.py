#!/usr/bin/env python3
"""Fail-closed validator for HEALTHY_TEACHER_TRAINING_BASE_CONTRACT_V1.

The frozen base must keep all execution-specific bindings null. Future successor/u0
facts belong in a separate immutable overlay. No command-line bypass exists.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import re

POPULATION_ROOT = "e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7"
F1B_ROOT = "daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b"
HISTORICAL_U0 = "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4"
KNOWN_INCOMPLETE_KERNEL = "c0eaf2acc0a5edc837fb2a48f726b9d626772f06"
READER_SPLIT = "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"
INVENTORY = "7ac13973162a46cafa5baa24c5bea14beb64bd5859e8f58900801eee07083a30"
SCHEDULE = "4657d669658712234d7ee8ede9496297009b808d4902766a9e43f7591ca640fc"
ADDRESS_NAMESPACE = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
OBSERVATION_STATE = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"


def _nonnull(value: Any) -> bool:
    return value not in (None, "", "BLOCKED_PENDING_REVIEWED_SUCCESSOR")


def _is_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{%d}" % length, value))


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []

    if contract.get("schema") != "HEALTHY_TEACHER_TRAINING_BASE_CONTRACT_V1":
        failures.append("schema mismatch")
    upstream = contract.get("upstream_authorities", {})
    if upstream.get("population_access_registry", {}).get("package_root_sha256") != POPULATION_ROOT:
        failures.append("population registry root mismatch")
    if upstream.get("f1b_attack_authority", {}).get("package_root_sha256") != F1B_ROOT:
        failures.append("F1-B attack root mismatch")

    population = contract.get("training_population", {})
    expected_population = {
        "donor_count": 104,
        "cell_count": 3292,
        "reader_split_sha256": READER_SPLIT,
        "inventory_sha256": INVENTORY,
    }
    for key, expected in expected_population.items():
        if population.get(key) != expected:
            failures.append(f"training population {key} mismatch")
    for key in (
        "continuation_train_included",
        "reader_validation_included",
        "reader_oracle_included",
        "foundation_development_included",
        "foundation_sealed_holdout_included",
        "pathology_access",
    ):
        if population.get(key) is not False:
            failures.append(f"protected population flag must be false: {key}")

    corpus = contract.get("corpus_and_address", {})
    if corpus.get("address_count") != 41238:
        failures.append("address count mismatch")
    if corpus.get("address_namespace_sha256") != ADDRESS_NAMESPACE:
        failures.append("address namespace mismatch")
    if corpus.get("observation_state_sha256") != OBSERVATION_STATE:
        failures.append("observation-state authority mismatch")

    sampler = contract.get("sampler", {})
    if sampler.get("schedule_sha256") != SCHEDULE:
        failures.append("training schedule mismatch")
    if sampler.get("replay_cap") != 8 or sampler.get("scheduled_presentations") != 26240:
        failures.append("sampler cap/presentation geometry mismatch")
    if sampler.get("same_update_duplicates_required") != 0:
        failures.append("same-update duplicates must be zero")

    geometry = contract.get("batch_geometry", {})
    if geometry.get("effective_batch") != 128 or geometry.get("microbatch") != 8:
        failures.append("batch geometry mismatch")
    if geometry.get("views") != 4:
        failures.append("view count mismatch")

    model = contract.get("model_and_masking", {})
    expected_model = {
        "vocabulary_size": 41238,
        "width": 160,
        "transformer_blocks": 6,
        "attention_heads": 4,
        "gradient_checkpointing": True,
        "views_per_cell": 4,
        "mask_fraction": 0.40,
        "target_block_count": 16,
    }
    for key, expected in expected_model.items():
        if model.get(key) != expected:
            failures.append(f"model/masking {key} mismatch")
    if model.get("target_mask_eligibility") != "MEASURED_SCALAR only":
        failures.append("mask eligibility mismatch")

    optimizer = contract.get("optimizer", {})
    expected_optimizer = {
        "type": "AdamW",
        "lr": 0.0001,
        "lr_schedule": "constant through u205",
        "betas": [0.9, 0.999],
        "eps": 1e-8,
        "weight_decay": 0.01,
        "ema_momentum": 0.996,
    }
    for key, expected in expected_optimizer.items():
        if optimizer.get(key) != expected:
            failures.append(f"optimizer {key} mismatch")

    precision = contract.get("precision_and_determinism", {})
    if precision.get("forward") != "fp16 autocast":
        failures.append("forward precision mismatch")
    if "autocast(enabled=False)" not in str(precision.get("backward")):
        failures.append("C2 backward repair absent")
    if precision.get("tf32") is not False or precision.get("deterministic_algorithms") is not True:
        failures.append("determinism/TF32 mismatch")

    gates = contract.get("gates", {})
    gradient = gates.get("pre_step_gradient_gate", {})
    if gradient.get("mandatory_backbone_count") != 48:
        failures.append("mandatory backbone count mismatch")
    if sorted(gradient.get("reject", [])) != ["exact_zero", "missing", "nonfinite"]:
        failures.append("gradient rejection semantics mismatch")
    if gradient.get("magnitude_floor") != "none; any finite nonzero live gradient is eligible":
        failures.append("arbitrary gradient magnitude floor introduced")

    movement = gates.get("movement_gate", {})
    if movement.get("fixed_2x_decay_margin_authorized") is not False:
        failures.append("hard-coded 2x decay margin is forbidden")
    if movement.get("scope") != "per mandatory tensor; pooled mean forbidden":
        failures.append("movement must be per tensor")

    qualification = contract.get("qualification_phase", {})
    if qualification.get("start_update") != 0 or qualification.get("stop_update") != 40:
        failures.append("formal qualification horizon must be exactly 0->40")
    if qualification.get("automatic_continuation") is not False:
        failures.append("qualification must not auto-continue")
    if qualification.get("checkpoint_updates") != [0, 10, 25, 40]:
        failures.append("qualification checkpoint schedule mismatch")

    continuation = contract.get("continuation_phase", {})
    if continuation.get("start_from_checkpoint") != 40 or continuation.get("final_update") != 205:
        failures.append("full continuation horizon mismatch")
    if continuation.get("checkpoint_updates") != [50, 100, 200, 205]:
        failures.append("continuation checkpoint schedule mismatch")
    if "explicit continuation authority" not in continuation.get("continuation_requires", []):
        failures.append("explicit continuation authority missing")

    firewall = contract.get("biological_firewall", {})
    for key in (
        "inline_reader_validation_evaluation",
        "inline_reader_oracle_evaluation",
        "foundation_development_access",
        "foundation_sealed_holdout_access",
        "external_holdout_access",
        "pathology_access",
        "d1_real_execution",
    ):
        if firewall.get(key) is not False:
            failures.append(f"biological firewall flag must be false: {key}")
    if firewall.get("biological_success_thresholds") is not None:
        failures.append("biology-dependent training threshold introduced")

    initialization = contract.get("initialization_policy", {})
    if initialization.get("historical_clean_u0_reference_sha256") != HISTORICAL_U0:
        failures.append("historical clean u0 reference mismatch")
    forbidden = " ".join(initialization.get("forbidden", []))
    for bad in ("historical u10", "historical u205", "defect-inherited"):
        if bad not in forbidden:
            failures.append(f"initialization prohibition missing: {bad}")
    if initialization.get("required_new_u0", {}).get("must_be_frozen_before_u1") is not True:
        failures.append("new successor-bound u0 must freeze before u1")

    bindings = contract.get("execution_bindings", {})
    if bindings.get("binding_mode") != "SEPARATE_IMMUTABLE_OVERLAY_REQUIRED":
        failures.append("execution binding mode must require separate immutable overlay")
    if bindings.get("ready") is not False:
        failures.append("frozen base execution ready flag must remain false")

    immutable_null_fields = (
        "integrated_successor_commit",
        "integrated_successor_source_manifest_root",
        "independent_external_review_terminal",
        "independent_external_review_artifact_sha256",
        "independent_external_review_reviewed_commit",
        "initialization_checkpoint_path",
        "initialization_checkpoint_sha256",
        "initialization_mode",
        "initialization_materialization_attestation_sha256",
        "predictor_mandatory_registry_sha256",
        "movement_adjudicator_sha256",
    )
    populated = [key for key in immutable_null_fields if bindings.get(key) is not None]
    if populated:
        failures.append(
            "frozen base execution fields must remain null; use separate overlay: "
            + ",".join(populated)
        )
    if "MUST remain null/false" not in str(bindings.get("immutable_null_policy")):
        failures.append("immutable null policy missing")

    overlay = contract.get("future_binding_overlay", {})
    if overlay.get("schema") != "HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1":
        failures.append("future execution overlay schema missing")
    if overlay.get("may_modify_base_contract") is not False:
        failures.append("future overlay must not modify frozen base")
    if overlay.get("overlay_itself_is_execution_authority") is not False:
        failures.append("binding overlay must not itself authorize execution")
    if overlay.get("required_base_binding") != "frozen base package root SHA-256":
        failures.append("future overlay must bind frozen base package root")

    required_overlay_fields = set(immutable_null_fields)
    if set(overlay.get("required_fields", [])) != required_overlay_fields:
        failures.append("future overlay required-field set mismatch")

    if contract.get("terminal") != "PASS_HEALTHY_TEACHER_BASE_CONTRACT_READY_FOR_FREEZE__EXECUTION_UNAUTHORIZED":
        failures.append("base contract terminal mismatch")

    terminal = (
        "PASS_HEALTHY_TEACHER_BASE_CONTRACT_READY_FOR_FREEZE__EXECUTION_UNAUTHORIZED"
        if not failures
        else "STOP_HEALTHY_TEACHER_BASE_CONTRACT_INVALID"
    )
    return {
        "schema": "healthy-teacher-training-contract-validation-v1",
        "failures": failures,
        "populated_execution_fields": populated,
        "terminal": terminal,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = validate_contract(contract)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["terminal"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
