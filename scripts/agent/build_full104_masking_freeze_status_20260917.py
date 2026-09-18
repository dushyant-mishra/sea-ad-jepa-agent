#!/usr/bin/env python3
"""Report the prospective FULL104 masking freeze status.

Computes every root that CAN be bound right now, and names precisely what
prevents the complete run contract from being frozen. Emits a hash-bound status
artifact. Opens no terminal masking outcome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict

import sys

SCHEMA = "V5_FULL104_MASKING_PROSPECTIVE_FREEZE_STATUS_V1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(payload: Dict[str, Any]) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo / "src"))
    from sea_ad_jepa.v5.masking_burden_ladder_authority_v1 import (
        MaskingBurdenLadderAuthorityV1,
    )
    from sea_ad_jepa.v5.masking_qualification_run_contract_v2 import (
        CANONICAL_REFERENCE_RELPATH,
        FULL104_STREAMING_EXECUTION_RELPATH,
    )
    from sea_ad_jepa.v5.target_evidence_budget_authority_v2 import (
        TargetEvidenceBudgetAuthorityV2,
    )

    census = json.loads(args.census.read_text(encoding="utf-8"))
    census_root = census["census_authority_sha256"]
    manifest_sha = census["substrate"]["full104_block_manifest_sha256"]
    obs_sha = census["substrate"]["operator_address_observation_state_sha256"]
    checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    checkpoint_root = checkpoint["checkpoint_semantic_sha256"]

    support_root = hashlib.sha256(
        b"PLACEHOLDER_SUPPORT_ESTIMABILITY_AUTHORITY_NOT_YET_INSTANTIATED"
    ).hexdigest()

    template = TargetEvidenceBudgetAuthorityV2(
        authority_id="FULL104_MASKING_EVIDENCE_BUDGET_TEMPLATE_20260917",
        support_estimability_authority_sha256=support_root,
        support_semantics_id="STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
        census_authority_sha256=census_root,
        full104_block_manifest_sha256=manifest_sha,
        observation_state_sha256=obs_sha,
        terminal_universe_id="FULL_COMMON_CORE_17186_V1",
        budget_semantics_id="MASK_FRACTION_OF_STRICT_MEASURED_NON_TARGET_ADDRESSES_V1",
        eligibility_rule_id="VALUE_INDEPENDENT_ELIGIBILITY__MEASURED_ZERO_IS_MEASURED_EVIDENCE_V1",
        rounding_policy_id="FLOOR_EXACT_RATIONAL_V1",
        mask_fraction_numerator=1,
        mask_fraction_denominator=20,
        min_retained_non_target_address_count=0,
        infeasible_policy_id="FAIL_CLOSED_IF_BUDGET_INFEASIBLE_V1",
    )
    ladder = MaskingBurdenLadderAuthorityV1(
        authority_id="FULL104_MASKING_BURDEN_LADDER_20260917",
        ladder_id="FULL104_CENSUS_BURDEN_LADDER_20260917_V1",
        census_authority_sha256=census_root,
        selection_rule_id="LOWEST_QUALIFYING_BURDEN_V1",
        escalation_rule_id="ASCENDING_BURDEN_STAGED_ESCALATION_V1",
        no_qualifier_policy_id="FAIL_CLOSED_NO_MASKING_AUTHORITY_V1",
        terminal_universe_size=17186,
    )
    eligible = 17186 - 1
    rung_budgets = ladder.all_rung_budgets(template)

    payload: Dict[str, Any] = {
        "schema": SCHEMA,
        "date": "2026-09-17",
        "status": (
            "FULL104_MASKING_PROSPECTIVE_PACKAGE_PARTIALLY_FROZEN__"
            "BLOCKED_ON_NUMERIC_PARAMETERS_AUTHORITY"
        ),
        "training_authorized": False,
        "protected_outcomes_authorized": False,
        "terminal_masking_outcomes_inspected": False,
        "frozen_roots": {
            "full104_block_manifest_sha256": manifest_sha,
            "observation_state_sha256": obs_sha,
            "census_authority_sha256": census_root,
            "machine_worktree_checkpoint_sha256": checkpoint_root,
            "target_evidence_budget_template_sha256": template.template_digest(),
            "burden_ladder_authority_sha256": ladder.canonical_digest(),
            "canonical_reference_source_sha256": sha256_file(
                args.repo / CANONICAL_REFERENCE_RELPATH
            ),
            "full104_streaming_execution_source_sha256": sha256_file(
                args.repo / FULL104_STREAMING_EXECUTION_RELPATH
            ),
        },
        "execution_source_roles": {
            "canonical_reference_relpath": CANONICAL_REFERENCE_RELPATH,
            "full104_streaming_execution_relpath": FULL104_STREAMING_EXECUTION_RELPATH,
            "execution_source_role_id": "FULL104_STREAMING_EXECUTION_V1",
            "note": (
                "The canonical reference defines correct behaviour and is what parity "
                "tests compare against; it does not execute FULL104. Binding its digest "
                "in the execution role is rejected."
            ),
        },
        "support_semantics": {
            "support_semantics_id": "STRICT_MEASURED_SCALAR_ONLY__COLLISION_UNRESOLVED_EXCLUDED_V1",
            "terminal_universe_id": "FULL_COMMON_CORE_17186_V1",
            "terminal_universe_size": 17186,
            "loose_only_excluded": 219,
            "eligible_masking_unit": "STRICT_MEASURED_SCALAR_NON_TARGET_MOLECULAR_ADDRESS",
            "measured_zero_is_measured_evidence": True,
            "value_independent_eligibility": True,
        },
        "burden_ladder": {
            "ladder_id": "FULL104_CENSUS_BURDEN_LADDER_20260917_V1",
            "selection_rule_id": "LOWEST_QUALIFYING_BURDEN_V1",
            "escalation_rule_id": "ASCENDING_BURDEN_STAGED_ESCALATION_V1",
            "no_qualifier_policy_id": "FAIL_CLOSED_NO_MASKING_AUTHORITY_V1",
            "rungs": [
                {
                    "fraction": f"{rung.numerator}/{rung.denominator}",
                    "co_mask_count": ladder.co_mask_count_for(rung, eligible),
                    "rung_budget_sha256": budget.canonical_digest(),
                }
                for rung, budget in sorted(rung_budgets.items())
            ],
            "note": (
                "Every rung descends from one burden-free template, so the freeze does "
                "not presuppose which burden will be selected."
            ),
        },
        "blockers": [
            {
                "id": "NUMERIC_PARAMETERS_AUTHORITY_NOT_FREEZABLE",
                "severity": "BLOCKS_COMPLETE_RUN_CONTRACT_FREEZE",
                "detail": (
                    "MaskingQualificationRunContractV2 requires "
                    "qualification_parameters_authority_sha256. "
                    "MaskingQualificationParametersAuthorityV1 requires "
                    "targeted_partner_cap, ridge_candidate_pool_count, "
                    "ridge_score_feature_count, ridge_alpha and the PREFIX3 inner-fold, "
                    "candidate, floor and reduction parameters. No frozen production "
                    "instance exists anywhere in src/, scripts/, docs/ or analysis/; the "
                    "only instantiations are test fixtures using cap=2 and alpha=1/100."
                ),
                "why_not_simply_inherited": (
                    "RIDGE8 cap 8 and ridge alpha 0.01 are named explicitly in the "
                    "anti-spillover list, and are scale-sensitive: they were chosen for "
                    "an 800-address discovery universe and the terminal universe is "
                    "17,186 addresses. Adopting them would be unproven inheritance, "
                    "which the standing rule forbids."
                ),
                "resolution_paths": [
                    "freeze a prospective derivation rule that computes cap, pool count, "
                    "feature count and ridge alpha from FULL104 geometry",
                    "record an explicit current authority documenting why specific values "
                    "are chosen prospectively, independent of discovery-era results",
                ],
            },
            {
                "id": "DEPENDENT_AUTHORITIES_NOT_YET_INSTANTIATED",
                "severity": "BLOCKS_COMPLETE_RUN_CONTRACT_FREEZE",
                "detail": (
                    "support estimability, outer split, target panel, precision and "
                    "RNG replay authority instances are not yet frozen for FULL104. The "
                    "classes exist; no production instance is bound. The support root in "
                    "this artifact is a placeholder and is NOT a frozen authority."
                ),
            },
            {
                "id": "BRANCH_DIVERGENCE_UNRESOLVED",
                "severity": "GOVERNANCE",
                "detail": (
                    "handoff/v5-masking-successor-ridge8-20260917 and "
                    "impl/v5-remaining-rna-target-semantics-20260917 both modify "
                    "current_authority_closure_v1.py and conflict textually; the "
                    "remaining-rna variant is a strict superset. This branch descends "
                    "from remaining-rna. The divergence is reported, not resolved here."
                ),
            },
        ],
        "not_claimed": [
            "NO_SELECTED_MASKING_POLICY",
            "NO_FULL104_MASKING_PASS",
            "NO_TRAINING_AUTHORIZATION",
            "NO_TERMINAL_OUTCOME_INSPECTED",
        ],
    }
    payload["freeze_status_sha256"] = canonical_sha(payload)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(payload["freeze_status_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
