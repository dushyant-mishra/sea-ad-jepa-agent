import torch
import pytest
from sea_ad_jepa.v5.biology_observation_adapter_v1 import BiologyObservationAdapterV1,biology_anchor_alignment_loss

def make_adapter():
    torch.manual_seed(3)
    return BiologyObservationAdapterV1(state_width=8,observation_feature_width=3,observation_width=5)

def test_observation_features_cannot_change_z_bio():
    m=make_adapter().eval(); torch.manual_seed(4)
    s=torch.randn(6,8); t=torch.randn(6,8); o=torch.randn(6,3)
    a=m(student_native_state=s,teacher_common_core_state=t,observation_features=o)
    b=m(student_native_state=s,teacher_common_core_state=t,observation_features=o+10)
    assert torch.equal(a.z_bio_prediction,b.z_bio_prediction)
    assert torch.equal(a.z_bio_anchor,b.z_bio_anchor)
    assert not torch.equal(a.z_obs,b.z_obs)

def test_common_core_anchor_is_detached():
    m=make_adapter().train()
    s=torch.randn(7,8,requires_grad=True); t=torch.randn(7,8,requires_grad=True); o=torch.randn(7,3,requires_grad=True)
    out=m(student_native_state=s,teacher_common_core_state=t,observation_features=o)
    biology_anchor_alignment_loss(out).backward()
    assert s.grad is not None and bool((s.grad!=0).any())
    assert t.grad is None
    assert o.grad is None

def test_observation_route_does_not_touch_teacher_anchor():
    m=make_adapter().train()
    s=torch.randn(4,8,requires_grad=True); t=torch.randn(4,8,requires_grad=True); o=torch.randn(4,3,requires_grad=True)
    out=m(student_native_state=s,teacher_common_core_state=t,observation_features=o)
    out.z_obs.square().mean().backward()
    assert s.grad is not None and o.grad is not None
    assert t.grad is None

def test_bad_shapes_and_nonfinite_stop():
    m=make_adapter(); s=torch.randn(4,8); t=torch.randn(4,8); o=torch.randn(4,3)
    with pytest.raises(ValueError,match="match"):
        m(student_native_state=s,teacher_common_core_state=t[:3],observation_features=o)
    bad=s.clone(); bad[0,0]=float("nan")
    with pytest.raises(ValueError,match="finite"):
        m(student_native_state=bad,teacher_common_core_state=t,observation_features=o)
