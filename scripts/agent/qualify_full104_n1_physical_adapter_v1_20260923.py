#!/usr/bin/env python3
"""Metadata-only PHYSICAL qualification of the corrected-source N1 adapter.

Authenticates the corrected FULL104 chain by bytes, runs the read-only structural
preflight and emits a content-addressed adapter-qualification receipt.

It opens no molecular outcome, selects no target, draws no mask, and issues no N1
execution authority. Reaching the terminal here means the inputs are authenticated
and the adapter's gates executed; it does not mean N1 may run.
"""
from __future__ import annotations

import argparse
import hashlib
import platform
import sys
from pathlib import Path

import numpy as np

from sea_ad_jepa.v5.audit_b_n1_physical_lineage_adapter_v1 import (
    ExecutionMode, PhysicalLineageError, authenticate_corrected_inputs,
    build_context, emit_adapter_qualification_receipt,
    preflight_corrected_derivative, require_n1_execution_authority, sha256_file,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for a in ("derivative", "pass1", "split-receipt", "level4-manifest",
              "array-manifest", "preflight-receipt", "out"):
        ap.add_argument("--" + a, type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite an existing receipt: {args.out}")

    mode = ExecutionMode.PHYSICAL_QUALIFICATION
    me = Path(__file__).resolve()
    adapter = (me.parents[2] / "src/sea_ad_jepa/v5/"
               "audit_b_n1_physical_lineage_adapter_v1.py")

    inputs = authenticate_corrected_inputs(
        mode=mode, derivative=args.derivative, pass1=args.pass1,
        split_receipt=args.split_receipt, level4_manifest=args.level4_manifest,
        array_manifest=args.array_manifest, preflight_receipt=args.preflight_receipt)
    print(f"authenticated {len(inputs)} physical inputs by byte digest", flush=True)

    identity = preflight_corrected_derivative(derivative=args.derivative,
                                              pass1=args.pass1, mode=mode)
    print("read-only structural preflight passed; source invariant clean", flush=True)

    ctx = build_context(
        mode=mode, task="AUDIT_B_N1_PHYSICAL_ADAPTER_QUALIFICATION",
        code_sha256=sha256_file(adapter), inputs=inputs,
        identity_digests=identity,
        parameters={"donors": 104, "strict_core": 17186, "folds": 4,
                    "source_names": "HVS|NPH52|SEA_AD"})

    # The gate that must stay shut, exercised here rather than merely asserted.
    try:
        require_n1_execution_authority(ctx)
        raise SystemExit("DEFECT: adapter qualification granted N1 authority")
    except PhysicalLineageError as exc:
        if "STOP_N1_NOT_AUTHORIZED" not in str(exc):
            raise
        n1_gate = str(exc).split(":")[0]

    sha = emit_adapter_qualification_receipt(
        path=args.out, ctx=ctx,
        body={"terminal": "PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW",
              "n1_authority_gate_exercised": n1_gate,
              "molecular_outcomes_opened": False,
              "environment": {"platform": platform.platform(),
                              "python": sys.version.split()[0],
                              "numpy": np.__version__},
              "limitations": [
                  "adapter qualification is not N1 execution authority",
                  "all-104 raw-count reaggregation from Level-4 remains UNPROVED; the "
                  "exhaustive metadata comparison does not establish it",
                  "the physical burden stream has not been exercised"]})
    print(f"receipt {args.out} sha256 {sha}")
    print("PHYSICAL_ADAPTER_QUALIFIED_FOR_INDEPENDENT_REVIEW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
