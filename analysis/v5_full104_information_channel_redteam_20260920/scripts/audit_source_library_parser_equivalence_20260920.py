"""Metadata-only equivalence audit for FULL104 source_library parser semantics.

The existing 242 MB B/C/E sufficient-statistics artifact was produced before the
audit builder switched from legacy int(float(token)) coercion to the exact
production parser. Reusing that heavy artifact is lawful only if the two parsers
produce exactly the same integer for every authenticated metadata row in the
current 4,553,407-cell FULL104 substrate.

This script does not read expression matrices and does not inspect terminal
outcomes. It authenticates the block manifest and each metadata CSV, then checks
every source_library token.

Exit 0 means exact equivalence for the bound artifact. Any strict-parser
rejection, legacy-parser failure, value mismatch, row-count mismatch, or metadata
hash mismatch fails closed and requires rebuilding the heavy sufficient
statistics with the current parser.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_masking_streaming_executor_v1 import _parse_source_library

SCHEMA = "V5_FULL104_SOURCE_LIBRARY_PARSER_EQUIVALENCE_V1"
EXPECTED_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_CELLS = 4_553_407
BOUND_HEAVY_ARTIFACT_SHA256 = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"

_MANIFEST_COLUMNS = (
    "block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
    "counts_path", "counts_sha256", "meta_path", "meta_sha256",
)
_META_COLUMNS = (
    "selection_row", "canonical_cell_id", "donor_id", "expression_row",
    "primary_row_weight", "source_library",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_under(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError("manifest path must be relative")
    out = (root / rel).resolve()
    try:
        out.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("manifest path escapes root") from exc
    return out


def legacy_parse(token: str) -> int:
    return int(float(token))


def classify_token(token: str) -> str:
    t = token.strip().lower()
    if "e" in t:
        return "scientific"
    if "." in t:
        return "decimal"
    return "integer"


def run(
    manifest: Path,
    level4_root: Path,
    *,
    expected_manifest_sha256: str,
    expected_cells: int,
    bound_artifact_sha256: str,
) -> dict:
    if sha256_file(manifest) != expected_manifest_sha256:
        raise ValueError("block manifest hash mismatch")

    with manifest.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != _MANIFEST_COLUMNS:
            raise ValueError("block manifest schema mismatch")
        rows = [dict(r) for r in reader]
    if not rows:
        raise ValueError("block manifest is empty")

    total_rows = 0
    strict_rejections = 0
    legacy_rejections = 0
    mismatches = 0
    examples = []
    syntax_counts = {"integer": 0, "decimal": 0, "scientific": 0}

    for i, row in enumerate(rows):
        meta = resolve_under(level4_root, row["meta_path"])
        if not meta.is_file():
            raise ValueError(f"metadata missing: {row['block_key']}")
        if sha256_file(meta) != row["meta_sha256"]:
            raise ValueError(f"metadata hash mismatch: {row['block_key']}")

        expected_rows = int(row["rows"])
        block_rows = 0
        with meta.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != _META_COLUMNS:
                raise ValueError(f"metadata schema mismatch: {row['block_key']}")
            for record in reader:
                block_rows += 1
                token = str(record["source_library"]).strip()
                syntax_counts[classify_token(token)] += 1
                strict_ok = legacy_ok = True
                strict_err = legacy_err = None
                try:
                    strict = _parse_source_library(token)
                except Exception as exc:
                    strict_ok = False
                    strict_rejections += 1
                    strict = None
                    strict_err = type(exc).__name__
                try:
                    legacy = legacy_parse(token)
                except Exception as exc:
                    legacy_ok = False
                    legacy_rejections += 1
                    legacy = None
                    legacy_err = type(exc).__name__

                mismatch = (not strict_ok) or (not legacy_ok) or strict != legacy
                if mismatch:
                    mismatches += 1
                    if len(examples) < 20:
                        examples.append({
                            "block_key": row["block_key"],
                            "selection_row": record["selection_row"],
                            "token": token,
                            "strict_value": strict,
                            "legacy_value": legacy,
                            "strict_error": strict_err,
                            "legacy_error": legacy_err,
                        })

        if block_rows != expected_rows:
            raise ValueError(
                f"metadata row count mismatch: {row['block_key']} "
                f"observed={block_rows} expected={expected_rows}"
            )
        total_rows += block_rows
        if (i + 1) % 2000 == 0:
            print(f"checked {i+1}/{len(rows)} blocks rows={total_rows}", flush=True)

    if total_rows != expected_cells:
        raise ValueError(f"FULL104 row closure mismatch: {total_rows} != {expected_cells}")

    equivalent = mismatches == 0
    return {
        "schema": SCHEMA,
        "block_manifest_sha256": expected_manifest_sha256,
        "bound_heavy_artifact_sha256": bound_artifact_sha256,
        "blocks_checked": len(rows),
        "rows_checked": total_rows,
        "strict_rejections": strict_rejections,
        "legacy_rejections": legacy_rejections,
        "value_or_parse_mismatches": mismatches,
        "token_syntax_counts": syntax_counts,
        "mismatch_examples": examples,
        "strict_parser_equals_legacy_for_current_FULL104": equivalent,
        "reuse_decision": (
            "ALLOW_CONTENT_ADDRESSED_REUSE_WITH_CURRENT_PARSER"
            if equivalent
            else "REBUILD_HEAVY_SUFFICIENT_STATISTICS_REQUIRED"
        ),
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--level4-root", type=Path, required=True)
    ap.add_argument("--expected-manifest-sha256", default=EXPECTED_MANIFEST_SHA256)
    ap.add_argument("--expected-cells", type=int, default=EXPECTED_CELLS)
    ap.add_argument("--bound-heavy-artifact-sha256", default=BOUND_HEAVY_ARTIFACT_SHA256)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    try:
        receipt = run(
            args.manifest,
            args.level4_root,
            expected_manifest_sha256=args.expected_manifest_sha256,
            expected_cells=args.expected_cells,
            bound_artifact_sha256=args.bound_heavy_artifact_sha256,
        )
    except Exception as exc:
        print(f"ABORT: {type(exc).__name__}: {exc}")
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["strict_parser_equals_legacy_for_current_FULL104"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
