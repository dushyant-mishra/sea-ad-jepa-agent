"""Frozen successor specification for the T0 donor IMMUNE_FRACTION covariate.

Status
------
This is an EXPLICIT SUCCESSOR SPECIFICATION resolving an undefined required
input. It is NOT recovered executable V18 semantics, and nothing here may be
presented as such.

V18 SS170 names "donor `IMMUNE_FRACTION` within op31 MTG" in prose and
`t0_adjudicator_v1` requires `IMMUNE_FRACTION` as a mandatory base column, but no
frozen executable definition of the ratio exists anywhere in the accepted
package. The covariate was therefore a required input with no definition, in the
same class as `technical_complete`, and it is resolved the same way: by an
explicit owner-frozen successor specification recorded before any production
authority is built against it.

The specification
-----------------
    IMMUNE_FRACTION(d) = immune_n_donor(d) / total_op31_n_donor(d)

    immune_n_donor(d)      accepted broad-IMMUNE reader-fit cells for donor d
    total_op31_n_donor(d)  all authenticated Phase2 op31 reader-fit cells for d

Both terms are exact non-negative integers. The integers are the authority and
the quotient is derived at the consumption boundary, so the frozen quantity does
not depend on binary floating-point formatting and both counts stay auditable.

Why the denominator needs no partition column
---------------------------------------------
`partition` is not a column of the Phase2 block metadata; it exists only in the
canonical foundation SQLite. So "reader-fit op31 cells" looked as though it might
not be derivable from the authenticated substrate.

It is, because the materialized Phase2 op31 store IS the reader_fit substrate:

    op31 reader_fit          638,150
    op31 reader_validation   173,736   excluded from the store
    op31 reader_oracle       121,386   excluded from the store
    op31 all partitions      933,272

and an independent scan of all 1,247 operator-31 block metadata files counts
exactly 638,150 cells. "All Phase2 op31 cells" and "all reader-fit op31 cells"
therefore denote the same population, the denominator is derivable from bytes the
authority already authenticates, and no dependency on the large external SQLite
enters the T0 graph. The same equality is an independent by-count confirmation
that the store excludes the reader-validation and reader-oracle partitions, which
is what its `no_validation_oracle_dev_sealed_pathology` flag asserts.

Scope
-----
`IMMUNE_FRACTION` is a nuisance covariate for the confirmation composition
sensitivity. It is not an eligibility input and must never feed
`technical_complete`.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

SCHEMA = "JEPA_T0_IMMUNE_FRACTION_FORMULA_SPEC_V1"
NAMESPACE = "T0-IMMUNE-FRACTION-FORMULA-V1"
DOMAIN_TAG = "T0-IMMUNE-FRACTION-FORMULA-SPEC-V1-TYPED-LENGTH-PREFIXED"
VERSION = "1.0.0"

STOP_SPEC_ROOT = "STOP_T0_IMMUNE_FRACTION_FORMULA_SPEC_ROOT_MISMATCH"
STOP_SPEC_FIELD = "STOP_T0_IMMUNE_FRACTION_FORMULA_SPEC_FIELD_VIOLATION"
STOP_SPEC_PROVENANCE = "STOP_T0_IMMUNE_FRACTION_FORMULA_SPEC_PROVENANCE_MISDECLARED"

# --- the frozen specification ----------------------------------------------

SPECIFICATION_STATUS = "EXPLICIT_SUCCESSOR_SPECIFICATION__RESOLVES_UNDEFINED_REQUIRED_INPUT"
RECOVERED_FROM_FROZEN_EXECUTABLE_V18 = False

FORMULA = "IMMUNE_FRACTION(d) = immune_n_donor(d) / total_op31_n_donor(d)"

NUMERATOR_DEFINITION = (
    "accepted broad-IMMUNE reader-fit cells for donor d, counted from the "
    "accepted immune membership authority")
DENOMINATOR_DEFINITION = (
    "all authenticated Phase2 operator-31 reader-fit cells for donor d, counted "
    "from the operator-31 subset selected internally from the authenticated "
    "complete Phase2 block manifest")

PRIMARY_AUTHORITY = "EXACT_INTEGER_NUMERATOR_AND_DENOMINATOR"
DERIVED_QUANTITY = "QUOTIENT_COMPUTED_AT_THE_CONSUMPTION_BOUNDARY"
FRACTION_STORED = False

# The substrate fact the specification depends on, bound so it cannot drift.
PHASE2_SUBSTRATE_IS_READER_FIT = True
SUBSTRATE_EXCLUDES = ("reader_validation", "reader_oracle")
OP31_READER_FIT_CELLS = 638_150
OP31_READER_VALIDATION_CELLS = 173_736
OP31_READER_ORACLE_CELLS = 121_386
OP31_ALL_PARTITION_CELLS = 933_272

SUBSTRATE_EVIDENCE = (
    "The canonical foundation SQLite reports operator-31 partition composition "
    "reader_fit 638150, reader_validation 173736, reader_oracle 121386, totalling "
    "933272. An independent scan of all 1247 operator-31 Phase2 block metadata "
    "files counts exactly 638150 cells. The materialized substrate is therefore "
    "exactly the reader_fit partition, so 'all Phase2 op31 cells' and 'all "
    "reader-fit op31 cells' denote one population and the denominator is "
    "derivable without the external SQLite. The equality also confirms by count "
    "that the store excludes the reader-validation and reader-oracle partitions."
)

CONSUMPTION_SCOPE = (
    "NUISANCE_COVARIATE_FOR_CONFIRMATION_COMPOSITION_SENSITIVITY__"
    "NOT_AN_ELIGIBILITY_INPUT__MUST_NOT_FEED_TECHNICAL_COMPLETE")

PROVENANCE_NOTE = (
    "V18 SS170 states the covariate in prose and t0_adjudicator_v1 requires the "
    "column, but no frozen executable definition of the ratio exists in the "
    "accepted package. This specification supplies one explicitly. It resolves an "
    "undefined required input and must never be described as recovered V18 "
    "executable semantics."
)

# Production geometry the specification expects of a lawful authority.
EXPECTED_DONORS = 46
EXPECTED_NUMERATOR_TOTAL = 20_804
EXPECTED_DENOMINATOR_TOTAL = 638_150


def _typed(value: Any) -> bytes:
    """Type-tagged, length-prefixed framing; injective over the declared types."""
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
        raise AssertionError("%s: cannot frame %r" % (STOP_SPEC_FIELD, type(value)))
    return b"%s%d:%s" % (tag, len(payload), payload)


def specification() -> dict[str, Any]:
    """The frozen specification as an explicit mapping."""
    return {
        "schema": SCHEMA,
        "namespace": NAMESPACE,
        "version": VERSION,
        "specification_status": SPECIFICATION_STATUS,
        "recovered_from_frozen_executable_v18": RECOVERED_FROM_FROZEN_EXECUTABLE_V18,
        "formula": FORMULA,
        "numerator_definition": NUMERATOR_DEFINITION,
        "denominator_definition": DENOMINATOR_DEFINITION,
        "primary_authority": PRIMARY_AUTHORITY,
        "derived_quantity": DERIVED_QUANTITY,
        "fraction_stored": FRACTION_STORED,
        "phase2_substrate_is_reader_fit": PHASE2_SUBSTRATE_IS_READER_FIT,
        "substrate_excludes": list(SUBSTRATE_EXCLUDES),
        "op31_reader_fit_cells": OP31_READER_FIT_CELLS,
        "op31_reader_validation_cells": OP31_READER_VALIDATION_CELLS,
        "op31_reader_oracle_cells": OP31_READER_ORACLE_CELLS,
        "op31_all_partition_cells": OP31_ALL_PARTITION_CELLS,
        "substrate_evidence": SUBSTRATE_EVIDENCE,
        "consumption_scope": CONSUMPTION_SCOPE,
        "provenance_note": PROVENANCE_NOTE,
        "expected_donors": EXPECTED_DONORS,
        "expected_numerator_total": EXPECTED_NUMERATOR_TOTAL,
        "expected_denominator_total": EXPECTED_DENOMINATOR_TOTAL,
    }


def formula_spec_root() -> str:
    """Digest of the frozen specification, over injectively framed bytes."""
    spec = specification()
    parts = [_typed(DOMAIN_TAG), _typed(len(spec))]
    for key in sorted(spec):
        parts.append(_typed([key, spec[key]]))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def assert_specification_lawful() -> bool:
    """Guard the properties that make this specification safe to build against."""
    if RECOVERED_FROM_FROZEN_EXECUTABLE_V18 is not False:
        raise AssertionError(
            "%s: this specification must never claim to be recovered V18 "
            "executable semantics" % STOP_SPEC_PROVENANCE)
    if not SPECIFICATION_STATUS.startswith("EXPLICIT_SUCCESSOR_SPECIFICATION"):
        raise AssertionError("%s: status is %r"
                             % (STOP_SPEC_PROVENANCE, SPECIFICATION_STATUS))
    if FRACTION_STORED is not False:
        raise AssertionError(
            "%s: the integers are the authority; the fraction must be derived"
            % STOP_SPEC_FIELD)
    if PHASE2_SUBSTRATE_IS_READER_FIT is not True:
        raise AssertionError(
            "%s: the denominator derivation depends on the substrate being the "
            "reader-fit partition" % STOP_SPEC_FIELD)
    if tuple(SUBSTRATE_EXCLUDES) != ("reader_validation", "reader_oracle"):
        raise AssertionError("%s: substrate exclusions are %r"
                             % (STOP_SPEC_FIELD, SUBSTRATE_EXCLUDES))
    # The partition arithmetic must close, or the substrate claim is unsupported.
    total = (OP31_READER_FIT_CELLS + OP31_READER_VALIDATION_CELLS
             + OP31_READER_ORACLE_CELLS)
    if total != OP31_ALL_PARTITION_CELLS:
        raise AssertionError(
            "%s: partition counts sum to %d but all-partition total is %d"
            % (STOP_SPEC_FIELD, total, OP31_ALL_PARTITION_CELLS))
    if OP31_READER_FIT_CELLS != EXPECTED_DENOMINATOR_TOTAL:
        raise AssertionError(
            "%s: the reader-fit population is %d but the expected denominator "
            "total is %d" % (STOP_SPEC_FIELD, OP31_READER_FIT_CELLS,
                             EXPECTED_DENOMINATOR_TOTAL))
    if "MUST_NOT_FEED_TECHNICAL_COMPLETE" not in CONSUMPTION_SCOPE:
        raise AssertionError(
            "%s: the covariate must be declared out of scope for eligibility"
            % STOP_SPEC_FIELD)
    return True


def assert_spec_root(expected_root_sha256: str) -> bool:
    """Bind an externally supplied expectation of the specification root."""
    assert_specification_lawful()
    actual = formula_spec_root()
    if actual != str(expected_root_sha256):
        raise AssertionError("%s: specification root is %s, expected %s"
                             % (STOP_SPEC_ROOT, actual, expected_root_sha256))
    return True


def assert_authority_matches_specification(rows: Mapping[str, Any] | list) -> bool:
    """Check a candidate authority's totals against the frozen expectations."""
    entries = list(rows)
    donors = [str(r["donor_id"]) for r in entries]
    if len(donors) != len(set(donors)):
        raise AssertionError("%s: duplicate donor in the authority" % STOP_SPEC_FIELD)
    if len(entries) != EXPECTED_DONORS:
        raise AssertionError("%s: %d donors, specification expects %d"
                             % (STOP_SPEC_FIELD, len(entries), EXPECTED_DONORS))
    numerator = sum(int(r["immune_n_donor"]) for r in entries)
    denominator = sum(int(r["total_op31_n_donor"]) for r in entries)
    if numerator != EXPECTED_NUMERATOR_TOTAL:
        raise AssertionError("%s: numerator total %d, specification expects %d"
                             % (STOP_SPEC_FIELD, numerator, EXPECTED_NUMERATOR_TOTAL))
    if denominator != EXPECTED_DENOMINATOR_TOTAL:
        raise AssertionError("%s: denominator total %d, specification expects %d"
                             % (STOP_SPEC_FIELD, denominator,
                                EXPECTED_DENOMINATOR_TOTAL))
    return True
