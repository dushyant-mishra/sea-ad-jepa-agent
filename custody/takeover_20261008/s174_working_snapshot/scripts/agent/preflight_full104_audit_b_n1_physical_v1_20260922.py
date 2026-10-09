#!/usr/bin/env python3
"""FULL104 Audit-B N1 READ-ONLY physical input preflight. NO N1 execution.

Authenticate the existing heavy aggregate and its six-donor independent
qualification; bind exact donor IDs, source/fold VALUES and strict-core order
against the frozen split. Never read Level-4 count blocks, select targets,
generate masks, compute burden, evaluate precision or authorize training.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sea_ad_jepa.v5.audit_b_n1_physical_binding_v1 import (
    canonical_digest, inspect_physical_inputs, sha256_file,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--heavy-artifact", type=Path, required=True)
    p.add_argument("--independent-qualification", type=Path, required=True)
    p.add_argument("--split-receipt", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    record = inspect_physical_inputs(
        heavy_artifact=args.heavy_artifact,
        independent_receipt=args.independent_qualification,
        split_receipt=args.split_receipt,
    )
    record["binding_implementation_file_sha256"] = sha256_file(
        Path(__file__).resolve().parents[2]
        / "src/sea_ad_jepa/v5/audit_b_n1_physical_binding_v1.py"
    )
    record["preflight_source_file_sha256"] = sha256_file(Path(__file__))
    record.pop("receipt_sha256")
    record["receipt_sha256"] = canonical_digest(record)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(args.out), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"state": record["state"],
                      "receipt_sha256": record["receipt_sha256"],
                      "masks_executed": False,
                      "burden_calculated": False,
                      "training_authorized": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
