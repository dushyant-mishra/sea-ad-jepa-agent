#!/usr/bin/env python3
"""Read-only runtime preflight for FULL104 rare-tail molecular qualification.

This command MUST NOT load any RNA/count matrix. It authenticates the frozen
molecular authority, execution contract, sample, donor split, Level-4 manifest,
target eligibility, exact source bytes, and deterministic pair-address hashes.
Only after this receipt is reviewed may the separate molecular executor be
considered for an expression-opening run.
"""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from sea_ad_jepa.v5.full104_rare_tail_molecular_authority_v1 import (
    PANEL_PAIR_ADDRESS_SHA256,
)
from sea_ad_jepa.v5.full104_rare_tail_molecular_execution_contract_v1 import (
    Full104RareTailMolecularExecutionContractV1,
)
from sea_ad_jepa.v5.full104_rare_tail_molecular_primitives_v1 import (
    select_gene_views,
    select_pairs,
    verify_pair_address_hash,
)
from scripts.agent.run_full104_rare_tail_molecular_prequalification_v1_20260922 import (
    load_authority,
    load_manifest,
    load_sample,
    load_split,
    sha256_file,
)

EXPECTED_LEVEL4_BLOCKS = 8915
EXPECTED_STRICT_CORE = 17186

SOURCE_PATHS = {
    "runner_normalized_text_sha256":
        "scripts/agent/run_full104_rare_tail_molecular_prequalification_v1_20260922.py",
    "primitives_normalized_text_sha256":
        "src/sea_ad_jepa/v5/full104_rare_tail_molecular_primitives_v1.py",
    "authority_source_normalized_text_sha256":
        "src/sea_ad_jepa/v5/full104_rare_tail_molecular_authority_v1.py",
    "tail_selector_source_normalized_text_sha256":
        "src/sea_ad_jepa/v5/full104_rare_biology_preservation_authority_v1.py",
    "source_library_parser_source_normalized_text_sha256":
        "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py",
}


def normalized_text_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_execution_contract(path: Path) -> tuple[dict[str, Any], Full104RareTailMolecularExecutionContractV1]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_RARE_TAIL_MOLECULAR_EXECUTION_CONTRACT_V1":
        raise ValueError("molecular execution contract schema mismatch")
    names = {f.name for f in fields(Full104RareTailMolecularExecutionContractV1)}
    missing = names - set(payload)
    if missing:
        raise ValueError(f"molecular execution contract missing fields: {sorted(missing)}")
    contract = Full104RareTailMolecularExecutionContractV1(
        **{name: payload[name] for name in names}
    )
    contract.validate()
    if payload.get("contract_sha256") != contract.canonical_digest():
        raise ValueError("molecular execution contract digest mismatch")
    return payload, contract


def run_preflight(
    *,
    authority_path: Path,
    execution_contract_path: Path,
    sample_dir: Path,
    split_receipt_path: Path,
    level4_root: Path,
    target_eligibility_path: Path,
    structural_provenance_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    authority = load_authority(authority_path)
    contract_payload, contract = load_execution_contract(execution_contract_path)

    if contract.molecular_authority_sha256 != authority.canonical_digest():
        raise ValueError("execution contract binds a different molecular authority")
    if contract.sample_receipt_sha256 != authority.sample_receipt_sha256:
        raise ValueError("authority/contract sample receipt mismatch")
    if contract.outer_split_receipt_sha256 != authority.outer_split_receipt_sha256:
        raise ValueError("authority/contract outer split mismatch")
    if contract.full104_manifest_sha256 != authority.full104_manifest_sha256:
        raise ValueError("authority/contract FULL104 manifest mismatch")
    if contract.target_eligibility_file_sha256 != authority.target_eligibility_file_sha256:
        raise ValueError("authority/contract target eligibility mismatch")

    sample_payload, sample = load_sample(sample_dir)
    split = load_split(split_receipt_path)
    if sample_payload.get("sample_receipt_sha256") != contract.sample_receipt_sha256:
        raise ValueError("physical sample differs from execution contract")
    if split.get("receipt_sha256") != contract.outer_split_receipt_sha256:
        raise ValueError("physical split differs from execution contract")
    if not np.array_equal(sample["fold_by_donor"], np.asarray(split["fold_by_donor"])):
        raise ValueError("sample fold vector differs from authenticated split")
    if not np.array_equal(
        sample["donor_source_code"], np.asarray(split["donor_source_code"])
    ):
        raise ValueError("sample source vector differs from authenticated split")

    # This reads only the manifest CSV. It deliberately does not resolve or load
    # any counts_path from the manifest.
    manifest_rows = load_manifest(level4_root)
    if len(manifest_rows) != EXPECTED_LEVEL4_BLOCKS:
        raise ValueError("FULL104 Level-4 block count drifted")

    if sha256_file(target_eligibility_path) != contract.target_eligibility_file_sha256:
        raise ValueError("target-eligibility file hash mismatch")
    eligibility = json.loads(target_eligibility_path.read_text(encoding="utf-8"))
    if eligibility.get("schema") != "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1":
        raise ValueError("target-eligibility receipt schema mismatch")
    common = np.asarray(eligibility.get("strict_core_cols"), dtype=np.int64)
    if (
        common.ndim != 1
        or common.size != EXPECTED_STRICT_CORE
        or np.unique(common).size != common.size
        or np.any(common < 0)
    ):
        raise ValueError("strict common-core geometry drifted")

    provenance = json.loads(structural_provenance_path.read_text(encoding="utf-8"))
    if provenance.get("structural_preflight_sha256") != contract.structural_preflight_sha256:
        raise ValueError("structural preflight digest mismatch")
    if provenance.get("expression_opened") is not False:
        raise ValueError("structural provenance unexpectedly opened expression")
    if provenance.get("count_matrices_opened") is not False:
        raise ValueError("structural provenance unexpectedly opened count matrices")

    observed_source_hashes: dict[str, str] = {}
    root = repo_root.resolve()
    for field_name, relative in SOURCE_PATHS.items():
        path = (root / relative).resolve()
        path.relative_to(root)
        observed = normalized_text_sha256(path)
        expected = getattr(contract, field_name)
        if observed != expected:
            raise ValueError(f"{field_name} mismatch")
        observed_source_hashes[field_name] = observed

    pair_hashes: dict[str, dict[str, str]] = {}
    for panel in (0, 1):
        views = select_gene_views(common, panel)
        panel_hashes: dict[str, str] = {}
        for view in ("Z", "X", "Y"):
            _, addresses = select_pairs(views[view], panel=panel, view=view)
            observed = verify_pair_address_hash(addresses, panel=panel, view=view)
            if observed != PANEL_PAIR_ADDRESS_SHA256[panel][view]:
                raise ValueError("pair-address authority mismatch")
            panel_hashes[view] = observed
        pair_hashes[str(panel)] = panel_hashes

    return {
        "schema": "V5_FULL104_RARE_TAIL_MOLECULAR_READONLY_PREFLIGHT_V1",
        "state": "READY_FOR_REVIEW__NO_RNA_OPENED",
        "molecular_authority_sha256": authority.canonical_digest(),
        "execution_contract_sha256": contract.canonical_digest(),
        "sample_receipt_sha256": contract.sample_receipt_sha256,
        "outer_split_receipt_sha256": contract.outer_split_receipt_sha256,
        "full104_manifest_sha256": contract.full104_manifest_sha256,
        "target_eligibility_file_sha256": contract.target_eligibility_file_sha256,
        "structural_preflight_sha256": contract.structural_preflight_sha256,
        "level4_manifest_rows": len(manifest_rows),
        "strict_core_addresses": int(common.size),
        "pair_address_hashes": pair_hashes,
        "source_hashes": observed_source_hashes,
        "execution_contract_id": contract_payload["contract_id"],
        "expression_opened": False,
        "count_matrices_opened": False,
        "molecular_distances_computed": False,
        "molecular_outcome_opened": False,
        "td60_authorized": False,
        "teacher_tail_evaluation_authorized": False,
        "training_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--authority", type=Path, required=True)
    p.add_argument("--execution-contract", type=Path, required=True)
    p.add_argument("--sample-dir", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--target-eligibility", type=Path, required=True)
    p.add_argument("--structural-provenance", type=Path, required=True)
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    if args.out.exists():
        raise SystemExit("output already exists; refuse overwrite")

    receipt = run_preflight(
        authority_path=args.authority,
        execution_contract_path=args.execution_contract,
        sample_dir=args.sample_dir,
        split_receipt_path=args.split_receipt,
        level4_root=args.level4_root,
        target_eligibility_path=args.target_eligibility,
        structural_provenance_path=args.structural_provenance,
        repo_root=args.repo_root,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": receipt["state"],
        "expression_opened": False,
        "count_matrices_opened": False,
        "molecular_outcome_opened": False,
        "training_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
