import copy
import pytest

from sea_ad_jepa.v5.same_cell_qc_bridge_v2 import CANONICAL_INTERVENTIONS
from sea_ad_jepa.v5.same_cell_qc_bridge_v3 import (
    build_same_cell_measurement_qualification_v3,
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


def artifacts():
    return {name: format(i + 1, "064x") for i, name in enumerate(CANONICAL_INTERVENTIONS)}


def run(r=None, a=None):
    return build_same_cell_measurement_qualification_v3(
        r or results(),
        low_level_artifact_sha256_by_intervention=a or artifacts(),
        intervention_authority_id="same-cell-family-v3",
        threshold_authority_ids=thresholds(),
    )


def test_v3_binds_every_low_level_artifact():
    out = run()
    assert out["schema"] == "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V3"
    assert out["low_level_artifact_sha256_by_intervention"] == artifacts()
    assert out["training_authorized"] is False


def test_missing_child_artifact_stops():
    a = artifacts(); del a[CANONICAL_INTERVENTIONS[0]]
    with pytest.raises(RuntimeError, match="ARTIFACT_SET_INCOMPLETE"):
        run(a=a)


def test_extra_child_artifact_stops():
    a = artifacts(); a["SOURCE_ID"] = "f" * 64
    with pytest.raises(RuntimeError, match="ARTIFACT_SET_INCOMPLETE"):
        run(a=a)


def test_invalid_child_digest_stops():
    a = artifacts(); a[CANONICAL_INTERVENTIONS[1]] = "not-a-digest"
    with pytest.raises(ValueError, match="SHA-256"):
        run(a=a)


def test_child_semantics_still_fail_closed():
    r = copy.deepcopy(results()); r[CANONICAL_INTERVENTIONS[2]]["passed"] = False
    with pytest.raises(RuntimeError, match="LOW_LEVEL_NOT_PASS"):
        run(r=r)
