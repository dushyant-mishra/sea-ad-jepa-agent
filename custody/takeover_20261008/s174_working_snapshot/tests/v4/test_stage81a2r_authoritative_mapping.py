from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from sea_ad_jepa.v4.gene_identity_authority import (
    AuthorityIndex,
    EnsemblGene,
    HgncGene,
    broad_biotype,
    classify_symbol_only,
    classify_source_native_feature,
    history_current_replacements,
    normalize_ensembl_gene_id,
    source_family,
)
from scripts.v4.stage81a2r_authoritative_gene_identity_recovery import (
    EXACT_TERMINAL,
    adjudicate_row,
    build_collisions,
    build_decisions,
    build_exact_registry,
    build_measurement,
)
from scripts.v4.stage81a2r_build_review_package import (
    build_foundation_reconciliation,
    build_nph_frozen_vocab_adjudication,
    history_relation,
    semantic_hash,
)
from scripts.v4.stage81a2r_audit_all_downloaded_identity import (
    adjudicate_features,
    dataset_id_from_matrix,
    feature_lines,
    matrix_text_features,
    modality,
    summarize,
)
from scripts.v4.stage81a2r_adjudicate_unresolved_identities import (
    adjudicate_protected_dossier,
    classify_one,
    unique_map,
)
from scripts.v4.stage81a2r_close_authoritative_identity_audit import (
    build_foundation_molecular_address_package,
    evidence_hash,
    finalize_dossier,
    foundation_identity_accounting,
    matrix_accounting_reconciliation,
    present,
    valid_ensembl,
    valid_ncbi,
)


def eid(number: int) -> str:
    return f"ENSG{number:011d}"


@pytest.fixture
def authority() -> AuthorityIndex:
    genes = {
        eid(1): EnsemblGene(eid(1), f"{eid(1)}.4", "CUR", "protein_coding", "1", 1, 10, "+"),
        eid(2): EnsemblGene(eid(2), f"{eid(2)}.2", "NEW", "protein_coding", "2", 11, 20, "+"),
        eid(3): EnsemblGene(eid(3), f"{eid(3)}.1", "NONHGNC", "lncRNA", "3", 21, 30, "-"),
        eid(4): EnsemblGene(eid(4), f"{eid(4)}.7", "HISTNEW", "protein_coding", "4", 31, 40, "+"),
        eid(5): EnsemblGene(eid(5), f"{eid(5)}.3", "OTHER", "protein_coding", "5", 41, 50, "+"),
        eid(6): EnsemblGene(eid(6), f"{eid(6)}.1", "PSEUDO", "processed_pseudogene", "6", 51, 60, "-"),
    }
    h1 = HgncGene("HGNC:1", "CUR", "current", "protein-coding gene", "gene with protein product", eid(1), ("PREV1", "PREVCOLL"), ("ALIAS1", "ALIASCOLL"))
    h2 = HgncGene("HGNC:2", "OTHER", "other", "protein-coding gene", "gene with protein product", eid(5), ("PREVCOLL",), ("ALIASCOLL",))
    records = {h1.hgnc_id: h1, h2.hgnc_id: h2}
    return AuthorityIndex(
        ensembl_by_id=genes,
        ensembl_by_symbol={gene.symbol: (gene.stable_id,) for gene in genes.values()},
        hgnc_by_id=records,
        hgnc_approved={"CUR": ("HGNC:1",), "OTHER": ("HGNC:2",)},
        hgnc_previous={"PREV1": ("HGNC:1",), "PREVCOLL": ("HGNC:1", "HGNC:2")},
        hgnc_alias={"ALIAS1": ("HGNC:1",), "ALIASCOLL": ("HGNC:1", "HGNC:2")},
        hgnc_withdrawn={"WITHDRAWN1": ("HGNC:1",), "SPLIT": ("HGNC:1", "HGNC:2"), "DEAD": ()},
    )


def row(symbol: str, canonical: str = "", method: str = "unresolved_exact_symbol", prior: str = "AMBIGUOUS_UNRESOLVED") -> SimpleNamespace:
    return SimpleNamespace(
        source_feature_symbol=symbol,
        source_feature_id="0",
        source_feature_type="Gene Expression",
        canonical_ensembl_gene_id=canonical,
        mapping_method=method,
        mapping_decision=prior,
    )


def test_version_suffix_stripping_preserves_original():
    assert normalize_ensembl_gene_id(f" {eid(1)}.12 ") == (eid(1), f"{eid(1)}.12", "12")


def test_current_exact_ensembl_resolves(authority):
    result = adjudicate_row(row("CUR", eid(1), "exact_source_ensembl_symbol_pair"), authority, {}, {eid(1)})
    assert result["terminal_disposition"] == "EXACT_CURRENT_ENSEMBL"


def test_historical_unique_replacement_resolves(authority):
    old = eid(100)
    result = adjudicate_row(row("HISTNEW", old, "exact_source_ensembl_symbol_pair"), authority, {old: {"latest": f"{old}.2", "possible_replacement": [{"stable_id": eid(4)}]}}, {eid(1)})
    assert result["terminal_disposition"] == "EXACT_HISTORICAL_ENSEMBL_TO_CURRENT"


def test_historical_multiple_replacements_does_not_choose(authority):
    old = eid(100)
    result = adjudicate_row(row("", old, "exact_source_ensembl_symbol_pair"), authority, {old: {"possible_replacement": [{"stable_id": eid(1)}, {"stable_id": eid(2)}]}}, set())
    assert result["terminal_disposition"] == "LEGACY_EXACT_ENSEMBL_MULTIPLE_CURRENT_REPLACEMENTS"
    assert not result["authority_current_ensembl_id"]


def test_historical_no_replacement_is_legacy(authority):
    old = eid(100)
    result = adjudicate_row(row("", old, "exact_source_ensembl_symbol_pair"), authority, {old: {"possible_replacement": []}}, set())
    assert result["terminal_disposition"] == "LEGACY_EXACT_ENSEMBL_NO_CURRENT_REPLACEMENT"


def test_hgnc_approved_symbol_resolves(authority):
    assert classify_symbol_only("CUR", authority)[:2] == ("EXACT_HGNC_APPROVED_TO_ENSEMBL", eid(1))


def test_unique_previous_symbol_resolves(authority):
    assert classify_symbol_only("PREV1", authority)[:2] == ("EXACT_HGNC_PREVIOUS_SYMBOL_RECOVERED", eid(1))


def test_previous_symbol_collision_is_ambiguous(authority):
    assert classify_symbol_only("PREVCOLL", authority)[0] == "AMBIGUOUS_PREVIOUS_SYMBOL_MULTIPLE_TARGETS"


def test_unique_alias_resolves(authority):
    assert classify_symbol_only("ALIAS1", authority)[:2] == ("EXACT_HGNC_ALIAS_RECOVERED", eid(1))


def test_alias_collision_is_ambiguous(authority):
    assert classify_symbol_only("ALIASCOLL", authority)[0] == "AMBIGUOUS_ALIAS_MULTIPLE_TARGETS"


def test_withdrawn_single_merge_resolves(authority):
    assert classify_symbol_only("WITHDRAWN1", authority)[:2] == ("EXACT_HGNC_WITHDRAWN_SINGLE_MERGE_RECOVERED", eid(1))


def test_withdrawn_split_is_ambiguous(authority):
    assert classify_symbol_only("SPLIT", authority)[0] == "AMBIGUOUS_HGNC_SPLIT"


def test_unique_ensembl_symbol_recovers_non_hgnc(authority):
    assert classify_symbol_only("NONHGNC", authority)[:2] == ("EXACT_ENSEMBL_CURRENT_SYMBOL_RECOVERED", eid(3))


def test_source_exact_ensembl_outranks_changed_modern_symbol(authority):
    result = adjudicate_row(row("CUR", eid(2), "exact_source_ensembl_symbol_pair"), authority, {}, set())
    assert result["terminal_disposition"] == "EXACT_CURRENT_ENSEMBL"
    assert result["authority_current_ensembl_id"] == eid(2)
    assert result["symbol_status"] == "source_symbol_differs_from_current"


@pytest.mark.parametrize("symbol", ["cur", "CUR-", " CUR X "])
def test_no_fuzzy_case_or_punctuation_mapping(authority, symbol):
    assert classify_symbol_only(symbol, authority)[0] == "SYMBOL_ONLY_UNRESOLVED"


def test_no_biotype_filter_for_lncRNA(authority):
    status, stable_id, _ = classify_symbol_only("NONHGNC", authority)
    assert status in EXACT_TERMINAL and authority.ensembl_by_id[stable_id].biotype == "lncRNA"


def test_pseudogene_remains_eligible(authority):
    status, stable_id, _ = classify_symbol_only("PSEUDO", authority)
    assert status in EXACT_TERMINAL and broad_biotype(authority.ensembl_by_id[stable_id], None) == "pseudogene"


def test_every_source_row_receives_one_terminal_disposition(authority):
    results = [adjudicate_row(row(symbol), authority, {}, set()) for symbol in ("CUR", "PREV1", "UNKNOWN")]
    assert all(item["terminal_disposition"] for item in results) and len(results) == 3


def unresolved_row(**updates):
    values = {
        "dataset_id": "TEST", "matrix_id": "source.tsv", "raw_feature_id": "UNKNOWN",
        "raw_gene_symbol": "UNKNOWN", "source_ensembl_id": "", "source_ncbi_gene_id": "",
        "source_refseq_id": "", "source_transcript_id": "", "source_chromosome": "",
        "source_start": "", "source_end": "", "source_strand": "", "source_biotype": "",
        "source_annotation_authority": "", "terminal_disposition": "SYMBOL_ONLY_UNRESOLVED",
        "modality": "gene-level RNA",
    }
    values.update(updates)
    return pd.Series(values)


def test_unresolved_exact_ncbi_recovery(authority):
    result = classify_one(
        unresolved_row(source_ncbi_gene_id="123"), authority, {},
        {"ncbi": {"123": eid(1)}, "refseq": {}, "mirbase_gene": {}}, {}, {},
    )
    assert result["new_terminal_disposition"] == "EXACT_NCBI_GENE_RECOVERED"
    assert result["recovered_canonical_ensembl_id"] == eid(1)
    assert result["automatic_fix_safe"]


def test_unresolved_exact_ncbi_without_current_projection_is_preserved(authority):
    result = classify_one(
        unresolved_row(source_ncbi_gene_id="999999"), authority, {},
        {"ncbi": {}, "refseq": {}, "mirbase_gene": {}}, {}, {},
    )
    assert result["new_terminal_disposition"] == "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED"
    assert result["mapping_evidence_class"] == "EXACT_NCBI_GENE"
    assert not result["recovered_canonical_ensembl_id"]


def test_unresolved_exact_refseq_recovery_strips_accession_version(authority):
    result = classify_one(
        unresolved_row(source_refseq_id="NM_000001.4"), authority, {},
        {"ncbi": {}, "refseq": {"NM_000001": eid(2)}, "mirbase_gene": {}}, {}, {},
    )
    assert result["new_terminal_disposition"] == "EXACT_REFSEQ_RECOVERED"
    assert result["recovered_canonical_ensembl_id"] == eid(2)


def test_unresolved_source_mirbase_is_preserved_without_gene_projection(authority):
    result = classify_one(
        unresolved_row(dataset_id="GSE305625", modality="miRNA"), authority, {},
        {"ncbi": {}, "refseq": {}, "mirbase_gene": {}}, {},
        {"source_mirbase_id": "MIMAT0000280", "source_symbol_raw": "hsa-miR-223-3p"},
    )
    assert result["new_terminal_disposition"] == "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED"
    assert not result["recovered_canonical_ensembl_id"]


def test_unresolved_symbol_without_exact_anchor_stays_unresolved(authority):
    result = classify_one(
        unresolved_row(), authority, {},
        {"ncbi": {}, "refseq": {}, "mirbase_gene": {}}, {}, {},
    )
    assert result["new_terminal_disposition"] == "TRULY_SYMBOL_ONLY_UNRESOLVED"
    assert not result["automatic_fix_safe"]


def test_source_local_exact_anchor_recovers_without_symbol_guessing(authority):
    result = classify_one(
        unresolved_row(dataset_id="SOURCE", raw_feature_id="OLD_SOURCE_NAME", raw_gene_symbol="OLD_SOURCE_NAME"),
        authority, {}, {"ncbi": {}, "refseq": {}, "mirbase_gene": {}},
        {("SOURCE", "OLD_SOURCE_NAME"): eid(2)}, {},
    )
    assert result["new_terminal_disposition"] == "SOURCE_ERA_EXACT_RECOVERED"
    assert result["recovered_canonical_ensembl_id"] == eid(2)


def test_featurecounts_numeric_value_is_not_used_as_gene_symbol(authority):
    result = classify_one(
        unresolved_row(dataset_id="GSE240609", raw_feature_id="CUR", raw_gene_symbol="42864"),
        authority, {}, {"ncbi": {}, "refseq": {}, "mirbase_gene": {}}, {}, {},
    )
    assert result["new_terminal_disposition"] == "CURRENT_ENSEMBL_RECOVERED"
    assert result["source_symbol_raw"] == "CUR"


def test_duplicate_alternative_authority_key_is_not_auto_mapped():
    assert unique_map([("123", eid(1)), ("123", eid(2))]) == {}


@pytest.mark.parametrize("value", ["", "NA", "N/A", "nan", "None", "NULL", "."])
def test_closure_missing_tokens_are_not_exact_anchors(value):
    assert not present(value)
    assert not valid_ensembl(value)
    assert not valid_ncbi(value)


def test_closure_exact_anchor_validators_are_strict():
    assert valid_ensembl(eid(1) + ".4")
    assert valid_ncbi("79104")
    assert not valid_ncbi("MEG8")
    assert evidence_hash({"b": 2, "a": 1}) == evidence_hash({"a": 1, "b": 2})


def test_closure_final_dossier_preserves_rows_and_resolves_case():
    dossier = pd.DataFrame([{
        "previous_canonical_ensembl_id": eid(1),
        "frozen_symbols": "GENE",
        "protected_identity_decision": "HUMAN_A2R_IDENTITY_REVIEW",
        "protected_identity_evidence": "prior evidence",
        "history_transition_types": "",
        "remaining_human_blocker": "True",
    }])
    decisions = pd.DataFrame([{
        "case_id": f"GENE_{eid(1)}",
        "decision": "KEEP_FROZEN_HISTORICAL_ID",
        "decision_reason": "ambiguous history is preserved",
        "history_topology": "many_to_one_possible_replacement",
        "same_biological_gene": "not_proven",
        "canonical_identity_correction_required": False,
        "human_blocker_remaining": False,
        "review_evidence_hash": "abc",
    }])
    result = finalize_dossier(dossier, decisions)
    assert len(result) == len(dossier)
    assert result.iloc[0].final_a2r_decision == "KEEP_FROZEN_HISTORICAL_ID"
    assert not bool(result.iloc[0].human_blocker_remaining)


def test_protected_alt_locus_keeps_frozen_identity(tmp_path):
    hgnc = tmp_path / "hgnc.tsv"
    pd.DataFrame([{
        "symbol": "ATF6B", "ensembl_gene_id": eid(1), "entrez_id": "1388",
    }]).to_csv(hgnc, sep="\t", index=False)
    dossier = pd.DataFrame([{
        "previous_canonical_ensembl_id": eid(1), "authoritative_canonical_ensembl_id": "",
        "frozen_symbols": "ATF6B", "source_exact_ensembl_ids": eid(99),
        "identity_change_classification": "SYMBOL_ONLY",
        "supporting_source_chromosomes": "CHR_HSCHR6_MHC_DBB_CTG1",
        "supporting_ncbi_gene_ids": "1388", "required_action": "HUMAN_A2R_IDENTITY_REVIEW",
        "human_a2r_decision_required": "True",
    }])
    result = adjudicate_protected_dossier(dossier, hgnc).iloc[0]
    assert result.protected_identity_decision == "KEEP_FROZEN_ALT_LOCUS_SOURCE_ALIAS"
    assert result.identity_change_classification == "SOURCE_EXACT_ALT_LOCUS_SAME_GENE"
    assert not bool(result.remaining_human_blocker)


def test_protected_different_source_id_without_shared_anchor_remains_blocked(tmp_path):
    hgnc = tmp_path / "hgnc.tsv"
    pd.DataFrame([{
        "symbol": "ATF6B", "ensembl_gene_id": eid(1), "entrez_id": "1388",
    }]).to_csv(hgnc, sep="\t", index=False)
    dossier = pd.DataFrame([{
        "previous_canonical_ensembl_id": eid(1), "authoritative_canonical_ensembl_id": "",
        "frozen_symbols": "ATF6B", "source_exact_ensembl_ids": eid(99),
        "identity_change_classification": "SYMBOL_ONLY", "supporting_source_chromosomes": "CHR_HSCHR6_ALT",
        "supporting_ncbi_gene_ids": "999", "required_action": "HUMAN_A2R_IDENTITY_REVIEW",
        "human_a2r_decision_required": "True",
    }])
    result = adjudicate_protected_dossier(dossier, hgnc).iloc[0]
    assert result.protected_identity_decision == "HUMAN_A2R_IDENTITY_REVIEW"
    assert str(result.remaining_human_blocker).lower() == "true"


def test_support_recovery_only_is_distinguished(authority):
    result = adjudicate_row(row("CUR"), authority, {}, {eid(1)})
    assert result["recovery_type"] == "SUPPORT_RECOVERY_ONLY"


def test_new_gene_recovery_is_distinguished(authority):
    result = adjudicate_row(row("NEW"), authority, {}, {eid(1)})
    assert result["recovery_type"] == "NEW_CANONICAL_GENE_RECOVERY"


def test_same_matrix_collisions_are_detected_without_merge():
    decisions = pd.DataFrame([
        {"source_dataset_id": "S", "authority_current_ensembl_id": eid(1), "terminal_disposition": "EXACT_CURRENT_ENSEMBL", "canonical_ensembl_gene_id": eid(1), "source_feature_index": "1", "raw_source_feature_symbol": "A", "raw_source_feature_id": "1"},
        {"source_dataset_id": "S", "authority_current_ensembl_id": eid(1), "terminal_disposition": "EXACT_HGNC_ALIAS_RECOVERED", "canonical_ensembl_gene_id": "", "source_feature_index": "2", "raw_source_feature_symbol": "B", "raw_source_feature_id": "2"},
    ])
    collisions = build_collisions(decisions, pd.DataFrame([{"matrix_id": "M", "source_dataset_id": "S"}]))
    assert len(collisions) == 1 and collisions.iloc[0].colliding_row_count == 2


def test_measurement_preserves_zero_unmeasured_semantics():
    decisions = pd.DataFrame([{"source_dataset_id": "S", "authority_current_ensembl_id": eid(1), "terminal_disposition": "EXACT_CURRENT_ENSEMBL"}])
    registry = pd.DataFrame([{"successor_gene_index": 0, "canonical_ensembl_gene_id": eid(1), "canonical_symbol": "A"}, {"successor_gene_index": 1, "canonical_ensembl_gene_id": eid(2), "canonical_symbol": "B"}])
    support = build_measurement(decisions, registry, pd.DataFrame([{"matrix_id": "M", "source_dataset_id": "S"}]))
    assert support.measured_gene.tolist() == [True, False]
    assert support.measured_zero_distinct_from_unmeasured.all()


def test_registry_is_not_constrained_to_historical_count(authority):
    decisions = pd.DataFrame([
        {"terminal_disposition": "EXACT_CURRENT_ENSEMBL", "authority_current_ensembl_id": eid(1), "source_dataset_id": "HVS_COMMON"},
        {"terminal_disposition": "EXACT_ENSEMBL_CURRENT_SYMBOL_RECOVERED", "authority_current_ensembl_id": eid(3), "source_dataset_id": "NPH52::X"},
    ])
    registry, _ = build_exact_registry(decisions, authority, {eid(1)})
    assert len(registry) == 2 and registry.new_relative_to_prior_37346.sum() == 1


def test_unobserved_ensembl_genes_are_not_added(authority):
    decisions = pd.DataFrame([{"terminal_disposition": "EXACT_CURRENT_ENSEMBL", "authority_current_ensembl_id": eid(1), "source_dataset_id": "HVS_COMMON"}])
    registry, _ = build_exact_registry(decisions, authority, set())
    assert set(registry.canonical_ensembl_gene_id) == {eid(1)}


def test_history_replacements_require_current_ids(authority):
    response = {"latest": f"{eid(100)}.2", "possible_replacement": [{"stable_id": eid(2)}, {"stable_id": eid(200)}]}
    assert history_current_replacements(response, set(authority.ensembl_by_id)) == (eid(2),)


@pytest.mark.parametrize("source,expected", [("HVS_COMMON", "HVS"), ("SEA_AD_COMMON", "SEA_AD"), ("NPH52::X", "NPH52")])
def test_source_family_is_exact(source, expected):
    assert source_family(source) == expected


def test_future_atac_peak_is_not_forced_through_ensembl(authority):
    features = pd.DataFrame([{
        "dataset_id": "ATAC", "study_id": "ATAC", "matrix_id": "peaks.h5ad",
        "modality": "ATAC/chromatin", "intended_role": "adapter", "pathology_bearing": False,
        "source_feature_index": "0", "raw_feature_id": eid(1), "raw_gene_symbol": "CUR",
        "source_ensembl_id": eid(1), "source_feature_type": "ATAC peak",
    }])
    audited = adjudicate_features(features, authority, {}, {eid(1)})
    assert audited.iloc[0].terminal_disposition == "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED"
    assert audited.iloc[0].foundation_compatibility == "SOURCE_NATIVE_FUTURE_ONLY_FEATURE"


def test_future_spatial_rna_uses_gene_authority_without_expanding_foundation(authority):
    features = pd.DataFrame([{
        "dataset_id": "SPATIAL", "study_id": "SPATIAL", "matrix_id": "spatial.h5ad",
        "modality": "spatial RNA", "intended_role": "context", "pathology_bearing": False,
        "source_feature_index": "0", "raw_feature_id": eid(2), "raw_gene_symbol": "NEW",
        "source_ensembl_id": eid(2), "source_feature_type": "Gene Expression",
    }])
    audited = adjudicate_features(features, authority, {}, {eid(1)})
    assert audited.iloc[0].terminal_disposition == "EXACT_CURRENT_ENSEMBL"
    assert audited.iloc[0].foundation_compatibility == "EXACT_FUTURE_ONLY_GENE"


def test_future_collision_summary_preserves_duplicate_rows(authority):
    common = {
        "dataset_id": "RNA", "study_id": "RNA", "matrix_id": "rna.csv",
        "modality": "gene-level RNA", "intended_role": "holdout", "pathology_bearing": True,
        "source_ensembl_id": eid(1), "source_feature_type": "Gene Expression",
    }
    features = pd.DataFrame([
        {**common, "source_feature_index": "0", "raw_feature_id": eid(1), "raw_gene_symbol": "CUR"},
        {**common, "source_feature_index": "1", "raw_feature_id": "CUR", "raw_gene_symbol": "CUR"},
    ])
    audited = adjudicate_features(features, authority, {}, {eid(1)})
    inventory = pd.DataFrame([{"dataset_id": "RNA", "modality": "gene-level RNA", "intended_project_role": "holdout"}])
    provenance = pd.DataFrame([{"dataset_id": "RNA", "genome_assembly": "GRCh38", "annotation_release": "unknown"}])
    compatibility, collisions = summarize(audited, inventory, provenance, {eid(1)})
    assert len(audited) == 2 and len(collisions) == 1
    assert compatibility.iloc[0].status == "MATERIALIZATION POLICY NEEDED"


def test_matrix_text_feature_reader_handles_headerless_input(tmp_path):
    path = tmp_path / "counts.csv"
    path.write_text("CUR,1,2\nNEW,3,4\n", encoding="utf-8")
    assert [row["raw_feature_id"] for row in matrix_text_features(path)] == ["CUR", "NEW"]


def test_sparse_coordinate_payload_is_not_a_feature_axis(tmp_path):
    path = tmp_path / "matrix.csv"
    path.write_text("row,col,value\n1,1,2\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="sparse coordinate"):
        matrix_text_features(path)


def test_observation_metadata_named_features_is_rejected():
    with pytest.raises(RuntimeError, match="observation metadata"):
        feature_lines(iter(["name,global.x,cluster_L1\n", "cell_1,1.0,EXC\n"]), ",")


@pytest.mark.parametrize(
    "matrix_id,expected",
    [
        ("data/external/v4/sea_ad/mtg/SEAAD_MTG_RNAseq.h5ad", "SEA_AD"),
        ("data/external/v4/living_human/hvs/part.h5ad", "HVS"),
        ("data/processed/v4/stage81a1d/sealed/nph52_organized/MG.qs", "NPH52"),
        ("data/external/v4/perturbation/GSE301119/GSE301119_RAW.tar::features.tsv.gz", "GSE301119"),
    ],
)
def test_matrix_paths_normalize_to_scientific_dataset(matrix_id, expected):
    assert dataset_id_from_matrix(matrix_id) == expected


@pytest.mark.parametrize(
    "name,dataset,role,expected",
    [
        ("matrix.h5", "GSE226267", "scATAC adapter", "ATAC/chromatin"),
        ("matrix.csv", "GSE305625", "validation", "miRNA"),
        ("protein.csv", "CITE", "antibody validation", "protein/antibody"),
        ("visium.h5ad", "SPATIAL", "context", "spatial RNA"),
    ],
)
def test_modality_is_classified_before_identity_audit(name, dataset, role, expected):
    assert modality(Path(name), dataset, role) == expected


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"raw_id": "NR_12345.2", "feature_type": "Gene Expression", "refseq_id": "NR_12345.2"}, "EXACT_REFSEQ_OR_NCBI_GENE"),
        ({"raw_id": "ENST00000123456.3", "feature_type": "transcript", "annotation_authority": "GENCODE v19"}, "EXACT_GENCODE_LEGACY"),
        ({"raw_id": "chr1:10-20", "feature_type": "ATAC peak"}, "SOURCE_NATIVE_GENOMIC_LOCUS"),
        ({"raw_id": "guide_1", "feature_type": "CRISPR Guide Capture"}, "NON_BIOLOGICAL_TECHNICAL_FEATURE"),
        ({"raw_id": "AC092295.4", "symbol": "AC092295.4", "feature_type": "Gene Expression"}, "SYMBOL_ONLY_UNRESOLVED"),
    ],
)
def test_source_native_terminal_taxonomy(kwargs, expected):
    assert classify_source_native_feature(**kwargs)[0] == expected


def test_source_native_merge_keys_are_not_overwritten(authority):
    source = pd.DataFrame([{
        "source_feature_id": "10", "source_feature_symbol": "CUR",
        "source_feature_type": "Gene Expression", "source_genome_build_or_annotation": "GRCh38",
        "canonical_ensembl_gene_id": eid(1), "mapping_method": "unresolved_exact_symbol",
        "mapping_decision": "AMBIGUOUS_UNRESOLVED", "source_dataset_id": "NPH52::X",
        "source_exact_ensembl_id": eid(1), "source_identity_evidence_file": "X.qs",
        "source_refseq_id": "", "source_ncbi_gene_id": "1", "source_transcript_id": "",
        "source_chromosome": "1", "source_start": "1", "source_end": "10",
        "source_strand": "+", "source_biotype": "protein_coding",
    }])
    decisions = build_decisions(source, authority, {}, set())
    assert decisions.iloc[0].authority_current_ensembl_id == eid(1)
    assert decisions.iloc[0].mapping_evidence_class == "SOURCE_EXACT"
    assert decisions.iloc[0].source_ncbi_gene_id == "1"


def test_review_package_semantic_hash_is_order_sensitive():
    assert semantic_hash([eid(1), eid(2)]) != semantic_hash([eid(2), eid(1)])


def test_review_package_history_classification_is_conservative():
    same = pd.Series({
        "previous_canonical_ensembl_id": eid(1),
        "authoritative_canonical_ensembl_id": eid(1),
        "terminal_disposition": "EXACT_CURRENT_ENSEMBL",
        "mapping_evidence_class": "SOURCE_EXACT",
    })
    changed = same.copy()
    changed["authoritative_canonical_ensembl_id"] = eid(2)
    assert history_relation(same) == ("STRONGER_EVIDENCE_SAME_CANONICAL", True)
    assert history_relation(changed) == ("GENUINE_CANONICAL_ID_CORRECTION", False)


def test_foundation_reconciliation_ignores_future_exact_genes():
    authoritative = pd.DataFrame({"canonical_ensembl_gene_id": [eid(1)]})
    projectwide = pd.DataFrame([
        {
            "dataset_id": "NPH52", "matrix_id": "nph.qs", "raw_feature_id": "A",
            "raw_gene_symbol": "A", "source_ensembl_id": eid(1),
            "terminal_disposition": "EXACT_CURRENT_ENSEMBL", "mapping_evidence_class": "SOURCE_EXACT",
            "current_ensembl_gene_id": eid(1), "foundation_eligible": True,
        },
        {
            "dataset_id": "FUTURE", "matrix_id": "future.h5ad", "raw_feature_id": "B",
            "raw_gene_symbol": "B", "source_ensembl_id": eid(2),
            "terminal_disposition": "EXACT_CURRENT_ENSEMBL", "mapping_evidence_class": "SOURCE_EXACT",
            "current_ensembl_gene_id": eid(2), "foundation_eligible": False,
        },
    ])
    ledger, gates = build_foundation_reconciliation(authoritative, projectwide)
    assert ledger.empty
    assert gates["foundation_reconciliation_exact"]
    assert gates["foundation_future_counterfactual_members_identical"]


def test_nph_frozen_vocab_adjudication_retains_every_frozen_gene():
    vocabulary = pd.DataFrame({
        "vocabulary_index": [0, 1],
        "canonical_ensembl_gene_id": [eid(1), eid(2)],
        "canonical_hgnc_symbol": ["A", "B"],
    })
    decisions = pd.DataFrame([{
        "source_dataset_id": "NPH52::MG.qs",
        "authority_current_ensembl_id": eid(1),
        "mapping_evidence_class": "SOURCE_EXACT",
        "terminal_disposition": "EXACT_CURRENT_ENSEMBL",
        "source_exact_ensembl_id": eid(1),
    }])
    result = build_nph_frozen_vocab_adjudication(vocabulary, decisions, pd.DataFrame())
    assert len(result) == 2
    assert result.nph_source_row_count.tolist() == [1, 0]
    assert not result.frozen_vocabulary_rewrite_allowed.any()


def test_foundation_accounting_separates_rows_identities_and_address_policy():
    def identity_row(dataset, index, disposition, *, current="", legacy="", native="", symbol=""):
        return {
            "source_record_index": f"{dataset}:{index}",
            "source_dataset_id": dataset,
            "source_object_or_matrix": dataset,
            "source_feature_index": index,
            "terminal_disposition": disposition,
            "authority_current_ensembl_id": current,
            "source_native_id": native,
            "normalized_source_ensembl_id": legacy,
            "source_exact_ensembl_id": legacy,
            "source_refseq_id": "NM_000001" if disposition.startswith("EXACT_REFSEQ") else "",
            "source_ncbi_gene_id": "",
            "source_transcript_id": "",
            "normalized_source_symbol": symbol,
            "raw_source_feature_id": str(index),
            "raw_source_feature_symbol": symbol,
            "canonical_hgnc_symbol": symbol,
            "source_biotype": "test_biotype",
            "mapping_evidence_class": "TEST_EXACT",
            "mapping_authority": "completed_test_ledger",
            "mapping_evidence_file": "test-ledger.csv",
            "hgnc_approved_ensembl": "",
            "hgnc_previous_ensembl": "",
            "hgnc_alias_ensembl": "",
            "hgnc_withdrawn_ensembl": "",
        }

    decisions = pd.DataFrame([
        identity_row("SEA_AD_COMMON", 0, "EXACT_CURRENT_ENSEMBL", current=eid(1), symbol="A"),
        identity_row("SEA_AD_COMMON", 1, "LEGACY_EXACT_ENSEMBL_NO_CURRENT_REPLACEMENT", legacy=eid(10), symbol="OLD"),
        identity_row("SEA_AD_COMMON", 2, "EXACT_REFSEQ_OR_NCBI_GENE", symbol="REF"),
        identity_row("HVS_COMMON", 0, "EXACT_CURRENT_ENSEMBL", current=eid(1), symbol="A"),
        identity_row("HVS_COMMON", 1, "SOURCE_NATIVE_TRANSCRIPT_MODEL", native="HGNC:99", symbol="NATIVE"),
        identity_row("NPH52::A.qs", 0, "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED", symbol="LOCUS"),
        identity_row("NPH52::A.qs", 1, "AMBIGUOUS_ALIAS", symbol="AMB"),
        identity_row("NPH52::A.qs", 2, "TRULY_SYMBOL_ONLY_UNRESOLVED", symbol="POOR"),
        identity_row("NPH52::B.qs", 3, "TRULY_SYMBOL_ONLY_UNRESOLVED", symbol="POOR"),
        identity_row("NPH52::B.qs", 4, "NON_BIOLOGICAL_TECHNICAL_FEATURE", symbol="TECH"),
    ])
    reclassification = pd.DataFrame(columns=[
        "dataset", "matrix_id", "source_feature_index", "new_terminal_disposition",
        "recovered_canonical_ensembl_id",
    ])

    accounting, policy, summary, frame = foundation_identity_accounting(decisions, reclassification)

    assert summary["source_rows_total"] == 10
    assert summary["unique_source_features"] == 9
    assert summary["unique_biological_identities"] == 8
    assert set(summary["identity_layer_counts"].values()) == {1}
    nph = accounting.set_index("scope").loc["NPH52"]
    assert nph.foundation_source_rows_total == 5
    assert nph.foundation_unique_source_features == 4
    assert nph.foundation_unique_biological_identities == 4
    assert nph.G_foundation_symbol_or_identifier_poor == 1
    policy = policy.set_index("identity_layer")
    assert policy.loc["source_native_anchored", "molecular_evidence_preserved"] == "YES"
    assert policy.loc["source_native_anchored", "proposed_universal_encoder_eligibility"] == "ELIGIBLE"
    assert policy.loc["symbol_or_identifier_poor", "universal_identity_established"] == "NO"
    assert policy.loc["true_technical_nonbiological", "molecular_evidence_preserved"] == "NO"
    assert len(frame) == len(decisions)

    support = pd.DataFrame([
        {
            "matrix_id": "SEA_MATRIX", "source_dataset_id": "SEA_AD_COMMON",
            "successor_gene_index": 0, "canonical_ensembl_gene_id": eid(1),
            "canonical_symbol": "A", "measured_gene": True,
            "measurement_status": "addressable_measured_zero_or_nonzero_at_runtime",
            "measured_zero_distinct_from_unmeasured": True,
            "source_feature_universe_hash": "sea-hash",
        },
        {
            "matrix_id": "HVS_MATRIX", "source_dataset_id": "HVS_COMMON",
            "successor_gene_index": 0, "canonical_ensembl_gene_id": eid(1),
            "canonical_symbol": "A", "measured_gene": True,
            "measurement_status": "addressable_measured_zero_or_nonzero_at_runtime",
            "measured_zero_distinct_from_unmeasured": True,
            "source_feature_universe_hash": "hvs-hash",
        },
    ])
    registry, provenance, expanded, nonuniversal, injectivity = (
        build_foundation_molecular_address_package(
            frame,
            support,
            expected_address_counts={
                "current_exact": 1,
                "legacy_exact": 1,
                "source_native_anchored": 1,
            },
            expected_nonuniversal_count=3,
        )
    )
    assert registry.molecular_address_id.tolist() == [eid(1), eid(10), "HGNC:99"]
    assert len(provenance) == 4
    assert len(expanded) == 6
    assert not expanded.duplicated(["matrix_id", "molecular_address_id"]).any()
    assert len(nonuniversal) == 3
    assert injectivity["exact_cross_layer_duplicate_equivalence_classes"] == 0
    assert injectivity["final_distinct_universal_molecular_addresses"] == 3
    assert not injectivity["dataset_or_source_family_used_in_address_id"]

    shuffled = frame.sample(frac=1, random_state=7).reset_index(drop=True)
    registry_2, provenance_2, expanded_2, nonuniversal_2, injectivity_2 = (
        build_foundation_molecular_address_package(
            shuffled,
            support.sample(frac=1, random_state=7).reset_index(drop=True),
            expected_address_counts={
                "current_exact": 1,
                "legacy_exact": 1,
                "source_native_anchored": 1,
            },
            expected_nonuniversal_count=3,
        )
    )
    pd.testing.assert_frame_equal(registry, registry_2)
    pd.testing.assert_frame_equal(provenance, provenance_2)
    pd.testing.assert_frame_equal(expanded, expanded_2)
    pd.testing.assert_frame_equal(nonuniversal, nonuniversal_2)
    assert injectivity == injectivity_2


def test_matrix_accounting_reconciles_historical_aggregate_with_a2r_operators():
    assets = pd.DataFrame(
        [{"study_id": "HVS", "foundation_eligible": True}] * 24
        + [{"study_id": "SEA_AD", "foundation_eligible": True}] * 11
        + [{"study_id": "NPH52", "foundation_eligible": True}]
        + [{"study_id": "FUTURE", "foundation_eligible": False}]
    )
    support = pd.DataFrame(
        [{"matrix_id": f"HVS::{index}", "source_dataset_id": "HVS_COMMON"} for index in range(24)]
        + [{"matrix_id": f"SEA::{index}", "source_dataset_id": "SEA_AD_COMMON"} for index in range(11)]
        + [{"matrix_id": f"NPH::{index}", "source_dataset_id": f"NPH52::source-{index}.qs"} for index in range(7)]
    )
    result = matrix_accounting_reconciliation(assets, support)
    assert result["historical_stage81a2_asset_entry_total"] == 36
    assert result["current_stage81a2r_measurement_support_matrix_total"] == 42
    assert result["new_foundation_datasets_introduced"] == 0
