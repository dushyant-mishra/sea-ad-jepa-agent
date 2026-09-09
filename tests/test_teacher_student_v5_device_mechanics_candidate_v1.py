from __future__ import annotations
import copy
import pytest, torch
from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules, run_inactive_reference_update,
    capture_reference_checkpoint, restore_reference_checkpoint,
)
from sea_ad_jepa.v5.inactive_update_device_candidate_v1 import build_device_candidate_modules
from sea_ad_jepa.v5.keyed_dropout_prototype_v2 import KeyedIPBEncoderV2Reference
from sea_ad_jepa.v5.keyed_dropout_device_candidate_v1 import KeyedIPBEncoderV2DeviceCandidate


def _case(device='cpu'):
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
    if str(device)!='cpu':
        expression=expression.to(device); measured=measured.to(device); cells=cells.to(device); weights=weights.to(device)
        views=[type(x)(hidden_mask=x.hidden_mask.to(device),indices=x.indices.to(device),member_mask=x.member_mask.to(device),fallback_counts=x.fallback_counts.to(device)) for x in views]
    return expression,measured,cells,ops,weights,views,{0:len(op0),1:len(op1)}


def _reference():
    return build_reference_modules(vocabulary_size=32,width=16,heads=4,blocks=1,ffn_width=24,dropout=.10,learning_rate=3e-4,betas=(.9,.999),eps=1e-8,weight_decay=.01,init_seed=8113002)


def _device(device='cpu'):
    return build_device_candidate_modules(vocabulary_size=32,width=16,heads=4,blocks=1,ffn_width=24,dropout=.10,learning_rate=3e-4,betas=(.9,.999),eps=1e-8,weight_decay=.01,init_seed=8113002,device=device)


def _kwargs(data,update=0,budget=40):
    return dict(expression=data[0],measurement_mask=data[1],stable_cell_keys=data[2],operator_ids=data[3],scientific_cell_weights=data[4],target_block_views=data[5],measured_tokens_by_operator=data[6],max_teacher_tokens_per_microbatch=budget,run_seed=8113002,update_index=update,ema_momentum=.996)


def _states_equal(a,b):
    for left,right in ((a.online,b.online),(a.teacher,b.teacher),(a.predictor,b.predictor)):
        sa=left.state_dict(); sb=right.state_dict(); assert sa.keys()==sb.keys()
        for name in sa: assert torch.equal(sa[name].cpu(),sb[name].cpu()),name


def test_device_candidate_parameter_registry_is_reference_compatible():
    a=KeyedIPBEncoderV2Reference(width=16,heads=4,blocks=2,ffn_width=24,dropout=.1,vocabulary_size=32)
    b=KeyedIPBEncoderV2DeviceCandidate(width=16,heads=4,blocks=2,ffn_width=24,dropout=.1,vocabulary_size=32)
    assert a.state_dict().keys()==b.state_dict().keys()
    b.load_state_dict(a.state_dict(),strict=True)


def test_cpu_device_candidate_update_is_bitwise_reference_equivalent():
    data=_case(); ref=_reference(); dev=_device()
    # Predictor initialization order is identical by construction; make the proof explicit.
    _states_equal(ref,dev)
    rr=run_inactive_reference_update(ref,**_kwargs(data))
    rd=run_inactive_reference_update(dev,**_kwargs(data))
    assert rr==rd
    _states_equal(ref,dev)


def test_cpu_device_candidate_two_update_checkpoint_resume_is_bitwise_stable():
    data=_case(); continuous=_device(); first=run_inactive_reference_update(continuous,**_kwargs(data,0))
    assert first['optimizer_step_after']==1
    ckpt=capture_reference_checkpoint(continuous,next_update_index=1,presentations_seen=6)
    resumed=_device(); assert restore_reference_checkpoint(resumed,ckpt)==(1,6)
    a=run_inactive_reference_update(continuous,**_kwargs(data,1)); b=run_inactive_reference_update(resumed,**_kwargs(data,1))
    assert a==b; _states_equal(continuous,resumed)


def test_microbatch_partition_changes_only_allowed_numerical_path_not_scientific_mass():
    data=_case(); a=_device(); b=_device()
    ra=run_inactive_reference_update(a,**_kwargs(data,0,40)); rb=run_inactive_reference_update(b,**_kwargs(data,0,80))
    assert ra['microbatch_plan']!=rb['microbatch_plan']
    assert ra['cells']==rb['cells']==6
    assert ra['scientific_weight_mass']==rb['scientific_weight_mass']==float(data[4].double().sum())
    assert abs(ra['loss']-rb['loss'])<1e-5


@pytest.mark.skipif(not torch.cuda.is_available(),reason='CUDA qualification requires a real target device')
def test_cuda_candidate_update_matches_cpu_scientific_report_and_reference_masks():
    # This is a qualification harness, not a CI claim on CPU-only runners.
    cpu_data=_case('cpu'); gpu_data=_case('cuda')
    cpu=_device('cpu'); gpu=_device('cuda'); gpu.online.load_state_dict(cpu.online.state_dict()); gpu.teacher.load_state_dict(cpu.teacher.state_dict()); gpu.predictor.load_state_dict(cpu.predictor.state_dict())
    rc=run_inactive_reference_update(cpu,**_kwargs(cpu_data))
    rg=run_inactive_reference_update(gpu,**_kwargs(gpu_data))
    assert rc['cells']==rg['cells']==6
    assert rc['views']==rg['views']==2
    assert rc['microbatch_plan']==rg['microbatch_plan']
    assert rc['scientific_weight_mass']==pytest.approx(rg['scientific_weight_mass'],rel=0,abs=1e-12)
    assert rc['optimizer_step_after']==rg['optimizer_step_after']==1
    assert rg['gradient_gate']['teacher_gradients']==0
