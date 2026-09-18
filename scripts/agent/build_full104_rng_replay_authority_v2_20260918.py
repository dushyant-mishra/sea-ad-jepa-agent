#!/usr/bin/env python3
"""Build FULL104 masking RNG replay authority V2 from current authority objects."""
from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path

from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import MaskingBurdenLadderAuthorityV2
from sea_ad_jepa.v5.masking_rng_replay_authority_v2 import MaskingRngReplayAuthorityV2
from sea_ad_jepa.v5.outer_split_authority_v1 import OuterDonorSplitAuthorityV1
from sea_ad_jepa.v5.target_panel_authority_v3 import TargetPanelAuthorityV3

EXPECTED_FULL104_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
EXPECTED_REGISTRY_AUTHORITY_DIGEST = "28b20a457c44ac864c375492c8875e865ed6fe6d2000338d5fd46d9557a25676"


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


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--canonical-registry-authority", type=Path, required=True)
    p.add_argument("--outer-split-authority", type=Path, required=True)
    p.add_argument("--target-panel-authority", type=Path, required=True)
    p.add_argument("--burden-ladder-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    registry = load(args.canonical_registry_authority)
    if registry.get("schema") != "V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1":
        raise SystemExit("canonical registry authority schema mismatch")
    registry_digest = str(registry.get("canonical_authority_digest", ""))
    if registry_digest != EXPECTED_REGISTRY_AUTHORITY_DIGEST:
        raise SystemExit("canonical registry authority digest mismatch")
    if registry.get("FULL104_SUBSTRATE", {}).get("sha256") != EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("canonical registry authority binds a different FULL104 substrate")
    if registry.get("training_authorized") is not False:
        raise SystemExit("canonical registry authority unexpectedly authorizes training")

    outer_payload = load(args.outer_split_authority)
    if outer_payload.get("schema") != "V5_OUTER_DONOR_SPLIT_AUTHORITY_V1":
        raise SystemExit("outer split authority V1 is required")
    outer = typed(outer_payload, OuterDonorSplitAuthorityV1, "authority_sha256")
    if outer.full104_substrate_sha256 != EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("outer split binds a different FULL104 substrate")

    panel_payload = load(args.target_panel_authority)
    if panel_payload.get("schema") != "V5_TARGET_PANEL_AUTHORITY_V3":
        raise SystemExit("target panel authority V3 is required")
    panel = typed(panel_payload, TargetPanelAuthorityV3, "authority_sha256")
    if panel.full104_substrate_sha256 != EXPECTED_FULL104_MANIFEST_SHA256:
        raise SystemExit("target panel binds a different FULL104 substrate")
    if panel.canonical_registry_authority_sha256 != registry_digest:
        raise SystemExit("target panel binds a different canonical registry")

    burden_payload = load(args.burden_ladder_authority)
    if burden_payload.get("schema") != "V5_MASKING_BURDEN_LADDER_AUTHORITY_V2":
        raise SystemExit("burden ladder authority V2 is required")
    burden = typed(burden_payload, MaskingBurdenLadderAuthorityV2, "authority_sha256")

    authority = MaskingRngReplayAuthorityV2(
        authority_id="JEPA_V5_FULL104_MASKING_RNG_REPLAY_AUTHORITY_V2",
        canonical_registry_authority_sha256=registry_digest,
        outer_split_authority_sha256=outer.canonical_digest(),
        target_panel_authority_sha256=panel.canonical_digest(),
        burden_ladder_authority_sha256=burden.canonical_digest(),
    )
    authority.validate()
    payload = {
        "schema": "V5_MASKING_RNG_REPLAY_AUTHORITY_V2",
        **authority.__dict__,
        "global_seed": authority.global_seed,
        "authority_sha256": authority.canonical_digest(),
        "terminal_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
