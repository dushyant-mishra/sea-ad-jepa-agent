"""The committed shortcut-audit result was produced by the committed tool with its declared
constants, keeps raw identity as a forbidden control and the RNA reference out of the context
classes, carries its synthetic-only caveat, and still shows what S157 found: the measurable-address
count, the hidden-target count that inherits it, and the support pattern are identity proxies."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "v77" / "V77_CONTEXT_SHORTCUT_AUDIT_V1.json"
TOOL = ROOT / "scripts" / "v77" / "audit_v77_context_shortcuts.py"
spec = importlib.util.spec_from_file_location("shortcut_results", TOOL)
A = importlib.util.module_from_spec(spec)
sys.modules["shortcut_results"] = A
spec.loader.exec_module(A)


def _r():
    return json.loads(RES.read_text(encoding="utf-8"))


def test_result_was_produced_by_the_committed_tool_with_its_declared_constants():
    r = _r()
    assert r["executor"]["scripts/v77/audit_v77_context_shortcuts.py"] == hashlib.sha256(TOOL.read_bytes()).hexdigest()
    d = r["declared"]
    assert (d["knn_k"], d["ridge_rel"], d["n_perm"], d["perm_seed"], d["lift_cutoff"]) == (
        A.KNN_K, A.RIDGE_REL, A.N_PERM, A.PERM_SEED, A.LIFT_CUTOFF)


def test_classes_keep_identity_forbidden_and_the_reference_apart():
    s = _r()["summary"]
    assert s["source_index"]["risk_class"] == s["operator_index"]["risk_class"] == "FORBIDDEN_RAW_IDENTITY_CONTROL"
    assert s["REFERENCE_rna_components"]["risk_class"] == "REFERENCE_NOT_A_CONTEXT_FIELD"
    for name in ("n_measured", "hidden_target_count", "support_pattern"):
        assert s[name]["risk_class"] == "HIGH_IDENTITY_PROXY_RISK", name


def test_every_world_audits_every_field_and_the_caveats_travel_with_the_result():
    r = _r()
    fields = set(r["summary"])
    assert set(r["worlds"]) == {"NULL", "BIO", "TWIN_EXACT", "TWIN_OPERATOR"}
    for w in r["worlds"].values():
        assert set(w["results"]) == fields
    assert any("synthetic observer only" in c for c in r["caveats"])
    for entry in r["summary"].values():
        assert all(v["raw_identity_ceiling"] > 0 for v in entry["identity_lift"].values())
