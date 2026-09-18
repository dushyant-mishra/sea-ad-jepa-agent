#!/usr/bin/env python3
"""Build an outcome-blind target-panel receipt from the FULL104 eligibility receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha, sha256_file
from sea_ad_jepa.v5.target_panel_selector_v2 import TargetPanelSelectionReceiptV2, select_target_cols


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--eligibility", type=Path, required=True)
    p.add_argument("--target-count", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    payload = json.loads(args.eligibility.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_TARGET_ELIGIBILITY_RECEIPT_V1":
        raise SystemExit("eligibility receipt schema mismatch")
    declared = payload.get("receipt_sha256")
    semantic = dict(payload)
    semantic.pop("receipt_sha256", None)
    if declared != canonical_sha(semantic):
        raise SystemExit("eligibility receipt digest mismatch")
    if payload.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("target selection must occur before terminal masking outcomes")

    selected = select_target_cols(
        payload["eligible_target_cols_all_folds"],
        target_count=args.target_count,
        eligibility_receipt_sha256=declared,
    )
    receipt = TargetPanelSelectionReceiptV2(
        eligibility_receipt_sha256=declared,
        target_count=args.target_count,
        selected_target_cols=selected,
    )
    receipt.validate()
    out = {
        "schema": "V5_TARGET_PANEL_SELECTION_RECEIPT_V2",
        **receipt.__dict__,
        "selected_target_cols": list(selected),
        "selector_source_sha256": sha256_file(Path(__file__).resolve()),
        "receipt_sha256": receipt.canonical_digest(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out["receipt_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
