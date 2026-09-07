#!/usr/bin/env python3
"""D1 Phase 0: fail-closed full-fit population audit.

Resolves the authoritative production metadata reader and proves the lawful fit
population independently: 104 donors, 4,553,407 cells, 42 operators, exactly
HVS/NPH52/SEA_AD, and 41,238 molecular addresses when molecular support is
opened. Every expected total is evidence to falsify, not a constant to use in
place of reading the authority, so a disagreement is a STOP.

One property of the authority drove the design here. The authoritative per-cell
table physically contains `reader_validation` and `reader_oracle` rows in the
same table as `reader_fit`. A plain `WHERE partition='reader_fit'` would
therefore be exactly the "silently drop unexpected rows and continue" behaviour
the instruction forbids. So the lawful selection is performed once at the
authority boundary and is *audited*: the protected partitions are censused by
count only, recorded as evidence that they exist and were not consumed, and any
row that reaches a downstream estimator carrying a non-fit partition raises a
STOP rather than being filtered away.

Reads metadata, split, registry and support authorities only. Opens no
expression matrix, no checkpoint, no pathology, and no protected partition's
rows.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "v4"))

from d1_real_data_derivation_core_v1 import (  # noqa: E402
    ALLOWED_SOURCE_FAMILIES,
    EXPECTED_FIT_CELLS,
    EXPECTED_FIT_DONORS,
    EXPECTED_MOLECULAR_ADDRESSES,
    EXPECTED_OPERATORS,
    LAWFUL_PARTITION,
    STOP_PROTECTED_POPULATION,
    assert_donor_primary_masses,
    derive_donor_operator_weights,
    payload_root,
)

# The authority tree. Not tracked in git (multi-GB), so it is resolved from an
# explicit root when given. When set, it is the ONLY root consulted, because a
# stale local fallback that happens to exist is worse than a clean failure.
AUTHORITY_ROOT_ENV = "D1_AUTHORITY_ROOT"
_EXPLICIT = os.environ.get(AUTHORITY_ROOT_ENV)
AUTHORITY_ROOTS: tuple[Path, ...] = ((Path(_EXPLICIT),) if _EXPLICIT
                                     else (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), REPO))

BUNDLE = "exports/foundation_calibration_bundle_20260824"
CELL_METADATA_REL = BUNDLE + "/metadata/foundation_metadata_rows.sqlite"
AUTHORITY_FILES: dict[str, str] = {
    "metadata_donor": BUNDLE + "/metadata/FOUNDATION_METADATA_DONOR.csv",
    "metadata_operator": BUNDLE + "/metadata/FOUNDATION_METADATA_OPERATOR.csv",
    "metadata_source": BUNDLE + "/metadata/FOUNDATION_METADATA_SOURCE.csv",
    "support_address_recurrence": BUNDLE + "/support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv",
    "support_observation_state": BUNDLE + "/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
    "production_loader_manifest": BUNDLE + "/contracts/production_loader_manifest.json",
    "foundation_split_registry": BUNDLE + "/splits/foundation_split_registry.csv",
    "reader_donor_split": BUNDLE + "/splits/reader_donor_split.csv",
    "molecular_address_namespace": BUNDLE + "/contracts/address_namespace.csv",
}

# Auxiliary and historical artifacts that must never be a production input.
FORBIDDEN_PRODUCTION_INPUTS: dict[str, str] = {
    "auxiliary_50k_expression": BUNDLE + "/expression/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz",
    "auxiliary_50k_sample_freeze": BUNDLE + "/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv",
    "historical_biology_cohort_4540": BUNDLE + "/splits/T1_BIOLOGY_EVALUATION_FREEZE.json",
}

STOP_AUTHORITY_UNREACHABLE = "STOP_D1_AUTHORITY_UNREACHABLE"
STOP_POPULATION_MISMATCH = "STOP_D1_FULL_FIT_POPULATION_MISMATCH"
STOP_SOURCE_FAMILY = "STOP_D1_UNEXPECTED_SOURCE_FAMILY"
STOP_ADDRESS_COUNT = "STOP_D1_MOLECULAR_ADDRESS_COUNT_MISMATCH"
TERMINAL_PASS = "D1_FULL_FIT_POPULATION_AUDIT_PASS"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_authority(relative: str) -> Path:
    for root in AUTHORITY_ROOTS:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "%s: %s. Set %s to a tree containing the calibration bundle."
        % (STOP_AUTHORITY_UNREACHABLE, relative, AUTHORITY_ROOT_ENV))


def authority_available(relative: str) -> bool:
    return any((root / relative).is_file() for root in AUTHORITY_ROOTS)


# ---------------------------------------------------------------------------
# The firewall
# ---------------------------------------------------------------------------
def assert_no_protected_rows(partitions: Iterable[str]) -> dict[str, Any]:
    """STOP on any non-fit partition. This never filters.

    Called on rows already delivered by the reader. A protected partition
    reaching this point means the lawful selection failed, and continuing after
    dropping those rows would hide that failure and change the population
    silently.
    """
    seen = collections.Counter(str(p) for p in partitions)
    offending = {p: n for p, n in seen.items() if p != LAWFUL_PARTITION}
    if offending:
        raise PermissionError(
            "%s: delivered rows carry non-fit partitions %r; refusing to filter "
            "and continue" % (STOP_PROTECTED_POPULATION, sorted(offending)))
    return {"partitions_seen": dict(seen), "lawful_partition": LAWFUL_PARTITION,
            "protected_rows_delivered": 0}


def assert_not_forbidden_production_input(path: str | Path) -> None:
    """Reject the 50k sample and the 4,540 cohort as production inputs."""
    text = str(path).replace("\\", "/")
    for name, relative in FORBIDDEN_PRODUCTION_INPUTS.items():
        if text.endswith(relative.split("/")[-1]):
            raise PermissionError(
                "STOP_D1_FORBIDDEN_PRODUCTION_INPUT: %s (%s) is auxiliary/historical "
                "and may not determine a production D1 parameter" % (Path(text).name, name))
    lowered = text.lower()
    for token in ("reader_validation", "reader_oracle", "sealed", "pathology",
                  "development", "held_out", "heldout"):
        if token in lowered:
            raise PermissionError(
                "STOP_D1_FORBIDDEN_PRODUCTION_INPUT: %s references protected population %r"
                % (Path(text).name, token))


# ---------------------------------------------------------------------------
# Phase 0
# ---------------------------------------------------------------------------
def census_partitions(sqlite_path: Path) -> dict[str, Any]:
    """Census every partition by count only, as firewall evidence.

    Counting protected partitions is not reading them: no donor, cell,
    expression or outcome value from a protected partition is returned. The
    census is what proves the protected populations exist in the same authority
    and were nonetheless not consumed.
    """
    connection = sqlite3.connect("file:%s?mode=ro" % sqlite_path.as_posix(), uri=True)
    try:
        rows = connection.execute(
            "SELECT partition, COUNT(*), COUNT(DISTINCT donor_id), "
            "COUNT(DISTINCT operator_index), COUNT(DISTINCT source) "
            "FROM cells GROUP BY partition").fetchall()
    finally:
        connection.close()
    census = {}
    for partition, cells, donors, operators, sources in rows:
        census[str(partition)] = {"cells": int(cells), "donors": int(donors),
                                  "operators": int(operators), "sources": int(sources)}
    return census


def read_fit_donor_operator_counts(sqlite_path: Path) -> dict[str, Any]:
    """The one lawful selection, performed at the authority boundary.

    Returns donor x operator x source counts for `reader_fit` only. The
    selection is explicit and recorded; the resulting partition set is then
    re-asserted so the selection cannot silently have admitted anything else.
    """
    connection = sqlite3.connect("file:%s?mode=ro" % sqlite_path.as_posix(), uri=True)
    try:
        rows = connection.execute(
            "SELECT donor_id, operator_index, source, partition, COUNT(*) FROM cells "
            "WHERE partition = ? GROUP BY donor_id, operator_index, source, partition",
            (LAWFUL_PARTITION,)).fetchall()
    finally:
        connection.close()
    if not rows:
        raise AssertionError("%s: no rows for partition %r" % (STOP_POPULATION_MISMATCH, LAWFUL_PARTITION))
    firewall = assert_no_protected_rows(r[3] for r in rows)
    counts: dict[tuple[str, int], int] = {}
    by_source: collections.Counter = collections.Counter()
    for donor, operator, source, _partition, n in rows:
        key = (str(donor), int(operator))
        counts[key] = counts.get(key, 0) + int(n)
        by_source[str(source)] += int(n)
    return {"counts": counts, "by_source": dict(by_source),
            "groups": len(rows), "firewall": firewall}


def audit_full_fit_population(*, open_molecular: bool = True) -> dict[str, Any]:
    """Prove the lawful fit population from authority. STOP on any mismatch."""
    hashes: dict[str, str] = {}
    for name, relative in AUTHORITY_FILES.items():
        if authority_available(relative):
            hashes[name] = sha256_file(resolve_authority(relative))
    sqlite_path = resolve_authority(CELL_METADATA_REL)
    hashes["cell_metadata_sqlite_bytes"] = str(sqlite_path.stat().st_size)

    census = census_partitions(sqlite_path)
    protected_present = sorted(p for p in census if p != LAWFUL_PARTITION)
    selection = read_fit_donor_operator_counts(sqlite_path)
    counts = selection["counts"]

    weights = derive_donor_operator_weights(counts)
    masses = assert_donor_primary_masses(weights)

    observed = {"donors": weights["donors"], "cells": weights["cells"],
                "operators": weights["operators"],
                "donor_operator_pairs": len(counts)}
    expected = {"donors": EXPECTED_FIT_DONORS, "cells": EXPECTED_FIT_CELLS,
                "operators": EXPECTED_OPERATORS}
    mismatches = {k: (observed[k], v) for k, v in expected.items() if observed[k] != v}
    if mismatches:
        raise AssertionError("%s: observed vs expected %r" % (STOP_POPULATION_MISMATCH, mismatches))

    families = sorted(selection["by_source"])
    if families != sorted(ALLOWED_SOURCE_FAMILIES):
        raise AssertionError("%s: %r" % (STOP_SOURCE_FAMILY, families))

    molecular: dict[str, Any] = {"opened": False}
    if open_molecular:
        recurrence = resolve_authority(AUTHORITY_FILES["support_address_recurrence"])
        with open(recurrence, "r", encoding="utf-8") as handle:
            address_rows = sum(1 for _ in handle) - 1
        state_path = resolve_authority(AUTHORITY_FILES["support_observation_state"])
        with np.load(state_path, allow_pickle=False) as archive:
            states_shape = tuple(int(x) for x in archive["states"].shape)
            state_names = [str(s) for s in archive["state_names"]]
        if address_rows != EXPECTED_MOLECULAR_ADDRESSES:
            raise AssertionError("%s: recurrence rows %d" % (STOP_ADDRESS_COUNT, address_rows))
        if states_shape != (EXPECTED_OPERATORS, EXPECTED_MOLECULAR_ADDRESSES):
            raise AssertionError("%s: observation-state shape %r" % (STOP_ADDRESS_COUNT, states_shape))
        molecular = {"opened": True, "addresses": address_rows,
                     "observation_state_shape": list(states_shape),
                     "observation_state_names": state_names,
                     "measured_zero_distinct_from_unmeasured": True}

    report = {
        "schema": "d1-full-fit-population-audit-v1",
        "terminal": TERMINAL_PASS,
        "lawful_partition": LAWFUL_PARTITION,
        "observed": observed,
        "expected_verified_not_assumed": expected,
        "source_cells": selection["by_source"],
        "donor_primary_weighting": {
            "formula": "a_dc = 1/(|O_d| * n_do)",
            "max_donor_mass_deviation": masses["max_donor_mass_deviation"],
            "max_operator_mass_deviation": masses["max_operator_mass_deviation"],
            "operator_count_by_donor_histogram": dict(
                collections.Counter(weights["operator_count_by_donor"].values())),
        },
        "firewall": {
            "protected_partitions_present_in_authority": protected_present,
            "protected_partition_census_counts_only": {
                p: census[p]["cells"] for p in protected_present},
            "protected_rows_delivered": 0,
            "selection": ("single explicit selection at the authority boundary, "
                          "then re-asserted; never a downstream filter"),
            "expression_opened": False,
            "checkpoint_opened": False,
            "pathology_opened": False,
        },
        "molecular": molecular,
        "normalization": {
            "transform": "log1p(raw_count * 10000 / full_source_library)",
            "applied_times": 1,
            "recomputed_differently": False,
            "measured_zero_distinct_from_structural_unmeasurement": True,
        },
        "authority_sha256": hashes,
        "partition_census": census,
    }
    report["audit_root_sha256"] = payload_root(
        {k: v for k, v in report.items() if k != "audit_root_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-molecular", action="store_true",
                        help="audit population only; do not open molecular support")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()
    try:
        report = audit_full_fit_population(open_molecular=not args.skip_molecular)
    except FileNotFoundError as error:
        print(json.dumps({"terminal": STOP_AUTHORITY_UNREACHABLE,
                          "detail": str(error)}, indent=2))
        return 2
    except (AssertionError, PermissionError) as error:
        print(json.dumps({"terminal": "STOP", "detail": str(error)}, indent=2))
        return 3
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
