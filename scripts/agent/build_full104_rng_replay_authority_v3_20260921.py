#!/usr/bin/env python3
"""Build FULL104 masking RNG replay authority V3 from pre-panel current roots."""
from __future__ import annotations

import argparse
from dataclasses import fields
import hashlib
import json
from pathlib import Path

from sea_ad_jepa.v5.masking_burden_ladder_authority_v2 import (
    MaskingBurdenLadderAuthorityV2,
)
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import (
    MaskingQualificationParametersAuthorityV3,
)
from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import (
    CANONICAL_REGISTRY_SHA256,
    FULL104_SUBSTRATE_SHA256,
    MaskingRngReplayAuthorityV3,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_digest_without(payload: dict, field: str) -> str:
    semantic = dict(payload)
    declared = semantic.pop(field, None)
    raw = json.dumps(
        semantic,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    observed = hashlib.sha256(raw).hexdigest()
    if declared != observed:
        raise SystemExit(f"{field} mismatch: declared={declared!r} observed={observed}")
    return observed


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


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--parameters-authority", type=Path, required=True)
    p.add_argument("--burden-ladder-authority", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    if sha256_file(args.registry) != CANONICAL_REGISTRY_SHA256:
        raise SystemExit("canonical registry artifact hash mismatch")

    split = load(args.split_receipt)
    if split.get("schema") != "V5_FULL104_SOURCE_STRATIFIED_DONOR_SPLIT_RECEIPT_V1":
        raise SystemExit("source-stratified split receipt V1 is required")
    split_digest = canonical_digest_without(split, "receipt_sha256")
    if int(split.get("n_folds", 0)) != 4:
        raise SystemExit("split receipt must contain four outer folds")
    if len(split.get("donor_ids", ())) != 104:
        raise SystemExit("split receipt must contain 104 donors")

    parameters_payload = load(args.parameters_authority)
    if parameters_payload.get("schema") != "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3":
        raise SystemExit("masking parameter authority V3 is required")
    parameters = typed(
        parameters_payload,
        MaskingQualificationParametersAuthorityV3,
        "authority_sha256",
    )
    if parameters.full104_substrate_sha256 != FULL104_SUBSTRATE_SHA256:
        raise SystemExit("masking parameters bind a different FULL104 substrate")

    burden_payload = load(args.burden_ladder_authority)
    if burden_payload.get("schema") != "V5_MASKING_BURDEN_LADDER_AUTHORITY_V2":
        raise SystemExit("masking burden ladder authority V2 is required")
    burden = typed(
        burden_payload,
        MaskingBurdenLadderAuthorityV2,
        "authority_sha256",
    )

    authority = MaskingRngReplayAuthorityV3(
        authority_id="JEPA_V5_FULL104_MASKING_RNG_REPLAY_AUTHORITY_V3",
        full104_substrate_sha256=FULL104_SUBSTRATE_SHA256,
        canonical_registry_sha256=CANONICAL_REGISTRY_SHA256,
        outer_split_receipt_sha256=split_digest,
        qualification_parameters_authority_sha256=parameters.canonical_digest(),
        burden_ladder_authority_sha256=burden.canonical_digest(),
    )
    authority.validate()
    payload = {
        "schema": "V5_MASKING_RNG_REPLAY_AUTHORITY_V3",
        **authority.__dict__,
        "global_seed": authority.global_seed,
        "authority_sha256": authority.canonical_digest(),
        "target_panel_dependency": "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS",
        "terminal_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(
        {
            "authority_sha256": payload["authority_sha256"],
            "global_seed": payload["global_seed"],
            "target_panel_dependency": payload["target_panel_dependency"],
        },
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
