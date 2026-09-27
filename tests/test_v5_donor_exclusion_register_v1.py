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
        assert rule["observed_defect"] and rule["resolution_requires"]
        assert rule["action"] in ("EXCLUDE", "SENSITIVITY_ANALYSIS_REQUIRED")


def test_guard_is_not_vacuous_positive_control():
    """A guard that never raises would pass every other test here."""
    raised = False
    try:
        enforce_exclusions(LANE6, covariates=["sex"])
    except ExclusionViolation:
        raised = True
    assert raised, "the guard never fires; it is vacuous"


def test_register_does_not_assert_an_unestablished_cause():
    """An observed conflict is not a demonstrated mechanism.

    The lane-6 entry previously described a demultiplexing swap as "the most
    parsimonious explanation", which asserts a cause that was never tested. The
    shared pooled lane makes a swap worth investigating; it does not make it the
    cause. The rule must stand on the OBSERVED conflict alone.
    """
    r = REGISTER["GSE214979_GEM_LANE_6_IDENTITY_CONFLICT"]
    assert r["cause"] == "NOT_ESTABLISHED"
    assert len(r["candidate_causes"]) > 1, "a single candidate reads as a conclusion"
    assert "demultiplexing swap" in r["candidate_causes"]
    blob = " ".join(str(v) for v in r.values()).lower()
    for overclaim in ("most parsimonious", "the cause is", "caused by", "demonstrated cause"):
        assert overclaim not in blob, f"register asserts an unestablished cause: {overclaim!r}"


# ==========================================================================
# INTEGRATION: the real entry point must reject unsafe configurations.
# Proving the guard raises when called directly is NOT enough - review found
# two bypasses that only appear at the entry point.
# ==========================================================================
from sea_ad_jepa.v5.donor_exclusion_register_v1 import (
    run_guarded_evaluation, derive_datasets_from_inputs, SensitivityArmResult)

SHA = "a" * 64
BOTH = {"data/GSE214979_matrix.h5": SHA, "data/GSE174367_snRNA.h5": SHA}
ONLY_979 = {"data/GSE214979_matrix.h5": SHA}


def _arm(excluded=("1224", "1230", "1238"), before=12, after=9,
         primary=0.30, sens=0.28):
    return SensitivityArmResult(tuple(excluded), before, after, primary, sens,
                                "4394f50e9085", SHA)


# ---- bypass 1: caller declares joint_claim=False while loading both ------
def test_BYPASS1_declaring_not_joint_does_not_evade_the_rule():
    """The original guard trusted the caller. The entry point derives it."""
    with pytest.raises(ExclusionViolation, match="joint claim"):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=BOTH,
                               cross_study_claim=False)      # <- the lie


def test_intent_can_only_tighten_never_loosen():
    """Declaring a joint claim on a single dataset still enforces the rule."""
    with pytest.raises(ExclusionViolation):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=ONLY_979, cross_study_claim=True)


def test_single_dataset_without_joint_intent_is_permitted():
    _, r = run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                                  input_manifest=ONLY_979, cross_study_claim=False)
    assert r["joint_enforced"] is False


# ---- bypass 2: sensitivity_arm_present=True with nothing behind it -------
def test_BYPASS2_a_boolean_is_not_evidence():
    with pytest.raises(ExclusionViolation, match="A boolean is not"):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=BOTH, cross_study_claim=True,
                               sensitivity_arm=None)


def test_sensitivity_arm_that_excluded_the_wrong_donors_is_rejected():
    with pytest.raises(ExclusionViolation, match="did not exclude"):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=BOTH, cross_study_claim=True,
                               sensitivity_arm=_arm(excluded=("9999",), after=11))


def test_sensitivity_arm_with_inconsistent_donor_count_is_rejected():
    """Claims the exclusion but the cohort never shrank."""
    with pytest.raises(ExclusionViolation, match="did not actually drop"):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=BOTH, cross_study_claim=True,
                               sensitivity_arm=_arm(before=12, after=12))


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_sensitivity_arm_with_nonfinite_estimate_is_rejected(bad):
    with pytest.raises(ExclusionViolation, match="finite number"):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=BOTH, cross_study_claim=True,
                               sensitivity_arm=_arm(sens=bad))


def test_sensitivity_arm_without_a_run_identity_is_rejected():
    bad = SensitivityArmResult(("1224", "1230", "1238"), 12, 9, 0.3, 0.28, "", SHA)
    with pytest.raises(ExclusionViolation, match="does not identify an actual run"):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=BOTH, cross_study_claim=True,
                               sensitivity_arm=bad)


# ---- positive control: a properly evidenced joint claim proceeds ---------
def test_properly_evidenced_joint_claim_is_permitted_and_runs():
    ran = []
    out, r = run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                                    input_manifest=BOTH, cross_study_claim=True,
                                    sensitivity_arm=_arm(),
                                    analysis=lambda: ran.append(1) or "done")
    assert out == "done" and ran == [1]
    assert r["joint_derived_ok"] if False else r["joint_claim_derived"] is True
    assert r["sensitivity_arm_verified"] is True


# ---- inputs must be authenticated ----------------------------------------
def test_unauthenticated_input_is_refused():
    with pytest.raises(ExclusionViolation, match="no valid SHA-256"):
        derive_datasets_from_inputs({"data/GSE214979_matrix.h5": "not-a-digest"})


def test_superseries_accession_resolves_to_its_data_series():
    """GSE214637 is a SuperSeries container; its data IS GSE214979."""
    assert derive_datasets_from_inputs({"data/GSE214637_x.h5": SHA}) == ("GSE214979",)


def test_lane6_enforced_through_the_entry_point_too():
    with pytest.raises(ExclusionViolation, match="GEM lane 6"):
        run_guarded_evaluation(donors=CLEAN + LANE6, covariates=["sex"],
                               input_manifest=ONLY_979, cross_study_claim=False)
