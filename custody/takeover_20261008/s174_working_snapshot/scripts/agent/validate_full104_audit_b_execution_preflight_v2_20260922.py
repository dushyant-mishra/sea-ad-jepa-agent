#!/usr/bin/env python3
"""Validate executable FULL104 Audit-B B4 readiness without computing burden."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.audit_b_execution_preflight_v2 import (
    require_contract_ready,
    verify_runtime_bindings,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--scientific-resolution", type=Path, required=True)
    p.add_argument("--precision-rule-authority", type=Path, required=True)
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
    contract.require_sample_level_ready("N1")
    observed = verify_runtime_bindings(
        contract,
        scientific_resolution=args.scientific_resolution,
        precision_rule_authority=args.precision_rule_authority,
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
        "state": "READY_FOR_AUDIT_B_N1_EXECUTION",
        "contract_sha256": contract.canonical_digest(),
        "precision_scope_id": contract.precision_scope_id,
        "primary_policy_id": contract.primary_policy_id,
        "primary_rung": [
            contract.primary_rung_numerator,
            contract.primary_rung_denominator,
        ],
        "precision_estimator_id": contract.precision_estimator_id,
        "authorized_sample_level": "N1",
        "direct_n2_n3_execution_authorized":
            contract.direct_n2_n3_execution_authorized,
        "runtime_bindings": observed,
        "burden_computed": False,
        "masks_executed": False,
        "terminal_masking_outcomes_inspected": False,
        "terminal_masking_authorized": False,
        "training_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
