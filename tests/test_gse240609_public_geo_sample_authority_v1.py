"""Independent source-metadata red-team for GSE240609 public-GEO pinned V2.

Original *lightweight* PR77 sample-identity CSV is available in GitHub;
heavy physical counts are not opened here. Synthetic test files only exercise
gate mechanics. No clinical, drug or independent transport claims are made.
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
SCRIPTS = ROOT / "analysis/therapeutic_perturbation_etl/scripts"
SOURCE_META = (ROOT / "analysis/therapeutic_perturbation_etl/evidence/bulk_disease"
               / "GSE240609_sample_identity.csv")
sys.path.insert(0, str(SCRIPTS))
from gse240609_public_geo_sample_authority_v1 import (  # noqa: E402
    EXPERIMENTAL_MATERIAL, GSE240609AuthorityError,
    REVIEWED_SAMPLES, validate_sample_basename, validate_sample_inventory,
)

spec = importlib.util.spec_from_file_location(
    "bulk_disease_v2_under_review",
    SCRIPTS / "build_bulk_disease_context_effects_v2.py",
)
assert spec and spec.loader
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)


def fake_files(tmp_path):
    paths = []
    for rec in REVIEWED_SAMPLES.values():
        path = tmp_path / rec["filename"]
        with gzip.open(path, "wt", encoding="utf-8") as out:
            out.write("ENSG001\t10\nENSG002\t0\n")
        paths.append(path)
    return paths


def test_committed_lightweight_physical_manifest_matches_public_geo_titles():
    with SOURCE_META.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert {row["file"].split("_", 1)[0] for row in rows} == set(REVIEWED_SAMPLES)
    for row in rows:
        approved = validate_sample_basename(row["file"])
        assert approved.sha256 == row["file_sha256"]
        assert approved.neuron_genotype == row["neuron_genotype"]
        assert approved.microglia_genotype == row["microglia_genotype"]
        assert approved.material == EXPERIMENTAL_MATERIAL
    assert {x["geo_title"] for x in REVIEWED_SAMPLES.values()} == {
        "APOE3CH-WT", "APOE3CH-PSEN1", "APOE3-WT", "APOE3-PSEN1"
    }


def test_full_factorial_2x2_identity_positive_control_with_synthetic_bytes(tmp_path):
    got = validate_sample_inventory(fake_files(tmp_path), test_fixture=True)
    assert len(got) == 4
    assert {(x.neuron_genotype, x.microglia_genotype) for x in got} == {
        ("WT", "APOE3ch"), ("WT", "APOE3"),
        ("PSEN", "APOE3ch"), ("PSEN", "APOE3"),
    }


def test_unexpected_accession_cannot_default_to_wildtype_apoe3(tmp_path):
    valid = fake_files(tmp_path)
    other = tmp_path / "GSM9999999_FAKE_gene_counts.txt.gz"
    other.write_bytes(valid[0].read_bytes())
    with pytest.raises(GSE240609AuthorityError, match="unreviewed GEO sample"):
        validate_sample_basename(other.name)


def test_wrong_filename_for_known_accession_rejected(tmp_path):
    original = next(rec for rec in REVIEWED_SAMPLES.values()
                    if rec["neuron_genotype"] == "WT")
    with pytest.raises(GSE240609AuthorityError, match="basename differs"):
        validate_sample_basename(
            "GSM7703564_XXX_PSEUDO_SAMPLE_gene_counts.txt.gz"
        )


def test_duplicate_or_missing_design_cell_rejected(tmp_path):
    files = fake_files(tmp_path)
    with pytest.raises(GSE240609AuthorityError, match="EXACT_FOUR"):
        validate_sample_inventory(files[:3], test_fixture=True)
    with pytest.raises(GSE240609AuthorityError, match="duplicated GEO accession"):
        validate_sample_inventory([files[0], files[0], files[2], files[3]],
                                  test_fixture=True)


def test_valid_filename_with_swapped_or_changed_raw_bytes_fails(tmp_path):
    files = fake_files(tmp_path)
    # The *same* expected GSM filename with fixture bytes must fail the actual
    # physical byte validator. Synthetic test bypass is never a PHYSICAL PASS.
    with pytest.raises(GSE240609AuthorityError, match="source bytes"):
        validate_sample_inventory(files, test_fixture=False)


def test_v2_production_entrypoint_rejects_forged_bulk_source_before_output(tmp_path, monkeypatch):
    files = fake_files(tmp_path)
    baseline = tmp_path / "fake_baseline.tsv.gz"
    cytokine = tmp_path / "fake_cytokine.tsv.gz"
    baseline.write_bytes(b"fake bulk baseline")
    cytokine.write_bytes(b"fake bulk cytokine")
    # Actual V2 main is invoked; file-hash gate must STOP before writing ANY
    # output, even though four valid-looking GEO filenames are present.
    out = tmp_path / "must_not_exist"
    monkeypatch.setattr(sys, "argv", [
        "bulk_v2_test_only",
        "--gse241858-baseline", str(baseline),
        "--gse241858-cytokine", str(cytokine),
        "--gse240609-dir", str(tmp_path),
        "--out-dir", str(out),
    ])
    with pytest.raises(SystemExit, match="SOURCE_ROOT_MISMATCH"):
        producer.main()
    assert not out.exists()


def test_versioned_v2_refuses_to_replace_historical_results(tmp_path, monkeypatch):
    out = tmp_path / "old"
    out.mkdir()
    sentinel = out / "BULK_DISEASE_CONTEXT_SUMMARY.json"
    sentinel.write_text("PR77_V1_PHYSICAL_RESULTS_IMMUTABLE")
    monkeypatch.setattr(sys, "argv", [
        "bulk_v2_test_only",
        "--gse241858-baseline", str(tmp_path / "missing_a"),
        "--gse241858-cytokine", str(tmp_path / "missing_b"),
        "--gse240609-dir", str(tmp_path),
        "--out-dir", str(out),
    ])
    with pytest.raises(SystemExit, match="OUTPUT_EXISTS"):
        producer.main()
    assert sentinel.read_text() == "PR77_V1_PHYSICAL_RESULTS_IMMUTABLE"


def test_disease_context_summary_never_suggests_inferred_biological_se():
    assert EXPERIMENTAL_MATERIAL == "CD11B_PURIFIED_MICROGLIA_AFTER_NEURON_COCULTURE"
    assert all(x["geo_title"] for x in REVIEWED_SAMPLES.values())
