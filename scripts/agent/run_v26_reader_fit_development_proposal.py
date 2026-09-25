#!/usr/bin/env python3
"""Read-only, byte-authenticated selection-row proposal: NEVER executes JEPA.

A full-data sample is emitted ONLY after the frozen pass1 and calibration
archive pass their exact SHA-256 and per-donor census checks. A separate
current-V5 execution authority is required before consuming this sample for
any real update. Never derive training permission from this receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

from sea_ad_jepa.v5.reader_fit_development_sampler_v1 import propose_from_frozen_pass1


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_synthetic_safe(
    *,
    out_dir: Path,
    proposal,
    receipt: dict[str, object],
) -> dict[str, object]:
    """File mechanics only; this helper is not a physical-source authority."""
    if out_dir.exists():
        raise FileExistsError("refuse an existing result directory: no historical output spillover")
    if not out_dir.parent.is_dir():
        raise ValueError("out_dir parent must already exist; use a new versioned runtime parent")
    if receipt.get("training_authorized") is not False:
        raise ValueError("sampler cannot emit a training-authorized receipt")
    if receipt.get("schema") != "V26_READER_FIT_DEVELOPMENT_PROPOSAL_V1":
        raise ValueError("unexpected proposal receipt schema")
    if receipt.get("selection_rows_sha256") != proposal.nontraining_report()["selection_rows_sha256"]:
        raise ValueError("selection rows differ from receipt")
    out_dir.mkdir(mode=0o700)
    selection_path = out_dir / "development_update_selection.npz"
    with selection_path.open("xb") as handle:
        np.savez_compressed(
            handle,
            selection_rows=proposal.selection_rows,
            donor_codes=proposal.donor_codes,
            proposal_probabilities=proposal.proposal_probabilities,
            importance_weights=proposal.importance_weights,
        )
    report = {
        **receipt,
        "selection_npz_sha256": _hash(selection_path),
        "selection_npz_bytes": selection_path.stat().st_size,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "command_scientific_scope": "READ_ONLY_PROPOSAL_NEVER_TRAINING",
        "training_authorized": False,
        "protected_outcomes_opened": False,
    }
    (out_dir / "development_update_receipt.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8",
    )
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pass1", type=Path, required=True)
    p.add_argument("--calibration-zip", type=Path, required=True)
    p.add_argument("--run-seed", type=int, required=True)
    p.add_argument("--update-index", type=int, required=True)
    p.add_argument("--presentations", type=int, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()
    if args.out_dir.exists():
        raise SystemExit("STOP: refuse to overwrite any existing output directory")
    selection, receipt = propose_from_frozen_pass1(
        pass1_path=args.pass1, calibration_zip=args.calibration_zip,
        run_seed=args.run_seed, update_index=args.update_index,
        presentations=args.presentations,
    )
    report = _write_synthetic_safe(out_dir=args.out_dir, proposal=selection, receipt=receipt)
    print(json.dumps({
        "status": report["status"],
        "scope": "PHYSICAL_INPUTS_BOUND__NO_FULL104_RAW_LINEAGE__NO_TRAINING",
        "selection_npz_sha256": report["selection_npz_sha256"],
        "receipt_sha256": _hash(args.out_dir / "development_update_receipt.json"),
        "training_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
