from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import h5py
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT / "scripts/v4/stage81a3_audit_masking_calibration.py"


def load_script():
    spec = importlib.util.spec_from_file_location("stage81a3_masking", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_split_registry() -> pd.DataFrame:
    rows = []
    for study, count in (("SEA_AD", 68), ("HVS", 62), ("NPH52", 19)):
        rows.extend(
            {
                "study_id": study,
                "canonical_person_id": f"{study}::TRAIN_{index:03d}",
                "split_domain": "foundation",
                "split": "train",
            }
            for index in range(count)
        )
        rows.extend(
            {
                "study_id": study,
                "canonical_person_id": f"{study}::{split.upper()}_001",
                "split_domain": "foundation",
                "split": split,
            }
            for split in ("development", "sealed_holdout")
        )
    return pd.DataFrame(rows)


def test_candidate_mask_fractions_are_exploratory() -> None:
    module = load_script()
    assert module.CANDIDATE_MASK_FRACTIONS == (0.15, 0.25, 0.40, 0.50, 0.60, 0.70)
    assert module.MASK_REPLICATES == 3
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"candidate_fraction_status": "exploratory_not_frozen"' in source
    assert '"masking_policy_frozen": False' in source
    assert '"production_seed_resolved": False' in source


def test_mask_identity_is_deterministic_and_gene_order_invariant() -> None:
    module = load_script()
    genes = ["ENSG000003", "ENSG000001", "ENSG000002", "ENSG000004"]
    expected = module.mask_order(genes, "cell-A", 8102, 1)
    assert module.mask_order(genes, "cell-A", 8102, 1) == expected
    assert module.mask_order(list(reversed(genes)), "cell-A", 8102, 1) == expected
    assert module.mask_order(genes + ["ENSG000001"], "cell-A", 8102, 1) == expected
    assert module.mask_order(genes, "cell-A", 8102, 2) != expected


def test_masking_uses_only_measured_genes_and_preserves_measured_zero_semantics() -> None:
    module = load_script()
    measured = [f"ENSG{i:06d}" for i in range(10)]
    nonzero = {
        measured[0]: (4.0, 2.0),
        measured[1]: (1.0, 1.0),
    }
    rows = module.cell_mask_metrics(
        cell_id="cell-A",
        source="synthetic",
        source_dataset_id="synthetic-source",
        broad_cell_class="synthetic-class",
        donor_id="train-donor",
        measured_gene_ids=measured,
        nonzero_values=nonzero,
        raw_library_total=5.0,
        seed=8102,
    )
    assert len(rows) == 18
    assert {row["measured_genes"] for row in rows} == {10}
    assert {row["detected_genes"] for row in rows} == {2}
    assert {row["vocabulary_genes"] for row in rows} == {4096}
    for row in rows:
        expected_masked = int(row["mask_fraction"] * 10)
        assert row["context_masked_measured_genes"] == expected_masked
        assert row["visible_measured_genes"] == 10 - expected_masked
        assert row["visible_measured_genes"] >= row["visible_detected_genes"]
    seventy = [row for row in rows if row["mask_fraction"] == 0.70]
    assert {row["context_masked_measured_genes"] for row in seventy} == {7}


def test_unmeasured_nonzero_feature_fails_loudly() -> None:
    module = load_script()
    try:
        module.cell_mask_metrics(
            cell_id="cell-A",
            source="synthetic",
            source_dataset_id="synthetic-source",
            broad_cell_class="synthetic-class",
            donor_id="train-donor",
            measured_gene_ids=["ENSG000001"],
            nonzero_values={"ENSG_NOT_MEASURED": (1.0, 1.0)},
            raw_library_total=1.0,
            seed=8102,
        )
    except RuntimeError as exc:
        assert "Unmeasured nonzero feature" in str(exc)
    else:
        raise AssertionError("An unmeasured nonzero feature entered masking")


def test_only_foundation_train_donors_enter_roster() -> None:
    module = load_script()
    registry = synthetic_split_registry()
    donors = module.train_donors(registry)
    assert {study: len(values) for study, values in donors.items()} == {
        "SEA_AD": 68,
        "HVS": 62,
        "NPH52": 19,
    }
    assert not any("DEVELOPMENT" in donor or "SEALED" in donor for values in donors.values() for donor in values)


def test_source_and_class_cannot_change_gene_mask_probability() -> None:
    module = load_script()
    parameters = inspect.signature(module.mask_order).parameters
    assert set(parameters) == {"measured_gene_ids", "cell_id", "seed", "replicate"}
    assert "source" not in parameters
    assert "broad_cell_class" not in parameters
    assert "donor_id" not in parameters


def test_anndata_index_field_is_resolved_from_group_attribute(tmp_path: Path) -> None:
    module = load_script()
    path = tmp_path / "index.h5"
    with h5py.File(path, "w") as handle:
        obs = handle.create_group("obs")
        obs.attrs["_index"] = "cell_names"
        obs.create_dataset("cell_names", data=[b"cell-A", b"cell-B"])
    with h5py.File(path, "r") as handle:
        assert module.read_h5_index(handle["obs"]).tolist() == ["cell-A", "cell-B"]


def test_no_pathology_or_model_runtime_is_imported() -> None:
    source = SCRIPT.read_text(encoding="utf-8").lower()
    imports = {
        line.strip().split()[1].split(".", 1)[0]
        for line in source.splitlines()
        if line.strip().startswith("import ")
    }
    imports |= {
        line.strip().split()[1].split(".", 1)[0]
        for line in source.splitlines()
        if line.strip().startswith("from ")
    }
    assert imports.isdisjoint({"torch", "tensorflow", "jax", "flax", "transformers"})
    assert "pathology_sidecar" not in source
    assert "stage81a1d_nph_pathology" not in source
    assert '"pathology_opened": false' in source
    assert '"model_training_performed": false' in source
    r_sources = "\n".join(
        (PROJECT / relative).read_text(encoding="utf-8").lower()
        for relative in (
            "scripts/v4/stage81a3_extract_nph_sample.R",
            "scripts/v4/stage81a3_rebuild_nph_disposition_cache.R",
        )
    )
    for forbidden in (
        "braak", "cerad", "amyloid", "tau", "at8", "gfap", "iba1",
        "neun", "diagnosis", "pathology_sidecar", "torch", "tensorflow",
    ):
        assert forbidden not in r_sources


def test_outputs_do_not_modify_frozen_stage81a2_files() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'output_dir / "stage81a3_masking_calibration_summary.csv"' in source
    assert 'output_dir / "stage81a3_masking_calibration_strata.csv"' in source
    assert 'output_dir / "stage81a3_masking_calibration_report.json"' in source
    assert "write_csv(output_dir / \"stage81a2_" not in source
    assert "write_json(output_dir / \"stage81a2_" not in source
