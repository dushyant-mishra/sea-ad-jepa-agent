"""The first bounded-mutation experiment is pre-registered, not run: its arms cover the shared
interface's control roster and the S157 twins, its primary question and reading rules are fixed,
every runtime slot stays UNSET until the runtime lane supplies a bound SHA and rehearsal contract,
the model sees MODEL_VISIBLE inputs only, and the Markdown is the rendering of the JSON."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / "results" / "v77" / "V77_S157_BOUNDED_MUTATION_PREREGISTRATION_V1.json"
MD = ROOT / "docs" / "agent" / "V77_S157_BOUNDED_MUTATION_PREREGISTRATION.md"
spec = importlib.util.spec_from_file_location("render_record_p7", ROOT / "scripts" / "v77" / "render_v77_record.py")
RENDER = importlib.util.module_from_spec(spec)
sys.modules["render_record_p7"] = RENDER
spec.loader.exec_module(RENDER)
ROSTER = {"CLEAN_NEGATIVE", "TECHNICAL_OPERATOR_SHORTCUT", "PLANTED_RECOVERABLE_BIOLOGICAL",
          "PLANTED_INACCESSIBLE_PRIVATE_STATE", "QUERY_LEAK"}
QUESTION = ("Does learned representation behaviour distinguish biology from nuisance beyond what is possible from "
            "the admitted observations?")


def _r():
    return json.loads(REC.read_text(encoding="utf-8"))


def test_arms_cover_the_interface_roster_and_the_s157_twins():
    arms = {a["arm"]: a for a in _r()["arms"]}
    assert set(arms) == {"BIO", "BIO_REPEAT", "TWIN_EXACT", "TWIN_OPERATOR", "NULL", "QUERY_LEAK"}
    assert {a["roster_arm"] for a in arms.values()} >= ROSTER


def test_primary_question_and_reading_rules_are_fixed():
    r = _r()
    assert r["primary_question"] == QUESTION
    rules = " ".join(r["reading_rules"]).lower()
    assert "exact twins remaining identical is a valid result" in rules
    assert "loss reduction is not a success criterion" in rules


def test_nothing_runs_until_the_runtime_lane_supplies_its_contract():
    r = _r()
    assert r["execution_status"] == "NOT_EXECUTED__AWAITS_BOUND_RUNTIME_SHA_AND_REHEARSAL_CONTRACT"
    assert r["unset_slots"] and all(s["value"] == "UNSET" for s in r["unset_slots"])
    assert "bound_runtime_sha" in {s["slot"] for s in r["unset_slots"]}


def test_the_model_sees_model_visible_inputs_only():
    p = _r()["permitted_inputs"]
    assert set(p["model"]) == {"gene_ids", "student_expression", "measurement_mask", "hidden_target_mask"}
    assert {"source_index", "operator_index", "n_measured", "visible_library_size"} <= set(p["excluded"])


def test_stop_rules_and_comparisons_name_defined_arms():
    r = _r()
    arms = {a["arm"] for a in r["arms"]}
    for x in r["stop_rules"] + r["comparisons"]:
        assert set(x["arms"]) <= arms, x["id"]
    assert any(s["id"] == "STOP_1" and set(s["arms"]) == {"BIO", "TWIN_EXACT"} for s in r["stop_rules"])


def test_markdown_is_the_rendering_of_the_json():
    assert MD.read_text(encoding="utf-8") == RENDER.render(_r())
