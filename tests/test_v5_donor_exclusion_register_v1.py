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


# ==========================================================================
# V4 CONTRACT PLANTED CONTROLS (i)-(v). Each MUST fail on its defect.
# ==========================================================================
from sea_ad_jepa.v5.donor_exclusion_register_v1 import (
    MIN_DETECTABLE_D, SUPERSEDED_FIGURES, EFFECT_SIZE_PRIOR_STATUS,
    POWER_METHOD_SEPARATION)

# Data S1 is authoritative: UT_04 / UT_09 are Control (A0/B0/C0).
DATA_S1_TRUTH = {"UT_04": "Control", "UT_09": "Control", "UT_2105": "EOAD",
                 "BEB18077": "Control", "BEB18110": "Control", "HCTZD": "Control",
                 "BEB19074": "EOAD", "BEB19080": "EOAD", "BEB20005": "EOAD"}
GEO_TITLE_LABEL = {"UT_04": "sEOAD", "UT_09": "sEOAD"}     # the contradictory titles
S8_SFG_COHORT = ["UT2206", "HA23-14", "N2301", "UT22-03"]  # separate validation cohort


def _diagnosis_from_titles(d):
    return GEO_TITLE_LABEL.get(d, DATA_S1_TRUTH[d])


def test_planted_i_geo_title_misclassification_MUST_fail():
    """(i) Parsing GEO titles moves 2 of 9 donors from control into case."""
    wrong = [d for d in DATA_S1_TRUTH if _diagnosis_from_titles(d) != DATA_S1_TRUTH[d]]
    assert wrong == ["UT_04", "UT_09"], wrong
    n_ctrl_titles = sum(1 for d in DATA_S1_TRUTH if _diagnosis_from_titles(d) == "Control")
    n_ctrl_truth = sum(1 for v in DATA_S1_TRUTH.values() if v == "Control")
    assert n_ctrl_titles == 3 and n_ctrl_truth == 5, "the planted defect must change the design"


def test_planted_ii_S8_and_region_libraries_MUST_not_inflate_the_cohort():
    """(ii) S8's four SFG donors and the 21 region-libraries are not extra people."""
    nine = set(DATA_S1_TRUTH)
    assert len(nine) == 9
    assert not (nine & set(S8_SFG_COHORT)), "S8 is a DISTINCT validation cohort"
    assert len(nine | set(S8_SFG_COHORT)) == 13, "merging them would claim 13 people"
    region_libraries = 3 * 1 + 6 * 3          # 3 UT single-region + 6 donors x 3 regions
    assert region_libraries == 21 and region_libraries != len(nine)


def test_planted_iii_lane6_in_a_donor_covariate_primary_set_MUST_fail():
    """(iii) already covered by the entry point; asserted here as a named control."""
    with pytest.raises(ExclusionViolation):
        run_guarded_evaluation(donors=CLEAN + LANE6, covariates=["sex", "age"],
                               input_manifest=ONLY_979, cross_study_claim=False)


def test_planted_iv_omitting_the_UCI_controls_from_the_sensitivity_MUST_fail():
    """(iv) a sensitivity arm that does not drop 1224/1230/1238 is not a sensitivity arm."""
    with pytest.raises(ExclusionViolation, match="did not exclude"):
        run_guarded_evaluation(donors=CLEAN + OVERLAP, covariates=[],
                               input_manifest=BOTH, cross_study_claim=True,
                               sensitivity_arm=_arm(excluded=("1224",), before=12, after=11))


def test_planted_v_unchanged_positive_dataset_MUST_pass():
    """(v) the positive control. Without it the four refusals prove nothing."""
    out, r = run_guarded_evaluation(donors=CLEAN, covariates=["sex", "age"],
                                    input_manifest=ONLY_979, cross_study_claim=False,
                                    analysis=lambda: "ok")
    assert out == "ok" and r["joint_enforced"] is False


# ---- cohort arithmetic: 12, not 10 and not 13 ----------------------------
def test_frozen_cohort_is_12_not_10_or_13():
    """PR #182 ALREADY drops the lane-6 pair; subtracting them again gives 10."""
    r = REGISTER["GSE214979_GEM_LANE_6_IDENTITY_CONFLICT"]
    assert r["frozen_cohort_n"] == 12
    assert r["frozen_cohort_composition"] == {"AD": 6, "control": 6, "microglia": 2872}
    assert "DO NOT subtract these donors a second time" in r["already_applied_upstream"]
    census_total = 15
    already_excluded = 3            # two lane-6 + one <50 microglia
    assert census_total - already_excluded == 12
    assert census_total - already_excluded - len(r["donors"]) == 10, "the double-subtraction error"


# ---- corrected effect sizes and estimand separation ----------------------
def test_morabito_is_11_7_not_the_illustrative_9_9():
    assert MIN_DETECTABLE_D["Morabito_18"]["groups"] == (11, 7)
    assert abs(MIN_DETECTABLE_D["Morabito_18"]["d"] - 1.443) < 1e-3
    assert SUPERSEDED_FIGURES["Morabito_9_9_illustrative"]["groups"] == (9, 9)


def test_uci_sensitivity_arm_power_is_recorded():
    r = REGISTER["GSE214979_MORABITO_POSSIBLE_OVERLAP"]
    assert r["sensitivity_cohort_composition"] == {"AD": 6, "control": 3}
    assert abs(r["sensitivity_min_detectable_d"] - 2.312) < 1e-3
    assert "NOT disagreement" in r["interpretation_guard"]


def test_hurdle_DE_power_is_not_presented_as_cross_validation():
    """I described the authors' power as 'corroborating' ours. Different estimands."""
    assert POWER_METHOD_SEPARATION["relationship"] == "SUPPORTIVE_CONTEXT_NOT_CROSS_VALIDATION"
    assert POWER_METHOD_SEPARATION["authors_hurdle_DE"]["estimand"] != \
           POWER_METHOD_SEPARATION["our_two_sample_d"]["estimand"]


def test_effect_prior_is_labelled_a_planning_assumption():
    assert EFFECT_SIZE_PRIOR_STATUS == "PLANNING_ASSUMPTION_NOT_ESTABLISHED_DISTRIBUTION"
