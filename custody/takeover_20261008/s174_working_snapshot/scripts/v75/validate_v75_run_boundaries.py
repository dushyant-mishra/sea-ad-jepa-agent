#!/usr/bin/env python3
"""Fail closed on protected-boundary or manifest-identity violations in V75 runs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def validate(receipt: dict) -> dict:
    checks = {}
    blockers = []

    def check(name: str, holds: bool, blocker: str) -> None:
        checks[name] = bool(holds)
        if not holds and blocker not in blockers:
            blockers.append(blocker)

    g = receipt.get("governance", {})
    check("pathology_absent", g.get("pathology_used") is False, "PATHOLOGY_BOUNDARY_VIOLATED")
    check("training_off", g.get("training") == "OFF", "TRAINING_BOUNDARY_VIOLATED")
    check("multimodal_training_off", g.get("multimodal_training") == "OFF", "MULTIMODAL_TRAINING_BOUNDARY_VIOLATED")
    check("stage4_not_authorized", g.get("stage4") == "NOT_AUTHORIZED", "STAGE4_BOUNDARY_VIOLATED")
    check("real_correspondence_unopened", g.get("real_correspondence") == "UNOPENED", "REAL_CORRESPONDENCE_BOUNDARY_VIOLATED")
    check("morabito_protected", g.get("Morabito") == "PROTECTED", "MORABITO_BOUNDARY_VIOLATED")
    check("recoverability_test_sealed", g.get("recoverability_TEST") == "SEALED", "RECOVERABILITY_TEST_BOUNDARY_VIOLATED")

    worlds = receipt.get("worlds", {})
    required_worlds = {"measurement_null_a", "measurement_null_b", "biology_positive"}
    check("required_control_worlds_present", required_worlds.issubset(worlds), "CONTROL_WORLDS_MISSING")

    digest_ok = True
    firewall_ok = True
    same_cell_ok = True
    for name in sorted(required_worlds & set(worlds)):
        world = worlds[name]
        specs = [
            ("truth_manifest", "truth_manifest_sha256"),
            ("rna_manifest", "rna_manifest_sha256"),
            ("multiome_manifest", "multiome_manifest_sha256"),
        ]
        for path_key, digest_key in specs:
            path_value = world.get(path_key)
            expected = world.get(digest_key)
            path = Path(path_value) if path_value else None
            if path is None or not path.exists() or not expected or sha256_file(path) != expected:
                digest_ok = False

        rna_path = Path(world["rna_manifest"]) if world.get("rna_manifest") else None
        multi_path = Path(world["multiome_manifest"]) if world.get("multiome_manifest") else None
        if rna_path and rna_path.exists():
            rna = json.loads(rna_path.read_text())
            if rna.get("hidden_truth_path_exposed") is not False:
                firewall_ok = False
        else:
            firewall_ok = False
        if multi_path and multi_path.exists():
            multi = json.loads(multi_path.read_text())
            if multi.get("model_facing_output_contains_hidden_truth") is not False:
                firewall_ok = False
            if multi.get("paired_same_cell_identity") is not True:
                same_cell_ok = False
        else:
            firewall_ok = False
            same_cell_ok = False

    check("manifest_digests_match_receipt", digest_ok, "MANIFEST_DIGEST_MISMATCH")
    check("model_facing_truth_firewalls_hold", firewall_ok, "MODEL_FACING_TRUTH_FIREWALL_FAILED")
    check("paired_multiome_same_cell_identity", same_cell_ok, "PAIRED_MULTIOME_IDENTITY_FAILED")

    status = "PASS__PROTECTED_BOUNDARIES_HOLD" if not blockers else "REFUSED__PROTECTED_BOUNDARY_VIOLATION"
    return {
        "schema": "V75_RUN_BOUNDARY_VALIDATION_V1",
        "status": status,
        "checks": checks,
        "blockers": blockers,
        "claim_scope": "machine validation of protected-data and manifest-integrity boundaries only; no biological or learned-state qualification",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    receipt = json.loads(Path(args.receipt).read_text())
    result = validate(receipt)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text)
    print(text, end="")
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
