#!/usr/bin/env python3
"""Build the pre-outcome Audit-B N1 execution authority from verified B4 state."""
from __future__ import annotations

import argparse
from dataclasses import asdict, fields
import json
from pathlib import Path

from sea_ad_jepa.v5.audit_b_execution_preflight_v2 import load_contract
from sea_ad_jepa.v5.audit_b_n1_execution_authority_v1 import (
    AuditBN1ExecutionAuthorityV1,
    B4_CONTRACT_SHA256,
    B4_RUNTIME_PREFLIGHT_SOURCE_SHA,
    B4_RUNTIME_PREFLIGHT_STATE,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--b4-contract", type=Path, required=True)
    p.add_argument("--b4-preflight-receipt", type=Path, required=True)
    p.add_argument(
        "--b4-preflight-source-sha",
        default=B4_RUNTIME_PREFLIGHT_SOURCE_SHA,
    )
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise SystemExit("output already exists; refuse overwrite")

    contract = load_contract(args.b4_contract)
    if contract.canonical_digest() != B4_CONTRACT_SHA256:
        raise SystemExit("supplied B4 contract is not the frozen final B4 contract")
    contract.require_sample_level_ready("N1")

    receipt = json.loads(args.b4_preflight_receipt.read_text(encoding="utf-8"))
    required = {
        "state": B4_RUNTIME_PREFLIGHT_STATE,
        "contract_sha256": B4_CONTRACT_SHA256,
        "authorized_sample_level": "N1",
        "direct_n2_n3_execution_authorized": False,
        "burden_computed": False,
        "masks_executed": False,
        "terminal_masking_outcomes_inspected": False,
        "terminal_masking_authorized": False,
        "training_authorized": False,
    }
    for name, expected in required.items():
        if receipt.get(name) != expected:
            raise SystemExit(f"B4 preflight receipt field mismatch: {name}")

    authority = AuditBN1ExecutionAuthorityV1(
        authority_id="JEPA_V5_FULL104_AUDIT_B_N1_EXECUTION_AUTHORITY_V1",
        b4_runtime_preflight_source_sha=str(args.b4_preflight_source_sha),
    )
    authority.validate()
    payload = {
        "schema": "V5_AUDIT_B_N1_EXECUTION_AUTHORITY_V1",
        **asdict(authority),
        "authority_sha256": authority.canonical_digest(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": "AUDIT_B_N1_EXECUTION_AUTHORITY_MATERIALIZED",
        "authority_sha256": authority.canonical_digest(),
        "sample_level": "N1",
        "target_count": 256,
        "n2_directly_authorized": False,
        "terminal_masking_authorized": False,
        "training_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
