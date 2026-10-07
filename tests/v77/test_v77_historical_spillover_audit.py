"""The historical spillover audit must be able to fail. Each structural check gets a planted
violation that must be flagged and a clean case that must pass; the text check must flag a
positive claim and spare the same claim negated."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("spill", ROOT / "scripts" / "v77" / "audit_v77_historical_spillover.py")
S = importlib.util.module_from_spec(spec)
sys.modules["spill"] = S
spec.loader.exec_module(S)

CLEAN_ADAPTER = "class SyntheticModelBatch:\n    gene_ids: int\n    student_expression: int\n"
LEAKY_ADAPTER = "class SyntheticModelBatch:\n    gene_ids: int\n    source_index: int\n"
CLEAN_BRIDGE = 'F("source_index", C.LAWFUL_OPERATOR_CONTEXT)'
LEAKY_BRIDGE = 'F("operator_index", C.MODEL_VISIBLE)'


def test_raw_identity_on_the_model_batch_is_flagged():
    assert S.raw_ids_model_visible(CLEAN_ADAPTER, CLEAN_BRIDGE)["status"] == "PASS"
    assert S.raw_ids_model_visible(LEAKY_ADAPTER, CLEAN_BRIDGE)["status"] == "FAIL"
    assert S.raw_ids_model_visible(CLEAN_ADAPTER, LEAKY_BRIDGE)["status"] == "FAIL"


def test_runtime_names_are_flagged():
    assert S.old_runtime_classes({"a.py": "x = 1"})["status"] == "PASS"
    assert S.old_runtime_classes({"a.py": "guard = CurrentOptimizerStepGuardV4(opt)"})["status"] == "FAIL"


def _truth(d: Path, ops, sources, counts):
    d.mkdir(parents=True)
    (d / "TRUTH_MANIFEST.json").write_text(json.dumps(dict(operator_ids=ops, operator_sources=sources)))
    op = np.concatenate([np.full(c, i) for i, c in enumerate(counts)]).astype(np.int16)
    np.savez(d / "TRUTH_000000000_000000010.npz", operator_index=op)


def test_zero_quota_operator_loss_is_flagged_only_when_the_source_could_cover_it(tmp_path):
    ops, srcs = ["a", "b", "c"], ["HVS", "HVS", "NPH52"]
    _truth(tmp_path / "ok", ops, srcs, [3, 2, 4])
    _truth(tmp_path / "lost", ops, srcs, [5, 0, 4])
    _truth(tmp_path / "tiny", ["a", "b", "c"], ["HVS", "HVS", "HVS"], [1, 0, 0])
    assert S.zero_quota_operator_loss([tmp_path / "ok"])["status"] == "PASS"
    lost = S.zero_quota_operator_loss([tmp_path / "lost"])
    assert lost["status"] == "FAIL" and lost["worlds"][0]["unexpected_operator_loss"] == ["b"]
    assert S.zero_quota_operator_loss([tmp_path / "tiny"])["status"] == "PASS", (
        "one HVS cell cannot cover three operators; that loss is expected, not a regression")


def test_text_check_flags_a_claim_and_spares_its_negation():
    hits = S.text_checks_lines([("x.md", ["identifiability is resolved by the new generator",
                                          "identifiability is not resolved by the new generator"])])
    assert [h["line"] for h in hits["V47_V48_OVERWRITTEN"]] == [1]


def test_negation_words_like_nothing_and_none_spare_a_line():
    hits = S.text_checks_lines([("x.json", ["DEVELOPMENT_CALIBRATION: nothing here is independent confirmation",
                                            "none of this is confirmatory", "this run is confirmatory"])])
    assert [h["line"] for h in hits["SEED7302_AS_CONFIRMATION"]] == [3]
