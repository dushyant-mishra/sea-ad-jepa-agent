from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml


PROJECT = Path(__file__).resolve().parents[2]
CONFIG = PROJECT / "configs/v4/stage81a2_canonical_freeze.yaml"
SCRIPT = PROJECT / "scripts/v4/stage81a2_freeze_canonical_contract.py"
RESULTS = PROJECT / "results/v4"


def load_script():
    spec = importlib.util.spec_from_file_location("stage81a2", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_exact_required_prior_inventory_and_hashes() -> None:
    cfg = config()
    assert cfg["stage_id"] == "stage81a2"
    assert len(cfg["required_prior_inputs"]) == 25
    for relative, expected in cfg["required_prior_inputs"].items():
        path = PROJECT / relative
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_policy_forbids_training_merge_shards_cloud_and_fuzzy_matching() -> None:
    policy = config()["policy"]
    assert policy["pathology_blind_foundation"] is True
    assert policy["exact_identity_only"] is True
    assert policy["fuzzy_gene_mapping"] is False
    assert policy["fuzzy_donor_mapping"] is False
    assert policy["physical_matrix_merge"] is False
    assert policy["training_shards"] is False
    assert policy["cloud_upload"] is False
    assert policy["model_training"] is False
    assert policy["stage81b_started"] is False


def test_hvs_exact_resolution_when_audit_output_exists() -> None:
    path = RESULTS / "stage81a2_hvs_donor_resolution.csv"
    if not path.exists():
        return
    frame = pd.read_csv(path)
    assert frame.source_partition.nunique() == 24
    assert frame.exact_source_donor_id.nunique() == 78
    assert int(frame.cell_count.sum()) == 379330
    assert not frame.fuzzy_matching_used.astype(bool).any()
    assert not frame.explicit_alias_table_exists.astype(bool).any()


def test_nph_dispositions_are_exact_and_unresolved_excluded() -> None:
    path = PROJECT / config()["local_audit_inputs"]["nph_disposition_summary"]
    frame = pd.read_csv(path)
    totals = frame[frame.source_object == "ALL_SOURCE_OBJECTS"].set_index("disposition").cell_count
    assert int(totals.sum()) == 957659
    assert int(totals["retained_with_final_annotation"]) == 892828
    assert int(totals["missing_required_annotation"]) == 64831
    assert int(totals.get("unresolved", 0)) == 0


def test_nph_exact_52_and_25_19_8_groups() -> None:
    donors = pd.read_csv(PROJECT / config()["local_audit_inputs"]["nph_exact_donors"])
    assert donors.donor_id.nunique() == 52
    assert donors.pathology_group.value_counts().to_dict() == {"Ctrl": 25, "Abeta": 19, "AbetaTau": 8}


def test_nph_bounded_normalization_and_cell_weighting_contract() -> None:
    source = (PROJECT / "scripts/v4/stage81a2_audit_nph_freeze.R").read_text(encoding="utf-8")
    assert "sample_cap <- 16L" in source
    assert 'split_registry$cohort == "NPH_Ctrl" & split_registry$split == "train"' in source
    assert "Expected 19 NPH control training donors" in source
    assert "library_size <- Matrix::colSums(block)" in source
    assert "10000 / library_size" in source
    assert "transformed@x <- log1p(transformed@x)" in source
    assert "Matrix::rowSums(transformed)" in source
    assert "Matrix::rowSums(block > 0)" in source
    assert "donor_measured_cell_count" in source
    assert "donor_sum[observed] / donor_measured_cell_count[observed]" in source
    assert "donor_detection[observed] / donor_measured_cell_count[observed]" in source
    assert "rowMeans(transformed)" not in source
    assert "donor_object_count" not in source


def test_nph_measurement_masks_remain_source_specific() -> None:
    source = (PROJECT / "scripts/v4/stage81a2_audit_nph_freeze.R").read_text(encoding="utf-8")
    assert "feature_index <- match(rownames(object), all_features)" in source
    assert "donor_measured_cell_count[feature_index, donor]" in source
    assert "training_donors_measured = rowSums(observed)" in source
    assert 'donor_aggregation = "actual_selected_cell_weighted_with_source_measurement_mask"' in source


def test_known_exact_rna_atac_overlap_is_45() -> None:
    frame = pd.read_csv(RESULTS / "stage81a1d_living_human_duplicate_overlap_registry.csv")
    row = frame[(frame.left_dataset == "GSE226602") & (frame.right_dataset == "GSE226267")].iloc[0]
    assert int(row.exact_overlap_count) == 45
    assert not bool(row.fuzzy_matching_used)


def test_deterministic_group_split_and_no_leakage() -> None:
    module = load_script()
    keys = [f"D{i:03d}" for i in range(25)]
    one = module.deterministic_split(keys, "NPH_Ctrl", "foundation", 8102, 3, 3)
    two = module.deterministic_split(list(reversed(keys)), "NPH_Ctrl", "foundation", 8102, 3, 3)
    assert one == two
    assert list(one.values()).count("development") == 3
    assert list(one.values()).count("sealed_holdout") == 3
    assert list(one.values()).count("train") == 19


def test_split_registry_keeps_people_in_one_split_when_present() -> None:
    path = RESULTS / "stage81a2_split_registry.csv"
    if not path.exists():
        return
    frame = pd.read_csv(path)
    bounded = frame[frame.split.isin(["train", "development", "sealed_holdout"])]
    assert int(bounded.groupby("split_group_id").split.nunique().max()) == 1
    assert not bounded.pathology_used_for_foundation_split.astype(bool).any()


def test_dataset_role_firewalls_when_present() -> None:
    path = RESULTS / "stage81a2_dataset_role_registry.csv"
    if not path.exists():
        return
    frame = pd.read_csv(path).set_index("dataset_id")
    assert frame.loc["siletti_hbca_all_non_neuronal", "role"] == "whole_study_external_holdout"
    assert not bool(frame.loc["gse243292_full_dlpfc_h5ad", "foundation_vocabulary_eligible"])
    assert frame.loc["gse146639_processed_microglia_archive", "tissue_state"] == "postmortem_brain"
    for dataset in ("GSE302937", "GSE200164", "GSE226602", "GSE226267", "GSE305625"):
        assert not bool(frame.loc[dataset, "foundation_vocabulary_eligible"])


def test_pathology_sidecar_is_not_a_vocabulary_argument() -> None:
    module = load_script()
    signature = inspect.signature(module.measurement_and_vocabulary)
    assert "pathology" not in signature.parameters
    source = inspect.getsource(module.measurement_and_vocabulary).lower()
    assert not any(term in source for term in ("braak", "cerad", "amyloid", "tau", "diagnosis"))


def test_exact_gene_mapping_has_no_fuzzy_branch(tmp_path: Path) -> None:
    module = load_script()
    nph = tmp_path / "nph.csv.gz"
    pd.DataFrame({"source_object": ["A.qs", "A.qs"], "source_feature_index": [0, 1],
                  "source_feature_symbol": ["GENE1", "UNKNOWN"], "source_feature_type": ["Gene Expression"] * 2}).to_csv(nph, index=False, compression="gzip")
    genes = module.canonical_genes({"GENE1": ("ENSG000001", "GENE1")},
                                   {"GENE1": ("ENSG000001", "GENE1")}, nph)
    mapped = genes[(genes.source_dataset_id == "NPH52::A.qs") & (genes.source_feature_symbol == "GENE1")].iloc[0]
    unresolved = genes[(genes.source_dataset_id == "NPH52::A.qs") & (genes.source_feature_symbol == "UNKNOWN")].iloc[0]
    assert mapped.mapping_status == "exact"
    assert unresolved.mapping_status == "unresolved"
    assert "fuzzy" not in " ".join(genes.mapping_method.astype(str)).lower()


@pytest.mark.parametrize("forbidden", ["genomic_peak", "Antibody Capture", "miRNA", "Negative Control Probe"])
def test_non_rna_features_cannot_be_valid_vocabulary_rows(forbidden: str) -> None:
    module = load_script()
    row = module.gene_row("source", "0", forbidden, "", True, "unresolved_exact_symbol")
    assert row["rna_vocabulary_eligible"] is False


def test_measurement_contract_distinguishes_zero_from_unmeasured_when_present() -> None:
    path = RESULTS / "stage81a2_gene_measurement_registry.csv"
    if not path.exists() or path.stat().st_size == 0:
        return
    frame = pd.read_csv(path)
    assert frame.measured_zero_distinct_from_unmeasured.astype(bool).all()
    assert set(frame.measurement_status).issubset({
        "measured_value_requires_runtime_zero_nonzero_resolution",
        "not_in_source_feature_universe",
    })


def test_matrix_semantics_are_explicit_when_present() -> None:
    path = RESULTS / "stage81a2_matrix_semantics_contract.csv"
    if not path.exists():
        return
    frame = pd.read_csv(path)
    assert frame.foundation_eligible.astype(bool).all()
    assert frame.integer_counts_available.astype(bool).all()
    assert set(frame.matrix_slot).issuperset({"layers/UMIs", "raw/X", "counts"})
    assert not frame.matrix_semantics.isna().any()


def test_vocabulary_is_deterministic_exact_and_ordered_when_frozen() -> None:
    report_path = RESULTS / "stage81a2_freeze_report.json"
    vocab_path = RESULTS / "stage81a2_foundation_vocabulary.csv"
    if not report_path.exists() or not vocab_path.exists():
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report.get("stage81a2_pass"):
        return
    frame = pd.read_csv(vocab_path)
    assert len(frame) == 4096
    assert frame.vocabulary_index.tolist() == list(range(4096))
    assert not frame.canonical_ensembl_gene_id.duplicated().any()
    assert frame.vocabulary_hash.nunique() == 1
    module = load_script()
    assert frame.vocabulary_hash.iloc[0] == module.source_hash(frame.canonical_ensembl_gene_id.astype(str))


def test_sampling_contract_is_donor_first_and_pathology_blind() -> None:
    contract = config()["sampling_contract"]
    assert contract["hierarchy"] == ["tissue_state", "study", "donor", "broad_cell_class", "cell"]
    assert contract["sealed_donors_allowed"] is False
    assert contract["pathology_labels_allowed"] is False


def test_outputs_are_portable_when_present() -> None:
    for path in RESULTS.glob("stage81a2_*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "C:\\" not in text
            assert "D:\\" not in text
            assert "/mnt/" not in text
            assert "file://" not in text


def test_freeze_report_preserves_scope_boundaries_when_present() -> None:
    path = RESULTS / "stage81a2_freeze_report.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["physical_matrix_merge_performed"] is False
    assert report["training_shards_created"] is False
    assert report["cloud_upload_performed"] is False
    assert report["model_trained"] is False
    assert report["stage81b_started"] is False
    if report["stage81a2_pass"]:
        assert report["ready_for_stage81b"] is True
        assert report["readiness_blockers"] == []


def test_protected_file_hashes_unchanged() -> None:
    for relative, expected in config()["protected_worktree_signatures"].items():
        assert hashlib.sha256((PROJECT / relative).read_bytes()).hexdigest() == expected
