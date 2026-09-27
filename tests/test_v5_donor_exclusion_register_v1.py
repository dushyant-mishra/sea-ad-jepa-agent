"""Tests for the standing donor-exclusion directives.

Both rules are SCOPED, so the tests must prove the guard fires inside its scope
AND stays quiet outside it. A guard that always raises is as useless as one that
never does - it would simply be switched off.
"""
from __future__ import annotations

import pytest

from sea_ad_jepa.v5.donor_exclusion_register_v1 import (
    REGISTER, ExclusionViolation, enforce_exclusions, excluded_for)

LANE6 = ["HCT17HEX", "HCTZZT"]
OVERLAP = ["1224", "1230", "1238"]
CLEAN = ["4313", "HCTAAA", "BEB18077"]


# ---- directive 1: GEM lane 6 identity conflict ---------------------------
@pytest.mark.parametrize("cov", ["sex", "age", "region", "brain_region", "age_at_death"])
def test_lane6_blocked_when_any_demographic_covariate_is_used(cov):
    with pytest.raises(ExclusionViolation, match="GEM lane 6"):
        enforce_exclusions(CLEAN + LANE6, covariates=[cov])


def test_lane6_permitted_when_no_demographic_covariate():
    """The directive is SCOPED. A non-demographic analysis is not invalidated."""
    d = enforce_exclusions(CLEAN + LANE6, covariates=["total_counts", "operator"])
    r = next(x for x in d if x.rule_id.endswith("IDENTITY_CONFLICT"))
    assert r.triggered and r.excluded_donors == ("HCT17HEX", "HCTZZT")


def test_lane6_absent_is_quiet():
    enforce_exclusions(CLEAN, covariates=["sex", "age"])


def test_lane6_partial_presence_still_blocks():
    with pytest.raises(ExclusionViolation):
        enforce_exclusions(CLEAN + ["HCTZZT"], covariates=["sex"])


def test_lane6_donor_id_normalisation():
    """Formatting must not be a way around the rule."""
    with pytest.raises(ExclusionViolation):
        enforce_exclusions(["hct-17-hex"], covariates=["age"])


# ---- directive 2: possible Morabito overlap ------------------------------
def test_joint_claim_without_sensitivity_arm_is_blocked():
    with pytest.raises(ExclusionViolation, match="agreeing with itself"):
        enforce_exclusions(CLEAN + OVERLAP, joint_claim=True,
                           sensitivity_arm_present=False)


def test_joint_claim_with_sensitivity_arm_is_permitted():
    d = enforce_exclusions(CLEAN + OVERLAP, joint_claim=True,
                           sensitivity_arm_present=True)
    r = next(x for x in d if x.rule_id.endswith("POSSIBLE_OVERLAP"))
    assert r.requires_sensitivity_arm is True


def test_single_dataset_use_is_permitted_without_exclusion():
    """Either dataset ALONE is fine; only agreement between them is constrained."""
    enforce_exclusions(CLEAN + OVERLAP, joint_claim=False)


def test_joint_claim_without_the_overlapping_donors_is_fine():
    enforce_exclusions(CLEAN, joint_claim=True, sensitivity_arm_present=False)


# ---- register integrity --------------------------------------------------
def test_scope_lookup_returns_the_right_donors():
    assert set(excluded_for("DEMOGRAPHIC_COVARIATE_ANALYSES")) == set(LANE6)
    assert set(excluded_for("JOINT_OR_CROSS_STUDY_CLAIMS")) == set(OVERLAP)


def test_register_records_why_each_rule_exists_and_how_it_clears():
    for rule in REGISTER.values():
        assert rule["defect"] and rule["resolution_requires"]
        assert rule["action"] in ("EXCLUDE", "SENSITIVITY_ANALYSIS_REQUIRED")


def test_guard_is_not_vacuous_positive_control():
    """A guard that never raises would pass every other test here."""
    raised = False
    try:
        enforce_exclusions(LANE6, covariates=["sex"])
    except ExclusionViolation:
        raised = True
    assert raised, "the guard never fires; it is vacuous"
