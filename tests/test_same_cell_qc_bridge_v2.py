import copy
import pytest

from sea_ad_jepa.v5.same_cell_qc_bridge_v2 import (
    CANONICAL_INTERVENTIONS,
    build_same_cell_measurement_qualification_v2,
)


def thresholds():
    return {name: f"threshold-{name.lower()}-v1" for name in CANONICAL_INTERVENTIONS}


def results():
    tids = thresholds()
    return {
        name: {
            "passed": True,
            "intervention": name,
            "calibration_authority_id": tids[name],
            "checks": {"bio_stability": True, "observation_response": True},
        }
        for name in CANONICAL_INTERVENTIONS
    }


def run(r=None, t=None):
    return build_same_cell_measurement_qualification_v2(
        r or results(),
        intervention_authority_id="same-cell-family-v2",
        threshold_authority_ids=t or thresholds(),
    )


def test_all_four_interventions_are_required_and_bound():
    out = run()
    assert out["passed"] is True
    assert tuple(out["interventions"]) == CANONICAL_INTERVENTIONS
    assert out["all_required_interventions_passed"] is True
    assert out["training_authorized"] is False


def test_missing_intervention_stops():
    r = results(); del r[CANONICAL_INTERVENTIONS[0]]
    with pytest.raises(RuntimeError, match="INTERVENTION_SET_INCOMPLETE"):
        run(r=r)


def test_extra_intervention_stops():
    r = results(); r["SOURCE_ID"] = copy.deepcopy(next(iter(r.values())))
    with pytest.raises(RuntimeError, match="INTERVENTION_SET_INCOMPLETE"):
        run(r=r)


def test_threshold_authority_set_must_match_intervention_set():
    t = thresholds(); del t[CANONICAL_INTERVENTIONS[-1]]
    with pytest.raises(RuntimeError, match="THRESHOLD_AUTHORITY_SET_INCOMPLETE"):
        run(t=t)


def test_intervention_identity_substitution_stops():
    r = results(); key = CANONICAL_INTERVENTIONS[0]; r[key]["intervention"] = CANONICAL_INTERVENTIONS[1]
    with pytest.raises(RuntimeError, match="IDENTITY_SUBSTITUTION"):
        run(r=r)


def test_threshold_authority_substitution_stops():
    r = results(); key = CANONICAL_INTERVENTIONS[0]; r[key]["calibration_authority_id"] = "other"
    with pytest.raises(ValueError, match="does not match threshold authority"):
        run(r=r)


def test_any_failed_intervention_stops_entire_family():
    r = results(); r[CANONICAL_INTERVENTIONS[2]]["passed"] = False
    with pytest.raises(RuntimeError, match="LOW_LEVEL_NOT_PASS"):
        run(r=r)


def test_hidden_failed_check_stops():
    r = results(); r[CANONICAL_INTERVENTIONS[1]]["checks"]["bio_stability"] = False
    with pytest.raises(RuntimeError, match="LOW_LEVEL_CHECK_NOT_PASS"):
        run(r=r)
