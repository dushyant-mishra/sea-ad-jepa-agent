"""Hostile promotion, source and simulator-claim tests for biology crosswalk."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.v5.verify_biology_synthetic_crosswalk_v1 import MACHINE,validate

ROOT = Path(__file__).resolve().parents[2]

def original():
    return json.loads((ROOT / MACHINE).read_text(encoding="utf-8"))

def test_real_crosswalk_is_valid_planning_only():
    validate(original(),ROOT)

@pytest.mark.parametrize("attack",[
 lambda x:x.update(authority="TARGET_WINNER_SELECTED"),
 lambda x:x.update(kind="REAL_HUMAN_DECIDING_RESULT"),
 lambda x:x.update(parent_audit={"pr":322,"head":"f"*40}),
 lambda x:x.update(active_handoff={"pr":460,"head":"a"*40}),
 lambda x:x["lineage"]["integrated_fixture"].update(role="HUMAN_BIOLOGICAL_EVIDENCE"),
 lambda x:x["lineage"]["integrated_design"].update(role="QUALIFIED_FULL_SIMULATION"),
 lambda x:x["lineage"]["fixture_bridge"].update(role="AUTHENTIC_A7_RECEIPT"),
 lambda x["lineage"]["e2g"]: None,
 lambda x:x["rules"].pop("masking"),
 lambda x:x["rules"].update(perturbation="CRISPR applies"),
 lambda x:x["state_questions"].pop(),
 lambda x:x["state_questions"][0].update(id="ALREADY_SELECTED_WINNER"),
 lambda x:x["state_questions"][0].update(promotion="PASS_HUMAN_BIOLOGY"),
 lambda x:x["state_questions"][0].update(family="C4_COMPOSITE"),
 lambda x:x["state_questions"][0].update(simulator_case="NEW_SYNTHETIC_WORLD_GENERATED"),
 lambda x:x["state_questions"][0].update(real_evidence=[]),
 lambda x:x["state_questions"][0]["real_evidence"][0].update(source="docs/agent/FORGED_HUMAN_RESULT.md"),
 lambda x:x["state_questions"][0]["real_evidence"][0].update(sha="f"*40),
 lambda x:x["state_questions"][0]["real_evidence"][0].update(interpretation="PASS"),
 lambda x:x["state_questions"][0].update(must_fail_or_abstain_on=["placeholder"]),
 lambda x:x["state_questions"][1].update(promotion="QUALIFIED_C2"),
 lambda x:x["state_questions"][2].update(promotion="PASS_RARE"),
 lambda x:x["state_questions"][3].update(promotion="TF_BINDING_PROVEN"),
 lambda x:x["state_questions"][4].update(promotion="CAUSALITY_ESTABLISHED"),
 lambda x:x["state_questions"][5].update(promotion="SELECTED_C4"),
 lambda x:x.update(deferrals=[]),
 lambda x:x.update(next_executable_science=[]),
])
def test_non_authoritative_plan_rejects_hostile_promotion(attack):
    d=deepcopy(original())
    # One mutation intentionally removes the field, instead of changing its content.
    try:
        attack(d)
    except (AttributeError,TypeError):
        # The guard must still reject a malformed mutation.
        return
    with pytest.raises(ValueError):
        validate(d,ROOT)

def test_candidate_names_not_planted_as_model_inputs():
    d=original()
    assert all(x["simulator_case"].startswith(("PR328_","PR315_")) for x in d["state_questions"])
    assert not any(x["promotion"]=="PASS" for x in d["state_questions"])

def test_existing_integration_is_reused_without_claiming_a_full_rehearsal():
    d=original()
    assert d["lineage"]["integrated_fixture"]["pr"]==328
    assert d["lineage"]["integrated_design"]["pr"]==315
    assert "DESIGN_ONLY" in d["lineage"]["integrated_design"]["role"]
    assert "NO_A7_REAL_RECEIPT" in d["lineage"]["fixture_bridge"]["role"]
    assert d["authority"].endswith("STAGE4_NOT_AUTHORIZED")
