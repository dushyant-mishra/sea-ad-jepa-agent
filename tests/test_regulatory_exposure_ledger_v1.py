import dataclasses
import pytest

from sea_ad_jepa.regulatory.regulatory_exposure_ledger_v1 import *


def test_seeded_outcome_families_are_granular_and_unknown_does_not_inherit():
    ledger = seed_historical_regulatory_exposure()
    assert ledger.status(RegulatoryOutcomeKey(
        "GSE174367_MORABITO", "RNA", "MICROGLIA_PSEUDOBULK_TF_TARGET_COACTIVITY"
    )) == DEVELOPMENT
    assert ledger.status(RegulatoryOutcomeKey(
        "GSE174367_MORABITO", "ATAC", "MARGINAL_ACCESSIBILITY_AND_COVERAGE"
    )) == INSPECTED

    # Exposure does not propagate from another modality/outcome family.
    assert ledger.status(RegulatoryOutcomeKey(
        "GSE174367_MORABITO", "ATAC", "TARGET_STATE_CIS_CORRESPONDENCE"
    )) == UNKNOWN
    assert ledger.status(RegulatoryOutcomeKey(
        "GSE214979", "MOLECULAR", "REGULATORY_RNA_ATAC_COVARIANCE"
    )) == UNKNOWN
    assert ledger.status(RegulatoryOutcomeKey(
        "GSE272082", "MOLECULAR", "REGULATORY_RNA_ATAC_COVARIANCE"
    )) == UNKNOWN
    assert ledger.status(RegulatoryOutcomeKey(
        "SEAAD_PUBLIC_MULTIOME", "ATAC", "TARGET_STATE_CIS_CORRESPONDENCE"
    )) == UNKNOWN
    assert ledger.status(RegulatoryOutcomeKey(
        "SEAAD_SPATIAL", "RNA", "TARGET_PROGRAM_SPATIAL_EXPRESSION"
    )) == UNKNOWN


def test_exposure_cannot_regress():
    ledger = seed_historical_regulatory_exposure()
    with pytest.raises(RegulatoryExposureError):
        append_event(ledger, ExposureEvent(
            RegulatoryOutcomeKey("FULL104", "RNA", "RELATIONAL_STATE_TD56_TD59"),
            STRUCTURAL_ONLY,
            "Attempt to relabel development evidence as merely structural.",
            "MUTATION",
        ))
    with pytest.raises(RegulatoryExposureError):
        append_event(ledger, ExposureEvent(
            RegulatoryOutcomeKey(
                "GSE174367_MORABITO", "ATAC", "MARGINAL_ACCESSIBILITY_AND_COVERAGE"
            ),
            STRUCTURAL_ONLY,
            "Attempt to downgrade an inspected ATAC outcome family.",
            "MUTATION",
        ))


def test_unknown_can_transition_to_development_but_never_self_authorizes_confirmation():
    ledger = seed_historical_regulatory_exposure()
    key = RegulatoryOutcomeKey(
        "GSE214979", "MOLECULAR", "REGULATORY_RNA_ATAC_COVARIANCE"
    )
    guard = guard_role(ledger, key, ROLE_CONFIRMATION_CANDIDATE)
    assert guard["role_state"] == "REQUIRES_SEPARATE_PHYSICAL_OUTCOME_SEAL"
    assert guard["prospective_confirmation_authorized"] is False

    ledger = append_event(ledger, ExposureEvent(
        key,
        DEVELOPMENT,
        "Synthetic test fixture for transition semantics; represents future use as development.",
        "TEST_ONLY",
    ))
    guard = guard_role(ledger, key, ROLE_CONFIRMATION_CANDIDATE)
    assert guard["role_state"] == "BLOCKED_ALREADY_EXPOSED"
    assert guard["prospective_confirmation_authorized"] is False


def test_spatial_technical_inspection_does_not_mark_target_program_expression_exposed():
    ledger = seed_historical_regulatory_exposure()
    assert ledger.status(RegulatoryOutcomeKey(
        "SEAAD_SPATIAL", "TECHNICAL", "DETECTION_AND_SEGMENTATION_METRICS"
    )) == INSPECTED
    assert ledger.status(RegulatoryOutcomeKey(
        "SEAAD_SPATIAL", "RNA", "TARGET_PROGRAM_SPATIAL_EXPRESSION"
    )) == UNKNOWN


def test_regulatory_object_cannot_confirm_on_its_own_construction_source():
    obj = RegulatoryObjectProvenance(
        object_id="EXAMPLE_GSE214979_CIS_MODULES",
        method="frozen cis module construction",
        construction_sources=(
            RegulatoryOutcomeKey(
                "GSE214979", "MOLECULAR", "REGULATORY_RNA_ATAC_COVARIANCE"
            ),
        ),
        uses_full104=False,
        uses_same_nucleus_pairing=True,
        uses_pathology_or_diagnosis=False,
    )
    assert obj.assessment_against("GSE214979")["state"] ==         "NOT_INDEPENDENT__CONSTRUCTION_SOURCE"
    assert obj.assessment_against("GSE174367_MORABITO")["state"] ==         "REQUIRES_SEPARATE_INDEPENDENCE_AND_OUTCOME_SEAL_AUDIT"


def test_cross_source_rules_fail_closed_and_preserve_uci_overlap_caveat():
    rule = cross_source_rule("GSE214979", "GSE174367_MORABITO")
    assert rule["determination"] == "UNDETERMINED_POSSIBLE_UCI_DONOR_OVERLAP"
    assert "1224,1230,1238" in rule["binding_rule"]
    assert cross_source_rule(
        "FULL104", "SEAAD_PUBLIC_MULTIOME"
    )["determination"].startswith("NOT_INDEPENDENT")
    assert cross_source_rule(
        "UNKNOWN_A", "UNKNOWN_B"
    )["determination"] == "UNKNOWN_REQUIRES_AUDIT"


def test_digest_mutation_is_detected():
    ledger = seed_historical_regulatory_exposure()
    bad = dataclasses.replace(ledger, ledger_sha256="0" * 64)
    with pytest.raises(RegulatoryExposureError):
        bad.validate()
