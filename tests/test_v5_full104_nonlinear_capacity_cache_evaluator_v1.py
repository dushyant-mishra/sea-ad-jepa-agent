import numpy as np
import pytest

from sea_ad_jepa.v5.full104_nonlinear_capacity_cache_evaluator_v1 import (
    _donor_r2,derive_nonlinear_capacity_seeds
)

def test_nonlinear_capacity_seed_is_plan_derived_and_cap_independent():
    a=derive_nonlinear_capacity_seeds("a"*64)
    b=derive_nonlinear_capacity_seeds("a"*64)
    c=derive_nonlinear_capacity_seeds("b"*64)
    assert a==b and a!=c
    assert 0<=a[0]<2**32

def test_donor_r2_is_centered_within_donor():
    y=np.array([1.,2.,3.,10.,20.,30.])
    pred=np.array([2.,4.,6.,7.,14.,21.])
    d=np.array([0,0,0,1,1,1])
    out=_donor_r2(y,pred,d)
    assert out[0]==pytest.approx(1.0)
    assert out[1]==pytest.approx(1.0)

def test_nonlinear_capacity_evaluator_script_is_cache_only_and_no_historical_paths():
    from pathlib import Path
    p=Path("scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py")
    source=p.read_text(encoding="utf-8")
    compile(source,str(p),"exec")
    assert "load_control_calibration_cache" in source
    assert "NonlinearSamplingCalibrationPlanV2" in source
    assert "REPLAY_REQUIRED_BEFORE_NONLINEAR_CAPACITY_VERDICT" in source
    assert "plan.next_cap(prior)" in source
    assert "cache.target_cols[:panel.target_count]" in source
    for forbidden in ("stage81","t1_checkpoint","post_u0_t1","0.996","X_common6000","outer5200_targets32"):
        assert forbidden.lower() not in source.lower()
