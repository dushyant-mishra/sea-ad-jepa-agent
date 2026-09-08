"""Donor IMMUNE_FRACTION authority for T0.

Why this exists
---------------
`t0_adjudicator_v1` requires a donor-level `IMMUNE_FRACTION` column as one of its
mandatory base columns, and that column exists in no input file anywhere in the
project. V18 defines it only in prose, as "donor `IMMUNE_FRACTION` within op31
MTG". It is therefore a derived quantity that must be built, and it was missing
from every input inventory until a measurability pass went looking for it.

It is a nuisance covariate for the confirmation composition sensitivity. It is
NOT an eligibility input and must never feed `technical_complete`.

Design
------
The integers are the authority; the fraction is derived.

    immune_n_donor        numerator, from the accepted immune membership
    total_op31_n_donor    denominator, from the authenticated op31 substrate
    IMMUNE_FRACTION   :=  immune_n_donor / total_op31_n_donor

Storing a float as the primary authority would make the authority depend on
binary floating-point formatting, and would lose the two counts that make the
quantity auditable. So the exact integers are bound and digested, and any
floating-point value is computed at the boundary from them.

The numerator and denominator come from two independent authorities, which is
the point: the numerator counts accepted IMMUNE cells, the denominator counts ALL
op31 cells in the authenticated Phase2 substrate. Both are bound here by digest.

The denominator population, resolved by verification
----------------------------------------------------
An external review described the denominator as "all reader-fit op31 cells",
which raised a real question, because `partition` is NOT a column in the Phase2
block metadata -- it exists only in the 2.7 GB canonical foundation SQLite. So
"reader-fit op31" looked as though it might not be computable from the
authenticated substrate at all.

It is. Querying the canonical SQLite for the op31 partition composition gives

    reader_fit          638,150
    reader_validation   173,736
    reader_oracle       121,386
    total op31          933,272

and the Phase2 op31 store contains exactly 638,150 cells, counted independently
by scanning all 1,247 operator-31 block metadata files. The materialized op31
substrate is therefore precisely and only the reader_fit partition, which is also
an independent by-count confirmation of the store's declared
`no_validation_oracle_dev_sealed_pathology: true`.

So "all op31 cells in the Phase2 store" and "all reader-fit op31 cells" denote the
same population, and this module uses the former: it is derivable from bytes that
are already authenticated here, and it adds no dependency on the large external
SQLite. That SQLite was used only to corroborate the equality; the authority does
not read it and does not bind it.

Specification status
--------------------
V18 states this covariate only in prose. The exact formula is therefore a
SUCCESSOR SPECIFICATION, not recovered executable semantics, and this module says
so in its metadata rather than presenting the ratio as though it had been
recovered from frozen code. What verification settled is the denominator
POPULATION; freezing the formula remains an owner act.

Manifest handling
-----------------
The frozen Phase2 manifest is the COMPLETE 8,915-block, 42-operator manifest. It
is authenticated first, in full, and the operator-31 rows are then selected from
those authenticated bytes internally. Authenticating an independently constructed
pre-filtered CSV instead would mean the bytes carrying the frozen digest are not
the bytes actually used, so that is refused: this module never accepts a manifest
whose declared digest is the complete-manifest digest but whose content is
already narrowed.

Pathology
---------
Nothing here reads, parses, retains or emits any pathology value. The quantity is
a ratio of cell counts.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "JEPA_T0_IMMUNE_FRACTION_AUTHORITY_V1"
NAMESPACE = "T0-IMMUNE-FRACTION-V1"
DOMAIN_TAG = "T0-IMMUNE-FRACTION-V1-TYPED-LENGTH-PREFIXED"

REGISTRY = "T0_IMMUNE_FRACTION_REGISTRY.csv"
METADATA = "T0_IMMUNE_FRACTION_METADATA.json"
MANIFEST = "T0_IMMUNE_FRACTION_MANIFEST.csv"
ROOT_FILE = "T0_IMMUNE_FRACTION_PACKAGE_ROOT_SHA256.txt"
MEMBERS = (REGISTRY, METADATA, MANIFEST)

STOP_MEMBERSHIP_DIGEST = "STOP_T0_IMMUNE_FRACTION_MEMBERSHIP_DIGEST_MISMATCH"
STOP_MANIFEST_DIGEST = "STOP_T0_IMMUNE_FRACTION_COMPLETE_MANIFEST_DIGEST_MISMATCH"
STOP_MANIFEST_PREFILTERED = "STOP_T0_IMMUNE_FRACTION_MANIFEST_IS_PREFILTERED_NOT_COMPLETE"
STOP_MANIFEST_GEOMETRY = "STOP_T0_IMMUNE_FRACTION_COMPLETE_MANIFEST_GEOMETRY_MISMATCH"
STOP_META_DIGEST = "STOP_T0_IMMUNE_FRACTION_BLOCK_METADATA_DIGEST_MISMATCH"
STOP_META_ABSENT = "STOP_T0_IMMUNE_FRACTION_BLOCK_METADATA_ABSENT"
STOP_COLUMNS = "STOP_T0_IMMUNE_FRACTION_REQUIRED_COLUMN_ABSENT"
STOP_MATRIX = "STOP_T0_IMMUNE_FRACTION_MATRIX_MISMATCH"
STOP_OPERATOR = "STOP_T0_IMMUNE_FRACTION_OPERATOR_MISMATCH"
STOP_DONOR_SETS_DIFFER = "STOP_T0_IMMUNE_FRACTION_NUMERATOR_DENOMINATOR_DONOR_SETS_DIFFER"
STOP_DUPLICATE_DONOR = "STOP_T0_IMMUNE_FRACTION_DUPLICATE_DONOR"
STOP_NOT_POSITIVE = "STOP_T0_IMMUNE_FRACTION_NUMERATOR_NOT_POSITIVE"
STOP_EXCEEDS_DENOMINATOR = "STOP_T0_IMMUNE_FRACTION_NUMERATOR_EXCEEDS_DENOMINATOR"
STOP_OUT_OF_RANGE = "STOP_T0_IMMUNE_FRACTION_OUT_OF_UNIT_RANGE"
STOP_PRODUCTION_GEOMETRY = "STOP_T0_IMMUNE_FRACTION_PRODUCTION_GEOMETRY_MISMATCH"
STOP_FIELD_SCHEMA = "STOP_T0_IMMUNE_FRACTION_FIELD_SCHEMA_VIOLATION"
STOP_ROOT_MISMATCH = "STOP_T0_IMMUNE_FRACTION_ROOT_MISMATCH"
STOP_PACKAGE_MEMBER = "STOP_T0_IMMUNE_FRACTION_PACKAGE_MEMBER_INVALID"
STOP_PARENT_IDENTITY = "STOP_T0_IMMUNE_FRACTION_PARENT_IDENTITY_NOT_EXTERNALLY_BOUND"
STOP_NOT_INTEGER = "STOP_T0_IMMUNE_FRACTION_COUNT_NOT_EXACT_NONNEGATIVE_INTEGER"

# --- frozen production geometry ---------------------------------------------
# Independently verified against the frozen manifest and a full scan of all 1,247
# operator-31 block metadata files.
COMPLETE_MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
COMPLETE_MANIFEST_BLOCKS = 8915
COMPLETE_MANIFEST_OPERATORS = 42
OP31_OPERATOR_INDEX = 31
OP31_BLOCKS = 1247
MTG_MATRIX_ID = "sea_ad_mtg_rna_final_2026"
PRODUCTION_DONORS = 46
PRODUCTION_IMMUNE_CELLS = 20804
PRODUCTION_OP31_CELLS = 638150

# The denominator population, and the evidence that it is unambiguous.
# `partition` is not a Phase2 metadata column, so "reader-fit op31" is not
# directly computable from the substrate; it does not need to be, because the
# materialized op31 store is exactly the reader_fit partition. Verified by
# counting all 1,247 op31 block metadata files (638,150) against the canonical
# SQLite partition composition (reader_fit 638,150, reader_validation 173,736,
# reader_oracle 121,386).
DENOMINATOR_POPULATION = "ALL_OP31_CELLS_IN_AUTHENTICATED_PHASE2_SUBSTRATE"
DENOMINATOR_EQUALS_READER_FIT_PARTITION = True
OP31_READER_VALIDATION_CELLS_EXCLUDED = 173736
OP31_READER_ORACLE_CELLS_EXCLUDED = 121386
OP31_ALL_PARTITIONS_CELLS = 933272

# V18 states the covariate in prose only. The formula is a successor
# specification awaiting explicit owner acceptance; it is NOT recovered
# executable semantics, and this module must not claim otherwise.
FORMULA_SPEC_VERSION = "1.0.0"
FORMULA_SPECIFICATION_STATUS = "SUCCESSOR_SPECIFICATION__AWAITING_EXPLICIT_OWNER_FREEZE"
FORMULA_PROVENANCE = (
    "V18 SS170 names 'donor IMMUNE_FRACTION within op31 MTG' in prose. No frozen "
    "executable definition of the ratio was recovered from the accepted package. "
    "Verification settled the denominator POPULATION (the materialized op31 store "
    "is exactly the reader_fit partition); it did not supply a frozen formula."
)

MEMBERSHIP_COLUMNS = ("source", "matrix_id", "operator_index", "donor_id", "cell_id")
META_COLUMNS = ("donor_id",)
MANIFEST_COLUMNS = ("block_key", "operator_index", "matrix_id", "rows",
                    "meta_path", "meta_sha256")


# --- injective framing ------------------------------------------------------

def _typed(value: Any) -> bytes:
    """Type-tagged, length-prefixed framing.

    Both a delimiter-joined encoding and a `str()`-coerced encoding are
    non-injective: the first collides when a value contains the delimiter, the
    second collides when an int and a string share a decimal spelling. This
    frames the type tag and the byte length explicitly so neither can happen.
    """
    if isinstance(value, bool):
        tag, payload = b"b", (b"1" if value else b"0")
    elif isinstance(value, int):
        tag, payload = b"i", str(int(value)).encode("ascii")
    elif isinstance(value, str):
        tag, payload = b"s", value.encode("utf-8")
    elif isinstance(value, (tuple, list)):
        tag = b"l"
        payload = b"%d:%s" % (len(value), b"".join(_typed(v) for v in value))
    else:
        raise AssertionError("%s: cannot frame %r" % (STOP_FIELD_SCHEMA, type(value)))
    return b"%s%d:%s" % (tag, len(payload), payload)


def exact_nonnegative_int(value: Any, *, what: str) -> int:
    """Accept only an exact non-negative integer. Refuse bool and float."""
    if isinstance(value, bool):
        raise AssertionError("%s: %s is a bool" % (STOP_NOT_INTEGER, what))
    if isinstance(value, int):
        number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text or not text.isdigit():
            raise AssertionError("%s: %s is %r" % (STOP_NOT_INTEGER, what, value))
        number = int(text)
    else:
        raise AssertionError("%s: %s is %r" % (STOP_NOT_INTEGER, what, type(value)))
    if number < 0:
        raise AssertionError("%s: %s is %d" % (STOP_NOT_INTEGER, what, number))
    return number


def _rows(raw: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """Parse CSV from bytes already in memory.

    Parsing from bytes rather than reopening the path closes the interval
    between authenticating a file and using it: the bytes that were digested are
    the bytes that get parsed.
    """
    text = bytes(raw).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    columns = tuple(reader.fieldnames or ())
    return columns, [dict(row) for row in reader]


def _require_columns(columns: Sequence[str], required: Iterable[str],
                     what: str) -> None:
    for name in required:
        if name not in columns:
            raise AssertionError("%s: %s lacks %r" % (STOP_COLUMNS, what, name))


# --- numerator: accepted immune membership ----------------------------------

def immune_numerator_from_membership(
        *,
        membership_bytes: bytes,
        expected_membership_sha256: str,
        operator_index: int = OP31_OPERATOR_INDEX,
        matrix_id: str = MTG_MATRIX_ID,
) -> dict[str, int]:
    """Per-donor count of accepted IMMUNE cells.

    The membership bytes are authenticated before anything is parsed, and the
    operator and matrix VALUES are compared rather than merely required to be
    present: requiring the columns and ignoring what they say would let a
    membership for another operator or another matrix define this numerator.
    """
    actual = hashlib.sha256(bytes(membership_bytes)).hexdigest()
    if actual != str(expected_membership_sha256):
        raise AssertionError("%s: membership is %s, expected %s"
                            % (STOP_MEMBERSHIP_DIGEST, actual,
                               expected_membership_sha256))
    columns, records = _rows(membership_bytes)
    _require_columns(columns, MEMBERSHIP_COLUMNS, "membership")

    counts: Counter[str] = Counter()
    seen_cells: set[str] = set()
    for position, record in enumerate(records):
        declared_operator = exact_nonnegative_int(
            record["operator_index"], what="membership operator_index")
        if declared_operator != int(operator_index):
            raise AssertionError("%s: membership row %d is operator %d, expected %d"
                                % (STOP_OPERATOR, position, declared_operator,
                                   int(operator_index)))
        if str(record["matrix_id"]).strip() != str(matrix_id):
            raise AssertionError("%s: membership row %d is matrix %r, expected %r"
                                % (STOP_MATRIX, position, record["matrix_id"],
                                   matrix_id))
        cell = str(record["cell_id"]).strip()
        if cell in seen_cells:
            raise AssertionError("%s: cell %s appears more than once in the membership"
                                % (STOP_DUPLICATE_DONOR, cell))
        seen_cells.add(cell)
        counts[str(record["donor_id"]).strip()] += 1
    return dict(counts)


# --- denominator: authenticated op31 substrate ------------------------------

def select_op31_blocks(
        *,
        complete_manifest_bytes: bytes,
        expected_complete_manifest_sha256: str = COMPLETE_MANIFEST_SHA256,
        operator_index: int = OP31_OPERATOR_INDEX,
        matrix_id: str = MTG_MATRIX_ID,
        expected_total_blocks: int = COMPLETE_MANIFEST_BLOCKS,
        expected_operators: int = COMPLETE_MANIFEST_OPERATORS,
        expected_op31_blocks: int = OP31_BLOCKS,
) -> tuple[dict[str, Any], ...]:
    """Authenticate the COMPLETE manifest, then select operator 31 internally.

    The frozen manifest is the whole 8,915-block, 42-operator manifest; its first
    row is operator 0. So a contract that authenticates the complete manifest and
    then requires every row to be operator 31 is internally impossible -- it stops
    on the first row. Selection therefore happens here, inside the authenticated
    bytes, and the expected production geometry of both the whole manifest and the
    selected subset is asserted so the selection cannot silently narrow.

    A pre-filtered manifest is refused: if the caller declares the complete
    manifest digest, the bytes must actually be the complete manifest.
    """
    actual = hashlib.sha256(bytes(complete_manifest_bytes)).hexdigest()
    if actual != str(expected_complete_manifest_sha256):
        raise AssertionError("%s: manifest is %s, expected %s"
                            % (STOP_MANIFEST_DIGEST, actual,
                               expected_complete_manifest_sha256))
    columns, records = _rows(complete_manifest_bytes)
    _require_columns(columns, MANIFEST_COLUMNS, "complete manifest")

    operators = {exact_nonnegative_int(r["operator_index"],
                                      what="manifest operator_index")
                 for r in records}
    if len(records) != int(expected_total_blocks):
        raise AssertionError("%s: manifest has %d blocks, expected %d"
                            % (STOP_MANIFEST_GEOMETRY, len(records),
                               int(expected_total_blocks)))
    if len(operators) != int(expected_operators):
        raise AssertionError("%s: manifest spans %d operators, expected %d"
                            % (STOP_MANIFEST_GEOMETRY, len(operators),
                               int(expected_operators)))
    # A manifest already narrowed to one operator cannot be the complete
    # manifest, whatever digest the caller declares for it.
    if len(operators) == 1:
        raise AssertionError(
            "%s: the supplied manifest spans a single operator, so it is not the "
            "complete %d-operator manifest" % (STOP_MANIFEST_PREFILTERED,
                                               int(expected_operators)))

    selected = []
    for record in records:
        if exact_nonnegative_int(record["operator_index"],
                                 what="manifest operator_index") != int(operator_index):
            continue
        if str(record["matrix_id"]).strip() != str(matrix_id):
            raise AssertionError(
                "%s: operator-%d block %s declares matrix %r, expected %r"
                % (STOP_MATRIX, int(operator_index), record["block_key"],
                   record["matrix_id"], matrix_id))
        selected.append({
            "block_key": str(record["block_key"]).strip(),
            "meta_path": str(record["meta_path"]).strip(),
            "meta_sha256": str(record["meta_sha256"]).strip(),
            "rows": exact_nonnegative_int(record["rows"], what="manifest rows"),
        })
    if len(selected) != int(expected_op31_blocks):
        raise AssertionError("%s: selected %d operator-%d blocks, expected %d"
                            % (STOP_MANIFEST_GEOMETRY, len(selected),
                               int(operator_index), int(expected_op31_blocks)))
    return tuple(selected)


def op31_denominator_from_blocks(
        *,
        selected_blocks: Sequence[Mapping[str, Any]],
        meta_bytes_by_path: Mapping[str, bytes],
) -> tuple[dict[str, int], dict[str, str]]:
    """Per-donor count of ALL operator-31 cells, over authenticated block metadata.

    Every block's metadata is authenticated against the digest the manifest
    declares for it, and the declared row count is checked against the rows
    actually parsed. Returns the per-donor counts and the digest of every
    metadata member consumed, so the denominator names its own inputs.
    """
    counts: Counter[str] = Counter()
    consumed: dict[str, str] = {}
    for block in selected_blocks:
        path = str(block["meta_path"])
        if path not in meta_bytes_by_path:
            raise AssertionError("%s: %s (%s)"
                                % (STOP_META_ABSENT, path, block["block_key"]))
        raw = bytes(meta_bytes_by_path[path])
        digest = hashlib.sha256(raw).hexdigest()
        if digest != str(block["meta_sha256"]):
            raise AssertionError("%s: %s is %s, manifest declares %s"
                                % (STOP_META_DIGEST, path, digest,
                                   block["meta_sha256"]))
        columns, records = _rows(raw)
        _require_columns(columns, META_COLUMNS, path)
        if len(records) != int(block["rows"]):
            raise AssertionError(
                "%s: %s parsed %d rows but the manifest declares %d"
                % (STOP_MANIFEST_GEOMETRY, path, len(records), int(block["rows"])))
        for record in records:
            counts[str(record["donor_id"]).strip()] += 1
        consumed[path] = digest
    return dict(counts), consumed


# --- the authority ----------------------------------------------------------

def _build_immune_fraction_rows(
        *,
        numerator_by_donor: Mapping[str, int],
        denominator_by_donor: Mapping[str, int],
) -> tuple[dict[str, Any], ...]:
    """Bind exact integer numerator and denominator per donor.

    The fraction is deliberately not stored. Every invariant is checked on the
    integers, where it is exact.
    """
    num_donors = set(map(str, numerator_by_donor))
    den_donors = set(map(str, denominator_by_donor))
    if num_donors != den_donors:
        only_num = sorted(num_donors - den_donors)
        only_den = sorted(den_donors - num_donors)
        raise AssertionError(
            "%s: numerator-only %s, denominator-only %s"
            % (STOP_DONOR_SETS_DIFFER, only_num, only_den))

    rows = []
    for donor in sorted(num_donors, key=lambda d: d.encode("utf-8")):
        numerator = exact_nonnegative_int(numerator_by_donor[donor],
                                          what="numerator for %s" % donor)
        denominator = exact_nonnegative_int(denominator_by_donor[donor],
                                           what="denominator for %s" % donor)
        # A donor present in the accepted immune membership has at least one
        # immune cell by construction, so a zero numerator means the membership
        # and the substrate disagree rather than that the donor has no immune
        # cells. A zero denominator would make the quantity undefined.
        if numerator <= 0:
            raise AssertionError("%s: %s has numerator %d"
                                % (STOP_NOT_POSITIVE, donor, numerator))
        if denominator <= 0:
            raise AssertionError("%s: %s has denominator %d"
                                % (STOP_NOT_POSITIVE, donor, denominator))
        if numerator > denominator:
            raise AssertionError(
                "%s: %s has %d immune cells but only %d operator-31 cells"
                % (STOP_EXCEEDS_DENOMINATOR, donor, numerator, denominator))
        rows.append({
            "donor_id": donor,
            "immune_n_donor": numerator,
            "total_op31_n_donor": denominator,
        })
    return tuple(rows)


def immune_fraction_value(row: Mapping[str, Any]) -> float:
    """Derive the covariate from the bound integers, at the boundary only."""
    numerator = exact_nonnegative_int(row["immune_n_donor"], what="immune_n_donor")
    denominator = exact_nonnegative_int(row["total_op31_n_donor"],
                                        what="total_op31_n_donor")
    if denominator <= 0:
        raise AssertionError("%s: denominator is %d" % (STOP_NOT_POSITIVE, denominator))
    value = numerator / denominator
    # The adjudicator refuses IMMUNE_FRACTION outside [0,1], so refuse it here
    # rather than letting it reach the model boundary.
    if not (0.0 <= value <= 1.0):
        raise AssertionError("%s: %s is %r"
                            % (STOP_OUT_OF_RANGE, row.get("donor_id"), value))
    return value


def immune_fraction_root(rows: Sequence[Mapping[str, Any]]) -> str:
    """Digest over the bound integers, with explicit cardinality.

    Value-bearing but pathology-blind. It moves when any count moves, which is
    the intended behaviour: unlike an availability predicate, this quantity is
    not invariant under changes to the substrate.
    """
    parts = [_typed(DOMAIN_TAG), _typed(SCHEMA), _typed(NAMESPACE),
             _typed(len(rows))]
    for row in rows:
        parts.append(_typed([
            str(row["donor_id"]),
            exact_nonnegative_int(row["immune_n_donor"], what="immune_n_donor"),
            exact_nonnegative_int(row["total_op31_n_donor"],
                                  what="total_op31_n_donor"),
        ]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def assert_production_geometry(
        rows: Sequence[Mapping[str, Any]],
        *,
        expected_donors: int = PRODUCTION_DONORS,
        expected_immune_cells: int = PRODUCTION_IMMUNE_CELLS,
        expected_op31_cells: int = PRODUCTION_OP31_CELLS,
) -> bool:
    """The frozen production invariants, checked on the integers."""
    donors = [str(r["donor_id"]) for r in rows]
    if len(donors) != len(set(donors)):
        duplicates = sorted({d for d in donors if donors.count(d) > 1})
        raise AssertionError("%s: %s" % (STOP_DUPLICATE_DONOR, duplicates))
    if len(rows) != int(expected_donors):
        raise AssertionError("%s: %d donors, expected %d"
                            % (STOP_PRODUCTION_GEOMETRY, len(rows),
                               int(expected_donors)))
    total_numerator = sum(int(r["immune_n_donor"]) for r in rows)
    total_denominator = sum(int(r["total_op31_n_donor"]) for r in rows)
    if total_numerator != int(expected_immune_cells):
        raise AssertionError("%s: numerator sums to %d, expected %d"
                            % (STOP_PRODUCTION_GEOMETRY, total_numerator,
                               int(expected_immune_cells)))
    if total_denominator != int(expected_op31_cells):
        raise AssertionError("%s: denominator sums to %d, expected %d"
                            % (STOP_PRODUCTION_GEOMETRY, total_denominator,
                               int(expected_op31_cells)))
    for row in rows:
        immune_fraction_value(row)
    return True


def package_root(members: Mapping[str, bytes]) -> str:
    """Digest binding every package member's bytes, with explicit cardinality."""
    names = sorted(members)
    parts = [_typed(DOMAIN_TAG), _typed("PACKAGE"), _typed(len(names))]
    for name in names:
        parts.append(_typed([name,
                             hashlib.sha256(bytes(members[name])).hexdigest()]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def parent_contract_root(
        *,
        membership_sha256: str,
        complete_manifest_sha256: str,
        formula_spec_root_sha256: str,
        derivation_code_sha256: str,
) -> str:
    """One root over every parent identity this authority depends on.

    An external reviewer can accept this single value instead of the four
    individual digests. Binding the parents is the difference between verifying
    the authority and merely storing provenance beside it.
    """
    parts = [_typed(DOMAIN_TAG), _typed("PARENT_CONTRACT"), _typed(4)]
    for name, value in (("membership_sha256", membership_sha256),
                        ("complete_manifest_sha256", complete_manifest_sha256),
                        ("formula_spec_root_sha256", formula_spec_root_sha256),
                        ("derivation_code_sha256", derivation_code_sha256)):
        if not (isinstance(value, str) and len(value) == 64
                and all(c in "0123456789abcdef" for c in value)):
            raise AssertionError("%s: %s is not a lowercase hex sha256"
                                 % (STOP_FIELD_SCHEMA, name))
        parts.append(_typed([name, str(value)]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def build_production_authority(
        outdir: Path | str,
        *,
        membership_bytes: bytes,
        expected_membership_sha256: str,
        complete_manifest_bytes: bytes,
        expected_complete_manifest_sha256: str,
        meta_bytes_by_path: Mapping[str, bytes],
        expected_formula_spec_root_sha256: str,
        derivation_code_sha256: str,
        operator_index: int = OP31_OPERATOR_INDEX,
        matrix_id: str = MTG_MATRIX_ID,
        expected_total_blocks: int = COMPLETE_MANIFEST_BLOCKS,
        expected_operators: int = COMPLETE_MANIFEST_OPERATORS,
        expected_op31_blocks: int = OP31_BLOCKS,
        expected_donors: int = PRODUCTION_DONORS,
        expected_immune_cells: int = PRODUCTION_IMMUNE_CELLS,
        expected_op31_cells: int = PRODUCTION_OP31_CELLS,
) -> dict[str, Any]:
    """The only lawful production path: parent bytes in, package out.

    The earlier entrypoint took results a caller had already assembled -- `rows`
    it had built, plus `membership_sha256`, `complete_manifest_sha256` and
    `consumed_meta_sha256` as free-standing strings that nothing tied to the bytes
    they claimed to describe. That let correct-looking provenance be attached to a
    population the authority never derived.

    This constructor accepts no assembled result and no detached digest label. It
    authenticates the parents, selects operator 31 from inside the authenticated
    complete manifest, derives both counts, builds the exact integer rows itself,
    asserts the frozen production geometry against the frozen formula
    specification, and only then writes the package. Every digest it records is
    computed here from the bytes it authenticated.
    """
    import t0_immune_fraction_formula_spec_v1 as formula_spec

    membership_payload = bytes(membership_bytes)
    manifest_payload = bytes(complete_manifest_bytes)

    # Bind the specification before deriving anything against it.
    formula_spec.assert_spec_root(expected_formula_spec_root_sha256)

    numerator = immune_numerator_from_membership(
        membership_bytes=membership_payload,
        expected_membership_sha256=expected_membership_sha256,
        operator_index=operator_index, matrix_id=matrix_id)

    selected = select_op31_blocks(
        complete_manifest_bytes=manifest_payload,
        expected_complete_manifest_sha256=expected_complete_manifest_sha256,
        operator_index=operator_index, matrix_id=matrix_id,
        expected_total_blocks=expected_total_blocks,
        expected_operators=expected_operators,
        expected_op31_blocks=expected_op31_blocks)

    denominator, consumed = op31_denominator_from_blocks(
        selected_blocks=selected, meta_bytes_by_path=meta_bytes_by_path)

    rows = _build_immune_fraction_rows(numerator_by_donor=numerator,
                                       denominator_by_donor=denominator)
    assert_production_geometry(rows, expected_donors=expected_donors,
                               expected_immune_cells=expected_immune_cells,
                               expected_op31_cells=expected_op31_cells)
    # The specification carries the frozen production totals, so conformance to
    # it is exactly the claim "this is the production population". Assert it
    # whenever that claim is made, which is whenever the caller has not
    # overridden the frozen geometry. A scaled fixture is a different population
    # and must not be certified as the production one -- but neither should it
    # fail a check it never claimed to satisfy.
    claims_production_geometry = (
        int(expected_donors) == PRODUCTION_DONORS
        and int(expected_immune_cells) == PRODUCTION_IMMUNE_CELLS
        and int(expected_op31_cells) == PRODUCTION_OP31_CELLS)
    if claims_production_geometry:
        formula_spec.assert_authority_matches_specification(rows)

    return _build_authority_from_rows(
        outdir, rows=rows,
        membership_sha256=hashlib.sha256(membership_payload).hexdigest(),
        complete_manifest_sha256=hashlib.sha256(manifest_payload).hexdigest(),
        selected_op31_blocks=len(selected),
        consumed_meta_sha256=consumed,
        derivation_code_sha256=derivation_code_sha256,
        formula_spec_root_sha256=formula_spec.formula_spec_root(),
        check_production_geometry=False,
    )


def _build_authority_from_rows(
        outdir: Path | str,
        *,
        rows: Sequence[Mapping[str, Any]],
        membership_sha256: str,
        complete_manifest_sha256: str,
        selected_op31_blocks: int,
        consumed_meta_sha256: Mapping[str, str],
        derivation_code_sha256: str,
        formula_spec_root_sha256: str | None = None,
        check_production_geometry: bool = True,
) -> dict[str, Any]:
    """Write the authority package.

    `derivation_code_sha256` must be the Git blob digest of the deriving module,
    not a digest of its bytes on disk: on a platform that rewrites line endings
    the worktree bytes and the committed bytes differ, so a disk digest is not
    reproducible from the branch.
    """
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise AssertionError("%s: output directory must be absent or empty: %s"
                            % (STOP_PACKAGE_MEMBER, out))
    for name, value in (("membership_sha256", membership_sha256),
                        ("complete_manifest_sha256", complete_manifest_sha256),
                        ("derivation_code_sha256", derivation_code_sha256)):
        if not (isinstance(value, str) and len(value) == 64
                and all(c in "0123456789abcdef" for c in value)):
            raise AssertionError("%s: %s is not a lowercase hex sha256"
                                % (STOP_FIELD_SCHEMA, name))
    if check_production_geometry:
        assert_production_geometry(rows)

    if formula_spec_root_sha256 is None:
        import t0_immune_fraction_formula_spec_v1 as formula_spec
        spec_root = formula_spec.formula_spec_root()
    else:
        spec_root = str(formula_spec_root_sha256)
    parent_root = parent_contract_root(
        membership_sha256=membership_sha256,
        complete_manifest_sha256=complete_manifest_sha256,
        formula_spec_root_sha256=spec_root,
        derivation_code_sha256=derivation_code_sha256)

    root = immune_fraction_root(rows)
    registry = io.StringIO()
    writer = csv.writer(registry, lineterminator="\n")
    writer.writerow(["donor_id", "immune_n_donor", "total_op31_n_donor"])
    for row in rows:
        writer.writerow([str(row["donor_id"]), int(row["immune_n_donor"]),
                         int(row["total_op31_n_donor"])])
    registry_bytes = registry.getvalue().encode("utf-8")

    meta = {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "finalized": True,
        "primary_authority": "EXACT_INTEGER_NUMERATOR_AND_DENOMINATOR",
        "derived_quantity": "IMMUNE_FRACTION := immune_n_donor / total_op31_n_donor",
        "fraction_stored": False,
        "donor_count": len(rows),
        "immune_cell_total": sum(int(r["immune_n_donor"]) for r in rows),
        "op31_cell_total": sum(int(r["total_op31_n_donor"]) for r in rows),
        "immune_fraction_root_sha256": root,
        "membership_sha256": str(membership_sha256),
        "complete_manifest_sha256": str(complete_manifest_sha256),
        "complete_manifest_selection": (
            "AUTHENTICATE_COMPLETE_MANIFEST_THEN_SELECT_OPERATOR_31_INTERNALLY"),
        "selected_op31_blocks": int(selected_op31_blocks),
        "consumed_block_metadata_count": len(consumed_meta_sha256),
        "consumed_block_metadata_sha256": dict(sorted(consumed_meta_sha256.items())),
        "derivation_code_sha256": str(derivation_code_sha256),
        "derivation_code_byte_semantics": "GIT_BLOB_BYTES__NOT_WORKTREE_BYTES",
        "formula_spec_root_sha256": str(spec_root),
        "formula_spec_version": FORMULA_SPEC_VERSION,
        "parent_contract_root_sha256": parent_root,
        "parent_contract_members": [
            "membership_sha256", "complete_manifest_sha256",
            "formula_spec_root_sha256", "derivation_code_sha256"],
        "eligibility_role": (
            "NUISANCE_COVARIATE_FOR_CONFIRMATION_COMPOSITION_SENSITIVITY__"
            "NOT_AN_ELIGIBILITY_INPUT__MUST_NOT_FEED_TECHNICAL_COMPLETE"),
        "denominator_population": DENOMINATOR_POPULATION,
        "denominator_equals_reader_fit_partition": DENOMINATOR_EQUALS_READER_FIT_PARTITION,
        "denominator_population_evidence": (
            "The materialized op31 store holds 638150 cells, counted over all 1247 "
            "op31 block metadata files. The canonical foundation SQLite reports op31 "
            "partition composition reader_fit 638150, reader_validation 173736, "
            "reader_oracle 121386. The substrate is therefore exactly the reader_fit "
            "partition, which also confirms by count that reader_validation and "
            "reader_oracle are excluded. The SQLite was used only to corroborate this "
            "equality; this authority neither reads nor binds it."),
        "formula_specification_status": FORMULA_SPECIFICATION_STATUS,
        "formula_provenance": FORMULA_PROVENANCE,
        "pathology_values_read": False,
        "real_execution_ready": False,
    }
    meta_bytes = (json.dumps(meta, sort_keys=True, indent=2) + "\n").encode("utf-8")

    manifest = io.StringIO()
    mwriter = csv.writer(manifest, lineterminator="\n")
    mwriter.writerow(["filename", "bytes", "sha256"])
    for name, payload in ((REGISTRY, registry_bytes), (METADATA, meta_bytes)):
        mwriter.writerow([name, len(payload),
                          hashlib.sha256(payload).hexdigest()])
    manifest_bytes = manifest.getvalue().encode("utf-8")

    members = {REGISTRY: registry_bytes, METADATA: meta_bytes,
               MANIFEST: manifest_bytes}
    pkg_root = package_root(members)

    out.mkdir(parents=True, exist_ok=True)
    for name, payload in members.items():
        with io.open(out / name, "wb") as handle:
            handle.write(payload)
    with io.open(out / ROOT_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(pkg_root + "\n")

    return {
        "immune_fraction_root_sha256": root,
        "package_root_sha256": pkg_root,
        "parent_contract_root_sha256": parent_root,
        "formula_spec_root_sha256": spec_root,
        "selected_op31_blocks": int(selected_op31_blocks),
        "donor_count": len(rows),
        "immune_cell_total": meta["immune_cell_total"],
        "op31_cell_total": meta["op31_cell_total"],
        "real_execution_ready": False,
    }


def load_authority(
        outdir: Path | str,
        *,
        expected_package_root_sha256: str,
        expected_immune_fraction_root_sha256: str,
        expected_parent_contract_root_sha256: str | None = None,
        expected_membership_sha256: str | None = None,
        expected_complete_manifest_sha256: str | None = None,
        expected_formula_spec_root_sha256: str | None = None,
        expected_derivation_code_sha256: str | None = None,
) -> dict[str, Any]:
    """Read the authority back, binding every root it claims.

    Verifying only the two roots this package computes itself would leave the
    parents unbound: `stored == recomputed` can hold while both differ from what
    an external reviewer expects. So the caller must supply either the parent
    contract root or the individual parent identities, and for each root the
    verifier establishes

        stored == recomputed == externally expected

    Every member is read exactly once and all verification runs against those
    captured bytes. Re-opening a member to hash it and again to parse it would
    leave an interval in which the two reads could differ.
    """
    out = Path(outdir)
    captured: dict[str, bytes] = {}
    for name in MEMBERS:
        path = out / name
        if not path.is_file():
            raise AssertionError("%s: %s absent" % (STOP_PACKAGE_MEMBER, path))
        captured[name] = path.read_bytes()

    individual = {
        "membership_sha256": expected_membership_sha256,
        "complete_manifest_sha256": expected_complete_manifest_sha256,
        "formula_spec_root_sha256": expected_formula_spec_root_sha256,
        "derivation_code_sha256": expected_derivation_code_sha256,
    }
    if expected_parent_contract_root_sha256 is None and not any(individual.values()):
        raise AssertionError(
            "%s: supply either expected_parent_contract_root_sha256 or the "
            "individual parent identities; verifying only this package's own "
            "roots leaves its parents unbound" % STOP_PARENT_IDENTITY)

    pkg_root = package_root(captured)
    if pkg_root != str(expected_package_root_sha256):
        raise AssertionError("%s: package root is %s, expected %s"
                             % (STOP_ROOT_MISMATCH, pkg_root,
                                expected_package_root_sha256))

    columns, records = _rows(captured[REGISTRY])
    _require_columns(columns, ("donor_id", "immune_n_donor", "total_op31_n_donor"),
                     REGISTRY)
    rows = _build_immune_fraction_rows(
        numerator_by_donor={r["donor_id"]: r["immune_n_donor"] for r in records},
        denominator_by_donor={r["donor_id"]: r["total_op31_n_donor"]
                              for r in records},
    )
    root = immune_fraction_root(rows)
    if root != str(expected_immune_fraction_root_sha256):
        raise AssertionError("%s: immune fraction root is %s, expected %s"
                             % (STOP_ROOT_MISMATCH, root,
                                expected_immune_fraction_root_sha256))

    meta = json.loads(captured[METADATA].decode("utf-8"))
    if meta.get("schema") != SCHEMA or meta.get("finalized") is not True:
        raise AssertionError("%s: metadata schema or finalized flag invalid"
                             % STOP_FIELD_SCHEMA)
    if meta.get("immune_fraction_root_sha256") != root:
        raise AssertionError("%s: metadata records root %r but the registry yields %s"
                             % (STOP_ROOT_MISMATCH,
                                meta.get("immune_fraction_root_sha256"), root))
    if meta.get("fraction_stored") is not False:
        raise AssertionError(
            "%s: the fraction must not be stored; the integers are the authority"
            % STOP_FIELD_SCHEMA)
    if meta.get("real_execution_ready") is not False:
        raise AssertionError("%s: real_execution_ready must be False"
                             % STOP_FIELD_SCHEMA)

    # Each individual parent identity: stored == externally expected.
    for name, expected in individual.items():
        if expected is None:
            continue
        stored = meta.get(name)
        if str(stored) != str(expected):
            raise AssertionError("%s: %s is stored as %r but externally expected %r"
                                 % (STOP_PARENT_IDENTITY, name, stored, expected))

    # The parent contract root: stored == recomputed == externally expected.
    recomputed_parent = parent_contract_root(
        membership_sha256=str(meta.get("membership_sha256")),
        complete_manifest_sha256=str(meta.get("complete_manifest_sha256")),
        formula_spec_root_sha256=str(meta.get("formula_spec_root_sha256")),
        derivation_code_sha256=str(meta.get("derivation_code_sha256")))
    stored_parent = meta.get("parent_contract_root_sha256")
    if str(stored_parent) != recomputed_parent:
        raise AssertionError(
            "%s: the stored parent contract root %r does not match the root "
            "recomputed from the stored parent identities %s"
            % (STOP_PARENT_IDENTITY, stored_parent, recomputed_parent))
    if expected_parent_contract_root_sha256 is not None:
        if recomputed_parent != str(expected_parent_contract_root_sha256):
            raise AssertionError(
                "%s: parent contract root is %s, externally expected %s"
                % (STOP_PARENT_IDENTITY, recomputed_parent,
                   expected_parent_contract_root_sha256))

    # The formula specification the authority was built against must still be
    # the lawful frozen one.
    import t0_immune_fraction_formula_spec_v1 as formula_spec
    formula_spec.assert_spec_root(str(meta.get("formula_spec_root_sha256")))

    return {"rows": rows, "metadata": meta,
            "immune_fraction_root_sha256": root,
            "package_root_sha256": pkg_root,
            "parent_contract_root_sha256": recomputed_parent}
