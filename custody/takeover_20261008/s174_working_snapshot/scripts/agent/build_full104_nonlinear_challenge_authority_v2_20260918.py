#!/usr/bin/env python3
"""Build nonlinear FULL104 challenge V2 from explicit historical provenance roots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v2 import NonlinearMaskingChallengeAuthorityV2

HISTORICAL_SCRIPT = "analysis/v5_masking_successor_spike_20260917/scripts/outer5200_nonlinear_probe32.py"
HISTORICAL_SUMMARY = "analysis/v5_masking_successor_spike_20260917/results/outer5200_nonlinear32_summary.csv"


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--primary-parameters-sha256", required=True)
    p.add_argument("--outer-split-sha256", required=True)
    p.add_argument("--target-panel-sha256", required=True)
    p.add_argument("--out", type=Path, required=True)
    args=p.parse_args()

    script=args.repo / HISTORICAL_SCRIPT
    summary=args.repo / HISTORICAL_SUMMARY
    text=script.read_text(encoding="utf-8")
    required=("HistGradientBoostingRegressor", "max_iter=50", "max_leaf_nodes=15", "l2_regularization=1.0")
    for fragment in required:
        if fragment not in text:
            raise SystemExit(f"historical nonlinear script no longer proves {fragment!r}")

    authority=NonlinearMaskingChallengeAuthorityV2(
        authority_id="JEPA_V5_FULL104_NONLINEAR_CHALLENGE_AUTHORITY_V2",
        primary_parameters_authority_sha256=args.primary_parameters_sha256,
        outer_split_authority_sha256=args.outer_split_sha256,
        target_panel_authority_sha256=args.target_panel_sha256,
        historical_nonlinear_script_sha256=sha256_file(script),
        historical_nonlinear_summary_sha256=sha256_file(summary),
    )
    authority.validate()
    payload={
        "schema":"V5_NONLINEAR_MASKING_CHALLENGE_AUTHORITY_V2",
        **authority.__dict__,
        "random_seed": authority.random_seed,
        "authority_sha256": authority.canonical_digest(),
        "historical_role":"SUPPORTING_CAPACITY_PROVENANCE_NOT_PRODUCTION_OUTCOME_AUTHORITY",
        "sampling_note":"256 cells per donor is a new FULL104 donor-balanced cap; it is not inherited from discovery.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(payload["authority_sha256"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
