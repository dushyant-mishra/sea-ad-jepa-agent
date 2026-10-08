#!/usr/bin/env python3
"""Build the current FULL104 sequential burden-ladder authority V2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import canonical_sha
from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import MaskingBurdenLadderAuthorityV2

EXPECTED_BLOCK_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--census-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    census = load(args.census_authority)
    if census.get("schema") != "V5_FULL104_READONLY_CENSUS_AUTHORITY_V2":
        raise SystemExit("census authority V2 is required")
    semantic = dict(census)
    census_root = semantic.pop("census_authority_sha256", None)
    if census_root != canonical_sha(semantic):
        raise SystemExit("census authority digest mismatch")
    if census.get("training_authorized") is not False:
        raise SystemExit("census authority unexpectedly authorizes training")
    if census.get("terminal_masking_outcomes_inspected") is not False:
        raise SystemExit("census authority records terminal outcome access")
    if census.get("substrate", {}).get("full104_block_manifest_sha256") != EXPECTED_BLOCK_MANIFEST_SHA256:
        raise SystemExit("census authority binds a different FULL104 substrate")

    authority = MaskingBurdenLadderAuthorityV2(
        authority_id="JEPA_V5_FULL104_MASKING_BURDEN_LADDER_AUTHORITY_V2",
        census_authority_sha256=str(census_root),
    )
    authority.validate()
    payload = {
        "schema": "V5_MASKING_BURDEN_LADDER_AUTHORITY_V2",
        **authority.__dict__,
        "rungs": [list(x) for x in authority.rungs],
        "authority_sha256": authority.canonical_digest(),
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
