#!/usr/bin/env python3
"""Fail-closed promotion gate for V73 synthetic stress execution.

The coupled architecture may be CI-green while still being scientifically unready for a
100K promotion. This validator makes that distinction executable. It refuses promotion
while donor-size structure or source/operator nesting remain placeholder assignments, or
while required source-composition/resource evidence is missing.

It does not generate data and cannot authorize 500K/full-scale execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

AMENDMENT = Path("results/v64/V73_SYNTHETIC_STRESS_TWIN_CONTRACT_AMENDMENT_1_SOURCE_COMPOSITION.json")


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def validate(root: Path, resource_receipt: Path | None = None) -> dict:
    truth_manifest = root / "hidden_truth" / "TRUTH_MANIFEST.json"
    full_manifest = root / "observable_raw" / "FULL104_like_sharded" / "FULL104_SHARDED_MANIFEST.json"
    multi_manifest = root / "observable_raw" / "PAIRED_MULTIOME_like_sharded" / "PAIRED_MULTIOME_SHARDED_MANIFEST.json"
    frag_manifest = root / "observable_raw" / "PAIRED_MULTIOME_fragments" / "SYNTHETIC_FRAGMENT_MANIFEST.json"

    required = [AMENDMENT, truth_manifest, full_manifest, multi_manifest, frag_manifest]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        return dict(
            schema="V73_SYNTHETIC_STRESS_PROMOTION_READINESS_V1",
            status="BLOCKED",
            missing_required_artifacts=missing,
            blockers=["MISSING_REQUIRED_ARTIFACTS"],
            authorized_scale="CI_ONLY",
        )

    amendment = json.loads(AMENDMENT.read_text())
    tm = json.loads(truth_manifest.read_text())
    fm = json.loads(full_manifest.read_text())
    mm = json.loads(multi_manifest.read_text())
    gm = json.loads(frag_manifest.read_text())

    blockers = []
    holds = {}

    holds["source_amendment_is_prospective"] = (
        amendment.get("status") == "PROSPECTIVE__BEFORE_100K_PROMOTION"
    )
    if not holds["source_amendment_is_prospective"]:
        blockers.append("SOURCE_COMPOSITION_AMENDMENT_NOT_PROSPECTIVE")

    expected_sources = tm.get("source_counts")
    holds["source_counts_match_across_observers"] = (
        expected_sources is not None
        and fm.get("source_counts") == expected_sources
        and mm.get("source_counts") == expected_sources
    )
    if not holds["source_counts_match_across_observers"]:
        blockers.append("SOURCE_COUNTS_DISAGREE_ACROSS_OBSERVERS")

    donor_status = tm.get("donor_assignment_status", "MISSING")
    operator_status = tm.get("operator_assignment_status", "MISSING")
    holds["donor_structure_qualified"] = donor_status.startswith("QUALIFIED_")
    holds["operator_structure_qualified"] = operator_status.startswith("QUALIFIED_")
    if not holds["donor_structure_qualified"]:
        blockers.append("DONOR_STRUCTURE_NOT_QUALIFIED")
    if not holds["operator_structure_qualified"]:
        blockers.append("SOURCE_OPERATOR_STRUCTURE_NOT_QUALIFIED")

    holds["paired_multiome_same_cell"] = mm.get("paired_same_cell_identity") is True
    holds["paired_multiome_truth_firewall"] = (
        mm.get("model_facing_output_contains_hidden_truth") is False
    )
    holds["fragment_truth_firewall"] = gm.get("hidden_truth_read") is False
    for k in ("paired_multiome_same_cell", "paired_multiome_truth_firewall", "fragment_truth_firewall"):
        if not holds[k]:
            blockers.append(k.upper() + "_FAILED")

    resource = None
    if resource_receipt is not None:
        if not resource_receipt.exists():
            blockers.append("RESOURCE_RECEIPT_MISSING")
        else:
            resource = json.loads(resource_receipt.read_text())
            measured = resource.get("measured", {})
            projection = resource.get("calibrated_projection", {})
            holds["fragment_resource_calibrated"] = (
                measured.get("fragment_bytes_per_cell", 0) > 0
                and projection.get("calibration_is_ci_scale_only") is True
                and projection.get("requires_100k_measurement_before_500k_promotion") is True
            )
            if not holds["fragment_resource_calibrated"]:
                blockers.append("FRAGMENT_RESOURCE_CALIBRATION_INCOMPLETE")
    else:
        holds["fragment_resource_calibrated"] = False
        blockers.append("RESOURCE_RECEIPT_NOT_SUPPLIED")

    status = "READY_FOR_100K_STRESS_ONLY" if not blockers else "BLOCKED"
    return dict(
        schema="V73_SYNTHETIC_STRESS_PROMOTION_READINESS_V1",
        status=status,
        authorized_scale=("100K_STRESS_ONLY" if status.startswith("READY") else "CI_ONLY"),
        explicitly_not_authorized=["500K_STRESS", "FULL_4553407", "TRAINING"],
        checks=holds,
        blockers=blockers,
        current_assignment_status=dict(donor=donor_status, operator=operator_status),
        source_counts=expected_sources,
        bindings=dict(
            source_amendment=dict(path=str(AMENDMENT), sha256=sha256_file(AMENDMENT)),
            truth_manifest=dict(path=str(truth_manifest), sha256=sha256_file(truth_manifest)),
            full104_manifest=dict(path=str(full_manifest), sha256=sha256_file(full_manifest)),
            paired_multiome_manifest=dict(path=str(multi_manifest), sha256=sha256_file(multi_manifest)),
            fragment_manifest=dict(path=str(frag_manifest), sha256=sha256_file(frag_manifest)),
            resource_receipt=(dict(path=str(resource_receipt), sha256=sha256_file(resource_receipt))
                              if resource_receipt and resource_receipt.exists() else None),
        ),
        real_data_opened=False,
        training_authorized=False,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--resource-receipt", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = validate(Path(a.root), Path(a.resource_receipt) if a.resource_receipt else None)
    text = json.dumps(out, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text)
    print(text, end="")
    return 0 if out["status"].startswith("READY") else 2


if __name__ == "__main__":
    raise SystemExit(main())
