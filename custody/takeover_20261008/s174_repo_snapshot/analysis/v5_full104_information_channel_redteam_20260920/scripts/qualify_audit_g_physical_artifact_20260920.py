"""Fail-closed physical qualification for Audit G calibration-cache evidence.

Run this only on a machine that actually holds the FULL104 pass1 and calibration
cache. Hosted CI uses a committed compact evidence fixture and MUST NOT claim
physical access to these Windows-local bytes.

This qualifier:
- authenticates the current pass1 file by SHA-256;
- authenticates the cache files named by the committed cache manifest;
- verifies selection rows, donor codes and per-donor retained counts;
- re-derives equal-donor source shares, cache complexity mean, and low-tail
  retention from the physical arrays;
- compares them with the committed Audit G hosted fixture.

Any missing artifact, hash mismatch, geometry mismatch or evidence disagreement
fails closed. No terminal masking outcome is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

EXPECTED_PASS1_SHA256 = "37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1"
CACHE_ROLE = "CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"required physical artifact missing: {path}")


def verify_named_file(cache_dir: Path, manifest: dict, logical: str, hash_key: str) -> Path:
    name = manifest["file_names"][logical]
    path = cache_dir / name
    require_file(path)
    observed = sha256_file(path)
    expected = str(manifest[hash_key])
    if observed != expected:
        raise ValueError(
            f"cache file hash mismatch for {logical}: observed={observed} expected={expected}"
        )
    return path


def qualify(
    *,
    cache_dir: Path,
    pass1_path: Path,
    cache_manifest_path: Path,
    hosted_fixture_path: Path,
    expected_pass1_sha256: str = EXPECTED_PASS1_SHA256,
) -> dict:
    for p in (pass1_path, cache_manifest_path, hosted_fixture_path):
        require_file(p)
    if not cache_dir.is_dir():
        raise FileNotFoundError(f"required cache directory missing: {cache_dir}")

    pass1_sha = sha256_file(pass1_path)
    if pass1_sha != expected_pass1_sha256:
        raise ValueError(
            f"pass1 SHA mismatch: observed={pass1_sha} expected={expected_pass1_sha256}"
        )

    manifest = json.loads(cache_manifest_path.read_text(encoding="utf-8"))
    fixture = json.loads(hosted_fixture_path.read_text(encoding="utf-8"))
    if manifest["cache_role_id"] != CACHE_ROLE or fixture["cache_role"] != CACHE_ROLE:
        raise ValueError("cache role mismatch")
    if manifest["max_rows_per_donor"] != fixture["per_donor_cap"]:
        raise ValueError("per-donor cap mismatch between manifest and hosted fixture")

    selection_path = verify_named_file(
        cache_dir, manifest, "selection_rows", "selection_rows_file_sha256"
    )
    donor_code_path = verify_named_file(
        cache_dir, manifest, "donor_code", "donor_code_file_sha256"
    )
    retained_path = verify_named_file(
        cache_dir, manifest, "retained_count_by_donor",
        "retained_count_by_donor_file_sha256",
    )

    p1 = np.load(pass1_path, allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"], dtype=np.int64)
    cell_nnz_core = np.asarray(p1["cell_nnz_core"], dtype=np.float64)
    donor_src = np.asarray(p1["donor_src"], dtype=np.int64)

    selection = np.load(selection_path).astype(np.int64, copy=False)
    cache_donor = np.load(donor_code_path).astype(np.int64, copy=False)
    retained = np.load(retained_path).astype(np.int64, copy=False)

    if cell_donor.size != fixture["population_cells"]:
        raise ValueError("population cell count disagrees with hosted fixture")
    if selection.size != fixture["cached_cells"]:
        raise ValueError("cache row count disagrees with hosted fixture")
    if retained.size != fixture["donors"] or donor_src.size != fixture["donors"]:
        raise ValueError("donor count disagrees with hosted fixture")
    if np.unique(selection).size != selection.size:
        raise ValueError("cache selection contains duplicate selection rows")
    if selection.min() < 0 or selection.max() >= cell_donor.size:
        raise ValueError("cache selection row is outside pass1 population")
    if not np.array_equal(cache_donor, cell_donor[selection]):
        raise ValueError("cache donor codes disagree with pass1 at selection rows")

    available_by_donor = np.bincount(cell_donor, minlength=retained.size)
    cap = int(fixture["per_donor_cap"])
    expected_retained = np.minimum(available_by_donor, cap)
    if not np.array_equal(retained, expected_retained):
        bad = np.flatnonzero(retained != expected_retained)
        raise ValueError(
            f"retained counts violate min(available, cap) for donors {bad[:20].tolist()}"
        )

    source_rows = []
    total = float(retained.sum())
    for src_code, row in enumerate(fixture["source_design"]):
        donors = np.flatnonzero(donor_src == src_code)
        observed_rows = int(retained[donors].sum())
        observed_share = observed_rows / total
        source_rows.append({
            "source": row["source"],
            "donors": int(donors.size),
            "observed_rows": observed_rows,
            "observed_share": observed_share,
            "equal_donor_target": float(row["equal_donor_target"]),
        })
        if observed_rows != int(row["observed_rows"]):
            raise ValueError(f"source cache rows disagree for {row['source']}")

    observed_complexity = float(cell_nnz_core[selection].mean())
    expected_complexity = float(
        fixture["complexity"]["equal_donor_expected_mean_core_nonzeros"]
    )
    if abs(
        observed_complexity - float(fixture["complexity"]["observed_cache_mean_core_nonzeros"])
    ) > 1e-9:
        raise ValueError("physical cache complexity mean disagrees with hosted fixture")

    threshold = int(fixture["low_tail"]["threshold_core_nonzeros"])
    observed_low = int((cell_nnz_core[selection] <= threshold).sum())
    if observed_low != int(fixture["low_tail"]["observed_cache_cells"]):
        raise ValueError("physical low-tail count disagrees with hosted fixture")

    result = {
        "schema": "V5_FULL104_AUDIT_G_PHYSICAL_QUALIFICATION_V1",
        "pass1_sha256": pass1_sha,
        "cache_role": CACHE_ROLE,
        "population_cells": int(cell_donor.size),
        "cached_cells": int(selection.size),
        "donors": int(retained.size),
        "donors_at_cap": int((retained == cap).sum()),
        "donors_below_cap": int((retained < cap).sum()),
        "source_geometry": source_rows,
        "observed_cache_mean_core_nonzeros": observed_complexity,
        "equal_donor_expected_mean_core_nonzeros": expected_complexity,
        "relative_complexity_deviation":
            abs(observed_complexity - expected_complexity) / expected_complexity,
        "low_tail_threshold": threshold,
        "low_tail_observed": observed_low,
        "status": "PASS_PHYSICAL_AUDIT_G_EQUAL_DONOR_QUALIFICATION",
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-dir", type=Path, required=True)
    ap.add_argument("--pass1", type=Path, required=True)
    ap.add_argument(
        "--cache-manifest",
        type=Path,
        default=Path(
            "analysis/v5_full104_pass1_rebuild_20260920/evidence/"
            "calibration_cache/cache_manifest.json"
        ),
    )
    ap.add_argument(
        "--hosted-fixture",
        type=Path,
        default=Path(
            "analysis/v5_full104_information_channel_redteam_20260920/evidence/"
            "audit_g/HOSTED_AUDIT_G_EQUAL_DONOR_FIXTURE_V1.json"
        ),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    try:
        result = qualify(
            cache_dir=args.cache_dir,
            pass1_path=args.pass1,
            cache_manifest_path=args.cache_manifest,
            hosted_fixture_path=args.hosted_fixture,
        )
    except Exception as exc:
        print(f"FAIL_PHYSICAL_AUDIT_G: {type(exc).__name__}: {exc}")
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
