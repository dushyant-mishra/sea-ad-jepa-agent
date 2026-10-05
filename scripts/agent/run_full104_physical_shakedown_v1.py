#!/usr/bin/env python3
"""Run the read-only physical FULL104 shakedown inside a fresh runtime envelope."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_physical_shakedown_v1 import run_physical_shakedown
from sea_ad_jepa.v5.full104_runtime_envelope_v1 import (
    live_clean_scientific_head,
    validate_runtime_envelope,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime-root", type=Path, required=True)
    p.add_argument("--worktree", type=Path, required=True)
    p.add_argument("--expected-scientific-anchor", required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--observation-state", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    live_head = live_clean_scientific_head(args.worktree)
    if args.expected_scientific_anchor.lower() != live_head:
        raise SystemExit(
            "expected scientific anchor does not equal the live clean worktree HEAD"
        )

    validate_runtime_envelope(
        args.runtime_root,
        expected_scientific_anchor_git_oid=live_head,
    )
    try:
        out_relative = args.out.resolve().relative_to(args.runtime_root.resolve())
    except ValueError as exc:
        raise SystemExit(
            "physical shakedown receipt must be written inside the fresh runtime envelope"
        ) from exc
    if args.out.exists():
        raise SystemExit("refuse to overwrite an existing physical shakedown receipt")

    receipt = run_physical_shakedown(
        level4_root=args.level4_root,
        registry_path=args.registry,
        observation_state_path=args.observation_state,
    )
    payload = {
        "schema": "V5_FULL104_PHYSICAL_SHAKEDOWN_RECEIPT_V1",
        **asdict(receipt),
        "source_names": list(receipt.source_names),
        "normalization_probe_columns": list(receipt.normalization_probe_columns),
        "receipt_sha256": receipt.canonical_digest(),
        "scientific_scope_note": (
            "READ-ONLY PHYSICAL FULL104 SHAKEDOWN ONLY. No target-panel ladder, "
            "masking-policy outcome, protected outcome, or training authority is opened."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Re-scan the runtime after receipt creation.  The newly written receipt must
    # itself comply with the no-spillover runtime envelope.
    live_head_after = live_clean_scientific_head(args.worktree)
    if live_head_after != live_head:
        raise SystemExit("scientific worktree HEAD changed during FULL104 shakedown")
    validate_runtime_envelope(
        args.runtime_root,
        expected_scientific_anchor_git_oid=live_head,
        allowed_relative_paths=(str(out_relative).replace("\\", "/"),),
    )
    print(
        json.dumps(
            {
                "status": "FULL104_PHYSICAL_SHAKEDOWN_PASS",
                "receipt_sha256": receipt.canonical_digest(),
                "block_count": receipt.block_count,
                "row_count": receipt.row_count,
                "donor_count": receipt.donor_count,
                "operator_count": receipt.operator_count,
                "rows_per_second": receipt.rows_per_second,
                "peak_rss_bytes": receipt.peak_rss_bytes,
                "peak_current_process_gpu_memory_mib": receipt.peak_current_process_gpu_memory_mib,
                "terminal_masking_authorized": False,
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
