#!/usr/bin/env python3
"""Build the prospective FULL104 null-equivalence margin authority V1."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from sea_ad_jepa.v5.null_equivalence_margin_authority_v1 import (
    FULL104_SUBSTRATE_SHA256,
    HISTORICAL_SCALE_CONTEXT_SHA256,
    NullEquivalenceMarginAuthorityV1,
)

HISTORICAL_SCALE_CONTEXT_RELPATH = (
    "analysis/v5_masking_successor_spike_20260917/reports/"
    "JEPA_MASKING_SCALE_STRESS_FOLLOWUP_20260917.md"
)
REQUIRED_SCALE_CONTEXT_SNIPPETS = (
    "Within-donor shuffled negative: mean delta -0.000240",
    "2,000 addresses: mean bounded-score drop 0.0069 "
    "(target-cluster bootstrap 95% CI 0.0030 to 0.0116)",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    historical = args.repo / HISTORICAL_SCALE_CONTEXT_RELPATH
    if not historical.is_file():
        raise SystemExit("frozen historical scale-context artifact is missing")
    observed_sha = sha256_file(historical)
    if observed_sha != HISTORICAL_SCALE_CONTEXT_SHA256:
        raise SystemExit(
            "historical scale-context byte drift: "
            f"expected {HISTORICAL_SCALE_CONTEXT_SHA256}, observed {observed_sha}"
        )
    text = historical.read_text(encoding="utf-8")
    for snippet in REQUIRED_SCALE_CONTEXT_SNIPPETS:
        if snippet not in text:
            raise SystemExit(
                "historical scale-context artifact no longer proves the required "
                f"sanity-check statement: {snippet!r}"
            )

    authority = NullEquivalenceMarginAuthorityV1(
        authority_id="JEPA_V5_FULL104_NULL_EQUIVALENCE_MARGIN_AUTHORITY_V1",
        full104_substrate_sha256=FULL104_SUBSTRATE_SHA256,
        historical_scale_context_artifact_sha256=observed_sha,
    )
    authority.validate()
    payload = {
        "schema": "V5_NULL_EQUIVALENCE_MARGIN_AUTHORITY_V1",
        **authority.__dict__,
        "margin": authority.margin,
        "authority_sha256": authority.canonical_digest(),
        "historical_scale_context_path": HISTORICAL_SCALE_CONTEXT_RELPATH,
        "historical_scale_context_role": authority.historical_role_id,
        "does_not_authorize": [
            "FULL104_DATA",
            "TARGETS",
            "FOLDS",
            "BURDEN",
            "SEED",
            "ROW_CAP",
            "POLICY_SELECTION",
            "PASS_STATUS",
            "RUNTIME",
            "TRAINING",
        ],
        "terminal_outcomes_inspected_before_freeze": False,
        "training_authorized": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(payload["authority_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
