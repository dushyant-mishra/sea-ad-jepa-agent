#!/usr/bin/env python3
"""Build the explicit FULL104 confirmation parameter authority from discovery provenance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v1 import (
    PRIMARY_ATTACKER_ID,
    PRIMARY_SCORE_ID,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v2 import (
    BURDEN_SEPARATION_POLICY_ID,
    CONFIRMATION_ROLE_ID,
    ORIGIN_POLICY_ID,
    MaskingQualificationParametersAuthorityV2,
)


REPORT = "analysis/v5_masking_successor_spike_20260917/reports/RIDGE8_EXPANDED_VALIDATION_20260917.md"
UNIVERSE_SCRIPT = "analysis/v5_masking_successor_spike_20260917/scripts/ridge8_universe_fold.py"
OUTSIDE_SCRIPT = "analysis/v5_masking_successor_spike_20260917/scripts/outer5200_32_unified_ridge_fold.py"
PROVENANCE = "analysis/v5_masking_successor_spike_20260917/provenance/RIDGE8_EXPANDED_VALIDATION_PROVENANCE_20260917.md"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    report = args.repo / REPORT
    universe = args.repo / UNIVERSE_SCRIPT
    outside = args.repo / OUTSIDE_SCRIPT
    provenance = args.repo / PROVENANCE
    for path in (report, universe, outside, provenance):
        if not path.is_file():
            raise SystemExit(f"missing discovery provenance file: {path}")

    report_text = report.read_text(encoding="utf-8")
    if "EXPLORATORY SUCCESSOR EVIDENCE ONLY. NO MASKING AUTHORITY. TRAINING OFF." not in report_text:
        raise SystemExit("expanded validation report no longer carries its exploratory-only boundary")
    required_report_phrases = (
        "6,000-address universe",
        "Outside-original-800 target challenge",
        "Nothing here freezes cap 8, 15% mask burden",
    )
    for phrase in required_report_phrases:
        if phrase not in report_text:
            raise SystemExit(f"discovery report is missing required provenance phrase: {phrase}")

    universe_text = universe.read_text(encoding="utf-8")
    outside_text = outside.read_text(encoding="utf-8")
    required_code_fragments = {
        "universe script": (
            "[:64]",
            "order[:8]",
            "alpha=.01",
            "maxf=32",
        ),
        "outside-800 script": (
            "cand_m=20",
            "floor=.05",
            "reduction=.50",
            "cap=8",
        ),
    }
    for label, fragments in required_code_fragments.items():
        text = universe_text if label == "universe script" else outside_text
        for fragment in fragments:
            if fragment not in text:
                raise SystemExit(f"{label} no longer proves discovery parameter fragment {fragment!r}")

    authority = MaskingQualificationParametersAuthorityV2(
        authority_id="JEPA_V5_FULL104_CONFIRMATION_PARAMETERS_AUTHORITY_V2",
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
        discovery_expanded_validation_report_sha256=sha256_file(report),
        discovery_universe_scale_script_sha256=sha256_file(universe),
        discovery_outside800_unified_script_sha256=sha256_file(outside),
        discovery_provenance_note_sha256=sha256_file(provenance),
        parameter_origin_policy_id=ORIGIN_POLICY_ID,
        confirmation_role_id=CONFIRMATION_ROLE_ID,
        burden_separation_policy_id=BURDEN_SEPARATION_POLICY_ID,
        terminal_full104_masking_outcomes_inspected=False,
        training_authorized=False,
    )
    authority.validate()
    payload = {
        "schema": "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V2",
        **authority.__dict__,
        "parameter_authority_sha256": authority.canonical_digest(),
        "rationale": (
            "These values are deliberately re-authorized as the exact pre-FULL104 "
            "discovery-defined candidate to confirm independently. They are not hidden "
            "defaults and were not derived from terminal FULL104 outcomes. The masking "
            "burden is excluded because the FULL104 census changed the scale-sensitive "
            "burden question."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["parameter_authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
