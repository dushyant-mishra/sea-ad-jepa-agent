#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

EXPECTED_TD_ARCHIVE_SHA256 = "c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417"
TD57C_MEMBER = "td57c_p0_hvs.json"


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def extract_td57c_member(archive: Path, expected_archive_sha256: str, out_path: Path) -> dict[str, Any]:
    archive = Path(archive)
    out_path = Path(out_path)
    actual_archive_sha = sha256_file(archive)
    if actual_archive_sha != expected_archive_sha256:
        raise RuntimeError(
            f"archive SHA mismatch: {actual_archive_sha} != {expected_archive_sha256}: {archive}"
        )
    with zipfile.ZipFile(archive) as z:
        hits = [name for name in z.namelist() if name == TD57C_MEMBER]
        if len(hits) != 1:
            raise RuntimeError(f"expected exactly one {TD57C_MEMBER}, found {len(hits)}")
        payload = z.read(TD57C_MEMBER)
    try:
        parsed = json.loads(payload)
    except Exception as e:
        raise RuntimeError(f"TD57C member is not valid JSON: {e}") from e
    if not isinstance(parsed, dict):
        raise RuntimeError("TD57C member must be a JSON object")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(payload)
    member_sha = hashlib.sha256(payload).hexdigest()
    return {
        "schema": "JEPA_TD57C_HISTORICAL_ARTIFACT_EXTRACTION_RECEIPT_V1",
        "status": "PASS_EXACT_TD57C_HISTORICAL_ARTIFACT_EXTRACTED",
        "archive_sha256": actual_archive_sha,
        "member": TD57C_MEMBER,
        "member_bytes": len(payload),
        "member_sha256": member_sha,
        "top_level_keys": sorted(parsed.keys()),
        "historical_only": True,
        "corrected_replay_ingested": False,
        "fit_authorized": False,
        "target_ranking_allowed": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()
    receipt = extract_td57c_member(args.archive, EXPECTED_TD_ARCHIVE_SHA256, args.out)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "member_sha256": receipt["member_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
