#!/usr/bin/env python3
"""Build the burden-free FULL104 target-evidence budget template from current roots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.target_evidence_budget_template_authority_v1 import (
    MIN_RETAINED_POLICY_ID,
    TargetEvidenceBudgetTemplateAuthorityV1,
)

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_OBSERVATION_STATE_SHA256 = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--observation-state", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--census-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    manifest_sha = sha256_file(manifest)
    observation_sha = sha256_file(args.observation_state)
    if manifest_sha != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("FULL104 block manifest mismatch")
    if observation_sha != EXPECTED_OBSERVATION_STATE_SHA256:
        raise SystemExit("observation-state authority mismatch")

    support = load(args.support_authority)
    support_sha = sha256_file(args.support_authority)
    if support.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    if support.get("full104_substrate_sha256") != manifest_sha:
        raise SystemExit("support authority binds a different FULL104 substrate")
    if support.get("missing_value_semantics_id") != "UNMEASURED_IS_MISSING_NOT_ZERO":
        raise SystemExit("support authority missing-value semantics mismatch")
    if support.get("training_authorized") is not False:
        raise SystemExit("support authority unexpectedly authorizes training")

    census = load(args.census_authority)
    if census.get("schema") != "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise SystemExit("census authority V2 is required")
    semantic = dict(census)
    declared = semantic.pop("census_authority_sha256", None)
    if declared != canonical_sha(semantic):
        raise SystemExit("census authority digest mismatch")
    if census.get("training_authorized") is not False:
        raise SystemExit("census authority unexpectedly authorizes training")
    if census.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("census authority records terminal outcome access")
    substrate = census.get("substrate", {})
    if substrate.get("full104_block_manifest_sha256") != manifest_sha:
        raise SystemExit("census authority binds a different FULL104 substrate")
    if substrate.get("operator_address_observation_state_sha256") != observation_sha:
        raise SystemExit("census authority binds a different observation state")
    if census.get("support_estimability_authority", {}).get("sha256") != support_sha:
        raise SystemExit("census authority binds a different support authority")

    template = TargetEvidenceBudgetTemplateAuthorityV1(
        authority_id="JEPA_V5_FULL104_TARGET_EVIDENCE_BUDGET_TEMPLATE_V1",
        support_estimability_authority_sha256=support_sha,
        support_semantics_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        census_authority_sha256=str(declared),
        full104_block_manifest_sha256=manifest_sha,
        observation_state_sha256=observation_sha,
        terminal_universe_id="FULL_COMMON_CORE_17186_V1",
        budget_semantics_id="MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
        eligibility_rule_id="VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        min_retained_non_target_address_count=0,
        min_retained_policy_id=MIN_RETAINED_POLICY_ID,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )
    payload = template.as_payload()
    payload["fraction_frozen_here"] = False
    payload["terminal_masking_outcomes_inspected"] = False
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["template_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
