"""The regulatory circularity audit separates Sol's three settings, classifies each explicitly, agrees
with the evidence matrix row by row, does not tunnel onto ATAC, and its Markdown is its rendering."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "results" / "v77" / "V77_REGULATORY_CIRCULARITY_AUDIT_V1.json"
MATRIX = ROOT / "results" / "v77" / "V77_INDEPENDENT_EVIDENCE_MATRIX_V1.json"
MD = ROOT / "docs" / "agent" / "V77_REGULATORY_CIRCULARITY_AUDIT.md"
spec = importlib.util.spec_from_file_location("render_circ", ROOT / "scripts" / "v77" / "render_v77_circularity_audit.py")
RENDER = importlib.util.module_from_spec(spec)
sys.modules["render_circ"] = RENDER
spec.loader.exec_module(RENDER)
LINEAGE = {"TW_EXACT", "TW_OPERATOR", "TW_TARGET_CAPTURE", "TW_ANCHOR"}
QUERY_MATCHED = {"SAME_NUCLEUS", "SAME_CELL", "SAME_LIBRARY", "SAME_DONOR"}


def _a():
    return json.loads(AUDIT.read_text(encoding="utf-8"))


def _rows():
    return {r["id"]: r for r in json.loads(MATRIX.read_text(encoding="utf-8"))["rows"]}


def test_three_settings_are_separated_and_classified():
    s = {x["id"]: x for x in _a()["settings"]}
    assert set(s) == {"A_SAME_RNA", "B_INDEPENDENT_CHROMATIN_PLUS_RNA", "C_PHYSICALLY_INDEPENDENT_LINKS"}
    assert s["A_SAME_RNA"]["circularity_class"] == "C3_QUERY_CIRCULAR"
    assert s["A_SAME_RNA"]["verdict"] == "CIRCULAR_WITH_CURRENT_RNA"
    for k in ("B_INDEPENDENT_CHROMATIN_PLUS_RNA", "C_PHYSICALLY_INDEPENDENT_LINKS"):
        assert s[k]["verdict"] == "SUPPORTIVE_BUT_NOT_IDENTIFYING"
        assert not set(s[k]["twins_broken"]) & LINEAGE, f"{k}: a static object cannot break a lineage twin"


def test_settings_agree_with_the_matrix():
    rows = _rows()
    for s in _a()["settings"]:
        for rid in s["matrix_rows"]:
            assert rows[rid]["class_if_qualified"] == s["verdict"], (s["id"], rid)


def test_not_only_atac_and_classes_match_query_matching():
    a, rows = _a(), _rows()
    assert sum("ATAC" not in e["evidence"] and "accessibility" not in e["evidence"] for e in a["not_only_atac"]) >= 6
    for e in a["not_only_atac"]:
        qm = rows[e["matrix_row"]]["query_matching"]
        if e["circularity_class"] == "C0_QUERY_MATCHED_INDEPENDENT":
            assert qm in QUERY_MATCHED, e["evidence"]
        else:
            assert qm == "EXTERNAL_STATIC", e["evidence"]


def test_every_pipeline_step_states_its_rna_use_and_local_evidence_exists():
    a = _a()
    assert len(a["pipeline"]) >= 9 and all(p["query_rna"] for p in a["pipeline"])
    for e in a["project_evidence"]:
        for path in e.get("local_paths", []):
            assert (ROOT / path).exists(), path


def test_markdown_is_the_rendering_of_the_json():
    assert MD.read_text(encoding="utf-8") == RENDER.render(_a())
