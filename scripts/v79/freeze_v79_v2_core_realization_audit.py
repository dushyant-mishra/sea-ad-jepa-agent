#!/usr/bin/env python3
"""Freeze controller-audit evidence from the realized V79 V2_CORE world set. Exact byte copies only.

The realized directory on the locked Windows machine is read-only authority. This script:
  1. checks that the source checkout is the exact, clean authority head;
  2. independently recomputes SHA-256 for every file in the realized directory and requires exactly 498 files, the
     root-manifest SHA and the full directory digest. The digest uses the writer's published rule: sorted portable
     paths, ``rel 0x00 sha256(bytes) 0x00``. It is reimplemented here, not imported;
  3. requires the recomputed per-file ledger to equal the ledger saved right after realization;
  4. copies, byte for byte, the three top-level files, the blinded-fit index, the 12 blinded per-world manifests
     and the whole controller-truth tree. That tree holds the 12 manifests, support, operator design, the planted
     detection/positive/new-donor truth and the operator offsets. Every copy is verified against the ledger;
  5. writes the complete 498-line ledger (``relative_path<TAB>sha256``) and an audit-freeze receipt;
  6. re-hashes all 498 source files and requires them unchanged.
It never imports the generator or writer, never writes into the source, and never copies observation arrays or
fit-side design arrays. It runs no benchmark, fit or score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE_HEAD = "cd6425b29f3fbd70b6d93351feb7c188f8b17cc8"
AUTHORIZATION_REL = "results/v79/v2_core_qualification/authorization/V79_V2_CORE_WORLD_REALIZATION_AUTHORIZATION_V1.json"
AUTHORIZATION_SHA = "8a2140f8d8ae721f403871de4465db5f0f8caaf3ffa1be9ee71cff7f6d96bba9"
REALIZED_REL = "results/v79/v2_core_qualification/realized_worlds_v1"
ROOT_MANIFEST = "V79_V2_CORE_WORLD_SET_MANIFEST_V1.json"
ROOT_MANIFEST_SHA = "84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de"
DIRECTORY_DIGEST = "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286"
RUNTIME_RECEIPT_SHA = "781d880ada58dfde06c9074401a15d49cf17887460987865655837884dbf9184"
BLINDED_INDEX_REL = "blinded_fit_inputs/V79_V2_CORE_BLINDED_FIT_INDEX_V1.json"
BLINDED_INDEX_SHA = "8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40"
FILE_COUNT = 498
WORLD_COUNT = 12
MODE = "QUALIFICATION_TRUTH_FREEZE"
LEDGER_NAME = "REALIZED_WORLDS_V1_COMPLETE_SHA256_LEDGER.tsv"
RECEIPT_NAME = "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1.json"
TOP_LEVEL = (ROOT_MANIFEST, "runtime_environment_receipt.json", "realization_authorization.json")


def stop(msg: str) -> None:
    raise SystemExit(f"STOP: {msg}")


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(Path(path).read_bytes())


def git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()


def ledger_of(source: Path) -> dict[str, str]:
    files = sorted((p for p in source.rglob("*") if p.is_file()), key=lambda p: p.relative_to(source).as_posix())
    return {p.relative_to(source).as_posix(): sha_file(p) for p in files}


def digest_of(ledger: dict[str, str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(ledger):
        h.update(rel.encode("utf-8")); h.update(b"\0"); h.update(bytes.fromhex(ledger[rel])); h.update(b"\0")
    return h.hexdigest()


def read_records_ledger(path: Path) -> dict[str, str]:
    """The ledger saved after realization: `sha256sum` lines over `find . -type f`, i.e. '<sha> *./rel'."""
    out: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        digest, _, rel = line.partition(" ")
        rel = rel.lstrip(" *")
        rel = rel[2:] if rel.startswith("./") else rel
        if rel in out:
            stop(f"duplicate path in saved records ledger: {rel}")
        out[rel] = digest
    return out


def selected_for_copy(ledger: dict[str, str]) -> list[str]:
    keep = []
    for rel in ledger:
        parts = rel.split("/")
        if rel in TOP_LEVEL or rel == BLINDED_INDEX_REL:
            keep.append(rel)
        elif parts[0] == "blinded_fit_inputs" and len(parts) == 3 and parts[2] == "manifest.json":
            keep.append(rel)
        elif parts[0] == "controller_truth":
            keep.append(rel)
    return sorted(keep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-checkout", required=True, help="the locked-Windows checkout that realized the worlds")
    ap.add_argument("--records-ledger", required=True, help="per-file sha256sum ledger saved right after realization")
    ap.add_argument("--out", required=True, help="new audit-freeze directory inside this repository")
    a = ap.parse_args()
    checkout, out = Path(a.source_checkout).resolve(), Path(a.out).resolve()
    source = checkout / REALIZED_REL

    # 1. exact clean authority checkout; the realized directory is git-ignored there
    if git(checkout, "rev-parse", "HEAD") != SOURCE_HEAD:
        stop("source checkout is not the authority head")
    if git(checkout, "status", "--porcelain"):
        stop("source checkout is not clean")
    if sha_file(checkout / AUTHORIZATION_REL) != AUTHORIZATION_SHA:
        stop("authorization receipt SHA mismatch in the source checkout")

    # 2. independent recompute
    ledger = ledger_of(source)
    if len(ledger) != FILE_COUNT:
        stop(f"realized file count {len(ledger)} != {FILE_COUNT}")
    if ledger.get(ROOT_MANIFEST) != ROOT_MANIFEST_SHA:
        stop("root manifest SHA mismatch")
    digest = digest_of(ledger)
    if digest != DIRECTORY_DIGEST:
        stop(f"directory digest mismatch: {digest}")
    for rel, want in ((TOP_LEVEL[1], RUNTIME_RECEIPT_SHA), (BLINDED_INDEX_REL, BLINDED_INDEX_SHA)):
        if ledger.get(rel) != want:
            stop(f"SHA mismatch: {rel}")

    # 3. equal to the ledger saved after realization
    saved = read_records_ledger(Path(a.records_ledger))
    if saved != ledger:
        stop(f"recomputed ledger differs from the saved records ledger: only_saved={sorted(set(saved) - set(ledger))[:5]} "
             f"only_now={sorted(set(ledger) - set(saved))[:5]} "
             f"changed={sorted(k for k in set(saved) & set(ledger) if saved[k] != ledger[k])[:5]}")

    root = json.loads((source / ROOT_MANIFEST).read_bytes().decode("utf-8"))
    if (root.get("world_count"), root.get("mode"), root.get("runtime_environment_receipt_sha256"),
            root.get("blinded_fit_index_sha256")) != (WORLD_COUNT, MODE, RUNTIME_RECEIPT_SHA, BLINDED_INDEX_SHA):
        stop("root manifest does not bind the reported count/mode/receipt/index")
    for key in ("benchmark_run", "training_authorized"):
        if root.get(key) is not False:
            stop(f"root manifest {key} is not false")
    if root.get("qualification_fits_run") != 0:
        stop("root manifest qualification_fits_run is not 0")

    # 4. exact byte copies
    if out.exists():
        stop(f"audit-freeze directory already exists: {out}")
    copy = selected_for_copy(ledger)
    truth = [r for r in copy if r.startswith("controller_truth/")]
    if len([r for r in copy if r.startswith("blinded_fit_inputs/") and r.endswith("/manifest.json")]) != WORLD_COUNT or \
            len([r for r in truth if r.endswith("/manifest.json")]) != WORLD_COUNT:
        stop("expected 12 blinded and 12 truth manifests")
    if any("/observations/" in r for r in copy):
        stop("an observation array was selected for copy")
    package = out / "package"
    for rel in copy:
        dst = package / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, dst)
        if sha_file(dst) != ledger[rel]:
            stop(f"copied bytes differ from the ledger: {rel}")

    # 5. complete ledger and receipt
    ledger_raw = "".join(f"{rel}\t{ledger[rel]}\n" for rel in sorted(ledger)).encode("utf-8")
    (out / LEDGER_NAME).write_bytes(ledger_raw)
    not_copied = sorted(set(ledger) - set(copy))

    # 6. the source is unchanged by this run
    if ledger_of(source) != ledger:
        stop("source realized directory changed during the freeze")

    receipt = {
        "schema": "V79_V2_CORE_REALIZATION_AUDIT_FREEZE_RECEIPT_V1",
        "status": "REALIZATION_AUDIT_EVIDENCE_FROZEN__CONTROLLER_INDEPENDENT_BYTE_AUDIT_REQUIRED",
        "source_checkout_sha": SOURCE_HEAD,
        "source_realized_directory": f"{REALIZED_REL} (git-ignored, locked Windows checkout; read-only)",
        "authorization_receipt_sha256": AUTHORIZATION_SHA,
        "root_manifest_sha256": ROOT_MANIFEST_SHA,
        "world_set_directory_digest": digest,
        "directory_digest_rule": "sha256 over sorted portable relative paths of: utf8(rel) 0x00 sha256(file bytes) 0x00",
        "total_file_count": len(ledger),
        "world_count": WORLD_COUNT,
        "mode": MODE,
        "runtime_environment_receipt_sha256": RUNTIME_RECEIPT_SHA,
        "blinded_fit_index_sha256": BLINDED_INDEX_SHA,
        "complete_ledger": LEDGER_NAME,
        "complete_ledger_sha256": sha_bytes(ledger_raw),
        "complete_ledger_equals_post_realization_records_ledger": True,
        "source_unchanged_after_freeze": True,
        "committed_package_root": "package/",
        "committed_package_file_count": len(copy),
        "committed_top_level_files": list(TOP_LEVEL) + [BLINDED_INDEX_REL],
        "committed_blinded_manifest_count": WORLD_COUNT,
        "committed_controller_truth_file_count": len(truth),
        "committed_controller_truth_manifest_count": WORLD_COUNT,
        "committed_controller_truth_authority_array_count": len(truth) - WORLD_COUNT,
        "not_committed_file_count": len(not_copied),
        "not_committed_observation_array_count": sum("/observations/" in r for r in not_copied),
        "not_committed_note": ("blinded observation arrays and fit-side design/support arrays were intentionally "
                               "not committed; they remain on the locked Windows machine and are hash-bound by the "
                               "complete 498-file ledger and the committed blinded manifests"),
        "copy_method": "shutil.copyfile byte copy; every copy re-hashed against the ledger; nothing reserialized",
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "scoring_run": False,
        "real_train_posterior_run": False,
        "factorial_science_run": False,
        "training_authorized": False,
    }
    receipt_raw = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (out / RECEIPT_NAME).write_bytes(receipt_raw)
    print(json.dumps({"complete_ledger_sha256": receipt["complete_ledger_sha256"],
                      "audit_freeze_receipt_sha256": sha_bytes(receipt_raw), "world_set_directory_digest": digest,
                      "root_manifest_sha256": ledger[ROOT_MANIFEST], "total_file_count": len(ledger),
                      "committed_package_file_count": len(copy),
                      "committed_controller_truth_file_count": len(truth),
                      "not_committed_observation_array_count": receipt["not_committed_observation_array_count"]},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
