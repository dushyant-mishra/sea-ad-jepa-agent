"""Independent GSE311359 guide-feature identity red-team.

The real evidence inspected here is ONLY PR77's committed lightweight guide
identity CSV. Matrix and external feature IDs live on Claude's GPU laptop.
The producer must fail closed until those IDs can be inspected and an
independent feature-ID→guide-library authority is reviewed.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRODUCER = (ROOT / "analysis/therapeutic_perturbation_etl/scripts"
            / "build_gse311359_intervention_effects_v1.py")
EVIDENCE = (ROOT / "analysis/therapeutic_perturbation_etl/evidence/gse311359"
            / "GSE311359_perturbation_identity.csv")
REVIEWED_CSV_SHA256 = (
    "1eeb4e40f14ec2ebe7472d7bb80769ae35bdb8df8ccbf4308493c8441eb363b5"
)

spec = importlib.util.spec_from_file_location("gse311359_producer_under_review", PRODUCER)
assert spec is not None and spec.loader is not None
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)


def test_real_committed_lightweight_identity_table_exposes_bin1_collision():
    raw = EVIDENCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == REVIEWED_CSV_SHA256
    with EVIDENCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    guides = [row["guide_id"] for row in rows]
    assert len(guides) == 381
    assert len(set(guides)) == 379
    assert guides.count("BIN1") == 3
    assert all(row["target_id"] == "BIN1" for row in rows if row["guide_id"] == "BIN1")
    with pytest.raises(SystemExit, match="STOP_GSE311359_DUPLICATE_GUIDE_NAMES"):
        producer.assert_unambiguous_feature_ids(
            [f"SYNTHETIC_FEATURE_{i}" for i in range(len(guides))],
            guides, ["CRISPR Guide Capture"] * len(guides),
        )


def test_distinct_guide_feature_ids_cannot_make_duplicate_names_valid():
    with pytest.raises(SystemExit, match="INDEPENDENT_FEATURE_ID_TO_GUIDE_LIBRARY_AUTHORITY"):
        producer.assert_unambiguous_feature_ids(
            ["GUIDE_FEATURE_1", "GUIDE_FEATURE_2", "GUIDE_FEATURE_3"],
            ["BIN1", "BIN1", "OTHER"],
            ["CRISPR Guide Capture"] * 3,
        )


def test_duplicate_feature_ids_fail_independently_of_unique_guide_names():
    with pytest.raises(SystemExit, match="STOP_GSE311359_DUPLICATE_FEATURE_IDS"):
        producer.assert_unambiguous_feature_ids(
            ["SAME_ID", "SAME_ID"], ["GUIDE_A", "GUIDE_B"],
            ["CRISPR Guide Capture"] * 2,
        )


def test_unique_guide_names_positive_control():
    producer.assert_unambiguous_feature_ids(
        ["ENSEMBL_ID_1", "GUIDE_FEATURE_1", "GUIDE_FEATURE_2"],
        ["GENE_A", "GUIDE_A_g1", "GUIDE_A_g2"],
        ["Gene Expression", "CRISPR Guide Capture", "CRISPR Guide Capture"],
    )


def test_empty_guide_name_rejected():
    with pytest.raises(SystemExit, match="STOP_GSE311359_EMPTY_GUIDE_NAME"):
        producer.assert_unambiguous_feature_ids(
            ["ID_1"], [""], ["CRISPR Guide Capture"],
        )


def _write_gz(path, lines):
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.writelines(lines)


def test_producer_stops_before_creating_output_for_duplicate_guides(tmp_path, monkeypatch):
    inp = tmp_path / "source"
    inp.mkdir()
    out = tmp_path / "must_not_exist"
    # Tiny disposable test-only 10x feature table: the producer's very first
    # source-identity gate is exercised; NO 105k-cell payload is fabricated.
    monkeypatch.setattr(producer, "N_FEATURES", 4)
    monkeypatch.setattr(producer, "SAMPLES", ("S1",))
    _write_gz(inp / "GSMTEST_S1_features.tsv.gz", [
        "ENSG00000000001\tGENE_A\tGene Expression\n",
        "CR1\tBIN1\tCRISPR Guide Capture\n",
        "CR2\tBIN1\tCRISPR Guide Capture\n",
        "CR3\tGUIDE_B\tCRISPR Guide Capture\n",
    ])
    monkeypatch.setattr(sys, "argv", [
        "synthetic-test-only", "--extracted-dir", str(inp),
        "--out-dir", str(out),
    ])
    with pytest.raises(SystemExit, match="STOP_GSE311359_DUPLICATE_GUIDE_NAMES"):
        producer.main()
    assert not out.exists(), "invalid guide identity must not publish partial artifacts"


def test_producer_refuses_existing_scientific_results_without_overwriting(tmp_path, monkeypatch):
    inp = tmp_path / "input"
    inp.mkdir()
    out = tmp_path / "historical"
    out.mkdir()
    old = out / "GSE311359_etl_summary.json"
    old.write_text("PR77_HISTORICAL_OUTPUTS_MUST_SURVIVE")
    monkeypatch.setattr(sys, "argv", [
        "synthetic-test-only", "--extracted-dir", str(inp), "--out-dir", str(out),
    ])
    with pytest.raises(SystemExit, match="OUTPUT_EXISTS__VERSIONED_SUCCESSOR_REQUIRED"):
        producer.main()
    assert old.read_text() == "PR77_HISTORICAL_OUTPUTS_MUST_SURVIVE"
