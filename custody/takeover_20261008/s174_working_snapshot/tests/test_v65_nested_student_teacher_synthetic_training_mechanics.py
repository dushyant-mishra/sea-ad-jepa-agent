from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/nested_student_teacher_synthetic_training_mechanics_v1.py"


def _load():
    spec=importlib.util.spec_from_file_location("mech",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_synthetic_training_mechanics_pass():
    out=_load().run_smoke()
    assert out["pass"] is True
    assert out["governance"]["real_data_used"] is False
    assert out["governance"]["real_training_authorized"] is False


def test_active_heads_receive_gradients_and_losses_fall():
    out=_load().run_smoke()
    g=out["gates"]
    assert g["active_gradients_nonzero"]
    assert g["rna_loss_decreased"]
    assert g["multimodal_shared_loss_decreased"]
    assert g["multimodal_private_loss_decreased"]


def test_private_loss_ignores_unpaired_targets_exactly():
    out=_load().run_smoke()
    n=out["mask_negative_control"]
    assert n["unpaired_target_perturbation_loss_abs_diff"]==0.0
    assert n["unpaired_target_perturbation_grad_max_abs_diff"]==0.0
    assert out["rna_private_head_present"] is False


def test_ema_moves_but_remains_lagged():
    out=_load().run_smoke()
    e=out["ema"]
    assert e["updates"]==120
    assert e["ema_is_exact_online_copy"] is False
    assert e["ema_to_current_online_l2"]>0
    assert e["ema_to_current_online_l2"]<e["initial_online_to_current_online_l2"]


def test_heldout_behavior_remains_finite_and_positive():
    out=_load().run_smoke()
    v=out["validation"]
    assert v["rna_shared_r2"]>0.2
    assert v["multimodal_shared_r2"]>0.2
    assert v["multimodal_private_r2"]>0.5
