#!/usr/bin/env python3
"""Build current FULL104 masking qualification design V2 without burden or discovery-universe spillover."""
from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import MaskingBurdenLadderAuthorityV2
from sea_ad_jepa.v5.masking_qualification_design_authority_v1 import (
    APPROVED_EXPRESSION_ATTACKER_ROLE_IDS,
    APPROVED_NONLINEAR_RETUNING_POLICY_IDS,
    APPROVED_PAIRED_ESTIMAND_IDS,
    APPROVED_POLICY_ARMS,
    APPROVED_POOLED_MEAN_GUARDRAIL_IDS,
    APPROVED_PRIMARY_ATTACKER_APPLICATION_POLICY_IDS,
    APPROVED_PRIMARY_ATTACKER_IDS,
    APPROVED_PRIMARY_SCORE_IDS,
    APPROVED_SCIENTIFIC_SEMANTICS_IDS,
    APPROVED_SECONDARY_ATTACKER_IDS,
    REQUIRED_CONTROLS,
)
from sea_ad_jepa.v5.masking_qualification_design_authority_v2 import MaskingQualificationDesignAuthorityV2
from sea_ad_jepa.v5.masking_rng_replay_authority_v2 import MaskingRngReplayAuthorityV2
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4
from sea_ad_jepa.v5.target_evidence_budget_template_authority_v1 import TargetEvidenceBudgetTemplateAuthorityV1
from sea_ad_jepa.v5.target_panel_authority_v3 import TargetPanelAuthorityV3

EXPECTED_FULL104_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_REGISTRY_AUTHORITY_DIGEST = "28b20a457c44ac864c375492c8875e865ed6fe6d2000338d5fd46d9557a25676"
RUNNER_RELPATH = "src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py"
EXPECTED_REPRESENTATION_AUTHORITY_CANONICAL_JSON_SHA256 = "92756711fde939e27abc982d6ab1a0bc0dab53fae209c0f5a3fba4fde86ef4b1"
EXPECTED_TEACHER_TARGET_AUTHORITY_CANONICAL_JSON_SHA256 = "a5c4702eae54ffeb9d3a92957ce3176e29db25c805843a48cf3a6121037d89d2"
EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256 = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"
EXPECTED_REGISTRY_AUTHORITY_CANONICAL_JSON_SHA256 = "3321f6a0acd5ae89faa4912dde2d2ebc7c9d52d2bccf82ef63e415ace51158c9"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def typed(payload: dict, cls, digest_field: str):
    names = {f.name for f in fields(cls)}
    missing = names - set(payload)
    if missing:
        raise SystemExit(f"{cls.__name__} missing fields: {sorted(missing)[:5]}")
    obj = cls(**{name: payload[name] for name in names})
    obj.validate()
    if payload.get(digest_field) != obj.canonical_digest():
        raise SystemExit(f"{cls.__name__} digest mismatch")
    return obj


def template_typed(payload: dict) -> TargetEvidenceBudgetTemplateAuthorityV1:
    if payload.get("schema") != "V5_TARGET_EVIDENCE_BUDGET_TEMPLATE_AUTHORITY_V1":
        raise SystemExit("target evidence-budget template authority V1 is required")
    names = {f.name for f in fields(TargetEvidenceBudgetTemplateAuthorityV1)}
    obj = TargetEvidenceBudgetTemplateAuthorityV1(**{name: payload[name] for name in names})
    obj.validate()
    if payload.get("template_sha256") != obj.template_digest():
        raise SystemExit("target evidence-budget template digest mismatch")
    if payload.get("fraction_frozen_here") is not False:
        raise SystemExit("target evidence-budget template must not freeze a burden fraction")
    return obj


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--representation-authority", type=Path, required=True)
    p.add_argument("--teacher-target-semantics-authority", type=Path, required=True)
    p.add_argument("--canonical-registry-authority", type=Path, required=True)
    p.add_argument("--support-authority", type=Path, required=True)
    p.add_argument("--target-evidence-budget-template", type=Path, required=True)
    p.add_argument("--burden-ladder-authority", type=Path, required=True)
    p.add_argument("--precision-authority", type=Path, required=True)
    p.add_argument("--outer-split-authority", type=Path, required=True)
    p.add_argument("--target-panel-authority", type=Path, required=True)
    p.add_argument("--rng-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    representation = load(args.representation_authority)
    if canonical_sha(representation) != EXPECTED_REPRESENTATION_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("representation authority is not the exact current semantic authority")
    if representation.get("schema") != "V5_PRIMARY_REPRESENTATION_AUTHORITY_V1":
        raise SystemExit("current primary representation authority V1 is required")
    if representation.get("substrate_authority_sha256") != EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("representation authority binds a different FULL104 substrate")
    if representation.get("training_authorized") is not False:
        raise SystemExit("representation authority unexpectedly authorizes training")
    representation_sha = sha256_file(args.representation_authority)

    teacher = load(args.teacher_target_semantics_authority)
    if canonical_sha(teacher) != EXPECTED_TEACHER_TARGET_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("teacher-target authority is not the exact current semantic authority")
    if teacher.get("schema") != "TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2":
        raise SystemExit("current teacher-target scientific authority V2 is required")
    if teacher.get("training_authorized") is not False or teacher.get("execution_authorized") is not False:
        raise SystemExit("teacher-target authority unexpectedly authorizes execution/training")
    teacher_sha = sha256_file(args.teacher_target_semantics_authority)

    registry = load(args.canonical_registry_authority)
    if canonical_sha(registry) != EXPECTED_REGISTRY_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("canonical registry authority is not the exact current semantic authority")
    if registry.get("schema") != "V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1":
        raise SystemExit("canonical registry authority schema mismatch")
    registry_digest = str(registry.get("canonical_authority_digest", ""))
    if registry_digest != EXPECTED_REGISTRY_AUTHORITY_DIGEST:
        raise SystemExit("canonical registry authority digest mismatch")
    if registry.get("FULL104_SUBSTRATE", {}).get("sha256") != EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("canonical registry authority binds a different FULL104 substrate")

    support = load(args.support_authority)
    if canonical_sha(support) != EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("support authority is not the exact current semantic authority")
    support_sha = sha256_file(args.support_authority)
    if support.get("schema") != "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    if support.get("full104_substrate_sha256") != EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("support authority binds a different FULL104 substrate")
    if support.get("training_authorized") is not False:
        raise SystemExit("support authority unexpectedly authorizes training")

    template = template_typed(load(args.target_evidence_budget_template))
    if template.full104_block_manifest_sha256 != EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("evidence-budget template binds a different FULL104 substrate")
    if template.support_estimability_authority_sha256 != support_sha:
        raise SystemExit("evidence-budget template binds a different support authority")

    burden_payload = load(args.burden_ladder_authority)
    if burden_payload.get("schema") != "V5_MASKING_BURDEN_LADDER_AUTHORITY_V2":
        raise SystemExit("burden ladder authority V2 is required")
    burden = typed(burden_payload, MaskingBurdenLadderAuthorityV2, "authority_sha256")
    if burden.census_authority_sha256 != template.census_authority_sha256:
        raise SystemExit("burden ladder and evidence-budget template bind different census authorities")

    outer_payload = load(args.outer_split_authority)
    if outer_payload.get("schema") != "V5_OUTER_DONOR_SPLIT_AUTHORITY_V1":
        raise SystemExit("outer split authority V1 is required")
    outer = typed(outer_payload, OuterDonorSplitAuthorityV1, "authority_sha256")

    panel_payload = load(args.target_panel_authority)
    if panel_payload.get("schema") != "V5_TARGET_PANEL_AUTHORITY_V3":
        raise SystemExit("target panel authority V3 is required")
    panel = typed(panel_payload, TargetPanelAuthorityV3, "authority_sha256")

    precision_payload = load(args.precision_authority)
    if precision_payload.get("schema") != "V5_QUALIFICATION_PRECISION_AUTHORITY_V4":
        raise SystemExit("precision authority V4 is required")
    precision = typed(precision_payload, QualificationPrecisionAuthorityV4, "authority_sha256")

    rng_payload = load(args.rng_authority)
    if rng_payload.get("schema") != "V5_MASKING_RNG_REPLAY_AUTHORITY_V2":
        raise SystemExit("RNG replay authority V2 is required")
    rng = typed(rng_payload, MaskingRngReplayAuthorityV2, "authority_sha256")

    runner_path = args.repo / RUNNER_RELPATH
    if not runner_path.is_file():
        raise SystemExit("current canonical qualification runner source is missing")

    authority = MaskingQualificationDesignAuthorityV2(
        authority_id="JEPA_V5_FULL104_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V2",
        full104_substrate_sha256=EXPECTED_FULL104_MANIFEST_SHA256,
        representation_authority_sha256=representation_sha,
        support_estimability_authority_sha256=support_sha,
        canonical_registry_authority_sha256=registry_digest,
        teacher_target_semantics_authority_sha256=teacher_sha,
        target_evidence_budget_template_sha256=template.template_digest(),
        burden_ladder_authority_sha256=burden.canonical_digest(),
        precision_authority_sha256=precision.canonical_digest(),
        outer_split_authority_sha256=outer.canonical_digest(),
        target_panel_authority_sha256=panel.canonical_digest(),
        rng_replay_authority_sha256=rng.canonical_digest(),
        qualification_runner_source_sha256=sha256_file(runner_path),
        scientific_semantics_id=APPROVED_SCIENTIFIC_SEMANTICS_IDS[0],
        expression_attacker_role_id=APPROVED_EXPRESSION_ATTACKER_ROLE_IDS[0],
        policy_arms=APPROVED_POLICY_ARMS,
        primary_attacker_id=APPROVED_PRIMARY_ATTACKER_IDS[0],
        primary_attacker_application_policy_id=APPROVED_PRIMARY_ATTACKER_APPLICATION_POLICY_IDS[0],
        secondary_attacker_id=APPROVED_SECONDARY_ATTACKER_IDS[0],
        primary_score_id=APPROVED_PRIMARY_SCORE_IDS[0],
        paired_estimand_id=APPROVED_PAIRED_ESTIMAND_IDS[0],
        controls=REQUIRED_CONTROLS,
        nonlinear_retuning_policy_id=APPROVED_NONLINEAR_RETUNING_POLICY_IDS[0],
        pooled_mean_guardrail_id=APPROVED_POOLED_MEAN_GUARDRAIL_IDS[0],
    )
    authority.bind_live_authorities(
        target_evidence_budget_template=template,
        burden_ladder=burden,
        precision=precision,
        outer_split=outer,
        target_panel=panel,
        rng_replay=rng,
    )
    payload = {
        "schema": "V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V2",
        **authority.__dict__,
        "policy_arms": list(authority.policy_arms),
        "controls": list(authority.controls),
        "authority_sha256": authority.canonical_digest(),
        "concrete_burden_frozen_in_design": False,
        "protected_outcomes_authorized": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
