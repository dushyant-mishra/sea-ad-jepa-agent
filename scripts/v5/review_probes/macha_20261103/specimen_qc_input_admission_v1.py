"""Fail-closed input admission for the frozen #513 specimen/QC probe (stdlib only).

usage: python -I specimen_qc_input_admission_v1.py <data-root> [--evidence-root DIR] [--run-probe OUT.json]

The original probe (scripts/v5/review_probes/macha_20261030/specimen_and_depositor_qc_probe.py)
checks no input hashes itself. This wrapper admits its inputs against receipts that already
exist, and runs it only after admission. It repeats no ETL audit. <data-root> holds the source data and the Stage81A2 files;
--evidence-root (default: <data-root>) holds the committed #513 ledger, probe and output.

Inherited receipts, each pinned by SHA-256:
  - the #513 ETL reuse ledger: lineage shards, the Level-4 block manifest and ASSET_AUTHENTICATION.csv;
  - the Stage81A2 freeze report (2026-08-07): the canonical asset registry;
  - the block manifest: per-file meta_sha256 for every Level-4 block meta CSV the probe reads;
  - ASSET_AUTHENTICATION.csv: path, bytes, mtime_ns and sha256 for every source H5AD.

Verification scope, declared per file class:
  REHASHED                   current SHA-256 equals the receipt
  STAT_ONLY_IDENTITY_INHERITED  H5ADs above the ledger's own re-hash limit: path, size and
                             mtime_ns equal the receipt; the bytes are NOT re-hashed and their
                             identity is inherited from ASSET_AUTHENTICATION.csv.
Every input must resolve inside its declared root (no symlinked parent, '..' or absolute escape).
--run-probe publishes the output only when it equals the committed output; otherwise it refuses
and keeps nothing. Replaying the real frozen probe is under a governance hold (REPLAY_HOLD).
Any missing, extra, unreceipted or mismatching input refuses. Reads file bytes for hashing and
the lineage (source, matrix_id) columns only; never expression, pathology, NPH52 H5ADs,
quarantined cells, reader_validation/oracle, DEV or SEALED data.
"""
from __future__ import annotations

import argparse
import csv
import glob
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

LEDGER = "results/target_discovery/unified_qualification_v1/JEPA_MACHA_ETL_REUSE_LEDGER_20261030.json"
FREEZE_REPORT = "results/v4/stage81a2_freeze_report.json"
PROBE = "scripts/v5/review_probes/macha_20261030/specimen_and_depositor_qc_probe.py"
PROBE_OUTPUT = "results/target_discovery/unified_qualification_v1/JEPA_MACHA_SPECIMEN_AND_DEPOSITOR_QC_20261030.json"
PINS = {
    LEDGER: "9b48639168cfb89d8f8ed2b6136423da66fb8ee867762a7c48ff0969a314ece9",
    FREEZE_REPORT: "0d0b7a41d18f2b82755c91fdfc827534f46ea988d025f0a91fbc2b3dd688e7f1",
    PROBE: "7e67314c80d368b7c2be12afae9ccadb7f2a200c4c96494bd5c9faa9a9f291b5",
    # LF-normalized SHA-256 of the committed output. The committed blob itself (raw SHA-256 952dc4c9...)
    # has CRLF line endings because the probe first ran on Windows.
    PROBE_OUTPUT: "4c76bd0b4ac6cba471544c0ada2464bd88d62b488d281131734f5a5b3301c1e2",
}
REGISTRY = "results/v4/stage81a2_canonical_asset_registry.csv"
F104 = "outputs/full104_v014_20260826/"
LINEAGE_GLOB = F104 + "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/*.csv.gz"
L4 = F104 + "03_phase2_state_derivation_v1/expression_level4/"
META_GLOB = L4 + "blocks/op*/block-*.meta.csv"
BLOCK_MANIFEST = L4 + "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
ASSET_AUTH = L4 + "ASSET_AUTHENTICATION.csv"
PROBE_SOURCES = ("SEA_AD", "HVS")  # the probe opens H5ADs for these sources only
# Governance hold (2026-11-03): the frozen probe reads SEA-AD 'Doublet score' and HVS 'is_primary_data',
# which are outside the analytic allowlist. Replaying the real frozen probe stays refused until a
# QC-only allowlist decision is recorded and this constant is cleared by a reviewed change.
REPLAY_HOLD = ("governance hold: replay of the frozen #513 QC probe re-reads 'Doublet score' and "
               "'is_primary_data'; refused until the QC-only allowlist decision is recorded")


class AdmissionRefused(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(root: Path, path: str) -> str:
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise AdmissionRefused(f"input resolves outside the data root: {path}") from exc


def _confined(base: Path, rel: str) -> Path:
    """A regular, non-symlink file whose fully resolved path stays inside base.

    Resolving the whole path closes escapes through a symlinked or junctioned parent
    directory, '..' components and absolute paths (GPT #529 R01)."""
    path = base / rel
    if path.is_symlink() or not path.is_file():
        raise AdmissionRefused(f"missing or symlinked input: {rel}")
    try:
        path.resolve(strict=True).relative_to(base)
    except (OSError, ValueError) as exc:
        raise AdmissionRefused(f"input resolves outside its declared root: {rel}") from exc
    return path


def admit(root: Path | str, *, evidence_root: Path | str | None = None, pins: dict = PINS) -> dict:
    root = Path(root).resolve()
    evidence = root if evidence_root is None else Path(evidence_root).resolve()
    reasons: list[str] = []

    def file(rel: str) -> Path:
        return _confined(evidence if rel in (LEDGER, PROBE, PROBE_OUTPUT) else root, rel)

    # 1. The receipts themselves are pinned.
    for rel in (LEDGER, FREEZE_REPORT):
        if _sha256(file(rel)) != pins[rel]:
            raise AdmissionRefused(f"receipt does not match its pin: {rel}")
    ledger = json.loads(file(LEDGER).read_text(encoding="utf-8"))
    limit = ledger["rehash_limit_bytes"]
    if type(limit) is not int or limit < 0:
        raise AdmissionRefused("ledger rehash_limit_bytes is malformed")
    verified = {}
    for row in ledger["rows"]:
        if row.get("classification") == "EXACT_SHA_ALREADY_VERIFIED":
            located = row.get("located_at", "").replace("\\", "/")
            if verified.setdefault(located, row["recorded_sha256"]) != row["recorded_sha256"]:
                raise AdmissionRefused(f"ledger records conflicting SHA-256 values for {located}")

    counts = {"REHASHED": {}, "STAT_ONLY_IDENTITY_INHERITED": {}}

    def rehashed(cls: str, rel: str, expected: str | None) -> None:
        if expected is None:
            reasons.append(f"no inherited receipt for {rel}")
        elif _sha256(file(rel)) != expected:
            reasons.append(f"SHA-256 differs from its receipt: {rel}")
        counts["REHASHED"][cls] = counts["REHASHED"].get(cls, 0) + 1

    # 2. Asset registry: its SHA is recorded once in the Stage81A2 freeze report.
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == Path(REGISTRY).name and isinstance(value, str):
                    found.append(value)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(json.loads(file(FREEZE_REPORT).read_text(encoding="utf-8")))
    if len(set(found)) != 1:
        raise AdmissionRefused("freeze report must record exactly one registry SHA-256")
    rehashed("asset_registry", REGISTRY, found[0])

    # 3. Level-4 receipts named by the ledger.
    for cls, rel in (("level4_block_manifest", BLOCK_MANIFEST), ("asset_authentication", ASSET_AUTH)):
        rehashed(cls, rel, verified.get(rel))
    if reasons:
        raise AdmissionRefused("; ".join(reasons))

    # 4. Lineage shards: the probe's glob must equal the ledger's shard rows, and each must match.
    shard_glob = {_rel(root, p) for p in glob.glob(str(root / LINEAGE_GLOB))}
    shard_rows = {p for p in verified if p.startswith(F104 + "01_full104_metadata_adapter/FULL104_ROW_LINEAGE_SHARDS/")}
    for rel in sorted(shard_glob ^ shard_rows):
        reasons.append(f"lineage shard present without receipt, or receipted but missing: {rel}")
    for rel in sorted(shard_glob & shard_rows):
        rehashed("lineage_shard", rel, verified[rel])

    # 5. Level-4 block meta CSVs: the probe's glob must equal the manifest's meta paths.
    with file(BLOCK_MANIFEST).open(newline="", encoding="utf-8") as fh:
        manifest = {L4 + row["meta_path"]: row["meta_sha256"] for row in csv.DictReader(fh)}
    meta_glob = {_rel(root, p) for p in glob.glob(str(root / META_GLOB))}
    for rel in sorted(meta_glob ^ set(manifest)):
        reasons.append(f"block meta present without manifest row, or listed but missing: {rel}")
    for rel in sorted(meta_glob & set(manifest)):
        rehashed("level4_block_meta", rel, manifest[rel])

    # 6. Source H5ADs the probe opens: registry path == authenticated path; hash or stat by the ledger limit.
    with file(REGISTRY).open(newline="", encoding="utf-8") as fh:
        registry = {row["dataset_id"]: row["matrix_path_or_object"] for row in csv.DictReader(fh)}
    with file(ASSET_AUTH).open(newline="", encoding="utf-8") as fh:
        auth = {row["matrix_id"]: row for row in csv.DictReader(fh)}
    matrices = set()
    for rel in sorted(shard_glob):
        with gzip.open(root / rel, "rt", newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["source"] in PROBE_SOURCES:
                    matrices.add(row["matrix_id"])
    for matrix_id in sorted(matrices):
        receipt = auth.get(matrix_id)
        if receipt is None or registry.get(matrix_id) != receipt["path"]:
            reasons.append(f"matrix without an authenticated path matching the registry: {matrix_id}")
            continue
        path = file(receipt["path"])
        stat = path.stat()
        if stat.st_size != int(receipt["bytes"]):
            reasons.append(f"size differs from ASSET_AUTHENTICATION: {receipt['path']}")
        elif stat.st_size <= limit:
            rehashed(f"h5ad_{receipt['source']}", receipt["path"], receipt["sha256"])
        elif stat.st_mtime_ns != int(receipt["mtime_ns"]):
            reasons.append(f"mtime differs from ASSET_AUTHENTICATION; re-hash required: {receipt['path']}")
        else:
            cls = f"h5ad_{receipt['source']}"
            counts["STAT_ONLY_IDENTITY_INHERITED"][cls] = counts["STAT_ONLY_IDENTITY_INHERITED"].get(cls, 0) + 1
    if not matrices:
        reasons.append("lineage names no SEA_AD or HVS matrix")
    if reasons:
        raise AdmissionRefused("; ".join(reasons[:20]) + (f" (+{len(reasons) - 20} more)" if len(reasons) > 20 else ""))

    return {
        "schema": "JEPA_MACHA_SPECIMEN_QC_INPUT_ADMISSION_V1",
        "status": "ADMITTED",
        "receipts": {rel: pins[rel] for rel in (LEDGER, FREEZE_REPORT)},
        "registry_sha256_from_freeze_report": found[0],
        "rehash_limit_bytes_from_ledger": limit,
        "verification_scope": counts,
        "probe_sources_with_h5ad_reads": list(PROBE_SOURCES),
        "matrices_admitted": len(matrices),
        "not_verified": "bytes of H5ADs above the re-hash limit (identity inherited from ASSET_AUTHENTICATION.csv); "
                        "provenance of the receipts themselves beyond their pins; files changing after admission",
    }


def run_probe(root: Path | str, out: Path | str, *, evidence_root: Path | str | None = None, pins: dict = PINS) -> dict:
    """Admit, run the pinned probe, and publish its output only if it equals the committed output.

    Any refusal (hold, existing output, admission, probe pin, probe failure, output mismatch)
    raises AdmissionRefused and leaves no output file (GPT #529 R02)."""
    if pins[PROBE] == PINS[PROBE] and REPLAY_HOLD:
        raise AdmissionRefused(REPLAY_HOLD)  # checked before any input is read
    out = Path(out)
    partial = out.with_name(out.name + ".partial")
    if out.exists() or out.is_symlink() or partial.exists() or partial.is_symlink():
        raise AdmissionRefused(f"replay output already exists: {out}")
    root = Path(root).resolve()
    evidence = root if evidence_root is None else Path(evidence_root).resolve()
    receipt = admit(root, evidence_root=evidence, pins=pins)
    probe = _confined(evidence, PROBE)
    if _sha256(probe) != pins[PROBE]:
        raise AdmissionRefused("frozen probe does not match its pin")
    try:
        with partial.open("xb") as fh:
            code = subprocess.run([sys.executable, "-I", str(probe), str(root)], stdout=fh).returncode
        if code != 0:
            raise AdmissionRefused(f"frozen probe exited with status {code}; no output kept")
        # Windows text-mode stdout writes CRLF; compare the LF-normalized bytes and report both digests.
        raw = partial.read_bytes()
        lf = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        if lf != pins[PROBE_OUTPUT]:
            raise AdmissionRefused(f"replay output (LF SHA-256 {lf}) differs from the committed #513 output; "
                                   "no output kept")
        partial.replace(out)
    finally:
        if partial.exists():
            partial.unlink()
    receipt.update({
        "status": "ADMITTED_AND_REPLAY_MATCHED",
        "probe_sha256": pins[PROBE],
        "probe_output_sha256_raw": hashlib.sha256(raw).hexdigest(),
        "probe_output_sha256_lf": lf,
        "probe_output_equals_committed_513_output": True,
    })
    return receipt


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed input admission for the frozen #513 QC probe")
    parser.add_argument("data_root")
    parser.add_argument("--evidence-root")
    parser.add_argument("--run-probe", metavar="OUT")
    args = parser.parse_args(argv)
    try:
        if args.run_probe:
            result = run_probe(args.data_root, args.run_probe, evidence_root=args.evidence_root)
        else:
            result = admit(args.data_root, evidence_root=args.evidence_root)
    except AdmissionRefused as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, indent=1))
        return 2
    print(json.dumps(result, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
