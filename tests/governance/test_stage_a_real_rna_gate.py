import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_20261005.json"


def _state() -> dict:
    assert STATE.exists(), "Stage-A prefreeze state must be published"
    return json.loads(STATE.read_text(encoding="utf-8"))


def test_stage_a_is_prefreeze_not_execution_authority() -> None:
    state = _state()
    assert state["status"] == "PREFREEZE_EXECUTION_CONTRACT__NOT_EXECUTION_AUTHORITY"
    assert state["execution_authorized"] is False
    assert state["encoder_optimizer_updates"] == 0
    assert state["ema_updates"] == 0
    assert state["test_open"] is False
    assert state["morabito_open"] is False
    assert state["external_assets_may_select_target"] is False


def test_leakage_and_shortcut_are_absolute_fail_gates() -> None:
    state = _state()
    assert state["gates"]["LEAKAGE"]["absolute_fail"] is True
    assert state["gates"]["LEAKAGE"]["fail_verdict"] == "FAIL_LEAKAGE"
    assert state["gates"]["SHORTCUT"]["absolute_fail"] is True
    assert state["gates"]["SHORTCUT"]["fail_verdict"] == "FAIL_SHORTCUT"


def test_recoverability_semantics_are_split() -> None:
    state = _state()
    rec = state["recoverability"]
    assert rec["real_rna_quantity"] == "TARGET_OBJECT_RECOVERABILITY"
    assert rec["biological_truth_quantity_requires_independent_truth"] == "BIOLOGICAL_TRUTH_RECOVERABILITY"
    assert rec["target_object_recoverability_is_biological_validation"] is False


def test_transfer_axes_are_separate_and_missing_evidence_is_not_pass() -> None:
    state = _state()
    assert state["transport"]["axes"] == [
        "DONOR_TRANSFER",
        "OPERATOR_TRANSFER",
        "STUDY_TRANSFER",
        "TECHNOLOGY_TRANSFER",
    ]
    assert state["transport"]["allowed_axis_statuses"] == [
        "PASS",
        "FAIL",
        "NOT_TESTED",
        "NOT_IDENTIFIABLE_UNDER_CURRENT_CONFOUNDING",
    ]
    assert state["transport"]["not_tested_is_pass"] is False
    assert state["transport"]["not_identifiable_is_pass"] is False


def test_diagnostic_readout_is_inner_train_and_frozen() -> None:
    readout = _state()["diagnostic_readout"]
    assert readout["fit_partition"] == "INNER_TRAIN_ONLY"
    assert readout["freeze_before"] == "HELD_DONOR_EVALUATION"
    assert readout["fit_on_deciding_units"] is False
    assert readout["may_change_target_definition_after_deciding_outcomes"] is False


def test_thresholds_and_open_choices_remain_fail_closed() -> None:
    state = _state()
    assert state["threshold_policy"]["post_hoc_origin_allowed"] is False
    assert state["threshold_policy"]["unjustified_numeric_margin"] == "UNSET_REQUIRES_APPROVAL"
    assert state["selected_target"] == "UNSET_REQUIRES_APPROVAL"
    assert state["selected_representation"] == "UNSET_REQUIRES_APPROVAL"
    assert state["selected_estimand"] == "UNSET_REQUIRES_APPROVAL"


def test_stage_a_verdicts_and_claim_limit_match_premise_authority() -> None:
    state = _state()
    assert state["allowed_verdicts"] == [
        "QUALIFIED_FOR_RNA_REPRESENTATION",
        "INFORMATIVE_BUT_NOT_QUALIFIED",
        "FAIL_LEAKAGE",
        "FAIL_SHORTCUT",
        "FAIL_TRANSPORT",
        "NONRECOVERABLE_FROM_VIEW",
        "INDETERMINATE",
    ]
    assert state["maximum_claim"] == "RNA_REPRESENTATION"
    assert state["qualification_authorizes_production_training"] is False
