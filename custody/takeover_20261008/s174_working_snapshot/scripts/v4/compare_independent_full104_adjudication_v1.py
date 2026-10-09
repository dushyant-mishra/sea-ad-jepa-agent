#!/usr/bin/env python3
"""Compare an already-frozen independent FULL104 adjudication to production output."""
from __future__ import annotations

import argparse
import hashlib
import json
import csv
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--independent-dir", type=Path, required=True)
    ap.add_argument("--production-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    ind_json = args.independent_dir / "INDEPENDENT_FULL104_REAL_RESULT_ADJUDICATION.json"
    ind_csv = args.independent_dir / "INDEPENDENT_FULL104_REFIT_NULL_CALIBRATION.csv"
    ind_manifest = args.independent_dir / "INDEPENDENT_FULL104_REAL_RESULT_MANIFEST.csv"
    prod_json = args.production_dir / "FULL512_REFIT_NULL_SELECTION.json"
    prod_csv = args.production_dir / "FULL512_REFIT_NULL_CALIBRATION.csv"

    independent = json.loads(ind_json.read_text(encoding="utf-8"))
    production = json.loads(prod_json.read_text(encoding="utf-8"))
    if independent.get("production_selection_opened") or independent.get("production_calibration_opened"):
        raise SystemExit("independent package was not blinded")

    ind = pd.read_csv(ind_csv)
    ind = ind[ind["population"].eq("ALL")]
    cols = ["sketch", "dimension", "signal_supported", "stability_supported",
            "predictability_supported", "jointly_supported"]
    prod = pd.read_csv(prod_csv)
    left = ind[cols].sort_values(["sketch", "dimension"]).reset_index(drop=True)
    right = prod[cols].sort_values(["sketch", "dimension"]).reset_index(drop=True)
    tables_exact = left.equals(right)
    if not tables_exact:
        raise SystemExit("independent/production support tables disagree")

    expected = {
        "candidate_D_shared": independent["ALL"]["one_se_candidate"],
        "first_jointly_unsupported_dimension": independent["ALL"]["first_jointly_unsupported_dimension"],
        "lawful_prefix": independent["ALL"]["lawful_contiguous_prefix"],
    }
    selection_exact = all(production.get(k) == v for k, v in expected.items())
    if not selection_exact:
        raise SystemExit("independent/production selection disagree")

    result = {
        "schema": "independent-production-full104-comparison-v1",
        "status": "PASS_EXACT_INDEPENDENT_PRODUCTION_AGREEMENT",
        "independent_was_frozen_before_production_open": True,
        "support_rows": int(len(left)),
        "support_booleans_exact": tables_exact,
        "selection_exact": selection_exact,
        "selection": production,
        "input_sha256": {
            "independent_adjudication": sha256(ind_json),
            "independent_calibration": sha256(ind_csv),
            "independent_manifest": sha256(ind_manifest),
            "production_selection": sha256(prod_json),
            "production_calibration": sha256(prod_csv),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    manifest = args.output.parent / "INDEPENDENT_VS_PRODUCTION_COMPARISON_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"])
        w.writeheader()
        for path in (args.output, Path(__file__).resolve()):
            w.writerow({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    print(json.dumps({"status": result["status"], "output_sha256": sha256(args.output),
                      "manifest_sha256": sha256(manifest)}))


if __name__ == "__main__":
    main()
