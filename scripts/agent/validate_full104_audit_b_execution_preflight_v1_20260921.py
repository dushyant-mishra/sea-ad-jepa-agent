#!/usr/bin/env python3
"""Validate FULL104 Audit-B execution readiness without computing any burden."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.audit_b_execution_preflight_v1 import (
    require_contract_ready,
    verify_runtime_bindings,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--sample-freeze", type=Path, required=True)
    p.add_argument("--heavy-artifact", type=Path, required=True)
    p.add_argument("--heavy-qualification-receipt", type=Path, required=True)
    p.add_argument("--rng-authority", type=Path, required=True)
    p.add_argument("--mask-plan-generator", type=Path, required=True)
    p.add_argument("--burden-estimator-source", type=Path, required=True)
    p.add_argument("--full104-manifest", type=Path, required=True)
    p.add_argument("--canonical-registry", type=Path, required=True)
    p.add_argument("--repo-root", type=Path, required=True)
    args = p.parse_args()

    contract = require_contract_ready(args.contract)
    observed = verify_runtime_bindings(
        contract,
        sample_freeze=args.sample_freeze,
        heavy_artifact=args.heavy_artifact,
        heavy_qualification_receipt=args.heavy_qualification_receipt,
        rng_authority=args.rng_authority,
        mask_plan_generator=args.mask_plan_generator,
        burden_estimator_source=args.burden_estimator_source,
        full104_manifest=args.full104_manifest,
        canonical_registry=args.canonical_registry,
        repo_root=args.repo_root,
    )
    print(json.dumps({
        "state": "READY_FOR_AUDIT_B_EXECUTION",
        "contract_sha256": contract.canonical_digest(),
        "precision_scope_id": contract.precision_scope_id,
        "runtime_bindings": observed,
        "burden_computed": False,
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
