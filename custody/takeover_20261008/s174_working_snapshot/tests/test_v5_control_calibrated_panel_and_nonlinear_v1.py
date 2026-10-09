import hashlib, pytest
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import TargetPanelSizingPlanAuthorityV2,TargetPanelControlVerdictV2,TargetPanelSizingReceiptV2
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import NonlinearSamplingCalibrationPlanV1,NonlinearCapControlVerdictV1,NonlinearSamplingCalibrationReceiptV1
from sea_ad_jepa.v5.control_capacity_calibration_receipt_v1 import ControlCapacityCalibrationReceiptV1
from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import CACHE_ROLE_ID

def h(x): return hashlib.sha256(x.encode()).hexdigest()
def panel(): return TargetPanelSizingPlanAuthorityV2("TEST",h("census"),h("elig"),104,17053)
def pcap(count,ok=True):
    return ControlCapacityCalibrationReceiptV1("TARGET_PANEL_SIZE_CAPACITY_CALIBRATION_V1",count,h("cache"),CACHE_ROLE_ID,h(f"p-{count}"),h(f"s-{count}"),h("calibration-precision"),0.03 if ok else 0.0,0.01 if ok else -0.001,104,count,4096,95,100,True)
def pver(count,ok=True):
    c=pcap(count,ok)
    return TargetPanelControlVerdictV2(count,c.canonical_digest(),c.planted_minus_shuffled_lower_one_sided,True,True,True)
def nplan(): return NonlinearSamplingCalibrationPlanV1("TEST",h("panel"),h("split"),h("params"))
def ncap(cap,ok=True):
    return ControlCapacityCalibrationReceiptV1("NONLINEAR_CAP_CAPACITY_CALIBRATION_V1",cap,h("cache"),CACHE_ROLE_ID,h(f"np-{cap}"),h(f"ns-{cap}"),h("precision"),0.03 if ok else 0.0,0.01 if ok else -0.001,104,128,4096,95,100,True)
def nver(cap,ok=True):
    c=ncap(cap,ok)
    return NonlinearCapControlVerdictV1(cap,c.canonical_digest(),c.planted_minus_shuffled_lower_one_sided,True,True)

def test_target_panel_starts_at_128_and_success_is_capacity_derived():
    p=panel(); assert p.next_target_count({})==128
    assert p.next_target_count({128:pver(128,False)})==256
    assert p.select({128:pver(128,True)})==128
    pver(128,True).bind_capacity_receipt(pcap(128,True))

def test_target_panel_receipt_binds_verdict_digests():
    p=panel(); vs={128:pver(128,True)}
    r=TargetPanelSizingReceiptV2(p.canonical_digest(),128,(128,),{128:vs[128].canonical_digest()})
    r.bind_verdicts(p,vs)
    with pytest.raises(ValueError,match="digests"):
        TargetPanelSizingReceiptV2(p.canonical_digest(),128,(128,),{128:h("fake")}).bind_verdicts(p,vs)

def test_nonlinear_cap_is_capacity_calibrated_not_frozen_to_256():
    p=nplan(); assert p.next_cap({})==64
    assert p.next_cap({64:nver(64,False),128:nver(128,False)})==256
    assert p.select({64:nver(64,True)})==64
    nver(64,True).bind_capacity_receipt(ncap(64,True))

def test_nonlinear_receipt_binds_verdict_digest():
    p=nplan(); vs={64:nver(64,True)}
    r=NonlinearSamplingCalibrationReceiptV1(p.canonical_digest(),64,(64,),{64:vs[64].canonical_digest()})
    r.bind_verdicts(p,vs)
    with pytest.raises(ValueError,match="mismatch"):
        NonlinearSamplingCalibrationReceiptV1(p.canonical_digest(),64,(64,),{64:h("fake")}).bind_verdicts(p,vs)

def test_higher_rungs_after_pass_are_rejected():
    with pytest.raises(ValueError,match="higher panel-count"):
        panel().select({128:pver(128,True),256:pver(256,False)})
    with pytest.raises(ValueError,match="higher nonlinear cap"):
        nplan().select({64:nver(64,True),128:nver(128,False)})
