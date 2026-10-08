import hashlib
from pathlib import Path

import numpy as np
import pytest

from sea_ad_jepa.v5.control_calibration_precision_authority_v2 import (
    ControlCalibrationPrecisionPlanV2,
)


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def plan(**updates):
    values = dict(
        authority_id="TEST_PRECISION_V2",
        census_authority_sha256=h("census"),
        support_estimability_authority_sha256=h("support"),
        target_eligibility_receipt_sha256=h("eligibility"),
        fold_assignment_artifact_sha256=h("split-receipt"),
        calibration_cache_manifest_sha256=h("cache-manifest"),
    )
    values.update(updates)
    return ControlCalibrationPrecisionPlanV2(**values)


class CacheStub:
    terminal_masking_qualification_authorized = False

    def __init__(self, p):
        self.census_authority_sha256 = p.census_authority_sha256
        self.support_estimability_authority_sha256 = p.support_estimability_authority_sha256
        self.target_eligibility_receipt_sha256 = p.target_eligibility_receipt_sha256
        self.split_receipt_sha256 = p.fold_assignment_artifact_sha256
        self._digest = p.calibration_cache_manifest_sha256

    def validate(self):
        return None

    def canonical_digest(self):
        return self._digest


def test_v2_names_fold_receipt_as_receipt_not_outer_split_authority():
    p = plan()
    p.validate()
    assert "fold_assignment_artifact_sha256" in p.__dataclass_fields__
    assert "outer_split_authority_sha256" not in p.__dataclass_fields__


def test_v2_binds_cache_and_rejects_role_splice():
    p = plan()
    p.bind_calibration_cache(CacheStub(p))
    bad = CacheStub(p)
    bad.split_receipt_sha256 = h("other-split")
    with pytest.raises(ValueError, match="split_receipt_sha256"):
        p.bind_calibration_cache(bad)


def test_v2_seed_depends_on_cache_root():
    assert plan().bootstrap_seed(128) != plan(calibration_cache_manifest_sha256=h("other-cache")).bootstrap_seed(128)


def test_v2_interval_requires_full104_donor_axis():
    p = plan()
    with pytest.raises(ValueError, match="104"):
        p.interval(np.zeros((128, 103)), np.zeros(104, dtype=int), target_count=128)


def test_target_panel_evaluator_materializes_both_plans_before_rung_evaluation():
    path = Path("scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py")
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    assert "ControlCalibrationPrecisionPlanV2" in source
    assert "outer_split_authority_sha256=cache.manifest.split_receipt_sha256" not in source
    sizing_write = source.index('target_panel_sizing_plan_v2.json')
    precision_write = source.index('control_calibration_precision_plan_v2.json')
    evaluate = source.index("evaluate_linear_capacity_rung(", max(sizing_write, precision_write))
    assert sizing_write < evaluate
    assert precision_write < evaluate
