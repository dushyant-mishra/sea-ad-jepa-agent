#!/usr/bin/env python3
"""Build FULL104 PrecisionAuthorityV4 after the target panel is control-calibrated."""
from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4
from sea_ad_jepa.v5.target_panel_authority_v3 import TargetPanelAuthorityV3
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import TargetPanelSizingReceiptV2

EXPECTED_FULL104_MANIFEST_SHA256="66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256="cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"


def load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def typed(payload:dict,cls,sha_field:str):
    names={f.name for f in fields(cls)}
    obj=cls(**{name:payload[name] for name in names})
    obj.validate()
    if payload.get(sha_field)!=obj.canonical_digest():
        raise SystemExit(f"{cls.__name__} digest mismatch")
    return obj


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--support-authority",type=Path,required=True)
    p.add_argument("--target-panel-authority",type=Path,required=True)
    p.add_argument("--target-panel-sizing-receipt",type=Path,required=True)
    p.add_argument("--outer-split-authority",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()

    support=load(args.support_authority)
    if canonical_sha(support)!=EXPECTED_SUPPORT_AUTHORITY_CANONICAL_JSON_SHA256:
        raise SystemExit("support authority is not the exact current semantic authority")
    support_sha=sha256_file(args.support_authority)
    if support.get("schema")!="V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1":
        raise SystemExit("support authority schema mismatch")
    if support.get("full104_substrate_sha256")!=EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("support authority uses a different FULL104 substrate")
    if support.get("training_authorized") is not False:
        raise SystemExit("support authority unexpectedly authorizes training")

    panel_payload=load(args.target_panel_authority)
    if panel_payload.get("schema")!="V5_TARGET_PANEL_AUTHORITY_V3":
        raise SystemExit("target-panel authority V3 is required")
    panel=typed(panel_payload,TargetPanelAuthorityV3,"authority_sha256")
    if panel.full104_substrate_sha256!=EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("target panel uses a different FULL104 substrate")
    if panel.support_estimability_authority_sha256!=support_sha:
        raise SystemExit("target panel and precision use different support authorities")

    sizing_payload=load(args.target_panel_sizing_receipt)
    if sizing_payload.get("schema")!="V5_TARGET_PANEL_SIZING_RECEIPT_V2":
        raise SystemExit("target-panel sizing receipt V2 is required")
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
    if sizing.canonical_digest()!=panel.target_panel_sizing_receipt_sha256:
        raise SystemExit("target panel is bound to a different sizing receipt")

    split_payload=load(args.outer_split_authority)
    if split_payload.get("schema")!="V5_OUTER_DONOR_SPLIT_AUTHORITY_V1":
        raise SystemExit("outer split authority V1 is required")
    outer=typed(split_payload,OuterDonorSplitAuthorityV1,"authority_sha256")
    if outer.full104_substrate_sha256!=EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("outer split uses a different FULL104 substrate")
    if outer.n_donors!=104 or outer.n_folds!=4:
        raise SystemExit("outer split donor/fold geometry mismatch")

    authority=QualificationPrecisionAuthorityV4(
        authority_id="JEPA_V5_FULL104_QUALIFICATION_PRECISION_AUTHORITY_V4",
        support_estimability_authority_sha256=support_sha,
        target_panel_authority_sha256=panel.canonical_digest(),
        target_panel_sizing_receipt_sha256=sizing.canonical_digest(),
        outer_split_authority_sha256=outer.canonical_digest(),
        required_target_count=panel.target_count,
    )
    authority.bind_target_panel(panel,sizing)
    authority.assert_sufficient(
        target_count=panel.target_count,
        donor_count=outer.n_donors,
        outer_fold_count=outer.n_folds,
    )
    payload={
        "schema":"V5_QUALIFICATION_PRECISION_AUTHORITY_V4",
        **authority.__dict__,
        "bootstrap_seed":authority.bootstrap_seed,
        "authority_sha256":authority.canonical_digest(),
        "terminal_outcomes_inspected_before_freeze":False,
        "training_authorized":False,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
