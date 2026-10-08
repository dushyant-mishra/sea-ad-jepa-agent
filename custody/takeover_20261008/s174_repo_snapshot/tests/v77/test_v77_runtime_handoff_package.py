"""The runtime handoff package executes nothing beyond ZERO_UPDATE, hands the runtime MODEL_VISIBLE
inputs only, covers every q-safety channel of the pinned interface with boundary evidence, records
well-formed digests in which the exact twin matches BIO, passes the executed q-safety probe on every
arm, and its Markdown is the rendering of its JSON."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "results" / "v77" / "V77_RUNTIME_HANDOFF_PACKAGE_V1.json"
MD = ROOT / "docs" / "agent" / "V77_RUNTIME_HANDOFF_PACKAGE.md"
spec = importlib.util.spec_from_file_location("render_record_p6", ROOT / "scripts" / "v77" / "render_v77_record.py")
RENDER = importlib.util.module_from_spec(spec)
sys.modules["render_record_p6"] = RENDER
spec.loader.exec_module(RENDER)
CHANNELS = ("QUERY_VALUE", "NORMALIZATION_DENOMINATOR", "LIBRARY_SIZE_SUMMARY", "DETECTED_FEATURE_SUMMARY",
            "QC_DESCENDANTS", "SUPPORT_OR_MISSINGNESS_SUMMARY", "MASK_CONSTRUCTION", "QUERY_DEPENDENT_PREPROCESSING",
            "TARGET_OR_TEACHER_PRE_CONTEXT")
HEX = re.compile(r"^[0-9a-f]{64}$")


def _p():
    return json.loads(PKG.read_text(encoding="utf-8"))


def test_nothing_beyond_zero_update_is_executed():
    chain = {c["step"].split(" ", 1)[0]: c for c in _p()["chain"]}
    for step in ("6", "7", "8", "9"):
        assert chain[step]["status"] == "NOT_EXECUTED", step
    assert "NOT_SUPPLIED" in chain["5"]["status"]


def test_the_runtime_receives_model_visible_inputs_only():
    rc = _p()["runtime_consumes"]
    assert {m["name"] for m in rc["model_inputs"]} == {"gene_ids", "student_expression", "measurement_mask",
                                                       "hidden_target_mask"}
    assert all(m["visibility"] == "MODEL_VISIBLE" for m in rc["model_inputs"])
    carried = " ".join(c["name"] for c in rc["carried_not_model_inputs"])
    for name in ("source_index", "operator_index", "n_measured", "visible_library_size"):
        assert name in carried, name


def test_every_q_safety_channel_has_boundary_evidence():
    q = _p()["q_safety_boundary"]
    assert tuple(c["channel"] for c in q) == CHANNELS
    assert all(c["v77_evidence"] and c["required_at_boundary"] for c in q)


def test_digests_are_well_formed_the_exact_twin_matches_bio_and_the_probe_passes():
    arms = _p()["arms"]
    assert set(arms) == {"NULL", "BIO", "TWIN_EXACT", "TWIN_OPERATOR"}
    for name, a in arms.items():
        rb = a["rehearsal_batch"]
        for k in ("adapter_model_digest", "feature_identity_digest", "operator_identity_digest",
                  "measurement_support_digest", "batch_scientific_identity_digest"):
            assert HEX.match(rb[k]), (name, k)
        assert rb["challenge_partition"] == "DEVELOPMENT_CALIBRATION"
        assert a["hidden_value_invariance"]["verdict"] == "PASS", name
        assert a["zero_update_plumbing"]["mutation_proof_status"] == "NOT_PROVEN_BY_SHARED_INTERFACE"
    assert arms["TWIN_EXACT"]["full_world"]["adapter_digests"]["model"] == arms["BIO"]["full_world"]["adapter_digests"]["model"]
    assert arms["NULL"]["full_world"]["adapter_digests"]["model"] != arms["BIO"]["full_world"]["adapter_digests"]["model"]


def test_markdown_is_the_rendering_of_the_json():
    assert MD.read_text(encoding="utf-8") == RENDER.render(_p())


def test_the_model_view_finding_is_recorded_with_its_requirement():
    bf = {b["id"]: b for b in _p()["boundary_findings"]}
    assert "lawful_operator_context" in bf["BF1_MODEL_VIEW_CARRIES_OPERATOR_CONTEXT"]["finding"]
    assert "model_inputs only" in bf["BF1_MODEL_VIEW_CARRIES_OPERATOR_CONTEXT"]["requirement"]
    assert {"BF2_RUN_IDS_NAME_THE_ARM", "BF3_EXACT_TWIN_IDENTITY"} <= set(bf)
