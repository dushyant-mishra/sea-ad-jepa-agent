#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PASS='PASS_TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_AUDIT__CUDA_AND_INDEPENDENT_VERIFIER_PENDING__TRAINING_UNAUTHORIZED'

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def req(cond:bool,msg:str)->None:
    if not cond: raise RuntimeError(msg)

def main()->int:
    manifest=ROOT/'docs/agent/TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_MANIFEST.csv'
    root=ROOT/'docs/agent/TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_ROOT.txt'
    req(manifest.is_file() and root.is_file(),'candidate manifest/root missing')
    with manifest.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    req(rows and len(rows)==len({r['path'] for r in rows}),'manifest empty or duplicate path')
    for row in rows:
        p=ROOT/row['path']; req(p.is_file(),f'missing candidate payload {p}')
        req(p.stat().st_size==int(row['bytes']),f'byte drift {p}')
        req(sha(p)==row['sha256'],f'SHA drift {p}')
    req(root.read_text().strip()==sha(manifest),'candidate root does not bind manifest bytes')

    candidate_path=ROOT/'docs/agent/TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_V1.json'
    x=json.loads(candidate_path.read_text())
    req(x['schema']=='TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_V1','schema drift')
    req(x['base_main_commit']=='b26ddcd587c7b63c8a2f327d74a86620eef66868','base main drift')
    req(x['frozen_v5_prototype']['prototype_root']=='9684f4c2b7eff1da863ae50124c6aad49d25f137a84898e05e98d2ae1f0c67ad','frozen prototype root drift')
    req((ROOT/'docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_ROOT.txt').read_text().strip()==x['frozen_v5_prototype']['prototype_root'],'repo prototype root drift')
    contract=ROOT/x['frozen_v5_prototype']['rng_contract_v2_path']
    req(sha(contract)==x['frozen_v5_prototype']['rng_contract_v2_sha256'],'frozen V2 RNG contract SHA drift')
    for key,path_key,sha_key in (
        ('device_rng','device_rng_path','device_rng_sha256'),
        ('device_encoder','device_encoder_path','device_encoder_sha256'),
        ('inactive_update_builder','inactive_update_builder_path','inactive_update_builder_sha256'),
    ):
        del key
        p=ROOT/x['candidate'][path_key]; req(sha(p)==x['candidate'][sha_key],f'{path_key} binding drift')
    req(x['candidate']['full_uint64_contract_supported'] is True,'uint64 contract narrowed')
    for forbidden in ('tensor_position_in_random_address','microbatch_ordinal_in_random_address','device_ordinal_in_random_address','packing_shape_in_random_address'):
        req(x['candidate'][forbidden] is False,f'forbidden RNG address component enabled: {forbidden}')
    req(x['cuda_qualification']['qualified'] is False and x['cuda_qualification']['evidence'] is None,'CUDA qualified without evidence')
    req(x['implementation_verifier']['terminal'] is None,'independent verifier terminal improperly self-issued')
    req(x['implementation_verifier']['status']=='PENDING_INDEPENDENT_IMPLEMENTATION_VERIFIER','verifier status drift')
    req(x['training_authorized'] is False and x['execution_authorized'] is False,'candidate opened execution')
    req(not any(bool(v) for k,v in x['authority_effect'].items() if k.startswith('authorizes_') or k.startswith('changes_')),'candidate changes frozen authority')

    selected=[r.strip() for r in (ROOT/'docs/agent/TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_TEST_SELECTION.txt').read_text().splitlines() if r.strip()]
    req(len(selected)==6 and len(selected)==len(set(selected)),'candidate test selection drift')
    for p in selected: req((ROOT/p).is_file(),f'missing selected test {p}')
    print(PASS); return 0

if __name__=='__main__': raise SystemExit(main())
