"""Bounded project-wide adjudication of Stage81A2R unresolved identities."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import h5py
import pandas as pd
import yaml

from sea_ad_jepa.v4.gene_identity_authority import (
    AuthorityIndex,
    build_authority_index,
    classify_symbol_only,
    history_current_replacements,
    load_history_cache,
    normalize_ensembl_gene_id,
)
from scripts.v4.stage81a2r_authoritative_gene_identity_recovery import (
    atomic_csv,
    atomic_json,
    sha256_file,
)


FINAL_AMBIGUOUS = {
    "AMBIGUOUS_HISTORY",
    "AMBIGUOUS_ALIAS",
    "AMBIGUOUS_MULTIPLE_CURRENT_GENES",
    "ASSEMBLY_UNRESOLVED",
    "TRULY_SYMBOL_ONLY_UNRESOLVED",
}
RECOVERED = {
    "CURRENT_ENSEMBL_RECOVERED",
    "HISTORICAL_ENSEMBL_UNIQUE_CURRENT_RECOVERY",
    "SOURCE_EXACT_ALT_LOCUS_SAME_GENE",
    "SOURCE_EXACT_NONPRIMARY_ENSEMBL_SAME_GENE",
    "EXACT_NCBI_GENE_RECOVERED",
    "EXACT_REFSEQ_RECOVERED",
    "EXACT_GENCODE_RECOVERED",
    "SOURCE_ERA_EXACT_RECOVERED",
    "SOURCE_ERA_RECONSTRUCTED",
}
SOURCE_NATIVE = {
    "SOURCE_NATIVE_GENOMIC_LOCUS",
    "SOURCE_NATIVE_TRANSCRIPT_MODEL",
    "SOURCE_ANNOTATED_NOVEL_OR_PREDICTED_GENE",
    "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED",
}

TECHNICAL_RE = re.compile(
    r"^(?:ENTREZID|UniqueID|Blank-?\d+|NegControl.*|NegativeControl.*|ERCC-.*|__.*|"
    r"Gran_[A-Za-z0-9]+_[ACGT]{8,}|Ex\d+_[A-Za-z0-9]+_[ACGT]{8,}|"
    r"In\d+_[A-Za-z0-9]+_[ACGT]{8,}|Ast_[A-Za-z0-9]+_[ACGT]{8,}|"
    r"Oli_[A-Za-z0-9]+_[ACGT]{8,}|Mic_[A-Za-z0-9]+_[ACGT]{8,})$",
    re.IGNORECASE,
)
MIRBASE_RE = re.compile(r"^MIMAT\d+$", re.IGNORECASE)


def joined(values: Any) -> str:
    return "|".join(sorted({str(value) for value in values if str(value)}))


def stable_id(value: Any) -> str:
    normalized = normalize_ensembl_gene_id(value)
    return normalized[0] if normalized else ""


def semantic_hash(values: list[str]) -> str:
    return hashlib.sha256("|".join(values).encode()).hexdigest()


def split_values(value: Any) -> list[str]:
    text = "" if value is None else str(value)
    return [item.strip() for item in re.split(r"[|,]", text) if item.strip()]


def unique_map(pairs: list[tuple[str, str]]) -> dict[str, str]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for key, value in pairs:
        if key and value:
            grouped[key].add(value)
    return {key: next(iter(values)) for key, values in grouped.items() if len(values) == 1}


def load_alternative_authorities(path: Path, current_ids: set[str]) -> dict[str, dict[str, str]]:
    hgnc = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    valid = hgnc[hgnc.ensembl_gene_id.isin(current_ids)]
    ncbi_pairs: list[tuple[str, str]] = []
    refseq_pairs: list[tuple[str, str]] = []
    mirbase_pairs: list[tuple[str, str]] = []
    for row in valid.itertuples(index=False):
        ncbi_pairs.extend((item, row.ensembl_gene_id) for item in split_values(row.entrez_id))
        refseq_pairs.extend((item.split(".", 1)[0], row.ensembl_gene_id) for item in split_values(row.refseq_accession))
        mirbase_pairs.extend((item, row.ensembl_gene_id) for item in split_values(row.mirbase))
    return {
        "ncbi": unique_map(ncbi_pairs),
        "refseq": unique_map(refseq_pairs),
        "mirbase_gene": unique_map(mirbase_pairs),
    }


def load_source_exact_symbol_map(projectwide: pd.DataFrame) -> dict[tuple[str, str], str]:
    exact = projectwide[
        projectwide.mapping_evidence_class.eq("SOURCE_EXACT")
        & projectwide.current_ensembl_gene_id.ne("")
    ]
    pairs: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in exact.itertuples(index=False):
        for value in (row.raw_feature_id, row.raw_gene_symbol):
            if value:
                pairs[(row.dataset_id, value)].add(row.current_ensembl_gene_id)
    return {key: next(iter(values)) for key, values in pairs.items() if len(values) == 1}


def decode(values: Any) -> list[str]:
    return [item.decode() if isinstance(item, bytes) else str(item) for item in values]


def build_source_overrides(project: Path, unresolved: pd.DataFrame) -> dict[tuple[str, str, int], dict[str, str]]:
    """Recover source-local fields without reading expression values."""
    overrides: dict[tuple[str, str, int], dict[str, str]] = {}

    # GSE241858 supplies exact Entrez IDs and symbols in the first two columns.
    for matrix_id in unresolved.loc[unresolved.dataset_id.eq("GSE241858"), "matrix_id"].unique():
        path = project / matrix_id
        with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for index, row in enumerate(reader):
                overrides[("GSE241858", matrix_id, index)] = {
                    "source_feature_id_raw": row.get("ENTREZID", ""),
                    "source_symbol_raw": row.get("SYMBOL", ""),
                    "source_ncbi_gene_id": row.get("ENTREZID", ""),
                    "evidence_file": matrix_id,
                    "mapping_authority": "GEO source table ENTREZID and SYMBOL columns",
                }

    # GSE243292 stores exact Ensembl IDs in var/Ensembl; the old reader missed case-sensitive field names.
    matrix_ids = unresolved.loc[unresolved.dataset_id.eq("GSE243292"), "matrix_id"].unique()
    for matrix_id in matrix_ids:
        cache = project / "data/external/v4/gene_identity_authority/container_cache" / Path(matrix_id).name[:-3]
        with h5py.File(cache, "r") as handle:
            ids = decode(handle["var/Ensembl"][:])
            names = decode(handle["var/genename"][:])
        for index, (ensembl, name) in enumerate(zip(ids, names)):
            overrides[("GSE243292", matrix_id, index)] = {
                "source_feature_id_raw": ensembl,
                "source_symbol_raw": name,
                "source_ensembl_id_raw": ensembl,
                "evidence_file": matrix_id + "::var/Ensembl",
                "mapping_authority": "source H5AD var/Ensembl",
            }

    # SCP2167 expression rows are positionally paired to its source 10x feature dictionary.
    feature_path = project / "data/external/v4/stage81a3_context/SCP2167_slidetags_PFC/SCP2167/10x_genes_file/lld_features.tsv.gz"
    if feature_path.exists():
        with gzip.open(feature_path, "rt", encoding="utf-8", newline="") as handle:
            features = list(csv.reader(handle, delimiter="\t"))
        for matrix_id in unresolved.loc[unresolved.dataset_id.eq("SCP2167_slidetags_PFC"), "matrix_id"].unique():
            if "expression/" not in matrix_id.replace("\\", "/"):
                continue
            for index, fields in enumerate(features):
                overrides[("SCP2167_slidetags_PFC", matrix_id, index)] = {
                    "source_feature_id_raw": fields[1],
                    "source_symbol_raw": fields[1],
                    "source_ensembl_id_raw": fields[0],
                    "evidence_file": str(feature_path.relative_to(project)).replace("\\", "/"),
                    "mapping_authority": "source-local 10x ordered feature dictionary",
                }

        # GSE301119 CRISPRi carries the same complete ordered 36,601-feature
        # reference fingerprint. Require every position to agree; the ten
        # known duplicated-gene labels add only the source's explicit `.1`.
        r_cache = project / "data/external/v4/gene_identity_authority/r_feature_cache/GSE301119_CRISPRi_seurat5.rds.features.tsv.gz"
        if r_cache.exists():
            source = pd.read_csv(r_cache, sep="\t", dtype=str, keep_default_na=False)
            source_names = source.raw_gene_symbol.tolist()
            reference_names = [fields[1] for fields in features]
            positional_agreement = [left == right or left == f"{right}.1" for left, right in zip(source_names, reference_names)]
            if len(source_names) != len(features) or not all(positional_agreement):
                raise RuntimeError("GSE301119 CRISPRi no longer matches the exact ordered 36,601-feature reference fingerprint")
            for matrix_id in unresolved.loc[
                unresolved.dataset_id.eq("GSE301119")
                & unresolved.matrix_id.str.contains("CRISPRi_seurat5", regex=False),
                "matrix_id",
            ].unique():
                for index, fields in enumerate(features):
                    overrides[("GSE301119", matrix_id, index)] = {
                        "source_feature_id_raw": source_names[index],
                        "source_symbol_raw": source_names[index],
                        "source_ensembl_id_raw": fields[0],
                        "evidence_file": str(feature_path.relative_to(project)).replace("\\", "/"),
                        "mapping_authority": "exact ordered 36,601-feature 10x reference fingerprint",
                    }

    # miRNA assay tables expose exact mature-miRNA MIMAT accessions.
    for matrix_id in unresolved.loc[unresolved.dataset_id.eq("GSE305625"), "matrix_id"].unique():
        path = project / matrix_id
        with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            overrides[("GSE305625", matrix_id, 0)] = {
                "source_feature_id_raw": "UniqueID",
                "source_symbol_raw": "UniqueID",
                "evidence_file": matrix_id,
                "mapping_authority": "source miRNA assay header",
            }
            for index, row in enumerate(reader, start=1):
                overrides[("GSE305625", matrix_id, index)] = {
                    "source_feature_id_raw": row.get("UniqueID", ""),
                    "source_symbol_raw": row.get("Assay Name", ""),
                    "source_mirbase_id": row.get("mirBase V21 Name", ""),
                    "evidence_file": matrix_id,
                    "mapping_authority": "source miRBase v21 assay annotation",
                }
    return overrides


def ambiguity_class(old: str) -> str:
    if "ALIAS" in old or "PREVIOUS_SYMBOL" in old:
        return "AMBIGUOUS_ALIAS"
    if "MULTIPLE" in old or old == "CONFLICTING_AUTHORITATIVE_IDENTITY":
        return "AMBIGUOUS_MULTIPLE_CURRENT_GENES"
    if "HISTORY" in old or "LEGACY" in old:
        return "AMBIGUOUS_HISTORY"
    return "TRULY_SYMBOL_ONLY_UNRESOLVED"


def classify_one(
    row: pd.Series,
    authority: AuthorityIndex,
    history: dict[str, dict[str, Any]],
    alternatives: dict[str, dict[str, str]],
    source_exact: dict[tuple[str, str], str],
    override: dict[str, str],
) -> dict[str, Any]:
    raw_id = override.get("source_feature_id_raw", row.raw_feature_id)
    raw_symbol = override.get("source_symbol_raw", row.raw_gene_symbol)
    source_ensembl = override.get("source_ensembl_id_raw", row.source_ensembl_id)
    source_ncbi = override.get("source_ncbi_gene_id", row.source_ncbi_gene_id)
    source_refseq = override.get("source_refseq_id", row.source_refseq_id)
    source_gencode = override.get("source_gencode_id", "")
    source_transcript = override.get("source_transcript_id", row.source_transcript_id)
    source_mirbase = override.get("source_mirbase_id", "")
    evidence_file = override.get("evidence_file", row.matrix_id)
    source_symbol = raw_symbol
    if row.dataset_id == "GSE240609" and str(raw_symbol).isdigit():
        source_symbol = raw_id

    result = {
        "source_feature_id_raw": raw_id,
        "source_symbol_raw": source_symbol,
        "source_ensembl_id_raw": source_ensembl,
        "source_ncbi_gene_id": source_ncbi,
        "source_refseq_id": source_refseq,
        "source_gencode_id": source_gencode,
        "source_transcript_id": source_transcript,
        "source_mirbase_id": source_mirbase,
        "new_terminal_disposition": "",
        "recovered_canonical_ensembl_id": "",
        "canonical_symbol": "",
        "mapping_evidence_class": "",
        "mapping_authority": override.get("mapping_authority", ""),
        "evidence_file": evidence_file,
        "evidence_reason": "",
        "ambiguity_reason": "",
        "automatic_fix_safe": False,
        "human_review_required": False,
        "notes": "",
    }

    if TECHNICAL_RE.fullmatch(raw_id or source_symbol):
        result.update(new_terminal_disposition="NON_BIOLOGICAL_TECHNICAL_FEATURE", mapping_evidence_class="SOURCE_EXACT_TECHNICAL", evidence_reason="exact source control/header/cell-barcode feature identity")
        return result

    normalized = normalize_ensembl_gene_id(source_ensembl)
    if normalized and normalized[0] in authority.ensembl_by_id:
        result.update(new_terminal_disposition="CURRENT_ENSEMBL_RECOVERED", recovered_canonical_ensembl_id=normalized[0], mapping_evidence_class="SOURCE_EXACT", evidence_reason="exact source Ensembl gene ID is current")
    elif normalized:
        replacements = history_current_replacements(history.get(normalized[0], {}), set(authority.ensembl_by_id))
        if len(replacements) == 1:
            result.update(new_terminal_disposition="HISTORICAL_ENSEMBL_UNIQUE_CURRENT_RECOVERY", recovered_canonical_ensembl_id=replacements[0], mapping_evidence_class="SOURCE_EXACT_HISTORY", evidence_reason="pinned Ensembl history gives one current continuation")
        elif len(replacements) > 1:
            result.update(new_terminal_disposition="AMBIGUOUS_HISTORY", mapping_evidence_class="SOURCE_EXACT_HISTORY", ambiguity_reason="historical Ensembl ID has multiple current replacements", human_review_required=True)
        else:
            result.update(new_terminal_disposition="SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED", mapping_evidence_class="SOURCE_EXACT_HISTORY", evidence_reason="exact historical Ensembl identity has no unique current projection")
    elif source_ncbi and source_ncbi in alternatives["ncbi"]:
        result.update(new_terminal_disposition="EXACT_NCBI_GENE_RECOVERED", recovered_canonical_ensembl_id=alternatives["ncbi"][source_ncbi], mapping_evidence_class="EXACT_NCBI_GENE", mapping_authority="HGNC 2026-08 exact NCBI Gene cross-reference", evidence_reason="exact source NCBI Gene ID uniquely maps to one current HGNC Ensembl gene")
    elif source_ncbi and source_ncbi.isdigit():
        result.update(new_terminal_disposition="SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED", mapping_evidence_class="EXACT_NCBI_GENE", mapping_authority="source table NCBI Gene namespace", evidence_reason="exact source NCBI Gene identity preserved; no unique current HGNC-Ensembl projection is available")
    elif source_refseq and source_refseq.split(".", 1)[0] in alternatives["refseq"]:
        result.update(new_terminal_disposition="EXACT_REFSEQ_RECOVERED", recovered_canonical_ensembl_id=alternatives["refseq"][source_refseq.split(".", 1)[0]], mapping_evidence_class="EXACT_REFSEQ", mapping_authority="HGNC 2026-08 exact RefSeq cross-reference", evidence_reason="exact source RefSeq accession uniquely maps to one current HGNC Ensembl gene")
    elif source_refseq and re.fullmatch(r"(?:NM|NR|XM|XR)_\d+(?:\.\d+)?", source_refseq):
        result.update(new_terminal_disposition="SOURCE_NATIVE_TRANSCRIPT_MODEL", mapping_evidence_class="EXACT_REFSEQ", mapping_authority="source table RefSeq namespace", evidence_reason="exact RefSeq accession preserved; no unique current HGNC-Ensembl projection is available")
    elif source_gencode and stable_id(source_gencode) in authority.ensembl_by_id:
        result.update(new_terminal_disposition="EXACT_GENCODE_RECOVERED", recovered_canonical_ensembl_id=stable_id(source_gencode), mapping_evidence_class="EXACT_GENCODE", evidence_reason="exact source GENCODE gene ID is a current Ensembl gene")
    elif source_mirbase and MIRBASE_RE.fullmatch(source_mirbase):
        result.update(new_terminal_disposition="SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED", mapping_evidence_class="SOURCE_EXACT_MIRBASE", evidence_reason="exact mature-miRNA miRBase accession preserved without forcing a protein-coding gene projection")
    elif (row.dataset_id, raw_id) in source_exact:
        result.update(new_terminal_disposition="SOURCE_ERA_EXACT_RECOVERED", recovered_canonical_ensembl_id=source_exact[(row.dataset_id, raw_id)], mapping_evidence_class="SOURCE_LOCAL_EXACT", evidence_reason="same dataset supplies this exact source identity with a stable current Ensembl anchor")
    elif (row.dataset_id, source_symbol) in source_exact:
        result.update(new_terminal_disposition="SOURCE_ERA_EXACT_RECOVERED", recovered_canonical_ensembl_id=source_exact[(row.dataset_id, source_symbol)], mapping_evidence_class="SOURCE_LOCAL_EXACT", evidence_reason="same dataset supplies this exact source symbol with a stable current Ensembl anchor")
    elif row.dataset_id == "SCP2167_slidetags_PFC" and override.get("source_ensembl_id_raw"):
        # This branch is normally handled above; it documents positional source-dictionary recovery explicitly.
        result.update(new_terminal_disposition="SOURCE_ERA_RECONSTRUCTED", recovered_canonical_ensembl_id=stable_id(override["source_ensembl_id_raw"]), mapping_evidence_class="SOURCE_LOCAL_ORDERED_DICTIONARY", evidence_reason="exact source-local ordered 10x dictionary supplies the stable ID")
    elif row.modality == "miRNA" or raw_id.endswith("_gene"):
        result.update(new_terminal_disposition="SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED", mapping_evidence_class="SOURCE_NATIVE_EXACT", evidence_reason="source-native assay/panel biological identity preserved; no unique canonical projection established")
    else:
        status, canonical, _ = classify_symbol_only(source_symbol or raw_id, authority)
        if canonical:
            result.update(new_terminal_disposition="CURRENT_ENSEMBL_RECOVERED", recovered_canonical_ensembl_id=canonical, mapping_evidence_class="PINNED_HGNC_ENSEMBL", mapping_authority="Ensembl 116 and HGNC 2026-08", evidence_reason=f"exact authority match: {status}")
        elif status.startswith("AMBIGUOUS") or status == "CONFLICTING_AUTHORITATIVE_IDENTITY":
            result.update(new_terminal_disposition=ambiguity_class(status), mapping_evidence_class="PINNED_HGNC_ENSEMBL", ambiguity_reason=status, human_review_required=True)
        else:
            result.update(new_terminal_disposition=ambiguity_class(row.terminal_disposition), mapping_evidence_class="SOURCE_SYMBOL_ONLY", ambiguity_reason="no exact source-native, current Ensembl, unique HGNC, NCBI, RefSeq, GENCODE, transcript, or coordinate anchor")

    canonical = result["recovered_canonical_ensembl_id"]
    if canonical:
        result["canonical_symbol"] = authority.ensembl_by_id[canonical].symbol
        result["automatic_fix_safe"] = True
    elif result["new_terminal_disposition"] in SOURCE_NATIVE | {"NON_BIOLOGICAL_TECHNICAL_FEATURE"}:
        result["automatic_fix_safe"] = True
    return result


def reclassify(
    unresolved: pd.DataFrame,
    projectwide: pd.DataFrame,
    authority: AuthorityIndex,
    history: dict[str, dict[str, Any]],
    alternatives: dict[str, dict[str, str]],
    overrides: dict[tuple[str, str, int], dict[str, str]],
) -> pd.DataFrame:
    source_exact = load_source_exact_symbol_map(projectwide)
    rows = []
    frozen = set(pd.read_csv("results/v4/stage81a2_foundation_vocabulary.csv", dtype=str, keep_default_na=False).canonical_ensembl_gene_id)
    for row in unresolved.itertuples(index=False):
        series = pd.Series(row._asdict())
        key = (row.dataset_id, row.matrix_id, int(row.source_feature_index))
        decision = classify_one(series, authority, history, alternatives, source_exact, overrides.get(key, {}))
        rows.append({
            "dataset": row.dataset_id,
            "source_file": row.matrix_id.split("::", 1)[0],
            "matrix_id": row.matrix_id,
            "feature_universe_id": row.feature_universe_sha256,
            "source_feature_index": row.source_feature_index,
            "source_feature_id_raw": decision["source_feature_id_raw"],
            "source_symbol_raw": decision["source_symbol_raw"],
            "source_ensembl_id_raw": decision["source_ensembl_id_raw"],
            "source_ncbi_gene_id": decision["source_ncbi_gene_id"],
            "source_refseq_id": decision["source_refseq_id"],
            "source_gencode_id": decision["source_gencode_id"],
            "source_transcript_id": decision["source_transcript_id"],
            "source_mirbase_id": decision["source_mirbase_id"],
            "source_chr": row.source_chromosome,
            "source_start": row.source_start,
            "source_end": row.source_end,
            "source_strand": row.source_strand,
            "source_biotype": row.source_biotype,
            "source_assembly": row.source_annotation_authority,
            "modality": row.modality,
            "source_matrix_multiplicity": row.source_matrix_multiplicity,
            "old_terminal_disposition": row.terminal_disposition,
            **decision,
            "protected_4096": decision["recovered_canonical_ensembl_id"] in frozen,
        })
    frame = pd.DataFrame(rows)
    frame["source_feature_index"] = pd.to_numeric(frame.source_feature_index, errors="raise").astype(int)
    return frame.sort_values(["dataset", "matrix_id", "source_feature_index"]).reset_index(drop=True)


def build_unique_summary(frame: pd.DataFrame) -> pd.DataFrame:
    keys = ["dataset", "source_feature_id_raw", "source_symbol_raw", "source_ensembl_id_raw", "source_ncbi_gene_id", "source_refseq_id", "source_gencode_id", "source_transcript_id", "source_mirbase_id", "new_terminal_disposition", "recovered_canonical_ensembl_id"]
    grouped = frame.groupby(keys, dropna=False, sort=True)
    return grouped.agg(
        materialized_source_rows=("matrix_id", "size"),
        source_row_equivalents=("source_matrix_multiplicity", lambda values: int(pd.to_numeric(values).sum())),
        matrix_count=("matrix_id", "nunique"),
        feature_universe_count=("feature_universe_id", "nunique"),
        evidence_files=("evidence_file", joined),
        evidence_reasons=("evidence_reason", joined),
        ambiguity_reasons=("ambiguity_reason", joined),
        protected_4096=("protected_4096", "max"),
        automatic_fix_safe=("automatic_fix_safe", "min"),
        human_review_required=("human_review_required", "max"),
    ).reset_index()


def adjudicate_protected_dossier(dossier: pd.DataFrame, hgnc_path: Path) -> pd.DataFrame:
    hgnc = pd.read_csv(hgnc_path, sep="\t", dtype=str, keep_default_na=False)
    by_symbol = {row.symbol: row for row in hgnc.itertuples(index=False)}
    result = dossier.copy()
    result["protected_identity_decision"] = result.required_action
    result["protected_identity_evidence"] = "prior Stage81A2R evidence unchanged"
    result["remaining_human_blocker"] = result.human_a2r_decision_required
    for index, row in result.iterrows():
        if row.identity_change_classification != "SYMBOL_ONLY":
            continue
        record = by_symbol.get(row.frozen_symbols)
        source_ids = split_values(row.source_exact_ensembl_ids)
        source_ncbi = split_values(row.supporting_ncbi_gene_ids)
        alt_contig = any(value.startswith("CHR_HSCHR") for value in split_values(row.supporting_source_chromosomes))
        exact_same_gene = record and len(source_ids) == 1 and record.ensembl_gene_id == row.previous_canonical_ensembl_id and record.entrez_id in source_ncbi
        if exact_same_gene:
            classification = "SOURCE_EXACT_ALT_LOCUS_SAME_GENE" if alt_contig else "SOURCE_EXACT_NONPRIMARY_ENSEMBL_SAME_GENE"
            result.loc[index, "identity_change_classification"] = classification
            result.loc[index, "protected_identity_decision"] = "KEEP_FROZEN_ALT_LOCUS_SOURCE_ALIAS"
            location = "lies on an alternate contig and " if alt_contig else "is a distinct source Ensembl representation that "
            result.loc[index, "protected_identity_evidence"] = f"exact source {source_ids[0]} {location}shares NCBI Gene {record.entrez_id} with frozen HGNC canonical {record.ensembl_gene_id}"
            result.loc[index, "remaining_human_blocker"] = False
            result.loc[index, "human_a2r_decision_required"] = False
            result.loc[index, "required_action"] = "KEEP_FROZEN_ALT_LOCUS_SOURCE_ALIAS"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_authoritative_mapping.yaml"))
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    outputs = {key: project / value for key, value in config["outputs"].items()}

    unresolved = pd.read_csv(outputs["projectwide_unresolved"], dtype=str, keep_default_na=False, low_memory=False)
    projectwide = pd.read_csv(outputs["projectwide_feature_identity"], dtype=str, keep_default_na=False, low_memory=False)
    datasets = pd.read_csv(outputs["projectwide_dataset_summary"], dtype=str, keep_default_na=False)
    prior_report = json.loads(outputs["projectwide_final_report"].read_text(encoding="utf-8"))
    if len(unresolved) != 277352 or unresolved.dataset_id.nunique() != 16:
        raise RuntimeError(f"project-wide unresolved scope drift: rows={len(unresolved)} datasets={unresolved.dataset_id.nunique()}")
    if prior_report["scope"]["scientific_datasets"] != 47:
        raise RuntimeError("project-wide dataset scope no longer reconciles to 47 datasets")

    authority = build_authority_index(project / config["authorities"]["ensembl"]["local_path"], project / config["authorities"]["hgnc_complete"]["local_path"], project / config["authorities"]["hgnc_withdrawn"]["local_path"])
    history = load_history_cache(project / config["authorities"]["ensembl_history"]["local_path"])
    alternatives = load_alternative_authorities(project / config["authorities"]["hgnc_complete"]["local_path"], set(authority.ensembl_by_id))
    overrides = build_source_overrides(project, unresolved)
    frame = reclassify(unresolved, projectwide, authority, history, alternatives, overrides)
    unique = build_unique_summary(frame)

    remaining = frame[frame.new_terminal_disposition.isin(FINAL_AMBIGUOUS)].copy()
    evidence = frame[~frame.new_terminal_disposition.isin(FINAL_AMBIGUOUS)].copy()
    dataset_rows = []
    for row in datasets.itertuples(index=False):
        subset = unique[unique.dataset.eq(row.dataset)]
        counts = Counter(subset.new_terminal_disposition)
        source_subset = frame[frame.dataset.eq(row.dataset)]
        dataset_rows.append({
            "dataset_id": row.dataset, "modality": row.modality,
            "matrix_count": int(row.matrix_count), "feature_universe_count": int(row.unique_feature_universes),
            "raw_source_row_count": int(row.source_row_equivalent_count),
            "previously_unresolved_source_rows": int(pd.to_numeric(source_subset.source_matrix_multiplicity).sum()) if len(source_subset) else 0,
            "previously_unresolved_unique_identities": len(subset),
            "recovered_exact_current": int(sum(counts[name] for name in {"CURRENT_ENSEMBL_RECOVERED", "SOURCE_ERA_EXACT_RECOVERED", "SOURCE_ERA_RECONSTRUCTED"})),
            "recovered_historical": int(counts["HISTORICAL_ENSEMBL_UNIQUE_CURRENT_RECOVERY"]),
            "recovered_alt_locus": int(counts["SOURCE_EXACT_ALT_LOCUS_SAME_GENE"] + counts["SOURCE_EXACT_NONPRIMARY_ENSEMBL_SAME_GENE"]),
            "recovered_ncbi_refseq_gencode": int(counts["EXACT_NCBI_GENE_RECOVERED"] + counts["EXACT_REFSEQ_RECOVERED"] + counts["EXACT_GENCODE_RECOVERED"]),
            "source_native_identified_unprojected": int(sum(counts[name] for name in SOURCE_NATIVE)),
            "ambiguous_remaining": int(sum(counts[name] for name in FINAL_AMBIGUOUS - {"TRULY_SYMBOL_ONLY_UNRESOLVED"})),
            "truly_identifier_poor_remaining": int(counts["TRULY_SYMBOL_ONLY_UNRESOLVED"]),
            "technical_features": int(counts["NON_BIOLOGICAL_TECHNICAL_FEATURE"]),
        })
    dataset_summary = pd.DataFrame(dataset_rows).sort_values("dataset_id").reset_index(drop=True)

    dossier = pd.read_csv(outputs["protected_identity_dossier"], dtype=str, keep_default_na=False)
    protected = adjudicate_protected_dossier(dossier, project / config["authorities"]["hgnc_complete"]["local_path"])
    remaining_protected = int(protected.remaining_human_blocker.astype(str).str.lower().eq("true").sum())

    old_registry = pd.read_csv(outputs["exact_registry"], dtype=str, keep_default_na=False)
    old_ids = old_registry.canonical_ensembl_gene_id.tolist()
    foundation_recovered = set(frame.loc[frame.dataset.isin({"SEA_AD", "HVS", "NPH52"}) & frame.recovered_canonical_ensembl_id.ne(""), "recovered_canonical_ensembl_id"])
    new_only = sorted(foundation_recovered - set(old_ids))
    comparison = pd.DataFrame([
        {"comparison": "OLD_CANDIDATE_FOUNDATION_CURRENT_GENES", "gene_count": len(old_ids), "semantic_hash": semantic_hash(old_ids), "details": "unchanged authoritative candidate"},
        {"comparison": "NEWLY_RECOVERED_GENES", "gene_count": len(new_only), "semantic_hash": semantic_hash(new_only), "details": joined(new_only)},
        {"comparison": "CANDIDATE_AFTER_BOUNDED_REPAIR", "gene_count": len(set(old_ids) | foundation_recovered), "semantic_hash": semantic_hash(sorted(set(old_ids) | foundation_recovered)), "details": "candidate comparison only; frozen vocabulary not modified"},
    ])

    class_counts_rows = frame.new_terminal_disposition.value_counts().sort_index().to_dict()
    class_counts_source_equivalents = (
        frame.assign(source_matrix_multiplicity=pd.to_numeric(frame.source_matrix_multiplicity))
        .groupby("new_terminal_disposition").source_matrix_multiplicity.sum().astype(int).sort_index().to_dict()
    )
    class_counts_unique = unique.new_terminal_disposition.value_counts().sort_index().to_dict()
    recovered_unique = int(unique.new_terminal_disposition.isin(RECOVERED).sum())
    identified_native_unique = int(unique.new_terminal_disposition.isin(SOURCE_NATIVE).sum())
    ambiguous_unique = int(unique.new_terminal_disposition.isin(FINAL_AMBIGUOUS - {"TRULY_SYMBOL_ONLY_UNRESOLVED"}).sum())
    truly_unique = int(unique.new_terminal_disposition.eq("TRULY_SYMBOL_ONLY_UNRESOLVED").sum())
    technical_unique = int(unique.new_terminal_disposition.eq("NON_BIOLOGICAL_TECHNICAL_FEATURE").sum())
    biological_identifiable_unique = recovered_unique + identified_native_unique
    safely_mapped_unique = int(unique.recovered_canonical_ensembl_id.ne("").sum())
    genuinely_unresolved_unique = ambiguous_unique + truly_unique
    recovered_canonical_genes = int(unique.recovered_canonical_ensembl_id.replace("", pd.NA).nunique())
    unresolved_by_dataset = (
        unique[unique.new_terminal_disposition.isin(FINAL_AMBIGUOUS)]
        .groupby("dataset").size().sort_values(ascending=False).astype(int).to_dict()
    )
    frozen_vocab = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv", dtype=str, keep_default_na=False)
    protected_hashes = []
    for relative_path, expected in config["protected_hashes"].items():
        observed = sha256_file(project / relative_path)
        protected_hashes.append({"path": relative_path, "expected": expected, "observed": observed, "pass": observed == expected})
    frozen_semantic = semantic_hash(frozen_vocab.canonical_ensembl_gene_id.tolist())
    summary = {
        "stage": "stage81a2r_projectwide_unresolved_identity_adjudication",
        "status": "UNRESOLVED_IDENTITY_AUDIT_COMPLETE_WITH_HUMAN_BLOCKERS" if remaining_protected else "UNRESOLVED_IDENTITY_AUDIT_COMPLETE",
        "scope": {
            "scientific_datasets": int(prior_report["scope"]["scientific_datasets"]),
            "datasets_with_unresolved_rows": int(unresolved.dataset_id.nunique()),
            "unresolved_materialized_rows": len(unresolved),
            "unresolved_source_row_equivalents": int(pd.to_numeric(unresolved.source_matrix_multiplicity).sum()),
            "old_projectwide_unique_symbols": int(unresolved.raw_gene_symbol.replace("", pd.NA).nunique()),
            "old_foundation_only_unique_symbols": int(prior_report["foundation_identity_categories"]["symbol_only_unresolved_unique_features"]),
            "adjudicated_unique_source_identities": len(unique),
            "scope_reconciliation_note": "2,010 was the foundation-only unresolved count; the complete project-wide ledger is the governing scope.",
        },
        "materialized_source_row_counts": class_counts_rows,
        "source_row_equivalent_counts": class_counts_source_equivalents,
        "unique_identity_counts": class_counts_unique,
        "answers": {
            "actually_biologically_identifiable_unique": biological_identifiable_unique,
            "safely_mapped_current_ensembl_unique_source_identities": safely_mapped_unique,
            "unique_current_ensembl_genes_represented_by_safe_mappings": recovered_canonical_genes,
            "identified_source_native_noncanonical_unique": identified_native_unique,
            "ambiguous_unique": ambiguous_unique,
            "truly_identifier_poor_unique": truly_unique,
            "technical_unique": technical_unique,
            "percent_biologically_identifiable": round(100 * biological_identifiable_unique / len(unique), 6),
            "percent_safely_canonicalized": round(100 * safely_mapped_unique / len(unique), 6),
            "percent_genuinely_unresolved": round(100 * genuinely_unresolved_unique / len(unique), 6),
            "true_unresolved_datasets": sorted(unique.loc[unique.new_terminal_disposition.isin(FINAL_AMBIGUOUS), "dataset"].unique()),
            "true_unresolved_unique_identities_by_dataset": unresolved_by_dataset,
            "remaining_category_reasons": {
                "AMBIGUOUS_ALIAS": "pinned HGNC alias or previous-symbol evidence points to more than one current gene",
                "AMBIGUOUS_HISTORY": "exact historical Ensembl evidence lacks a unique one-to-one current continuation",
                "AMBIGUOUS_MULTIPLE_CURRENT_GENES": "exact authority channels conflict or support multiple current genes",
                "ASSEMBLY_UNRESOLVED": "coordinates are present without a sufficient assembly-qualified unique projection",
                "TRULY_SYMBOL_ONLY_UNRESOLVED": "no exact source-native stable ID, alternative authority ID, source-era dictionary anchor, or unique pinned authority mapping exists",
            },
            "true_unresolved_affect_frozen_4096": bool(unique.loc[unique.new_terminal_disposition.isin(FINAL_AMBIGUOUS), "protected_4096"].any()),
            "previous_protected_blockers": 9,
            "remaining_protected_blockers": remaining_protected,
            "frozen_semantic_identity_correction_required": remaining_protected > 0,
            "foundation_registry_old_count": len(old_ids),
            "foundation_registry_new_candidate_count": len(set(old_ids) | foundation_recovered),
            "foundation_registry_new_genes": new_only,
        },
        "frozen_vocabulary": {
            "modified": False, "members": len(frozen_vocab),
            "semantic_hash": frozen_semantic,
            "expected_semantic_hash": config["protected_semantic_hashes"]["results/v4/stage81a2_foundation_vocabulary.csv"],
            "semantic_hash_unchanged": frozen_semantic == config["protected_semantic_hashes"]["results/v4/stage81a2_foundation_vocabulary.csv"],
        },
        "future_exclusion": prior_report["foundation"],
        "protected_hashes": protected_hashes,
        "protected_hashes_unchanged": all(item["pass"] for item in protected_hashes),
        "expression_values_accessed": False, "pathology_opened": False,
        "stage81a3r_started": False, "stage81b_started": False,
        "push_performed": False,
    }
    if not summary["frozen_vocabulary"]["semantic_hash_unchanged"] or not summary["protected_hashes_unchanged"]:
        raise RuntimeError("protected hash gate failed")
    if frame.new_terminal_disposition.eq("").any() or len(frame) != len(unresolved):
        raise RuntimeError("unresolved source-row terminal accounting failed")
    if frame.duplicated(["dataset", "matrix_id", "source_feature_index"]).any():
        raise RuntimeError("duplicate unresolved source provenance keys detected")
    if len(dataset_summary) != prior_report["scope"]["scientific_datasets"]:
        raise RuntimeError("dataset reconciliation omitted registered scientific datasets")
    unsafe = frame.new_terminal_disposition.isin(FINAL_AMBIGUOUS) & frame.automatic_fix_safe.astype(bool)
    if unsafe.any():
        raise RuntimeError("ambiguous identities were marked automatically repairable")
    exact_ensembl_left = frame.new_terminal_disposition.eq("TRULY_SYMBOL_ONLY_UNRESOLVED") & frame.source_ensembl_id_raw.map(stable_id).ne("")
    if exact_ensembl_left.any():
        raise RuntimeError("exact source Ensembl IDs remain in the truly symbol-only category")

    atomic_csv(outputs["unresolved_reclassification"], frame, "gzip")
    atomic_csv(outputs["unresolved_unique_summary"], unique)
    atomic_csv(outputs["unresolved_recovery_evidence"], evidence, "gzip")
    atomic_csv(outputs["still_truly_unresolved"], remaining, "gzip")
    atomic_csv(outputs["unresolved_dataset_summary"], dataset_summary)
    atomic_csv(outputs["protected_identity_dossier_adjudicated"], protected)
    atomic_csv(outputs["foundation_registry_repair_comparison"], comparison)
    atomic_json(outputs["unresolved_resolution_summary"], summary)

    top = dataset_summary[dataset_summary.previously_unresolved_unique_identities.gt(0)].sort_values("truly_identifier_poor_remaining", ascending=False)
    audit = [
        "# Stage81A2R Project-Wide Unresolved Identity Adjudication", "",
        "**CANDIDATE EVIDENCE - FROZEN VOCABULARY UNCHANGED**", "",
        "This bounded pass adjudicates every identity in the complete project-wide unresolved ledger plus the existing protected review cases. It uses feature metadata only; no expression values or pathology labels were accessed.", "",
        "## Scope reconciliation", "",
        f"The earlier **2,010** count is foundation-only. The governing project-wide ledger contains **{summary['scope']['old_projectwide_unique_symbols']:,}** unique unresolved symbols across **{summary['scope']['datasets_with_unresolved_rows']}** datasets and **{summary['scope']['scientific_datasets']}** registered scientific datasets in total.", "",
        "## Final unique-identity counts", "",
        *[f"- {key}: {value:,}" for key, value in class_counts_unique.items()], "",
        f"- Biologically identifiable source identities: **{biological_identifiable_unique:,}** ({summary['answers']['percent_biologically_identifiable']:.3f}%)",
        f"- Safely projected to current Ensembl: **{safely_mapped_unique:,}** ({summary['answers']['percent_safely_canonicalized']:.3f}%)",
        f"- Distinct current Ensembl genes represented: **{recovered_canonical_genes:,}**",
        f"- Identified source-native/noncanonical: **{identified_native_unique:,}**",
        f"- Genuinely unresolved: **{genuinely_unresolved_unique:,}** ({summary['answers']['percent_genuinely_unresolved']:.3f}%)",
        f"- Ambiguous: **{ambiguous_unique:,}**",
        f"- Truly identifier-poor: **{truly_unique:,}**",
        f"- Technical/non-biological: **{technical_unique:,}**", "",
        "## Dataset reconciliation", "", top.to_csv(index=False), "",
        "## Protected 4,096 gate", "",
        f"Five source-exact alternate/nonprimary Ensembl cases were reclassified using shared NCBI Gene/HGNC anchors. Remaining protected human blockers: **{remaining_protected}**. The frozen vocabulary file and semantic hash were not changed.", "",
        "The adjudicated dossier is a row-preserving versioned successor to the prior protected dossier: all prior evidence columns remain present, and the new decision/evidence/blocker fields are appended rather than maintained as a disconnected case list.", "",
        "## Governance", "",
        f"Final decision: **{summary['status']}**", "",
        "Stage81A3R not started. Stage81B not started. No model training. No expression biology. No pathology. No push.",
    ]
    outputs["unresolved_resolution_audit"].parent.mkdir(parents=True, exist_ok=True)
    outputs["unresolved_resolution_audit"].write_text("\n".join(audit) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
