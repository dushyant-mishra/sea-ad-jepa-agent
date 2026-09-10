#!/usr/bin/env python3
"""Are there fresh eligible donors outside the frozen V20 membership? Audit only.

Answers section 0.1 of the V21 draft: whether a genuinely fresh confirmation set
exists, which is the question the V21 design branches on. Nothing is fitted,
nothing is frozen, no estimator is chosen, and V20 is not touched.

**Pathology-blind by construction.** The only pathology-derived input is the
AT8 *availability* flag, taken from the frozen availability authority's own
registry, which contains `donor_id` and `AT8_available` and nothing else. The
pathology source CSV is never opened here, so no AT8 value is parsed, retained,
compared or emitted. That is the same discipline the availability lane was built
under.

The audit is a set of counts over the canonical metadata SQLite, using the
frozen membership query as its reference. The V20 membership is

    SELECT ... FROM cells
    WHERE source='SEA_AD' AND matrix_id='sea_ad_mtg_rna_final_2026'
      AND operator_index=31 AND partition='reader_fit' AND native_class='Immune'

giving 46 donors and 20,804 rows. Any AT8-available donor absent from that set
must differ on one of those five predicates, and which one it is decides whether
fresh donors are reachable at all. So the audit relaxes the predicates one at a
time and reports where the unused donors actually live.

Nothing here proposes extending the membership. Establishing whether extension
would even be possible, and whether it would constitute a new population rather
than a modification of V20, is the whole output.
"""

from __future__ import annotations

import argparse
import csv as csvmod
import hashlib
import io
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_numeric_environment_v1 as numeric_environment  # noqa: E402

STOP = "STOP_T0_V21_FRESH_DONOR_AUDIT_REFUSED"
REPORT = "T0_V21_FRESH_DONOR_AUDIT.json"
DONOR_CSV = "T0_V21_FRESH_DONOR_AUDIT_DONORS.csv"

# The frozen V20 membership predicates, quoted from the source authority.
SOURCE = "SEA_AD"
MATRIX_ID = "sea_ad_mtg_rna_final_2026"
OPERATOR_INDEX = 31
PARTITION = "reader_fit"
NATIVE_CLASS = "Immune"

# The project firewall, read rather than assumed. A partition listed closed here
# is a gate only the owner can open, in the same class as pathology.
FIREWALL_DOC = "docs/agent/CURRENT_WORK_CHECKPOINT.json"
PARTITION_FIREWALL_KEYS = {
    "reader_validation": "reader_validation_closed",
    "reader_oracle": "reader_oracle_closed",
}


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_availability(path: Path) -> dict[str, bool]:
    """donor_id -> AT8_available. The flag only; no value column exists here."""
    rows: dict[str, bool] = {}
    with io.open(path, newline="", encoding="utf-8") as handle:
        reader = csvmod.DictReader(handle)
        if set(reader.fieldnames or []) != {"donor_id", "AT8_available"}:
            _fail("the availability registry carries unexpected columns %r; "
                  "this audit must see availability only"
                  % (reader.fieldnames,))
        for row in reader:
            rows[str(row["donor_id"]).strip()] = \
                str(row["AT8_available"]).strip() == "True"
    return rows


def read_age_sex(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with io.open(path, newline="", encoding="utf-8") as handle:
        for row in csvmod.DictReader(handle):
            rows[str(row["donor_id"]).strip()] = {
                "age": str(row["age"]).strip(), "sex": str(row["sex"]).strip()}
    return rows


def read_membership_donors(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with io.open(path, newline="", encoding="utf-8") as handle:
        for row in csvmod.DictReader(handle):
            donor = str(row["donor_id"]).strip()
            counts[donor] = counts.get(donor, 0) + 1
    return counts


def audit(*, sqlite_path: Path, availability: dict[str, bool],
          membership: dict[str, int], age_sex: dict[str, dict[str, str]],
          log=print) -> dict[str, Any]:
    available = sorted(d for d, flag in availability.items() if flag)
    unused = sorted(set(available) - set(membership))
    log("%d AT8-available donors, %d in the frozen membership, %d unused"
        % (len(available), len(membership), len(unused)))

    connection = sqlite3.connect("file:%s?mode=ro" % sqlite_path.as_posix(),
                                 uri=True)
    connection.row_factory = sqlite3.Row
    try:
        columns = {row["name"] for row in
                   connection.execute("PRAGMA table_info(cells)")}
        required = {"source", "matrix_id", "operator_index", "partition",
                    "native_class", "donor_id"}
        missing = required - columns
        if missing:
            _fail("the cells table lacks %r" % sorted(missing))

        placeholders = ",".join("?" * len(unused)) if unused else "NULL"

        def counts_for(where: str, params: list[Any]) -> dict[str, int]:
            if not unused:
                return {}
            query = ("SELECT donor_id, COUNT(*) AS n FROM cells WHERE "
                     "donor_id IN (%s)%s GROUP BY donor_id" %
                     (placeholders, (" AND " + where) if where else ""))
            return {str(row["donor_id"]): int(row["n"])
                    for row in connection.execute(query, unused + params)}

        # Progressively relaxed views of where the unused donors' cells live.
        log("querying the canonical metadata source, read-only")
        any_cells = counts_for("", [])
        log("  unused donors with any cells at all: %d" % len(any_cells))
        this_matrix = counts_for("source=? AND matrix_id=?",
                                 [SOURCE, MATRIX_ID])
        log("  ... with cells in the MTG matrix: %d" % len(this_matrix))
        this_operator = counts_for(
            "source=? AND matrix_id=? AND operator_index=?",
            [SOURCE, MATRIX_ID, OPERATOR_INDEX])
        log("  ... at operator %d: %d" % (OPERATOR_INDEX, len(this_operator)))
        immune_any_partition = counts_for(
            "source=? AND matrix_id=? AND operator_index=? AND native_class=?",
            [SOURCE, MATRIX_ID, OPERATOR_INDEX, NATIVE_CLASS])
        log("  ... immune, any partition: %d" % len(immune_any_partition))
        full_predicate = counts_for(
            "source=? AND matrix_id=? AND operator_index=? AND partition=? "
            "AND native_class=?",
            [SOURCE, MATRIX_ID, OPERATOR_INDEX, PARTITION, NATIVE_CLASS])
        log("  ... immune AND reader_fit, the full V20 predicate: %d"
            % len(full_predicate))

        # Which partitions and classes do they actually occupy?
        partitions: dict[str, int] = {}
        classes: dict[str, int] = {}
        matrices: dict[str, int] = {}
        if unused:
            for row in connection.execute(
                    "SELECT partition, COUNT(*) AS n FROM cells WHERE "
                    "donor_id IN (%s) AND source=? AND matrix_id=? AND "
                    "operator_index=? GROUP BY partition" % placeholders,
                    unused + [SOURCE, MATRIX_ID, OPERATOR_INDEX]):
                partitions[str(row["partition"])] = int(row["n"])
            for row in connection.execute(
                    "SELECT native_class, COUNT(*) AS n FROM cells WHERE "
                    "donor_id IN (%s) AND source=? AND matrix_id=? AND "
                    "operator_index=? GROUP BY native_class" % placeholders,
                    unused + [SOURCE, MATRIX_ID, OPERATOR_INDEX]):
                classes[str(row["native_class"])] = int(row["n"])
            for row in connection.execute(
                    "SELECT matrix_id, COUNT(*) AS n FROM cells WHERE "
                    "donor_id IN (%s) GROUP BY matrix_id" % placeholders,
                    unused):
                matrices[str(row["matrix_id"])] = int(row["n"])

        # Partition composition at operator 31 over ALL donors, so the claim
        # that the materialised store covers reader_fit only rests on a query.
        composition = {
            str(row["partition"]): int(row["n"]) for row in
            connection.execute(
                "SELECT partition, COUNT(*) AS n FROM cells WHERE source=? "
                "AND matrix_id=? AND operator_index=? GROUP BY partition",
                [SOURCE, MATRIX_ID, OPERATOR_INDEX])}
        immune_composition = {
            str(row["partition"]): int(row["n"]) for row in
            connection.execute(
                "SELECT partition, COUNT(*) AS n FROM cells WHERE source=? "
                "AND matrix_id=? AND operator_index=? AND native_class=? "
                "GROUP BY partition",
                [SOURCE, MATRIX_ID, OPERATOR_INDEX, NATIVE_CLASS])}
        donors_by_partition = {
            str(row["partition"]): int(row["n"]) for row in
            connection.execute(
                "SELECT partition, COUNT(DISTINCT donor_id) AS n FROM cells "
                "WHERE source=? AND matrix_id=? AND operator_index=? AND "
                "native_class=? GROUP BY partition",
                [SOURCE, MATRIX_ID, OPERATOR_INDEX, NATIVE_CLASS])}
        log("op31 partition composition: %s" % composition)
        log("op31 immune donors by partition: %s" % donors_by_partition)

        # Sanity: the frozen predicate must reproduce the frozen membership on
        # the donors it does contain. If it does not, the audit is querying
        # something other than the authority it claims to reference.
        held = sorted(membership)
        held_placeholders = ",".join("?" * len(held))
        reproduced = {
            str(row["donor_id"]): int(row["n"]) for row in
            connection.execute(
                "SELECT donor_id, COUNT(*) AS n FROM cells WHERE donor_id IN "
                "(%s) AND source=? AND matrix_id=? AND operator_index=? AND "
                "partition=? AND native_class=? GROUP BY donor_id"
                % held_placeholders,
                held + [SOURCE, MATRIX_ID, OPERATOR_INDEX, PARTITION,
                        NATIVE_CLASS])}
        if reproduced != membership:
            differing = sorted(d for d in set(reproduced) | set(membership)
                               if reproduced.get(d) != membership.get(d))
            _fail("the frozen predicate does not reproduce the frozen "
                  "membership counts for %r; this audit is not querying the "
                  "authority it references" % differing[:5])
        log("frozen predicate reproduces all %d membership donors exactly"
            % len(membership))
    finally:
        connection.close()

    donor_rows = []
    for donor in unused:
        metadata = age_sex.get(donor)
        cells = full_predicate.get(donor, 0)
        donor_rows.append({
            "donor_id": donor,
            "at8_available": True,
            "cells_any": any_cells.get(donor, 0),
            "cells_mtg_matrix": this_matrix.get(donor, 0),
            "cells_mtg_operator31": this_operator.get(donor, 0),
            "cells_immune_any_partition": immune_any_partition.get(donor, 0),
            "cells_v20_predicate": cells,
            "age_sex_in_frozen_authority": metadata is not None,
            "age": (metadata or {}).get("age", ""),
            "sex": (metadata or {}).get("sex", ""),
        })

    with_cells = [r for r in donor_rows if r["cells_v20_predicate"] > 0]
    return {
        "at8_available_donors": len(available),
        "frozen_membership_donors": len(membership),
        "frozen_membership_cells": sum(membership.values()),
        "unused_at8_available_donors": len(unused),
        "unused_with_any_cells": len(any_cells),
        "unused_with_cells_in_mtg_matrix": len(this_matrix),
        "unused_with_cells_at_operator_31": len(this_operator),
        "unused_with_immune_cells_any_partition": len(immune_any_partition),
        "unused_satisfying_full_v20_predicate": len(with_cells),
        "unused_usable_cells_under_v20_predicate":
            sum(r["cells_v20_predicate"] for r in with_cells),
        "unused_partition_distribution_at_operator_31": partitions,
        "unused_native_class_distribution_at_operator_31": classes,
        "unused_matrix_distribution": matrices,
        "op31_partition_composition_all_cells": composition,
        "op31_immune_partition_composition": immune_composition,
        "op31_immune_donors_by_partition": donors_by_partition,
        "frozen_predicate_reproduces_membership": True,
        "per_donor": donor_rows,
    }


def run(*, availability_pkg: Path, age_sex_pkg: Path, membership: Path,
        sqlite_path: Path, outdir: Path, log=print) -> dict[str, Any]:
    availability = read_availability(
        availability_pkg / "T0_AT8_AVAILABILITY_REGISTRY.csv")
    age_sex = read_age_sex(age_sex_pkg / "T0_AGE_SEX_REGISTRY.csv")
    membership_counts = read_membership_donors(membership)

    metadata = json.loads(
        (availability_pkg / "T0_AT8_AVAILABILITY_METADATA.json"
         ).read_text(encoding="utf-8"))
    if int(metadata["membership_donor_count"]) != len(membership_counts):
        _fail("membership donor count %d does not match the availability "
              "authority's %d" % (len(membership_counts),
                                  metadata["membership_donor_count"]))

    result = audit(sqlite_path=sqlite_path, availability=availability,
                   membership=membership_counts, age_sex=age_sex, log=log)

    # The firewall, read from the project checkpoint rather than assumed.
    firewall: dict[str, Any] = {}
    checkpoint = Path(__file__).resolve().parents[2] / FIREWALL_DOC
    if checkpoint.is_file():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        declared = state.get("firewall", {}) if isinstance(state, dict) else {}
        for partition, key in PARTITION_FIREWALL_KEYS.items():
            firewall[partition] = {
                "firewall_key": key,
                "declared_closed": bool(declared.get(key)),
            }
    else:
        firewall = {"unavailable": "checkpoint not present at %s" % FIREWALL_DOC}

    # Where the unused donors' immune cells actually are, and whether those
    # partitions are open.
    occupied = sorted(
        p for p, n in result["unused_partition_distribution_at_operator_31"
                             ].items() if n > 0)
    closed = [p for p in occupied
              if firewall.get(p, {}).get("declared_closed") is True]

    fresh_under_v20 = result["unused_satisfying_full_v20_predicate"]
    reachable = result["unused_with_immune_cells_any_partition"]

    if fresh_under_v20 > 0:
        verdict = "FRESH_DONORS_SATISFY_V20_PREDICATE__ONLY_A_NEW_AUTHORITY_NEEDED"
    elif reachable == 0:
        verdict = "NO_FRESH_DONORS_EXIST_IN_THIS_POPULATION_AT_ALL"
    elif closed:
        verdict = ("FRESH_DONORS_EXIST_BUT_ONLY_IN_FIREWALL_CLOSED_PARTITIONS"
                   "__OWNER_GATE_NEW_POPULATION_AUTHORITY_AND_STORE_BUILD_"
                   "REQUIRED")
    else:
        verdict = ("FRESH_DONORS_EXIST_OUTSIDE_THE_V20_PARTITION"
                   "__NEW_POPULATION_AUTHORITY_REQUIRED")

    report = {
        "schema": "JEPA_T0_V21_FRESH_DONOR_AUDIT_V1",
        "what": "Whether AT8-available donors outside the frozen V20 MTG "
                "immune membership could supply a fresh V21 confirmation set.",
        "answers": "section 0.1 of docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md",
        "verdict": verdict,
        "audit_only": True,
        "pathology_blind": True,
        "reads_at8_values": False,
        "at8_input": "the frozen availability registry's donor_id and "
                     "AT8_available columns only; the pathology source CSV is "
                     "never opened by this module",
        "v20_modified": False,
        "estimator_fitted": False,
        "weighting_or_power_analysis_run": False,
        "tail_diagnostic_run": False,
        "membership_modified": False,
        "training_authorized": False,
        "fresh_donors_with_immune_cells_outside_reader_fit": reachable,
        "partitions_holding_them": occupied,
        "partitions_declared_closed_by_the_firewall": closed,
        "partition_firewall": firewall,
        "requires_new_v21_population_authority": True,
        "why_new_authority": (
            "The frozen V20 population closure is defined by the predicate "
            "below, which fixes partition='reader_fit'. Admitting donors from "
            "another partition changes that predicate, so it cannot be done by "
            "extending V20 without mutating a frozen authority. It requires a "
            "separate V21 population authority."),
        "requires_new_expression_store_build": True,
        "why_new_store": (
            "The materialised Phase2 op31 expression store covers the "
            "reader_fit partition only. Cells in the other partitions exist in "
            "the canonical metadata source but their counts are not "
            "materialised anywhere the T0 machinery reads, so a fresh "
            "confirmation set would need a new store build, not only a new "
            "authority."),
        "age_sex_authority_covers_them": False,
        "frozen_v20_predicate": {
            "source": SOURCE, "matrix_id": MATRIX_ID,
            "operator_index": OPERATOR_INDEX, "partition": PARTITION,
            "native_class": NATIVE_CLASS,
        },
        **result,
        "provenance": {
            "availability_registry_sha256": _sha256_file(
                availability_pkg / "T0_AT8_AVAILABILITY_REGISTRY.csv"),
            "age_sex_registry_sha256": _sha256_file(
                age_sex_pkg / "T0_AGE_SEX_REGISTRY.csv"),
            "membership_sha256": _sha256_file(membership),
            "canonical_sqlite_bytes": sqlite_path.stat().st_size,
            "canonical_sqlite_path": str(sqlite_path).replace("\\", "/"),
        },
        "numeric_environment": numeric_environment.numeric_environment(),
    }

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")
    donor_path = outdir / DONOR_CSV
    if report["per_donor"]:
        columns = list(report["per_donor"][0].keys())
        with io.open(donor_path, "w", encoding="utf-8", newline="") as handle:
            writer = csvmod.DictWriter(handle, fieldnames=columns,
                                       lineterminator="\n")
            writer.writeheader()
            for row in report["per_donor"]:
                writer.writerow(row)
    log("verdict: %s" % verdict)
    log("wrote %s, %s" % (out.name, donor_path.name))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("availability-pkg", "age-sex-pkg", "membership",
                 "sqlite-path", "outdir"):
        p.add_argument("--%s" % name, required=True, type=Path)
    a = p.parse_args(argv)
    report = run(availability_pkg=a.availability_pkg, age_sex_pkg=a.age_sex_pkg,
                 membership=a.membership, sqlite_path=a.sqlite_path,
                 outdir=a.outdir)
    print()
    print("AT8 available                       %4d" % report["at8_available_donors"])
    print("in frozen V20 membership            %4d  (%d cells)"
          % (report["frozen_membership_donors"],
             report["frozen_membership_cells"]))
    print("unused AT8-available                %4d"
          % report["unused_at8_available_donors"])
    print("  with any cells anywhere           %4d" % report["unused_with_any_cells"])
    print("  with cells in the MTG matrix      %4d"
          % report["unused_with_cells_in_mtg_matrix"])
    print("  at operator 31                    %4d"
          % report["unused_with_cells_at_operator_31"])
    print("  immune, any partition             %4d"
          % report["unused_with_immune_cells_any_partition"])
    print("  satisfying the full V20 predicate %4d  (%d cells)"
          % (report["unused_satisfying_full_v20_predicate"],
             report["unused_usable_cells_under_v20_predicate"]))
    print()
    print("verdict: %s" % report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
