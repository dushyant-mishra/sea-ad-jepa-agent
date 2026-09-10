import pytest

from sea_ad_jepa.v5.same_cell_qc_bridge_v1 import (
    build_same_cell_measurement_qualification,
)


def low_level(**kw):
    out = {
        "passed": True,
        "intervention": "MEASUREMENT_DEPTH",
        "calibration_authority_id": "threshold-v1",
        "checks": {
            "bio_median_relative_l2": True,
            "bio_p95_relative_l2": True,
            "bio_median_cosine": True,
            "obs_median_relative_l2": True,
            "bio_to_obs_median_delta_ratio": True,
        },
    }
    out.update(kw)
    return out


def test_bridge_emits_exact_qc_schema_and_never_training_authority():
    out = build_same_cell_measurement_qualification(
        low_level(),
        intervention_authority_id="samecell-v1",
        threshold_authority_id="threshold-v1",
    )
    assert out["schema"] == "JEPA_V5_SAME_CELL_MEASUREMENT_QUALIFICATION_V1"
    assert out["authority_id"] == "samecell-v1"
    assert out["threshold_authority_id"] == "threshold-v1"
    assert out["passed"] is True
    assert out["training_authorized"] is False


def test_bridge_rejects_threshold_authority_substitution():
    with pytest.raises(ValueError, match="calibration authority"):
        build_same_cell_measurement_qualification(
            low_level(),
            intervention_authority_id="samecell-v1",
            threshold_authority_id="after-the-fact",
        )


def test_bridge_rejects_low_level_nonpass():
    with pytest.raises(RuntimeError, match="LOW_LEVEL_NOT_PASS"):
        build_same_cell_measurement_qualification(
            low_level(passed=False),
            intervention_authority_id="samecell-v1",
            threshold_authority_id="threshold-v1",
        )


def test_bridge_rejects_hidden_failed_check_even_if_pass_flag_is_true():
    row = low_level()
    row["checks"]["bio_median_cosine"] = False
    with pytest.raises(RuntimeError, match="LOW_LEVEL_CHECK_NOT_PASS"):
        build_same_cell_measurement_qualification(
            row,
            intervention_authority_id="samecell-v1",
            threshold_authority_id="threshold-v1",
        )
