"""The S157 terminal receipt is frozen. Its statements, the evidence they rest on, and the older
records it marks as superseded cannot change silently: a change needs a successor receipt that
names V1, never an edit of V1 or of the history it annotates."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "results" / "v77" / "V77_S157_TERMINAL_RECEIPT_V1.json"
STATEMENTS_SHA256 = "35aa2702cc6240a79bcc974aae9fdb8256d9eebbf93c893e63c3ba639efbaccf"
# Older records the terminal marks as superseded, scoped or withdrawn. They stay byte-identical.
HISTORY_SHA256 = {
    "results/v77/REHEARSAL_ZERO_UPDATE_PLUMBING_QUALIFICATION_V1.json":
        "e5062dbe2f5a26e958a785104329beb0f710c1efd4903eea9fa6934a346ff76c",
    "results/v77/V77_PHASE4_WORLD_EXTENSION_SPEC_V1.json":
        "f9d6887f74252ba148c7511a0638b89a24f1f2827a64ce83ecd57147191c988b",
    "results/v77/V77_REAL_WITHIN_COHORT_ENVELOPE_V1.json":
        "a2682f6c6ccfc5a500bc3a6d57ab671594e6273406d9a4d332b393dcb5cfd5be",
    "results/v77/V77_REAL_WITHIN_COHORT_ENVELOPE_V2.json":
        "5bfd007c3f9b66bff8653152869b02e1b4c8960a895974051be303dde76e1a29",
    "results/v77/V77_WITHIN_COHORT_AUTHORITY_CORRECTION_V1.json":
        "9b80fd5d31d40da9023eccd3ff47c6b1300f674b7ded4c561533a08d2e980985",
}


def _load():
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def _statements_digest(rec):
    pairs = [[s["id"], s["statement"]] for s in rec["TERMINAL_STATEMENTS"]]
    return hashlib.sha256(json.dumps(pairs, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def test_terminal_statements_are_frozen():
    rec = _load()
    assert rec["status"].startswith("FROZEN_TERMINAL")
    assert [s["id"] for s in rec["TERMINAL_STATEMENTS"]] == [f"T{i}" for i in range(1, 8)]
    assert _statements_digest(rec) == STATEMENTS_SHA256, (
        "S157 terminal statements changed: write a successor receipt naming V1 instead of editing V1")


def test_the_freeze_guard_can_fail():
    mutated = copy.deepcopy(_load())
    mutated["TERMINAL_STATEMENTS"][0]["statement"] = "The exact same-assay semantic twin is resolved."
    assert _statements_digest(mutated) != STATEMENTS_SHA256


def test_terminal_evidence_is_unchanged():
    for rel, digest in _load()["EVIDENCE"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel


def test_superseded_history_is_marked_not_rewritten():
    rec = _load()
    assert all(s["status"] and s["superseded_by"] for s in rec["SUPERSEDED_OLDER_STATEMENTS"])
    for rel, digest in HISTORY_SHA256.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, f"{rel} was rewritten"
