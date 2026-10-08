#!/usr/bin/env python3
"""Build the current FULL104 outer-donor split authority from the census split receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1

EXPECTED_FULL104_MANIFEST_SHA256="66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_FOLD_SIZES=(28,26,25,25)
EXPECTED_DONORS=104


def load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--split-receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()

    split=load(args.split_receipt)
    if split.get("schema")!="V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1":
        raise SystemExit("split receipt schema mismatch")
    declared=split.get("receipt_sha256")
    semantic=dict(split); semantic.pop("receipt_sha256",None)
    if declared!=canonical_sha(semantic):
        raise SystemExit("split receipt digest mismatch")
    if split.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("outer split must be frozen before terminal masking outcomes")
    donor_ids=tuple(map(str,split.get("donor_ids",[])))
    donor_source=tuple(map(int,split.get("donor_source_code",[])))
    source_names=tuple(map(str,split.get("source_names",[])))
    fold=tuple(map(int,split.get("fold_by_donor",[])))
    if len(donor_ids)!=EXPECTED_DONORS or len(set(donor_ids))!=EXPECTED_DONORS:
        raise SystemExit("split receipt donor registry must contain 104 unique donors")
    if len(donor_source)!=EXPECTED_DONORS or len(fold)!=EXPECTED_DONORS:
        raise SystemExit("split receipt donor vectors must contain 104 entries")
    if int(split.get("n_folds",-1))!=4 or tuple(map(int,split.get("fold_sizes",[])))!=EXPECTED_FOLD_SIZES:
        raise SystemExit("split receipt fold geometry mismatch")
    if sorted(set(fold))!=[0,1,2,3]:
        raise SystemExit("split receipt must use exactly four folds")
    if min(donor_source)<0 or max(donor_source)>=len(source_names):
        raise SystemExit("split receipt donor source code is invalid")

    donor_registry_sha=canonical_sha({
        "schema":"V5_FULL104_DONOR_REGISTRY_SEMANTIC_V1",
        "donor_ids":list(donor_ids),
        "donor_source_code":list(donor_source),
        "source_names":list(source_names),
    })
    authority=OuterDonorSplitAuthorityV1(
        authority_id="JEPA_V5_FULL104_OUTER_DONOR_SPLIT_AUTHORITY_V1",
        full104_substrate_sha256=EXPECTED_FULL104_MANIFEST_SHA256,
        donor_registry_sha256=donor_registry_sha,
        fold_assignment_artifact_sha256=str(declared),
        split_semantics_id="OUTER_HELD_DONOR_EVALUATION_V1",
        screening_scope_policy_id="SCREEN_AND_FIT_ON_OUTER_TRAIN_DONORS_ONLY_V1",
        heldout_scope_policy_id="HELDOUT_DONORS_EVALUATION_ONLY_V1",
        n_folds=4,
        n_donors=EXPECTED_DONORS,
    )
    authority.validate()
    payload={
        "schema":"V5_OUTER_DONOR_SPLIT_AUTHORITY_V1",
        **authority.__dict__,
        "authority_sha256":authority.canonical_digest(),
        "source_split_receipt_sha256":declared,
        "terminal_masking_outcomes_inspected":False,
        "training_authorized":False,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
