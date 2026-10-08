import hashlib
import pytest
from sea_ad_jepa.v5.nonlinear_capacity_model_authority_v1 import NonlinearCapacityModelAuthorityV1
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v2 import (
    NonlinearSamplingCalibrationPlanV2,NonlinearSamplingCalibrationReceiptV2
)
from sea_ad_jepa.v5.nonlinear_sampling_calibration_authority_v1 import NonlinearCapControlVerdictV1

def h(x): return hashlib.sha256(x.encode()).hexdigest()

def model(**u):
    v=dict(authority_id="TEST",primary_parameters_authority_sha256=h("params"),historical_nonlinear_script_sha256=h("script"),historical_nonlinear_summary_sha256=h("summary"))
    v.update(u); return NonlinearCapacityModelAuthorityV1(**v)

def plan(**u):
    v=dict(authority_id="TEST",target_panel_authority_sha256=h("panel"),precision_authority_sha256=h("precision"),outer_split_authority_sha256=h("split"),primary_parameters_authority_sha256=h("params"),model_capacity_authority_sha256=h("model"),calibration_cache_manifest_sha256=h("cache"),calibration_evaluator_source_sha256=h("evaluator"))
    v.update(u); return NonlinearSamplingCalibrationPlanV2(**v)

def verdict(cap,ok=True):
    return NonlinearCapControlVerdictV1(cap,h(f"receipt-{cap}"),0.01 if ok else -0.001,True,True)

def test_model_capacity_authority_excludes_discovery_data_and_row_cap():
    a=model(); a.validate()
    assert a.feature_count==32 and a.max_iter==50 and a.max_leaf_nodes==15
    assert a.row_cap_frozen_here is False
    assert a.discovery_dataset_authorized_for_full104 is False
    assert a.discovery_target_list_authorized_for_full104 is False
    assert a.discovery_burden_authorized_for_full104 is False
    with pytest.raises(ValueError,match="row_cap_frozen_here"):
        model(row_cap_frozen_here=True).validate()

def test_nonlinear_v2_plan_uses_current_roots_and_stops_first_pass():
    p=plan(); p.validate()
    assert p.next_cap({})==64
    assert p.next_cap({64:verdict(64,False)})==128
    assert p.select({64:verdict(64,True)})==64
    with pytest.raises(ValueError,match="higher nonlinear cap"):
        p.select({64:verdict(64,True),128:verdict(128,False)})

def test_nonlinear_v2_receipt_binds_cache_precision_model_and_verdicts():
    p=plan(); vs={64:verdict(64,True)}
    r=NonlinearSamplingCalibrationReceiptV2(
        p.canonical_digest(),p.calibration_cache_manifest_sha256,p.precision_authority_sha256,
        p.model_capacity_authority_sha256,64,(64,),{64:vs[64].canonical_digest()}
    )
    r.bind_verdicts(p,vs)
    with pytest.raises(ValueError,match="cache root"):
        NonlinearSamplingCalibrationReceiptV2(
            p.canonical_digest(),h("other-cache"),p.precision_authority_sha256,
            p.model_capacity_authority_sha256,64,(64,),{64:vs[64].canonical_digest()}
        ).bind_verdicts(p,vs)
