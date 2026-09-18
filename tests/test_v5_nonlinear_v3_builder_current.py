import hashlib
from pathlib import Path

import pytest

from sea_ad_jepa.v5.masking_nonlinear_challenge_authority_v3 import (
    NonlinearMaskingChallengeAuthorityV3,
)
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import (
    NonlinearCapControlVerdictV1,
)
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v2 import (
    NonlinearSamplingCalibrationPlanV2,
    NonlinearSamplingCalibrationReceiptV2,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def verdict(cap: int, qualified: bool) -> NonlinearCapControlVerdictV1:
    return NonlinearCapControlVerdictV1(
        max_cells_per_donor=cap,
        capacity_receipt_sha256=h(f"capacity-{cap}"),
        planted_minus_shuffled_lower_one_sided=0.1 if qualified else 0.0,
        replay_exact=True,
        all_donors_represented=True,
    )


def plan() -> NonlinearSamplingCalibrationPlanV2:
    return NonlinearSamplingCalibrationPlanV2(
        authority_id="TEST_PLAN",
        target_panel_authority_sha256=h("panel"),
        precision_authority_sha256=h("precision"),
        outer_split_authority_sha256=h("split"),
        primary_parameters_authority_sha256=h("parameters"),
        model_capacity_authority_sha256=h("model"),
        calibration_cache_manifest_sha256=h("cache"),
        calibration_evaluator_source_sha256=h("evaluator"),
    )


def receipt(p: NonlinearSamplingCalibrationPlanV2) -> NonlinearSamplingCalibrationReceiptV2:
    v = {64: verdict(64, False), 128: verdict(128, True)}
    r = NonlinearSamplingCalibrationReceiptV2(
        plan_authority_sha256=p.canonical_digest(),
        calibration_cache_manifest_sha256=p.calibration_cache_manifest_sha256,
        precision_authority_sha256=p.precision_authority_sha256,
        model_capacity_authority_sha256=p.model_capacity_authority_sha256,
        selected_max_cells_per_donor=128,
        evaluated_caps=(64, 128),
        verdict_digest_by_cap={cap: obj.canonical_digest() for cap, obj in v.items()},
    )
    r.bind_verdicts(p, v)
    return r


def test_nonlinear_v3_binds_control_calibrated_cap_not_historical_row_cap():
    p = plan()
    r = receipt(p)
    a = NonlinearMaskingChallengeAuthorityV3(
        authority_id="TEST_V3",
        primary_parameters_authority_sha256=p.primary_parameters_authority_sha256,
        outer_split_authority_sha256=p.outer_split_authority_sha256,
        target_panel_authority_sha256=p.target_panel_authority_sha256,
        historical_nonlinear_script_sha256=h("historical-model-shape-script"),
        historical_nonlinear_summary_sha256=h("historical-model-shape-summary"),
        sampling_calibration_plan_sha256=p.canonical_digest(),
        sampling_calibration_receipt_sha256=r.canonical_digest(),
        max_cells_per_donor=128,
    )
    a.bind_sampling_calibration(p, r)
    assert a.max_cells_per_donor == r.selected_max_cells_per_donor
    assert a.random_seed == a.random_seed


def test_nonlinear_v3_rejects_cap_not_selected_by_current_receipt():
    p = plan()
    r = receipt(p)
    a = NonlinearMaskingChallengeAuthorityV3(
        authority_id="TEST_V3",
        primary_parameters_authority_sha256=p.primary_parameters_authority_sha256,
        outer_split_authority_sha256=p.outer_split_authority_sha256,
        target_panel_authority_sha256=p.target_panel_authority_sha256,
        historical_nonlinear_script_sha256=h("historical-model-shape-script"),
        historical_nonlinear_summary_sha256=h("historical-model-shape-summary"),
        sampling_calibration_plan_sha256=p.canonical_digest(),
        sampling_calibration_receipt_sha256=r.canonical_digest(),
        max_cells_per_donor=256,
    )
    with pytest.raises(ValueError, match="cap disagrees"):
        a.bind_sampling_calibration(p, r)


def test_current_v3_builder_does_not_open_historical_files_directly():
    path = Path("scripts/agent/build_full104_nonlinear_challenge_authority_v3_20260918.py")
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    lowered = source.lower()
    assert "analysis/v5_masking_successor_spike" not in lowered
    assert "outer5200_nonlinear" not in lowered
    assert "historical_nonlinear_script_sha256=model.historical_nonlinear_script_sha256" in source
    assert "historical_nonlinear_summary_sha256=model.historical_nonlinear_summary_sha256" in source
    assert "--sampling-plan" in source
    assert "--sampling-receipt" in source
    assert "--cap-verdict" in source


def test_nonlinear_evaluator_materializes_plan_before_opening_a_rung():
    path = Path("scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py")
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    write_plan = source.index('nonlinear_sampling_calibration_plan_v2.json')
    evaluate = source.index("evaluate_nonlinear_capacity_rung(", write_plan)
    assert write_plan < evaluate
