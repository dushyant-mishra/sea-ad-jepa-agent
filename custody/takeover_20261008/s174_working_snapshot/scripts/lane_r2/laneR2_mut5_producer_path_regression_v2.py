#!/usr/bin/env python
"""LANE R2 MUT-5 successor regression: exercise Claude's recovered producer end-to-end.

Historical V1 is never edited. The exact user-recovered `CLAUDE_R2_LOCAL_SCRIPTS.zip`
is stored in Git as base64 text. This successor decodes that exact archive, verifies its
SHA-256 and the recovered producer SHA-256, constructs a synthetic technical fixture,
then executes the recovered V1 producer as a subprocess.

The fixture makes every batch enrich the full motif collection. For each TF, support is
therefore constant across batch labels, so every exact TF-label assignment has the same
trace. The real producer must report the direct and extended label-permutation nulls as
degenerate constants.

Governance: TRAINING=OFF | synthetic/technical fixture only | no protected outcome
opened | no biological claim.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd

ARCHIVE_SHA256 = "337bd8823e006febc1f5103b00b48c7953e3a91e3fb257a4d02d90c04b4af571"
PRODUCER_SHA256 = "6accb237a29718668146eb3dab5c54638c969363d71a40a95fbab3c88925ee1e"
TFS = ["BACH1", "CEBPA", "ELF1", "IRF8", "MITF", "NRF1"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_archive_b64() -> Path:
    return repo_root() / "docs" / "agent" / "recovered-v52-20260928" / "CLAUDE_R2_LOCAL_SCRIPTS.zip.b64"


def recover_producer(archive_b64: Path, scratch: Path) -> tuple[Path, dict]:
    raw = base64.b64decode("".join(archive_b64.read_text(encoding="ascii").split()), validate=True)
    archive_sha = sha256_bytes(raw)
    if archive_sha != ARCHIVE_SHA256:
        raise RuntimeError(f"archive SHA mismatch: {archive_sha} != {ARCHIVE_SHA256}")

    archive_path = scratch / "CLAUDE_R2_LOCAL_SCRIPTS.zip"
    archive_path.write_bytes(raw)
    extract_dir = scratch / "recovered_scripts"
    extract_dir.mkdir(parents=True, exist_ok=True)
    # The original archive was created on Windows and stores backslashes in
    # member names. Normalize them explicitly so recovery is platform-stable.
    with zipfile.ZipFile(archive_path) as zf:
        for info in zf.infolist():
            normalized = Path(*info.filename.replace("\\", "/").split("/"))
            target = extract_dir / normalized
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(info))

    candidates = list(extract_dir.rglob("laneR2_stage75f_tf_specificity_control_v1.py"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one recovered producer, found {len(candidates)}")
    producer = candidates[0]
    producer_sha = sha256_bytes(producer.read_bytes())
    if producer_sha != PRODUCER_SHA256:
        raise RuntimeError(f"producer SHA mismatch: {producer_sha} != {PRODUCER_SHA256}")
    return producer, {"archive_sha256": archive_sha, "producer_sha256": producer_sha}


def write_fixture(root: Path) -> tuple[Path, Path]:
    pilot = root / "pilot"
    batch = root / "batch"
    pilot.mkdir(parents=True, exist_ok=True)
    batch.mkdir(parents=True, exist_ok=True)

    motifs = [f"M{i:02d}" for i in range(12)]
    direct = [TFS[i % len(TFS)] for i in range(len(motifs))]

    for tf in TFS:
        frame = pd.DataFrame({
            "MotifID": motifs,
            "batch_tf": [tf] * len(motifs),
            "enriched": [True] * len(motifs),
            "Direct_annot": direct,
            "Motif_similarity_annot": [""] * len(motifs),
            "Orthology_annot": [""] * len(motifs),
            "Motif_similarity_and_Orthology_annot": [""] * len(motifs),
        })
        frame.to_csv(
            pilot / f"stage75f_batch_{tf}.motif_enrichment_all.csv.gz",
            index=False,
            compression="gzip",
        )

        stem = f"stage75f_batch_0001_{tf}"
        (batch / f"{stem}.regions.bed").write_text(
            "\n".join(f"chr1\t{100+i*20}\t{110+i*20}" for i in range(8)) + "\n",
            encoding="utf-8",
        )
        (batch / f"{stem}.cistarget_regions.txt").write_text(
            "\n".join(f"chr1:{100+i*20}-{110+i*20}" for i in range(8)) + "\n",
            encoding="utf-8",
        )
        (batch / f"{stem}.genes.txt").write_text(
            "\n".join(f"GENE{i}" for i in range(8)) + "\n",
            encoding="utf-8",
        )
    return pilot, batch


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--archive-b64", default=str(default_archive_b64()))
    args = ap.parse_args()

    scratch = Path(args.scratch).resolve()
    out_dir = Path(args.out_dir).resolve()
    archive_b64 = Path(args.archive_b64).resolve()
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    producer, custody = recover_producer(archive_b64, scratch)
    pilot, batch = write_fixture(scratch / "fixture")
    producer_out = scratch / "producer_out"
    cmd = [
        sys.executable, str(producer),
        "--pilot-dir", str(pilot),
        "--batch-dir", str(batch),
        "--out-dir", str(producer_out),
        "--annot-permutations", "25",
        "--seed", "750261",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    report_path = producer_out / "laneR2_report_v1.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else None
    exact = (report or {}).get("T1_tf_label_permutation_exact", {})
    direct = exact.get("direct", {})
    extended = exact.get("extended", {})
    checks = {
        "archive_sha_verified": custody["archive_sha256"] == ARCHIVE_SHA256,
        "producer_sha_verified": custody["producer_sha256"] == PRODUCER_SHA256,
        "producer_exit_zero": proc.returncode == 0,
        "producer_report_exists": report_path.is_file(),
        "producer_structural_gate_passed": bool((report or {}).get("structural_gate_passed")),
        "direct_null_degenerate": direct.get("null_is_degenerate_constant") is True,
        "extended_null_degenerate": extended.get("null_is_degenerate_constant") is True,
        "direct_one_distinct_null_value": direct.get("n_distinct_null_values") == 1,
        "extended_one_distinct_null_value": extended.get("n_distinct_null_values") == 1,
        "producer_identifiability_flags_degenerate": (
            (report or {}).get("identifiability", {}).get("tf_label_permutation_null_degenerate") is True
        ),
    }
    passed = all(checks.values())
    result = {
        "audit": "laneR2_mut5_producer_path_regression_v2",
        "purpose": "exercise the exact recovered V1 producer path for the degenerate-null mutation",
        "fixture": "synthetic_technical_all_batches_enrich_full_motif_collection",
        "custody": custody,
        "producer_returncode": proc.returncode,
        "checks": checks,
        "direct": direct,
        "extended": extended,
        "verdict": "PASS_PRODUCER_DEGENERACY_PATH_EXERCISED" if passed else "FAIL_PRODUCER_DEGENERACY_PATH",
        "governance": "TRAINING=OFF | synthetic/technical fixture only | no protected outcome opened | no biological claim",
    }
    (out_dir / "laneR2_mut5_producer_path_regression_v2.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out_dir / "laneR2_mut5_producer_path_regression_v2.stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
    (out_dir / "laneR2_mut5_producer_path_regression_v2.stderr.txt").write_text(proc.stderr or "", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
