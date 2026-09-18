#!/usr/bin/env python3
"""Build the current FULL104 TargetPanelAuthorityV3 from calibrated evidence."""
from __future__ import annotations

import argparse
from dataclasses import fields
import inspect
import json
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.full104_control_calibration_cache_evaluator_v1 import (
    load_control_calibration_cache,
)
from sea_ad_jepa.v5.target_panel_authority_v3 import (
    OUTCOME_FIREWALL_ID,
    SELECTION_POLICY_ID,
    STRICT_SUPPORT_ID,
    TargetPanelAuthorityV3,
)
from sea_ad_jepa.v5 import target_panel_selector_v2 as selector_impl
from sea_ad_jepa.v5.target_panel_selector_v2 import TargetPanelSelectionReceiptV2
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import (
    TargetPanelControlVerdictV2,
    TargetPanelSizingPlanAuthorityV2,
    TargetPanelSizingReceiptV2,
)

EXPECTED_FULL104_MANIFEST_SHA256="66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_REGISTRY_AUTHORITY_DIGEST="28b20a457c44ac864c375492c8875e865ed6fe6d2000338d5fd46d9557a25676"
EXPECTED_ELIGIBLE_TARGET_COUNT=17053


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_receipt(payload: dict, schema: str, path: Path) -> str:
    if payload.get("schema") != schema:
        raise SystemExit(f"{path}: expected schema {schema}")
    declared=payload.get("receipt_sha256")
    semantic=dict(payload); semantic.pop("receipt_sha256",None)
    # Some typed receipts add informative fields outside their canonical dataclass.
    if schema in (
        "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",
    ):
        if declared!=canonical_sha(semantic):
            raise SystemExit(f"{path}: receipt digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is True:
        raise SystemExit(f"{path}: terminal masking outcomes were inspected")
    return str(declared)


def load_verdict(path: Path) -> TargetPanelControlVerdictV2:
    payload=load(path)
    if payload.get("schema")!="V5_TARGET_PANEL_CONTROL_VERDICT_V2":
        raise SystemExit(f"{path}: target-panel verdict schema mismatch")
    names={f.name for f in fields(TargetPanelControlVerdictV2)}
    verdict=TargetPanelControlVerdictV2(**{name:payload[name] for name in names})
    verdict.validate()
    if payload.get("verdict_sha256")!=verdict.canonical_digest():
        raise SystemExit(f"{path}: target-panel verdict digest mismatch")
    return verdict


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache-dir",type=Path,required=True)
    p.add_argument("--canonical-registry-authority",type=Path,required=True)
    p.add_argument("--support-authority",type=Path,required=True)
    p.add_argument("--census-authority",type=Path,required=True)
    p.add_argument("--target-eligibility",type=Path,required=True)
    p.add_argument("--sizing-receipt",type=Path,required=True)
    p.add_argument("--capacity-verdict",type=Path,action="append",required=True)
    p.add_argument("--selection-receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()

    cache=load_control_calibration_cache(args.cache_dir)
    cache.manifest.assert_calibration_only()

    census=load(args.census_authority)
    if census.get("schema")!="V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise SystemExit("census V2 authority is required")
    census_root=str(census.get("census_authority_sha256",""))
    semantic=dict(census); semantic.pop("census_authority_sha256",None)
    if census_root!=canonical_sha(semantic):
        raise SystemExit("census V2 canonical digest mismatch")
    if census_root!=cache.manifest.census_authority_sha256:
        raise SystemExit("cache is bound to a different census authority")

    eligibility=load(args.target_eligibility)
    eligibility_root=require_receipt(
        eligibility,"V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1",args.target_eligibility
    )
    if eligibility_root!=cache.manifest.target_eligibility_receipt_sha256:
        raise SystemExit("cache is bound to a different target-eligibility receipt")
    if int(eligibility.get("eligible_target_count",-1))!=EXPECTED_ELIGIBLE_TARGET_COUNT:
        raise SystemExit("eligible target count mismatch")

    support=load(args.support_authority)
    support_sha=sha256_file(args.support_authority)
    if support.get("schema")!="V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    if support.get("full104_substrate_sha256")!=EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("support authority uses a different FULL104 substrate")
    if support_sha!=cache.manifest.support_estimability_authority_sha256:
        raise SystemExit("cache is bound to a different support authority")
    if support.get("training_authorized") is not False:
        raise SystemExit("support authority unexpectedly authorizes training")

    registry=load(args.canonical_registry_authority)
    if registry.get("schema")!="V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1":
        raise SystemExit("canonical registry authority schema mismatch")
    registry_digest=str(registry.get("canonical_authority_digest",""))
    if registry_digest!=EXPECTED_REGISTRY_AUTHORITY_DIGEST:
        raise SystemExit("canonical registry authority digest mismatch")
    if registry.get("FULL104_SUBSTRATE",{}).get("sha256")!=EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("canonical registry authority uses a different FULL104 substrate")

    plan=TargetPanelSizingPlanAuthorityV2(
        authority_id="JEPA_V5_FULL104_TARGET_PANEL_SIZING_PLAN_V2",
        census_authority_sha256=census_root,
        target_eligibility_receipt_sha256=eligibility_root,
        independent_donor_count=104,
        eligible_target_count=EXPECTED_ELIGIBLE_TARGET_COUNT,
    )
    plan.validate()

    verdicts={}
    for path in args.capacity_verdict:
        verdict=load_verdict(path)
        if verdict.target_count in verdicts:
            raise SystemExit("duplicate target-panel capacity verdict")
        verdicts[verdict.target_count]=verdict
    verdicts=dict(sorted(verdicts.items()))

    sizing_payload=load(args.sizing_receipt)
    if sizing_payload.get("schema")!="V5_TARGET_PANEL_SIZING_RECEIPT_V2":
        raise SystemExit("target-panel sizing receipt schema mismatch")
    sizing=TargetPanelSizingReceiptV2(
        plan_authority_sha256=sizing_payload["plan_authority_sha256"],
        selected_target_count=int(sizing_payload["selected_target_count"]),
        evaluated_counts=tuple(map(int,sizing_payload["evaluated_counts"])),
        verdict_digest_by_count={int(k):str(v) for k,v in sizing_payload["verdict_digest_by_count"].items()},
        real_masking_policy_outcomes_inspected=bool(sizing_payload.get("real_masking_policy_outcomes_inspected",False)),
        training_authorized=bool(sizing_payload.get("training_authorized",False)),
    )
    sizing.validate()
    if sizing_payload.get("receipt_sha256")!=sizing.canonical_digest():
        raise SystemExit("target-panel sizing receipt digest mismatch")
    sizing.bind_verdicts(plan,verdicts)

    selection_payload=load(args.selection_receipt)
    if selection_payload.get("schema")!="V5_TARGET_PANEL_SELECTION_RECEIPT_V2":
        raise SystemExit("target-panel selection receipt schema mismatch")
    selection=TargetPanelSelectionReceiptV2(
        eligibility_receipt_sha256=selection_payload["eligibility_receipt_sha256"],
        target_count=int(selection_payload["target_count"]),
        selected_target_cols=tuple(map(int,selection_payload["selected_target_cols"])),
        selector_id=selection_payload["selector_id"],
        namespace=selection_payload["namespace"],
        terminal_masking_outcomes_inspected=bool(selection_payload.get("terminal_masking_outcomes_inspected",False)),
        training_authorized=bool(selection_payload.get("training_authorized",False)),
    )
    selection.validate()
    if selection_payload.get("receipt_sha256")!=selection.canonical_digest():
        raise SystemExit("target-panel selection receipt digest mismatch")
    actual_selector_sha=sha256_file(Path(inspect.getfile(selector_impl)).resolve())
    if selection_payload.get("selector_source_sha256")!=actual_selector_sha:
        raise SystemExit("selection receipt is not bound to the live target selector source")

    target_count=sizing.selected_target_count
    if selection.target_count!=target_count:
        raise SystemExit("selection and calibrated sizing target counts disagree")
    expected_prefix=tuple(map(int,cache.target_cols[:target_count]))
    if selection.selected_target_cols!=expected_prefix:
        raise SystemExit("selected target columns do not match the authenticated cache prefix")

    authority=TargetPanelAuthorityV3(
        authority_id="JEPA_V5_FULL104_TARGET_PANEL_AUTHORITY_V3",
        full104_substrate_sha256=EXPECTED_FULL104_MANIFEST_SHA256,
        canonical_registry_authority_sha256=registry_digest,
        support_estimability_authority_sha256=support_sha,
        target_eligibility_receipt_sha256=eligibility_root,
        target_panel_sizing_plan_sha256=plan.canonical_digest(),
        target_panel_sizing_receipt_sha256=sizing.canonical_digest(),
        target_selection_receipt_sha256=selection.canonical_digest(),
        selector_source_sha256=actual_selector_sha,
        support_state_policy_id=STRICT_SUPPORT_ID,
        selection_policy_id=SELECTION_POLICY_ID,
        outcome_firewall_policy_id=OUTCOME_FIREWALL_ID,
        target_count=target_count,
    )
    authority.bind(plan,sizing,selection)
    payload={
        "schema":"V5_TARGET_PANEL_AUTHORITY_V3",
        **authority.__dict__,
        "authority_sha256":authority.canonical_digest(),
        "calibration_cache_manifest_sha256":cache.manifest_sha256,
        "calibration_cache_role_id":cache.manifest.cache_role_id,
        "terminal_masking_outcomes_inspected":False,
        "training_authorized":False,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(payload["authority_sha256"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
