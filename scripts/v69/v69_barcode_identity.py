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


def assert_donor_map_is_not_suffix_derived(barcode_to_donor: dict) -> dict:
    """Fail closed if the donor mapping is suffix-derived, or if it is indistinguishable
    from one.

    Two distinct failures are caught:

    1. The mapping is literally suffix-derived: every barcode sharing a suffix has the
       same donor. In THIS cohort that is impossible for a correct mapping, because
       three suffixes genuinely span two donors each. So a mapping with no
       multi-donor suffix has either been built from the suffix or been restricted to
       a subset where the distinction vanished -- and in both cases downstream
       donor-aware work would be wrong or unverifiable.

    2. A single barcode maps to more than one donor, which makes the mapping ill-formed.

    Returns the evidence dict for the caller's receipt.
    """
    if not barcode_to_donor:
        raise BarcodeIdentityError(
            "FAIL__EMPTY_BARCODE_TO_DONOR_MAP: cannot verify donor identity")

    seen = {}
    for bc, donor in barcode_to_donor.items():
        d = str(donor)
        if bc in seen and seen[bc] != d:
            raise BarcodeIdentityError(
                "FAIL__BARCODE_MAPS_TO_MULTIPLE_DONORS: %r -> %r and %r"
                % (bc, seen[bc], d))
        seen[bc] = d

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
