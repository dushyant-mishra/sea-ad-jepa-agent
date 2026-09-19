#!/usr/bin/env python3
"""Build FULL104 census authority V2 from actual execution receipts."""
from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_pass1_physical_binding_v1 import (
    SCHEMA_ID as PASS1_BINDING_SCHEMA_ID,
    Full104Pass1PhysicalBindingReceiptV1,
    verify_pass1_against_physical_full104,
)
from sea_ad_jepa.v5.full104_census_receipt_v2 import (
    FULL104_CORE_NONZERO_COUNT,
    FULL104_CORE_SLOT_COUNT,
    FULL104_CORE_ZERO_COUNT,
    FULL104_CORE_ZERO_FREQUENCY,
    canonical_sha,
    sha256_file,
    validate_full104_crosscheck,
)

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256 = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_receipt(payload: dict, schema: str, path: Path) -> None:
    if payload.get("schema") != schema:
        raise SystemExit(f"{path}: schema mismatch")
    declared = payload.get("receipt_sha256")
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    if declared != canonical_sha(semantic):
        raise SystemExit(f"{path}: receipt digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit(f"{path}: terminal masking outcomes must remain unopened")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--observation-state", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--pass1", type=Path, required=True)
    p.add_argument("--pass1-physical-binding", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--split", type=Path, required=True)
    p.add_argument("--target-eligibility", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    block_manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    manifest_sha = sha256_file(block_manifest)
    observation_sha = sha256_file(args.observation_state)
    if manifest_sha != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 block manifest mismatch")
    if observation_sha != EXPECTED_OBSERVATION_STATE_SHA256:
        raise SystemExit("observation-state authority mismatch")

    pass1_sha = sha256_file(args.pass1)

    binding_payload = load(args.pass1_physical_binding)
    if binding_payload.get("schema") != PASS1_BINDING_SCHEMA_ID:
        raise SystemExit("pass1 physical-binding receipt schema mismatch")
    binding_names = {item.name for item in fields(Full104Pass1PhysicalBindingReceiptV1)}
    missing_binding = binding_names - set(binding_payload)
    if missing_binding:
        raise SystemExit(
            f"pass1 physical-binding receipt missing fields: {sorted(missing_binding)[:5]}"
        )
    binding_values = {name: binding_payload[name] for name in binding_names}
    binding_values["source_names"] = tuple(binding_values["source_names"])
    persisted_binding = Full104Pass1PhysicalBindingReceiptV1(**binding_values)
    persisted_binding.validate()
    binding_root = persisted_binding.canonical_digest()
    if binding_payload.get("receipt_sha256") != binding_root:
        raise SystemExit("pass1 physical-binding receipt digest mismatch")
    if persisted_binding.pass1_npz_sha256 != pass1_sha:
        raise SystemExit("pass1 physical-binding receipt binds different pass1 bytes")

    rederived_binding = verify_pass1_against_physical_full104(
        pass1_path=args.pass1,
        level4_root=args.level4_root,
        registry_path=args.registry,
        observation_state_path=args.observation_state,
    )
    if rederived_binding.canonical_digest() != binding_root:
        raise SystemExit(
            "pass1 physical binding does not rederive from current FULL104 physical bytes"
        )

    summary = load(args.summary)
    split = load(args.split)
    eligibility = load(args.target_eligibility)
    require_receipt(summary, "V5_FULL104_READONLY_CENSUS_SUMMARY_RECEIPT_V2", args.summary)
    require_receipt(split, "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1", args.split)
    require_receipt(eligibility, "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1", args.target_eligibility)
    for label, receipt in (("summary", summary), ("split", split), ("eligibility", eligibility)):
        if receipt.get("pass1_npz_sha256") != pass1_sha:
            raise SystemExit(f"{label} receipt is not bound to supplied pass1 NPZ")
        if receipt.get("pass1_physical_binding_sha256") != binding_root:
            raise SystemExit(
                f"{label} receipt is not bound to the rederived physical FULL104 pass1 proof"
            )

    validate_full104_crosscheck(summary["corrected_core_zero_crosscheck"])
    if summary["corrected_core_zero_crosscheck"]["total_core_slots"] != FULL104_CORE_SLOT_COUNT:
        raise SystemExit("core slot count mismatch")
    if summary["corrected_core_zero_crosscheck"]["core_nonzero_sum_per_cell"] != FULL104_CORE_NONZERO_COUNT:
        raise SystemExit("core nonzero count mismatch")
    if summary["corrected_core_zero_crosscheck"]["core_measured_zero_count"] != FULL104_CORE_ZERO_COUNT:
        raise SystemExit("corrected core zero count mismatch")
    if abs(summary["corrected_core_zero_crosscheck"]["core_measured_zero_frequency"] - FULL104_CORE_ZERO_FREQUENCY) > 1e-15:
        raise SystemExit("corrected core zero frequency mismatch")

    if split.get("n_folds") != 4 or split.get("fold_sizes") != [28, 26, 25, 25]:
        raise SystemExit("outer split receipt mismatch")
    if eligibility.get("eligible_target_count") != 17053:
        raise SystemExit("eligible target count mismatch")
    if eligibility.get("split_receipt_sha256") != split.get("receipt_sha256"):
        raise SystemExit("target eligibility is not bound to split receipt")

    support = load(args.support_authority)
    if canonical_sha(support) != EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("support authority is not the exact current semantic authority")
    required_support = {
        "schema": "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1",
        "full104_substrate_sha256": EXPECTED_BLOCK_MANIFEST_SHA256,
        "missing_value_semantics_id": "UNMEASURED_IS_MISSING_NOT_ZERO",
        "training_authorized": False,
    }
    for key, expected in required_support.items():
        if support.get(key) != expected:
            raise SystemExit(f"support authority mismatch for {key}")
    support_sha = sha256_file(args.support_authority)

    payload = {
        "schema": "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2",
        "date": "2026-09-18",
        "status": "FULL104_READONLY_CENSUS_EXECUTION_RECEIPTS_BOUND__TERMINAL_MASKING_OUTCOMES_UNOPENED",
        "training_authorized": False,
        "terminal_masking_outcomes_inspected": False,
        "substrate": {
            "full104_block_manifest_sha256": manifest_sha,
            "operator_address_observation_state_sha256": observation_sha,
            "pass1_npz_sha256": pass1_sha,
            "pass1_physical_binding_sha256": binding_root,
            "canonical_registry_sha256": rederived_binding.canonical_registry_sha256,
        },
        "support_estimability_authority": {
            "path": str(args.support_authority),
            "sha256": support_sha,
        },
        "execution_receipts": {
            "pass1_physical_binding_path": str(args.pass1_physical_binding),
            "pass1_physical_binding_file_sha256": sha256_file(args.pass1_physical_binding),
            "pass1_physical_binding_receipt_sha256": binding_root,
            "summary_path": str(args.summary),
            "summary_file_sha256": sha256_file(args.summary),
            "summary_receipt_sha256": summary["receipt_sha256"],
            "split_path": str(args.split),
            "split_file_sha256": sha256_file(args.split),
            "split_receipt_sha256": split["receipt_sha256"],
            "target_eligibility_path": str(args.target_eligibility),
            "target_eligibility_file_sha256": sha256_file(args.target_eligibility),
            "target_eligibility_receipt_sha256": eligibility["receipt_sha256"],
        },
        "corrected_core_zero_accounting": summary["corrected_core_zero_crosscheck"],
        "target_support": summary["target_support"],
        "donor_precision_context": summary["donor_precision_context"],
        "burden_stress_ladder": summary["burden_stress_ladder"],
        "withdrawn_v1_builder_semantics": (
            "V1 packaged hard-coded census constants with script and substrate hashes "
            "but did not bind the actual pass1/result receipts. V2 requires the pass1 "
            "NPZ and receipt files, re-derives pass1 semantics from the authenticated "
            "8,915-block FULL104 substrate, and refuses mismatched roots."
        ),
    }
    payload["census_authority_sha256"] = canonical_sha(payload)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["census_authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
