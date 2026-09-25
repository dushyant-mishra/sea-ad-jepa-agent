"""Pure adversarial controls for the real-data clean-head CRISPRbrain replayer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from analysis.therapeutic_perturbation_etl.scripts import clean_replay_crisprbrain_against_legacy_receipt_v1 as clean


def _fixture(tmp_path):
    root = tmp_path / "repo"
    folder = root / clean.RECEIPT_REL.parent
    folder.mkdir(parents=True)
    outputs = []
    for name in (
        "concordance_by_abundance.csv",
        "fdr_threshold_sensitivity.csv",
        "jointly_significant_rows.csv",
        "non_replication_classification.csv",
        "per_target_concordance.csv",
        "target_engagement.csv",
        "target_identity.csv",
    ):
        p = folder / name
        p.write_bytes(("column\n" + name + "\n").encode())
        outputs.append({
            "path": str(p.relative_to(root)).replace("\\", "/"),
            "rows": 1,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        })
    return root, {"outputs": outputs}


def test_01_all_exact_original_csv_digest_verified(tmp_path):
    root, receipt = _fixture(tmp_path)
    rows = clean.validate_original_outputs(root, receipt)
    assert len(rows) == 7
    assert len({r["relative_path"] for r in rows}) == 7


def test_02_byte_tamper_is_detected_even_with_correct_row_count(tmp_path):
    root, receipt = _fixture(tmp_path)
    p = root / receipt["outputs"][0]["path"]
    p.write_bytes(p.read_bytes() + b"\n")
    with pytest.raises(clean.ReplayError, match="hash drift"):
        clean.validate_original_outputs(root, receipt)


def test_03_duplicate_historical_output_fails_closed(tmp_path):
    root, receipt = _fixture(tmp_path)
    receipt["outputs"][-1] = dict(receipt["outputs"][0])
    with pytest.raises(clean.ReplayError, match="census|duplicate"):
        clean.validate_original_outputs(root, receipt)


def test_04_unexpected_file_path_fails_closed(tmp_path):
    root, receipt = _fixture(tmp_path)
    receipt["outputs"][0]["path"] = "historical_small_run/concordance_by_abundance.csv"
    with pytest.raises(clean.ReplayError, match="path-escaped"):
        clean.validate_original_outputs(root, receipt)


def test_05_scientific_value_change_is_never_silently_ignored():
    old = {"S3": {"effect": .072, "target": ["STAT2", "ZNF644"]}, "generated_utc": "t0"}
    new = {"S3": {"effect": .073, "target": ["STAT2", "ZNF644"]}, "generated_utc": "t1"}
    result = clean.compare_scientific_fields(old, new)
    assert not result["fields_exact_match"]
    assert result["different_field_paths"] == ["/S3/effect"]


def test_06_only_four_declared_volatile_keys_excluded():
    a = {
        "generated_utc": "t0", "environment": {"python": "3.9"},
        "git_head": "old", "git_dirty": True,
        "inputs": [{"sha256": "x"}], "outputs": [{"sha256": "y"}],
        "S3": {"paired_rows": 406118},
    }
    b = {
        **a, "generated_utc": "t1", "environment": {"python": "3.11"},
        "git_head": "new", "git_dirty": False,
    }
    assert clean.compare_scientific_fields(a, b)["fields_exact_match"]
    b["inputs"] = [{"sha256": "different"}]
    assert not clean.compare_scientific_fields(a, b)["fields_exact_match"]
    b["inputs"] = a["inputs"]
    b["outputs"] = [{"sha256": "different"}]
    assert not clean.compare_scientific_fields(a, b)["fields_exact_match"]


def test_07_field_deletion_is_not_treated_as_equality():
    result = clean.compare_scientific_fields({"S3": {"pooled_n": 406118}}, {"S3": {}})
    assert result["different_field_count"] == 1
    assert result["different_field_paths"] == ["/S3/pooled_n"]


def test_08_no_false_equality_between_bool_and_int():
    result = clean.compare_scientific_fields({"S3": {"qualifies": True}}, {"S3": {"qualifies": 1}})
    assert not result["fields_exact_match"]


def test_09_clean_replay_refuses_report_inside_checkout_without_touching_inputs(tmp_path):
    root, _ = _fixture(tmp_path)
    with pytest.raises(clean.ReplayError, match="OUTSIDE"):
        clean.replay(root, root / "new_receipt.json")


def test_10_duplicate_existing_report_fails_without_touching_checkout(tmp_path):
    root, _ = _fixture(tmp_path)
    report = tmp_path / "preexisting.json"
    report.write_text("sentinel")
    with pytest.raises(clean.ReplayError, match="overwrite"):
        clean.replay(root, report)
    assert report.read_text() == "sentinel"
