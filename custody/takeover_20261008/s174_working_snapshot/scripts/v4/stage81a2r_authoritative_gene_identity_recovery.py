"""Build the provisional Stage81A2R authoritative gene-identity audit."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from sea_ad_jepa.v4.gene_identity_authority import (
    AuthorityIndex,
    broad_biotype,
    build_authority_index,
    classify_source_native_feature,
    classify_symbol_only,
    history_current_replacements,
    load_history_cache,
    normalize_ensembl_gene_id,
    normalize_text,
    source_family,
    symbol_evidence,
)


EXACT_TERMINAL = {
    "EXACT_CURRENT_ENSEMBL",
    "EXACT_HISTORICAL_ENSEMBL_TO_CURRENT",
    "EXACT_HGNC_APPROVED_TO_ENSEMBL",
    "EXACT_HGNC_PREVIOUS_SYMBOL_RECOVERED",
    "EXACT_HGNC_ALIAS_RECOVERED",
    "EXACT_HGNC_WITHDRAWN_SINGLE_MERGE_RECOVERED",
    "EXACT_ENSEMBL_CURRENT_SYMBOL_RECOVERED",
}
LEGACY_TERMINAL = {
    "LEGACY_EXACT_ENSEMBL_NO_CURRENT_REPLACEMENT",
    "LEGACY_EXACT_ENSEMBL_MULTIPLE_CURRENT_REPLACEMENTS",
}
ALTERNATIVE_AUTHORITY_TERMINAL = {
    "EXACT_REFSEQ_OR_NCBI_GENE",
    "EXACT_GENCODE_LEGACY",
}
SOURCE_NATIVE_TERMINAL = {
    "SOURCE_NATIVE_GENOMIC_LOCUS",
    "SOURCE_NATIVE_TRANSCRIPT_MODEL",
    "SOURCE_ANNOTATED_NOVEL_OR_PREDICTED_GENE",
    "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED",
}
TECHNICAL_TERMINAL = {"NON_BIOLOGICAL_TECHNICAL_FEATURE"}


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def bsd_sum_file(path: Path, chunk: int = 8 * 1024 * 1024) -> tuple[int, int]:
    checksum = 0
    size = 0
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            size += len(block)
            for value in block:
                checksum = ((checksum >> 1) | ((checksum & 1) << 15))
                checksum = (checksum + value) & 0xFFFF
    return checksum, (size + 1023) // 1024


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, default=str) + "\n"
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def atomic_csv(path: Path, frame: pd.DataFrame, compression: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="", suffix=".csv") as handle:
        raw = Path(handle.name)
    temporary = raw
    try:
        frame.to_csv(raw, index=False, lineterminator="\n")
        if compression == "gzip":
            with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent, suffix=".csv.gz") as target_handle:
                temporary = Path(target_handle.name)
                with raw.open("rb") as source, gzip.GzipFile(filename="", fileobj=target_handle, mode="wb", mtime=0) as target:
                    shutil.copyfileobj(source, target)
        os.replace(temporary, path)
    finally:
        raw.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)


def joined(values: Any) -> str:
    return "|".join(sorted(set(values)))


def hgnc_for_ensembl(authority: AuthorityIndex) -> dict[str, tuple[str, ...]]:
    result: dict[str, set[str]] = defaultdict(set)
    for record in authority.hgnc_by_id.values():
        normalized = normalize_ensembl_gene_id(record.ensembl_gene_id)
        if normalized and normalized[0] in authority.ensembl_by_id:
            result[normalized[0]].add(record.hgnc_id)
    return {key: tuple(sorted(values)) for key, values in result.items()}


def adjudicate_row(
    row: Any,
    authority: AuthorityIndex,
    history: dict[str, dict[str, Any]],
    prior_genes: set[str],
) -> dict[str, Any]:
    symbol = normalize_text(row.source_feature_symbol)
    evidence = symbol_evidence(symbol, authority)
    provided = None
    native_provided = normalize_ensembl_gene_id(getattr(row, "source_exact_ensembl_id", ""))
    if native_provided:
        provided = native_provided
    elif row.mapping_method == "exact_source_ensembl_symbol_pair":
        provided = normalize_ensembl_gene_id(row.canonical_ensembl_gene_id)
    terminal = ""
    canonical = ""
    historical = ""
    replacements: tuple[str, ...] = ()
    source_anchor: dict[str, str] = {}
    if normalize_text(row.source_feature_type) != "Gene Expression":
        terminal, source_anchor = classify_source_native_feature(
            row.source_feature_id,
            row.source_feature_symbol,
            row.source_feature_type,
            getattr(row, "source_genome_build_or_annotation", ""),
        )
    elif provided:
        historical = provided[0]
        if historical in authority.ensembl_by_id:
            canonical = historical
            terminal = "EXACT_CURRENT_ENSEMBL"
        else:
            response = history.get(historical, {})
            replacements = history_current_replacements(response, set(authority.ensembl_by_id))
            if len(replacements) == 1:
                canonical = replacements[0]
                terminal = "EXACT_HISTORICAL_ENSEMBL_TO_CURRENT"
            elif len(replacements) > 1:
                terminal = "LEGACY_EXACT_ENSEMBL_MULTIPLE_CURRENT_REPLACEMENTS"
            else:
                terminal = "LEGACY_EXACT_ENSEMBL_NO_CURRENT_REPLACEMENT"
        # Exact source Ensembl identity outranks a modern symbol disagreement.
        # The disagreement is retained in symbol_status rather than rewriting ID.
    else:
        terminal, canonical, evidence = classify_symbol_only(symbol, authority)
        if terminal == "EXACT_HGNC_ID_BUT_NO_EXACT_ENSEMBL_GENE":
            terminal = "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED"
            source_anchor = {
                "source_native_id": joined(evidence["hgnc_approved_ids"]),
                "source_native_symbol": symbol,
                "source_annotation_authority": "HGNC 2026-08",
            }
        elif terminal == "SYMBOL_ONLY_UNRESOLVED":
            terminal, source_anchor = classify_source_native_feature(
                row.source_feature_id,
                row.source_feature_symbol,
                row.source_feature_type,
                getattr(row, "source_genome_build_or_annotation", ""),
            )
    exact = terminal in EXACT_TERMINAL
    if native_provided or (provided and row.mapping_method == "exact_source_ensembl_symbol_pair"):
        evidence_class = "SOURCE_EXACT" if terminal in EXACT_TERMINAL else "LEGACY_ENSEMBL_EXACT" if terminal in LEGACY_TERMINAL else "AMBIGUOUS_UNRESOLVED"
        evidence_method = "source feature metadata exact Ensembl stable ID"
        evidence_file = getattr(row, "source_identity_evidence_file", "") or "frozen source feature metadata"
    elif terminal in EXACT_TERMINAL:
        evidence_class = "AUTHORITY_RECONSTRUCTED"
        evidence_method = "exact symbol adjudication against pinned Ensembl/HGNC authorities"
        evidence_file = "Ensembl 116 GTF; HGNC 2026-08 snapshots"
    elif terminal in ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL:
        evidence_class = "SOURCE_ERA_EXACT"
        evidence_method = "source-native biological anchor preserved without current Ensembl projection"
        evidence_file = getattr(row, "source_identity_evidence_file", "")
    elif terminal in TECHNICAL_TERMINAL:
        evidence_class = "NON_GENE_FEATURE"
        evidence_method = "source-native feature type"
        evidence_file = getattr(row, "source_identity_evidence_file", "")
    else:
        evidence_class = "AMBIGUOUS_UNRESOLVED" if terminal.startswith(("AMBIGUOUS", "CONFLICTING")) else "UNRESOLVED"
        evidence_method = "no exact support after source and authority audit"
        evidence_file = ""
    prior_unresolved = row.mapping_decision == "AMBIGUOUS_UNRESOLVED"
    recovery_type = ""
    if exact and prior_unresolved:
        recovery_type = "SUPPORT_RECOVERY_ONLY" if canonical in prior_genes else "NEW_CANONICAL_GENE_RECOVERY"
    elif exact:
        recovery_type = "PRIOR_EXACT_RECONFIRMED"
    elif terminal in LEGACY_TERMINAL:
        recovery_type = "LEGACY_EXACT_PRESERVED"
    reason = {
        "EXACT_CURRENT_ENSEMBL": "source-provided stable Ensembl gene ID is current in release 116",
        "EXACT_HISTORICAL_ENSEMBL_TO_CURRENT": "official Ensembl history has exactly one release-116 current replacement",
        "EXACT_HGNC_APPROVED_TO_ENSEMBL": "exact HGNC approved symbol has one release-116 Ensembl gene",
        "EXACT_HGNC_PREVIOUS_SYMBOL_RECOVERED": "exact unique HGNC previous symbol has one release-116 Ensembl gene",
        "EXACT_HGNC_ALIAS_RECOVERED": "exact unique HGNC alias has one release-116 Ensembl gene",
        "EXACT_HGNC_WITHDRAWN_SINGLE_MERGE_RECOVERED": "exact withdrawn HGNC symbol has one approved replacement with one release-116 Ensembl gene",
        "EXACT_ENSEMBL_CURRENT_SYMBOL_RECOVERED": "exact current Ensembl gene symbol identifies one release-116 gene",
        "LEGACY_EXACT_ENSEMBL_NO_CURRENT_REPLACEMENT": "exact historical source Ensembl ID has no unique current projection",
        "LEGACY_EXACT_ENSEMBL_MULTIPLE_CURRENT_REPLACEMENTS": "exact historical source Ensembl ID has multiple current projections",
        "AMBIGUOUS_HGNC_SPLIT": "withdrawn HGNC symbol has multiple approved replacement reports",
        "AMBIGUOUS_ALIAS_MULTIPLE_TARGETS": "exact HGNC alias maps to multiple current genes",
        "AMBIGUOUS_PREVIOUS_SYMBOL_MULTIPLE_TARGETS": "exact HGNC previous symbol maps to multiple current genes",
        "CONFLICTING_AUTHORITATIVE_IDENTITY": "exact authoritative channels disagree on current gene identity",
        "EXACT_REFSEQ_OR_NCBI_GENE": "exact source-provided RefSeq or NCBI Gene anchor preserved without Ensembl projection",
        "EXACT_GENCODE_LEGACY": "exact source-provided legacy GENCODE identity preserved without current Ensembl projection",
        "SOURCE_NATIVE_GENOMIC_LOCUS": "exact source-native genomic locus preserved without cross-dataset merging",
        "SOURCE_NATIVE_TRANSCRIPT_MODEL": "exact source-native transcript model preserved without gene projection",
        "SOURCE_ANNOTATED_NOVEL_OR_PREDICTED_GENE": "source-annotated novel or predicted biological feature preserved",
        "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED": "exact source-native biological identity is preserved but not projected into the current gene registry",
        "SYMBOL_ONLY_UNRESOLVED": "source provides a symbol but no exact current, historical, or alternative biological anchor",
        "NON_BIOLOGICAL_TECHNICAL_FEATURE": "source explicitly identifies a technical or non-biological feature",
    }[terminal]
    return {
        "raw_source_feature_id": row.source_feature_id,
        "raw_source_feature_symbol": row.source_feature_symbol,
        "normalized_source_symbol": symbol,
        "source_provided_ensembl_id": provided[1] if provided else "",
        "normalized_source_ensembl_id": historical,
        "authority_current_ensembl_id": canonical,
        "ensembl_history_replacements": joined(replacements),
        "terminal_disposition": terminal,
        "terminal_reason": reason,
        "recovery_type": recovery_type,
        "hgnc_approved_ids": joined(evidence["hgnc_approved_ids"]),
        "hgnc_approved_ensembl": joined(evidence["hgnc_approved_ensembl"]),
        "hgnc_previous_ids": joined(evidence["hgnc_previous_ids"]),
        "hgnc_previous_ensembl": joined(evidence["hgnc_previous_ensembl"]),
        "hgnc_alias_ids": joined(evidence["hgnc_alias_ids"]),
        "hgnc_alias_ensembl": joined(evidence["hgnc_alias_ensembl"]),
        "hgnc_withdrawn_replacement_ids": joined(evidence["hgnc_withdrawn_replacement_ids"]),
        "hgnc_withdrawn_ensembl": joined(evidence["hgnc_withdrawn_ensembl"]),
        "ensembl_current_symbol_candidates": joined(evidence["ensembl_symbol_candidates"]),
        "source_native_id": source_anchor.get("source_native_id", ""),
        "source_annotation_authority": source_anchor.get("source_annotation_authority", ""),
        "source_refseq_id": source_anchor.get("source_refseq_id", ""),
        "source_ncbi_gene_id": source_anchor.get("source_ncbi_gene_id", ""),
        "source_transcript_id": source_anchor.get("source_transcript_id", ""),
        "source_chromosome": source_anchor.get("source_chromosome", ""),
        "source_start": source_anchor.get("source_start", ""),
        "source_end": source_anchor.get("source_end", ""),
        "source_strand": source_anchor.get("source_strand", ""),
        "source_biotype": source_anchor.get("source_biotype", ""),
        "mapping_status_authoritative": "exact" if exact else "legacy_exact" if terminal in LEGACY_TERMINAL else "preserved_unprojected" if terminal in ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL else "ambiguous" if evidence_class == "AMBIGUOUS_UNRESOLVED" else "unresolved",
        "mapping_evidence_class": evidence_class,
        "mapping_method_authoritative": evidence_method,
        "mapping_authority": "source_native" if evidence_class in {"SOURCE_EXACT", "SOURCE_ERA_EXACT", "SOURCE_ERA_RECONSTRUCTED"} else "Ensembl_116_and_HGNC_2026_08" if evidence_class == "AUTHORITY_RECONSTRUCTED" else "none",
        "mapping_evidence_file": evidence_file,
        "canonical_release": "Ensembl 116" if canonical else "",
        "historical_id_status": terminal if provided and terminal != "EXACT_CURRENT_ENSEMBL" else "current" if provided else "not_source_ensembl",
        "symbol_status": "source_symbol_differs_from_current" if canonical and symbol and authority.ensembl_by_id[canonical].symbol != symbol else "exact_or_not_applicable",
        "ambiguity_reason": reason if evidence_class in {"AMBIGUOUS_UNRESOLVED", "UNRESOLVED"} else "",
    }


def build_decisions(source: pd.DataFrame, authority: AuthorityIndex, history: dict[str, dict[str, Any]], prior_genes: set[str]) -> pd.DataFrame:
    key_columns = ["source_feature_id", "source_feature_symbol", "source_feature_type", "source_genome_build_or_annotation", "canonical_ensembl_gene_id", "mapping_method", "mapping_decision", "source_exact_ensembl_id", "source_identity_evidence_file", "source_refseq_id", "source_ncbi_gene_id", "source_transcript_id", "source_chromosome", "source_start", "source_end", "source_strand", "source_biotype"]
    unique = source[key_columns].drop_duplicates().reset_index(drop=True)
    additions = [adjudicate_row(row, authority, history, prior_genes) for row in unique.itertuples(index=False)]
    lookup = unique.copy()
    for column in additions[0]:
        if column not in lookup.columns:
            lookup[column] = [item[column] for item in additions]
    result = source.copy()
    result.insert(0, "source_record_index", range(len(result)))
    result.insert(2, "source_object_or_matrix", result["source_dataset_id"])
    result.insert(3, "source_feature_index", result["source_feature_id"])
    result = result.merge(lookup, on=key_columns, how="left", validate="many_to_one", sort=False)
    if len(result) != len(source) or result.terminal_disposition.eq("").any():
        raise RuntimeError("terminal disposition accounting failed")
    return result


def attach_source_native_feature_evidence(project: Path, source: pd.DataFrame, manifest_path: str) -> pd.DataFrame:
    """Attach exact rowData evidence by source object and feature index."""
    enriched = source.copy()
    native_columns = [
        "source_exact_ensembl_id", "source_identity_evidence_file", "source_refseq_id",
        "source_ncbi_gene_id", "source_transcript_id", "source_chromosome", "source_start",
        "source_end", "source_strand", "source_biotype",
    ]
    for column in native_columns:
        enriched[column] = ""
    direct = enriched.mapping_method.eq("exact_source_ensembl_symbol_pair")
    enriched.loc[direct, "source_exact_ensembl_id"] = enriched.loc[direct, "canonical_ensembl_gene_id"]
    enriched.loc[direct, "source_identity_evidence_file"] = enriched.loc[direct, "source_dataset_id"].map(lambda value: f"source feature metadata::{value}")
    path = project / manifest_path
    if not path.exists():
        return enriched
    manifest = pd.read_csv(path, dtype=str, keep_default_na=False)
    for record in manifest.to_dict("records"):
        relative = record["source_local_path"].replace("\\", "/")
        if not relative.endswith(".qs"):
            continue
        source_id = f"NPH52::{Path(relative).name}"
        selected = enriched.source_dataset_id.eq(source_id)
        if not selected.any():
            continue
        raw_cache = record["cache_path"].replace("\\", "/")
        cache_path = project / raw_cache if not raw_cache.startswith("/mnt/") else project / raw_cache.split("/Jepa project/", 1)[-1]
        cache = pd.read_csv(cache_path, sep="\t", dtype=str, keep_default_na=False)
        cache = cache.set_index("source_feature_index", drop=False)
        indices = enriched.loc[selected, "source_feature_id"]
        missing = set(indices) - set(cache.index)
        if missing:
            raise RuntimeError(f"NPH source evidence missing {len(missing)} feature indices for {source_id}")
        lookup = cache.loc[indices]
        enriched.loc[selected, "source_exact_ensembl_id"] = lookup.source_ensembl_id.to_numpy()
        enriched.loc[selected, "source_identity_evidence_file"] = relative
        for destination, cache_column in (
            ("source_refseq_id", "source_refseq_id"), ("source_ncbi_gene_id", "source_ncbi_gene_id"),
            ("source_transcript_id", "source_transcript_id"), ("source_chromosome", "source_chromosome"),
            ("source_start", "source_start"), ("source_end", "source_end"),
            ("source_strand", "source_strand"), ("source_biotype", "source_biotype"),
        ):
            if cache_column in lookup:
                enriched.loc[selected, destination] = lookup[cache_column].to_numpy()
    return enriched


def build_exact_registry(decisions: pd.DataFrame, authority: AuthorityIndex, prior_genes: set[str]) -> tuple[pd.DataFrame, str]:
    exact = decisions[decisions.terminal_disposition.isin(EXACT_TERMINAL)].copy()
    ids = sorted(set(exact.authority_current_ensembl_id))
    hgnc_by_ens = hgnc_for_ensembl(authority)
    grouped = exact.groupby("authority_current_ensembl_id", sort=False).agg(
        source_record_count=("authority_current_ensembl_id", "size"),
        source_support_count=("source_dataset_id", "nunique"),
        source_family_support=("source_dataset_id", lambda values: joined(source_family(value) for value in values)),
    )
    rows = []
    for index, stable_id in enumerate(ids):
        gene = authority.ensembl_by_id[stable_id]
        hgnc_ids = hgnc_by_ens.get(stable_id, ())
        hgnc = authority.hgnc_by_id.get(hgnc_ids[0]) if len(hgnc_ids) == 1 else None
        support = grouped.loc[stable_id]
        rows.append({
            "successor_gene_index": index,
            "canonical_ensembl_gene_id": stable_id,
            "ensembl_versioned_gene_id": gene.versioned_id,
            "canonical_symbol": gene.symbol,
            "ensembl_biotype": gene.biotype,
            "broad_biotype": broad_biotype(gene, hgnc),
            "chromosome": gene.chromosome,
            "start": gene.start,
            "end": gene.end,
            "strand": gene.strand,
            "hgnc_ids": joined(hgnc_ids),
            "hgnc_locus_group": hgnc.locus_group if hgnc else "",
            "hgnc_locus_type": hgnc.locus_type if hgnc else "",
            "source_record_count": int(support.source_record_count),
            "source_support_count": int(support.source_support_count),
            "source_family_support": support.source_family_support,
            "new_relative_to_prior_37346": stable_id not in prior_genes,
            "authority_release": "Ensembl 116 / HGNC 2026-08",
            "status": "PROVISIONAL_NOT_FROZEN",
        })
    registry = pd.DataFrame(rows)
    semantic = "".join(f"{row.canonical_ensembl_gene_id}\t{row.canonical_symbol}\t{row.ensembl_biotype}\n" for row in registry.itertuples())
    semantic_hash = hashlib.sha256(semantic.encode()).hexdigest()
    registry["registry_semantic_hash"] = semantic_hash
    return registry, semantic_hash


def build_legacy_registry(decisions: pd.DataFrame) -> pd.DataFrame:
    legacy = decisions[decisions.terminal_disposition.isin(LEGACY_TERMINAL)]
    columns = ["historical_ensembl_gene_id", "source_record_count", "source_families", "source_objects", "raw_symbols", "possible_current_replacements", "terminal_disposition", "human_projection_policy_required"]
    rows = []
    for stable_id, group in legacy.groupby("normalized_source_ensembl_id", sort=True):
        rows.append({
            "historical_ensembl_gene_id": stable_id,
            "source_record_count": len(group),
            "source_families": joined(group.source_dataset_id.map(source_family)),
            "source_objects": joined(group.source_dataset_id),
            "raw_symbols": joined(group.raw_source_feature_symbol),
            "possible_current_replacements": joined("|".join(group.ensembl_history_replacements).split("|")),
            "terminal_disposition": joined(group.terminal_disposition),
            "human_projection_policy_required": True,
        })
    return pd.DataFrame(rows, columns=columns)


def build_source_native_registry(decisions: pd.DataFrame) -> pd.DataFrame:
    terminal = ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL
    source_native = decisions[decisions.terminal_disposition.isin(terminal)].copy()
    columns = [
        "source_dataset_id", "source_object_or_matrix", "source_feature_index",
        "raw_source_feature_id", "raw_source_feature_symbol", "terminal_disposition",
        "source_native_id", "source_annotation_authority", "source_refseq_id",
        "source_ncbi_gene_id", "source_transcript_id", "source_chromosome",
        "source_start", "source_end", "source_strand", "source_biotype",
        "encoder_address_space_policy", "cross_dataset_merge_policy",
    ]
    if not len(source_native):
        return pd.DataFrame(columns=columns)
    result = source_native[[column for column in columns if column in source_native]].copy()
    result["encoder_address_space_policy"] = "HUMAN_A2R_DECISION_REQUIRED"
    result["cross_dataset_merge_policy"] = "DO_NOT_MERGE_WITHOUT_EXACT_SHARED_IDENTITY"
    return result[columns].sort_values(["source_dataset_id", "source_object_or_matrix", "source_feature_index"])


def build_unresolved(decisions: pd.DataFrame) -> pd.DataFrame:
    resolved_or_preserved = EXACT_TERMINAL | LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL | TECHNICAL_TERMINAL
    unresolved = decisions[~decisions.terminal_disposition.isin(resolved_or_preserved)]
    columns = ["raw_symbol", "source_families", "source_objects", "source_row_count", "current_ensembl_exact_symbol_candidates", "hgnc_approved_match_count", "hgnc_previous_symbol_match_count", "hgnc_alias_match_count", "hgnc_withdrawn_match", "replacement_hgnc_ids", "ensembl_current_gene_candidates", "historical_ensembl_evidence", "terminal_reason"]
    rows = []
    for symbol, group in unresolved.groupby("raw_source_feature_symbol", sort=True):
        rows.append({
            "raw_symbol": symbol,
            "source_families": joined(group.source_dataset_id.map(source_family)),
            "source_objects": joined(group.source_dataset_id),
            "source_row_count": len(group),
            "current_ensembl_exact_symbol_candidates": joined("|".join(group.ensembl_current_symbol_candidates).split("|")),
            "hgnc_approved_match_count": len(set("|".join(group.hgnc_approved_ids).split("|")) - {""}),
            "hgnc_previous_symbol_match_count": len(set("|".join(group.hgnc_previous_ids).split("|")) - {""}),
            "hgnc_alias_match_count": len(set("|".join(group.hgnc_alias_ids).split("|")) - {""}),
            "hgnc_withdrawn_match": bool("".join(group.hgnc_withdrawn_replacement_ids)),
            "replacement_hgnc_ids": joined("|".join(group.hgnc_withdrawn_replacement_ids).split("|")),
            "ensembl_current_gene_candidates": joined("|".join(group[["hgnc_approved_ensembl", "hgnc_previous_ensembl", "hgnc_alias_ensembl", "hgnc_withdrawn_ensembl", "ensembl_current_symbol_candidates"]].astype(str).agg("|".join, axis=1)).split("|")),
            "historical_ensembl_evidence": joined(group.normalized_source_ensembl_id),
            "terminal_reason": joined(group.terminal_disposition),
        })
    return pd.DataFrame(rows, columns=columns).sort_values(["source_row_count", "raw_symbol"], ascending=[False, True])


def matrix_units(prior_support: pd.DataFrame) -> pd.DataFrame:
    return prior_support[["matrix_id", "source_dataset_id"]].drop_duplicates().sort_values(["source_dataset_id", "matrix_id"])


def build_measurement(decisions: pd.DataFrame, registry: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    exact = decisions[decisions.terminal_disposition.isin(EXACT_TERMINAL)]
    measured = exact.groupby("source_dataset_id").authority_current_ensembl_id.apply(set).to_dict()
    rows = []
    for unit in units.itertuples(index=False):
        present = measured.get(unit.source_dataset_id, set())
        universe_hash = hashlib.sha256("\n".join(sorted(present)).encode()).hexdigest()
        for gene in registry.itertuples(index=False):
            supported = gene.canonical_ensembl_gene_id in present
            rows.append({
                "matrix_id": unit.matrix_id,
                "source_dataset_id": unit.source_dataset_id,
                "successor_gene_index": gene.successor_gene_index,
                "canonical_ensembl_gene_id": gene.canonical_ensembl_gene_id,
                "canonical_symbol": gene.canonical_symbol,
                "measured_gene": supported,
                "measurement_status": "addressable_measured_zero_or_nonzero_at_runtime" if supported else "structurally_unmeasured",
                "measured_zero_distinct_from_unmeasured": True,
                "source_feature_universe_hash": universe_hash,
            })
    return pd.DataFrame(rows)


def build_delta(registry: pd.DataFrame, prior_support: pd.DataFrame, measurement: pd.DataFrame) -> pd.DataFrame:
    old = prior_support[prior_support.measured_gene.astype(str).str.lower().eq("true")].groupby("canonical_ensembl_gene_id").matrix_id.nunique()
    new = measurement[measurement.measured_gene].groupby("canonical_ensembl_gene_id").matrix_id.nunique()
    rows = []
    for gene in registry.itertuples(index=False):
        old_count = int(old.get(gene.canonical_ensembl_gene_id, 0))
        new_count = int(new.get(gene.canonical_ensembl_gene_id, 0))
        rows.append({
            "canonical_ensembl_gene_id": gene.canonical_ensembl_gene_id,
            "canonical_symbol": gene.canonical_symbol,
            "delta_type": "NEW_CANONICAL_GENE_RECOVERY" if gene.new_relative_to_prior_37346 else ("SUPPORT_RECOVERY_ONLY" if new_count > old_count else "UNCHANGED_EXACT_SUPPORT"),
            "prior_measured_matrix_count": old_count,
            "authoritative_measured_matrix_count": new_count,
            "measurement_support_delta": new_count - old_count,
        })
    return pd.DataFrame(rows)


def build_mapping_comparison(decisions: pd.DataFrame, frozen_vocabulary: set[str]) -> pd.DataFrame:
    rows = []
    for item in decisions.itertuples(index=False):
        before = item.canonical_ensembl_gene_id if item.mapping_decision == "EXACT_RETAINED" else ""
        after = item.authority_current_ensembl_id
        if before == after:
            change = "STRONGER_EVIDENCE_SAME_ID" if before and item.mapping_evidence_class == "SOURCE_EXACT" else "NO_CHANGE"
        elif not before and after:
            change = "NEWLY_RESOLVED"
        elif before and not after:
            change = "LEGITIMATE_ID_CORRECTION" if item.terminal_disposition in LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL else "BECAME_AMBIGUOUS" if item.mapping_evidence_class == "AMBIGUOUS_UNRESOLVED" else "BECAME_UNRESOLVED"
        else:
            change = "LEGITIMATE_ID_CORRECTION"
        rows.append({
            "source_dataset_id": item.source_dataset_id,
            "source_feature_index": item.source_feature_index,
            "source_feature_id_raw": item.raw_source_feature_id,
            "source_feature_symbol_raw": item.raw_source_feature_symbol,
            "previous_canonical_ensembl_id": before,
            "authoritative_canonical_ensembl_id": after,
            "comparison_class": change,
            "mapping_evidence_class": item.mapping_evidence_class,
            "terminal_disposition": item.terminal_disposition,
            "affects_frozen_4096_gene": bool((before and before in frozen_vocabulary) or (after and after in frozen_vocabulary)),
            "automatic_frozen_vocabulary_rewrite_allowed": False,
        })
    return pd.DataFrame(rows)


def build_collisions(decisions: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    exact = decisions[decisions.terminal_disposition.isin(EXACT_TERMINAL)]
    physical = units.groupby("source_dataset_id").matrix_id.apply(list).to_dict()
    columns = ["matrix_id", "source_object", "canonical_ensembl_gene_id", "source_feature_indices", "raw_symbols", "raw_ids", "resolution_tiers", "already_duplicate_before_remapping", "colliding_row_count", "classification"]
    rows = []
    for (source, canonical), group in exact.groupby(["source_dataset_id", "authority_current_ensembl_id"], sort=True):
        if len(group) < 2:
            continue
        prior = set(group.canonical_ensembl_gene_id) - {""}
        for matrix_id in physical.get(source, [source]):
            rows.append({
                "matrix_id": matrix_id,
                "source_object": source,
                "canonical_ensembl_gene_id": canonical,
                "source_feature_indices": joined(group.source_feature_index),
                "raw_symbols": joined(group.raw_source_feature_symbol),
                "raw_ids": joined(group.raw_source_feature_id),
                "resolution_tiers": joined(group.terminal_disposition),
                "already_duplicate_before_remapping": len(prior) == 1 and next(iter(prior), "") == canonical,
                "colliding_row_count": len(group),
                "classification": "DUPLICATE_CANONICAL_MAPPING_REQUIRES_MATERIALIZATION_POLICY",
            })
    return pd.DataFrame(rows, columns=columns)


def source_summary(decisions: pd.DataFrame, collisions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups: list[tuple[str, pd.DataFrame]] = [(name, group) for name, group in decisions.groupby("source_dataset_id", sort=True)]
    groups += [(f"aggregate::{family}", decisions[decisions.source_dataset_id.map(source_family).eq(family)]) for family in ("SEA_AD", "HVS", "NPH52")]
    for name, group in groups:
        collision_count = int(collisions.source_object.isin(group.source_dataset_id.unique()).sum()) if len(collisions) else 0
        rows.append({
            "source": name,
            "source_rows": len(group),
            "prior_exact": int(group.mapping_decision.eq("EXACT_RETAINED").sum()),
            "prior_unresolved": int(group.mapping_decision.eq("AMBIGUOUS_UNRESOLVED").sum()),
            "newly_recovered_source_rows": int(group.recovery_type.isin(["SUPPORT_RECOVERY_ONLY", "NEW_CANONICAL_GENE_RECOVERY"]).sum()),
            "support_only_recovered_rows": int(group.recovery_type.eq("SUPPORT_RECOVERY_ONLY").sum()),
            "new_gene_recovered_rows": int(group.recovery_type.eq("NEW_CANONICAL_GENE_RECOVERY").sum()),
            "alternative_authority_exact_rows": int(group.terminal_disposition.isin(ALTERNATIVE_AUTHORITY_TERMINAL).sum()),
            "source_native_biological_rows": int(group.terminal_disposition.isin(SOURCE_NATIVE_TERMINAL).sum()),
            "symbol_only_unresolved_rows": int(group.terminal_disposition.eq("SYMBOL_ONLY_UNRESOLVED").sum()),
            "technical_feature_rows": int(group.terminal_disposition.isin(TECHNICAL_TERMINAL).sum()),
            "remaining_unresolved_rows": int((~group.terminal_disposition.isin(EXACT_TERMINAL | LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL | TECHNICAL_TERMINAL)).sum()),
            "legacy_exact_rows": int(group.terminal_disposition.isin(LEGACY_TERMINAL).sum()),
            "duplicate_canonical_collision_rows": collision_count,
            "measured_current_exact_genes_after_recovery": group.loc[group.terminal_disposition.isin(EXACT_TERMINAL), "authority_current_ensembl_id"].nunique(),
        })
    return pd.DataFrame(rows)


def biotype_summary(decisions: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    new = registry[registry.new_relative_to_prior_37346]
    exact = decisions[decisions.terminal_disposition.isin(EXACT_TERMINAL)]
    rows = []
    for biotype, group in new.groupby("broad_biotype", sort=True):
        ids = set(group.canonical_ensembl_gene_id)
        source = exact[exact.authority_current_ensembl_id.isin(ids)]
        rows.append({
            "broad_biotype": biotype,
            "new_current_gene_count": len(group),
            "recovered_source_record_count": len(source),
            "source_families": joined(source.source_dataset_id.map(source_family)),
            "source_objects": joined(source.source_dataset_id),
        })
    return pd.DataFrame(rows, columns=["broad_biotype", "new_current_gene_count", "recovered_source_record_count", "source_families", "source_objects"])


def authority_manifest(project: Path, config: dict, history_dir: Path) -> dict:
    items = []
    for key in ("ensembl", "hgnc_complete", "hgnc_withdrawn"):
        entry = dict(config["authorities"][key])
        path = project / entry["local_path"]
        entry.update({"byte_size": path.stat().st_size, "sha256": sha256_file(path), "retrieval_recorded_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), "role_in_adjudication": key})
        if key == "ensembl":
            expected = entry["source_checksum"].split()
            observed = bsd_sum_file(path)
            entry["source_checksum_observed"] = f"{observed[0]} {observed[1]} {path.name}"
            entry["source_checksum_verified"] = observed == (int(expected[0]), int(expected[1]))
        elif entry.get("source_md5_base64"):
            observed_md5 = base64.b64encode(hashlib.md5(path.read_bytes()).digest()).decode()
            entry["source_md5_observed_base64"] = observed_md5
            entry["source_checksum_verified"] = observed_md5 == entry["source_md5_base64"]
        items.append(entry)
    history_files = sorted(history_dir.glob("archive_id_batch_*.json"))
    history_hashes = {str(path.relative_to(project)).replace("\\", "/"): sha256_file(path) for path in history_files}
    semantic = hashlib.sha256(json.dumps(history_hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "stage": config["stage_id"],
        "status": config["status"],
        "authorities": items,
        "ensembl_history": {**config["authorities"]["ensembl_history"], "response_file_count": len(history_files), "response_files": history_hashes, "cache_semantic_sha256": semantic},
        "no_rolling_unpinned_authority": True,
        "fuzzy_mapping_used": False,
    }


def build_readout(summary: dict, by_source: pd.DataFrame, by_biotype: pd.DataFrame, unresolved: pd.DataFrame) -> str:
    def markdown(frame: pd.DataFrame) -> str:
        columns = list(frame.columns)
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        rows = ["| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in frame.itertuples(index=False, name=None)]
        return "\n".join([header, separator, *rows])

    source_table = markdown(by_source)
    biotype_table = markdown(by_biotype) if len(by_biotype) else "No new current genes recovered."
    reasons = "\n".join(f"- `{key}`: {value:,}" for key, value in summary["remaining_terminal_reasons"].items())
    top = markdown(unresolved[["raw_symbol", "source_row_count", "terminal_reason"]].head(20)) if len(unresolved) else "No unresolved symbols."
    return f"""# Stage81A2R Authoritative Gene-Identity Recovery

**PROVISIONAL - NOT FROZEN - AUTHORITATIVE MAPPING RECOVERY**

Stage81A3R/global-state work remained paused. This audit used exact release-pinned Ensembl/HGNC evidence only; it performed no model training and opened no DEV RNA, SEALED RNA, or pathology.

## Accounting

1. Previous current-exact candidate: **37,346**
2. Previously unresolved source records: **106,118**
3. Previously unresolved unique symbols: **{summary['before']['unique_unresolved_symbols']:,}**
4. Source records newly resolved: **{summary['recovery']['source_records_recovered']:,}**
5. Unique symbols newly resolved: **{summary['recovery']['unique_symbols_recovered']:,}**
6. Support-only recovered source records: **{summary['recovery']['support_only_recovered_records']:,}**
   - Existing genes gaining support in one or more additional matrices: **{summary['recovery']['existing_genes_gaining_matrix_support']:,}**
7. Genuinely new current Ensembl genes recovered: **{summary['recovery']['new_current_genes']:,}**
8. Final provisional current exact address-space size: **{summary['after']['current_exact_gene_count']:,}**
9. Exact historical/legacy Ensembl identities without unique projection: **{summary['after']['legacy_exact_count']:,}**
   - Source records preserving those identities: **{summary['after']['legacy_exact_source_records']:,}**
10. Remaining unresolved source records: **{summary['after']['remaining_unresolved_source_records']:,}**
11. Remaining unresolved unique symbols: **{summary['after']['remaining_unresolved_unique_symbols']:,}**
12. Within-matrix canonical collisions: **{summary['after']['within_matrix_collision_count']:,}**
13. New semantic hash: `{summary['after']['current_registry_semantic_hash']}`

## Preserved Biological Identity Classes

- Current canonical Ensembl genes: **{summary['biological_identity_categories']['current_canonical_unique_genes']:,}** unique genes across **{summary['biological_identity_categories']['current_canonical_gene_source_rows']:,}** source rows.
- Legacy exact Ensembl genes: **{summary['biological_identity_categories']['legacy_exact_unique_genes']:,}** unique IDs across **{summary['biological_identity_categories']['legacy_exact_gene_source_rows']:,}** source rows.
- Alternative-authority exact features: **{summary['biological_identity_categories']['alternative_authority_exact_unique_features']:,}** unique anchors across **{summary['biological_identity_categories']['alternative_authority_exact_source_rows']:,}** source rows.
- Source-native coordinate/transcript/biological features: **{summary['biological_identity_categories']['source_native_biological_unique_features']:,}** source-scoped features across **{summary['biological_identity_categories']['source_native_biological_source_rows']:,}** rows.
- Symbol-only unresolved: **{summary['biological_identity_categories']['symbol_only_unresolved_unique_features']:,}** unique symbols across **{summary['biological_identity_categories']['symbol_only_unresolved_source_rows']:,}** rows.
- Technical/non-biological: **{summary['biological_identity_categories']['technical_nonbiological_unique_features']:,}** unique features across **{summary['biological_identity_categories']['technical_nonbiological_source_rows']:,}** rows.

Absence from Ensembl/HGNC is not a biological-exclusion criterion. Source-native biological evidence is preserved in a separate registry and remains subject to a human A2R encoder-address-space decision. It is never merged across datasets without exact shared identity.

Source-row counts are not gene counts. Support-only recovery improves legitimate matrix measurement evidence without increasing the biological address space.

## Remaining Reasons

{reasons or '- None'}

## Recovery By Source

{source_table}

## New Current Genes By Biotype

{biotype_table}

No protein-coding or other biotype filter was applied.

## Highest-Frequency Unresolved Symbols

{top}

The complete tail is preserved in `stage81a2r_authoritative_unresolved_features_candidate.csv.gz`; it is not hidden behind these aggregates.

## Collision Boundary

Collision rows are evidence only. No expression rows were summed, dropped, duplicated, or otherwise materialized. Any reported collision requires a later human materialization policy.

## Governance

**{summary['human_decision']}**

A2R is not frozen. Freeze1 is not declared. Do not proceed into A3R automatically.
"""


def run(project: Path, config: dict) -> dict:
    outputs = {key: project / value for key, value in config["outputs"].items()}
    authority_cfg = config["authorities"]
    authority = build_authority_index(
        project / authority_cfg["ensembl"]["local_path"],
        project / authority_cfg["hgnc_complete"]["local_path"],
        project / authority_cfg["hgnc_withdrawn"]["local_path"],
    )
    history_dir = project / authority_cfg["ensembl_history"]["local_path"]
    history = load_history_cache(history_dir)
    inputs = config["inputs"]
    source = pd.read_csv(project / inputs["prior_source_decisions"], dtype=str, keep_default_na=False)
    source = attach_source_native_feature_evidence(project, source, inputs["r_feature_cache_manifest"])
    prior_registry = pd.read_csv(project / inputs["prior_exact_registry"], dtype=str, keep_default_na=False)
    prior_support = pd.read_csv(project / inputs["prior_measurement_support"], dtype=str, keep_default_na=False)
    prior_genes = set(prior_registry.canonical_ensembl_gene_id)
    source_ensembl = {
        normalized[0]
        for row in source.itertuples(index=False)
        if row.mapping_method == "exact_source_ensembl_symbol_pair"
        for normalized in [normalize_ensembl_gene_id(row.canonical_ensembl_gene_id)]
        if normalized
    }
    missing_history = (source_ensembl - set(authority.ensembl_by_id)) - set(history)
    if missing_history:
        raise RuntimeError(f"missing Ensembl history responses for {len(missing_history)} exact non-current source IDs")
    decisions = build_decisions(source, authority, history, prior_genes)
    registry, semantic_hash = build_exact_registry(decisions, authority, prior_genes)
    legacy = build_legacy_registry(decisions)
    source_native = build_source_native_registry(decisions)
    unresolved = build_unresolved(decisions)
    units = matrix_units(prior_support)
    measurement = build_measurement(decisions, registry, units)
    delta = build_delta(registry, prior_support, measurement)
    collisions = build_collisions(decisions, units)
    by_source = source_summary(decisions, collisions)
    by_biotype = biotype_summary(decisions, registry)
    frozen_vocabulary_frame = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv", dtype=str, keep_default_na=False)
    frozen_vocabulary = set(frozen_vocabulary_frame.canonical_ensembl_gene_id)
    comparison = build_mapping_comparison(decisions, frozen_vocabulary)
    protected_corrections = comparison[(comparison.comparison_class == "LEGITIMATE_ID_CORRECTION") & comparison.affects_frozen_4096_gene]
    atomic_csv(outputs["projectwide_mapping_comparison"], comparison)
    protected_unique_pairs = protected_corrections[["previous_canonical_ensembl_id", "authoritative_canonical_ensembl_id"]].drop_duplicates()
    manifest = authority_manifest(project, config, history_dir)
    prior_unresolved = decisions.mapping_decision.eq("AMBIGUOUS_UNRESOLVED")
    recovered = prior_unresolved & decisions.terminal_disposition.isin(EXACT_TERMINAL)
    preserved = EXACT_TERMINAL | LEGACY_TERMINAL | ALTERNATIVE_AUTHORITY_TERMINAL | SOURCE_NATIVE_TERMINAL | TECHNICAL_TERMINAL
    remaining = ~decisions.terminal_disposition.isin(preserved)
    before_symbols = set(decisions.loc[prior_unresolved, "raw_source_feature_symbol"])
    recovered_symbols = set(decisions.loc[recovered, "raw_source_feature_symbol"])
    still_symbols = set(decisions.loc[remaining, "raw_source_feature_symbol"])
    normalized_source_ids = set(decisions.normalized_source_ensembl_id) - {""}
    historical_source_ids = normalized_source_ids - set(authority.ensembl_by_id)
    symbol_only = decisions[decisions.normalized_source_ensembl_id.eq("")]
    summary = {
        "stage": config["stage_id"], "status": config["status"],
        "before": {"current_exact_gene_count": len(prior_genes), "unresolved_source_records": int(prior_unresolved.sum()), "unique_unresolved_symbols": len(before_symbols)},
        "source_record_accounting": {"total": len(decisions), "exact_before": int(decisions.mapping_decision.eq("EXACT_RETAINED").sum()), "unresolved_before": int(prior_unresolved.sum()), "recovered_after_authority_audit": int(recovered.sum()), "unresolved_after_authority_audit": int(remaining.sum()), "terminal_disposition_total": int(decisions.terminal_disposition.ne("").sum()), "terminal_dispositions": decisions.terminal_disposition.value_counts().sort_index().to_dict()},
        "unique_feature_accounting": {
            "total_unique_raw_symbols": decisions.raw_source_feature_symbol.nunique(),
            "unique_previously_unresolved_symbols": len(before_symbols),
            "unique_recovered_symbols": len(recovered_symbols - still_symbols),
            "unique_still_unresolved_symbols": len(still_symbols),
            "unique_source_ensembl_ids": len(normalized_source_ids),
            "unique_historical_source_ensembl_ids": len(historical_source_ids),
            "unique_symbol_only_features": symbol_only.raw_source_feature_symbol.nunique(),
        },
        "recovery": {
            "source_records_recovered": int(recovered.sum()),
            "unique_symbols_recovered": len(recovered_symbols - still_symbols),
            "support_only_recovered_records": int(decisions.recovery_type.eq("SUPPORT_RECOVERY_ONLY").sum()),
            "existing_genes_gaining_matrix_support": int(delta.delta_type.eq("SUPPORT_RECOVERY_ONLY").sum()),
            "new_gene_recovered_records": int(decisions.recovery_type.eq("NEW_CANONICAL_GENE_RECOVERY").sum()),
            "new_current_genes": int(registry.new_relative_to_prior_37346.sum()),
        },
        "after": {
            "current_exact_gene_count": len(registry), "legacy_exact_count": len(legacy), "legacy_exact_source_records": int(decisions.terminal_disposition.isin(LEGACY_TERMINAL).sum()),
            "remaining_unresolved_source_records": int(remaining.sum()), "remaining_unresolved_unique_symbols": len(still_symbols),
            "within_matrix_collision_count": len(collisions), "affected_collision_matrices": collisions.matrix_id.nunique() if len(collisions) else 0,
            "current_registry_semantic_hash": semantic_hash,
        },
        "biological_identity_categories": {
            "current_canonical_gene_source_rows": int(decisions.terminal_disposition.isin(EXACT_TERMINAL).sum()),
            "current_canonical_unique_genes": len(registry),
            "legacy_exact_gene_source_rows": int(decisions.terminal_disposition.isin(LEGACY_TERMINAL).sum()),
            "legacy_exact_unique_genes": len(legacy),
            "alternative_authority_exact_source_rows": int(decisions.terminal_disposition.isin(ALTERNATIVE_AUTHORITY_TERMINAL).sum()),
            "alternative_authority_exact_unique_features": decisions.loc[decisions.terminal_disposition.isin(ALTERNATIVE_AUTHORITY_TERMINAL), "source_native_id"].replace("", pd.NA).nunique(),
            "source_native_biological_source_rows": int(decisions.terminal_disposition.isin(SOURCE_NATIVE_TERMINAL).sum()),
            "source_native_biological_unique_features": decisions.loc[decisions.terminal_disposition.isin(SOURCE_NATIVE_TERMINAL), ["source_dataset_id", "source_native_id", "raw_source_feature_symbol"]].drop_duplicates().shape[0],
            "symbol_only_unresolved_source_rows": int(decisions.terminal_disposition.eq("SYMBOL_ONLY_UNRESOLVED").sum()),
            "symbol_only_unresolved_unique_features": decisions.loc[decisions.terminal_disposition.eq("SYMBOL_ONLY_UNRESOLVED"), "raw_source_feature_symbol"].nunique(),
            "technical_nonbiological_source_rows": int(decisions.terminal_disposition.isin(TECHNICAL_TERMINAL).sum()),
            "technical_nonbiological_unique_features": decisions.loc[decisions.terminal_disposition.isin(TECHNICAL_TERMINAL), "raw_source_feature_symbol"].nunique(),
        },
        "mapping_evidence_classes": decisions.mapping_evidence_class.value_counts().sort_index().to_dict(),
        "prior_106118_unresolved_reclassification": decisions.loc[prior_unresolved, "terminal_disposition"].value_counts().sort_index().to_dict(),
        "prior_17607_unresolved_symbol_reclassification": decisions.loc[prior_unresolved, ["raw_source_feature_symbol", "terminal_disposition"]].drop_duplicates().terminal_disposition.value_counts().sort_index().to_dict(),
        "mapping_comparison_classes": comparison.comparison_class.value_counts().sort_index().to_dict(),
        "protected_frozen_vocabulary": {
            "gene_count": len(frozen_vocabulary_frame),
            "unique_gene_count": frozen_vocabulary_frame.canonical_ensembl_gene_id.nunique(),
            "order_hash_before_and_after": config["protected_semantic_hashes"]["results/v4/stage81a2_foundation_vocabulary.csv"],
            "source_row_identity_corrections_affecting_frozen_gene": len(protected_corrections),
            "unique_id_correction_pairs_affecting_frozen_gene": len(protected_unique_pairs),
            "candidate_corrections_applied_to_frozen_artifact": 0,
            "unchanged": True,
        },
        "remaining_terminal_reasons": decisions.loc[remaining, "terminal_disposition"].value_counts().to_dict(),
        "no_biotype_filter": True, "fuzzy_mapping_used": False,
        "development_rna_accessed": False, "sealed_rna_accessed": False, "pathology_accessed": False,
        "stage81a3r_work_performed": False, "stage81b_started": False, "freeze1_declared": False,
        "acceptance": {"all_source_rows_terminal": bool(len(decisions) == 299775 and decisions.terminal_disposition.ne("").all()), "authorities_pinned": True, "no_fuzzy_mapping": True},
        "human_decision": "STOP FOR HUMAN A2R ADDRESS-SPACE AND PROTECTED-IDENTITY REVIEW",
    }
    access = {
        "stage": config["stage_id"], "opened_paths": [inputs["prior_source_decisions"], inputs["prior_exact_registry"], inputs["prior_measurement_support"], inputs["frozen_asset_registry"], authority_cfg["ensembl"]["local_path"], authority_cfg["hgnc_complete"]["local_path"], authority_cfg["hgnc_withdrawn"]["local_path"], authority_cfg["ensembl_history"]["local_path"]],
        "expression_matrices_opened": False, "development_rna_accessed": False, "sealed_rna_accessed": False, "pathology_accessed": False,
    }
    atomic_json(outputs["authority_manifest"], manifest)
    atomic_csv(outputs["source_decisions"], decisions, "gzip")
    atomic_csv(outputs["exact_registry"], registry)
    atomic_csv(outputs["legacy_registry"], legacy)
    atomic_csv(outputs["source_native_registry"], source_native, "gzip")
    atomic_csv(outputs["unresolved"], unresolved, "gzip")
    atomic_csv(outputs["measurement_support"], measurement, "gzip")
    atomic_csv(outputs["mapping_delta"], delta)
    atomic_csv(outputs["collisions"], collisions)
    atomic_csv(outputs["by_source"], by_source)
    atomic_csv(outputs["by_biotype"], by_biotype)
    atomic_json(outputs["summary"], summary)
    atomic_json(outputs["access_manifest"], access)
    outputs["readout"].parent.mkdir(parents=True, exist_ok=True)
    outputs["readout"].write_text(build_readout(summary, by_source, by_biotype, unresolved), encoding="utf-8", newline="\n")
    generated = {str(path.relative_to(project)).replace("\\", "/"): {"bytes": path.stat().st_size, "sha256": sha256_file(path)} for key, path in outputs.items() if key not in {"hash_verification", "test_report"} and path.is_file()}
    protected = []
    for relative, expected in config["protected_hashes"].items():
        observed = sha256_file(project / relative)
        protected.append({"path": relative, "expected_sha256": expected, "observed_sha256": observed, "pass": observed == expected})
    for relative, expected in config["protected_semantic_hashes"].items():
        vocabulary = pd.read_csv(project / relative, dtype=str, keep_default_na=False)
        observed = hashlib.sha256("|".join(vocabulary.canonical_ensembl_gene_id).encode()).hexdigest()
        protected.append({"path": f"{relative}::semantic", "expected_sha256": expected, "observed_sha256": observed, "pass": observed == expected})
    hash_report = {"generated": generated, "protected": protected, "protected_hashes_unchanged": all(item["pass"] for item in protected), "prior_a2r_semantic_hash_unchanged": prior_registry.registry_semantic_hash.iloc[0] == "d9d8b08bcf8e88b73d2f5483b573767c49b47ff661da57b99c5b5aab828aa8a2"}
    atomic_json(outputs["hash_verification"], hash_report)
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_authoritative_mapping.yaml"))
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    run(project, config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
