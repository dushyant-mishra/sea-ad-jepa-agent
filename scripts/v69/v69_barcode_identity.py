#!/usr/bin/env python3
"""V69 shared barcode-identity guard — ENFORCED, not merely documented.

GSE214979 aggregates multiple libraries, and its barcode suffixes are NOT one-to-one
with donors. Measured on the frozen cohort:

    suffix 5 -> {4313, 4482}
    suffix 6 -> {HCT17HEX, HCTZZT}
    suffix 7 -> {4305, 4443}

So `AAACAGCCAAACCCTA-5` does not identify a donor. Any producer that derives donor
identity from the suffix will silently merge two donors into one pseudobulk, which
would corrupt donor-aware peak calling and make leave-one-donor-out meaningless --
while looking perfectly normal in every summary statistic.

A guard recorded in a receipt is documentation. This module exists so the guard lives
in the code that actually reads barcodes. Every V69 producer that maps barcodes to
donors calls `assert_donor_map_is_not_suffix_derived` and fails closed.
"""
from __future__ import annotations

from collections import defaultdict


class BarcodeIdentityError(Exception):
    """Raised when a donor mapping is, or could be, suffix-derived."""


def suffix_of(barcode: str) -> str:
    """The aggregation suffix. Identifies a 10x library slot, NOT a donor."""
    return str(barcode).rsplit("-", 1)[-1]


def suffixes_carrying_multiple_donors(barcode_to_donor: dict) -> dict:
    """Which aggregation suffixes span more than one donor, with the donors."""
    by_suffix = defaultdict(set)
    for bc, donor in barcode_to_donor.items():
        by_suffix[suffix_of(bc)].add(str(donor))
    return {s: sorted(d) for s, d in by_suffix.items() if len(d) > 1}


def assert_donor_map_is_not_suffix_derived(barcode_to_donor: dict,
                                          authority_evidence: dict | None = None) -> dict:
    """Fail closed if the donor mapping is suffix-derived, or if it is indistinguishable
    from one.

    Two distinct failures are caught:

    1. The mapping is literally suffix-derived: every barcode sharing a suffix has the
       same donor. In THIS cohort that is impossible for a correct mapping, because
       three suffixes genuinely span two donors each. So a mapping with no
       multi-donor suffix has either been built from the suffix or been restricted to
       a subset where the distinction vanished -- and in both cases downstream
       donor-aware work would be wrong or unverifiable.

    A barcode bound to two donors is NOT detectable here and never was; see the
    V74 note in the body. Pass `authority_evidence` from
    `audit_barcode_authority_frame` so the receipt records that the only check capable
    of catching it actually ran.

    Returns the evidence dict for the caller's receipt.
    """
    if not barcode_to_donor:
        raise BarcodeIdentityError(
            "FAIL__EMPTY_BARCODE_TO_DONOR_MAP: cannot verify donor identity")

    # V74 DEFECT REPAIR. This guard previously looped over barcode_to_donor.items()
    # looking for a barcode bound to two donors. That check COULD NOT FAIL: a dict has
    # one value per key, so by the time the mapping reaches this function any conflict
    # has already been destroyed by whatever built it (typically dict(zip(...)), which
    # silently keeps the LAST row). The check has been removed rather than left in
    # place looking like protection. The conflict is detectable only in the source
    # table, before collapse, which is what audit_barcode_authority_frame does --
    # callers pass its evidence here so a receipt shows whether that audit ran.
    if authority_evidence is None:
        authority_audit = {
            "performed": False,
            "why_it_matters": (
                "Without a pre-collapse audit of the source table, a barcode bound to "
                "two donors is silently resolved to one by dict(zip(...)) and cannot "
                "be detected downstream. Absence of a conflict in this mapping is "
                "therefore not evidence that no conflict existed."),
        }
    else:
        authority_audit = dict(authority_evidence)
        authority_audit["performed"] = True

    multi = suffixes_carrying_multiple_donors(barcode_to_donor)
    evidence = {
        "rule": ("Donor identity comes ONLY from the metadata keyed on the FULL "
                 "barcode string. Suffix-based donor inference is a defect."),
        "n_barcodes": len(barcode_to_donor),
        "n_donors": len({str(v) for v in barcode_to_donor.values()}),
        "n_suffixes": len({suffix_of(b) for b in barcode_to_donor}),
        "suffixes_carrying_more_than_one_donor": multi,
        "suffix_is_a_valid_donor_key": False,
        "guard": "ENFORCED_IN_CODE",
        "pre_collapse_authority_audit": authority_audit,
    }
    if not multi:
        raise BarcodeIdentityError(
            "FAIL__DONOR_MAP_INDISTINGUISHABLE_FROM_SUFFIX_DERIVED: no aggregation "
            "suffix spans more than one donor. In the GSE214979 cohort suffixes 5, 6 "
            "and 7 each span two donors, so a correct full-cohort mapping must show "
            "multi-donor suffixes. Either the mapping was derived from the suffix, or "
            "it covers a subset where the distinction cannot be checked; donor-aware "
            "work must not proceed on an unverifiable mapping.")
    return evidence


def donor_of(barcode: str, barcode_to_donor: dict) -> str:
    """Look up a donor. Refuses to guess from the suffix when the barcode is absent."""
    try:
        return barcode_to_donor[barcode]
    except KeyError:
        raise BarcodeIdentityError(
            "FAIL__BARCODE_NOT_IN_COHORT_MAP: %r has no donor assignment. It must be "
            "discarded and counted, never assigned a donor from its suffix." % barcode)


# ---------------------------------------------------------------------------------
# V74 REPAIR: audit the barcode authority BEFORE it is collapsed into a dict.
#
# `dict(zip(df["barcode"], df["donor"]))` is a lossy operation with no diagnostic. If
# one barcode appears twice with two different donors, the dict keeps whichever row
# came last, the conflict disappears, and every downstream check -- including the
# suffix guard above -- sees a well-formed mapping. The cohort's own QC receipt already
# shows that three aggregation suffixes carry two donors each, so barcode identity in
# this dataset is exactly the thing that must not be guessed at or quietly resolved.
#
# POLICY, stated once and enforced here:
#   * EXACT duplicate rows (barcode, donor and subcluster all identical) are BENIGN.
#     They are collapsed to a single row and the number collapsed is recorded. They
#     carry no contradictory information.
#   * A barcode bound to more than one DONOR fails closed.
#   * A barcode bound to more than one SUBCLUSTER fails closed.
#   * A missing, null or blank barcode, donor or subcluster fails closed. A structurally
#     absent identifier is not a value and must never be coerced to "" or to a default.
#   * An empty authority table fails closed.
# ---------------------------------------------------------------------------------

_BLANKS = {"", "nan", "none", "null", "na", "<na>"}


class BarcodeAuthorityError(BarcodeIdentityError):
    """A barcode authority table that cannot be collapsed without losing information."""

    def __init__(self, status: str, **detail):
        super().__init__(status + (": " + repr(detail) if detail else ""))
        self.status = status
        self.detail = detail


def _blank(v) -> bool:
    return v is None or str(v).strip().lower() in _BLANKS


def audit_barcode_authority_rows(rows) -> tuple:
    """Audit (barcode, donor, subcluster) triples before any dictionary collapse.

    Returns (barcode_to_donor, barcode_to_subcluster, evidence).
    Raises BarcodeAuthorityError, which carries a named `.status`, on any conflict.
    """
    rows = [tuple(r) for r in rows]
    if not rows:
        raise BarcodeAuthorityError(
            "FAIL__BARCODE_AUTHORITY_IS_EMPTY",
            note="An empty authority cannot establish donor identity for any cell.")

    blanks = [i for i, r in enumerate(rows) if any(_blank(x) for x in r)]
    if blanks:
        raise BarcodeAuthorityError(
            "FAIL__BARCODE_AUTHORITY_HAS_NULL_OR_BLANK_IDENTIFIERS",
            n_offending_rows=len(blanks), first_offending_row_indices=blanks[:10],
            note=("A blank barcode, donor or subcluster is a structural absence. It is "
                  "not a measured value and must not be coerced into one."))

    norm = [(str(b).strip(), str(d).strip(), str(s).strip()) for b, d, s in rows]

    by_bc_donor, by_bc_sub, seen_rows = {}, {}, {}
    for b, d, s in norm:
        by_bc_donor.setdefault(b, set()).add(d)
        by_bc_sub.setdefault(b, set()).add(s)
        seen_rows[(b, d, s)] = seen_rows.get((b, d, s), 0) + 1

    conflict_donor = {b: sorted(v) for b, v in by_bc_donor.items() if len(v) > 1}
    if conflict_donor:
        raise BarcodeAuthorityError(
            "FAIL__BARCODE_MAPS_TO_MULTIPLE_DONORS",
            n_conflicting_barcodes=len(conflict_donor),
            examples=dict(sorted(conflict_donor.items())[:10]),
            note=("dict(zip(barcode, donor)) would have silently kept the last row and "
                  "assigned these cells to one donor. Donor-aware peak calling and "
                  "leave-one-donor-out would both be wrong and would look normal."))

    conflict_sub = {b: sorted(v) for b, v in by_bc_sub.items() if len(v) > 1}
    if conflict_sub:
        raise BarcodeAuthorityError(
            "FAIL__BARCODE_MAPS_TO_MULTIPLE_SUBCLUSTERS",
            n_conflicting_barcodes=len(conflict_sub),
            examples=dict(sorted(conflict_sub.items())[:10]),
            note=("The pseudobulk unit is donor x subcluster, so an ambiguous "
                  "subcluster makes the pseudobulk assignment ambiguous."))

    n_exact_dupes = sum(c - 1 for c in seen_rows.values() if c > 1)
    barcode_to_donor = {b: next(iter(v)) for b, v in by_bc_donor.items()}
    barcode_to_sub = {b: next(iter(v)) for b, v in by_bc_sub.items()}

    evidence = {
        "audit": "V74_BARCODE_AUTHORITY_PRE_COLLAPSE_AUDIT_V1",
        "n_rows_in": len(rows),
        "n_distinct_barcodes": len(barcode_to_donor),
        "n_exact_duplicate_rows_collapsed": n_exact_dupes,
        "exact_duplicate_policy": (
            "COLLAPSE_EXACT_DUPLICATE_ROWS -- benign, because barcode, donor and "
            "subcluster all agree. The number collapsed is recorded, never hidden."),
        "conflicting_duplicate_policy": (
            "FAIL_CLOSED -- a barcode bound to more than one donor or more than one "
            "subcluster stops the run. It is never resolved by position, by order, or "
            "by taking the last row."),
        "n_barcodes_with_conflicting_donor": 0,
        "n_barcodes_with_conflicting_subcluster": 0,
        "null_or_blank_identifier_policy": "FAIL_CLOSED",
    }
    return barcode_to_donor, barcode_to_sub, evidence


def audit_barcode_authority_frame(df, barcode_col="barcode", donor_col="donor",
                                  subcluster_col="subcluster") -> tuple:
    """pandas adapter for `audit_barcode_authority_rows`."""
    missing = [c for c in (barcode_col, donor_col, subcluster_col)
               if c not in getattr(df, "columns", [])]
    if missing:
        raise BarcodeAuthorityError(
            "FAIL__BARCODE_AUTHORITY_MISSING_COLUMN", missing_columns=missing,
            present_columns=list(getattr(df, "columns", [])))
    rows = list(zip(df[barcode_col].tolist(), df[donor_col].tolist(),
                    df[subcluster_col].tolist()))
    return audit_barcode_authority_rows(rows)
