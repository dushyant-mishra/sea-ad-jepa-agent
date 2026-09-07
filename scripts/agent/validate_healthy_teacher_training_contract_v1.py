#!/usr/bin/env python3
"""Fail-closed validator for HEALTHY_TEACHER_TRAINING_CONTRACT_V1.

The current draft is expected to STOP until successor/u0 bindings are populated.
No command-line bypass exists.
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

    if contract.get("schema") != "HEALTHY_TEACHER_TRAINING_CONTRACT_V1_DRAFT":
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
    required_binding_fields = (
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
    unbound = [key for key in required_binding_fields if not _nonnull(bindings.get(key))]
    if bindings.get("ready") is True and unbound:
        failures.append("execution bindings marked ready while fields are unbound")
    if not unbound and bindings.get("ready") is not True:
        failures.append("all execution bindings populated but ready is not true")

    if _nonnull(bindings.get("integrated_successor_commit")):
        if not _is_hex(bindings["integrated_successor_commit"], 40):
            failures.append("integrated successor commit is not a 40-hex SHA")
        if bindings["integrated_successor_commit"] == KNOWN_INCOMPLETE_KERNEL:
            failures.append("known incomplete mechanics kernel cannot be final successor binding")
    for key in (
        "integrated_successor_source_manifest_root",
        "independent_external_review_artifact_sha256",
        "initialization_checkpoint_sha256",
        "initialization_materialization_attestation_sha256",
        "predictor_mandatory_registry_sha256",
        "movement_adjudicator_sha256",
    ):
        if _nonnull(bindings.get(key)) and not _is_hex(bindings[key], 64):
            failures.append(f"{key} is not a 64-hex SHA-256")

    review = bindings.get("independent_external_review_terminal")
    if _nonnull(review) and not (isinstance(review, str) and review.startswith("PASS_") and "REVIEW" in review):
        failures.append("independent external review terminal is not a PASS review terminal")
    reviewed_commit = bindings.get("independent_external_review_reviewed_commit")
    if _nonnull(reviewed_commit):
        if not _is_hex(reviewed_commit, 40):
            failures.append("independent external review reviewed commit is not a 40-hex SHA")
        elif _nonnull(bindings.get("integrated_successor_commit")) and reviewed_commit != bindings.get("integrated_successor_commit"):
            failures.append("external review is not bound to the integrated successor commit")

    init_mode = bindings.get("initialization_mode")
    allowed_init_modes = {
        "successor-bound import of clean historical u0 state",
        "successor-bound mixed import plus prospectively seeded changed components",
    }
    if _nonnull(init_mode) and init_mode not in allowed_init_modes:
        failures.append("initialization mode is not prospectively allowed")

    init_sha = bindings.get("initialization_checkpoint_sha256")
    if _nonnull(init_sha) and init_sha == HISTORICAL_U0:
        failures.append("historical u0 cannot be used directly as successor execution checkpoint")
    required_u0_sha = initialization.get("required_new_u0", {}).get("exact_sha256")
    if not unbound:
        if required_u0_sha != init_sha:
            failures.append("successor-bound u0 policy SHA does not match execution binding")

    scaler = precision.get("grad_scaler", {})
    if scaler != {
        "initial_scale": 65536.0,
        "growth_factor": 2.0,
        "backoff_factor": 0.5,
        "growth_interval": 2000,
    }:
        failures.append("GradScaler contract mismatch")

    if gates.get("optimizer_step_gate", {}).get("before_ema") is not True:
        failures.append("optimizer step proof must precede EMA")
    if gates.get("ema_gate", {}).get("equation_check") is not True:
        failures.append("EMA equation check missing")

    terminal = (
        "PASS_HEALTHY_TEACHER_TRAINING_CONTRACT_BOUND__EXECUTION_STILL_REQUIRES_AUTHORITY"
        if not failures and not unbound
        else (
            "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_UNBOUND"
            if not failures and unbound
            else "STOP_HEALTHY_TEACHER_TRAINING_CONTRACT_INVALID"
        )
    )
    return {
        "schema": "healthy-teacher-training-contract-validation-v1",
        "failures": failures,
        "unbound_fields": unbound,
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
