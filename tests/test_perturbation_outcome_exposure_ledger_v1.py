"""Synthetic mechanics and real known-exposure metadata, no molecular outcomes opened."""
from dataclasses import replace
import pytest

from sea_ad_jepa.perturbation.outcome_exposure_ledger_v1 import (
    DECLARED_UNINSPECTED, DEVELOPMENT, INSPECTED, UNKNOWN,
    ExposureError, ExposureEvent, OutcomeKey, append_event,
    freeze_ledger, seed_historical_exposure, guard_descriptive_benchmark,
)


def event(key, status, ref="FROZEN_FICTITIOUS_REVIEW_RECORD"):
    return ExposureEvent(key, status,
        "Synthetic exposure state transition: tested without inspecting outcomes.",
        ref)


def test_existing_six_outcome_families_cannot_be_marked_untouched():
    frozen = seed_historical_exposure()
    keys = [
        OutcomeKey("GSE301119", "CRISPRa", "target_engagement"),
        OutcomeKey("GSE301119", "CRISPRi", "target_engagement"),
        OutcomeKey("GSE293118", "HMC3_noncoding_CRISPRi", "target_engagement"),
        OutcomeKey("GSE254205", "bulk_GNE317", "AB_vs_NT"),
        OutcomeKey("GSE254205", "bulk_GNE317", "AB_GNE_vs_AB"),
        OutcomeKey("GSE254205", "bulk_GNE317", "AB_GNE_vs_NT"),
    ]
    for key in keys:
        assert frozen.status(key) == INSPECTED
        s = frozen.evaluation_scope(key)
        assert s["historically_inspected"]
        assert not s["untouched_external_confirmation_authorized"]
        with pytest.raises(ExposureError, match="forbidden exposure regression"):
            append_event(frozen, event(key, DECLARED_UNINSPECTED))


def test_other_arm_is_not_assumed_uninspected_or_inspected():
    frozen = seed_historical_exposure()
    other = OutcomeKey("GSE254205", "ATAC", "chromatin_response")
    assert frozen.status(other) == UNKNOWN
    assert not frozen.evaluation_scope(other)["retrospective_reporting_allowed"]
    assert not frozen.evaluation_scope(other)["untouched_external_confirmation_authorized"]


def test_declared_uninspected_never_certifies_independent_confirmation():
    base = seed_historical_exposure()
    key = OutcomeKey("SYNTHETIC_ONLY_STUDY", "SYNTHETIC_ARM", "response")
    declared = append_event(base, event(key, DECLARED_UNINSPECTED))
    assert declared.status(key) == DECLARED_UNINSPECTED
    assert not declared.evaluation_scope(key)["untouched_external_confirmation_authorized"]
    inspected = append_event(declared, event(key, INSPECTED))
    assert inspected.status(key) == INSPECTED
    with pytest.raises(ExposureError, match="forbidden exposure regression"):
        append_event(inspected, event(key, DECLARED_UNINSPECTED))
    dev = append_event(inspected, event(key, DEVELOPMENT))
    assert dev.status(key) == DEVELOPMENT
    with pytest.raises(ExposureError, match="forbidden exposure regression"):
        append_event(dev, event(key, INSPECTED))


def test_exposure_is_per_arm_and_outcome_not_entire_study():
    ledger = seed_historical_exposure()
    key = OutcomeKey("GSE301119", "CRISPRa", "transcriptome_wide_DE")
    assert ledger.status(key) == UNKNOWN
    assert ledger.status(OutcomeKey(
        "GSE301119", "CRISPRa", "target_engagement",
    )) == INSPECTED
    assert ledger.status(OutcomeKey(
        "GSE301119", "CRISPRi", "transcriptome_wide_DE",
    )) == UNKNOWN


def test_reordered_or_tampered_events_cannot_reuse_ledger_digest():
    original = seed_historical_exposure()
    assert original.ledger_sha256 == seed_historical_exposure().ledger_sha256
    tampered = replace(original, events=tuple(reversed(original.events)))
    with pytest.raises(ExposureError, match="changed after freeze"):
        tampered.validate()
    changed = replace(original, ledger_sha256="f" * 64)
    with pytest.raises(ExposureError, match="changed after freeze"):
        changed.validate()


def test_missing_evidence_or_empty_scope_fails_closed():
    key = OutcomeKey("SYNTHETIC_ONLY", "ARM", "outcome")
    with pytest.raises(ExposureError, match="concrete historical/review reference"):
        freeze_ledger([event(key, INSPECTED, ref="")])
    with pytest.raises(ExposureError, match="nonempty exact strings"):
        freeze_ledger([event(OutcomeKey("SYNTHETIC", " ", "response"), INSPECTED)])
    with pytest.raises(ExposureError, match="non-UNKNOWN"):
        freeze_ledger([event(key, UNKNOWN)])


def test_cannot_claim_heldout_for_known_inspected_even_from_empty_ledger():
    key = OutcomeKey("GSE254205", "bulk_GNE317", "AB_GNE_vs_AB")
    with pytest.raises(ExposureError, match="forbidden exposure regression"):
        freeze_ledger([event(key, DECLARED_UNINSPECTED)])
    empty = freeze_ledger([])
    assert empty.status(key) == INSPECTED
    assert not empty.evaluation_scope(key)["untouched_external_confirmation_authorized"]


def test_benchmark_exposure_gate_rejects_false_heldout_even_on_inspected_data():
    frozen = seed_historical_exposure()
    key = OutcomeKey("GSE254205", "bulk_GNE317", "AB_GNE_vs_AB")
    with pytest.raises(ExposureError, match="prospective outcome seal"):
        guard_descriptive_benchmark(
            ledger=frozen, key=key, partition_exposure="HELD_OUT",
        )
    accepted = guard_descriptive_benchmark(
        ledger=frozen, key=key, partition_exposure="RETROSPECTIVE_BENCHMARK",
    )
    assert accepted["recorded_status"] == INSPECTED
    assert accepted["independent_confirmation_authorized"] is False
    assert accepted["real_physical_input_authenticated_here"] is False


def test_benchmark_exposure_gate_denies_unknown_or_unreviewed_declared_holdout():
    frozen = seed_historical_exposure()
    key = OutcomeKey("SYNTHETIC_NEW_STUDY", "SYNTHETIC_ASSAY", "target_excluded_response")
    with pytest.raises(ExposureError, match="UNKNOWN"):
        guard_descriptive_benchmark(
            ledger=frozen, key=key, partition_exposure="RETROSPECTIVE_BENCHMARK",
        )
    declared = append_event(frozen, event(key, DECLARED_UNINSPECTED))
    with pytest.raises(ExposureError, match="cannot authorize"):
        guard_descriptive_benchmark(
            ledger=declared, key=key, partition_exposure="RETROSPECTIVE_BENCHMARK",
        )
    development = guard_descriptive_benchmark(
        ledger=declared, key=key, partition_exposure="DEVELOPMENT",
    )
    assert development["scope"] == "DESCRIPTIVE_DEVELOPMENT_OR_RETROSPECTIVE_ONLY"
    assert not development["independent_confirmation_authorized"]
