from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

import sea_ad_jepa.v5.audit_b_execution_preflight_v2 as P
from sea_ad_jepa.v5.audit_b_execution_contract_v2 import (
    AuditBExecutionContractV2,
    BURDEN_ESTIMATOR_SOURCE_SHA256,
    CANONICAL_REGISTRY_SHA256,
    EXECUTION_REQUIREMENTS,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    HEAVY_QUALIFICATION_RECEIPT_SHA256,
    MANDATORY_ROBUSTNESS_AGGREGATION_ID,
    MASK_PLAN_GENERATOR_SHA256,
    PARENT_PREEXECUTION_CONTRACT_SHA256,
    PHASE_IV_SAMPLE_ARTIFACT_SHA256,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
    PRECISION_ESTIMATOR_ID,
    PRECISION_RULE_AUTHORITY_SHA256,
    PRECISION_SCOPE_ID,
    PRIMARY_POLICY_ID,
    PRIMARY_RUNG,
    PRIMARY_TARGET_AGGREGATION_ID,
    RNG_AUTHORITY_SHA256,
    SCIENTIFIC_RESOLUTION_SHA256,
    SOURCE_STRATIFIED_REPORTING_ID,
    ZERO_MEAN_RULE_ID,
)

ROOT = Path(__file__).resolve().parents[1]
PHASE_IV = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv"
PHASE_I = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_i"
RESOLUTION = PHASE_IV / "AUDIT_B_SCIENTIFIC_RESOLUTION_V3.json"
PRECISION = PHASE_IV / "AUDIT_B_PRECISION_RULE_AUTHORITY_V2.json"
RNG = PHASE_IV / "MASKING_RNG_REPLAY_AUTHORITY_V3.json"
HEAVY_RECEIPT = PHASE_I / "HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2.json"


def contract(**updates) -> AuditBExecutionContractV2:
    values = dict(
        contract_id="TEST_B4_PREFLIGHT",
        parent_preexecution_contract_sha256=PARENT_PREEXECUTION_CONTRACT_SHA256,
        scientific_resolution_sha256=SCIENTIFIC_RESOLUTION_SHA256,
        precision_rule_authority_sha256=PRECISION_RULE_AUTHORITY_SHA256,
        phase_iv_sample_freeze_digest=PHASE_IV_SAMPLE_FREEZE_DIGEST,
        phase_iv_sample_artifact_sha256=PHASE_IV_SAMPLE_ARTIFACT_SHA256,
        full104_manifest_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        heavy_artifact_sha256=HEAVY_ARTIFACT_SHA256,
        heavy_qualification_receipt_sha256=HEAVY_QUALIFICATION_RECEIPT_SHA256,
        rng_authority_sha256=RNG_AUTHORITY_SHA256,
        mask_plan_generator_sha256=MASK_PLAN_GENERATOR_SHA256,
        burden_estimator_source_sha256=BURDEN_ESTIMATOR_SOURCE_SHA256,
        precision_scope_id=PRECISION_SCOPE_ID,
        target_aggregation_id=PRIMARY_TARGET_AGGREGATION_ID,
        mandatory_robustness_aggregation_id=MANDATORY_ROBUSTNESS_AGGREGATION_ID,
        primary_policy_id=PRIMARY_POLICY_ID,
        primary_rung_numerator=PRIMARY_RUNG.numerator,
        primary_rung_denominator=PRIMARY_RUNG.denominator,
        precision_estimator_id=PRECISION_ESTIMATOR_ID,
        relative_se_tolerance_numerator=1,
        relative_se_tolerance_denominator=20,
        absolute_se_tolerance_numerator=1,
        absolute_se_tolerance_denominator=860,
        absolute_tolerance_origin_id="ONE_AVERAGE_MASKED_ADDRESS_SHARE_AT_PRIMARY_5_PERCENT_RUNG_V1",
        zero_mean_rule_id=ZERO_MEAN_RULE_ID,
        reporting_scope_id="ALL_3_NONUNIFORM_X_6_RUNG_CELLS_REPORTED_V1",
        source_stratified_reporting_id=SOURCE_STRATIFIED_REPORTING_ID,
        execution_requirements=EXECUTION_REQUIREMENTS,
    )
    values.update(updates)
    return AuditBExecutionContractV2(**values)


def payload(c: AuditBExecutionContractV2) -> dict:
    return {
        "schema": "V5_AUDIT_B_EXECUTION_CONTRACT_V2",
        **asdict(c),
        "sample_ladder": list(c.sample_ladder),
        "execution_requirements": list(c.execution_requirements),
        "execution_authorized": c.execution_authorized,
        "contract_sha256": c.canonical_digest(),
        "terminal_masking_outcomes_inspected": False,
    }


def test_real_semantic_resolution_precision_and_rng_bind_to_b4() -> None:
    c = contract()
    resolution = P._load_resolution(RESOLUTION, c)
    precision = P._load_precision_rule(PRECISION, c)
    rng = P._load_rng(RNG, c)
    assert resolution.canonical_digest() == SCIENTIFIC_RESOLUTION_SHA256
    assert precision.canonical_digest() == PRECISION_RULE_AUTHORITY_SHA256
    assert rng.canonical_digest() == RNG_AUTHORITY_SHA256


def test_b4_contract_round_trip_is_execution_ready_but_not_terminal_authority(
    tmp_path: Path,
) -> None:
    c = contract()
    p = tmp_path / "contract.json"
    p.write_text(json.dumps(payload(c)), encoding="utf-8")
    loaded = P.require_contract_ready(p)
    assert loaded.execution_authorized is True
    assert loaded.terminal_masking_authorized is False
    assert loaded.training_authorized is False


def test_runtime_binding_success_rechecks_semantics_and_physical_roots(
    tmp_path: Path,
    monkeypatch,
) -> None:
    c = contract()
    sample = tmp_path / "sample"
    heavy = tmp_path / "heavy-artifact"
    plan = tmp_path / "plan"
    estimator = tmp_path / "estimator"
    manifest = tmp_path / "manifest"
    registry = tmp_path / "registry"
    for p in (sample, heavy, plan, estimator, manifest, registry):
        p.write_text("placeholder", encoding="utf-8")

    expected = {
        sample.name: c.phase_iv_sample_artifact_sha256,
        heavy.name: c.heavy_artifact_sha256,
        HEAVY_RECEIPT.name: c.heavy_qualification_receipt_sha256,
        RNG.name: "f" * 64,  # file bytes are descriptive; semantic digest is checked separately
        plan.name: c.mask_plan_generator_sha256,
        estimator.name: c.burden_estimator_source_sha256,
        manifest.name: c.full104_manifest_sha256,
        registry.name: c.canonical_registry_sha256,
    }
    monkeypatch.setattr(P, "sha256_file", lambda path: expected[Path(path).name])
    monkeypatch.setattr(P, "verify_phase_iv_sample_freeze", lambda *a, **k: {})

    out = P.verify_runtime_bindings(
        c,
        scientific_resolution=RESOLUTION,
        precision_rule_authority=PRECISION,
        sample_freeze=sample,
        heavy_artifact=heavy,
        heavy_qualification_receipt=HEAVY_RECEIPT,
        rng_authority=RNG,
        mask_plan_generator=plan,
        burden_estimator_source=estimator,
        full104_manifest=manifest,
        canonical_registry=registry,
        repo_root=tmp_path,
    )
    assert out["scientific_resolution_sha256"] == SCIENTIFIC_RESOLUTION_SHA256
    assert out["precision_rule_authority_sha256"] == PRECISION_RULE_AUTHORITY_SHA256
    assert out["rng_authority_sha256"] == RNG_AUTHORITY_SHA256


def test_resealed_or_modified_semantic_inputs_fail_closed(tmp_path: Path) -> None:
    c = contract()

    resolution = json.loads(RESOLUTION.read_text(encoding="utf-8"))
    resolution["target_aggregation_id"] = (
        "DONOR_UNIFORM_ACROSS_ALL_DONORS__TARGET_UNIFORM_V1"
    )
    bad_resolution = tmp_path / "resolution.json"
    bad_resolution.write_text(json.dumps(resolution), encoding="utf-8")
    with pytest.raises(ValueError, match="target_aggregation_id drifted|digest"):
        P._load_resolution(bad_resolution, c)

    precision = json.loads(PRECISION.read_text(encoding="utf-8"))
    precision["absolute_se_tolerance_denominator"] = 859
    bad_precision = tmp_path / "precision.json"
    bad_precision.write_text(json.dumps(precision), encoding="utf-8")
    with pytest.raises(ValueError, match="absolute_se_tolerance_denominator drifted|digest"):
        P._load_precision_rule(bad_precision, c)


def test_payload_cannot_lie_about_execution_authorization() -> None:
    c = contract()
    bad = payload(c)
    bad["execution_authorized"] = False
    with pytest.raises(ValueError, match="explicitly authorize"):
        P.contract_from_payload(bad)
