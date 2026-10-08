#!/usr/bin/env python3
"""Build FULL104-bound masking confirmation parameters from historical provenance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import (
    PRIMARY_ATTACKER_ID,
    PRIMARY_SCORE_ID,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import (
    BURDEN_SEPARATION_POLICY_ID,
    CONFIRMATION_ROLE_ID,
    FULL104_SUBSTRATE_SHA256,
    HISTORICAL_PROVENANCE_ROLE_ID,
    ORIGIN_POLICY_ID,
    SUPPORT_ESTIMABILITY_AUTHORITY_SHA256,
    TERMINAL_UNIVERSE_ID,
    TERMINAL_UNIVERSE_SIZE,
    MaskingQualificationParametersAuthorityV3,
)

REPORT = "analysis/v5_masking_successor_spike_20260917/reports/RIDGE8_EXPANDED_VALIDATION_20260917.md"
UNIVERSE_SCRIPT = "analysis/v5_masking_successor_spike_20260917/scripts/ridge8_universe_fold.py"
OUTSIDE_SCRIPT = "analysis/v5_masking_successor_spike_20260917/scripts/outer5200_32_unified_ridge_fold.py"
PROVENANCE = "analysis/v5_masking_successor_spike_20260917/provenance/RIDGE8_EXPANDED_VALIDATION_PROVENANCE_20260917.md"

EXPECTED_HISTORICAL_SHA256 = {
    REPORT: "a649a4bd220851423679a3ee47fdc096691056eea0cfb09984de64caceb3ad88",
    UNIVERSE_SCRIPT: "eb32280d90cf2bdc7ab2fed86e1a5af41c4e0293d89d61cc6f2641b9a1fb3511",
    OUTSIDE_SCRIPT: "7a33785c774485363ea0f57d90acdee2a1d64c81772da1a35f1bef24c5b3a5dc",
    PROVENANCE: "6b972a20e49876b5f77b35ab836b5ce9d416cc1e671aa80dcd5d8461e5a6f038",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if not manifest.is_file():
        raise SystemExit("current FULL104 Level-4 block manifest is missing")
    manifest_sha = sha256_file(manifest)
    if manifest_sha != FULL104_SUBSTRATE_SHA256:
        raise SystemExit(
            "current FULL104 block-manifest root mismatch: "
            f"expected {FULL104_SUBSTRATE_SHA256}, observed {manifest_sha}"
        )

    support = load_json(args.support_authority)
    support_semantic = canonical_sha(support)
    if support_semantic != SUPPORT_ESTIMABILITY_AUTHORITY_SHA256:
        raise SystemExit("support authority is not the exact current FULL104 semantic authority")
    if support.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    if support.get("full104_substrate_sha256") != FULL104_SUBSTRATE_SHA256:
        raise SystemExit("support authority binds a different FULL104 substrate")
    if support.get("training_authorized") is not False:
        raise SystemExit("support authority unexpectedly authorizes training")

    historical_paths = {
        role: args.repo / role
        for role in EXPECTED_HISTORICAL_SHA256
    }
    for role, path in historical_paths.items():
        if not path.is_file():
            raise SystemExit(f"missing historical parameter-provenance file: {path}")
        observed = sha256_file(path)
        expected = EXPECTED_HISTORICAL_SHA256[role]
        if observed != expected:
            raise SystemExit(
                f"historical discovery provenance byte drift for {role}: "
                f"expected {expected}, observed {observed}"
            )

    report_text = historical_paths[REPORT].read_text(encoding="utf-8")
    if "EXPLORATORY SUCCESSOR EVIDENCE ONLY. NO MASKING AUTHORITY. TRAINING OFF." not in report_text:
        raise SystemExit("historical report lost its exploratory-only boundary")
    for phrase in (
        "6,000-address universe",
        "Outside-original-800 target challenge",
        "Nothing here freezes cap 8, 15% mask burden",
    ):
        if phrase not in report_text:
            raise SystemExit(
                f"historical report is missing required provenance phrase: {phrase}"
            )

    universe_text = historical_paths[UNIVERSE_SCRIPT].read_text(encoding="utf-8")
    outside_text = historical_paths[OUTSIDE_SCRIPT].read_text(encoding="utf-8")
    for fragment in ("[:64]", "order[:8]", "alpha=.01", "maxf=32"):
        if fragment not in universe_text:
            raise SystemExit(
                f"historical universe script no longer proves parameter fragment {fragment!r}"
            )
    for fragment in ("cand_m=20", "floor=.05", "reduction=.50", "cap=8"):
        if fragment not in outside_text:
            raise SystemExit(
                f"historical outside-800 script no longer proves parameter fragment {fragment!r}"
            )

    authority = MaskingQualificationParametersAuthorityV3(
        authority_id="JEPA_V5_FULL104_BOUND_CONFIRMATION_PARAMETERS_AUTHORITY_V3",
        full104_substrate_sha256=manifest_sha,
        support_estimability_authority_sha256=support_semantic,
        terminal_universe_id=TERMINAL_UNIVERSE_ID,
        terminal_universe_size=TERMINAL_UNIVERSE_SIZE,
        primary_attacker_id=PRIMARY_ATTACKER_ID,
        primary_score_id=PRIMARY_SCORE_ID,
        targeted_partner_cap=8,
        ridge_candidate_pool_count=64,
        ridge_score_feature_count=32,
        ridge_alpha_numerator=1,
        ridge_alpha_denominator=100,
        prefix_inner_fold_count=3,
        prefix_candidate_count=20,
        prefix_floor_numerator=1,
        prefix_floor_denominator=20,
        prefix_reduction_numerator=1,
        prefix_reduction_denominator=2,
        discovery_expanded_validation_report_sha256=sha256_file(historical_paths[REPORT]),
        discovery_universe_scale_script_sha256=sha256_file(historical_paths[UNIVERSE_SCRIPT]),
        discovery_outside800_unified_script_sha256=sha256_file(historical_paths[OUTSIDE_SCRIPT]),
        discovery_provenance_note_sha256=sha256_file(historical_paths[PROVENANCE]),
        parameter_origin_policy_id=ORIGIN_POLICY_ID,
        confirmation_role_id=CONFIRMATION_ROLE_ID,
        burden_separation_policy_id=BURDEN_SEPARATION_POLICY_ID,
        historical_provenance_role_id=HISTORICAL_PROVENANCE_ROLE_ID,
        terminal_full104_masking_outcomes_inspected=False,
        protected_outcomes_authorized=False,
        training_authorized=False,
    )
    authority.validate()

    payload = {
        "schema": "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3",
        **authority.__dict__,
        "parameter_authority_sha256": authority.canonical_digest(),
        "historical_evidence_role": (
            "SUPPORTING PARAMETER-ORIGIN PROVENANCE ONLY. The historical evidence "
            "does not supply current FULL104 data, targets, folds, burden, seed, "
            "row cap, policy selection, PASS state, runtime input, geometry, or training authority."
        ),
        "capacity_scope_note": (
            "This authority governs the current 32-feature confirmation attacker only. "
            "It does not close G3 or establish production-JEPA capacity matching."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(payload["parameter_authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
