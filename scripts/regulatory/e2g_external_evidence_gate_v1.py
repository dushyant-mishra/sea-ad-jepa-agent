#!/usr/bin/env python3
"""Read-only, fail-closed intake for external E2G annotations.

The historical Stage75 rows are TF->gene hypotheses, *not* enhancer->gene
intervals. A target-gene match is annotation only, never TF->gene validation.
No training, target selection, network access, or source mutation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

STAGE75_FIELDS = {
    "tf", "target_gene", "existing_stage75_edge", "stage75_evidence_tier",
    "peak_to_gene_support", "sea_ad_multiome_support",
    "direction_evidence_type", "allowed_model_role", "prohibited_claim",
}
E2G_FIELDS = {
    "chrom", "start", "end", "target_ensembl_id", "score",
    "genome_build", "biosample", "source_dataset", "model_family",
    "model_version", "exposure_class",
}
GENE_MAP_FIELDS = {"target_gene", "target_ensembl_id"}
FAMILIES = {"scE2G", "ENCODE-rE2G", "ENCODE-E2G", "GraphReg"}
EXPOSURES = {
    "DEVELOPMENT_EXPOSED", "CONDITIONAL_EXTERNAL_SUPPORT",
    "PROTECTED_NOT_AVAILABLE_FOR_SELECTION", "INDEPENDENCE_UNDETERMINED",
}
ENSEMBL = re.compile(r"ENSG[0-9]{11}$")
CHROM = re.compile(r"chr(?:[1-9]|1[0-9]|2[0-2]|X|Y|M|MT)$")


class EvidenceGateError(ValueError):
    pass


def _rows(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise EvidenceGateError(f"Input missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise EvidenceGateError(
                f"{path}: required columns missing: {sorted(required - set(reader.fieldnames or []))}"
            )
        records = list(reader)
        if any(None in row for row in records):
            raise EvidenceGateError(f"{path}: malformed CSV row")
        return records


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(stage75: Path, predictions: Path | None = None,
          gene_map: Path | None = None, expected_count: int = 96,
          genome_build: str = "GRCh38") -> dict:
    if (predictions is None) != (gene_map is None):
        raise EvidenceGateError("Predictions and gene map must be provided together")
    candidates = _rows(stage75, STAGE75_FIELDS)
    if len(candidates) != expected_count:
        raise EvidenceGateError(
            f"Stage75 row authority drift: expected {expected_count}, got {len(candidates)}"
        )
    pairs = [(r["tf"], r["target_gene"]) for r in candidates]
    if len(set(pairs)) != len(pairs) or any(not a or not b for a, b in pairs):
        raise EvidenceGateError("Stage75 contains duplicate or empty TF/gene pairs")
    if any(r["existing_stage75_edge"] != "True" for r in candidates):
        raise EvidenceGateError("Stage75 historical edge identity changed")
    if any(not r["peak_to_gene_support"].startswith("proximity_only:")
           for r in candidates):
        raise EvidenceGateError("Unreviewed Stage75 peak->gene semantic change")
    if any(r["direction_evidence_type"] != "predicted_response_sign_from_coactivity"
           for r in candidates):
        raise EvidenceGateError("Unreviewed Stage75 direction semantic change")
    targets = {row["target_gene"] for row in candidates}
    receipt = {
        "schema": "JEPA_EXTERNAL_E2G_EVIDENCE_GATE_V1",
        "authority": {
            "target_selection": False, "real_training": False,
            "stage4": False, "causal_validation": False,
            "tf_target_regulatory_validation": False,
        },
        "stage75": {
            "sha256": _hash(stage75), "candidate_tf_gene_rows": len(candidates),
            "tf_count": len({a for a, _ in pairs}),
            "target_gene_count": len(targets),
            "tier_counts": dict(sorted(Counter(
                r["stage75_evidence_tier"] for r in candidates
            ).items())),
            "peak_gene_semantics": "PROXIMITY_ONLY_NOT_AUTHENTICATED_E2G",
        },
        "e2g": {
            "status": "NOT_RUN_NO_EXTERNAL_PREDICTIONS",
            "target_gene_annotation_overlap": None,
            "candidate_tf_target_rows_with_annotated_target": None,
            "tf_target_edge_validation_count": None,
            "reason": "Stage75 lacks authenticated TF-bound enhancer coordinates",
        },
    }
    if predictions is None:
        return receipt

    mapping_rows = _rows(gene_map, GENE_MAP_FIELDS)
    symbol_to_id: dict[str, str] = {}
    id_to_symbol: dict[str, str] = {}
    for row in mapping_rows:
        symbol, gene_id = row["target_gene"], row["target_ensembl_id"]
        if not symbol or not ENSEMBL.fullmatch(gene_id):
            raise EvidenceGateError("Missing/invalid canonical unversioned Ensembl mapping")
        if symbol in symbol_to_id or gene_id in id_to_symbol:
            raise EvidenceGateError("Ambiguous or duplicate gene identity mapping")
        symbol_to_id[symbol] = gene_id
        id_to_symbol[gene_id] = symbol
    if not targets.issubset(symbol_to_id):
        raise EvidenceGateError("Unmapped Stage75 target genes: " +
                                ",".join(sorted(targets - symbol_to_id.keys())))

    annotations = _rows(predictions, E2G_FIELDS)
    hit_ids: set[str] = set()
    contexts: set[tuple[str, str, str]] = set()
    for row in annotations:
        try:
            start, end, score = int(row["start"]), int(row["end"]), float(row["score"])
        except (ValueError, TypeError) as exc:
            raise EvidenceGateError("Invalid interval or score") from exc
        if (not CHROM.fullmatch(row["chrom"]) or start < 0 or end <= start
                or not math.isfinite(score) or not 0 <= score <= 1):
            raise EvidenceGateError("Invalid genomic interval or probability-range score")
        if row["genome_build"] != genome_build:
            raise EvidenceGateError("Genome build mismatch; no silent liftover")
        if not ENSEMBL.fullmatch(row["target_ensembl_id"]):
            raise EvidenceGateError("E2G target gene must be canonical Ensembl (unversioned)")
        if row["model_family"] not in FAMILIES or not row["model_version"]:
            raise EvidenceGateError("Unknown/unversioned E2G model")
        if row["exposure_class"] not in EXPOSURES:
            raise EvidenceGateError("E2G provenance/exposure class absent or unrecognized")
        if not row["biosample"] or not row["source_dataset"]:
            raise EvidenceGateError("E2G biosample and source provenance required")
        hit_ids.add(row["target_ensembl_id"])
        contexts.add((row["source_dataset"], row["biosample"], row["model_family"]))

    target_hits = {symbol for symbol in targets if symbol_to_id[symbol] in hit_ids}
    receipt["e2g"] = {
        "status": "ANNOTATION_ONLY__NO_TF_EDGE_CONFIRMATION",
        "sha256": _hash(predictions), "gene_map_sha256": _hash(gene_map),
        "genome_build": genome_build,
        "source_model_contexts": [list(x) for x in sorted(contexts)],
        "external_interval_gene_rows": len(annotations),
        "target_gene_annotation_overlap": len(target_hits),
        "candidate_tf_target_rows_with_annotated_target": sum(
            row["target_gene"] in target_hits for row in candidates
        ),
        "tf_target_edge_validation_count": None,
        "reason": "No authenticated per-element TF binding and Stage75 interval join; a gene-level overlap is not a regulatory edge validation",
    }
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage75", type=Path, required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--gene-map", type=Path)
    parser.add_argument("--genome-build", default="GRCh38")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit(args.stage75, args.predictions, args.gene_map,
                    genome_build=args.genome_build)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
