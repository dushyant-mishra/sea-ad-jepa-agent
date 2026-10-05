import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_STATE_20261005.json"
CONTRACT = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_CONTRACT_20261005.md"

EXPECTED_GATES = ["P1", "P2", "P3", "P4", "P5", "P6"]
EXPECTED_VERDICTS = {
    "QUALIFIED_FOR_RNA_REPRESENTATION",
    "INFORMATIVE_BUT_NOT_QUALIFIED",
    "FAIL_LEAKAGE",
    "FAIL_SHORTCUT",
    "FAIL_TRANSPORT",
    "NONRECOVERABLE_FROM_VIEW",
    "INDETERMINATE",
}


def load_state():
    assert STATE.exists(), f"missing premise state: {STATE}"
    return json.loads(STATE.read_text())


def test_premise_contract_files_exist():
    assert CONTRACT.exists(), f"missing premise contract: {CONTRACT}"
    assert STATE.exists(), f"missing premise state: {STATE}"


def test_premise_state_has_all_six_gates_and_frozen_boundaries():
    state = load_state()
    assert list(state["premise_gates"].keys()) == EXPECTED_GATES
    assert state["training_authorized"] is False
    assert state["test_open"] is False
    assert state["morabito_open"] is False
    assert state["selected_target"] == "UNSET_REQUIRES_APPROVAL"
    assert state["selected_representation"] == "UNSET_REQUIRES_APPROVAL"
    assert state["numeric_margin_authority"] == "UNSET_REQUIRES_APPROVAL"


def test_premise_state_verdict_enum_is_exact_and_non_promoting():
    state = load_state()
    assert set(state["stage_a_allowed_verdicts"]) == EXPECTED_VERDICTS
    assert state["rna_representation_authorizes_training"] is False
    assert state["rna_representation_auto_promotes_to_biology"] is False
    assert state["stronger_claims_require_separate_qualification"] is True
