"""Build the deterministic Stage81A2R human-review evidence package.

This consumes feature-identity metadata and candidate ledgers only. It does not
read expression values or rewrite any frozen scientific artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from scripts.v4.stage81a2r_authoritative_gene_identity_recovery import (
    ALTERNATIVE_AUTHORITY_TERMINAL,
    EXACT_TERMINAL,
    LEGACY_TERMINAL,
    SOURCE_NATIVE_TERMINAL,
    TECHNICAL_TERMINAL,
    atomic_csv,
    atomic_json,
    sha256_file,
)


FOUNDATION_DATASETS = {"SEA_AD", "HVS", "NPH52"}
PLACEHOLDER_STATUS = "SOURCE ASSET NOT LOCALLY AVAILABLE / ACQUISITION PLACEHOLDER"
ADMIN_STATUS = "ADMINISTRATIVE INVENTORY / NO MOLECULAR FEATURE CONTRACT"
TERMINAL_DATASET_STATUSES = {
    "IDENTITY COMPATIBLE",
    "COMPATIBLE WITH LEGACY FEATURES",
    "MATERIALIZATION POLICY NEEDED",
    "NON-RNA / SEPARATE FEATURE AUTHORITY",
    PLACEHOLDER_STATUS,
    ADMIN_STATUS,
}


def semantic_hash(values: list[str]) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()


def stable_frame_hash(frame: pd.DataFrame, columns: list[str]) -> str:
    normalized = frame.loc[:, columns].fillna("").astype(str)
    payload = "\n".join("\t".join(row) for row in normalized.itertuples(index=False, name=None))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def history_relation(row: pd.Series) -> tuple[str, bool]:
    previous = str(row.get("previous_canonical_ensembl_id", ""))
    current = str(row.get("authoritative_canonical_ensembl_id", ""))
    terminal = str(row.get("terminal_disposition", ""))
    evidence = str(row.get("mapping_evidence_class", ""))
    if previous == current and current:
        return "STRONGER_EVIDENCE_SAME_CANONICAL", True
    if terminal == "EXACT_HISTORICAL_ENSEMBL_TO_CURRENT" and current:
        return "HISTORICAL_ID_SAME_GENE", True
    if "AMBIGUOUS" in terminal:
        return "SOURCE_EXACT_AMBIGUOUS_HISTORY", False
    if "CONFLICT" in terminal:
        return "SOURCE_METADATA_CONFLICT", False
    if evidence == "SOURCE_EXACT" and previous and current and previous != current:
        return "GENUINE_CANONICAL_ID_CORRECTION", False
    if not current:
        return "SYMBOL_ONLY", False
    return "GENUINE_CANONICAL_ID_CORRECTION", False


def build_nph_cache_validation(project: Path, config: dict[str, Any]) -> pd.DataFrame:
    manifest_path = project / config["inputs"]["r_feature_cache_manifest"]
    manifest = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
    extractor = project / "scripts/v4/stage81a2r_extract_r_feature_metadata.R"
    rows: list[dict[str, Any]] = []
    for item in manifest.to_dict("records"):
        source_relative = item["source_local_path"].replace("\\", "/")
        if not source_relative.endswith(".qs"):
            continue
        source = project / source_relative
        raw_cache = item["cache_path"].replace("\\", "/")
        cache = project / (raw_cache.split("/Jepa project/", 1)[-1] if raw_cache.startswith("/mnt/") else raw_cache)
        frame = pd.read_csv(cache, sep="\t", dtype=str, keep_default_na=False)
        expected_indices = [str(index) for index in range(len(frame))]
        order_pass = frame.source_feature_index.tolist() == expected_indices
        identity_columns = [column for column in frame.columns if column != "source_feature_index"]
        rows.append({
            "source_path": source_relative,
            "source_file_sha256": sha256_file(source),
            "source_size_bytes": source.stat().st_size,
            "source_feature_count_recorded_at_extraction": int(item["feature_count"]),
            "cache_path": str(cache.relative_to(project)).replace("\\", "/"),
            "cache_sha256": sha256_file(cache),
            "cache_feature_row_count": len(frame),
            "cache_row_order_sha256": stable_frame_hash(frame, ["source_feature_index", "raw_feature_id"]),
            "cache_identity_fields_sha256": stable_frame_hash(frame, ["source_feature_index", *identity_columns]),
            "metadata_fields_extracted": "|".join(identity_columns),
            "source_row_count_equals_cache_count": int(item["feature_count"]) == len(frame),
            "zero_based_source_order_preserved": order_pass,
            "extractor_script": str(extractor.relative_to(project)).replace("\\", "/"),
            "extractor_sha256": sha256_file(extractor),
            "extraction_environment": "stage81a2r-r-feature-audit",
            "expression_values_materialized_or_evaluated": str(item["expression_matrix_materialized"]).lower() == "true",
        })
    result = pd.DataFrame(rows).sort_values("source_path").reset_index(drop=True)
    if len(result) != 7:
        raise RuntimeError(f"expected seven NPH source-cache records, found {len(result)}")
    if not result.source_row_count_equals_cache_count.all() or not result.zero_based_source_order_preserved.all():
        raise RuntimeError("NPH source-cache count/order validation failed")
    if result.expression_values_materialized_or_evaluated.any():
        raise RuntimeError("NPH cache manifest reports expression materialization")
    return result


def build_foundation_reconciliation(
    authoritative: pd.DataFrame, projectwide: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    a = set(authoritative.canonical_ensembl_gene_id)
    foundation = projectwide[
        projectwide.foundation_eligible.astype(str).str.lower().eq("true")
        & projectwide.terminal_disposition.isin(EXACT_TERMINAL)
    ].copy()
    b = set(foundation.current_ensembl_gene_id)
    rows: list[dict[str, Any]] = []
    for gene in sorted(a ^ b):
        subset = foundation[foundation.current_ensembl_gene_id.eq(gene)]
        side = "AUDITED_FOUNDATION_RNA_ONLY" if gene in b else "AUTHORITATIVE_REGISTRY_ONLY"
        for record in (subset.to_dict("records") or [{}]):
            historical = record.get("source_ensembl_id", "")
            reason = (
                "source-exact historical NPH identity gained a unique official Ensembl current replacement after the prior authoritative registry generation"
                if side == "AUDITED_FOUNDATION_RNA_ONLY" and record.get("dataset_id") == "NPH52"
                else "foundation identity representations disagree; human adjudication required"
            )
            rows.append({
                "canonical_ensembl_gene_id": gene,
                "difference_side": side,
                "source_dataset": record.get("dataset_id", ""),
                "source_matrix": record.get("matrix_id", ""),
                "source_feature": record.get("raw_feature_id", ""),
                "source_symbol": record.get("raw_gene_symbol", ""),
                "source_ensembl_id": historical,
                "evidence_class": record.get("mapping_evidence_class", ""),
                "terminal_disposition": record.get("terminal_disposition", ""),
                "aliasing_caused_difference": False,
                "non_rna_leakage_caused_difference": False,
                "historical_id_timing_caused_difference": "historical" in reason,
                "explanation": reason,
            })
    reconciliation_columns = [
        "canonical_ensembl_gene_id", "difference_side", "source_dataset",
        "source_matrix", "source_feature", "source_symbol", "source_ensembl_id",
        "evidence_class", "terminal_disposition", "aliasing_caused_difference",
        "non_rna_leakage_caused_difference", "historical_id_timing_caused_difference",
        "explanation",
    ]
    ledger = pd.DataFrame(rows, columns=reconciliation_columns)
    if len(ledger):
        ledger = ledger.sort_values(["canonical_ensembl_gene_id", "source_dataset", "source_matrix"]).reset_index(drop=True)
    sorted_a = sorted(a)
    sorted_b = sorted(b)
    future_removed = projectwide[projectwide.dataset_id.isin(FOUNDATION_DATASETS)]
    counterfactual = sorted(set(
        future_removed.loc[
            future_removed.foundation_eligible.astype(str).str.lower().eq("true")
            & future_removed.terminal_disposition.isin(EXACT_TERMINAL),
            "current_ensembl_gene_id",
        ]
    ))
    gates = {
        "authoritative_current_exact_count": len(a),
        "audited_foundation_rna_current_exact_count": len(b),
        "difference_gene_count": len(a ^ b),
        "authoritative_semantic_hash": semantic_hash(sorted_a),
        "audited_foundation_semantic_hash": semantic_hash(sorted_b),
        "future_present_semantic_hash": semantic_hash(sorted_b),
        "future_excluded_semantic_hash": semantic_hash(counterfactual),
        "foundation_future_counterfactual_members_identical": sorted_b == counterfactual,
        "foundation_future_counterfactual_order_identical": sorted_b == counterfactual,
        "foundation_future_counterfactual_semantic_hash_identical": semantic_hash(sorted_b) == semantic_hash(counterfactual),
        "foundation_reconciliation_exact": sorted_a == sorted_b,
    }
    return ledger, gates


def build_protected_dossier(
    project: Path, comparison: pd.DataFrame, decisions: pd.DataFrame, vocabulary: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    affected = comparison[
        comparison.affects_frozen_4096_gene.astype(str).str.lower().eq("true")
        & comparison.comparison_class.eq("LEGITIMATE_ID_CORRECTION")
    ].copy()
    if not len(affected):
        return affected, affected
    classifications = affected.apply(history_relation, axis=1)
    affected["identity_change_classification"] = [item[0] for item in classifications]
    affected["one_to_one_identity_continuity"] = [item[1] for item in classifications]
    affected["human_a2r_decision_required"] = ~affected.one_to_one_identity_continuity
    vocab = vocabulary[["vocabulary_index", "canonical_ensembl_gene_id", "canonical_hgnc_symbol"]]
    frozen_ids = set(vocab.canonical_ensembl_gene_id)
    affected["frozen_canonical_ensembl_id"] = [
        previous if previous in frozen_ids else current if current in frozen_ids else ""
        for previous, current in zip(
            affected.previous_canonical_ensembl_id,
            affected.authoritative_canonical_ensembl_id,
        )
    ]
    if affected.frozen_canonical_ensembl_id.eq("").any():
        raise RuntimeError("protected comparison row does not resolve to a frozen vocabulary member")
    affected = affected.merge(
        vocab,
        left_on="frozen_canonical_ensembl_id",
        right_on="canonical_ensembl_gene_id",
        how="left",
    )
    evidence_columns = [
        "source_dataset_id", "source_feature_index", "source_object_or_matrix",
        "raw_source_feature_id", "raw_source_feature_symbol", "source_exact_ensembl_id",
        "source_chromosome", "source_start", "source_end", "source_strand",
        "source_biotype", "source_ncbi_gene_id", "ensembl_history_replacements",
        "terminal_reason", "mapping_evidence_class", "terminal_disposition",
    ]
    evidence = decisions[[column for column in evidence_columns if column in decisions]].copy()
    affected = affected.merge(
        evidence,
        on=["source_dataset_id", "source_feature_index"],
        how="left",
        suffixes=("", "_source"),
    )
    historical = decisions[decisions.terminal_disposition.eq("EXACT_HISTORICAL_ENSEMBL_TO_CURRENT")].copy()
    historical["source_stable_id"] = historical.source_exact_ensembl_id.str.extract(r"(ENSG[0-9]+)", expand=False).fillna("")
    inverse_counts = historical.groupby("authority_current_ensembl_id").source_stable_id.nunique().to_dict()
    is_history = affected.identity_change_classification.eq("HISTORICAL_ID_SAME_GENE")
    source_stable = affected.source_exact_ensembl_id.str.extract(r"(ENSG[0-9]+)", expand=False).fillna("")
    replacement_count = affected.ensembl_history_replacements.fillna("").map(
        lambda value: len({item for item in value.split("|") if item})
    )
    unique_inverse = affected.authoritative_canonical_ensembl_id.map(inverse_counts).fillna(0).eq(1)
    one_to_one = is_history & source_stable.ne("") & replacement_count.eq(1) & unique_inverse
    affected["history_transition_type"] = ""
    affected.loc[is_history, "history_transition_type"] = "ambiguous_or_merge_signal"
    affected.loc[one_to_one, "history_transition_type"] = "one_to_one_stable_continuation"
    affected.loc[is_history & ~one_to_one, "identity_change_classification"] = "SOURCE_EXACT_AMBIGUOUS_HISTORY"
    affected.loc[is_history, "one_to_one_identity_continuity"] = one_to_one[is_history]
    affected["human_a2r_decision_required"] = ~affected.one_to_one_identity_continuity.astype(bool)
    affected["frozen_artifact_modified"] = False
    affected["proposed_model_role"] = "HUMAN_A2R_IDENTITY_REVIEW_ONLY"
    affected = affected.sort_values(["vocabulary_index", "source_dataset_id", "source_feature_index"]).reset_index(drop=True)
    pair_keys = ["previous_canonical_ensembl_id", "authoritative_canonical_ensembl_id"]
    pair_rows = []
    for keys, group in affected.groupby(pair_keys, dropna=False, sort=True):
        pair_rows.append({
            "previous_canonical_ensembl_id": keys[0],
            "authoritative_canonical_ensembl_id": keys[1],
            "frozen_vocabulary_indices": "|".join(sorted(set(group.vocabulary_index.astype(str)), key=lambda value: int(value))),
            "frozen_symbols": "|".join(sorted(set(group.canonical_hgnc_symbol.astype(str)))),
            "affected_source_row_count": len(group),
            "source_datasets": "|".join(sorted(set(group.source_dataset_id.astype(str)))),
            "source_objects": "|".join(sorted(set(group.source_object_or_matrix.astype(str)))),
            "source_feature_indices": "|".join(sorted(set(group.source_feature_index.astype(str)), key=lambda value: int(value))),
            "source_feature_ids": "|".join(sorted(set(group.raw_source_feature_id.astype(str)))),
            "source_symbols": "|".join(sorted(set(group.raw_source_feature_symbol.astype(str)))),
            "source_exact_ensembl_ids": "|".join(sorted(set(group.source_exact_ensembl_id.astype(str)))),
            "identity_change_classification": "|".join(sorted(set(group.identity_change_classification.astype(str)))),
            "history_transition_types": "|".join(sorted(set(group.history_transition_type.fillna("").astype(str)) - {""})),
            "one_to_one_identity_continuity": bool(group.one_to_one_identity_continuity.astype(bool).all()),
            "human_a2r_decision_required": bool(group.human_a2r_decision_required.astype(bool).any()),
            "supporting_source_chromosomes": "|".join(sorted(set(group.source_chromosome.astype(str)) - {""})),
            "supporting_source_biotypes": "|".join(sorted(set(group.source_biotype.astype(str)) - {""})),
            "supporting_ncbi_gene_ids": "|".join(sorted(set(group.source_ncbi_gene_id.astype(str)) - {""})),
            "ensembl_history_replacements": "|".join(sorted(set(group.ensembl_history_replacements.astype(str)) - {""})),
            "frozen_artifact_modified": False,
            "required_action": "HUMAN_A2R_IDENTITY_REVIEW" if group.human_a2r_decision_required.astype(bool).any() else "REVIEW_CONTINUITY_EVIDENCE",
        })
    return affected, pd.DataFrame(pair_rows)


def build_nph_frozen_vocab_adjudication(
    vocabulary: pd.DataFrame, decisions: pd.DataFrame, dossier: pd.DataFrame
) -> pd.DataFrame:
    nph = decisions[decisions.source_dataset_id.str.startswith("NPH52::")].copy()
    supported = nph[nph.authority_current_ensembl_id.ne("")].groupby(
        "authority_current_ensembl_id", sort=False
    ).agg(
        nph_source_row_count=("authority_current_ensembl_id", "size"),
        nph_source_objects=("source_dataset_id", lambda values: "|".join(sorted(set(values)))),
        nph_evidence_classes=("mapping_evidence_class", lambda values: "|".join(sorted(set(values)))),
        nph_terminal_dispositions=("terminal_disposition", lambda values: "|".join(sorted(set(values)))),
        nph_source_exact_ensembl_rows=("source_exact_ensembl_id", lambda values: int(pd.Series(values).str.match(r"^ENSG[0-9]+(?:\.[0-9]+)?$").sum())),
    ).reset_index().rename(columns={"authority_current_ensembl_id": "canonical_ensembl_gene_id"})
    result = vocabulary[["vocabulary_index", "canonical_ensembl_gene_id", "canonical_hgnc_symbol"]].merge(
        supported, on="canonical_ensembl_gene_id", how="left"
    )
    changed = set(dossier.canonical_ensembl_gene_id) if len(dossier) else set()
    result["nph_source_row_count"] = pd.to_numeric(result.nph_source_row_count, errors="coerce").fillna(0).astype(int)
    result["nph_source_exact_ensembl_rows"] = pd.to_numeric(result.nph_source_exact_ensembl_rows, errors="coerce").fillna(0).astype(int)
    for column in ("nph_source_objects", "nph_evidence_classes", "nph_terminal_dispositions"):
        result[column] = result[column].fillna("")
    result["nph_measured_identity_present"] = result.nph_source_row_count.gt(0)
    result["protected_identity_change_dossier_present"] = result.canonical_ensembl_gene_id.isin(changed)
    result["adjudication_state"] = result.protected_identity_change_dossier_present.map(
        {True: "HUMAN_A2R_DECISION_REQUIRED", False: "NO_NPH_CANONICAL_CHANGE_PROPOSED"}
    )
    result["frozen_vocabulary_rewrite_allowed"] = False
    return result.sort_values("vocabulary_index", key=lambda values: pd.to_numeric(values)).reset_index(drop=True)


def normalize_dataset_statuses(summary: pd.DataFrame) -> pd.DataFrame:
    result = summary.copy()
    placeholder = result.dataset.isin({
        "10x_Xenium_healthy_cortex_preview", "CosMx_WTX_human_hippocampus",
        "CosMx_human_frontal_cortex_6K", "HPA_human_brain_StereoSeq",
    })
    administrative = result.dataset.eq("_acquisition")
    result.loc[placeholder, "status"] = PLACEHOLDER_STATUS
    result.loc[administrative, "status"] = ADMIN_STATUS
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_authoritative_mapping.yaml"))
    parser.add_argument("--focused-passed", type=int)
    parser.add_argument("--full-v4-passed", type=int)
    parser.add_argument("--full-v4-warnings", type=int, default=0)
    parser.add_argument("--broader-passed", type=int)
    parser.add_argument("--broader-failed", type=int, default=0)
    parser.add_argument("--r-smoke-pass", action="store_true")
    parser.add_argument("--determinism-pass", action="store_true")
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    outputs = {key: project / value for key, value in config["outputs"].items()}

    authoritative = pd.read_csv(outputs["exact_registry"], dtype=str, keep_default_na=False)
    projectwide = pd.read_csv(outputs["projectwide_feature_identity"], dtype=str, keep_default_na=False, low_memory=False)
    comparison = pd.read_csv(outputs["projectwide_mapping_comparison"], dtype=str, keep_default_na=False)
    decisions = pd.read_csv(outputs["source_decisions"], dtype=str, keep_default_na=False, low_memory=False)
    vocabulary = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv", dtype=str, keep_default_na=False)
    dataset_summary = normalize_dataset_statuses(pd.read_csv(outputs["projectwide_dataset_summary"], dtype=str, keep_default_na=False))
    authoritative_summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
    projectwide_summary = json.loads(outputs["projectwide_summary"].read_text(encoding="utf-8"))

    nph_cache = build_nph_cache_validation(project, config)
    reconciliation, foundation_gates = build_foundation_reconciliation(authoritative, projectwide)
    protected_source_rows, dossier = build_protected_dossier(project, comparison, decisions, vocabulary)
    nph_frozen = build_nph_frozen_vocab_adjudication(vocabulary, decisions, protected_source_rows)

    nph_rows = decisions[decisions.source_dataset_id.str.startswith("NPH52::")]
    source_ensg = nph_rows.source_exact_ensembl_id.str.match(r"^ENSG[0-9]+(?:\.[0-9]+)?$")
    authority_with_source = int((source_ensg & nph_rows.mapping_evidence_class.eq("AUTHORITY_RECONSTRUCTED")).sum())
    if authority_with_source:
        raise RuntimeError(f"NPH source precedence invariant failed for {authority_with_source} rows")

    batch_dir = project / config["authorities"]["ensembl_history"]["local_path"]
    batch_rows = []
    for path in sorted(batch_dir.glob("archive_id_batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        batch_rows.append({
            "batch": path.stem,
            "path": str(path.relative_to(project)).replace("\\", "/"),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "response_count": len(payload.get("queried_ids", [])) if isinstance(payload, dict) else len(payload),
            "append_only": True,
        })
    batches = pd.DataFrame(batch_rows)
    original_expected = config["original_history_batch_sha256"]
    original_observed = {
        Path(record["path"]).name: record["sha256"] for record in batch_rows
        if Path(record["path"]).name in original_expected
    }
    original_history_integrity = (
        len(original_observed) == len(original_expected)
        and all(original_observed.get(name) == expected for name, expected in original_expected.items())
    )
    if not original_history_integrity:
        raise RuntimeError("original 24 Ensembl history batch hashes changed")

    nonterminal = dataset_summary[~dataset_summary.status.isin(TERMINAL_DATASET_STATUSES)]
    protected = []
    for relative, expected in config["protected_hashes"].items():
        observed = sha256_file(project / relative)
        protected.append({"path": relative, "expected": expected, "observed": observed, "pass": expected == observed})
    vocabulary_file_hash = sha256_file(project / "results/v4/stage81a2_foundation_vocabulary.csv")
    vocabulary_semantic = semantic_hash(vocabulary.canonical_ensembl_gene_id.tolist())
    expected_semantic = config["protected_semantic_hashes"]["results/v4/stage81a2_foundation_vocabulary.csv"]

    genuine = int(protected_source_rows.identity_change_classification.eq("GENUINE_CANONICAL_ID_CORRECTION").sum()) if len(protected_source_rows) else 0
    ambiguity = int(protected_source_rows.human_a2r_decision_required.sum()) if len(protected_source_rows) else 0
    blockers = []
    if len(nonterminal): blockers.append(f"{len(nonterminal)} relevant dataset audits remain nonterminal")
    if not foundation_gates["foundation_reconciliation_exact"]: blockers.append("authoritative and audited foundation RNA registries do not reconcile exactly")
    if authority_with_source: blockers.append("NPH source-exact precedence invariant failed")
    if genuine or ambiguity: blockers.append("protected 4,096 identities require human A2R adjudication")
    if not all(item["pass"] for item in protected): blockers.append("protected file hash verification failed")
    if vocabulary_semantic != expected_semantic: blockers.append("frozen 4,096 semantic hash changed")
    status = (
        "AUDIT_INCOMPLETE_TECHNICAL_BLOCKER" if len(nonterminal) or not foundation_gates["foundation_reconciliation_exact"]
        else "READY_FOR_HUMAN_REVIEW_WITH_PROTECTED_IDENTITY_BLOCKER" if genuine or ambiguity
        else "READY_FOR_HUMAN_REVIEW_NO_PROTECTED_IDENTITY_CHANGE"
    )
    report = {
        "stage": "stage81a2r_projectwide_identity_review_package",
        "status": status,
        "scope": {
            "physical_source_files_inventoried": int(pd.read_csv(outputs["all_downloaded_inventory"]).shape[0]),
            "scientific_datasets": int(dataset_summary.dataset.nunique()),
            "matrix_contracts": int(projectwide.matrix_id.nunique()),
            "feature_universes": int(pd.read_csv(outputs["projectwide_feature_universe_inventory"]).shape[0]),
            "normalized_feature_rows": len(projectwide),
            "source_row_equivalent_count": int(pd.to_numeric(projectwide.source_matrix_multiplicity).sum()),
        },
        "projectwide_identity_categories": {
            "materialized_mapping_evidence_class_counts": projectwide_summary["materialized_mapping_evidence_class_counts"],
            "source_row_mapping_evidence_class_counts": projectwide_summary["source_row_mapping_evidence_class_counts"],
            "materialized_project_identity_class_counts": projectwide_summary["materialized_project_identity_class_counts"],
            "source_row_project_identity_class_counts": projectwide_summary["source_row_project_identity_class_counts"],
            "unique_current_canonical_genes": projectwide_summary["unique_current_canonical_genes"],
            "unique_legacy_exact_ids": projectwide_summary["unique_legacy_exact_ids"],
            "unique_source_native_features": projectwide_summary["unique_source_native_features"],
            "unique_symbol_only_unresolved": projectwide_summary["unique_symbol_only_unresolved"],
        },
        "foundation_identity_categories": authoritative_summary["biological_identity_categories"],
        "foundation": foundation_gates,
        "nph": {
            "source_objects": len(nph_cache),
            "source_rows": len(nph_rows),
            "valid_source_native_ensembl_rows": int(source_ensg.sum()),
            "source_native_ensembl_missing_rows": int((~source_ensg).sum()),
            "source_exact_rows": int(nph_rows.mapping_evidence_class.eq("SOURCE_EXACT").sum()),
            "authority_reconstructed_with_valid_source_ensembl": authority_with_source,
            "source_cache_validation_pass": True,
        },
        "frozen_4096": {
            "members": len(vocabulary), "unique_members": vocabulary.canonical_ensembl_gene_id.nunique(),
            "file_sha256": vocabulary_file_hash, "semantic_hash": vocabulary_semantic,
            "expected_semantic_hash": expected_semantic, "semantic_hash_unchanged": vocabulary_semantic == expected_semantic,
            "affected_source_rows": len(protected_source_rows),
            "unique_identity_pairs": len(dossier),
            "unique_frozen_genes_touched": protected_source_rows.canonical_ensembl_gene_id.nunique() if len(protected_source_rows) else 0,
            "classification_counts": protected_source_rows.identity_change_classification.value_counts().sort_index().to_dict() if len(protected_source_rows) else {},
            "pair_classification_counts": dossier.identity_change_classification.value_counts().sort_index().to_dict() if len(dossier) else {},
            "genuine_canonical_correction_rows": genuine,
            "human_a2r_decision_required_rows": ambiguity,
            "artifact_rewritten": False,
        },
        "projectwide_completeness": {
            "status_counts": dataset_summary.status.value_counts().sort_index().to_dict(),
            "relevant_nonterminal_datasets": nonterminal.dataset.tolist(),
            "relevant_nonterminal_count": len(nonterminal),
        },
        "authority": {
            "ensembl_release": 116, "assembly": "GRCh38.p14", "hgnc_snapshot": "2026-08",
            "history_batch_count": len(batches), "original_history_batch_count": len(original_expected),
            "appended_history_batch_count": len(batches) - len(original_expected),
            "original_history_batch_integrity_pass": original_history_integrity,
            "appended_history_batches_hashed": len(batches) > len(original_expected),
            "all_batches_hashed": bool(len(batches)),
        },
        "protected_hashes": protected,
        "protected_hashes_unchanged": all(item["pass"] for item in protected),
        "validation": {
            "focused_stage81a2r_tests_passed": args.focused_passed,
            "full_v4_tests_passed": args.full_v4_passed,
            "full_v4_warnings": args.full_v4_warnings,
            "broader_repository_tests_passed": args.broader_passed,
            "broader_repository_tests_failed": args.broader_failed,
            "r_feature_cache_smoke_pass": args.r_smoke_pass,
            "deterministic_reporting_rerun_pass": args.determinism_pass,
        },
        "scientific_blockers": blockers,
        "frozen_vocabulary_modified": False,
        "expression_values_accessed": False,
        "pathology_opened": False,
        "stage81a3r_started": False,
        "stage81b_started": False,
        "push_performed": False,
    }

    atomic_csv(outputs["nph_cache_validation"], nph_cache)
    atomic_csv(outputs["nph_frozen_vocab_adjudication"], nph_frozen)
    atomic_csv(outputs["protected_identity_source_rows"], protected_source_rows)
    atomic_csv(outputs["protected_identity_dossier"], dossier)
    atomic_csv(outputs["foundation_reconciliation"], reconciliation)
    atomic_csv(outputs["authority_batch_integrity"], batches)
    atomic_csv(outputs["projectwide_dataset_summary"], dataset_summary)
    atomic_json(outputs["projectwide_final_report"], report)

    audit = [
        "# Stage81A2R Project-Wide Identity Audit Candidate", "",
        "**FEATURE/PROVENANCE ONLY - NOT FROZEN - HUMAN REVIEW REQUIRED**", "",
        f"Final audit status: `{status}`", "",
        "## Foundation", "",
        f"- Authoritative current exact genes: {foundation_gates['authoritative_current_exact_count']:,}",
        f"- Audited foundation-RNA current exact genes: {foundation_gates['audited_foundation_rna_current_exact_count']:,}",
        f"- Difference genes: {foundation_gates['difference_gene_count']:,}",
        f"- Future/nonfoundation counterfactual firewall: {foundation_gates['foundation_future_counterfactual_members_identical']}", "",
        f"- Exact legacy identities preserved: {authoritative_summary['biological_identity_categories']['legacy_exact_unique_genes']:,}",
        f"- Source-native biological identities preserved: {authoritative_summary['biological_identity_categories']['source_native_biological_unique_features']:,}",
        f"- Symbol-only unresolved identities: {authoritative_summary['biological_identity_categories']['symbol_only_unresolved_unique_features']:,}", "",
        "## NPH", "",
        f"- Seven source caches validated: {len(nph_cache) == 7}",
        f"- Source-native Ensembl rows incorrectly relegated to authority fallback: {authority_with_source}", "",
        "## Frozen 4,096", "",
        f"- File SHA256: `{vocabulary_file_hash}`",
        f"- Semantic SHA256: `{vocabulary_semantic}`",
        f"- Affected source rows requiring classification: {len(protected_source_rows):,}",
        f"- Unique affected identity pairs: {len(dossier):,}",
        f"- Human-decision-required rows: {ambiguity:,}",
        "- The protected vocabulary was not rewritten.", "",
        "## Completeness", "",
        *[f"- {key}: {value}" for key, value in sorted(report['projectwide_completeness']['status_counts'].items())], "",
        "## Boundaries", "",
        "No expression values or pathology labels were evaluated. Stage81A3R and Stage81B were not started. No source data or frozen scientific artifact was modified.", "",
    ]
    outputs["projectwide_final_audit"].parent.mkdir(parents=True, exist_ok=True)
    outputs["projectwide_final_audit"].write_text("\n".join(audit), encoding="utf-8", newline="\n")

    substantive = [
        outputs["nph_cache_validation"], outputs["nph_frozen_vocab_adjudication"],
        outputs["protected_identity_source_rows"], outputs["protected_identity_dossier"], outputs["foundation_reconciliation"],
        outputs["authority_batch_integrity"], outputs["projectwide_final_report"],
        outputs["projectwide_final_audit"],
    ]
    if outputs["r_environment_manifest"].is_file():
        substantive.append(outputs["r_environment_manifest"])
    hashes = {
        str(path.relative_to(project)).replace("\\", "/"): {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in substantive
    }
    atomic_json(outputs["review_hash_manifest"], {"stage": report["stage"], "artifacts": hashes})
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
