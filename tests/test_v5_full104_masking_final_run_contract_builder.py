from pathlib import Path

def test_final_freeze_builder_requires_outputs_outside_worktree_and_valid_checkpoint():
    source=Path("scripts/agent/build_full104_masking_final_run_contract_20260918.py").read_text(encoding="utf-8")
    assert "_outside(args.out_source_manifest,args.worktree)" in source
    assert "validate_checkpoint(" in source
    assert "checkpoint_semantic_sha256" in source


def test_source_closure_includes_transitive_precision_and_decision_dependencies():
    source=Path("scripts/agent/build_full104_masking_final_run_contract_20260918.py").read_text(encoding="utf-8")
    required=(
        "precision_authority_v2.py",
        "precision_authority_v4.py",
        "masking_qualification_decision_v1.py",
        "masking_qualification_decision_v2.py",
        "masking_qualification_decision_v3.py",
        "masking_evidence_assembler_v1.py",
        "masking_nonlinear_orchestrator_v1.py",
        "masking_qualification_execution_authority_v5.py",
    )
    assert [x for x in required if x not in source] == []


def test_final_freeze_builder_never_opens_outcomes_or_training():
    source=Path("scripts/agent/build_full104_masking_final_run_contract_20260918.py").read_text(encoding="utf-8")
    forbidden=("training_authorized=True","terminal_masking_outcomes_inspected=True","selected_policy_id")
    assert [x for x in forbidden if x in source] == []
