#!/usr/bin/env python3
"""Outcome-blind V2 rare-tail preflight: bind the PHYSICAL structural evidence.

Success is READY_FOR_INDEPENDENT_REVIEW only. This program never accesses
expression/count blocks, computes molecular distances, or launches the executor.
The frozen V1 preflight and scientific runner are left byte-for-byte unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from scripts.agent.preflight_full104_rare_tail_molecular_readonly_v1_20260922 import (
    load_execution_contract,
    normalized_text_sha256,
    run_preflight,
    sha256_file,
)
from scripts.agent.validate_full104_rare_tail_structural_preflight_v1_20260922 import (
    validate_structural_receipt,
)

STRUCTURAL_RECEIPT_FILE_SHA256 = (
    "7b9ff5938e3940fca8640e98217b1c9cf075597305d80bbc04c6df15d1eae801"
)
STRUCTURAL_PROVENANCE_FILE_SHA256 = (
    "3f1ecdffbeea6d942ee5dc8d488a8de98cb9c99d00c79cd10a7bb695bd9d9d"
)
EXPECTED_STRUCTURAL_TERMINAL = (
    "STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN"
)
EXPECTED_STRUCTURAL_VALIDATOR_STATUS = (
    "PASS_FULL104_RARE_TAIL_STRUCTURAL_PREFLIGHT_RECEIPT_V1"
)
EXPECTED_V1_STATE = "READY_FOR_REVIEW__NO_RNA_OPENED"
SCHEMA = "V5_FULL104_RARE_TAIL_MOLECULAR_READONLY_PREFLIGHT_V2"


def canonical_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def authenticate_structural_evidence(
    *,
    structural_receipt_path: Path,
    structural_provenance_path: Path,
    sample_dir: Path,
    expected_canonical_sha256: str,
) -> dict[str, Any]:
    """Verify independent bytes and semantics, not self-declared SHA strings."""
    if sha256_file(structural_receipt_path) != STRUCTURAL_RECEIPT_FILE_SHA256:
        raise ValueError("physical structural receipt file SHA-256 mismatch")
    if sha256_file(structural_provenance_path) != STRUCTURAL_PROVENANCE_FILE_SHA256:
        raise ValueError("physical structural provenance file SHA-256 mismatch")
    receipt = json.loads(structural_receipt_path.read_text(encoding="utf-8"))
    provenance = json.loads(structural_provenance_path.read_text(encoding="utf-8"))
    validated = validate_structural_receipt(receipt, sample_dir=sample_dir)
    if validated.get("status") != EXPECTED_STRUCTURAL_VALIDATOR_STATUS:
        raise ValueError("structural validation did not PASS its own scope")
    if validated.get("structural_terminal") != EXPECTED_STRUCTURAL_TERMINAL:
        raise ValueError("physical structural receipt is not structurally possible")
    if validated.get("structural_preflight_sha256") != expected_canonical_sha256:
        raise ValueError("physical structural receipt canonical SHA-256 mismatch")
    if provenance.get("structural_preflight_sha256") != expected_canonical_sha256:
        raise ValueError("structural provenance declares a different result")
    if provenance.get("structural_preflight_file_sha256") != STRUCTURAL_RECEIPT_FILE_SHA256:
        raise ValueError("structural provenance has a different physical result SHA-256")
    if provenance.get("structural_terminal") != EXPECTED_STRUCTURAL_TERMINAL:
        raise ValueError("structural provenance has the wrong terminal")
    for flag in ("expression_opened", "count_matrices_opened",
                 "molecular_outcome_opened", "training_authorized"):
        if provenance.get(flag) is not False:
            raise ValueError("structural provenance unsafe or missing flag: " + flag)
    for flag in ("expression_opened", "count_matrix_opened",
                 "molecular_distance_computed", "zxy_molecular_outcome_opened",
                 "training_authorized"):
        if receipt.get(flag) is not False:
            raise ValueError("structural receipt unsafe or missing flag: " + flag)
    return {
        "structural_receipt_file_sha256": STRUCTURAL_RECEIPT_FILE_SHA256,
        "structural_provenance_file_sha256": STRUCTURAL_PROVENANCE_FILE_SHA256,
        "structural_validation_status": validated["status"],
        "structural_preflight_sha256": validated["structural_preflight_sha256"],
    }


def run_preflight_v2(
    *,
    authority_path: Path,
    execution_contract_path: Path,
    sample_dir: Path,
    split_receipt_path: Path,
    level4_root: Path,
    target_eligibility_path: Path,
    structural_receipt_path: Path,
    structural_provenance_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    _, contract = load_execution_contract(execution_contract_path)
    structural = authenticate_structural_evidence(
        structural_receipt_path=structural_receipt_path,
        structural_provenance_path=structural_provenance_path,
        sample_dir=sample_dir,
        expected_canonical_sha256=contract.structural_preflight_sha256,
    )
    previous = run_preflight(
        authority_path=authority_path,
        execution_contract_path=execution_contract_path,
        sample_dir=sample_dir,
        split_receipt_path=split_receipt_path,
        level4_root=level4_root,
        target_eligibility_path=target_eligibility_path,
        structural_provenance_path=structural_provenance_path,
        repo_root=repo_root,
    )
    if previous.get("state") != EXPECTED_V1_STATE:
        raise ValueError("frozen V1 preflight did not complete")
    for flag in ("expression_opened", "count_matrices_opened",
                 "molecular_distances_computed", "molecular_outcome_opened",
                 "td60_authorized", "teacher_tail_evaluation_authorized",
                 "training_authorized"):
        if previous.get(flag) is not False:
            raise ValueError("V1 preflight unsafe or missing flag: " + flag)
    if previous.get("structural_preflight_sha256") != structural["structural_preflight_sha256"]:
        raise ValueError("V1 preflight structural binding disagrees with physical receipt")

    root = repo_root.resolve()
    payload = {
        "schema": SCHEMA,
        "state": "READY_FOR_INDEPENDENT_REVIEW__NO_RNA_OPENED",
        "v1_preflight_canonical_sha256": canonical_digest(previous),
        "v1_preflight_source_normalized_sha256": normalized_text_sha256(
            root / "scripts/agent/preflight_full104_rare_tail_molecular_readonly_v1_20260922.py"
        ),
        "v2_preflight_source_normalized_sha256": normalized_text_sha256(Path(__file__)),
        "structural_validator_source_normalized_sha256": normalized_text_sha256(
            root / "scripts/agent/validate_full104_rare_tail_structural_preflight_v1_20260922.py"
        ),
        "molecular_authority_sha256": previous["molecular_authority_sha256"],
        "execution_contract_sha256": previous["execution_contract_sha256"],
        "sample_receipt_sha256": previous["sample_receipt_sha256"],
        "outer_split_receipt_sha256": previous["outer_split_receipt_sha256"],
        "full104_manifest_sha256": previous["full104_manifest_sha256"],
        "target_eligibility_file_sha256": previous["target_eligibility_file_sha256"],
        "source_hashes": previous["source_hashes"],
        "pair_address_hashes": previous["pair_address_hashes"],
        **structural,
        "expression_opened": False,
        "count_matrices_opened": False,
        "molecular_distances_computed": False,
        "molecular_outcome_opened": False,
        "td60_authorized": False,
        "teacher_tail_evaluation_authorized": False,
        "training_authorized": False,
    }
    return {**payload, "receipt_sha256": canonical_digest(payload)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--authority", type=Path, required=True)
    p.add_argument("--execution-contract", type=Path, required=True)
    p.add_argument("--sample-dir", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--target-eligibility", type=Path, required=True)
    p.add_argument("--structural-receipt", type=Path, required=True)
    p.add_argument("--structural-provenance", type=Path, required=True)
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    receipt = run_preflight_v2(
        authority_path=args.authority,
        execution_contract_path=args.execution_contract,
        sample_dir=args.sample_dir,
        split_receipt_path=args.split_receipt,
        level4_root=args.level4_root,
        target_eligibility_path=args.target_eligibility,
        structural_receipt_path=args.structural_receipt,
        structural_provenance_path=args.structural_provenance,
        repo_root=args.repo_root,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(args.out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(receipt, output, sort_keys=True, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps({"state": receipt["state"],
                      "receipt_sha256": receipt["receipt_sha256"],
                      "expression_opened": False,
                      "count_matrices_opened": False,
                      "training_authorized": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
