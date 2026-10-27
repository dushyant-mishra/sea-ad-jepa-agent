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
 lambda x:x["lineage"].pop("e2g"),
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
    attack(d)
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

@pytest.mark.parametrize("attack",[
 lambda d:d.pop("completed_real_evidence"),
 lambda d:d["completed_real_evidence"].pop(),
 lambda d:d["completed_real_evidence"][0].update(classification="BIOLOGICAL_TARGET_QUALIFIED"),
 lambda d:d["completed_real_evidence"][1].update(classification="TD57B_24_OF_24_CURRENT_TARGET_PASS"),
 lambda d:d["completed_real_evidence"][1].update(classification="CORRECTED_REPLAY_REQUIRED_NOT_EXECUTED"),
 lambda d:d["completed_real_evidence"][1].update(source_ref="audit/target-discovery-takeover-20261011"),
 lambda d:d["completed_real_evidence"][2].update(classification="V44_REAL_JEPA_CHAMPION"),
 lambda d:d["completed_real_evidence"][3].update(classification="RARE_BENCHMARK_LOCKED"),
 lambda d:d["completed_real_evidence"][5].update(classification="SCENIC_PROVEN_CAUSAL_TF"),
 lambda d:d["completed_real_evidence"][6].update(classification="MICROGLIA_EXPERIMENTAL_CAUSAL_STATE"),
 lambda d:d["completed_real_evidence"][0].update(source_ref="invented/unreviewed-branch"),
 lambda d:d["completed_real_evidence"][1].update(source="new_unqualified_24_of_24_data.md"),
 lambda d:d["state_questions"][2].update(family="C3_QUERY_MEASURED"),
 lambda d:d["state_questions"][6].update(family="RARE_SPECIALIST_NOT_C3"),
])
def test_completed_science_and_c3_taxonomy_cannot_be_rewritten(attack):
    d=deepcopy(original())
    attack(d)
    with pytest.raises(ValueError):
        validate(d,ROOT)


def test_historical_partial_rna_and_source_mapping_limits_kept_together():
    d=original()
    by_id={r["key"]:r for r in d["completed_real_evidence"]}
    assert "0.4300" in by_id["TD_R5_QUERY_DEVELOPMENT"]["result"]
    assert "0.407823" in by_id["V44_RNA_TEACHER_PROXIES"]["result"]
    assert "CORRECTED_REPLAY_PR314_COMPLETED" in by_id["TD56_59_RELATIONAL"]["classification"]
    assert "TD59 PASS" in by_id["TD56_59_RELATIONAL"]["result"]
    assert "TD57C nearest-third HVS P0 FAIL" in by_id["TD56_59_RELATIONAL"]["result"]
    assert "0 reader-validation donors" in by_id["M_STRICT_REAL_COUNTS"]["result"]
    families={r["id"]:r["family"] for r in d["state_questions"]}
    assert families["QUERY_MEASURED_RNA_STATE"]=="C3_QUERY_MEASURED"
    assert families["RARE_MICROGLIAL_PROGRAM"]=="RARE_SPECIALIST_NOT_C3"
