from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.masking_qualification_run_contract_v3 import (
    DECISION_RULE_ID,
    EXECUTION_SOURCE_ROLE_ID,
    FREEZE_POLICY_ID,
    STRICT_SUPPORT_POLICY_ID,
    TERMINAL_UNIVERSE_ID,
    MaskingQualificationRunContractV3,
)


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def contract(**updates):
    fields = [
        "design", "parameters", "manifest", "observation", "support", "census",
        "budget-template", "burden-ladder", "split", "target-panel", "precision",
        "rng", "checkpoint", "reference", "streaming", "precision-source",
        "donor-evidence-source", "decision-source", "spillover-source",
    ]
    roots = {name: h(name) for name in fields}
    values = dict(
        authority_id="TEST",
        qualification_design_authority_sha256=roots["design"],
        qualification_parameters_authority_sha256=roots["parameters"],
        full104_block_manifest_sha256=roots["manifest"],
        observation_state_sha256=roots["observation"],
        support_estimability_authority_sha256=roots["support"],
        census_authority_sha256=roots["census"],
        target_evidence_budget_template_sha256=roots["budget-template"],
        burden_ladder_authority_sha256=roots["burden-ladder"],
        outer_split_authority_sha256=roots["split"],
        target_panel_authority_sha256=roots["target-panel"],
        precision_authority_sha256=roots["precision"],
        rng_replay_authority_sha256=roots["rng"],
        machine_worktree_checkpoint_sha256=roots["checkpoint"],
        canonical_reference_source_sha256=roots["reference"],
        full104_streaming_execution_source_sha256=roots["streaming"],
        precision_evaluator_source_sha256=roots["precision-source"],
        donor_evidence_source_sha256=roots["donor-evidence-source"],
        decision_evaluator_source_sha256=roots["decision-source"],
        anti_spillover_test_source_sha256=roots["spillover-source"],
        execution_source_role_id=EXECUTION_SOURCE_ROLE_ID,
        decision_rule_id=DECISION_RULE_ID,
        freeze_policy_id=FREEZE_POLICY_ID,
        support_state_policy_id=STRICT_SUPPORT_POLICY_ID,
        terminal_universe_id=TERMINAL_UNIVERSE_ID,
    )
    values.update(updates)
    return MaskingQualificationRunContractV3(**values)


def test_v3_contract_is_deterministic_and_training_off():
    c = contract()
    c.validate()
    assert c.canonical_digest() == contract().canonical_digest()


def test_placeholder_or_nonhash_root_fails_closed():
    with pytest.raises(ValueError, match="SHA-256"):
        contract(census_authority_sha256="PLACEHOLDER").validate()


def test_role_splicing_fails_closed():
    same = h("same")
    with pytest.raises(ValueError, match="role-distinct"):
        contract(
            donor_evidence_source_sha256=same,
            decision_evaluator_source_sha256=same,
        ).validate()


def test_terminal_outcome_access_before_freeze_is_rejected():
    with pytest.raises(ValueError, match="before terminal outcomes"):
        contract(terminal_outcomes_inspected_before_freeze=True).validate()


def test_decision_rule_and_strict_support_are_fixed():
    with pytest.raises(ValueError, match="decision_rule_id"):
        contract(decision_rule_id="FREE_TEXT_PASS").validate()
    with pytest.raises(ValueError, match="support_state_policy_id"):
        contract(support_state_policy_id="LOOSE_MEASURED").validate()
