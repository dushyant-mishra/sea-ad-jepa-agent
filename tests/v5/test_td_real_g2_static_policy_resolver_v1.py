from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import scripts.v5.td_real_tournament_contract_v1 as T


def _resolver():
    import importlib.util
    name = "scripts.v5.td_real_g2_static_policy_resolver_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required G2 static policy resolver missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _coverage():
    root = Path(os.environ["TD_G2_SUPPORT_ROOT"])
    return json.loads((root / "results/target_discovery/real_tournament/TD_REAL_TRANSFER_COVERAGE_STATIC_CONTRACT_V2.json").read_text())


def _registry():
    return T.load_real_tournament_contract()


def test_current_support_registry_blocks_static_policy_for_every_candidate_without_inventing_strata():
    R = _resolver()
    registry = T.validate_candidate_registry(_registry())
    coverage = _coverage()
    for candidate_id, record in registry.items():
        out = R.resolve_current_g2_static_policy(
            candidate_id=candidate_id,
            tournament_contract=_registry(),
            transfer_coverage_contract=coverage,
            tournament_registry_source_commit=R.TOURNAMENT_REGISTRY_SOURCE_COMMIT,
            support_registry_source_commit=R.SUPPORT_REGISTRY_SOURCE_COMMIT,
        )
        assert out["status"] == "BLOCKED_DEPENDENCY"
        assert out["baseline_catalog"] == record["mandatory_falsifiers"]
        assert out["applicable_baselines"] == []
        assert out["required_strata"] == []
        assert out["human_g2_policy_authorized"] is False
        assert all(v is False for v in out["authority"].values())


def test_foundation_candidates_report_evidence_contract_block_not_fake_no_support():
    R = _resolver(); coverage = _coverage(); contract = _registry()
    for candidate_id in ("C1_SHARED_EMERGENT", "C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED", "C6_SHARED_QUERY_COMPOSITE", "C4_STRUCTURED_COMPOSITE"):
        out = R.resolve_current_g2_static_policy(
            candidate_id=candidate_id, tournament_contract=contract, transfer_coverage_contract=coverage,
            tournament_registry_source_commit=R.TOURNAMENT_REGISTRY_SOURCE_COMMIT,
            support_registry_source_commit=R.SUPPORT_REGISTRY_SOURCE_COMMIT,
        )
        assert out["reason"] == "CANDIDATE_SPECIFIC_EVIDENCE_SUPPORT_CONTRACT_NOT_FROZEN"


def test_specialist_reports_structural_foundation_absence_not_evidence_contract_block():
    R = _resolver()
    out = R.resolve_current_g2_static_policy(
        candidate_id="C5_REGULATORY_SPECIALIST", tournament_contract=_registry(), transfer_coverage_contract=_coverage(),
        tournament_registry_source_commit=R.TOURNAMENT_REGISTRY_SOURCE_COMMIT,
        support_registry_source_commit=R.SUPPORT_REGISTRY_SOURCE_COMMIT,
    )
    assert out["reason"] == "NO_FOUNDATION_SUPPORTED_STRATA__SEPARATE_REGULATORY_CHROMATIN_REGISTRY_REQUIRED"


def test_policy_cannot_accept_caller_baseline_or_stratum_overrides():
    R = _resolver()
    with pytest.raises(TypeError):
        R.resolve_current_g2_static_policy(
            candidate_id="C1_SHARED_EMERGENT", tournament_contract=_registry(), transfer_coverage_contract=_coverage(),
            tournament_registry_source_commit=R.TOURNAMENT_REGISTRY_SOURCE_COMMIT,
            support_registry_source_commit=R.SUPPORT_REGISTRY_SOURCE_COMMIT,
            applicable_baselines=["constant_train_mean"], required_strata=[["SEA_AD", "PRIMARY"]],
        )


def test_registry_source_commit_identity_is_exact_not_branch_tip_or_caller_claim():
    R = _resolver()
    with pytest.raises(R.G2StaticPolicyError, match="tournament registry source"):
        R.resolve_current_g2_static_policy(
            candidate_id="C1_SHARED_EMERGENT", tournament_contract=_registry(), transfer_coverage_contract=_coverage(),
            tournament_registry_source_commit="0" * 40,
            support_registry_source_commit=R.SUPPORT_REGISTRY_SOURCE_COMMIT,
        )
    with pytest.raises(R.G2StaticPolicyError, match="support registry source"):
        R.resolve_current_g2_static_policy(
            candidate_id="C1_SHARED_EMERGENT", tournament_contract=_registry(), transfer_coverage_contract=_coverage(),
            tournament_registry_source_commit=R.TOURNAMENT_REGISTRY_SOURCE_COMMIT,
            support_registry_source_commit="0" * 40,
        )


def test_coverage_contract_cannot_be_mutated_to_manufacture_supported_policy():
    R = _resolver(); coverage = _coverage()
    coverage["claim_envelope_status"]["C1_SHARED_EMERGENT"] = "SUPPORTED"
    coverage["mandatory_claim_envelopes"]["C1_SHARED_EMERGENT"] = ["SEA_AD::PRIMARY"]
    with pytest.raises(R.G2StaticPolicyError, match="coverage contract drift"):
        R.resolve_current_g2_static_policy(
            candidate_id="C1_SHARED_EMERGENT", tournament_contract=_registry(), transfer_coverage_contract=coverage,
            tournament_registry_source_commit=R.TOURNAMENT_REGISTRY_SOURCE_COMMIT,
            support_registry_source_commit=R.SUPPORT_REGISTRY_SOURCE_COMMIT,
        )


def test_unknown_candidate_is_rejected_before_policy_derivation():
    R = _resolver()
    with pytest.raises(R.G2StaticPolicyError, match="candidate"):
        R.resolve_current_g2_static_policy(
            candidate_id="C99", tournament_contract=_registry(), transfer_coverage_contract=_coverage(),
            tournament_registry_source_commit=R.TOURNAMENT_REGISTRY_SOURCE_COMMIT,
            support_registry_source_commit=R.SUPPORT_REGISTRY_SOURCE_COMMIT,
        )
