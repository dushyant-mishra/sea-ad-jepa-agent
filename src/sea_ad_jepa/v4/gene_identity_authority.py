"""Exact-only Ensembl/HGNC identity adjudication for Stage81A2R."""

from __future__ import annotations

import csv
import gzip
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ENSEMBL_GENE_RE = re.compile(r"^(ENSG\d{11})(?:\.(\d+))?$")
REFSEQ_TRANSCRIPT_RE = re.compile(r"^(?:NM|NR|XM|XR)_\d+(?:\.\d+)?$")
GENCODE_TRANSCRIPT_RE = re.compile(r"^ENST\d+(?:\.\d+)?$")
GENOMIC_LOCUS_RE = re.compile(r"^(?:chr)?[A-Za-z0-9_.]+[:_-](\d+)[-_](\d+)$")
TECHNICAL_FEATURE_RE = re.compile(r"^(?:ERCC-|__|NO_FEATURE$|AMBIGUOUS$|UNMAPPED$)", re.IGNORECASE)


@dataclass(frozen=True)
class EnsemblGene:
    stable_id: str
    versioned_id: str
    symbol: str
    biotype: str
    chromosome: str
    start: int
    end: int
    strand: str


@dataclass(frozen=True)
class HgncGene:
    hgnc_id: str
    symbol: str
    name: str
    locus_group: str
    locus_type: str
    ensembl_gene_id: str
    previous_symbols: tuple[str, ...]
    alias_symbols: tuple[str, ...]


@dataclass
class AuthorityIndex:
    ensembl_by_id: dict[str, EnsemblGene]
    ensembl_by_symbol: dict[str, tuple[str, ...]]
    hgnc_by_id: dict[str, HgncGene]
    hgnc_approved: dict[str, tuple[str, ...]]
    hgnc_previous: dict[str, tuple[str, ...]]
    hgnc_alias: dict[str, tuple[str, ...]]
    hgnc_withdrawn: dict[str, tuple[str, ...]]


def normalize_text(value: Any) -> str:
    """Apply only whitespace trimming and Unicode canonical normalization."""
    return unicodedata.normalize("NFC", "" if value is None else str(value)).strip()


def normalize_ensembl_gene_id(value: Any) -> tuple[str, str, str] | None:
    """Return stable ID, original normalized text, and version without guessing."""
    raw = normalize_text(value)
    match = ENSEMBL_GENE_RE.fullmatch(raw)
    if not match:
        return None
    return match.group(1), raw, match.group(2) or ""


def _split_pipe(value: Any) -> tuple[str, ...]:
    return tuple(item for item in (normalize_text(part) for part in normalize_text(value).split("|")) if item)


def _gtf_attributes(text: str) -> dict[str, str]:
    return {key: value for key, value in re.findall(r'(\w+) "([^"]*)"', text)}


def parse_ensembl_gtf(path: Path) -> dict[str, EnsemblGene]:
    genes: dict[str, EnsemblGene] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9 or fields[2] != "gene":
                continue
            attributes = _gtf_attributes(fields[8])
            normalized = normalize_ensembl_gene_id(attributes.get("gene_id", ""))
            if normalized is None:
                continue
            stable_id, versioned_id, version = normalized
            if not version and attributes.get("gene_version"):
                versioned_id = f"{stable_id}.{attributes['gene_version']}"
            candidate = EnsemblGene(
                stable_id=stable_id,
                versioned_id=versioned_id,
                symbol=normalize_text(attributes.get("gene_name", "")),
                biotype=normalize_text(attributes.get("gene_biotype", "")),
                chromosome=fields[0],
                start=int(fields[3]),
                end=int(fields[4]),
                strand=fields[6],
            )
            previous = genes.get(stable_id)
            if previous is None or candidate.versioned_id > previous.versioned_id:
                genes[stable_id] = candidate
    return genes


def parse_hgnc_complete(path: Path) -> dict[str, HgncGene]:
    records: dict[str, HgncGene] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            record = HgncGene(
                hgnc_id=normalize_text(row.get("hgnc_id")),
                symbol=normalize_text(row.get("symbol")),
                name=normalize_text(row.get("name")),
                locus_group=normalize_text(row.get("locus_group")),
                locus_type=normalize_text(row.get("locus_type")),
                ensembl_gene_id=normalize_text(row.get("ensembl_gene_id")),
                previous_symbols=_split_pipe(row.get("prev_symbol")),
                alias_symbols=_split_pipe(row.get("alias_symbol")),
            )
            records[record.hgnc_id] = record
    return records


def parse_hgnc_withdrawn(path: Path) -> dict[str, tuple[str, ...]]:
    by_symbol: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            symbol = normalize_text(row.get("WITHDRAWN_SYMBOL"))
            merged = normalize_text(row.get("MERGED_INTO_REPORT(S) (i.e HGNC_ID|SYMBOL|STATUS)"))
            if symbol:
                for report in merged.split(",") if merged else ():
                    hgnc_id = normalize_text(report).split("|", 1)[0]
                    if hgnc_id:
                        by_symbol[symbol].add(hgnc_id)
                by_symbol.setdefault(symbol, set())
    return {symbol: tuple(sorted(values)) for symbol, values in by_symbol.items()}


def _invert(records: Iterable[HgncGene], field: str) -> dict[str, tuple[str, ...]]:
    index: dict[str, set[str]] = defaultdict(set)
    for record in records:
        values = getattr(record, field)
        if isinstance(values, str):
            values = (values,)
        for value in values:
            if value:
                index[value].add(record.hgnc_id)
    return {key: tuple(sorted(values)) for key, values in index.items()}


def build_authority_index(gtf: Path, hgnc_complete: Path, hgnc_withdrawn: Path) -> AuthorityIndex:
    ensembl = parse_ensembl_gtf(gtf)
    by_symbol: dict[str, set[str]] = defaultdict(set)
    for gene in ensembl.values():
        if gene.symbol:
            by_symbol[gene.symbol].add(gene.stable_id)
    hgnc = parse_hgnc_complete(hgnc_complete)
    return AuthorityIndex(
        ensembl_by_id=ensembl,
        ensembl_by_symbol={key: tuple(sorted(values)) for key, values in by_symbol.items()},
        hgnc_by_id=hgnc,
        hgnc_approved=_invert(hgnc.values(), "symbol"),
        hgnc_previous=_invert(hgnc.values(), "previous_symbols"),
        hgnc_alias=_invert(hgnc.values(), "alias_symbols"),
        hgnc_withdrawn=parse_hgnc_withdrawn(hgnc_withdrawn),
    )


def load_history_cache(directory: Path) -> dict[str, dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("archive_id_batch_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for stable_id, response in payload["responses"].items():
            combined[stable_id] = response
    return combined


def history_current_replacements(response: dict[str, Any], current_ids: set[str]) -> tuple[str, ...]:
    replacements: set[str] = set()
    latest = normalize_ensembl_gene_id(response.get("latest", ""))
    if latest and latest[0] in current_ids:
        replacements.add(latest[0])
    for item in response.get("possible_replacement") or ():
        raw = item.get("stable_id", "") if isinstance(item, dict) else item
        normalized = normalize_ensembl_gene_id(raw)
        if normalized and normalized[0] in current_ids:
            replacements.add(normalized[0])
    return tuple(sorted(replacements))


def valid_hgnc_ensembl(hgnc_ids: Iterable[str], authority: AuthorityIndex) -> tuple[str, ...]:
    values: set[str] = set()
    for hgnc_id in hgnc_ids:
        record = authority.hgnc_by_id.get(hgnc_id)
        normalized = normalize_ensembl_gene_id(record.ensembl_gene_id if record else "")
        if normalized and normalized[0] in authority.ensembl_by_id:
            values.add(normalized[0])
    return tuple(sorted(values))


def symbol_evidence(symbol: str, authority: AuthorityIndex) -> dict[str, tuple[str, ...]]:
    exact = normalize_text(symbol)
    approved_ids = authority.hgnc_approved.get(exact, ())
    previous_ids = authority.hgnc_previous.get(exact, ())
    alias_ids = authority.hgnc_alias.get(exact, ())
    withdrawn_ids = authority.hgnc_withdrawn.get(exact, ())
    return {
        "hgnc_approved_ids": approved_ids,
        "hgnc_approved_ensembl": valid_hgnc_ensembl(approved_ids, authority),
        "hgnc_previous_ids": previous_ids,
        "hgnc_previous_ensembl": valid_hgnc_ensembl(previous_ids, authority),
        "hgnc_alias_ids": alias_ids,
        "hgnc_alias_ensembl": valid_hgnc_ensembl(alias_ids, authority),
        "hgnc_withdrawn_replacement_ids": withdrawn_ids,
        "hgnc_withdrawn_ensembl": valid_hgnc_ensembl(withdrawn_ids, authority),
        "ensembl_symbol_candidates": authority.ensembl_by_symbol.get(exact, ()),
    }


def classify_symbol_only(symbol: str, authority: AuthorityIndex) -> tuple[str, str, dict[str, tuple[str, ...]]]:
    evidence = symbol_evidence(symbol, authority)
    ordered = (
        ("hgnc_approved_ensembl", "EXACT_HGNC_APPROVED_TO_ENSEMBL", "approved"),
        ("hgnc_previous_ensembl", "EXACT_HGNC_PREVIOUS_SYMBOL_RECOVERED", "previous"),
        ("hgnc_alias_ensembl", "EXACT_HGNC_ALIAS_RECOVERED", "alias"),
        ("hgnc_withdrawn_ensembl", "EXACT_HGNC_WITHDRAWN_SINGLE_MERGE_RECOVERED", "withdrawn"),
        ("ensembl_symbol_candidates", "EXACT_ENSEMBL_CURRENT_SYMBOL_RECOVERED", "ensembl"),
    )
    for key, success, channel in ordered:
        values = evidence[key]
        if len(values) == 1:
            other = set().union(*(set(evidence[item]) for item, _, _ in ordered if item != key))
            if other and other != set(values) and not set(values).issubset(other):
                return "CONFLICTING_AUTHORITATIVE_IDENTITY", "", evidence
            return success, values[0], evidence
        if len(values) > 1:
            ambiguity = {
                "previous": "AMBIGUOUS_PREVIOUS_SYMBOL_MULTIPLE_TARGETS",
                "alias": "AMBIGUOUS_ALIAS_MULTIPLE_TARGETS",
                "withdrawn": "AMBIGUOUS_HGNC_SPLIT",
            }.get(channel, "CONFLICTING_AUTHORITATIVE_IDENTITY")
            return ambiguity, "", evidence
        if channel == "approved" and evidence["hgnc_approved_ids"]:
            return "EXACT_HGNC_ID_BUT_NO_EXACT_ENSEMBL_GENE", "", evidence
    return "SYMBOL_ONLY_UNRESOLVED", "", evidence


def classify_source_native_feature(
    raw_id: Any,
    symbol: Any = "",
    feature_type: Any = "",
    annotation_authority: Any = "",
    refseq_id: Any = "",
    ncbi_gene_id: Any = "",
    transcript_id: Any = "",
    chromosome: Any = "",
    start: Any = "",
    end: Any = "",
    strand: Any = "",
    biotype: Any = "",
) -> tuple[str, dict[str, str]]:
    """Classify exact source-native anchors without projecting or fuzzy matching."""
    raw = normalize_text(raw_id)
    name = normalize_text(symbol)
    kind = normalize_text(feature_type)
    authority = normalize_text(annotation_authority)
    refseq = normalize_text(refseq_id)
    ncbi = normalize_text(ncbi_gene_id)
    transcript = normalize_text(transcript_id)
    chrom = normalize_text(chromosome)
    begin = normalize_text(start)
    finish = normalize_text(end)
    orientation = normalize_text(strand)
    source_biotype = normalize_text(biotype)
    anchor = {
        "source_native_id": raw,
        "source_native_symbol": name,
        "source_annotation_authority": authority,
        "source_refseq_id": refseq,
        "source_ncbi_gene_id": ncbi,
        "source_transcript_id": transcript,
        "source_chromosome": chrom,
        "source_start": begin,
        "source_end": finish,
        "source_strand": orientation,
        "source_biotype": source_biotype,
    }
    if (refseq and REFSEQ_TRANSCRIPT_RE.fullmatch(refseq)) or (ncbi and ncbi.isdigit()):
        return "EXACT_REFSEQ_OR_NCBI_GENE", anchor
    transcript_value = transcript or raw
    if GENCODE_TRANSCRIPT_RE.fullmatch(transcript_value):
        anchor["source_transcript_id"] = transcript_value
        if "gencode" in authority.lower():
            return "EXACT_GENCODE_LEGACY", anchor
        return "SOURCE_NATIVE_TRANSCRIPT_MODEL", anchor
    locus = GENOMIC_LOCUS_RE.fullmatch(raw)
    if locus and int(locus.group(1)) < int(locus.group(2)):
        return "SOURCE_NATIVE_GENOMIC_LOCUS", anchor
    if chrom and begin.isdigit() and finish.isdigit() and int(begin) < int(finish):
        return "SOURCE_NATIVE_GENOMIC_LOCUS", anchor
    lower_kind = kind.lower()
    if TECHNICAL_FEATURE_RE.match(raw or name) or any(term in lower_kind for term in ("antibody capture", "crispr guide", "multiplexing capture", "technical")):
        return "NON_BIOLOGICAL_TECHNICAL_FEATURE", anchor
    if source_biotype and any(term in source_biotype.lower() for term in ("novel", "predicted", "uncharacterized")):
        return "SOURCE_ANNOTATED_NOVEL_OR_PREDICTED_GENE", anchor
    if raw and kind and lower_kind not in {"gene expression", "gene"}:
        return "SOURCE_NATIVE_BIOLOGICAL_FEATURE_UNPROJECTED", anchor
    return "SYMBOL_ONLY_UNRESOLVED", anchor


def source_family(source_dataset_id: str) -> str:
    if source_dataset_id.startswith("NPH52::"):
        return "NPH52"
    if source_dataset_id == "SEA_AD_COMMON":
        return "SEA_AD"
    if source_dataset_id == "HVS_COMMON":
        return "HVS"
    return source_dataset_id


def broad_biotype(gene: EnsemblGene, hgnc: HgncGene | None) -> str:
    biotype = gene.biotype.lower()
    symbol = gene.symbol
    locus = "" if hgnc is None else f"{hgnc.locus_group} {hgnc.locus_type}".lower()
    if gene.chromosome == "MT" or biotype.startswith("mt_"):
        return "mitochondrial"
    if "immunoglobulin" in biotype or "immunoglobulin" in locus or symbol.startswith("IG"):
        return "immunoglobulin"
    if "tr_" in biotype or "t cell receptor" in locus or symbol.startswith("TR"):
        return "TCR"
    if "pseudogene" in biotype or "pseudogene" in locus:
        return "pseudogene"
    if biotype == "protein_coding":
        return "protein_coding"
    if "lncrna" in biotype or "long non-coding" in locus:
        return "lncRNA"
    if "readthrough" in biotype or "readthrough" in locus:
        return "readthrough"
    if symbol.startswith(("RPL", "RPS")):
        return "ribosomal_related"
    if biotype in {"mirna", "snrna", "snorna", "rrna", "trna", "scrna", "srna", "misc_rna", "ribozyme"}:
        return "other_ncRNA"
    return "other"
