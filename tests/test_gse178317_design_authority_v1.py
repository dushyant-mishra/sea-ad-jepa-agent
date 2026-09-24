"""Fail-closed design-semantics checks for GSE178317 development producers.

These tests inspect source contracts only. They do not execute or validate the
physical GSE178317 data and do not confer biological authority.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EFFECT = ROOT / "analysis/therapeutic_perturbation_etl/scripts/build_gse178317_intervention_effects_v1.py"
CALL = ROOT / "analysis/therapeutic_perturbation_etl/scripts/recover_gse178317_guide_assignments_v2.py"


def test_four_lanes_cannot_be_called_biological_uncertainty():
    s = EFFECT.read_text()
    assert '"biological_replicate_authority": "NOT_ESTABLISHED"' in s
    assert '"biological_uncertainty_estimable": False' in s
    assert '"lane_spread_interpretation": "DESCRIPTIVE_TECHNICAL_OR_PARTITION_SPREAD_ONLY"' in s
    assert '"lane_spread_estimable": bool(estimable)' in s
    assert '"uncertainty_estimable": bool(estimable)' not in s


def test_post_smoke_thresholds_are_not_prospective_confirmation():
    s = CALL.read_text()
    assert '"development_status": "THRESHOLDS_FIXED_AFTER_BOUNDED_SMOKE_RUN"' in s
    assert '"prospective_confirmation_eligible": False' in s
    assert '"verdict_scope": "DEVELOPMENT_USABILITY_ONLY"' in s
    assert "development-calibrated, not prospective" in s


def test_no_training_or_therapeutic_authority_added():
    for p in (EFFECT, CALL):
        s = p.read_text()
        assert "therapeutic_ranking" in s
    s = CALL.read_text()
    assert '"prospective_confirmation_eligible": False' in s
