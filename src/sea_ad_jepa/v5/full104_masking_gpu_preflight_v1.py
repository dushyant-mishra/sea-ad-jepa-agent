"""Fail-closed validation for the current FULL104 masking GPU preflight.

This module validates authority/root closure only. It never opens masking outcomes,
selects a masking policy, or authorizes training.
"""
from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
from typing import Any, Mapping

from .full104_census_receipt_v2 import canonical_sha, sha256_file
from .full104_control_calibration_cache_evaluator_v1 import load_control_calibration_cache
from .masking_qualification_parameters_authority_v3 import MaskingQualificationParametersAuthorityV3
from .masking_qualification_run_contract_v4 import (
    CALIBRATION_CACHE_ROLE_ID,
    MaskingQualificationRunContractV4,
    TERMINAL_EXECUTION_INPUT_ROLE_ID,
)
from .masking_nonlinear_challenge_authority_v3 import NonlinearMaskingChallengeAuthorityV3
from .masking_rng_replay_authority_v2 import MaskingRngReplayAuthorityV2
from .outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from .precision_authority_v4 import QualificationPrecisionAuthorityV4
from .target_panel_authority_v3 import TargetPanelAuthorityV3

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_REGISTRY_SHA256 = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
EXPECTED_CELLS = 4553407
EXPECTED_DONORS = 104
EXPECTED_ADDRESSES = 41238
EXPECTED_CORE = 17186
EXPECTED_ELIGIBLE = 17053
EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256 = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"
EXPECTED_REGISTRY_AUTHORITY_CANONICAL_JSON_SHA256 = "3321f6a0acd5ae89faa4912dde2d2ebc7c9d52d2bccf82ef63e415ace51158c9"


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def typed(
    payload: Mapping[str, Any],
    cls: type,
    digest_fields: tuple[str, ...],
    expected_schema: str,
):
    if payload.get("schema") != expected_schema:
        raise ValueError(
            f"{cls.__name__} schema mismatch: expected {expected_schema}, "
            f"observed {payload.get('schema')!r}"
        )
    names = {item.name for item in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise ValueError(f"{cls.__name__} missing fields: {sorted(missing)[:5]}")
    obj = cls(**{name: payload[name] for name in names})
    obj.validate()
    declared = next((payload.get(name) for name in digest_fields if payload.get(name)), None)
    if declared is None:
        raise ValueError(f"{cls.__name__} lacks declared canonical digest")
    if declared != obj.canonical_digest():
        raise ValueError(f"{cls.__name__} canonical digest mismatch")
    return obj


def receipt_digest(payload: Mapping[str, Any], schema: str) -> str:
    if payload.get("schema") != schema:
        raise ValueError(f"receipt schema mismatch: expected {schema}")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise ValueError("receipt records terminal masking outcome access")
    semantic = dict(payload)
    declared = semantic.pop("receipt_sha256", None)
    if declared != canonical_sha(semantic):
        raise ValueError("receipt canonical digest mismatch")
    return str(declared)


def census_digest(payload: Mapping[str, Any]) -> str:
    if payload.get("schema") != "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise ValueError("census authority V2 is required")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise ValueError("census authority records terminal masking outcome access")
    if payload.get("training_authorized") is not False:
        raise ValueError("census authority unexpectedly authorizes training")
    semantic = dict(payload)
    declared = semantic.pop("census_authority_sha256", None)
    if declared != canonical_sha(semantic):
        raise ValueError("census authority canonical digest mismatch")
    return str(declared)


def validate_calibration_bindings(
    *,
    block_manifest_sha256: str,
    observation_state_sha256: str,
    registry_file_sha256: str,
    registry_authority: Mapping[str, Any],
    support_authority: Mapping[str, Any],
    support_file_sha256: str,
    parameters_payload: Mapping[str, Any],
    census_payload: Mapping[str, Any],
    split_payload: Mapping[str, Any],
    eligibility_payload: Mapping[str, Any],
    cache_manifest: Any,
    cache_manifest_sha256: str,
) -> dict[str, str]:
    if block_manifest_sha256 != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise ValueError("FULL104 block-manifest root mismatch")
    if observation_state_sha256 != EXPECTED_OBSERVATION_STATE_SHA256:
        raise ValueError("observation-state root mismatch")
    if registry_file_sha256 != EXPECTED_REGISTRY_SHA256:
        raise ValueError("canonical registry file root mismatch")

    if canonical_sha(dict(registry_authority)) != EXPECTED_REGISTRY_AUTHORITY_CANONICAL_JSON_SHA256:
        raise ValueError("canonical registry authority is not the exact current semantic authority")
    if registry_authority.get("schema") != "V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1":
        raise ValueError("canonical registry authority schema mismatch")
    registry = registry_authority.get("ADDRESS_REGISTRY", {})
    substrate = registry_authority.get("FULL104_SUBSTRATE", {})
    observation = registry_authority.get("OPERATOR_ADDRESS_OBSERVATION_STATE", {})
    if registry.get("sha256") != EXPECTED_REGISTRY_SHA256 or registry.get("row_count") != EXPECTED_ADDRESSES:
        raise ValueError("canonical registry authority does not bind current registry")
    if substrate.get("sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise ValueError("canonical registry authority binds a different FULL104 substrate")
    if substrate.get("cells") != EXPECTED_CELLS or substrate.get("donors") != EXPECTED_DONORS:
        raise ValueError("canonical registry authority FULL104 population mismatch")
    if observation.get("sha256") != EXPECTED_OBSERVATION_STATE_SHA256:
        raise ValueError("canonical registry authority observation-state root mismatch")
    if registry_authority.get("training_authorized") is not False:
        raise ValueError("canonical registry authority unexpectedly authorizes training")

    if canonical_sha(dict(support_authority)) != EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256:
        raise ValueError("support authority is not the exact current semantic authority")
    if support_authority.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise ValueError("support authority schema mismatch")
    if support_authority.get("full104_substrate_sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise ValueError("support authority binds a different FULL104 substrate")
    if support_authority.get("missing_value_semantics_id") != "UNMEASURED_IS_MISSING_NOT_ZERO":
        raise ValueError("support authority missing-value semantics mismatch")
    if support_authority.get("training_authorized") is not False:
        raise ValueError("support authority unexpectedly authorizes training")

    parameters = typed(
        parameters_payload,
        MaskingQualificationParametersAuthorityV3,
        ("parameter_authority_sha256", "authority_sha256"),
        "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3",
    )
    if parameters.full104_substrate_sha256 != block_manifest_sha256:
        raise ValueError("masking parameters bind a different FULL104 substrate")
    if parameters.support_estimability_authority_sha256 != EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256:
        raise ValueError("masking parameters bind a different support authority")
    if parameters.terminal_universe_id != "FULL_COMMON_CORE_17186_V1":
        raise ValueError("masking parameters bind a different terminal universe")
    if parameters.terminal_universe_size != EXPECTED_CORE:
        raise ValueError("masking parameters bind a different terminal-universe size")
    split_root = receipt_digest(
        split_payload, "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1"
    )
    eligibility_root = receipt_digest(
        eligibility_payload, "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1"
    )
    if split_payload.get("n_folds") != 4 or split_payload.get("fold_sizes") != [28, 26, 25, 25]:
        raise ValueError("current four-fold donor split mismatch")
    if eligibility_payload.get("eligible_target_count") != EXPECTED_ELIGIBLE:
        raise ValueError("current eligible target count mismatch")
    if eligibility_payload.get("split_receipt_sha256") != split_root:
        raise ValueError("target eligibility binds a different donor split")
    strict_core = eligibility_payload.get("strict_core_cols", ())
    if len(strict_core) != EXPECTED_CORE:
        raise ValueError("strict common-core size mismatch")

    census_root = census_digest(census_payload)
    csubstrate = census_payload.get("substrate", {})
    if csubstrate.get("full104_block_manifest_sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise ValueError("census authority binds a different FULL104 substrate")
    if csubstrate.get("operator_address_observation_state_sha256") != EXPECTED_OBSERVATION_STATE_SHA256:
        raise ValueError("census authority binds a different observation state")
    if census_payload.get("support_estimability_authority", {}).get("sha256") != support_file_sha256:
        raise ValueError("census authority binds a different support authority")
    receipts = census_payload.get("execution_receipts", {})
    pass1_binding_root = csubstrate.get("pass1_physical_binding_sha256")
    if not isinstance(pass1_binding_root, str) or len(pass1_binding_root) != 64:
        raise ValueError("census authority lacks current physical pass1 binding")
    if receipts.get("pass1_physical_binding_receipt_sha256") != pass1_binding_root:
        raise ValueError("census authority physical pass1 receipt mismatch")
    if split_payload.get("pass1_physical_binding_sha256") != pass1_binding_root:
        raise ValueError("donor split binds a different physical pass1 proof")
    if eligibility_payload.get("pass1_physical_binding_sha256") != pass1_binding_root:
        raise ValueError("target eligibility binds a different physical pass1 proof")
    if receipts.get("split_receipt_sha256") != split_root:
        raise ValueError("census authority binds a different donor split")
    if receipts.get("target_eligibility_receipt_sha256") != eligibility_root:
        raise ValueError("census authority binds a different target-eligibility receipt")

    cache_manifest.assert_calibration_only()
    if cache_manifest.cache_role_id != CALIBRATION_CACHE_ROLE_ID:
        raise ValueError("cache role is not calibration-only")
    if cache_manifest.full104_block_manifest_sha256 != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise ValueError("calibration cache binds a different FULL104 substrate")
    if cache_manifest.canonical_registry_sha256 != EXPECTED_REGISTRY_SHA256:
        raise ValueError("calibration cache binds a different canonical registry")
    if cache_manifest.census_authority_sha256 != census_root:
        raise ValueError("calibration cache binds a different census authority")
    if cache_manifest.pass1_physical_binding_sha256 != pass1_binding_root:
        raise ValueError("calibration cache binds a different physical pass1 proof")
    if cache_manifest.support_estimability_authority_sha256 != support_file_sha256:
        raise ValueError("calibration cache binds a different support authority")
    if cache_manifest.split_receipt_sha256 != split_root:
        raise ValueError("calibration cache binds a different donor split")
    if cache_manifest.target_eligibility_receipt_sha256 != eligibility_root:
        raise ValueError("calibration cache binds a different target eligibility")
    if cache_manifest.terminal_masking_qualification_authorized is not False:
        raise ValueError("calibration cache unexpectedly authorizes terminal masking")
    if cache_manifest.training_authorized is not False:
        raise ValueError("calibration cache unexpectedly authorizes training")

    return {
        "parameters_authority_sha256": parameters.canonical_digest(),
        "census_authority_sha256": census_root,
        "pass1_physical_binding_sha256": pass1_binding_root,
        "split_receipt_sha256": split_root,
        "target_eligibility_receipt_sha256": eligibility_root,
        "support_authority_file_sha256": support_file_sha256,
        "cache_manifest_sha256": cache_manifest_sha256,
    }


def validate_calibration_files(
    *,
    level4_root: Path,
    observation_state: Path,
    registry_file: Path,
    registry_authority_file: Path,
    support_authority_file: Path,
    parameters_authority_file: Path,
    census_authority_file: Path,
    split_receipt_file: Path,
    target_eligibility_file: Path,
    cache_dir: Path,
) -> dict[str, str]:
    manifest = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    cache = load_control_calibration_cache(cache_dir)
    return validate_calibration_bindings(
        block_manifest_sha256=sha256_file(manifest),
        observation_state_sha256=sha256_file(observation_state),
        registry_file_sha256=sha256_file(registry_file),
        registry_authority=load_json(registry_authority_file),
        support_authority=load_json(support_authority_file),
        support_file_sha256=sha256_file(support_authority_file),
        parameters_payload=load_json(parameters_authority_file),
        census_payload=load_json(census_authority_file),
        split_payload=load_json(split_receipt_file),
        eligibility_payload=load_json(target_eligibility_file),
        cache_manifest=cache.manifest,
        cache_manifest_sha256=cache.manifest_sha256,
    )


def validate_terminal_bindings(
    *,
    calibration_roots: Mapping[str, str],
    target_panel_payload: Mapping[str, Any],
    precision_payload: Mapping[str, Any],
    outer_split_payload: Mapping[str, Any],
    nonlinear_payload: Mapping[str, Any],
    rng_payload: Mapping[str, Any],
    run_contract_payload: Mapping[str, Any],
) -> dict[str, str]:
    panel = typed(
        target_panel_payload,
        TargetPanelAuthorityV3,
        ("authority_sha256",),
        "V5_TARGET_PANEL_AUTHORITY_V3",
    )
    precision = typed(
        precision_payload,
        QualificationPrecisionAuthorityV4,
        ("authority_sha256",),
        "V5_QUALIFICATION_PRECISION_AUTHORITY_V4",
    )
    outer = typed(
        outer_split_payload,
        OuterDonorSplitAuthorityV1,
        ("authority_sha256",),
        "V5_OUTER_DONOR_SPLIT_AUTHORITY_V1",
    )
    nonlinear = typed(
        nonlinear_payload,
        NonlinearMaskingChallengeAuthorityV3,
        ("authority_sha256",),
        "V5_NONLINEAR_MASKING_CHALLENGE_AUTHORITY_V3",
    )
    rng = typed(
        rng_payload,
        MaskingRngReplayAuthorityV2,
        ("authority_sha256",),
        "V5_MASKING_RNG_REPLAY_AUTHORITY_V2",
    )
    contract = typed(
        run_contract_payload,
        MaskingQualificationRunContractV4,
        ("run_contract_sha256", "authority_sha256"),
        "V5_MASKING_QUALIFICATION_RUN_CONTRACT_V4",
    )
    if precision.target_panel_authority_sha256 != panel.canonical_digest():
        raise ValueError("precision authority binds a different target panel")
    if precision.outer_split_authority_sha256 != outer.canonical_digest():
        raise ValueError("precision authority binds a different outer split")
    if nonlinear.target_panel_authority_sha256 != panel.canonical_digest():
        raise ValueError("nonlinear authority binds a different target panel")
    if nonlinear.outer_split_authority_sha256 != outer.canonical_digest():
        raise ValueError("nonlinear authority binds a different outer split")
    if nonlinear.primary_parameters_authority_sha256 != calibration_roots["parameters_authority_sha256"]:
        raise ValueError("nonlinear authority binds different masking parameters")
    if contract.qualification_parameters_authority_sha256 != calibration_roots["parameters_authority_sha256"]:
        raise ValueError("run contract binds different masking parameters")
    if contract.census_authority_sha256 != calibration_roots["census_authority_sha256"]:
        raise ValueError("run contract binds a different census authority")
    if contract.support_estimability_authority_sha256 != calibration_roots["support_authority_file_sha256"]:
        raise ValueError("run contract binds a different support authority")
    if contract.control_calibration_cache_manifest_sha256 != calibration_roots["cache_manifest_sha256"]:
        raise ValueError("run contract binds a different calibration cache")
    if contract.outer_split_authority_sha256 != outer.canonical_digest():
        raise ValueError("run contract binds a different outer split")
    if contract.target_panel_authority_sha256 != panel.canonical_digest():
        raise ValueError("run contract binds a different target panel")
    if contract.precision_authority_sha256 != precision.canonical_digest():
        raise ValueError("run contract binds a different precision authority")
    if contract.nonlinear_challenge_authority_sha256 != nonlinear.canonical_digest():
        raise ValueError("run contract binds a different nonlinear authority")
    if contract.rng_replay_authority_sha256 != rng.canonical_digest():
        raise ValueError("run contract binds a different RNG authority")
    contract.assert_terminal_execution_input_role(TERMINAL_EXECUTION_INPUT_ROLE_ID)
    if contract.execution_input_role_id == CALIBRATION_CACHE_ROLE_ID:
        raise ValueError("calibration cache cannot be terminal execution input")
    return {
        "target_panel_authority_sha256": panel.canonical_digest(),
        "precision_authority_sha256": precision.canonical_digest(),
        "outer_split_authority_sha256": outer.canonical_digest(),
        "nonlinear_authority_sha256": nonlinear.canonical_digest(),
        "rng_authority_sha256": rng.canonical_digest(),
        "run_contract_sha256": contract.canonical_digest(),
    }
