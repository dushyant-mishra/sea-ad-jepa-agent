import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_REPRESENTATION_FAMILY_QUALIFICATION_20261005.json"
EXPECTED = [
    "GLOBAL_CELL_STATE",
    "QUERY_LOCAL_STATE",
    "PROGRAM_STATE",
    "STRUCTURED_COMBINED_STATE",
]


def _state() -> dict:
    assert STATE.exists(), "representation family qualification state must be published"
    return json.loads(STATE.read_text(encoding="utf-8"))


def test_exactly_four_required_representation_families_are_neutral() -> None:
    state = _state()
    assert list(state["families"]) == EXPECTED
    assert state["selected_family"] == "UNSET_REQUIRES_APPROVAL"
    assert state["default_family"] == "NONE"
    assert state["cell_state_is_qualified_default"] is False
    assert state["structured_combined_is_qualified_default"] is False
    assert state["dimensionality"] == "UNSET_EVIDENCE_DERIVED"


def test_each_family_declares_scope_losses_controls_transport_and_claim_limit() -> None:
    state = _state()
    required = {
        "extraction_object",
        "intended_scope",
        "legitimate_losses",
        "mandatory_shortcut_controls",
        "transport_axes",
        "rare_novel_rna_behavior",
        "maximum_claim_before_external_evidence",
    }
    for name in EXPECTED:
        family = state["families"][name]
        assert required <= set(family)
        assert family["maximum_claim_before_external_evidence"] == "RNA_REPRESENTATION"
        assert family["transport_axes"] == [
            "DONOR_TRANSFER",
            "OPERATOR_TRANSFER",
            "STUDY_TRANSFER",
            "TECHNOLOGY_TRANSFER",
        ]
        assert "ADDRESS_IDENTITY" in family["mandatory_shortcut_controls"]
        assert "TECHNICAL_ONLY" in family["mandatory_shortcut_controls"]


def test_global_family_may_legitimately_lose_local_or_novel_information() -> None:
    state = _state()
    losses = state["families"]["GLOBAL_CELL_STATE"]["legitimate_losses"]
    assert "GENUINELY_QUERY_LOCAL_INFORMATION" in losses
    assert "RARE_NOVEL_INFORMATION_NOT_SHARED_GLOBALLY" in losses


def test_query_local_and_program_families_are_not_required_to_be_complete_cell_states() -> None:
    state = _state()
    assert state["families"]["QUERY_LOCAL_STATE"]["is_complete_cell_state_claim"] is False
    assert state["families"]["PROGRAM_STATE"]["is_complete_cell_state_claim"] is False


def test_structured_combined_family_must_earn_incremental_value() -> None:
    state = _state()
    combined = state["families"]["STRUCTURED_COMBINED_STATE"]
    assert combined["must_show_incremental_value_over_components"] is True
    assert combined["more_components_is_not_automatic_advantage"] is True
