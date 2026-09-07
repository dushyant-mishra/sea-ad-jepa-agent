#!/usr/bin/env python3
"""D1 Phase 0: fail-closed full-fit population audit.

Proves the lawful fit population from authority: exactly the 104 donors named by
the frozen reader split, 4,553,407 cells, 42 operators, 1,400 donor x operator
pairs, exactly HVS/NPH52/SEA_AD at their exact source totals, and 41,238
molecular addresses when molecular support is opened. Every expected total is
evidence to falsify, not a constant to use in place of reading the authority, so
a disagreement is a STOP.

Four properties of this audit exist because earlier revisions of it were too
weak, and each is load bearing:

1. Every controlling authority is MANDATORY and exact-hash checked. An earlier
   revision hashed an authority only `if authority_available(...)`, so a missing
   loader manifest or split registry could simply vanish from the report while
   the audit still returned PASS.
2. The authoritative per-cell SQLite is bound by content digest. An earlier
   revision recorded its byte count inside a dict named `authority_sha256`,
   which is not an identity at all: that file is what establishes the
   4.55-million-cell population.
3. Population IDENTITY is asserted, not just totals. The exact 104 donor
   identifiers must equal the frozen `reader_fit` roster from
   `reader_donor_split.csv`, the per-source totals must match exactly, and the
   donor x operator pair count must be exactly 1,400. Totals alone would admit a
   different 104-donor population that happened to sum correctly.
4. Protected per-cell rows are never queried. An earlier revision censused
   every partition with COUNT(DISTINCT donor_id/operator_index/source), which
   reads protected rows' metadata even though only cell counts were emitted. The
   lawful roster now comes from the donor-level split authority, only
   `reader_fit` per-cell rows are queried, and any delivered non-fit row is a
   STOP rather than a filter.

Normalization is proven from the controlling loader implementation rather than
asserted in the output. Opens no expression matrix, no checkpoint, and no
pathology.
"""

from __future__ import annotations

import argparse
import collections
import csv
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
    load_observation_state_codes,
    payload_root,
    verify_normalization_from_loader_source,
)

AUTHORITY_ROOT_ENV = "D1_AUTHORITY_ROOT"
_EXPLICIT = os.environ.get(AUTHORITY_ROOT_ENV)
AUTHORITY_ROOTS: tuple[Path, ...] = ((Path(_EXPLICIT),) if _EXPLICIT
                                     else (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), REPO))

BUNDLE = "exports/foundation_calibration_bundle_20260824"
CELL_METADATA_REL = BUNDLE + "/metadata/foundation_metadata_rows.sqlite"

# Every controlling authority, with its exact expected digest. All mandatory.
MANDATORY_AUTHORITIES: dict[str, tuple[str, str]] = {
    "cell_metadata_sqlite": (
        CELL_METADATA_REL,
        "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"),
    "reader_donor_split": (
        BUNDLE + "/splits/reader_donor_split.csv",
        "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"),
    "foundation_split_registry": (
        BUNDLE + "/splits/foundation_split_registry.csv",
        "35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433"),
    "production_loader_manifest": (
        BUNDLE + "/contracts/production_loader_manifest.json",
        "2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328"),
    "production_loader_source": (
        BUNDLE + "/code/production_train_loader.py",
        "267fa42a5fa6f8b5f8199c68add1ffe0c8b49142095b7d980d1af27a8a31154a"),
    "molecular_address_namespace": (
        BUNDLE + "/contracts/address_namespace.csv",
        "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"),
    "metadata_donor": (
        BUNDLE + "/metadata/FOUNDATION_METADATA_DONOR.csv",
        "c9cbe47d4727aabec8a0c3fed5474c2dab4f9f2b8848357e08b0cec6ef044508"),
    "metadata_operator": (
        BUNDLE + "/metadata/FOUNDATION_METADATA_OPERATOR.csv",
        "d5ead72b682c0d8ac81e8c8f700d473b8c0a407b077294e41ec616a604078ac6"),
    "metadata_source": (
        BUNDLE + "/metadata/FOUNDATION_METADATA_SOURCE.csv",
        "1e441f1a007c2d50bdce19893738bd0b56300c993a6a49c6188a64f54ddc7bba"),
}

# Mandatory only when molecular support is opened.
MOLECULAR_AUTHORITIES: dict[str, tuple[str, str]] = {
    "support_address_recurrence": (
        BUNDLE + "/support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv",
        "8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da"),
    "support_observation_state": (
        BUNDLE + "/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
        "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"),
}

AUTHORITY_FILES = {name: rel for name, (rel, _) in
                   {**MANDATORY_AUTHORITIES, **MOLECULAR_AUTHORITIES}.items()}

EXPECTED_SOURCE_CELLS = {"HVS": 198718, "NPH52": 236476, "SEA_AD": 4118213}
EXPECTED_DONOR_OPERATOR_PAIRS = 1400

FORBIDDEN_PRODUCTION_INPUTS: dict[str, str] = {
    "auxiliary_50k_expression": BUNDLE + "/expression/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz",
    "auxiliary_50k_sample_freeze": BUNDLE + "/expression/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv",
    "historical_biology_cohort_4540": BUNDLE + "/splits/T1_BIOLOGY_EVALUATION_FREEZE.json",
}

STOP_AUTHORITY_UNREACHABLE = "STOP_D1_AUTHORITY_UNREACHABLE"
STOP_AUTHORITY_DIGEST = "STOP_D1_AUTHORITY_DIGEST_MISMATCH"
STOP_POPULATION_MISMATCH = "STOP_D1_FULL_FIT_POPULATION_MISMATCH"
STOP_ROSTER_MISMATCH = "STOP_D1_FIT_DONOR_ROSTER_MISMATCH"
STOP_SOURCE_FAMILY = "STOP_D1_UNEXPECTED_SOURCE_FAMILY"
STOP_SOURCE_TOTALS = "STOP_D1_SOURCE_CELL_TOTAL_MISMATCH"
STOP_ADDRESS_COUNT = "STOP_D1_MOLECULAR_ADDRESS_COUNT_MISMATCH"
TERMINAL_PASS = "D1_FULL_FIT_POPULATION_AUDIT_PASS"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
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


def verify_mandatory_authorities(*, include_molecular: bool) -> dict[str, str]:
    """Resolve and exact-hash every controlling authority. Missing is a STOP."""
    required = dict(MANDATORY_AUTHORITIES)
    if include_molecular:
        required.update(MOLECULAR_AUTHORITIES)
    observed: dict[str, str] = {}
    for name, (relative, expected) in sorted(required.items()):
        path = resolve_authority(relative)         # raises if absent
        digest = sha256_file(path)
        if digest != expected:
            raise AssertionError(
                "%s: %s (%s) is %s, expected %s"
                % (STOP_AUTHORITY_DIGEST, name, relative, digest, expected))
        observed[name] = digest
    return observed


# ---------------------------------------------------------------------------
# The firewall
# ---------------------------------------------------------------------------
def assert_no_protected_rows(partitions: Iterable[str]) -> dict[str, Any]:
    """STOP on any non-fit partition. This never filters."""
    seen = collections.Counter(str(p) for p in partitions)
    offending = {p: n for p, n in seen.items() if p != LAWFUL_PARTITION}
    if offending:
        raise PermissionError(
            "%s: delivered rows carry non-fit partitions %r; refusing to filter "
            "and continue" % (STOP_PROTECTED_POPULATION, sorted(offending)))
    return {"partitions_seen": dict(seen), "lawful_partition": LAWFUL_PARTITION,
            "protected_rows_delivered": 0}


def assert_not_forbidden_production_input(path: str | Path) -> None:
    """Reject the 50k sample, the 4,540 cohort and protected populations."""
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


def read_frozen_reader_roster(split_path: Path) -> dict[str, Any]:
    """The lawful donor roster, from the donor-level frozen split authority.

    Donor-level split membership is metadata about the split itself, not
    protected per-cell content, so reading it does not open a protected
    population. It is what lets the audit assert population *identity* without
    ever querying a protected row.
    """
    with open(split_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "donor_id" not in rows[0] or "reader_partition" not in rows[0]:
        raise AssertionError("%s: unexpected reader split schema %r"
                             % (STOP_ROSTER_MISMATCH, list(rows[0]) if rows else None))
    by_partition: dict[str, set[str]] = {}
    for row in rows:
        by_partition.setdefault(str(row["reader_partition"]), set()).add(str(row["donor_id"]))
    fit = by_partition.get(LAWFUL_PARTITION, set())
    if len(fit) != EXPECTED_FIT_DONORS:
        raise AssertionError("%s: frozen split declares %d %s donors, expected %d"
                             % (STOP_ROSTER_MISMATCH, len(fit), LAWFUL_PARTITION,
                                EXPECTED_FIT_DONORS))
    return {"fit_roster": fit,
            "declared_partition_donor_counts": {p: len(v) for p, v in sorted(by_partition.items())},
            "roster_sha256": hashlib.sha256(
                "\n".join(sorted(fit)).encode("utf-8")).hexdigest()}


def read_fit_donor_operator_counts(sqlite_path: Path, roster: set[str]) -> dict[str, Any]:
    """Query ONLY reader_fit per-cell rows, then re-assert what was delivered.

    No protected partition is queried at all, not even for a count. The lawful
    selection is bounded by the frozen roster as well as by the partition label,
    so a row whose partition said reader_fit but whose donor is not on the
    roster is still a STOP.
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
        raise AssertionError("%s: no rows for partition %r"
                            % (STOP_POPULATION_MISMATCH, LAWFUL_PARTITION))
    firewall = assert_no_protected_rows(r[3] for r in rows)

    off_roster = sorted({str(r[0]) for r in rows} - roster)
    if off_roster:
        raise PermissionError(
            "%s: %d delivered donors are not on the frozen fit roster, first=%r"
            % (STOP_PROTECTED_POPULATION, len(off_roster), off_roster[0]))

    counts: dict[tuple[str, int], int] = {}
    by_source: collections.Counter = collections.Counter()
    for donor, operator, source, _partition, n in rows:
        key = (str(donor), int(operator))
        counts[key] = counts.get(key, 0) + int(n)
        by_source[str(source)] += int(n)
    return {"counts": counts, "by_source": dict(by_source),
            "groups": len(rows), "firewall": firewall,
            "delivered_donors": sorted({str(r[0]) for r in rows})}


def audit_full_fit_population(*, open_molecular: bool = True) -> dict[str, Any]:
    """Prove the lawful fit population from authority. STOP on any mismatch."""
    hashes = verify_mandatory_authorities(include_molecular=open_molecular)

    split_path = resolve_authority(MANDATORY_AUTHORITIES["reader_donor_split"][0])
    roster = read_frozen_reader_roster(split_path)

    sqlite_path = resolve_authority(CELL_METADATA_REL)
    selection = read_fit_donor_operator_counts(sqlite_path, roster["fit_roster"])
    counts = selection["counts"]

    weights = derive_donor_operator_weights(counts)
    masses = assert_donor_primary_masses(weights)

    observed = {"donors": weights["donors"], "cells": weights["cells"],
                "operators": weights["operators"],
                "donor_operator_pairs": len(counts)}
    expected = {"donors": EXPECTED_FIT_DONORS, "cells": EXPECTED_FIT_CELLS,
                "operators": EXPECTED_OPERATORS,
                "donor_operator_pairs": EXPECTED_DONOR_OPERATOR_PAIRS}
    mismatches = {k: (observed[k], v) for k, v in expected.items() if observed[k] != v}
    if mismatches:
        raise AssertionError("%s: observed vs expected %r"
                            % (STOP_POPULATION_MISMATCH, mismatches))

    # Population IDENTITY, not merely totals.
    delivered = set(selection["delivered_donors"])
    if delivered != roster["fit_roster"]:
        raise AssertionError(
            "%s: delivered donor set differs from the frozen roster; missing=%r extra=%r"
            % (STOP_ROSTER_MISMATCH,
               sorted(roster["fit_roster"] - delivered)[:5],
               sorted(delivered - roster["fit_roster"])[:5]))

    families = sorted(selection["by_source"])
    if families != sorted(ALLOWED_SOURCE_FAMILIES):
        raise AssertionError("%s: %r" % (STOP_SOURCE_FAMILY, families))
    if selection["by_source"] != EXPECTED_SOURCE_CELLS:
        raise AssertionError("%s: observed %r expected %r"
                            % (STOP_SOURCE_TOTALS, selection["by_source"],
                               EXPECTED_SOURCE_CELLS))

    # Normalization proven from the controlling loader implementation.
    loader_path = resolve_authority(MANDATORY_AUTHORITIES["production_loader_source"][0])
    loader_bytes = loader_path.read_bytes()
    normalization = verify_normalization_from_loader_source(
        loader_bytes.decode("utf-8"),
        source_sha256=hashlib.sha256(loader_bytes).hexdigest())

    # The loader manifest independently declares the observation-state codes.
    manifest_path = resolve_authority(MANDATORY_AUTHORITIES["production_loader_manifest"][0])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared_codes = manifest.get("state_codes", {})
    if declared_codes.get("MEASURED_SCALAR") != 1 or declared_codes.get("STRUCTURALLY_UNMEASURED") != 0:
        raise AssertionError("STOP_D1_OBSERVATION_STATE_CODE_MISMATCH: loader manifest declares %r"
                            % (declared_codes,))
    if int(manifest.get("address_count", -1)) != EXPECTED_MOLECULAR_ADDRESSES:
        raise AssertionError("%s: loader manifest address_count %r"
                            % (STOP_ADDRESS_COUNT, manifest.get("address_count")))

    molecular: dict[str, Any] = {"opened": False}
    if open_molecular:
        recurrence = resolve_authority(MOLECULAR_AUTHORITIES["support_address_recurrence"][0])
        with open(recurrence, "r", encoding="utf-8") as handle:
            address_rows = sum(1 for _ in handle) - 1
        state_path = resolve_authority(MOLECULAR_AUTHORITIES["support_observation_state"][0])
        with np.load(state_path, allow_pickle=False) as archive:
            states_shape = tuple(int(x) for x in archive["states"].shape)
            state_names = [str(s) for s in archive["state_names"]]
        codes = load_observation_state_codes(state_names)
        if address_rows != EXPECTED_MOLECULAR_ADDRESSES:
            raise AssertionError("%s: recurrence rows %d" % (STOP_ADDRESS_COUNT, address_rows))
        if states_shape != (EXPECTED_OPERATORS, EXPECTED_MOLECULAR_ADDRESSES):
            raise AssertionError("%s: observation-state shape %r"
                                % (STOP_ADDRESS_COUNT, states_shape))
        molecular = {"opened": True, "addresses": address_rows,
                     "observation_state_shape": list(states_shape),
                     "observation_state_names": state_names,
                     "observation_state_codes": codes,
                     "codes_agree_with_loader_manifest": True,
                     "measured_zero_distinct_from_unmeasured": True}

    report = {
        "schema": "d1-full-fit-population-audit-v1",
        "terminal": TERMINAL_PASS,
        "lawful_partition": LAWFUL_PARTITION,
        "observed": observed,
        "expected_verified_not_assumed": expected,
        "source_cells": selection["by_source"],
        "expected_source_cells": EXPECTED_SOURCE_CELLS,
        "population_identity": {
            "fit_donor_roster_source": MANDATORY_AUTHORITIES["reader_donor_split"][0],
            "fit_roster_sha256": roster["roster_sha256"],
            "delivered_donor_set_equals_frozen_roster": True,
            "declared_partition_donor_counts": roster["declared_partition_donor_counts"],
        },
        "donor_primary_weighting": {
            "formula": "a_dc = 1/(|O_d| * n_do)",
            "max_donor_mass_deviation": masses["max_donor_mass_deviation"],
            "max_operator_mass_deviation": masses["max_operator_mass_deviation"],
            "operator_count_by_donor_histogram": dict(
                collections.Counter(weights["operator_count_by_donor"].values())),
        },
        "firewall": {
            "protected_rows_delivered": 0,
            "lawful_partition": LAWFUL_PARTITION,
            "donor_roster_verified": True,
            "protected_per_cell_rows_queried": False,
            "protected_partition_metadata_queried": False,
            "selection": ("single explicit reader_fit selection bounded by the frozen "
                          "donor roster; protected partitions are never queried, not "
                          "even for a count"),
            "expression_opened": False,
            "checkpoint_opened": False,
            "pathology_opened": False,
        },
        "molecular": molecular,
        "normalization": normalization,
        "authority_sha256": hashes,
        "authority_binding": "every controlling authority is mandatory and exact-hash checked",
    }
    report["audit_root_sha256"] = payload_root(
        {k: v for k, v in report.items() if k != "audit_root_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-molecular", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()
    try:
        report = audit_full_fit_population(open_molecular=not args.skip_molecular)
    except FileNotFoundError as error:
        print(json.dumps({"terminal": STOP_AUTHORITY_UNREACHABLE, "detail": str(error)}, indent=2))
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
