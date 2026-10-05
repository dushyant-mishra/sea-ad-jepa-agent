"""Tests for the V2 exposure ledger successor.

Two things must hold that V1 alone could not express:

  1. Exposure and ACCESS are separate axes. Kosoy Hi-C is access-required and
     barely exposed; DS010 is embargoed and development-exposed. Encoding access
     as an exposure state would make each imply the other, and both implications
     are false.
  2. Exposure is MONOTONE. Once an outcome family has been seen it cannot be
     un-seen, and the ledger must refuse a regression rather than record one.

V1 must remain untouched — a successor that mutates its predecessor destroys the
reproducibility of every snapshot taken against it.
"""
from __future__ import annotations

import pytest

from sea_ad_jepa.regulatory import regulatory_exposure_ledger_v1 as V1
from sea_ad_jepa.regulatory import regulatory_exposure_ledger_v2 as V2
from sea_ad_jepa.regulatory.regulatory_exposure_ledger_v2 import (
    ABSTRACT_LEVEL, CONTROLLED_OR_ACCESS_REQUIRED, DEVELOPMENT, EMBARGOED,
    INSPECTED, OPEN_PUBLIC, STRUCTURAL_ONLY, UNKNOWN, AccessRecord,
    ExposureEventV2, RegulatoryExposureError, RegulatoryOutcomeKey,
    freeze_ledger_v2, seed_v63_exposure,
)


def test_v1_is_not_mutated():
    assert V1.SCHEMA == "JEPA_REGULATORY_OUTCOME_EXPOSURE_LEDGER_V1"
    assert V2.SUPERSEDES == V1.SCHEMA
    assert V2.SCHEMA != V1.SCHEMA
    # V1's lattice must not have gained the new state
    assert ABSTRACT_LEVEL not in V1.STATES
    assert ABSTRACT_LEVEL in V2.STATES_V2


def test_abstract_level_sits_between_structural_and_inspected():
    o = V2.ORDER
    assert o[STRUCTURAL_ONLY] < o[ABSTRACT_LEVEL] < o[INSPECTED] < o[DEVELOPMENT]


def test_exposure_is_monotone_and_regression_is_refused():
    K = RegulatoryOutcomeKey("S", "M", "F")
    ok = freeze_ledger_v2(
        [ExposureEventV2(K, ABSTRACT_LEVEL, "read the abstract only, no data inspected", "ref"),
         ExposureEventV2(K, DEVELOPMENT, "subsequently used during development work", "ref")],
        [AccessRecord("S", OPEN_PUBLIC, "ref")])
    assert ok.current()[K.tuple()] == DEVELOPMENT

    with pytest.raises(RegulatoryExposureError):
        freeze_ledger_v2(
            [ExposureEventV2(K, DEVELOPMENT, "used during development work here", "ref"),
             ExposureEventV2(K, ABSTRACT_LEVEL, "pretending we only saw the abstract", "ref")],
            [AccessRecord("S", OPEN_PUBLIC, "ref")])


def test_access_is_a_separate_axis_from_exposure():
    """The two must be independently settable in all four corners."""
    K = RegulatoryOutcomeKey("S", "M", "F")
    for exposure in (STRUCTURAL_ONLY, DEVELOPMENT):
        for access in (OPEN_PUBLIC, CONTROLLED_OR_ACCESS_REQUIRED):
            led = freeze_ledger_v2(
                [ExposureEventV2(K, exposure, "a substantive reason for this state", "ref")],
                [AccessRecord("S", access, "ref")])
            assert led.current()[K.tuple()] == exposure
            assert led.access_for("S").access_class == access


def test_load_bearing_is_fail_closed():
    """Anything not affirmatively OPEN_PUBLIC is refused, UNKNOWN included."""
    K = RegulatoryOutcomeKey("S", "M", "F")
    for access, allowed in ((OPEN_PUBLIC, True), (EMBARGOED, False),
                            (CONTROLLED_OR_ACCESS_REQUIRED, False), (UNKNOWN, False)):
        kw = {"scheduled_release": "2027-02-01"} if access == EMBARGOED else {}
        led = freeze_ledger_v2(
            [ExposureEventV2(K, STRUCTURAL_ONLY, "a substantive reason for this state", "r")],
            [AccessRecord("S", access, "r", **kw)])
        assert led.may_be_load_bearing("S")["allowed"] is allowed


def test_unrecorded_source_is_refused_not_permitted():
    led = seed_v63_exposure()
    out = led.may_be_load_bearing("SOME_SOURCE_NOBODY_AUDITED")
    assert out["allowed"] is False
    assert out["reason"] == "NO_ACCESS_RECORD__FAIL_CLOSED"


def test_embargo_requires_a_release_date():
    K = RegulatoryOutcomeKey("S", "M", "F")
    with pytest.raises(RegulatoryExposureError):
        freeze_ledger_v2(
            [ExposureEventV2(K, STRUCTURAL_ONLY, "a substantive reason for this state", "r")],
            [AccessRecord("S", EMBARGOED, "r")])


def test_v63_seed_records_the_required_task9_facts():
    led = seed_v63_exposure()
    cur = led.current()

    # DS010 published AD/control molecular outcomes -> DEVELOPMENT exposure
    assert cur[("DS010_WANG2025", "SNM3C_CONTACT",
                "AD_VS_CONTROL_LOOP_AND_COMPARTMENT")] == DEVELOPMENT
    assert cur[("DS010_WANG2025", "METHYLATION",
                "AD_VS_CONTROL_DIFFERENTIAL_METHYLATION")] == DEVELOPMENT

    # McQuade / GSE335887 -> ABSTRACT_LEVEL, not INSPECTED
    assert cur[("GSE335887_MCQUADE", "UNSPECIFIED",
                "PUBLISHED_ABSTRACT_CLAIMS")] == ABSTRACT_LEVEL

    # Kosoy Hi-C -> access-required, supporting only, and NOT load-bearing
    assert led.may_be_load_bearing("KOSOY2022_HIC")["allowed"] is False
    assert led.access_for("KOSOY2022_HIC").access_class == CONTROLLED_OR_ACCESS_REQUIRED

    # DS010 contact -> embargoed with the verified release date
    rec = led.access_for("DS010_WANG2025_CONTACT")
    assert rec.access_class == EMBARGOED and rec.scheduled_release == "2027-02-01"
    assert led.may_be_load_bearing("DS010_WANG2025_CONTACT")["allowed"] is False

    # Kosoy ATAC terms are UNVERIFIED -> must be refused, not assumed open
    assert led.access_for("KOSOY2022_ATAC").access_class == UNKNOWN
    assert led.may_be_load_bearing("KOSOY2022_ATAC")["allowed"] is False

    # NIH-CARD is open, and is a validation candidate only
    assert led.may_be_load_bearing("NIH_CARD_CATCHING2026")["allowed"] is True
    assert "VALIDATION CANDIDATE ONLY" in V2.CONSTRUCTION_PROHIBITIONS["NIH_CARD_CATCHING2026"]
    assert "must NEVER enter E2 construction" in \
        V2.CONSTRUCTION_PROHIBITIONS["NIH_CARD_CATCHING2026"]


def test_tian_li_vs_siletti_is_probable_not_proven():
    r = V2.cross_source_rule_v2("TIAN_LI", "SILETTI")
    assert r["determination"] == "PROBABLE_SHARED_DONORS"
    assert r["independent_confirmation_authorized"] is False
    assert "weaker than PROVEN" in r["binding_rule"]


def test_v1_cross_source_rules_are_inherited_unchanged():
    for pair in V1.CROSS_SOURCE_RULES:
        a, b = pair
        assert V2.cross_source_rule_v2(a, b)["determination"] == \
            V1.cross_source_rule(a, b)["determination"]


def test_unknown_pair_requires_audit_rather_than_defaulting_to_independent():
    r = V2.cross_source_rule_v2("SOME_COHORT", "ANOTHER_COHORT")
    assert r["determination"] == "UNKNOWN_REQUIRES_AUDIT"
    assert r["independent_confirmation_authorized"] is False


def test_ledger_digest_is_stable_and_content_addressed():
    a, b = seed_v63_exposure(), seed_v63_exposure()
    assert a.ledger_sha256 == b.ledger_sha256
    K = RegulatoryOutcomeKey("EXTRA", "M", "F")
    c = freeze_ledger_v2(
        list(a.events) + [ExposureEventV2(K, STRUCTURAL_ONLY,
                                          "an additional substantive reason here", "r")],
        list(a.access))
    assert c.ledger_sha256 != a.ledger_sha256


def test_duplicate_access_records_are_refused():
    K = RegulatoryOutcomeKey("S", "M", "F")
    with pytest.raises(RegulatoryExposureError):
        freeze_ledger_v2(
            [ExposureEventV2(K, STRUCTURAL_ONLY, "a substantive reason for this state", "r")],
            [AccessRecord("S", OPEN_PUBLIC, "r"), AccessRecord("S", EMBARGOED, "r",
                                                               scheduled_release="2027-02-01")])
