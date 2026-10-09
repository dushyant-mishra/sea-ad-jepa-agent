#!/usr/bin/env python3
"""Original FULL104 heavy-NPZ source-lineage audit (metadata only).

DO NOT treat a diagnostic terminal as N1 execution approval. This command
expects the *original* byte-pinned heavy artifact, which is known to be
internally inconsistent, and produces an immutable QUARANTINE receipt.
It opens all 8,915 authenticated metadata files but NO count matrices.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sea_ad_jepa.v5.audit_b_n1_source_lineage_v1 import (
    audit_original_heavy_source_lineage,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--heavy-artifact", type=Path, required=True)
    p.add_argument("--level4-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    record = audit_original_heavy_source_lineage(
        heavy_artifact=args.heavy_artifact, level4_root=args.level4_root,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(args.out), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({
        "state": record["state"],
        "source_name_order_matches": record["source_name_order_matches"],
        "per_cell_source_aligned": record[
            "src_of_cell_equals_donor_src_at_metadata_donor"
        ],
        "src_of_cell_mismatch_count": record["src_of_cell_mismatch_count"],
        "receipt_sha256": record["receipt_sha256"],
        "training_authorized": False,
    }, sort_keys=True))
    return 0 if record["state"] == (
        "CANONICAL_SOURCE_ALIGNMENT_OBSERVED__DIAGNOSTIC_ONLY"
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())
