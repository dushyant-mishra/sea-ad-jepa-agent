"""The multimodal semantic-twin design is prospective: every arm carries a designed expectation,
oracle fields never reach permitted inputs, object-specific parameters stay UNSET (choosing them
is choosing an object), nothing is executed, no threshold is inherited from S149 or S159, and the
Markdown is the rendering of the JSON."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / "results" / "v77" / "V77_MULTIMODAL_TWIN_PREREGISTRATION_V1.json"
MD = ROOT / "docs" / "agent" / "V77_MULTIMODAL_TWIN_PREREGISTRATION.md"
spec = importlib.util.spec_from_file_location("render_record", ROOT / "scripts" / "v77" / "render_v77_record.py")
RENDER = importlib.util.module_from_spec(spec)
sys.modules["render_record"] = RENDER
spec.loader.exec_module(RENDER)
ARMS = {"BIO", "RNA_TWIN", "MULTIMODAL_TWIN", "MULTIMODAL_TWIN_GLOBAL", "CLEAN", "QUERY_LEAK", "STATIC_OBJECT",
        "OBJECT_NUISANCE_ONLY"}
DESIGN = {"IDENTIFIABLE_BY_DESIGN", "NON_IDENTIFIABLE_BY_DESIGN", "CIRCULAR_BY_CONSTRUCTION", "NO_PROGRAM",
          "REFERENCE"}


def _r():
    return json.loads(REC.read_text(encoding="utf-8"))


def test_every_arm_is_defined_with_a_designed_expectation():
    arms = {a["arm"]: a for a in _r()["arms"]}
    assert set(arms) == ARMS
    for a in arms.values():
        assert a["designed_identifiability_against_BIO"] in DESIGN and a["expected_outcome"], a["arm"]
    assert arms["MULTIMODAL_TWIN"]["designed_identifiability_against_BIO"] == "NON_IDENTIFIABLE_BY_DESIGN"
    assert arms["RNA_TWIN"]["designed_identifiability_against_BIO"] == "IDENTIFIABLE_BY_DESIGN"
    assert arms["QUERY_LEAK"]["designed_identifiability_against_BIO"] == "CIRCULAR_BY_CONSTRUCTION"


def test_oracle_fields_never_reach_permitted_inputs():
    r = _r()
    permitted = set(r["permitted_model_inputs"]["fields"])
    assert not permitted & set(r["oracle_only_fields"])
    assert not permitted & {"source_index", "operator_index", "donor_index", "global_cell_index"}


def test_object_choice_stays_unset_and_nothing_is_executed():
    r = _r()
    assert r["execution_status"] == "NOT_EXECUTED__REQUIRES_EVIDENCE_OBJECT_CHOICE"
    assert r["object_choice_slots"] and all(s["value"] == "UNSET" for s in r["object_choice_slots"])
    assert r["acceptance_thresholds"] == []


def test_no_threshold_is_inherited_from_s149_or_s159():
    text = json.dumps({k: v for k, v in _r().items() if k != "threshold_policy"})
    assert "S149" not in text and "S159" not in text


def test_falsification_rules_name_defined_arms_only():
    r = _r()
    for rule in r["falsification_logic"]:
        assert set(rule["arms"]) <= ARMS and rule["consequence"], rule["id"]


def test_markdown_is_the_rendering_of_the_json():
    assert MD.read_text(encoding="utf-8") == RENDER.render(_r())
