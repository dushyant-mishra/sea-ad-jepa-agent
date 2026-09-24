"""Synthetic fixture regression for the assay/detection correction.

No real GSE254205 files are read. Test V1 vs V2 on the same fake nine-sample
counts to show that the correction changes interpretation, not old effect values.
"""
import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parents[1] / "analysis/therapeutic_perturbation_etl/scripts"
V1 = HERE / "build_gse254205_drug_response_v1.py"
V2 = HERE / "build_gse254205_drug_response_v2.py"
CONDITIONS = ("NT", "AB", "AB_GNE")
REPLICATES = ("rep1", "rep2", "rep3")


@pytest.fixture
def nine_sample_fixture(tmp_path):
    src = tmp_path / "fake_counts"
    src.mkdir()
    # B is assayed in all nine files but undetected in every sample.
    # A/C are detectable; amplitudes differ by experimental condition.
    values = {"NT": (10, 0, 5), "AB": (20, 0, 8), "AB_GNE": (16, 0, 12)}
    for condition in CONDITIONS:
        for rep in REPLICATES:
            path = src / f"{condition}_{rep}ReadsPerGene.out.tab"
            path.write_text(
                "Gene\tCounts\n"
                + "".join(
                    f"{gene}\t{count}\n"
                    for gene, count in zip(("ENSG_A", "ENSG_B", "ENSG_C"), values[condition])
                ), encoding="utf-8",
            )
    return src


def run(script, src, output):
    proc = subprocess.run(
        [sys.executable, str(script), "--counts-dir", str(src), "--out-dir", str(output)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_assayed_undetected_never_masquerades_as_unmeasured(nine_sample_fixture, tmp_path):
    out = tmp_path / "v2"
    run(V2, nine_sample_fixture, out)
    m = json.loads((out / "GSE254205_drug_response_summary_v2.json").read_text())
    assert m["genes_in_annotation"] == 3
    assert m["genes_assayed"] == 3
    assert m["genes_detected_anywhere"] == 2
    assert m["genes_assayed_but_undetected"] == 1
    assert m["genes_structurally_unmeasured_within_reference"] == 0
    assert m["genes_excluded_from_effects_by_detection_filter"] == 1
    features = read_rows(out / "GSE254205_feature_assay_status_v2.csv")
    assert len(features) == 3
    b = next(r for r in features if r["gene_id"] == "ENSG_B")
    assert b["assayed"] == "True"
    assert b["detected_anywhere"] == "False"
    assert b["assay_status"] == "ASSAYED_BUT_UNDETECTED"
    assert b["n_samples_detected"] == "0"
    assert b["included_in_v1_compatible_effects"] == "False"


def test_old_effects_preserved_exactly_except_explicit_v2_metadata(nine_sample_fixture, tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    run(V1, nine_sample_fixture, old)
    run(V2, nine_sample_fixture, new)
    original = read_rows(old / "GSE254205_drug_response_effects.csv")
    versioned = read_rows(new / "GSE254205_drug_response_effects_v2.csv")
    assert len(original) == len(versioned) == 6
    for earlier, now in zip(original, versioned):
        for key in earlier:
            assert earlier[key] == now[key], (key, earlier[key], now[key])
        assert now["assayed"] == "True"
        assert now["detected_anywhere"] == "True"
    old_summary = json.loads((old / "GSE254205_drug_response_summary.json").read_text())
    new_summary = json.loads((new / "GSE254205_drug_response_summary_v2.json").read_text())
    assert old_summary["contrasts"] == new_summary["contrasts"]
    assert new_summary["v1_result_replaced"] is False


def test_versioned_writer_refuses_any_nonempty_output_directory(nine_sample_fixture, tmp_path):
    out = tmp_path / "already"
    out.mkdir()
    sentinel = out / "GSE254205_drug_response_summary.json"
    sentinel.write_text("HISTORICAL_DO_NOT_OVERWRITE")
    proc = subprocess.run(
        [sys.executable, str(V2), "--counts-dir", str(nine_sample_fixture),
         "--out-dir", str(out)], capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "NEW EMPTY directory" in (proc.stdout + proc.stderr)
    assert sentinel.read_text() == "HISTORICAL_DO_NOT_OVERWRITE"


def test_structurally_missing_gene_in_one_count_file_fails(nine_sample_fixture, tmp_path):
    path = nine_sample_fixture / "NT_rep1ReadsPerGene.out.tab"
    path.write_text("Gene\tCounts\nENSG_A\t10\nENSG_C\t5\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(V2), "--counts-dir", str(nine_sample_fixture),
         "--out-dir", str(tmp_path / "reject")], capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "different gene order/universe" in (proc.stdout + proc.stderr)
