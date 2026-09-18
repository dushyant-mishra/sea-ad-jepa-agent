import hashlib, pytest
from sea_ad_jepa.v5.target_panel_sizing_authority_v2 import TargetPanelSizingPlanAuthorityV2,TargetPanelControlVerdictV2,TargetPanelSizingReceiptV2
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import NonlinearSamplingCalibrationPlanV1,NonlinearCapControlVerdictV1,NonlinearSamplingCalibrationReceiptV1

def h(x): return hashlib.sha256(x.encode()).hexdigest()
def panel(): return TargetPanelSizingPlanAuthorityV2("TEST",h("census"),h("elig"),104,17053)
def pver(count,ok=True):
    return TargetPanelControlVerdictV2(count,h(f"control-{count}"),h(f"precision-{count}"),-0.01,0.01,0.03 if ok else 0.005,0.005,True,True,True)
def nplan(): return NonlinearSamplingCalibrationPlanV1("TEST",h("panel"),h("split"),h("params"))
def nver(cap,ok=True):
    return NonlinearCapControlVerdictV1(cap,h(f"nl-{cap}"),-0.01,0.01,0.03 if ok else 0.005,0.005,True,True)

def test_target_panel_starts_at_128_but_success_is_control_derived():
    p=panel(); assert p.next_target_count({})==128
    assert p.next_target_count({128:pver(128,False)})==256
    assert p.select({128:pver(128,True)})==128
    assert pver(128,True).qualified and not pver(128,False).qualified

def test_target_panel_receipt_binds_actual_verdict_digests():
    p=panel(); vs={128:pver(128,True)}
    r=TargetPanelSizingReceiptV2(p.canonical_digest(),128,(128,),{128:vs[128].canonical_digest()})
    r.bind_verdicts(p,vs)
    bad=TargetPanelSizingReceiptV2(p.canonical_digest(),128,(128,),{128:h("fake")})
    with pytest.raises(ValueError,match="digests"): bad.bind_verdicts(p,vs)

def test_target_panel_cannot_use_real_policy_outcomes():
    with pytest.raises(ValueError,match="cannot inspect"):
        pver(128,True).__class__(**{**pver(128,True).__dict__,"real_masking_policy_outcomes_inspected":True}).validate()

def test_nonlinear_cap_is_control_calibrated_not_frozen_to_256():
    p=nplan(); assert p.next_cap({})==64
    assert p.next_cap({64:nver(64,False),128:nver(128,False)})==256
    assert p.select({64:nver(64,True)})==64

def test_nonlinear_receipt_binds_mechanical_control_verdict():
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
