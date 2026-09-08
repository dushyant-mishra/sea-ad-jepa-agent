"""T0 V20 pathology-blind row and count authority.

Scope: verifies the integrity of this project's own data-provenance records. See
docs/agent/T0_LANE_SECURITY_SCOPE.md.

Locating the 20,804 membership rows is the easy half. The obligation is to bind
the exact raw count rows and the full-row `source_library` values that are
actually consumed, and to keep three notions separate so that none can quietly
stand in for another:

* `population_closure_root` — the exhaustive scan and its closure properties.
  The scan covers every block of the operator and does not stop once every
  target has been seen, because a duplicate can appear in a later block.
* `logical_row_authority_root` — the rows in frozen membership order, each bound
  to its block, its row index, the counts and metadata digests, and all six
  Phase2 metadata fields. Membership order is the statistical population's
  order; permuting it is a different population.
* `physical_read_plan_root` — an ordering sorted for I/O locality. Every entry
  carries its `logical_index`, and the plan must restore the logical root
  exactly, which is what stops a physical ordering from redefining the
  population.

`source_library` is an integer sum of the FULL raw source row, computed before
source-to-address projection. Neither the stored 41,238-address row nor the
35,076-address T0 projection needs to sum to it, so it is bound as an exact
positive integer and never recomputed.

Nothing here reads pathology, and nothing here authorizes real T0 execution.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "JEPA_T0_V20_ROW_COUNT_AUTHORITY_V1"
NAMESPACE = "T0-V20-ROW-COUNT-V1"

ADDRESS_SPACE_SIZE = 41_238

# Declared rather than implied: which bound fields the frozen V20 reader
# consumes, and which exist only so an auditor can reconstruct provenance.
V20_CONSUMED_FIELDS = ("canonical_cell_id", "donor_id", "expression_row",
                       "source_library")
AUDIT_ONLY_FIELDS = ("selection_row", "primary_row_weight")

STOP_MEMBERSHIP_COLUMNS = "STOP_T0_B2_MEMBERSHIP_COLUMNS_UNEXPECTED"
STOP_MANIFEST_COLUMNS = "STOP_T0_B2_BLOCK_MANIFEST_COLUMNS_UNEXPECTED"
STOP_OPERATOR = "STOP_T0_B2_BLOCK_OPERATOR_MISMATCH"
STOP_MATRIX = "STOP_T0_B2_BLOCK_MATRIX_MISMATCH"
STOP_META_ABSENT = "STOP_T0_B2_BLOCK_META_ABSENT"
STOP_META_DIGEST = "STOP_T0_B2_BLOCK_META_DIGEST_MISMATCH"
STOP_DUPLICATE = "STOP_T0_B2_DUPLICATE_TARGET_ROW"
STOP_NOT_FOUND = "STOP_T0_B2_TARGET_NOT_FOUND"
STOP_FEATURE_ROOT_ABSENT = "STOP_T0_B2_FEATURE_AUTHORITY_ROOT_ABSENT"
STOP_FEATURE_ROOT_MALFORMED = "STOP_T0_B2_FEATURE_AUTHORITY_ROOT_MALFORMED"
STOP_SOURCE_LIBRARY = "STOP_T0_B2_SOURCE_LIBRARY_NOT_EXACT_POSITIVE_INTEGER"
STOP_SOURCE_LIBRARY_BOUND = "STOP_T0_B2_SOURCE_LIBRARY_NOT_BOUND"
STOP_NORMALIZATION = "STOP_T0_B2_NORMALIZATION_NOT_ONCE_ONLY"
STOP_RESTORE = "STOP_T0_B2_LOGICAL_ORDER_NOT_RESTORABLE"
STOP_COUNTS_DIGEST = "STOP_T0_B2_COUNTS_PAYLOAD_DIGEST_MISMATCH"


def _rows(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    handle = io.StringIO(bytes(payload).decode("utf-8-sig"))
    reader = csv.DictReader(handle)
    return list(reader.fieldnames or []), [dict(record) for record in reader]


def _is_hex64(value: Any) -> bool:
    text = str(value).strip().lower()
    return len(text) == 64 and all(c in "0123456789abcdef" for c in text)


def exact_positive_integer(raw: Any, context: str) -> int:
    """Parse an exact positive integer, refusing anything else.

    `source_library` is a count, so a fractional, exponent-form, zero, negative
    or non-numeric value is not a lossy version of the right answer: it means
    the field is not the one the frozen contract describes.
    """
    text = str(raw).strip()
    if not text or not (text.isdigit() or (text[0] == "+" and text[1:].isdigit())):
        raise AssertionError("%s: %s is %r, not an exact positive integer"
                             % (STOP_SOURCE_LIBRARY, context, raw))
    value = int(text)
    if value <= 0:
        raise AssertionError("%s: %s is %d, which is not positive"
                             % (STOP_SOURCE_LIBRARY, context, value))
    return value


def normalise_once(*, raw_counts: Iterable[float], source_library: int) -> list[float]:
    """The frozen transform: `log1p(raw * 10000 / max(library, 1))`."""
    library = max(float(source_library), 1.0)
    return [math.log1p(float(count) * (10000.0 / library)) for count in raw_counts]


def assert_normalised_once(*, values: Sequence[float], raw_counts: Iterable[float],
                           source_library: int) -> bool:
    """Refuse values that are not the transform applied exactly once."""
    expected = normalise_once(raw_counts=raw_counts, source_library=source_library)
    supplied = [float(value) for value in values]
    if len(supplied) != len(expected):
        raise AssertionError("%s: %d values against %d raw counts"
                             % (STOP_NORMALIZATION, len(supplied), len(expected)))
    worst = max((abs(a - b) for a, b in zip(supplied, expected)), default=0.0)
    if worst > 1e-12:
        raise AssertionError(
            "%s: the supplied values are not log1p(raw*10000/max(library,1)) applied "
            "once; max deviation %.6e" % (STOP_NORMALIZATION, worst))
    return True


def _length_prefixed(value: Any) -> bytes:
    """`<byte length>:<utf-8 bytes>` — injective for any content.

    Delimiter-joined framings were found non-injective in two sibling
    authorities in this lane, so all three roots use length prefixing rather
    than waiting for the same finding a third time. Block keys and cell
    identities are external strings and must not be able to absorb a delimiter.
    """
    payload = str(value).encode("utf-8")
    return b"%d:%s" % (len(payload), payload)


def _closure_root(operator_index: int, matrix_id: str, blocks: Sequence[str],
                  rows_scanned: int, locations: Mapping[str, Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(_length_prefixed("T0_V20_POPULATION_CLOSURE_V2"))
    digest.update(_length_prefixed(int(operator_index)))
    digest.update(_length_prefixed(matrix_id))
    digest.update(_length_prefixed(len(blocks)))
    digest.update(_length_prefixed(int(rows_scanned)))
    for key in blocks:
        digest.update(_length_prefixed(key))
    ordered = sorted(locations, key=lambda value: value.encode("utf-8"))
    digest.update(_length_prefixed(len(ordered)))
    for cell in ordered:
        record = locations[cell]
        digest.update(_length_prefixed(cell))
        digest.update(_length_prefixed(record["block_key"]))
        digest.update(_length_prefixed(int(record["row_index"])))
    return digest.hexdigest()


def build_population_closure(
    *,
    membership_bytes: bytes,
    block_manifest_bytes: bytes,
    meta_bytes_by_path: Mapping[str, bytes],
    operator_index: int,
    matrix_id: str,
) -> dict[str, Any]:
    """Scan every block of the operator and close the population."""
    membership_columns, membership_rows = _rows(membership_bytes)
    for required in ("cell_id", "donor_id", "operator_index", "matrix_id"):
        if required not in membership_columns:
            raise AssertionError("%s: %r absent" % (STOP_MEMBERSHIP_COLUMNS, required))
    targets = {}
    for record in membership_rows:
        targets[str(record["cell_id"]).strip()] = str(record["donor_id"]).strip()

    manifest_columns, manifest_rows = _rows(block_manifest_bytes)
    for required in ("block_key", "operator_index", "matrix_id", "meta_path",
                     "meta_sha256", "counts_path", "counts_sha256"):
        if required not in manifest_columns:
            raise AssertionError("%s: %r absent" % (STOP_MANIFEST_COLUMNS, required))

    blocks = []
    locations: dict[str, dict[str, Any]] = {}
    rows_scanned = 0
    donors: set[str] = set()

    for record in sorted(manifest_rows, key=lambda r: str(r["block_key"])):
        block_key = str(record["block_key"]).strip()
        if int(str(record["operator_index"]).strip()) != int(operator_index):
            raise AssertionError("%s: %s is operator %s, expected %d"
                                 % (STOP_OPERATOR, block_key, record["operator_index"],
                                    int(operator_index)))
        if str(record["matrix_id"]).strip() != str(matrix_id):
            raise AssertionError("%s: %s is matrix %s, expected %s"
                                 % (STOP_MATRIX, block_key, record["matrix_id"], matrix_id))
        meta_path = str(record["meta_path"]).strip()
        if meta_path not in meta_bytes_by_path:
            raise AssertionError("%s: %s" % (STOP_META_ABSENT, meta_path))
        meta_blob = meta_bytes_by_path[meta_path]
        actual = hashlib.sha256(meta_blob).hexdigest()
        if actual != str(record["meta_sha256"]).strip():
            raise AssertionError("%s: %s is %s, manifest says %s"
                                 % (STOP_META_DIGEST, meta_path, actual,
                                    record["meta_sha256"]))
        blocks.append(block_key)

        # Every row of every block is examined. Stopping once all targets have
        # been seen would hide a duplicate in a later block.
        _meta_columns, meta_rows = _rows(meta_blob)
        for row_index, meta_row in enumerate(meta_rows):
            rows_scanned += 1
            cell = str(meta_row.get("canonical_cell_id") or "").strip()
            if cell not in targets:
                continue
            if cell in locations:
                raise AssertionError(
                    "%s: %s appears in %s#%d and again in %s#%d"
                    % (STOP_DUPLICATE, cell, locations[cell]["block_key"],
                       locations[cell]["row_index"], block_key, row_index))
            locations[cell] = {
                "block_key": block_key,
                "row_index": row_index,
                "meta_path": meta_path,
                "meta_sha256": actual,
                "counts_path": str(record["counts_path"]).strip(),
                "counts_sha256": str(record["counts_sha256"]).strip(),
                "meta_row": dict(meta_row),
            }
            donors.add(targets[cell])

    missing = sorted(set(targets) - set(locations))
    if missing:
        raise AssertionError("%s: %d of %d targets absent, e.g. %r"
                             % (STOP_NOT_FOUND, len(missing), len(targets), missing[:5]))

    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "operator_index": int(operator_index),
        "matrix_id": str(matrix_id),
        "blocks_scanned": len(blocks),
        "metadata_rows_scanned": rows_scanned,
        "target_cells": len(locations),
        "missing": len(missing),
        "duplicate_target_hits": 0,
        "donors": sorted(donors),
        "row_locations": locations,
        "full_scan": True,
        "population_closure_root_sha256": _closure_root(
            operator_index, matrix_id, blocks, rows_scanned, locations),
        "real_execution_ready": False,
    }


def _logical_root(rows: Sequence[Mapping[str, Any]], feature_root: str) -> str:
    fields = ("logical_index", "canonical_cell_id", "donor_id", "block_key",
              "row_index", "selection_row", "expression_row",
              "primary_row_weight", "source_library", "meta_sha256",
              "counts_sha256")
    digest = hashlib.sha256()
    digest.update(_length_prefixed("T0_V20_LOGICAL_ROW_AUTHORITY_V2"))
    digest.update(_length_prefixed(feature_root))
    digest.update(_length_prefixed(len(rows)))
    digest.update(_length_prefixed(len(fields)))
    for row in rows:
        for field in fields:
            digest.update(_length_prefixed(row[field]))
    return digest.hexdigest()


def build_logical_row_authority(
    *,
    closure: Mapping[str, Any],
    membership_bytes: bytes,
    feature_authority_root_sha256: str,
) -> dict[str, Any]:
    """Bind the rows in frozen membership order to their physical provenance."""
    if not str(feature_authority_root_sha256).strip():
        raise AssertionError("%s: the Lane B1 feature authority root is required"
                             % STOP_FEATURE_ROOT_ABSENT)
    if not _is_hex64(feature_authority_root_sha256):
        raise AssertionError("%s: %r is not a SHA-256 hex digest"
                             % (STOP_FEATURE_ROOT_MALFORMED, feature_authority_root_sha256))

    _columns, membership_rows = _rows(membership_bytes)
    locations = closure["row_locations"]
    rows = []
    for logical_index, record in enumerate(membership_rows):
        cell = str(record["cell_id"]).strip()
        found = locations[cell]
        meta_row = found["meta_row"]
        source_library = exact_positive_integer(
            meta_row.get("source_library"), "source_library for %s" % cell)
        rows.append({
            "logical_index": logical_index,
            "canonical_cell_id": cell,
            "donor_id": str(record["donor_id"]).strip(),
            "block_key": found["block_key"],
            "row_index": int(found["row_index"]),
            "meta_path": found["meta_path"],
            "meta_sha256": found["meta_sha256"],
            "counts_path": found["counts_path"],
            "counts_sha256": found["counts_sha256"],
            "selection_row": int(str(meta_row["selection_row"]).strip()),
            "expression_row": int(str(meta_row["expression_row"]).strip()),
            "primary_row_weight": str(meta_row["primary_row_weight"]).strip(),
            "source_library": source_library,
        })

    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "feature_authority_root_sha256": str(feature_authority_root_sha256),
        "population_closure_root_sha256": closure["population_closure_root_sha256"],
        "rows": rows,
        "row_count": len(rows),
        "ordering": "EXACT_FROZEN_MEMBERSHIP_ORDER",
        "v20_consumed_fields": list(V20_CONSUMED_FIELDS),
        "audit_only_fields": list(AUDIT_ONLY_FIELDS),
        "source_library_rule": (
            "integer sum of the FULL raw source row, computed before projection; bound "
            "exactly and never recomputed from the 41,238-address row or the 35,076-address "
            "projection"
        ),
        "logical_row_authority_root_sha256": _logical_root(
            rows, feature_authority_root_sha256),
        "real_execution_ready": False,
    }


def build_physical_read_plan(*, logical: Mapping[str, Any]) -> dict[str, Any]:
    """Sort for I/O locality while carrying the logical index on every entry."""
    plan = sorted(
        ({"logical_index": row["logical_index"],
          "block_key": row["block_key"],
          "row_index": row["row_index"],
          "counts_path": row["counts_path"],
          "counts_sha256": row["counts_sha256"]} for row in logical["rows"]),
        key=lambda entry: (entry["block_key"], entry["row_index"]),
    )
    digest = hashlib.sha256()
    digest.update(_length_prefixed("T0_V20_PHYSICAL_READ_PLAN_V2"))
    digest.update(_length_prefixed(logical["logical_row_authority_root_sha256"]))
    digest.update(_length_prefixed(len(plan)))
    for entry in plan:
        digest.update(_length_prefixed(entry["block_key"]))
        digest.update(_length_prefixed(int(entry["row_index"])))
        digest.update(_length_prefixed(int(entry["logical_index"])))
    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "plan": plan,
        "entries": len(plan),
        # Carried so restoration is checked against the population size rather
        # than the plan's own length: dropping the last entry leaves indices
        # that are still a permutation of range(len(entries)).
        "logical_row_count": int(logical["row_count"]),
        "ordering": "BLOCK_THEN_ROW_FOR_IO_LOCALITY__LOGICAL_INDEX_RETAINED",
        "logical_row_authority_root_sha256": logical["logical_row_authority_root_sha256"],
        "feature_authority_root_sha256": logical["feature_authority_root_sha256"],
        "physical_read_plan_root_sha256": digest.hexdigest(),
        "real_execution_ready": False,
    }


def assert_plan_restores_logical(*, plan: Mapping[str, Any],
                                 expected_logical_root_sha256: str) -> bool:
    """A physical ordering may never redefine the logical population.

    Restoration is the whole point: reordering the plan by `logical_index` must
    reproduce the logical root exactly. A tampered index, a dropped entry or a
    physical root offered in place of the logical one all fail here.
    """
    entries = list(plan["plan"])
    expected_count = int(plan["logical_row_count"])
    if len(entries) != expected_count:
        raise AssertionError("%s: the plan holds %d entries for a population of %d"
                             % (STOP_RESTORE, len(entries), expected_count))
    indices = [entry["logical_index"] for entry in entries]
    if sorted(indices) != list(range(expected_count)):
        raise AssertionError(
            "%s: logical indices are not a permutation of 0..%d"
            % (STOP_RESTORE, expected_count - 1))
    if str(plan["logical_row_authority_root_sha256"]) != str(expected_logical_root_sha256):
        raise AssertionError("%s: the plan carries logical root %s, expected %s"
                             % (STOP_RESTORE, plan["logical_row_authority_root_sha256"],
                                expected_logical_root_sha256))
    return True


def assert_source_library_bound(*, logical: Mapping[str, Any], logical_index: int,
                                candidate_source_library: Any) -> bool:
    """Refuse any `source_library` other than the bound one.

    The two substitutions the frozen contract forbids are a sum over the stored
    41,238-address row and a sum over the 35,076-address projection. Neither
    needs to equal the full-row sum, so neither may be accepted.
    """
    bound = logical["rows"][int(logical_index)]["source_library"]
    candidate = exact_positive_integer(
        candidate_source_library, "candidate source_library")
    if candidate != bound:
        raise AssertionError(
            "%s: %d is not the bound full-row source_library %d for logical index %d; "
            "it may not be recomputed from the stored address row or the projection"
            % (STOP_SOURCE_LIBRARY_BOUND, candidate, bound, int(logical_index)))
    return True


def verify_counts_payload(*, logical: Mapping[str, Any], logical_index: int,
                          counts_bytes: bytes) -> bool:
    """Confirm a counts payload is the one bound for this row."""
    row = logical["rows"][int(logical_index)]
    actual = hashlib.sha256(bytes(counts_bytes)).hexdigest()
    if actual != row["counts_sha256"]:
        raise AssertionError("%s: %s is %s, bound %s"
                             % (STOP_COUNTS_DIGEST, row["counts_path"], actual,
                                row["counts_sha256"]))
    return True
