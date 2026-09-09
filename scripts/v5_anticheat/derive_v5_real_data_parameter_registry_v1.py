#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sqlite3
import zipfile
from pathlib import Path

import numpy as np

SUPPORT_MEMBER = (
    "FOUNDATION_CALIBRATION_BUNDLE_20260824/"
    "foundation_calibration_bundle_20260824/support/"
    "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def derive(
    *,
    metadata_sqlite: Path,
    expected_metadata_sha256: str,
    calibration_zip: Path,
    expected_calibration_sha256: str,
    expected_support_member_sha256: str,
    partition: str,
    max_folds: int,
    min_donors_per_source_per_fold: int,
    diagnostic_group_floor: int,
) -> dict:
    meta_sha = sha256_file(metadata_sqlite)
    cal_sha = sha256_file(calibration_zip)
    if meta_sha != expected_metadata_sha256:
        raise RuntimeError("metadata SHA mismatch")
    if cal_sha != expected_calibration_sha256:
        raise RuntimeError("calibration bundle SHA mismatch")

    con = sqlite3.connect(f"file:{metadata_sqlite}?mode=ro&immutable=1", uri=True)
    cur = con.cursor()
    cells = int(cur.execute(
        "select count(*) from cells where partition=?", (partition,)
    ).fetchone()[0])
    donors = int(cur.execute(
        "select count(distinct donor_id) from cells where partition=?", (partition,)
    ).fetchone()[0])
    operators = int(cur.execute(
        "select count(distinct operator_index) from cells where partition=?", (partition,)
    ).fetchone()[0])
    sources = int(cur.execute(
        "select count(distinct source) from cells where partition=?", (partition,)
    ).fetchone()[0])
    group_rows = cur.execute(
        "select donor_id,operator_index,source,count(*) from cells "
        "where partition=? group by donor_id,operator_index,source",
        (partition,),
    ).fetchall()
    donor_rows = cur.execute(
        "select donor_id,source,count(*) from cells where partition=? "
        "group by donor_id,source",
        (partition,),
    ).fetchall()
    con.close()

    by_donor = {}
    for donor, source, n in donor_rows:
        donor = str(donor)
        if donor in by_donor:
            raise RuntimeError(f"donor appears in multiple sources: {donor}")
        by_donor[donor] = (str(source), int(n))

    source_donors = {}
    source_cells = {}
    for source, n in by_donor.values():
        source_donors[source] = source_donors.get(source, 0) + 1
        source_cells[source] = source_cells.get(source, 0) + n

    minimum_donor = min(by_donor.items(), key=lambda x: x[1][1])
    maximum_donor = max(by_donor.items(), key=lambda x: x[1][1])
    group_sizes = [int(row[3]) for row in group_rows]

    if max_folds < 1 or min_donors_per_source_per_fold < 1:
        raise ValueError("fold controls must be positive")
    if diagnostic_group_floor < 1:
        raise ValueError("diagnostic_group_floor must be positive")
    outer_folds = min(
        max_folds,
        min(n // min_donors_per_source_per_fold for n in source_donors.values()),
    )
    if outer_folds < 2:
        raise RuntimeError("cannot derive >=2 source-stratified donor folds")

    with zipfile.ZipFile(calibration_zip) as archive:
        support_bytes = archive.read(SUPPORT_MEMBER)
    support_sha = hashlib.sha256(support_bytes).hexdigest()
    if support_sha != expected_support_member_sha256:
        raise RuntimeError("support member SHA mismatch")
    data = np.load(io.BytesIO(support_bytes))
    states = np.asarray(data["states"], dtype=np.uint8)
    if states.shape[0] != operators:
        raise RuntimeError("support/operator count mismatch")
    measured = states == 1
    common = np.where(measured.all(axis=0))[0]
    per_operator = measured.sum(axis=1).astype(int)

    return {
        "schema": "JEPA_V5_REAL_DATA_PARAMETER_REGISTRY_V1",
        "status": (
            "DERIVED_FROM_AUTHENTICATED_REAL_READER_FIT_AND_CALIBRATION_ASSETS"
            "__NO_TRAINING_AUTHORITY"
        ),
        "inputs": {
            "metadata_sqlite_sha256": meta_sha,
            "calibration_bundle_sha256": cal_sha,
            "support_member_sha256": support_sha,
            "partition": partition,
            "synthetic_data_used": False,
            "pathology_used": False,
            "checkpoint_outcomes_used": False,
        },
        "population_geometry": {
            "cells": cells,
            "donors": donors,
            "operators": operators,
            "sources": sources,
            "donor_operator_source_groups": len(group_rows),
            "minimum_donor": {
                "donor_id": minimum_donor[0],
                "source": minimum_donor[1][0],
                "cells": minimum_donor[1][1],
            },
            "maximum_donor": {
                "donor_id": maximum_donor[0],
                "source": maximum_donor[1][0],
                "cells": maximum_donor[1][1],
            },
            "minimum_group_cells": min(group_sizes),
            "maximum_group_cells": max(group_sizes),
            "groups_below_diagnostic_floor": {
                "floor": diagnostic_group_floor,
                "groups": sum(x < diagnostic_group_floor for x in group_sizes),
                "role": "diagnostic only; does not create schedule or training authority",
            },
            "source_cells": dict(sorted(source_cells.items())),
            "source_donors": dict(sorted(source_donors.items())),
        },
        "donor_equal_estimand": {
            "source_weights_from_fit_donor_composition": {
                source: {
                    "numerator": n,
                    "denominator": donors,
                    "float": n / donors,
                }
                for source, n in sorted(source_donors.items())
            },
            "per_cell_target_probability_rule": (
                "p_i = 1 / (n_fit_donors * n_cells_in_donor_i)"
            ),
        },
        "donor_folds": {
            "derivation_rule": (
                "largest K <= max_folds with at least "
                "min_donors_per_source_per_fold donors from every source in every fold"
            ),
            "max_folds": max_folds,
            "min_donors_per_source_per_fold": min_donors_per_source_per_fold,
            "derived_outer_folds": outer_folds,
        },
        "measurement_support_geometry": {
            "molecular_addresses": int(states.shape[1]),
            "common_measured_all_operators": int(len(common)),
            "measured_addresses_per_operator_min": int(per_operator.min()),
            "measured_addresses_per_operator_median": float(np.median(per_operator)),
            "measured_addresses_per_operator_max": int(per_operator.max()),
            "common_core_index_raw_i4_sha256": hashlib.sha256(
                common.astype("<i4").tobytes()
            ).hexdigest(),
            "common_core_hash_semantics_note": (
                "Raw index-vector digest is not a substitute for the canonical "
                "CSV byte digest."
            ),
        },
        "dimension_authority_state": {
            "D_shared": (
                "UNRESOLVED__MUST_BE_DERIVED_FROM_FULL_REAL_READER_FIT_EXPRESSION"
            ),
            "D_private": (
                "UNRESOLVED__ONLY_AFTER_D_SHARED_FREEZE__ZERO_IS_LAWFUL"
            ),
            "D_total": "UNRESOLVED__D_SHARED_PLUS_D_PRIVATE",
            "D_obs": "UNRESOLVED__SEPARATE_OBSERVATION_CHANNEL_RANK",
            "d_gene": (
                "ARCHITECTURE_CAPACITY_PARAMETER__NOT_BIOLOGICAL_DIMENSION_AUTHORITY"
            ),
            "candidate_search_rank": (
                "SEARCH_ENVELOPE_ONLY__BOUNDARY_HIT_REQUIRES_PROSPECTIVE_EXPANSION"
                "_NOT_SELECTION"
            ),
        },
        "training_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--metadata-sqlite", type=Path, required=True)
    p.add_argument("--expected-metadata-sha256", required=True)
    p.add_argument("--calibration-zip", type=Path, required=True)
    p.add_argument("--expected-calibration-sha256", required=True)
    p.add_argument("--expected-support-member-sha256", required=True)
    p.add_argument("--partition", required=True)
    p.add_argument("--max-folds", type=int, required=True)
    p.add_argument("--min-donors-per-source-per-fold", type=int, required=True)
    p.add_argument("--diagnostic-group-floor", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = derive(
        metadata_sqlite=a.metadata_sqlite,
        expected_metadata_sha256=a.expected_metadata_sha256,
        calibration_zip=a.calibration_zip,
        expected_calibration_sha256=a.expected_calibration_sha256,
        expected_support_member_sha256=a.expected_support_member_sha256,
        partition=a.partition,
        max_folds=a.max_folds,
        min_donors_per_source_per_fold=a.min_donors_per_source_per_fold,
        diagnostic_group_floor=a.diagnostic_group_floor,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
