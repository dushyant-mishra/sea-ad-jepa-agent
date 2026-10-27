#!/usr/bin/env python3
"""Prospectively frozen, public E2G browser-track comparison (annotation only).

Requires 96 historical Stage75 TF->gene rows. Downloads ONLY seven small,
already HEAD-qualified public browser tracks, without GCS billing credentials.
Symbol overlap is not canonical Ensembl identity or validated TF regulation.
"""
from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import io
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://e2g.stanford.edu/graphql"
QUERY = """query FixedSevenPublicTracks {
  getDataTracks { cellTypeId cellType study modelType e2gPredictionsUrl }
}"""
EXPECTED_BLOB = "87117c485c25f9c7295a6ac4ba5ca48b45c844aa"
PANEL = (
    "inflammatory_macrophage_ENCSR593WXK",
    "inflammatory_macrophage_ENCSR643ZGR",
    "inflammatory_macrophage_ENCSR226JLK",
    "Macrophage", "Immune_monocyte_1",
    "brain_ENCSR344FLH", "Stitziel_hCA_Myeloid",
)
MAX_FILE = 9_000_000
MAX_TOTAL = 50_000_000
MAX_UNCOMPRESSED_PER_FILE = 100_000_000
CHR = re.compile(r"chr(?:[1-9]|1[0-9]|2[0-2]|X|Y|M|MT)$")
SUFFIXES = ("_promoter", "_genic", "_intergenic")


class EvidenceError(ValueError):
    pass


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not public_url(newurl):
            raise EvidenceError("Unsafe redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def public_url(url: str) -> bool:
    p = urllib.parse.urlsplit(url)
    return (p.scheme == "https" and p.hostname == "storage.googleapis.com"
            and p.port is None and p.username is None and p.password is None
            and not p.query and not p.fragment and bool(p.path))


def authenticated_stage75(source: Path) -> set[str]:
    with source.open("rb") as f:
        content = f.read()
    # Same SHA algorithm as Git blobs, not a plain-file SHA-256.
    git_blob = hashlib.sha1(
        b"blob " + str(len(content)).encode() + bytes([0]) + content
    ).hexdigest()
    if git_blob != EXPECTED_BLOB:
        raise EvidenceError("Historical Stage75 source Git blob is not frozen")
    table = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    if len(table) != 96:
        raise EvidenceError("Stage75 row count changed")
    pairs = {(r["tf"], r["target_gene"]) for r in table}
    genes = {r["target_gene"] for r in table}
    if len(pairs) != 96 or len(genes) != 27 or len({x for x, _ in pairs}) != 7:
        raise EvidenceError("Stage75 TF->gene identity or count drift")
    if any(not r["peak_to_gene_support"].startswith("proximity_only:")
           or r["direction_evidence_type"] != "predicted_response_sign_from_coactivity"
           for r in table):
        raise EvidenceError("Stage75 semantics appear to have been promoted")
    return genes


def public_sources() -> dict[str, dict]:
    req = urllib.request.Request(API, method="POST",
        data=json.dumps({"query": QUERY}).encode(),
        headers={"Content-Type": "application/json", "Accept":"application/json",
                 "User-Agent": "JEPA-E2G-Bounded-Descriptive-Audit/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        data = response.read(8_000_001)
    if len(data) > 8_000_000:
        raise EvidenceError("GraphQL metadata too large")
    j = json.loads(data)
    if j.get("errors") or not isinstance(j.get("data"), dict):
        raise EvidenceError("GraphQL metadata inaccessible")
    chosen = {}
    for row in j["data"]["getDataTracks"]:
        ident = row["cellTypeId"]
        if ident in PANEL:
            if ident in chosen:
                raise EvidenceError("Ambiguous track id")
            chosen[ident] = row
    if set(chosen) != set(PANEL):
        raise EvidenceError("Seven predeclared tracks not all present")
    return chosen


def bounded_public_download(url: str, remaining: int) -> tuple[bytes, str]:
    if not public_url(url):
        raise EvidenceError("Forbidden track host/signed URL")
    opener = urllib.request.build_opener(SameHostRedirect)
    head = urllib.request.Request(url, method="HEAD")
    with opener.open(head, timeout=25) as res:
        if res.status != 200:
            raise EvidenceError("HEAD not successful")
        declared = res.headers.get("Content-Length")
    if declared is None or not declared.isdecimal() or not 0 < int(declared) <= MAX_FILE:
        raise EvidenceError("Track size invalid/over cap")
    if int(declared) > remaining:
        raise EvidenceError("Overall transfer cap reached")
    req = urllib.request.Request(url, method="GET",
        headers={"Accept-Encoding": "identity",
                 "User-Agent": "JEPA-E2G-Bounded-Descriptive-Audit/1.0"})
    digest = hashlib.sha256()
    chunks, count = [], 0
    with opener.open(req, timeout=45) as response:
        if response.status != 200:
            raise EvidenceError("GET not successful")
        while True:
            data = response.read(65536)
            if not data:
                break
            count += len(data)
            if count > MAX_FILE or count > remaining:
                raise EvidenceError("Download exceeded predeclared cap")
            digest.update(data)
            chunks.append(data)
    if count != int(declared):
        raise EvidenceError("Content-Length mismatch")
    return b"".join(chunks), digest.hexdigest()


def gene_from_name(label: str, targets: set[str]) -> str | None:
    token = label.split("|", 1)[0]
    if token in targets:
        return token
    for suffix in SUFFIXES:
        if token.endswith(suffix):
            candidate = token[:-len(suffix)]
            if candidate in targets:
                return candidate
    return None


def parse_track(content: bytes, gzipped: bool, targets: set[str]) -> dict:
    opener = gzip.GzipFile(fileobj=io.BytesIO(content)) if gzipped else io.BytesIO(content)
    count = 0
    n_uncompressed = 0
    matches = collections.Counter()
    distal = collections.Counter()
    unique: dict[str, set[tuple[str, int, int]]] = collections.defaultdict(set)
    max_score = collections.defaultdict(lambda: None)
    target_row_count = collections.Counter()
    try:
        for lineno, raw in enumerate(opener, 1):
            n_uncompressed += len(raw)
            if n_uncompressed > MAX_UNCOMPRESSED_PER_FILE:
                raise EvidenceError("Uncompressed output exceeded cap")
            if not raw.strip():
                continue
            parts = raw.decode("utf-8").rstrip("\r\n").split("\t")
            if len(parts) != 10:
                raise EvidenceError("Unexpected BEDPE columns at row " + str(lineno))
            e_chr, a, b, g_chr, g1, g2, label, value = parts[:8]
            try:
                a, b, g1, g2 = int(a), int(b), int(g1), int(g2)
                score = float(value)
            except (ValueError, TypeError) as exc:
                raise EvidenceError("Invalid numeric BEDPE entry") from exc
            if (not CHR.fullmatch(e_chr) or g_chr != e_chr or
                a < 0 or a >= b or g1 < 0 or g2 < g1 or
                not math.isfinite(score) or not 0 <= score <= 1):
                raise EvidenceError("Invalid BEDPE region/score")
            count += 1
            gene = gene_from_name(label, targets)
            if gene is not None:
                matches[gene] += 1
                unique[gene].add((e_chr, a, b))
                if abs((a + b) / 2 - g1) >= 20_000:
                    distal[gene] += 1
                prev = max_score[gene]
                max_score[gene] = score if prev is None else max(prev, score)
    finally:
        opener.close()
    return {
        "file_total_predictions": count,
        "matched_prediction_rows": sum(matches.values()),
        "matched_distinct_target_symbols": len(matches),
        "per_gene": {
            gene: {
                "prediction_count": matches[gene],
                "distinct_enhancer_intervals": len(unique[gene]),
                "distal_at_least_20kb_count": distal[gene],
                "max_score_within_source": max_score[gene],
                "symbol_status": ("PROVISIONAL_SYMBOL_MATCH" if matches[gene]
                                  else "NO_ROW_IN_THRESHOLD_FILE__NOT_BIOLOGICAL_NEGATIVE"),
            }
            for gene in sorted(targets)
        },
    }


def analyze(stage75_path: Path) -> dict:
    targets = authenticated_stage75(stage75_path)
    srcs = public_sources()
    remaining = MAX_TOTAL
    analyses = []
    for ident in PANEL:
        meta = srcs[ident]
        url = meta.get("e2gPredictionsUrl") or ""
        raw, digest = bounded_public_download(url, remaining)
        remaining -= len(raw)
        parsed = parse_track(raw, url.endswith(".gz"), targets)
        analyses.append({
            "cell_type_id": ident, "published_cell_type": meta.get("cellType"),
            "published_study": meta.get("study"),
            "model": meta.get("modelType"),
            "source_basename": urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1],
            "source_sha256": digest, "compressed_bytes": len(raw),
            **parsed,
        })
    return {
        "schema": "JEPA_PUBLIC_E2G_7TRACK_TARGET_GENE_SYMBOL_SURVEY_V1",
        "source": "e2g.stanford.edu public thresholded browser tracks",
        "target_basis": "frozen Stage75 27 target-gene symbols / 96 TF hypotheses",
        "target_gene_count": len(targets), "source_count": len(analyses),
        "data_provenance": "public live GraphQL selected HEAD200, source files hashed",
        "matches_are": "PROVISIONAL_SYMBOL_OVERLAP__NOT_CANONICAL_GENE_ID",
        "e2g_edge_validated_for_specific_tf": None,
        "direct_adult_microglia_validation": False,
        "no_accepted_biological_negative_from_empty_file": True,
        "no_cross_model_score_calibration": True,
        "no_causal_claim": True,
        "no_biological_target_selection": True,
        "training_authorized": False,
        "sources": analyses,
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: <Stage75 CSV> <output JSON>")
    result = analyze(Path(sys.argv[1]))
    dest = Path(sys.argv[2])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "target_gene_count": result["target_gene_count"],
        "matches_are": result["matches_are"],
        "sources": [
            {k: x[k] for k in ("cell_type_id", "model", "file_total_predictions",
                                "matched_prediction_rows",
                                "matched_distinct_target_symbols","compressed_bytes",
                                "source_sha256")}
            for x in result["sources"]
        ],
        "e2g_edge_validated_for_specific_tf": None,
        "training_authorized": False,
    }, indent=2))

if __name__ == "__main__":
    main()
