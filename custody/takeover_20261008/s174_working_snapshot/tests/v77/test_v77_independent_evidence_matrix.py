"""The independent-evidence matrix covers every Phase 5 candidate, obeys the classification rule it
declares, selects nothing, quotes the older statements it narrows exactly, and its Markdown is the
rendering of its JSON."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "results" / "v77" / "V77_INDEPENDENT_EVIDENCE_MATRIX_V1.json"
MD = ROOT / "docs" / "agent" / "V77_INDEPENDENT_EVIDENCE_MATRIX.md"
spec = importlib.util.spec_from_file_location("render_matrix", ROOT / "scripts" / "v77" / "render_v77_evidence_matrix.py")
RENDER = importlib.util.module_from_spec(spec)
sys.modules["render_matrix"] = RENDER
spec.loader.exec_module(RENDER)

CLASSES = {"CAN_BREAK_A_SPECIFIC_TWIN", "SUPPORTIVE_BUT_NOT_IDENTIFYING", "CIRCULAR_WITH_CURRENT_RNA",
           "PROTECTED_OR_NOT_AVAILABLE", "UNQUALIFIED"}
CAPABILITY = {"CAN_BREAK_A_SPECIFIC_TWIN", "SUPPORTIVE_BUT_NOT_IDENTIFYING", "CIRCULAR_WITH_CURRENT_RNA"}
LINEAGE = {"TW_EXACT", "TW_OPERATOR", "TW_TARGET_CAPTURE", "TW_ANCHOR"}
QUERY_MATCHED = {"SAME_NUCLEUS", "SAME_CELL", "SAME_LIBRARY", "SAME_DONOR"}


def _m():
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def test_every_phase5_candidate_is_covered_with_all_ten_columns():
    m = _m()
    assert {r["candidate"] for r in m["rows"]} == set(range(1, 11))
    assert len(m["columns"]) == 10
    for r in m["rows"]:
        for c in m["columns"]:
            assert r.get(c) not in (None, "", [], {}), (r["id"], c)


def test_classes_follow_the_declared_rule():
    for r in _m()["rows"]:
        now, cap = r["c10_classification"], r["class_if_qualified"]
        breaks = set(r["c6_twins_it_can_falsify"]["twins"]) & LINEAGE
        assert now in CLASSES and cap in CAPABILITY, r["id"]
        if r["c3_construction_independence"]["verdict"] == "CIRCULAR":
            assert now == cap == "CIRCULAR_WITH_CURRENT_RNA", r["id"]
        if r["query_matching"] in ("EXTERNAL_STATIC", "QUERY_RNA"):
            assert not breaks, f"{r['id']}: a static or query-derived object cannot break a lineage twin (P1)"
        assert (cap == "CAN_BREAK_A_SPECIFIC_TWIN") == bool(breaks), r["id"]
        if cap == "CAN_BREAK_A_SPECIFIC_TWIN":
            assert r["query_matching"] in QUERY_MATCHED, r["id"]
        if now == "UNQUALIFIED":
            assert cap == "CAN_BREAK_A_SPECIFIC_TWIN" and r["c9_missing_controls_blocking_use"], r["id"]
        if now == "SUPPORTIVE_BUT_NOT_IDENTIFYING":
            assert cap == "SUPPORTIVE_BUT_NOT_IDENTIFYING", r["id"]
        if now == "CAN_BREAK_A_SPECIFIC_TWIN":
            assert not r["c9_missing_controls_blocking_use"], f"{r['id']}: blocking controls are still missing"


def test_morabito_is_never_usable_here():
    for r in _m()["rows"]:
        if "Morabito" in r["name"] or "GSE174367" in r["name"]:
            assert r["c10_classification"] in ("PROTECTED_OR_NOT_AVAILABLE", "CIRCULAR_WITH_CURRENT_RNA"), r["id"]


def test_nothing_is_selected():
    m = _m()
    assert m["selection"] == "NONE"
    text = json.dumps(m["rows"]).lower()
    for word in ("winner", "recommended", "selected object", "ranked first"):
        assert word not in text, word


def test_narrowed_statements_are_quoted_exactly_from_their_source():
    for s in _m()["supersedes"]:
        src = (ROOT / s["where"].split(" (")[0]).read_text(encoding="utf-8")
        assert s["statement"] in src, s["statement"]


def test_markdown_is_the_rendering_of_the_json():
    assert MD.read_text(encoding="utf-8") == RENDER.render(_m())
