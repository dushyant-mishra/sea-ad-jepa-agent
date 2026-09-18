from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import Path

import pytest

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha
from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import CACHE_ROLE_ID
from sea_ad_jepa.v5.full104_masking_gpu_preflight_v1 import (
    EXPECTED_BLOCK_MANIFEST_SHA256,
    EXPECTED_OBSERVATION_STATE_SHA256,
    EXPECTED_REGISTRY_SHA256,
    validate_calibration_bindings,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import (
    PRIMARY_ATTACKER_ID,
    PRIMARY_SCORE_ID,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v2 import (
    BURDEN_SEPARATION_POLICY_ID,
    CONFIRMATION_ROLE_ID,
    ORIGIN_POLICY_ID,
    MaskingQualificationParametersAuthorityV2,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def parameters_payload(**updates):
    values = dict(
        authority_id="TEST",
        primary_attacker_id=PRIMARY_ATTACKER_ID,
        primary_score_id=PRIMARY_SCORE_ID,
        targeted_partner_cap=8,
        ridge_candidate_pool_count=64,
        ridge_score_feature_count=32,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=20,
        prefix_floor_numerator=1,
        prefix_floor_denominator=20,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
        discovery_expanded_validation_report_sha256=h("report"),
        discovery_universe_scale_script_sha256=h("universe"),
        discovery_outside800_unified_script_sha256=h("outside"),
        discovery_provenance_note_sha256=h("provenance"),
        parameter_origin_policy_id=ORIGIN_POLICY_ID,
        confirmation_role_id=CONFIRMATION_ROLE_ID,
        burden_separation_policy_id=BURDEN_SEPARATION_POLICY_ID,
        terminal_full104_masking_outcomes_inspected=False,
        training_authorized=False,
    )
    values.update(updates)
    obj = MaskingQualificationParametersAuthorityV2(**values)
    payload = {"schema": "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V2", **asdict(obj)}
    payload["parameter_authority_sha256"] = obj.canonical_digest()
    return payload


def receipt(schema: str, **values):
    payload = {
        "schema": schema,
        "terminal_masking_outcomes_inspected": False,
        **values,
    }
    payload["receipt_sha256"] = canonical_sha(payload)
    return payload


class CacheManifestStub:
    def __init__(self, **updates):
        values = dict(
            cache_role_id=CACHE_ROLE_ID,
            full104_block_manifest_sha256=EXPECTED_BLOCK_MANIFEST_SHA256,
            canonical_registry_sha256=EXPECTED_REGISTRY_SHA256,
            census_authority_sha256="",
            support_estimability_authority_sha256=h("support-file"),
            split_receipt_sha256="",
            target_eligibility_receipt_sha256="",
            terminal_masking_qualification_authorized=False,
            training_authorized=False,
        )
        values.update(updates)
        self.__dict__.update(values)

    def assert_calibration_only(self):
        if self.cache_role_id != CACHE_ROLE_ID:
            raise ValueError("cache is not calibration-only")


def valid_bundle():
    support_file_sha = h("support-file")
    support = {
        "schema": "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1",
        "full104_substrate_sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
        "missing_value_semantics_id": "UNMEASURED_IS_MISSING_NOT_ZERO",
        "training_authorized": False,
    }
    registry_authority = {
        "schema": "V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1",
        "ADDRESS_REGISTRY": {"sha256": EXPECTED_REGISTRY_SHA256, "row_count": 41238},
        "FULL104_SUBSTRATE": {
            "sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
            "cells": 4553407,
            "donors": 104,
        },
        "OPERATOR_ADDRESS_OBSERVATION_STATE": {"sha256": EXPECTED_OBSERVATION_STATE_SHA256},
        "training_authorized": False,
    }
    split = receipt(
        "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1",
        n_folds=4,
        fold_sizes=[28, 26, 25, 25],
    )
    eligibility = receipt(
        "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",
        eligible_target_count=17053,
        split_receipt_sha256=split["receipt_sha256"],
        strict_core_cols=list(range(17186)),
    )
    census = {
        "schema": "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2",
        "training_authorized": False,
        "terminal_masking_outcomes_inspected": False,
        "substrate": {
            "full104_block_manifest_sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
            "operator_address_observation_state_sha256": EXPECTED_OBSERVATION_STATE_SHA256,
        },
        "support_estimability_authority": {"sha256": support_file_sha},
        "execution_receipts": {
            "split_receipt_sha256": split["receipt_sha256"],
            "target_eligibility_receipt_sha256": eligibility["receipt_sha256"],
        },
    }
    census["census_authority_sha256"] = canonical_sha(census)
    cache = CacheManifestStub(
        census_authority_sha256=census["census_authority_sha256"],
        split_receipt_sha256=split["receipt_sha256"],
        target_eligibility_receipt_sha256=eligibility["receipt_sha256"],
    )
    return registry_authority, support, support_file_sha, parameters_payload(), census, split, eligibility, cache


def call_valid(**overrides):
    registry, support, support_sha, params, census, split, eligibility, cache = valid_bundle()
    values = dict(
        block_manifest_sha256=EXPECTED_BLOCK_MANIFEST_SHA256,
        observation_state_sha256=EXPECTED_OBSERVATION_STATE_SHA256,
        registry_file_sha256=EXPECTED_REGISTRY_SHA256,
        registry_authority=registry,
        support_authority=support,
        support_file_sha256=support_sha,
        parameters_payload=params,
        census_payload=census,
        split_payload=split,
        eligibility_payload=eligibility,
        cache_manifest=cache,
        cache_manifest_sha256=h("cache-manifest"),
    )
    values.update(overrides)
    return validate_calibration_bindings(**values)


def test_calibration_preflight_closes_current_full104_roots():
    roots = call_valid()
    assert roots["parameters_authority_sha256"] == parameters_payload()["parameter_authority_sha256"]
    assert roots["cache_manifest_sha256"] == h("cache-manifest")


def test_calibration_preflight_rejects_registry_splice():
    with pytest.raises(ValueError, match="registry file root"):
        call_valid(registry_file_sha256=h("smaller-historical-registry"))


def test_calibration_preflight_rejects_post_outcome_parameter_reuse():
    with pytest.raises(ValueError, match="before terminal FULL104"):
        call_valid(parameters_payload=parameters_payload(terminal_full104_masking_outcomes_inspected=True))


def test_calibration_preflight_rejects_cache_promoted_to_terminal_role():
    _, _, _, _, _, _, _, cache = valid_bundle()
    cache.cache_role_id = "AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1"
    with pytest.raises(ValueError, match="calibration-only"):
        call_valid(cache_manifest=cache)


def test_terminal_python_preflight_binds_checkpoint_semantics_not_json_file_bytes():
    source = Path("scripts/agent/validate_full104_masking_gpu_preflight_v1.py").read_text(encoding="utf-8")
    assert "semantic_sha256(checkpoint_payload)" in source
    assert "bind_machine_checkpoint_semantic" in source
    assert "checkpoint_sha = sha256_file(checkpoint_path)" not in source
    assert 'control_calibration_precision_authority_v2.py' in source
    assert 'control_calibration_precision_authority_v1.py' not in source


def test_powershell_wrapper_is_current_fail_closed_and_non_destructive():
    source = Path("scripts/agent/v5_full104_masking_gpu_preflight_20260918.ps1").read_text(encoding="utf-8")
    assert 'ValidateSet("Calibration","Terminal")' in source
    assert "ExpectedScientificAnchor" in source
    assert "CURRENT_WORK_CHECKPOINT_STATE.json" in source
    assert "validate_full104_masking_gpu_preflight_v1.py" in source
    assert "AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM" not in source or "Terminal" in source
    assert "critical focused suite reported a skip" in source
    assert "Run FULL104 masking authority regressions" in source
    lowered = source.lower()
    assert "git reset" not in lowered
    assert "git clean" not in lowered
    assert "git stash" not in lowered
    assert "8ee5d0a5be483e18819a6f6975efa183327b2158" not in source
