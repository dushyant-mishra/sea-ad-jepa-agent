#!/usr/bin/env python3
"""Build the prospective FULL104 Audit-B execution contract.

This script never executes Audit B. It verifies and binds the already-frozen
Phase-IV target sample plus the post-audit execution semantics.

Default precision scope is deliberately UNRESOLVED, which produces a valid
content-addressed contract whose execution_authorized flag is false.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from sea_ad_jepa.v5.audit_b_execution_contract_v1 import (
    ALLOWED_PRECISION_SCOPES,
    CANONICAL_REGISTRY_SHA256,
    FULL104_MANIFEST_SHA256,
    HEAVY_ARTIFACT_SHA256,
    MASK_PLAN_GENERATOR_SHA256,
    PHASE_IV_SAMPLE_FREEZE_DIGEST,
    PRECISION_SCOPE_UNRESOLVED,
    AuditBExecutionContractV1,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_freeze_digest(payload: dict) -> str:
    material = json.dumps(
        {
            "schema": payload["schema"],
            "salt": payload["salt"],
            "ladder": payload["ladder"],
            "bound": payload["bound_inputs"],
            "samples": {
                key: value["targets"] for key, value in payload["samples"].items()
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"required JSON artifact is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--sample-freeze",
        type=Path,
        default=Path(
            "analysis/v5_full104_information_channel_redteam_20260920/"
            "evidence/phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json"
        ),
    )
    p.add_argument("--heavy-qualification-receipt", type=Path, required=True)
    p.add_argument("--rng-authority", type=Path, required=True)
    p.add_argument(
        "--burden-estimator-source",
        type=Path,
        default=Path("src/sea_ad_jepa/v5/audit_b_production_burden_v1.py"),
    )
    p.add_argument(
        "--precision-scope",
        choices=ALLOWED_PRECISION_SCOPES,
        default=PRECISION_SCOPE_UNRESOLVED,
    )
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    freeze = load_json(args.sample_freeze)
    if freeze.get("schema") != "V5_AUDIT_B_FROZEN_TARGET_SAMPLE_V1":
        raise SystemExit("Phase-IV sample freeze schema mismatch")
    observed_freeze = canonical_freeze_digest(freeze)
    if freeze.get("freeze_digest") != observed_freeze:
        raise SystemExit("Phase-IV sample freeze has an invalid internal digest")
    if observed_freeze != PHASE_IV_SAMPLE_FREEZE_DIGEST:
        raise SystemExit("builder was given a different Phase-IV sample freeze")
    if freeze.get("ladder") != [256, 1024, 4096]:
        raise SystemExit("Phase-IV sample ladder drifted")
    if freeze.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("sample freeze was produced after terminal outcome inspection")
    if freeze.get("training_authorized") is not False:
        raise SystemExit("sample freeze unexpectedly authorizes training")
    if (
        freeze.get("bound_inputs", {})
        .get("mask_plan_generator", {})
        .get("sha256")
        != MASK_PLAN_GENERATOR_SHA256
    ):
        raise SystemExit("sample freeze binds a different mask-plan generator")

    heavy = load_json(args.heavy_qualification_receipt)
    if heavy.get("schema") not in {
        "V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2",
    }:
        raise SystemExit("exhaustive heavy-statistics qualification V2 is required")
    if heavy.get("verdict") != "HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE":
        raise SystemExit("heavy sufficient statistics are not qualified for reuse")
    if heavy.get("artifact_sha256") != HEAVY_ARTIFACT_SHA256:
        raise SystemExit("heavy qualification binds a different heavy artifact")
    if heavy.get("artifact_sha_matches_bound") is not True:
        raise SystemExit("heavy artifact content-address binding failed")
    if heavy.get("all_104_donor_library_totals_agree") is not True:
        raise SystemExit("all-104-donor source-library qualification did not pass")
    if heavy.get("per_cell_source_vector_agrees") is not True:
        raise SystemExit("per-cell source-vector qualification did not pass")
    if heavy.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("heavy qualification occurred after terminal outcomes")
    if heavy.get("training_authorized") is not False:
        raise SystemExit("heavy qualification unexpectedly authorizes training")

    rng = load_json(args.rng_authority)
    if rng.get("schema") != "V5_MASKING_RNG_REPLAY_AUTHORITY_V3":
        raise SystemExit("pre-panel masking RNG authority V3 is required")
    if rng.get("full104_substrate_sha256") != FULL104_MANIFEST_SHA256:
        raise SystemExit("RNG authority binds a different FULL104 substrate")
    if rng.get("canonical_registry_sha256") != CANONICAL_REGISTRY_SHA256:
        raise SystemExit("RNG authority binds a different canonical registry")
    if rng.get("target_panel_dependency") != "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS":
        raise SystemExit("RNG authority does not explicitly exclude target-panel dependence")
    if rng.get("terminal_outcomes_inspected_before_freeze") is not False:
        raise SystemExit("RNG authority was frozen after terminal outcomes")
    if rng.get("training_authorized") is not False:
        raise SystemExit("RNG authority unexpectedly authorizes training")
    rng_digest = str(rng.get("authority_sha256", ""))
    if len(rng_digest) != 64:
        raise SystemExit("RNG authority digest is missing or malformed")

    if not args.burden_estimator_source.is_file():
        raise SystemExit("burden estimator source is missing")

    contract = AuditBExecutionContractV1(
        contract_id="JEPA_V5_FULL104_AUDIT_B_EXECUTION_CONTRACT_V1",
        phase_iv_sample_freeze_digest=observed_freeze,
        phase_iv_sample_artifact_sha256=sha256_file(args.sample_freeze),
        full104_manifest_sha256=FULL104_MANIFEST_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        heavy_artifact_sha256=HEAVY_ARTIFACT_SHA256,
        heavy_qualification_receipt_sha256=sha256_file(args.heavy_qualification_receipt),
        rng_authority_sha256=rng_digest,
        mask_plan_generator_sha256=MASK_PLAN_GENERATOR_SHA256,
        burden_estimator_source_sha256=sha256_file(args.burden_estimator_source),
        precision_scope_id=args.precision_scope,
    )
    contract.validate()

    payload = {
        "schema": "V5_AUDIT_B_EXECUTION_CONTRACT_V1",
        **asdict(contract),
        "sample_ladder": list(contract.sample_ladder),
        "execution_requirements": list(contract.execution_requirements),
        "execution_authorized": contract.execution_authorized,
        "contract_sha256": contract.canonical_digest(),
        "source_artifacts": {
            "sample_freeze": str(args.sample_freeze),
            "heavy_qualification_receipt": str(args.heavy_qualification_receipt),
            "rng_authority": str(args.rng_authority),
            "burden_estimator_source": str(args.burden_estimator_source),
        },
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "contract_sha256": payload["contract_sha256"],
                "precision_scope_id": payload["precision_scope_id"],
                "execution_authorized": payload["execution_authorized"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
