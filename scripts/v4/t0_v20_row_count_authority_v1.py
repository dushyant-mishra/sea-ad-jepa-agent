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

# Width of a raw row in the ORIGINAL MTG H5AD source, before source-to-address
# projection. `source_library` is the integer sum of a row of THIS width, which
# is why an address-space row can never prove it.
SOURCE_FEATURE_COUNT = 36_601

# Frozen identity of the MTG H5AD source asset and the slot the raw counts live
# in. Proving `source_library` means reading a row out of these exact bytes.
MTG_SOURCE_SHA256 = "e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79"
MTG_SOURCE_MATRIX_SLOT = "layers/UMIs"

# Frozen production geometry of the complete Phase2 manifest.
COMPLETE_MANIFEST_BLOCKS = 8_915
COMPLETE_MANIFEST_OPERATORS = 42
OP31_BLOCK_COUNT = 1_247

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
STOP_MANIFEST_GEOMETRY = "STOP_T0_B2_COMPLETE_MANIFEST_GEOMETRY_MISMATCH"
STOP_SOURCE_IDENTITY = "STOP_T0_B2_RAW_SOURCE_ASSET_NOT_AUTHENTICATED"
STOP_SOURCE_SLOT = "STOP_T0_B2_RAW_SOURCE_MATRIX_SLOT_NOT_RAW_UMI"
STOP_SOURCE_ROW_IDENTITY = "STOP_T0_B2_RAW_SOURCE_ROW_IDENTITY_MISMATCH"
STOP_SOURCE_WIDTH = "STOP_T0_B2_RAW_SOURCE_ROW_WIDTH_NOT_SOURCE_FEATURE_SPACE"
STOP_BLOCK_ROW_NOT_BOUND = "STOP_T0_B2_SELECTED_BLOCK_ROW_NOT_BOUND"
STOP_COUNTS_GEOMETRY = "STOP_T0_B2_COUNTS_MATRIX_GEOMETRY_MISMATCH"
STOP_COUNTS_FORMAT = "STOP_T0_B2_COUNTS_PAYLOAD_FORMAT_UNEXPECTED"
STOP_CLOSURE_ROOT = "STOP_T0_B2_POPULATION_CLOSURE_ROOT_MISMATCH"
STOP_PLAN_ROOT = "STOP_T0_B2_PHYSICAL_READ_PLAN_ROOT_MISMATCH"
STOP_PLAN_FIELD = "STOP_T0_B2_PHYSICAL_PLAN_ENTRY_DISAGREES_WITH_LOGICAL_ROW"
STOP_MEMBERSHIP_SPLICE = "STOP_T0_B2_MEMBERSHIP_SPLICED_AFTER_CLOSURE"
STOP_PARENT_IDENTITY = "STOP_T0_B2_PARENT_IDENTITY_NOT_EXTERNALLY_BOUND"
STOP_STORED_ROOT_DISAGREES = "STOP_T0_B2_STORED_ROOT_DISAGREES_WITH_RECOMPUTED_ROOT"
STOP_COUNTS_DIGEST = "STOP_T0_B2_COUNTS_PAYLOAD_DIGEST_MISMATCH"
STOP_FIELD_TYPE = "STOP_T0_B2_AUTHORITY_FIELD_TYPE_NOT_ALLOWED"
STOP_FIELD_SCHEMA = "STOP_T0_B2_AUTHORITY_FIELD_SCHEMA_VIOLATION"
STOP_MEMBERSHIP_DIGEST = "STOP_T0_B2_MEMBERSHIP_DIGEST_MISMATCH"
STOP_MANIFEST_DIGEST = "STOP_T0_B2_BLOCK_MANIFEST_DIGEST_MISMATCH"
STOP_MEMBERSHIP_OPERATOR = "STOP_T0_B2_MEMBERSHIP_OPERATOR_MISMATCH"
STOP_MEMBERSHIP_MATRIX = "STOP_T0_B2_MEMBERSHIP_MATRIX_MISMATCH"
STOP_MEMBERSHIP_UNIQUE = "STOP_T0_B2_MEMBERSHIP_CELL_NOT_UNIQUE"
STOP_DONOR_DISAGREES = "STOP_T0_B2_DONOR_IDENTITY_DISAGREES_WITH_PHASE2_METADATA"
STOP_LIBRARY_NOT_PROVEN = "STOP_T0_B2_SOURCE_LIBRARY_NOT_PROVEN_FROM_RAW_ROW"
STOP_RAW_WIDTH_ADDRESS = "STOP_T0_B2_RAW_ROW_WIDTH_IS_ADDRESS_SPACE"
STOP_RAW_SEMANTICS = "STOP_T0_B2_RAW_COUNTS_NOT_NONNEGATIVE_INTEGERS"
STOP_RAW_PROVENANCE = "STOP_T0_B2_RAW_ROW_PROVENANCE_NOT_BOUND"
STOP_ROW_WIDTH = "STOP_T0_B2_SELECTED_ROW_WIDTH_NOT_ADDRESS_SPACE"
STOP_ROW_SEMANTICS = "STOP_T0_B2_SELECTED_ROW_COUNTS_NOT_NONNEGATIVE_INTEGERS"
STOP_ROW_NOT_BOUND = "STOP_T0_B2_SELECTED_ROW_NOT_BOUND"
STOP_ROW_BOUNDS = "STOP_T0_B2_EXPRESSION_ROW_OUT_OF_BOUNDS"
STOP_CALLER_VALUES = "STOP_T0_B2_CALLER_SUPPLIED_RAW_SOURCE_VALUES_REFUSED"


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


def _typed(value: Any) -> bytes:
    """Type-tagged, length-prefixed encoding: `<tag><byte length>:<bytes>`.

    Length prefixing alone closed delimiter ambiguity but not type ambiguity,
    because every value was funnelled through `str()` first. The integer 41238
    and the string "41238" therefore produced identical pre-hash bytes, as did
    the boolean False and the string "False", and a role count of 28061 and
    "28061". Different typed authorities could share a root.

    `bool` is checked before `int` because `bool` is a subclass of `int` in
    Python, so the order here is load-bearing rather than stylistic.
    """
    if isinstance(value, bool):
        tag, payload = b"b", (b"1" if value else b"0")
    elif isinstance(value, int):
        tag, payload = b"i", str(int(value)).encode("ascii")
    elif isinstance(value, str):
        tag, payload = b"s", value.encode("utf-8")
    else:
        raise AssertionError(
            "%s: %r is a %s; only bool, int and str may be hashed into an authority root"
            % (STOP_FIELD_TYPE, value, type(value).__name__))
    return b"%s%d:%s" % (tag, len(payload), payload)


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
                  rows_scanned: int, locations: Mapping[str, Mapping[str, Any]],
                  membership_sha256: str, block_manifest_sha256: str,
                  block_geometry: Mapping[str, Mapping[str, int]] | None = None
                  ) -> str:
    digest = hashlib.sha256()
    # 4F/4G: the closure binds the identities of the two authorities that define
    # the population. Without them the root described a population without
    # naming what produced it, so a closure built from one membership could not
    # be distinguished from one built from another.
    digest.update(_typed(membership_sha256))
    digest.update(_typed(block_manifest_sha256))
    # No coercion here. Wrapping a value in int() or str() before hashing
    # normalises a type substitution away, so the type tag would bind nothing:
    # operator 31 and "31" both became int 31. The declared type is required
    # instead, and a substitution produces a different root.
    digest.update(_typed("T0_V20_POPULATION_CLOSURE_V4"))
    digest.update(_typed(operator_index))
    digest.update(_typed(matrix_id))
    digest.update(_typed(len(blocks)))
    digest.update(_typed(rows_scanned))
    for key in blocks:
        digest.update(_typed(key))
        # Declared rows and nnz are decision-bearing: they gate the metadata and
        # counts geometry checks. Binding them means a mutated manifest geometry
        # moves the root instead of passing unnoticed.
        if block_geometry is not None:
            declared = block_geometry.get(key) or {}
            digest.update(_typed(int(declared.get("rows", 0))))
            digest.update(_typed(int(declared.get("nnz", 0))))
    ordered = sorted(locations, key=lambda value: value.encode("utf-8"))
    digest.update(_typed(len(ordered)))
    for cell in ordered:
        record = locations[cell]
        digest.update(_typed(cell))
        digest.update(_typed(record["block_key"]))
        digest.update(_typed(record["row_index"]))
        # 4I: meta_path and counts_path are consumed on the execution path, so
        # they are bound here rather than travelling as unbound strings.
        digest.update(_typed(record["meta_path"]))
        digest.update(_typed(record["meta_sha256"]))
        digest.update(_typed(record["counts_path"]))
        digest.update(_typed(record["counts_sha256"]))
    return digest.hexdigest()


def build_population_closure(
    *,
    membership_bytes: bytes,
    expected_membership_sha256: str,
    block_manifest_bytes: bytes,
    expected_block_manifest_sha256: str,
    meta_bytes_by_path: Mapping[str, bytes],
    operator_index: int,
    matrix_id: str,
    expected_total_blocks: int | None = None,
    expected_operators: int | None = None,
    expected_op31_block_count: int | None = None,
) -> dict[str, Any]:
    """Scan every block of the operator and close the population.

    Both inputs are authenticated by digest before anything is parsed, so this
    cannot be run against arbitrary caller-supplied CSV bytes. The accepted
    membership member and the pinned complete Phase2 block manifest are the two
    authorities the population is defined by, and they must be named.
    """
    actual_membership = hashlib.sha256(bytes(membership_bytes)).hexdigest()
    if actual_membership != str(expected_membership_sha256):
        raise AssertionError("%s: membership is %s, expected %s"
                             % (STOP_MEMBERSHIP_DIGEST, actual_membership,
                                expected_membership_sha256))
    actual_manifest = hashlib.sha256(bytes(block_manifest_bytes)).hexdigest()
    if actual_manifest != str(expected_block_manifest_sha256):
        raise AssertionError("%s: block manifest is %s, expected %s"
                             % (STOP_MANIFEST_DIGEST, actual_manifest,
                                expected_block_manifest_sha256))

    # Retained so the logical authority can prove it was handed the same
    # membership this closure was built from, rather than a spliced substitute.
    bound_membership_sha256 = actual_membership
    bound_manifest_sha256 = actual_manifest

    membership_columns, membership_rows = _rows(membership_bytes)
    for required in ("cell_id", "donor_id", "operator_index", "matrix_id"):
        if required not in membership_columns:
            raise AssertionError("%s: %r absent" % (STOP_MEMBERSHIP_COLUMNS, required))

    # The values, not merely the columns. Requiring the columns and ignoring
    # what they say let a membership for another operator or another matrix
    # define this population.
    targets: dict[str, str] = {}
    for position, record in enumerate(membership_rows):
        declared_operator = str(record["operator_index"]).strip()
        if int(declared_operator) != int(operator_index):
            raise AssertionError("%s: membership row %d is operator %s, expected %d"
                                 % (STOP_MEMBERSHIP_OPERATOR, position,
                                    declared_operator, int(operator_index)))
        if str(record["matrix_id"]).strip() != str(matrix_id):
            raise AssertionError("%s: membership row %d is matrix %s, expected %s"
                                 % (STOP_MEMBERSHIP_MATRIX, position,
                                    record["matrix_id"], matrix_id))
        cell = str(record["cell_id"]).strip()
        # A dict assignment silently redefined the population on a duplicate.
        if cell in targets:
            raise AssertionError("%s: %s appears more than once in the membership"
                                 % (STOP_MEMBERSHIP_UNIQUE, cell))
        targets[cell] = str(record["donor_id"]).strip()

    manifest_columns, manifest_rows = _rows(block_manifest_bytes)
    for required in ("block_key", "operator_index", "matrix_id", "meta_path",
                     "meta_sha256", "counts_path", "counts_sha256",
                     "rows", "nnz"):
        if required not in manifest_columns:
            raise AssertionError("%s: %r absent" % (STOP_MANIFEST_COLUMNS, required))

    blocks = []
    geometry: dict[str, dict[str, int]] = {}
    locations: dict[str, dict[str, Any]] = {}
    rows_scanned = 0
    donors: set[str] = set()

    # The frozen Phase2 manifest is the COMPLETE 8,915-block, 42-operator
    # manifest and its first row is operator 0. Authenticating it and then
    # requiring every row to be this operator stopped on row one, which made the
    # production contract impossible to satisfy: a pre-filtered manifest avoids
    # the stop but then its bytes cannot carry the frozen complete-manifest
    # digest. So the operator is selected from inside the authenticated bytes.
    all_operators = {int(str(r["operator_index"]).strip()) for r in manifest_rows}
    if expected_total_blocks is not None and len(manifest_rows) != int(expected_total_blocks):
        raise AssertionError("%s: manifest holds %d blocks, expected %d"
                             % (STOP_MANIFEST_GEOMETRY, len(manifest_rows),
                                int(expected_total_blocks)))
    if expected_operators is not None and len(all_operators) != int(expected_operators):
        raise AssertionError("%s: manifest spans %d operators, expected %d"
                             % (STOP_MANIFEST_GEOMETRY, len(all_operators),
                                int(expected_operators)))
    # A manifest carrying no block at all for this operator is an operator
    # mismatch for this population, and stays a STOP under the same terminal it
    # always raised.
    if int(operator_index) not in all_operators:
        raise AssertionError(
            "%s: the authenticated manifest carries no block for operator %d; it "
            "spans %s" % (STOP_OPERATOR, int(operator_index), sorted(all_operators)))

    for record in sorted(manifest_rows, key=lambda r: str(r["block_key"])):
        block_key = str(record["block_key"]).strip()
        if int(str(record["operator_index"]).strip()) != int(operator_index):
            # A block of another operator. Not this population's concern, and
            # not a defect in the complete manifest.
            continue
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
        # The manifest's declared geometry is checked against what the
        # authenticated metadata actually contains. It was previously guarded by
        # a presence test, which made it skippable by omitting the column; the
        # column is now required above, so this check always runs.
        declared_rows = exact_positive_integer(
            record["rows"], "manifest rows for %s" % block_key)
        if declared_rows != len(meta_rows):
            raise AssertionError(
                "%s: %s declares %d rows but its authenticated metadata holds %d"
                % (STOP_COUNTS_GEOMETRY, block_key, declared_rows,
                   len(meta_rows)))
        declared_nnz = exact_positive_integer(
            record["nnz"], "manifest nnz for %s" % block_key)
        geometry[block_key] = {"rows": declared_rows, "nnz": declared_nnz}
        for row_index, meta_row in enumerate(meta_rows):
            rows_scanned += 1
            cell = str(meta_row.get("canonical_cell_id") or "").strip()
            if cell not in targets:
                continue
            # The metadata carries its own donor_id. Emitting the membership
            # donor while ignoring it meant a metadata row for one donor could
            # be represented under another.
            metadata_donor = str(meta_row.get("donor_id") or "").strip()
            if metadata_donor != targets[cell]:
                raise AssertionError(
                    "%s: %s is donor %s in the Phase2 metadata at %s#%d but donor %s "
                    "in the membership"
                    % (STOP_DONOR_DISAGREES, cell, metadata_donor, block_key,
                       row_index, targets[cell]))
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

    if expected_op31_block_count is not None and len(blocks) != int(expected_op31_block_count):
        raise AssertionError(
            "%s: selected %d operator-%d blocks, expected %d"
            % (STOP_MANIFEST_GEOMETRY, len(blocks), int(operator_index),
               int(expected_op31_block_count)))

    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "operator_index": int(operator_index),
        "matrix_id": str(matrix_id),
        "membership_sha256": bound_membership_sha256,
        "block_manifest_sha256": bound_manifest_sha256,
        "blocks": list(blocks),
        "manifest_total_blocks": len(manifest_rows),
        "manifest_operators": len(all_operators),
        "blocks_scanned": len(blocks),
        "metadata_rows_scanned": rows_scanned,
        "target_cells": len(locations),
        "missing": len(missing),
        "duplicate_target_hits": 0,
        "donors": sorted(donors),
        "row_locations": locations,
        "full_scan": True,
        "block_geometry": geometry,
        "population_closure_root_sha256": _closure_root(
            operator_index, matrix_id, blocks, rows_scanned, locations,
            bound_membership_sha256, bound_manifest_sha256, geometry),
        "real_execution_ready": False,
    }


def _logical_root(rows: Sequence[Mapping[str, Any]], feature_root: str,
                  closure_root: str) -> str:
    """Digest of the logical row authority.

    Binds BOTH parents and every execution-relevant row field. Two omissions
    were found here by external review after the R2 repairs: the population
    closure root, and the `meta_path` / `counts_path` the execution path actually
    reads. Without the closure root a logical object could carry a different
    population identity and still reproduce the expected root; without the paths
    it could point at different files. Mutating the logical rows and the physical
    plan together keeps them consistent with each other, so the physical
    verifier's field comparison cannot substitute for binding them here.
    """
    fields = ("logical_index", "canonical_cell_id", "donor_id", "block_key",
              "row_index", "selection_row", "expression_row",
              "primary_row_weight", "source_library", "meta_path",
              "meta_sha256", "counts_path", "counts_sha256")
    digest = hashlib.sha256()
    digest.update(_typed("T0_V20_LOGICAL_ROW_AUTHORITY_V5"))
    digest.update(_typed(feature_root))
    digest.update(_typed(closure_root))
    digest.update(_typed(len(rows)))
    digest.update(_typed(len(fields)))
    for row in rows:
        for field in fields:
            digest.update(_typed(row[field]))
    return digest.hexdigest()


def build_logical_row_authority(
    *,
    closure: Mapping[str, Any],
    membership_bytes: bytes,
    feature_authority_root_sha256: str,
) -> dict[str, Any]:
    """Bind the rows in frozen membership order to their physical provenance.

    The membership supplied here must be the one the closure was built from.
    Without that check a closure computed over membership A could be combined
    with membership B to order rows, so the population and its order would come
    from different authorities.
    """
    bound = closure.get("membership_sha256")
    if not _is_hex64(bound):
        raise AssertionError(
            "%s: the closure does not carry a bound membership digest, so a "
            "spliced membership cannot be detected" % STOP_MEMBERSHIP_SPLICE)
    supplied = hashlib.sha256(bytes(membership_bytes)).hexdigest()
    if supplied != str(bound):
        raise AssertionError(
            "%s: this membership is %s but the closure was built from %s"
            % (STOP_MEMBERSHIP_SPLICE, supplied, bound))
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
            rows, feature_authority_root_sha256,
            closure["population_closure_root_sha256"]),
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
    digest.update(_typed("T0_V20_PHYSICAL_READ_PLAN_V4"))
    digest.update(_typed(logical["logical_row_authority_root_sha256"]))
    digest.update(_typed(len(plan)))
    for entry in plan:
        digest.update(_typed(entry["block_key"]))
        digest.update(_typed(entry["row_index"]))
        digest.update(_typed(entry["logical_index"]))
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
                                 expected_logical_root_sha256: str,
                                 logical: Mapping[str, Any] | None = None) -> bool:
    """A physical ordering may never redefine the logical population.

    Checking the entry count, that the logical indices form a permutation, and
    that the carried logical-root string matches is not restoration. All three
    hold while an entry points at a different block and row, because none of
    them looks at what the entry actually says. So when the logical authority is
    supplied, every execution-relevant field is compared against the logical row
    that the entry's own `logical_index` names.

    `logical` is optional only so existing two-argument call sites keep working.
    A production verification must pass it, and `assert_physical_plan_lawful`
    requires it.
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

    if logical is not None:
        rows = logical["rows"]
        if len(rows) != expected_count:
            raise AssertionError(
                "%s: the logical authority holds %d rows for a plan of %d"
                % (STOP_RESTORE, len(rows), expected_count))
        for entry in entries:
            index = int(entry["logical_index"])
            if not (0 <= index < len(rows)):
                raise AssertionError("%s: logical_index %d is out of range"
                                     % (STOP_RESTORE, index))
            row = rows[index]
            for field in ("block_key", "row_index", "counts_path", "counts_sha256"):
                if str(entry[field]) != str(row[field]):
                    raise AssertionError(
                        "%s: plan entry for logical_index %d carries %s=%r but the "
                        "logical row binds %r"
                        % (STOP_PLAN_FIELD, index, field, entry[field], row[field]))
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


ROW_FIELD_TYPES = {
    "logical_index": int,
    "canonical_cell_id": str,
    "donor_id": str,
    "block_key": str,
    "row_index": int,
    "selection_row": int,
    "expression_row": int,
    "primary_row_weight": str,
    "source_library": int,
    "meta_path": str,
    "meta_sha256": str,
    "counts_path": str,
    "counts_sha256": str,
}


def assert_row_field_types(logical: Mapping[str, Any]) -> bool:
    """Enforce declared row-field types before any root is recomputed.

    B2 had no external verifier path, so a future verifier recomputing roots
    from an authority object could have accepted `row_index` as either 1 or
    "1". Type-tagged framing makes those digests differ; this makes the
    substitution refusable at the boundary as well, which is the other half.
    """
    rows = logical.get("rows")
    if not isinstance(rows, list) or not rows:
        raise AssertionError("%s: rows must be a non-empty list" % STOP_FIELD_SCHEMA)
    for index, row in enumerate(rows):
        for name, expected in ROW_FIELD_TYPES.items():
            if name not in row:
                raise AssertionError("%s: row %d lacks %s"
                                     % (STOP_FIELD_SCHEMA, index, name))
            value = row[name]
            if expected is int:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise AssertionError("%s: row %d %s is %s, expected int"
                                         % (STOP_FIELD_SCHEMA, index, name,
                                            type(value).__name__))
            elif not isinstance(value, str):
                raise AssertionError("%s: row %d %s is %s, expected str"
                                     % (STOP_FIELD_SCHEMA, index, name,
                                        type(value).__name__))
    if not isinstance(logical.get("row_count"), int) or isinstance(
            logical.get("row_count"), bool):
        raise AssertionError("%s: row_count must be int" % STOP_FIELD_SCHEMA)
    if logical["row_count"] != len(rows):
        raise AssertionError("%s: row_count %r does not match %d rows"
                             % (STOP_FIELD_SCHEMA, logical["row_count"], len(rows)))
    return True


def assert_row_authority_lawful(
    *,
    logical: Mapping[str, Any],
    expected_logical_row_authority_root_sha256: str,
    expected_feature_authority_root_sha256: str,
    expected_population_closure_root_sha256: str,
) -> dict[str, Any]:
    """External verifier: enforce types, then establish all three equalities.

    Comparing only the recomputed root against the outside expectation left an
    object whose STORED root disagreed with its own contents able to pass. So the
    check is stored == recomputed == externally expected, and both parents -- the
    feature root and the population closure root -- are externally bound.
    """
    if logical.get("real_execution_ready") is not False:
        raise AssertionError("%s: a pathology-blind row authority may not claim readiness"
                             % STOP_FIELD_SCHEMA)
    assert_row_field_types(logical)
    if str(logical.get("feature_authority_root_sha256")) != str(
            expected_feature_authority_root_sha256):
        raise AssertionError("%s: the row authority names feature root %s, expected %s"
                             % (STOP_FEATURE_ROOT_MALFORMED,
                                logical.get("feature_authority_root_sha256"),
                                expected_feature_authority_root_sha256))
    stored_closure = logical.get("population_closure_root_sha256")
    if not _is_hex64(stored_closure):
        raise AssertionError(
            "%s: the row authority does not carry a population closure root, so "
            "its population identity cannot be bound"
            % (STOP_PARENT_IDENTITY,))
    if str(stored_closure) != str(expected_population_closure_root_sha256):
        raise AssertionError(
            "%s: the row authority names closure root %s, externally expected %s"
            % (STOP_PARENT_IDENTITY, stored_closure,
               expected_population_closure_root_sha256))

    recomputed = _logical_root(logical["rows"],
                               logical["feature_authority_root_sha256"],
                               stored_closure)
    stored_root = logical.get("logical_row_authority_root_sha256")
    if str(stored_root) != recomputed:
        raise AssertionError(
            "%s: the object stores logical root %s but its own contents "
            "recompute to %s"
            % (STOP_STORED_ROOT_DISAGREES, stored_root, recomputed))
    if recomputed != str(expected_logical_row_authority_root_sha256):
        raise AssertionError("%s: recomputed %s is not the expected %s"
                             % (STOP_RESTORE, recomputed,
                                expected_logical_row_authority_root_sha256))
    return {"logical_row_authority_root_sha256": recomputed,
            "population_closure_root_sha256": str(stored_closure),
            "rows": len(logical["rows"])}


def _prove_source_library_fixture_only(
    *,
    logical: Mapping[str, Any],
    logical_index: int,
    raw_source_row_values: Sequence[Any],
    raw_source_provenance: Mapping[str, Any],
    expected_source_sha256: str = MTG_SOURCE_SHA256,
    expected_matrix_slot: str = MTG_SOURCE_MATRIX_SLOT,
    expected_source_width: int = SOURCE_FEATURE_COUNT,
) -> bool:
    """Fixture-only checker for already-supplied values.

    This is deliberately private and may be used only by synthetic tests. It is
    not an authentication path: production source-library proof lives in
    t0_raw_source_row_authority_v1 and reads the source bytes itself.


    The earlier version required three provenance keys to be present and checked
    none of them. It never verified `source_sha256` against anything, never
    required `source_row_index` to equal the bound `expression_row`, and never
    checked the row's cell or donor identity. A vector of zeros with a single
    correct total and an arbitrary digest string proved the value, which is
    exactly the distinction this function exists to make.

    Proof now requires all of:

      * the source asset digest equals the frozen MTG H5AD identity;
      * the matrix slot is the raw UMI layer, not a normalised one;
      * the row width is the source feature space, not the projected address
        space -- `source_library` is the sum of a pre-projection row, so an
        address-space row can never prove it even if its total happens to match;
      * the source row index equals the bound `expression_row`;
      * the source cell and donor identities equal the bound ones;
      * every value is an exact non-negative integer count;
      * the total equals the bound `source_library`.

    This mirrors the historical Phase2 materializer, which checked
    `cells[source_row] == canonical_cell_id` and `donors[source_row] ==
    donor_id` before summing the row it had sliced out of `indptr`.
    """
    row = logical["rows"][int(logical_index)]

    for field in ("source_sha256", "source_row_index", "source_width",
                  "canonical_cell_id", "donor_id", "matrix_slot"):
        if field not in raw_source_provenance:
            raise AssertionError("%s: %s is absent" % (STOP_RAW_PROVENANCE, field))

    declared_digest = str(raw_source_provenance["source_sha256"])
    if declared_digest != str(expected_source_sha256):
        raise AssertionError(
            "%s: the row is declared to come from source %s, but the frozen MTG "
            "source asset is %s"
            % (STOP_SOURCE_IDENTITY, declared_digest, expected_source_sha256))

    declared_slot = str(raw_source_provenance["matrix_slot"])
    if declared_slot != str(expected_matrix_slot):
        raise AssertionError(
            "%s: the row is declared to come from slot %r, but raw counts live in %r"
            % (STOP_SOURCE_SLOT, declared_slot, expected_matrix_slot))

    declared_width = int(raw_source_provenance["source_width"])
    if declared_width != len(raw_source_row_values):
        raise AssertionError("%s: provenance declares width %d but %d values were supplied"
                             % (STOP_RAW_PROVENANCE, declared_width,
                                len(raw_source_row_values)))
    if declared_width == ADDRESS_SPACE_SIZE:
        raise AssertionError(
            "%s: a row of %d values is the projected address-space row, not the "
            "pre-projection raw source row" % (STOP_RAW_WIDTH_ADDRESS, declared_width))
    if declared_width != int(expected_source_width):
        raise AssertionError(
            "%s: the raw source row is %d wide but the source feature space is %d"
            % (STOP_SOURCE_WIDTH, declared_width, int(expected_source_width)))

    declared_row = int(raw_source_provenance["source_row_index"])
    if declared_row != int(row["expression_row"]):
        raise AssertionError(
            "%s: the row was read at source row %d but logical index %d binds "
            "expression_row %d"
            % (STOP_SOURCE_ROW_IDENTITY, declared_row, int(logical_index),
               int(row["expression_row"])))

    declared_cell = str(raw_source_provenance["canonical_cell_id"])
    if declared_cell != str(row["canonical_cell_id"]):
        raise AssertionError(
            "%s: the source row identifies cell %r but logical index %d binds %r"
            % (STOP_SOURCE_ROW_IDENTITY, declared_cell, int(logical_index),
               row["canonical_cell_id"]))

    declared_donor = str(raw_source_provenance["donor_id"])
    if declared_donor != str(row["donor_id"]):
        raise AssertionError(
            "%s: the source row identifies donor %r but logical index %d binds %r"
            % (STOP_SOURCE_ROW_IDENTITY, declared_donor, int(logical_index),
               row["donor_id"]))

    total = 0
    for position, value in enumerate(raw_source_row_values):
        if isinstance(value, bool) or not isinstance(value, int):
            if not (isinstance(value, float) and float(value).is_integer()):
                raise AssertionError("%s: position %d is %r"
                                     % (STOP_RAW_SEMANTICS, position, value))
        numeric = int(value)
        if numeric < 0:
            raise AssertionError("%s: position %d is %r"
                                 % (STOP_RAW_SEMANTICS, position, value))
        total += numeric

    bound = row["source_library"]
    if total != bound:
        raise AssertionError(
            "%s: the authenticated raw row sums to %d but the bound source_library is %d"
            % (STOP_LIBRARY_NOT_PROVEN, total, bound))
    return True



def prove_source_library(**kwargs: Any) -> bool:
    """Refuse the retired caller-vector API.

    R4 added a byte-reading prover but accidentally left this public name wired
    to the old raw_source_row_values/raw_source_provenance interface. The exact
    fabricated-vector attack therefore remained callable. This compatibility
    name now fails closed unconditionally; synthetic tests that need the old
    value semantics must call the private fixture helper above.
    """
    offending = sorted(str(key) for key in kwargs)
    raise AssertionError(
        "%s: the caller-vector source-library prover is retired; supplied keys=%s. "
        "Production proof must be derived from authenticated H5AD bytes."
        % (STOP_CALLER_VALUES, offending))


def verify_selected_row(
    *,
    logical: Mapping[str, Any],
    logical_index: int,
    row_values: Sequence[Any],
    selected_expression_row: int,
    address_space_size: int = ADDRESS_SPACE_SIZE,
    expression_row_upper_bound: int | None = None,
) -> bool:
    """Verify the row actually selected, not merely the payload it came from.

    A correct block digest says the bytes are the bound bytes. It says nothing
    about which row inside them was read, how wide that row is, or whether its
    values are counts, so all four are checked here.
    """
    row = logical["rows"][int(logical_index)]
    # Bounds before correspondence: a structurally impossible row index is a
    # more fundamental fault than naming the wrong one, and reporting it as
    # "not bound" would hide why.
    if expression_row_upper_bound is not None:
        if not (0 <= int(selected_expression_row) < int(expression_row_upper_bound)):
            raise AssertionError("%s: %d is outside 0..%d"
                                 % (STOP_ROW_BOUNDS, int(selected_expression_row),
                                    int(expression_row_upper_bound) - 1))
    if int(selected_expression_row) != int(row["expression_row"]):
        raise AssertionError("%s: row %d was selected but %d is bound for logical index %d"
                             % (STOP_ROW_NOT_BOUND, int(selected_expression_row),
                                int(row["expression_row"]), int(logical_index)))
    if len(row_values) != int(address_space_size):
        raise AssertionError("%s: %d values, expected %d"
                             % (STOP_ROW_WIDTH, len(row_values), int(address_space_size)))
    for position, value in enumerate(row_values):
        if isinstance(value, bool) or not isinstance(value, int):
            if not (isinstance(value, float) and value.is_integer()):
                raise AssertionError("%s: position %d is %r"
                                     % (STOP_ROW_SEMANTICS, position, value))
        if int(value) < 0:
            raise AssertionError("%s: position %d is %r"
                                 % (STOP_ROW_SEMANTICS, position, value))
    return True


# ---------------------------------------------------------------------------
# 4C: the two row coordinates, kept apart.
#
# `expression_row` addresses the ORIGINAL H5 source matrix. `row_index`
# addresses the row within the materialized `block-*.counts.npz` payload. The
# Phase2 producer enumerates `local` inside the block while `expression_row`
# names the source row, so for the same cell they are different numbers.
# Verifying a block selection against `expression_row` checks the wrong
# coordinate, and one argument must never carry both.
# ---------------------------------------------------------------------------

def verify_selected_block_row(
    *,
    logical: Mapping[str, Any],
    logical_index: int,
    selected_row_index: int,
    row_values: Sequence[Any],
    address_space_size: int = ADDRESS_SPACE_SIZE,
) -> bool:
    """Verify the row selected from the MATERIALIZED block payload.

    Bound to `row_index`. Passing the H5 source coordinate here is refused,
    which is what keeps the two checks from being substitutable for each other.
    """
    row = logical["rows"][int(logical_index)]
    bound_block_row = int(row["row_index"])
    if int(selected_row_index) != bound_block_row:
        raise AssertionError(
            "%s: block row %d was selected but logical index %d binds block row "
            "%d (its H5 expression_row is %d, a different coordinate)"
            % (STOP_BLOCK_ROW_NOT_BOUND, int(selected_row_index),
               int(logical_index), bound_block_row, int(row["expression_row"])))
    if len(row_values) != int(address_space_size):
        raise AssertionError("%s: %d values, expected %d"
                             % (STOP_ROW_WIDTH, len(row_values),
                                int(address_space_size)))
    for position, value in enumerate(row_values):
        if isinstance(value, bool) or not isinstance(value, int):
            if not (isinstance(value, float) and float(value).is_integer()):
                raise AssertionError("%s: position %d is %r"
                                     % (STOP_ROW_SEMANTICS, position, value))
        if int(value) < 0:
            raise AssertionError("%s: position %d is %r"
                                 % (STOP_ROW_SEMANTICS, position, value))
    return True


# ---------------------------------------------------------------------------
# 4D and 4E: authenticate the payload, then select from THOSE bytes.
# ---------------------------------------------------------------------------

def _parse_csr_counts(payload: bytes) -> dict[str, Any]:
    """Parse a scipy-CSR `.npz` from bytes already held in memory.

    The real Phase2 blocks are `scipy.sparse.save_npz` output: members `data`,
    `indices`, `indptr`, `shape` and `format`, with `format` == b"csr", shape
    (rows, 41238) and int32 counts. Only numpy is needed to read them, and
    slicing `indptr` is what the historical materializer did.
    """
    import numpy as np

    with np.load(io.BytesIO(bytes(payload))) as handle:
        members = set(handle.files)
        required = {"data", "indices", "indptr", "shape", "format"}
        if not required.issubset(members):
            raise AssertionError("%s: payload members are %s, expected at least %s"
                                 % (STOP_COUNTS_FORMAT, sorted(members),
                                    sorted(required)))
        fmt_text = bytes(handle["format"].tobytes()).decode("ascii").rstrip("\x00")
        if fmt_text != "csr":
            raise AssertionError("%s: payload format is %r, expected 'csr'"
                                 % (STOP_COUNTS_FORMAT, fmt_text))
        shape = [int(value) for value in handle["shape"]]
        if len(shape) != 2:
            raise AssertionError("%s: payload shape is %r" % (STOP_COUNTS_GEOMETRY, shape))
        return {"data": handle["data"][:], "indices": handle["indices"][:],
                "indptr": handle["indptr"][:], "shape": shape}


def verify_block_row_from_authenticated_payload(
    *,
    logical: Mapping[str, Any],
    logical_index: int,
    counts_payload_bytes: bytes,
    declared_rows: int | None = None,
    declared_nnz: int | None = None,
    address_space_size: int = ADDRESS_SPACE_SIZE,
) -> list[int]:
    """Authenticate the counts payload, then select and validate the bound row.

    The coupling is the point. Authenticating one payload and then validating an
    independently supplied `row_values` vector proves nothing about those bytes,
    because the digest and the values would describe different things. Here the
    payload is captured once, authenticated against the digest the logical
    authority binds, parsed from those same captured bytes, and the block-local
    `row_index` is selected out of the parsed matrix. The row returned is the row
    that was actually read.
    """
    row = logical["rows"][int(logical_index)]
    payload = bytes(counts_payload_bytes)

    actual = hashlib.sha256(payload).hexdigest()
    if actual != str(row["counts_sha256"]):
        raise AssertionError(
            "%s: the supplied counts payload is %s but logical index %d binds %s"
            % (STOP_COUNTS_DIGEST, actual, int(logical_index), row["counts_sha256"]))

    parsed = _parse_csr_counts(payload)
    rows, width = parsed["shape"][0], parsed["shape"][1]
    if width != int(address_space_size):
        raise AssertionError("%s: counts width is %d, expected %d"
                             % (STOP_COUNTS_GEOMETRY, width, int(address_space_size)))
    if declared_rows is not None and rows != int(declared_rows):
        raise AssertionError(
            "%s: the authenticated counts matrix holds %d rows but the manifest "
            "declares %d" % (STOP_COUNTS_GEOMETRY, rows, int(declared_rows)))
    if declared_nnz is not None:
        stored = int(parsed["indptr"][rows]) - int(parsed["indptr"][0])
        if stored != int(declared_nnz):
            raise AssertionError(
                "%s: the authenticated counts matrix stores %d values but the "
                "manifest declares nnz %d"
                % (STOP_COUNTS_GEOMETRY, stored, int(declared_nnz)))

    block_row = int(row["row_index"])
    if not (0 <= block_row < rows):
        raise AssertionError(
            "%s: bound block row %d is outside 0..%d of the authenticated payload"
            % (STOP_BLOCK_ROW_NOT_BOUND, block_row, rows - 1))

    indptr = parsed["indptr"]
    start, end = int(indptr[block_row]), int(indptr[block_row + 1])
    dense = [0] * width
    for offset in range(start, end):
        column = int(parsed["indices"][offset])
        value = parsed["data"][offset]
        if float(value) != int(value) or int(value) < 0:
            raise AssertionError("%s: column %d of block row %d is %r"
                                 % (STOP_ROW_SEMANTICS, column, block_row, value))
        if not (0 <= column < width):
            raise AssertionError("%s: column %d is outside the address space"
                                 % (STOP_COUNTS_GEOMETRY, column))
        dense[column] = int(value)

    verify_selected_block_row(logical=logical, logical_index=logical_index,
                              selected_row_index=block_row, row_values=dense,
                              address_space_size=address_space_size)
    return dense


# ---------------------------------------------------------------------------
# 4G and 4H: an external verifier for each of the three roots, each
# establishing stored == recomputed == externally expected.
# ---------------------------------------------------------------------------

def assert_closure_lawful(
    *,
    closure: Mapping[str, Any],
    expected_closure_root_sha256: str,
    expected_membership_sha256: str,
    expected_block_manifest_sha256: str,
) -> bool:
    """External verification of the population closure root and its parents."""
    for name, expected in (("membership_sha256", expected_membership_sha256),
                           ("block_manifest_sha256", expected_block_manifest_sha256)):
        stored = closure.get(name)
        if not _is_hex64(stored):
            raise AssertionError("%s: the closure does not carry %s"
                                 % (STOP_PARENT_IDENTITY, name))
        if str(stored) != str(expected):
            raise AssertionError("%s: closure %s is %s, externally expected %s"
                                 % (STOP_PARENT_IDENTITY, name, stored, expected))

    stored_root = closure.get("population_closure_root_sha256")
    if not _is_hex64(stored_root):
        raise AssertionError("%s: the closure carries no root" % STOP_CLOSURE_ROOT)

    recomputed = _closure_root(
        closure["operator_index"], closure["matrix_id"], closure["blocks"],
        closure["metadata_rows_scanned"], closure["row_locations"],
        closure["membership_sha256"], closure["block_manifest_sha256"],
        closure.get("block_geometry"))
    if recomputed != str(stored_root):
        raise AssertionError(
            "%s: the stored closure root %s does not match the root recomputed "
            "from the closure's own contents %s"
            % (STOP_CLOSURE_ROOT, stored_root, recomputed))
    if recomputed != str(expected_closure_root_sha256):
        raise AssertionError("%s: closure root is %s, externally expected %s"
                             % (STOP_CLOSURE_ROOT, recomputed,
                                expected_closure_root_sha256))
    return True


def assert_physical_plan_lawful(
    *,
    plan: Mapping[str, Any],
    expected_physical_root_sha256: str,
    expected_logical_root_sha256: str,
    logical: Mapping[str, Any],
) -> bool:
    """External verification of the physical read plan root.

    The plan root existed but nothing compared it against an external
    expectation, so a plan could be altered and its recomputed root would simply
    move along with it. Here the root is recomputed from the plan's own entries
    and required to equal both the stored value and the externally supplied one,
    and every entry is restored against its logical row first.
    """
    assert_plan_restores_logical(
        plan=plan, expected_logical_root_sha256=expected_logical_root_sha256,
        logical=logical)

    digest = hashlib.sha256()
    digest.update(_typed("T0_V20_PHYSICAL_READ_PLAN_V4"))
    digest.update(_typed(plan["logical_row_authority_root_sha256"]))
    digest.update(_typed(len(plan["plan"])))
    for entry in plan["plan"]:
        digest.update(_typed(entry["block_key"]))
        digest.update(_typed(entry["row_index"]))
        digest.update(_typed(entry["logical_index"]))
    recomputed = digest.hexdigest()

    stored = plan.get("physical_read_plan_root_sha256")
    if str(stored) != recomputed:
        raise AssertionError(
            "%s: the stored physical plan root %s does not match the root "
            "recomputed from the plan entries %s"
            % (STOP_PLAN_ROOT, stored, recomputed))
    if recomputed != str(expected_physical_root_sha256):
        raise AssertionError("%s: physical plan root is %s, externally expected %s"
                             % (STOP_PLAN_ROOT, recomputed,
                                expected_physical_root_sha256))
    return True
