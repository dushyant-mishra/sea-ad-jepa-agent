from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

import sea_ad_jepa.v5.audit_b_execution_preflight_v1 as P
from sea_ad_jepa.v5.audit_b_execution_contract_v1 import (
    CANONICAL_REGISTRY_SHA256,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    MASK_PLAN_GENERATOR_SHA256,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
    AuditBExecutionContractV1,
)
from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import MaskingRngReplayAuthorityV3


def h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def rng_authority() -> MaskingRngReplayAuthorityV3:
    return MaskingRngReplayAuthorityV3(
        authority_id="TEST_PREFLIGHT_RNG_V3",
        full104_substrate_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        outer_split_receipt_sha256="1" * 64,
        qualification_parameters_authority_sha256="2" * 64,
        burden_ladder_authority_sha256="3" * 64,
    )


def contract() -> AuditBExecutionContractV1:
    rng = rng_authority()
    return AuditBExecutionContractV1(
        contract_id="TEST_PREFLIGHT",
        phase_iv_sample_freeze_digest=PHASE_IV_SAMPLE_FREEZE_DIGEST,
        phase_iv_sample_artifact_sha256=h("sample"),
        full104_manifest_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        heavy_artifact_sha256=HEAVY_ARTIFACT_SHA256,
        heavy_qualification_receipt_sha256=h("heavy-receipt"),
        rng_authority_sha256=rng.canonical_digest(),
        mask_plan_generator_sha256=MASK_PLAN_GENERATOR_SHA256,
        burden_estimator_source_sha256=h("estimator"),
    )


def payload(c: AuditBExecutionContractV1) -> dict:
    d = {
        "schema": "V5_AUDIT_B_EXECUTION_CONTRACT_V1",
        **asdict(c),
        "sample_ladder": list(c.sample_ladder),
        "execution_requirements": list(c.execution_requirements),
        "execution_authorized": c.execution_authorized,
        "contract_sha256": c.canonical_digest(),
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    return d


def test_contract_payload_round_trip_and_digest_check() -> None:
    c = contract()
    loaded = P.contract_from_payload(payload(c))
    assert loaded.canonical_digest() == c.canonical_digest()

    bad = payload(c)
    bad["max_relative_standard_error"] = 0.50
    with pytest.raises(ValueError, match="threshold drifted"):
        P.contract_from_payload(bad)


def test_v1_contract_cannot_pass_execution_preflight(tmp_path: Path) -> None:
    p = tmp_path / "contract.json"
    p.write_text(json.dumps(payload(contract())))
    with pytest.raises(ValueError, match="STOP_AUDIT_B_V1_PREEXECUTION_ONLY"):
        P.require_contract_ready(p)


def test_runtime_binding_success_checks_rng_semantic_digest_not_file_hash(
    tmp_path: Path, monkeypatch
) -> None:
    c = contract()
    paths = {name: tmp_path / name for name in [
        "sample", "heavy-artifact", "heavy-receipt", "rng", "plan",
        "estimator", "manifest", "registry"
    ]}
    for p in paths.values():
        p.write_text("placeholder")

    rng = rng_authority()
    paths["rng"].write_text(json.dumps({
        "schema": c.rng_authority_schema_id,
        **rng.__dict__,
        "global_seed": rng.global_seed,
        "authority_sha256": rng.canonical_digest(),
        "target_panel_dependency": c.rng_target_panel_dependency_id,
        "terminal_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    }))
    paths["heavy-receipt"].write_text(json.dumps({
        "schema": c.heavy_qualification_schema_id,
        "verdict": c.heavy_qualification_verdict_id,
        "block_manifest_sha256": c.full104_manifest_sha256,
        "artifact_sha256": c.heavy_artifact_sha256,
        "rows_traversed": 4_553_407,
        "donors": 104,
        "core_addresses": 17_186,
        "three_route_total_agreement": True,
        "all_104_donor_library_totals_agree": True,
        "per_cell_source_vector_agrees": True,
    }))

    expected_by_name = {
        "sample": c.phase_iv_sample_artifact_sha256,
        "heavy-artifact": c.heavy_artifact_sha256,
        "heavy-receipt": c.heavy_qualification_receipt_sha256,
        # Deliberately different from semantic authority digest: proves the
        # preflight does not confuse JSON file bytes with authority identity.
        "rng": h("rng-json-file-bytes"),
        "plan": c.mask_plan_generator_sha256,
        "estimator": c.burden_estimator_source_sha256,
        "manifest": c.full104_manifest_sha256,
        "registry": c.canonical_registry_sha256,
    }
    monkeypatch.setattr(
        P,
        "sha256_file",
        lambda path: expected_by_name[Path(path).name],
    )

    observed = P.verify_runtime_bindings(
        c,
        sample_freeze=paths["sample"],
        heavy_artifact=paths["heavy-artifact"],
        heavy_qualification_receipt=paths["heavy-receipt"],
        rng_authority=paths["rng"],
        mask_plan_generator=paths["plan"],
        burden_estimator_source=paths["estimator"],
        full104_manifest=paths["manifest"],
        canonical_registry=paths["registry"],
    )
    assert observed["rng_authority_file_sha256"] == h("rng-json-file-bytes")
    assert c.rng_authority_sha256 != observed["rng_authority_file_sha256"]


def test_runtime_binding_mismatch_fails_closed(tmp_path: Path, monkeypatch) -> None:
    c = contract()
    dummy = tmp_path / "x"
    dummy.write_text("{}")
    monkeypatch.setattr(P, "sha256_file", lambda path: h("wrong"))
    with pytest.raises(ValueError, match="runtime binding mismatch"):
        P.verify_runtime_bindings(
            c,
            sample_freeze=dummy,
            heavy_artifact=dummy,
            heavy_qualification_receipt=dummy,
            rng_authority=dummy,
            mask_plan_generator=dummy,
            burden_estimator_source=dummy,
            full104_manifest=dummy,
            canonical_registry=dummy,
        )
