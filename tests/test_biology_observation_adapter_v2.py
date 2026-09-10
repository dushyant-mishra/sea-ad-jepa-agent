import pytest
import torch

from sea_ad_jepa.v5.biology_observation_adapter_v2 import (
    BiologyObservationAdapterV2,
    biology_anchor_alignment_loss_v2,
    gene_ledger_reconstruction_inputs_v2,
)


def make_adapter():
    torch.manual_seed(11)
    return BiologyObservationAdapterV2(
        state_width=8,
        observation_feature_width=3,
        observation_width=5,
    )


def test_observation_features_cannot_directly_change_z_bio():
    m = make_adapter().eval()
    torch.manual_seed(12)
    s = torch.randn(6, 8)
    t = torch.randn(6, 8)
    o = torch.randn(6, 3)
    a = m(
        student_biology_state=s,
        teacher_common_core_state=t,
        observation_features=o,
    )
    b = m(
        student_biology_state=s,
        teacher_common_core_state=t,
        observation_features=o + 10,
    )
    assert torch.equal(a.z_bio_prediction, b.z_bio_prediction)
    assert torch.equal(a.z_bio_anchor, b.z_bio_anchor)
    assert not torch.equal(a.z_obs, b.z_obs)


def test_observation_only_loss_cannot_write_into_biology_state():
    m = make_adapter().train()
    s = torch.randn(7, 8, requires_grad=True)
    t = torch.randn(7, 8, requires_grad=True)
    o = torch.randn(7, 3, requires_grad=True)
    out = m(
        student_biology_state=s,
        teacher_common_core_state=t,
        observation_features=o,
    )
    out.z_obs.square().mean().backward()
    assert s.grad is None
    assert t.grad is None
    assert o.grad is None
    assert any(p.grad is not None for p in m.obs_head.parameters())


def test_combined_loss_has_exact_same_biology_input_gradient_as_biology_loss_alone():
    m = make_adapter().train()
    torch.manual_seed(13)
    s1 = torch.randn(5, 8, requires_grad=True)
    t1 = torch.randn(5, 8, requires_grad=True)
    o1 = torch.randn(5, 3, requires_grad=True)
    out1 = m(
        student_biology_state=s1,
        teacher_common_core_state=t1,
        observation_features=o1,
    )
    biology_anchor_alignment_loss_v2(out1).backward()
    grad_bio_only = s1.grad.detach().clone()

    m.zero_grad(set_to_none=True)
    s2 = s1.detach().clone().requires_grad_(True)
    t2 = t1.detach().clone().requires_grad_(True)
    o2 = o1.detach().clone().requires_grad_(True)
    out2 = m(
        student_biology_state=s2,
        teacher_common_core_state=t2,
        observation_features=o2,
    )
    (biology_anchor_alignment_loss_v2(out2) + out2.z_obs.square().mean()).backward()
    assert torch.equal(s2.grad, grad_bio_only)
    assert t2.grad is None
    assert o2.grad is None


def test_reconstruction_helper_detaches_biology_context_but_trains_observation_route():
    m = make_adapter().train()
    s = torch.randn(6, 8, requires_grad=True)
    t = torch.randn(6, 8, requires_grad=True)
    o = torch.randn(6, 3, requires_grad=True)
    out = m(
        student_biology_state=s,
        teacher_common_core_state=t,
        observation_features=o,
    )
    bio_context, obs_state = gene_ledger_reconstruction_inputs_v2(out)
    assert bio_context.requires_grad is False
    # A dummy decoder-like scalar that uses both allowed contexts.
    loss = bio_context.square().mean() + obs_state.square().mean()
    loss.backward()
    assert s.grad is None
    assert t.grad is None
    assert o.grad is None
    assert all(p.grad is None for p in m.bio_predictor.parameters())
    assert any(p.grad is not None for p in m.obs_head.parameters())


def test_teacher_anchor_is_detached_and_biology_loss_does_not_touch_observation_features():
    m = make_adapter().train()
    s = torch.randn(4, 8, requires_grad=True)
    t = torch.randn(4, 8, requires_grad=True)
    o = torch.randn(4, 3, requires_grad=True)
    out = m(
        student_biology_state=s,
        teacher_common_core_state=t,
        observation_features=o,
    )
    biology_anchor_alignment_loss_v2(out).backward()
    assert s.grad is not None and bool((s.grad != 0).any())
    assert t.grad is None
    assert o.grad is None


def test_bad_shapes_and_nonfinite_stop():
    m = make_adapter()
    s = torch.randn(4, 8)
    t = torch.randn(4, 8)
    o = torch.randn(4, 3)
    with pytest.raises(ValueError, match="match"):
        m(
            student_biology_state=s,
            teacher_common_core_state=t[:3],
            observation_features=o,
        )
    bad = s.clone()
    bad[0, 0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        m(
            student_biology_state=bad,
            teacher_common_core_state=t,
            observation_features=o,
        )
