"""Fail-closed design-semantics checks for GSE178317 development producers.

These tests inspect source contracts only. They do not execute or validate the
physical GSE178317 data and do not confer biological authority.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "analysis/therapeutic_perturbation_etl/scripts/build_gse178317_intervention_effects_v1.py"
V2 = ROOT / "analysis/therapeutic_perturbation_etl/scripts/build_gse178317_intervention_effects_v2.py"
CALL = ROOT / "analysis/therapeutic_perturbation_etl/scripts/recover_gse178317_guide_assignments_v2.py"


def test_legacy_v1_effect_producer_is_fail_closed():
    s = V1.read_text()
    assert "STOP_GSE178317_V1_EFFECTS_SUPERSEDED" in s


def test_four_lanes_cannot_be_called_biological_uncertainty():
    s = V2.read_text()
    assert '"biological_uncertainty_estimable": False' in s
    assert '"n_independent_biological_replicates": "NOT_ESTABLISHED"' in s
    assert '"qualification_scope": "DESCRIPTIVE_WITHIN_CAPTURE_WELLS_ONLY"' in s
    assert '"technical_capture_well_spread_estimable"' in s


def test_post_smoke_thresholds_are_not_prospective_confirmation():
    s = CALL.read_text()
    assert '"development_status": "THRESHOLDS_FIXED_AFTER_BOUNDED_SMOKE_RUN"' in s
    assert '"prospective_confirmation_eligible": False' in s
    assert '"verdict_scope": "DEVELOPMENT_USABILITY_ONLY"' in s
    assert '"qualification_scope": "DEVELOPMENT_POST_SMOKE_NOT_GUIDE_IDENTITY_VALIDATION"' in s
    assert "development-calibrated, not prospective" in s


def test_no_training_or_therapeutic_authority_added():
    v2 = V2.read_text()
    assert '"training_authorized": False' in v2
    assert '"prospective_confirmation_authorized": False' in v2
    assert '"therapeutic_ranking": False' in v2
    call = CALL.read_text()
    assert '"prospective_confirmation_eligible": False' in call
