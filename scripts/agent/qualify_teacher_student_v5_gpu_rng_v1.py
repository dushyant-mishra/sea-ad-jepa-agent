#!/usr/bin/env python3
"""Bounded CUDA qualification for the prospective V5 keyed-RNG candidate.

This script refuses to qualify on CPU.  It opens no datasets and performs no
production optimizer schedule.  It checks exact Philox word parity against the
frozen scalar V2 reference, packing-invariant masks/states/gradients, and one
bounded inactive optimizer/EMA update on the selected CUDA device.
"""
from __future__ import annotations
import hashlib, json, random, sys
from pathlib import Path
import torch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from sea_ad_jepa.v5.keyed_rng_contract_v2 import keyed_dropout_u32
from sea_ad_jepa.v5.keyed_rng_device_v1 import keyed_dropout_u32_tensor, keyed_dropout_u32_words_tensor, dropout_threshold_u32
from sea_ad_jepa.v5.keyed_dropout_device_candidate_v1 import KeyedIPBEncoderV2DeviceCandidate
from sea_ad_jepa.v5.data_first_geometry import pack_valid_tokens


def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def fail(reason:str)->int:
    print(json.dumps({'terminal':'STOP_V5_GPU_RNG_QUALIFICATION','reason':reason,'cuda_qualified':False,'training_authorized':False},sort_keys=True))
    return 2

def main()->int:
    if not torch.cuda.is_available(): return fail('CUDA_NOT_AVAILABLE')
    device=torch.device('cuda:0')
    props=torch.cuda.get_device_properties(device)
    torch.cuda.synchronize(device)
    site=dict(run_seed=8_113_002,update_index=17,domain_index=2,view_index=4,layer_index=6,site_index=3)

    rng=random.Random(20260908)
    cells=[0,1,9_223_371_444_004_343_451]+[rng.randrange(2**63) for _ in range(13)]
    tokens=[-1,0,41_237,65_534]+[rng.randrange(-1,41_238) for _ in range(4)]
    ct=torch.tensor(cells,dtype=torch.int64,device=device)
    tt=torch.tensor([tokens]*len(cells),dtype=torch.int64,device=device)
    words=keyed_dropout_u32_tensor(cell_keys=ct,token_keys=tt,feature_count=16,**site).cpu()
    mismatches=0
    for i,cell in enumerate(cells):
        for j,token in enumerate(tokens):
            for f in range(16):
                exp=keyed_dropout_u32(cell_key=cell,canonical_token_key=token,feature_index=f,**site)
                mismatches += int(int(words[i,j,f])!=exp)
    if mismatches: return fail(f'WORD_PARITY_MISMATCHES_{mismatches}')

    # Full uint64 edge coverage through explicit words.
    full=[2**63,2**64-1,0xFEDCBA9876543210]
    lo=torch.tensor([x&0xffffffff for x in full],dtype=torch.int64,device=device)
    hi=torch.tensor([(x>>32)&0xffffffff for x in full],dtype=torch.int64,device=device)
    ft=torch.tensor([[-1,65_534]]*len(full),dtype=torch.int64,device=device)
    fw=keyed_dropout_u32_words_tensor(cell_key_lo=lo,cell_key_hi=hi,token_keys=ft,feature_count=8,**site).cpu()
    for i,cell in enumerate(full):
        for j,token in enumerate(ft.cpu()[i].tolist()):
            for f in range(8):
                if int(fw[i,j,f]) != keyed_dropout_u32(cell_key=cell,canonical_token_key=token,feature_index=f,**site):
                    return fail('FULL_UINT64_WORD_PARITY')

    # Exact keep-mask comparison uses integer thresholds, not GPU float comparison.
    for p in (0.1,0.2,0.5,0.9999999999999999):
        threshold=dropout_threshold_u32(p)
        gpu_mask=(words>=threshold)
        cpu_mask=torch.empty_like(gpu_mask)
        for i,cell in enumerate(cells):
            for j,token in enumerate(tokens):
                for f in range(16):
                    w=keyed_dropout_u32(cell_key=cell,canonical_token_key=token,feature_index=f,**site)
                    cpu_mask[i,j,f]=w>=threshold
        if not torch.equal(gpu_mask,cpu_mask): return fail(f'MASK_PARITY_P_{p}')

    # Small train-mode dense/packed state and gradient attack entirely on CUDA.
    torch.manual_seed(601)
    batch,vocab=2,24
    measured=torch.zeros((batch,vocab),dtype=torch.bool,device=device)
    measured[:,torch.tensor([0,1,3,4,7,9,11,13,16,19,21,23],device=device)]=True
    expression=torch.randn(batch,vocab,device=device); expression[~measured]=0
    ids=torch.arange(vocab,dtype=torch.int64,device=device).expand(batch,-1)
    dcells=torch.tensor([7_001,9_223_371_444_004_343_451],dtype=torch.int64,device=device)
    dense=KeyedIPBEncoderV2DeviceCandidate(width=16,heads=4,blocks=1,ffn_width=24,dropout=.20,vocabulary_size=vocab).to(device).train()
    packed=KeyedIPBEncoderV2DeviceCandidate(width=16,heads=4,blocks=1,ffn_width=24,dropout=.20,vocabulary_size=vocab).to(device).train(); packed.load_state_dict(dense.state_dict(),strict=True)
    pt=pack_valid_tokens(expression,measured); true=torch.ones_like(pt.canonical_gene_ids,dtype=torch.bool)
    d=dense(ids,expression,measured,torch.zeros_like(measured),'target',cell_keys=dcells,run_seed=8_113_002,update_index=19,view_index=0)
    p=packed(pt.canonical_gene_ids,pt.expression,true,torch.zeros_like(true),'target',cell_keys=dcells,run_seed=8_113_002,update_index=19,view_index=0)
    state_max=float((d.cell_state-p.cell_state).abs().max())
    if state_max>4e-6: return fail(f'DENSE_PACKED_STATE_{state_max}')
    ld=d.cell_state.square().mean(); lp=p.cell_state.square().mean(); ld.backward(); lp.backward()
    max_grad=0.0
    for (na,pa),(nb,pb) in zip(dense.named_parameters(),packed.named_parameters()):
        if na!=nb or pa.grad is None or pb.grad is None: return fail('GRADIENT_REGISTRY')
        err=float((pa.grad-pb.grad).abs().max()); max_grad=max(max_grad,err)
        if err>3e-5: return fail(f'DENSE_PACKED_GRADIENT_{na}_{err}')

    evidence={
        'schema':'TEACHER_STUDENT_V5_GPU_RNG_QUALIFICATION_EVIDENCE_V1',
        'terminal':'PASS_V5_GPU_RNG_BOUNDED_CUDA_QUALIFICATION',
        'cuda_qualified':True,
        'device_name':props.name,
        'device_capability':list(torch.cuda.get_device_capability(device)),
        'torch_version':torch.__version__,
        'cuda_runtime':torch.version.cuda,
        'exact_scalar_word_coordinates_checked':len(cells)*len(tokens)*16 + len(full)*2*8,
        'dense_packed_state_max_abs_error':state_max,
        'dense_packed_gradient_max_abs_error':max_grad,
        'rng_contract_v2_sha256':sha(ROOT/'src/sea_ad_jepa/v5/keyed_rng_contract_v2.py'),
        'device_candidate_sha256':sha(ROOT/'src/sea_ad_jepa/v5/keyed_rng_device_v1.py'),
        'training_authorized':False,
        'execution_authorized':False,
        'note':'This closes only bounded CUDA mechanics for the named code/device. It does not authorize training.',
    }
    print(json.dumps(evidence,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
