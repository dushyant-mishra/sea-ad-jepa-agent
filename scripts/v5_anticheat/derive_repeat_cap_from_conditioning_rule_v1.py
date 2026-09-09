#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
from fractions import Fraction
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def derive(
    *,
    metadata_sqlite: Path,
    expected_metadata_sha256: str,
    partition: str,
    conditioning_ceiling: Fraction,
) -> dict:
    if conditioning_ceiling <= 0:
        raise ValueError("conditioning ceiling must be positive")
    observed = sha256_file(metadata_sqlite)
    if observed.lower() != expected_metadata_sha256.lower():
        raise RuntimeError("STOP_REPEAT_CAP_METADATA_SHA_MISMATCH")

    con = sqlite3.connect(f"file:{metadata_sqlite}?mode=ro&immutable=1", uri=True)
    rows = con.execute(
        "select donor_id,count(*) from cells where partition=? group by donor_id order by donor_id",
        (partition,),
    ).fetchall()
    cells = int(
        con.execute(
            "select count(*) from cells where partition=?", (partition,)
        ).fetchone()[0]
    )
    con.close()
    if not rows or sum(int(n) for _, n in rows) != cells:
        raise RuntimeError("STOP_REPEAT_CAP_DONOR_GEOMETRY_CLOSURE")

    donor_sizes = {str(d): int(n) for d, n in rows}
    nmin = min(donor_sizes.values())
    nmax = max(donor_sizes.values())

    # Full unique-cell coverage forces largest-donor multiplicity >=1.
    # A cap C bounds smallest-donor multiplicity <=C. Therefore the best
    # possible max/min n_d*m_i product ratio is at least nmax/(nmin*C).
    cap = max(
        1,
        math.ceil(
            Fraction(nmax, nmin) / conditioning_ceiling
        ),
    )
    ratio = Fraction(nmax, nmin * cap)
    if ratio > conditioning_ceiling:
        raise RuntimeError("STOP_REPEAT_CAP_BOUNDARY_ARITHMETIC")
    previous = cap - 1
    previous_ratio = (
        Fraction(nmax, nmin * previous) if previous >= 1 else None
    )
    if previous_ratio is not None and previous_ratio <= conditioning_ceiling:
        raise RuntimeError("STOP_REPEAT_CAP_NOT_MINIMAL")

    return {
        "schema": "JEPA_V5_REPEAT_CAP_FROM_CONDITIONING_RULE_V1",
        "status": "REAL_DONOR_GEOMETRY_DERIVATION__NO_REPEAT_CAP_AUTHORITY",
        "inputs": {
            "metadata_sqlite_sha256": observed,
            "partition": partition,
            "conditioning_ceiling": {
                "numerator": conditioning_ceiling.numerator,
                "denominator": conditioning_ceiling.denominator,
                "float": float(conditioning_ceiling),
                "role": "PROSPECTIVELY_SUPPLIED_RISK_CONTROL__NOT_DATA_DISCOVERED",
            },
        },
        "population": {
            "cells": cells,
            "donors": len(donor_sizes),
            "minimum_donor_cells": nmin,
            "maximum_donor_cells": nmax,
        },
        "derived_boundary": {
            "minimum_compatible_cell_repeat_cap": cap,
            "ratio_at_cap": {
                "numerator": ratio.numerator,
                "denominator": ratio.denominator,
                "float": float(ratio),
                "passes": ratio <= conditioning_ceiling,
            },
            "immediately_previous_cap": previous if previous >= 1 else None,
            "ratio_at_previous_cap": (
                {
                    "numerator": previous_ratio.numerator,
                    "denominator": previous_ratio.denominator,
                    "float": float(previous_ratio),
                    "passes": previous_ratio <= conditioning_ceiling,
                }
                if previous_ratio is not None
                else None
            ),
        },
        "proof": "Under full unique-cell coverage, max donor_cells*multiplicity >= n_max and min donor_cells*multiplicity <= n_min*cap, so any schedule has weight-conditioning ratio >= n_max/(n_min*cap). The returned cap is the smallest integer whose lower bound does not exceed the supplied ceiling.",
        "selection_boundary": "This derives a cap only conditional on the supplied conditioning ceiling. It does not justify or freeze that ceiling.",
        "synthetic_data_used_for_numeric_authority": False,
        "checkpoint_outcomes_used": False,
        "pathology_used": False,
        "training_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--metadata-sqlite", type=Path, required=True)
    p.add_argument("--expected-metadata-sha256", required=True)
    p.add_argument("--partition", default="reader_fit")
    p.add_argument("--conditioning-ceiling-numerator", type=int, required=True)
    p.add_argument("--conditioning-ceiling-denominator", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    ceiling = Fraction(
        a.conditioning_ceiling_numerator,
        a.conditioning_ceiling_denominator,
    )
    out = derive(
        metadata_sqlite=a.metadata_sqlite,
        expected_metadata_sha256=a.expected_metadata_sha256,
        partition=a.partition,
        conditioning_ceiling=ceiling,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
