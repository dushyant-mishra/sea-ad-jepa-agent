#!/usr/bin/env python3
"""Prepare or validate a fresh current-root-bound FULL104 shakedown runtime."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_runtime_envelope_v1 import (
    CANONICAL_REGISTRY_SHA256,
    FULL104_BLOCK_MANIFEST_SHA256,
    OBSERVATION_STATE_SHA256,
    live_clean_scientific_head,
    prepare_fresh_runtime,
    sha256_file,
    validate_runtime_envelope,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("prepare", "validate"), required=True)
    p.add_argument("--runtime-root", type=Path, required=True)
    p.add_argument("--worktree", type=Path, required=True)
    p.add_argument("--expected-scientific-anchor", required=True)
    p.add_argument("--level4-root", type=Path)
    p.add_argument("--registry", type=Path)
    p.add_argument("--observation-state", type=Path)
    args = p.parse_args()

    live_head = live_clean_scientific_head(args.worktree)
    if args.expected_scientific_anchor.lower() != live_head:
        raise SystemExit(
            "expected scientific anchor does not equal the live clean worktree HEAD"
        )

    if args.mode == "prepare":
        for name in ("level4_root", "registry", "observation_state"):
            if getattr(args, name) is None:
                raise SystemExit(f"--{name.replace('_', '-')} is required in prepare mode")
        manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
        if not manifest.is_file():
            raise SystemExit("FULL104 Level-4 block manifest is missing")
        roots = {
            "full104_block_manifest_sha256": sha256_file(manifest),
            "canonical_registry_sha256": sha256_file(args.registry),
            "observation_state_sha256": sha256_file(args.observation_state),
        }
        expected = {
            "full104_block_manifest_sha256": FULL104_BLOCK_MANIFEST_SHA256,
            "canonical_registry_sha256": CANONICAL_REGISTRY_SHA256,
            "observation_state_sha256": OBSERVATION_STATE_SHA256,
        }
        for role, value in roots.items():
            if value != expected[role]:
                raise SystemExit(
                    f"{role} mismatch: expected {expected[role]}, observed {value}"
                )
        envelope = prepare_fresh_runtime(
            args.runtime_root,
            scientific_anchor_git_oid=live_head,
            **roots,
        )
    else:
        envelope = validate_runtime_envelope(
            args.runtime_root,
            expected_scientific_anchor_git_oid=live_head,
        )

    print(
        json.dumps(
            {
                "status": (
                    "FULL104_FRESH_RUNTIME_PREPARED"
                    if args.mode == "prepare"
                    else "FULL104_RUNTIME_ENVELOPE_VALID"
                ),
                "runtime_root": str(args.runtime_root),
                "runtime_envelope_sha256": envelope.canonical_digest(),
                "target_panel_ladder_authorized": False,
                "terminal_masking_authorized": False,
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
