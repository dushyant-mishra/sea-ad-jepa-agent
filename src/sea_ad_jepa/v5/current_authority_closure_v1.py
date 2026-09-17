"""Cross-authority closure checks for current V5; produces roots, never training authority."""
from __future__ import annotations
import hashlib, json
from typing import Any, Mapping
from .base_training_estimand_recovery_v1 import validate_current_recovered_base_estimand_v1
from .current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS, CURRENT_V5_RECEIPT_AUTHORITY_ROOTS
from .current_masking_policy_authority_v2 import CurrentMaskingPolicyAuthorityV2
from .current_target_address_provider_authority_v1 import CurrentTargetAddressProviderAuthorityV1

def _sha(v:object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _auth(obj:Any,name:str)->str:
    if getattr(obj,'training_authorized',False) is not False: raise ValueError(f'{name} unexpectedly authorizes training')
    obj.validate()
    return _sha(obj.canonical_digest(),f'{name} canonical digest')
def _eq(actual:object,expected:str,message:str)->None:
    if actual!=expected: raise ValueError(message)
def _require_current_successor_schemas(*,target_address:Any,masking:Any)->None:
    if not isinstance(target_address,CurrentTargetAddressProviderAuthorityV1):
        raise ValueError('target_address must use the current target-address provider schema')
    if not isinstance(masking,CurrentMaskingPolicyAuthorityV2):
        raise ValueError('masking must use the current masking policy schema')

def validate_current_v5_authority_closure_v1(*,full104_substrate_sha256:str,representation:Any,support_estimability:Any,base_training_weight_law:Any,base_training_estimand:Any,target_address:Any,masking:Any,ema:Any,teacher_target:Any,measurement_robustness:Any,target_identity_gate:Any,critical_test:Any,anti_cheat:Any,model_geometry:Any,protected_registry:Any,preexecution:Any,observation_gradient_firewall_authority_sha256:str,schedule_authority_sha256:str,runtime_source_sha256:str)->dict[str,Any]:
    _require_current_successor_schemas(target_address=target_address,masking=masking)
    full=_sha(full104_substrate_sha256,'full104_substrate_sha256'); schedule=_sha(schedule_authority_sha256,'schedule_authority_sha256'); runtime=_sha(runtime_source_sha256,'runtime_source_sha256'); firewall=_sha(observation_gradient_firewall_authority_sha256,'observation_gradient_firewall_authority_sha256')
    rep=_auth(representation,'representation'); support=_auth(support_estimability,'support_estimability'); est=_auth(base_training_estimand,'base_training_estimand'); address=_auth(target_address,'target_address'); mask=_auth(masking,'masking'); ema_sha=_auth(ema,'ema'); teacher=_auth(teacher_target,'teacher_target'); measurement=_auth(measurement_robustness,'measurement_robustness'); identity=_auth(target_identity_gate,'target_identity_gate'); critical=_auth(critical_test,'critical_test'); anticheat=_auth(anti_cheat,'anti_cheat'); registry=_auth(protected_registry,'protected_registry'); geometry=_auth(model_geometry,'model_geometry'); pre=_auth(preexecution,'preexecution')

    validate_current_recovered_base_estimand_v1(base_training_weight_law,base_training_estimand)
    _eq(getattr(representation,'substrate_authority_sha256',None),full,'representation substrate root mismatch')
    _eq(getattr(support_estimability,'full104_substrate_sha256',None),full,'support substrate root mismatch')
    _eq(getattr(support_estimability,'measurement_support_authority_sha256',None),getattr(representation,'support_authority_sha256',None),'support measurement root mismatch')
    _eq(getattr(base_training_estimand,'support_estimability_authority_sha256',None),support,'estimand support root mismatch')
    _eq(getattr(ema,'base_training_estimand_sha256',None),est,'EMA base-training estimand root mismatch')
    _eq(getattr(ema,'schedule_authority_sha256',None),schedule,'EMA schedule root mismatch')
    _eq(getattr(teacher_target,'representation_authority_sha256',None),rep,'teacher representation root mismatch')
    _eq(getattr(teacher_target,'support_estimability_authority_sha256',None),support,'teacher support root mismatch')
    _eq(getattr(teacher_target,'target_address_query_authority_sha256',None),address,'teacher target-address root mismatch')
    _eq(getattr(teacher_target,'scientific_weight_authority_sha256',None),est,'teacher scientific-weight estimand root mismatch')
    _eq(getattr(teacher_target,'masking_authority_sha256',None),mask,'teacher masking root mismatch')
    _eq(getattr(teacher_target,'ema_boundary_authority_sha256',None),ema_sha,'teacher EMA root mismatch')
    _eq(getattr(measurement_robustness,'representation_authority_sha256',None),rep,'measurement representation root mismatch')
    _eq(getattr(measurement_robustness,'teacher_target_semantics_sha256',None),teacher,'measurement teacher-target root mismatch')
    _eq(getattr(target_identity_gate,'teacher_target_semantics_sha256',None),teacher,'target-identity teacher root mismatch')
    _eq(getattr(target_identity_gate,'representation_authority_sha256',None),rep,'target-identity representation root mismatch')
    _eq(getattr(target_identity_gate,'base_training_estimand_sha256',None),est,'target-identity estimand root mismatch')
    _eq(getattr(target_identity_gate,'masking_authority_sha256',None),mask,'target-identity masking root mismatch')
    _eq(getattr(anti_cheat,'target_identity_gate_authority_sha256',None),identity,'anti-cheat target-identity root mismatch')
    _eq(getattr(anti_cheat,'masking_authority_sha256',None),mask,'anti-cheat masking root mismatch')
    _eq(getattr(anti_cheat,'measurement_robustness_authority_sha256',None),measurement,'anti-cheat measurement-robustness root mismatch')
    _eq(getattr(anti_cheat,'observation_gradient_firewall_authority_sha256',None),firewall,'anti-cheat observation-firewall root mismatch')
    _eq(getattr(anti_cheat,'critical_test_authority_sha256',None),critical,'anti-cheat critical-test root mismatch')
    _eq(getattr(model_geometry,'protected_registry_authority_sha256',None),registry,'model-geometry protected-registry root mismatch')

    roots={
        'full104_substrate_sha256':full,
        'representation_authority_sha256':rep,
        'support_estimability_authority_sha256':support,
        'base_training_estimand_sha256':est,
        'teacher_target_semantics_sha256':teacher,
        'target_address_query_authority_sha256':address,
        'masking_authority_sha256':mask,
        'model_geometry_authority_sha256':geometry,
        'schedule_authority_sha256':schedule,
        'ema_authority_sha256':ema_sha,
        'anti_cheat_authority_sha256':anticheat,
        'runtime_source_sha256':runtime,
    }
    if tuple(roots)!=CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS: raise RuntimeError('internal upstream root order mismatch')
    if preexecution.normalized_roots()!=roots: raise ValueError('preexecution authority roots mismatch')
    _eq(getattr(preexecution,'protected_registry_authority_sha256',None),registry,'preexecution protected-registry root mismatch')
    _eq(getattr(preexecution,'critical_test_authority_sha256',None),critical,'preexecution critical-test root mismatch')

    receipt_roots={name:(pre if name=='preexecution_authority_sha256' else roots[name]) for name in CURRENT_V5_RECEIPT_AUTHORITY_ROOTS}
    payload={'schema':'V5_CURRENT_AUTHORITY_CLOSURE_V1','authority_roots':roots,'receipt_authority_roots':receipt_roots,'protected_registry_authority_sha256':registry,'critical_test_authority_sha256':critical,'training_authorized':False}
    return {**payload,'closure_digest':_digest(payload)}
