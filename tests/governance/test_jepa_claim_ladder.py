import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs/agent/JEPA_CLAIM_LADDER_20261005.json"
LEVELS = [
    "RNA_REPRESENTATION",
    "TRANSFERABLE_BIOLOGICAL_STATE",
    "REGULATORY_SUPPORT",
    "CAUSAL_PERTURBATIONAL_PREDICTION",
]


def _state() -> dict:
    assert STATE.exists(), "claim ladder state must be published"
    return json.loads(STATE.read_text(encoding="utf-8"))


def test_claim_levels_are_exact_and_never_auto_promote() -> None:
    state = _state()
    assert state["levels"] == LEVELS
    assert state["automatic_promotion"] is False
    assert state["transitive_auto_promotion"] is False
    assert state["stage_a_maximum_claim"] == "RNA_REPRESENTATION"


def test_rna_to_biology_requires_independent_semantic_and_transport_evidence() -> None:
    edge = _state()["promotions"]["RNA_REPRESENTATION->TRANSFERABLE_BIOLOGICAL_STATE"]
    assert "INDEPENDENT_SEMANTIC_EVIDENCE" in edge["required_evidence"]
    assert "RELEVANT_TRANSFER_AXES" in edge["required_evidence"]
    assert edge["stage_a_alone_sufficient"] is False


def test_biology_to_regulatory_requires_independent_regulatory_evidence() -> None:
    edge = _state()["promotions"]["TRANSFERABLE_BIOLOGICAL_STATE->REGULATORY_SUPPORT"]
    assert "INDEPENDENT_CHROMATIN_OR_REGULATORY_EVIDENCE" in edge["required_evidence"]
    assert edge["rna_derived_edges_alone_sufficient"] is False


def test_regulatory_to_causal_requires_intervention_evidence() -> None:
    edge = _state()["promotions"]["REGULATORY_SUPPORT->CAUSAL_PERTURBATIONAL_PREDICTION"]
    assert "INTERVENTION_OR_PERTURBATION_EVIDENCE" in edge["required_evidence"]
    assert edge["observational_association_sufficient"] is False


def test_forbidden_inferences_are_explicit() -> None:
    forbidden = set(_state()["forbidden_inferences"])
    assert "MASKED_RNA_SUCCESS_IMPLIES_BIOLOGICAL_VALIDITY" in forbidden
    assert "RNA_ATAC_ASSOCIATION_IMPLIES_REGULATORY_QUALIFICATION" in forbidden
    assert "OBSERVATIONAL_PREDICTION_IMPLIES_INTERVENTION_EFFECT" in forbidden
    assert "LARGE_CELL_COUNT_IMPLIES_LARGE_BIOLOGICAL_UNIT_COUNT" in forbidden
    assert "SYNTHETIC_SUCCESS_IMPLIES_REAL_BIOLOGICAL_VALIDATION" in forbidden
