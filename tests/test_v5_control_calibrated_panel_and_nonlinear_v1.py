import hashlib
import pytest
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import (
    TargetPanelSizingPlanAuthorityV2, TargetPanelControlVerdictV2
)
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import (
    NonlinearSamplingCalibrationPlanV1, NonlinearCapControlVerdictV1
)

def h(x): return hashlib.sha256(x.encode()).hexdigest()

def panel():
    return TargetPanelSizingPlanAuthorityV2("TEST",h("census"),h("elig"),104,17053)

def pver(count,ok):
    return TargetPanelControlVerdictV2(count,ok,ok,ok,ok,ok,ok)

def nplan():
    return NonlinearSamplingCalibrationPlanV1("TEST",h("panel"),h("split"),h("params"))

def nver(cap,ok):
    return NonlinearCapControlVerdictV1(cap,ok,ok,ok,ok,ok)

def test_target_panel_starts_at_128_but_does_not_hardcode_128_as_success():
    p=panel(); p.validate()
    assert p.next_target_count({})==128
    assert p.next_target_count({128:pver(128,False)})==256
    assert p.select({128:pver(128,True)})==128

def test_target_panel_stops_after_first_control_qualified_rung():
    p=panel()
    with pytest.raises(ValueError,match="higher panel-count"):
        p.select({128:pver(128,True),256:pver(256,False)})

def test_target_panel_all_control_fail_is_fail_closed():
    p=panel()
    with pytest.raises(ValueError,match="FAIL_CLOSED"):
        p.select({c:pver(c,False) for c in (128,256,512,1024)})

def test_nonlinear_cap_is_control_calibrated_not_frozen_to_256():
    p=nplan(); p.validate()
    assert p.next_cap({})==64
    assert p.next_cap({64:nver(64,False),128:nver(128,False)})==256
    assert p.select({64:nver(64,True)})==64

def test_nonlinear_cap_stops_after_first_control_pass():
    p=nplan()
    with pytest.raises(ValueError,match="higher nonlinear cap"):
        p.select({64:nver(64,True),128:nver(128,False)})
