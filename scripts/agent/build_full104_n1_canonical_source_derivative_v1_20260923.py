#!/usr/bin/env python3
"""Build an immutable FULL104 metadata-only heavy-NPZ source derivative.

The original 242MB NPZ remains untouched. Uses the original authenticated
8,915-block Level-4 metadata census, not count matrices. This is a physical
repair artifact for independent review, NOT N1 execution authorization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.audit_b_n1_source_derivative_v1 import (
    build_canonical_source_derivative,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-heavy-artifact", required=True, type=Path)
    p.add_argument("--level4-root", required=True, type=Path)
    p.add_argument("--out-derivative", required=True, type=Path)
    p.add_argument("--out-receipt", required=True, type=Path)
    p.add_argument("--build-metadata-only-derivative", action="store_true")
    args = p.parse_args()
    if not args.build_metadata_only_derivative:
        raise SystemExit(
            "STOP: requires --build-metadata-only-derivative; "
            "no N1 execution is performed by this command"
        )
    out = build_canonical_source_derivative(
        original=args.original_heavy_artifact,
        level4_root=args.level4_root,
        out=args.out_derivative,
        out_receipt=args.out_receipt,
    )
    print(json.dumps({
        "state": out["state"],
        "original_sha256": out["original_heavy_sha256"],
        "derivative_sha256": out["corrected_derivative_sha256"],
        "receipt_sha256": out["receipt_sha256"],
        "changed_members": out["changed_members"],
        "training_authorized": out["training_authorized"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
