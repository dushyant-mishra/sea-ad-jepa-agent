from __future__ import annotations
import hashlib
import json
from pathlib import Path

import torch
import pytest
import sea_ad_jepa.v5.inactive_update_reference as update_reference
from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules,
    capture_reference_checkpoint, restore_reference_checkpoint,
)
from sea_ad_jepa.v5.inactive_guarded_update_v1 import run_guarded_inactive_reference_update
from sea_ad_jepa.v5.prefreeze_runtime_authority import PrefreezeMechanicalAuthorityV1, StepCompletionError


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json"


def _case():
    torch.manual_seed(707)
    n,vocab=6,32
    ops=[0,1,0,1,1,0]
    op0=torch.tensor([0,1,3,5,7,9,12,15,18,21,25,29])
    op1=torch.tensor([0,1,2,3,4,5,7,8,9,11,13,15,17,19,21,23,25,27,29,31])
    measured=torch.zeros((n,vocab),dtype=torch.bool)
    for row,op in enumerate(ops): measured[row,op0 if op==0 else op1]=True
    expression=torch.randn(n,vocab); expression[~measured]=0
    cells=torch.tensor([70_001,70_002,70_003,70_004,70_005,70_006],dtype=torch.int64)
    weights=torch.tensor([.4,2.0,1.1,.7,3.2,.6],dtype=torch.float32)
    views=[sample_uniform_target_blocks(measured,production_seed=8813003,cell_indices=cells,sample_pass=0,view_index=v,mask_fraction=.40,block_count=4) for v in range(2)]
    return expression,measured,cells,ops,weights,views,{0:len(op0),1:len(op1)}


def _modules():
    return build_reference_modules(vocabulary_size=32,width=16,heads=4,blocks=1,ffn_width=24,dropout=.10,learning_rate=3e-4,betas=(.9,.999),eps=1e-8,weight_decay=.01,init_seed=8113002)


def _amp_scaler():
    return torch.amp.GradScaler('cpu',init_scale=8.0,growth_factor=2.0,backoff_factor=.5,growth_interval=1)


def _authority(modules, update_index):
    checkpoint_digest=hashlib.sha256(f"inactive-reference-start-{update_index}".encode()).hexdigest()
    return PrefreezeMechanicalAuthorityV1.issue_for_optimizer(
        governance_state=json.loads(STATE_PATH.read_text()),
        optimizer=modules.optimizer,
        checkpoint_digest=checkpoint_digest,
    )


def _run(modules, data, *, update_index=0, max_tokens=40, scaler=None):
    kwargs=dict(
        expression=data[0],measurement_mask=data[1],stable_cell_keys=data[2],operator_ids=data[3],
        scientific_cell_weights=data[4],target_block_views=data[5],measured_tokens_by_operator=data[6],
        max_teacher_tokens_per_microbatch=max_tokens,run_seed=8113002,update_index=update_index,ema_momentum=.996)
    if scaler is not None:
        kwargs['scaler']=scaler
    return run_guarded_inactive_reference_update(
        modules,authority=_authority(modules,update_index),**kwargs)


def test_inactive_reference_update_steps_once_has_no_teacher_grad_and_exact_ema():
    data=_case(); modules=_modules()
    report=_run(modules,data)
    assert report['optimizer_step_before']==0 and report['optimizer_step_after']==1
    assert report['ema_max_abs_error']<=1e-7
    assert report['gradient_gate']['teacher_gradients']==0
    assert report['execution_authorized'] is False and report['training_authorized'] is False
    assert report['guarded_optimizer_step'] is True
    assert report['guarded_ema'] is True
    assert report['guard_kind']=='V5_PREFREEZE_OPTIMIZER_GUARD_V1'
    assert sorted(x for mb in report['microbatch_plan'] for x in mb)==list(range(6))


def test_canonical_v5_adamw_gradscaler_finite_step_completes_before_ema():
    data=_case(); modules=_modules(); scaler=torch.amp.GradScaler('cpu')
    report=_run(modules,data,scaler=scaler)
    assert report['optimizer_step_before']==0 and report['optimizer_step_after']==1
    assert report['guarded_optimizer_step'] is True
    assert report['guarded_ema'] is True
    assert report['amp_scaler_used'] is True
    assert report['ema_max_abs_error']<=1e-7


def test_canonical_v5_gradscaler_skip_cannot_advance_optimizer_or_teacher(monkeypatch):
    data=_case(); modules=_modules(); scaler=torch.amp.GradScaler('cpu')
    online_before={k:v.detach().clone() for k,v in modules.online.state_dict().items()}
    teacher_before={k:v.detach().clone() for k,v in modules.teacher.state_dict().items()}
    parameter=next(modules.online.parameters())
    hook=parameter.register_hook(lambda grad: torch.full_like(grad,float('inf')))
    monkeypatch.setattr(update_reference,'_gradient_report',lambda _modules: {
        'missing':0,'nonfinite':0,'exact_zero':0,'teacher_gradients':0,'max_abs_gradient':1.0})
    try:
        with pytest.raises(StepCompletionError,match='scaler.*skipped|did not complete'):
            _run(modules,data,scaler=scaler)
    finally:
        hook.remove()
    for name,before in online_before.items():
        assert torch.equal(modules.online.state_dict()[name],before),name
    for name,before in teacher_before.items():
        assert torch.equal(modules.teacher.state_dict()[name],before),name


def test_inactive_reference_update_is_deterministic_replay_on_same_initial_state():
    data=_case(); a=_modules(); b=_modules()
    ra=_run(a,data); rb=_run(b,data)
    assert ra==rb
    for ma,mb in ((a.online,b.online),(a.teacher,b.teacher),(a.predictor,b.predictor)):
        sa=ma.state_dict(); sb=mb.state_dict(); assert sa.keys()==sb.keys()
        for name in sa: assert torch.equal(sa[name],sb[name]),name


def test_compute_token_budget_changes_partition_not_scientific_cell_set_or_weight_mass():
    data=_case(); a=_modules(); b=_modules()
    ra=_run(a,data,max_tokens=40); rb=_run(b,data,max_tokens=80)
    assert ra['microbatch_plan']!=rb['microbatch_plan']
    assert ra['cells']==rb['cells']==6
    assert ra['scientific_weight_mass']==rb['scientific_weight_mass']==float(data[4].double().sum())
    assert abs(ra['loss']-rb['loss']) < 1e-5


def _module_state_equal(a,b):
    for ma,mb in ((a.online,b.online),(a.teacher,b.teacher),(a.predictor,b.predictor)):
        sa=ma.state_dict(); sb=mb.state_dict(); assert sa.keys()==sb.keys()
        for name in sa: assert torch.equal(sa[name],sb[name]),name


def test_incomplete_post_step_failure_cannot_advance_teacher_ema(monkeypatch):
    data=_case(); modules=_modules()
    teacher_before={k:v.detach().clone() for k,v in modules.teacher.state_dict().items()}
    online_before={k:v.detach().clone() for k,v in modules.online.state_dict().items()}
    original_step=modules.optimizer.step
    def step_then_reject(*args, **kwargs):
        original_step(*args, **kwargs)
        raise RuntimeError('PLANTED_POST_STEP_FAILURE')
    monkeypatch.setattr(modules.optimizer,'step',step_then_reject)
    with pytest.raises(RuntimeError, match='PLANTED_POST_STEP_FAILURE'):
        _run(modules,data)
    teacher_after=modules.teacher.state_dict(); online_after=modules.online.state_dict()
    for name,before in teacher_before.items(): assert torch.equal(teacher_after[name],before),name
    assert any(not torch.equal(online_after[name],before) for name,before in online_before.items())


def test_inactive_reference_checkpoint_resume_matches_uninterrupted_two_update_path():
    data=_case(); continuous=_modules(); first_report=_run(continuous,data,update_index=0)
    assert first_report['optimizer_step_after']==1
    ckpt=capture_reference_checkpoint(continuous,next_update_index=1,presentations_seen=len(data[0]))
    resumed=_modules(); cursor,presentations=restore_reference_checkpoint(resumed,ckpt)
    assert cursor==1 and presentations==6
    ra=_run(continuous,data,update_index=1); rb=_run(resumed,data,update_index=1)
    assert ra==rb
    assert ra['optimizer_step_before']==1 and ra['optimizer_step_after']==2
    _module_state_equal(continuous,resumed)


def test_amp_checkpoint_resume_preserves_scaler_and_exact_two_update_trajectory():
    data=_case(); continuous=_modules(); continuous_scaler=_amp_scaler()
    first=_run(continuous,data,update_index=0,scaler=continuous_scaler)
    assert first['optimizer_step_after']==1
    assert continuous_scaler.get_scale()==16.0

    checkpoint=capture_reference_checkpoint(
        continuous,next_update_index=1,presentations_seen=len(data[0]),scaler=continuous_scaler)
    assert checkpoint.amp_scaler_used is True
    assert checkpoint.scaler_state==continuous_scaler.state_dict()

    resumed=_modules(); resumed_scaler=_amp_scaler()
    assert resumed_scaler.get_scale()==8.0
    cursor,presentations=restore_reference_checkpoint(resumed,checkpoint,scaler=resumed_scaler)
    assert (cursor,presentations)==(1,6)
    assert resumed_scaler.state_dict()==continuous_scaler.state_dict()

    ra=_run(continuous,data,update_index=1,scaler=continuous_scaler)
    rb=_run(resumed,data,update_index=1,scaler=resumed_scaler)
    assert ra==rb
    _module_state_equal(continuous,resumed)
    assert resumed_scaler.state_dict()==continuous_scaler.state_dict()
    assert continuous_scaler.get_scale()==32.0


def test_reference_checkpoint_fails_closed_on_cursor_step_mismatch():
    modules=_modules()
    with pytest.raises(ValueError): capture_reference_checkpoint(modules,next_update_index=1,presentations_seen=0)


def test_reference_checkpoint_rejects_float_cursor_even_if_integral_value():
    modules=_modules()
    with pytest.raises(ValueError): capture_reference_checkpoint(modules,next_update_index=0.0,presentations_seen=0)
    with pytest.raises(ValueError): capture_reference_checkpoint(modules,next_update_index=0,presentations_seen=0.0)
