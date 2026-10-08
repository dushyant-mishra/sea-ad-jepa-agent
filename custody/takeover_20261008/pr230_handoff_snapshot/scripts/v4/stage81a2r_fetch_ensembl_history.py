"""Fetch and pin Ensembl stable-ID history for exact non-current source IDs."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import ssl
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import certifi

from sea_ad_jepa.v4.gene_identity_authority import normalize_ensembl_gene_id, parse_ensembl_gtf


ENDPOINT = "https://rest.ensembl.org/archive/id/{stable_id}"
BATCH_SIZE = 50


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def fetch_one(stable_id: str) -> tuple[str, dict]:
    request = urllib.request.Request(
        ENDPOINT.format(stable_id=stable_id),
        method="GET",
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "sea-ad-jepa-stage81a2r/1.0"},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120, context=context) as response:
                return stable_id, json.loads(response.read())
        except Exception as error:
            last_error = error
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Ensembl history failed for {stable_id}") from last_error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source", type=Path, default=Path("results/v4/stage81a2r_source_mapping_decisions_candidate.csv.gz"))
    parser.add_argument("--ids-file", type=Path, help="Optional newline-delimited exact source Ensembl IDs to append to the cache")
    parser.add_argument("--gtf", type=Path, default=Path("data/external/v4/gene_identity_authority/ensembl_116/Homo_sapiens.GRCh38.116.gtf.gz"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/external/v4/gene_identity_authority/ensembl_archive_responses"))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    current = set(parse_ensembl_gtf(project / args.gtf))
    source_ids: set[str] = set()
    if args.ids_file:
        for value in (project / args.ids_file).read_text(encoding="utf-8").splitlines():
            normalized = normalize_ensembl_gene_id(value.strip())
            if normalized:
                source_ids.add(normalized[0])
    else:
        source = pd.read_csv(project / args.source, dtype=str, keep_default_na=False)
        for row in source.itertuples(index=False):
            if row.mapping_method != "exact_source_ensembl_symbol_pair":
                continue
            normalized = normalize_ensembl_gene_id(row.canonical_ensembl_gene_id)
            if normalized:
                source_ids.add(normalized[0])
    queries = sorted(source_ids - current)
    output_dir = project / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    completed: set[str] = set()
    existing_batches = sorted(output_dir.glob("archive_id_batch_*.json"))
    for path in existing_batches:
        completed.update(json.loads(path.read_text(encoding="utf-8"))["queried_ids"])
    pending = [stable_id for stable_id in queries if stable_id not in completed]
    next_batch_index = max((int(path.stem.rsplit("_", 1)[-1]) for path in existing_batches), default=-1) + 1
    for offset in range(0, len(pending), BATCH_SIZE):
        batch = pending[offset : offset + BATCH_SIZE]
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            response = dict(executor.map(fetch_one, batch))
        retrieved = datetime.now(timezone.utc).isoformat()
        payload = {
            "authority": "Ensembl REST stable-ID archive",
            "endpoint_template": ENDPOINT,
            "bulk_post_attempted": True,
            "bulk_post_result": "HTTP_500_SERVICE_ERROR; bounded official GET fallback used",
            "retrieval_timestamp_utc": retrieved,
            "queried_ids": batch,
            "responses": response,
            "response_semantic_sha256": hashlib.sha256(json.dumps(response, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }
        batch_index = next_batch_index + offset // BATCH_SIZE
        atomic_json(output_dir / f"archive_id_batch_{batch_index:04d}.json", payload)
        completed.update(batch)
        print(f"fetched append batch {offset // BATCH_SIZE + 1}/{(len(pending) + BATCH_SIZE - 1) // BATCH_SIZE}", flush=True)
        time.sleep(0.2)
    manifest = {
        "authority": "Ensembl",
        "endpoint_template": ENDPOINT,
        "current_release": 116,
        "source_provided_ensembl_ids": len(source_ids),
        "current_source_ids": len(source_ids & current),
        "noncurrent_ids_queried": len(queries),
        "new_queries_fetched": len(pending),
        "cache_batch_count": len(list(output_dir.glob("archive_id_batch_*.json"))),
        "all_queries_cached": set(queries).issubset(completed),
    }
    atomic_json(output_dir / "archive_query_manifest.json", manifest)
    if args.ids_file and manifest["all_queries_cached"]:
        # The request ledger is a pending-work queue, not an authority record.
        # Successful responses remain immutably preserved in append-only batches.
        (project / args.ids_file).write_text("", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
