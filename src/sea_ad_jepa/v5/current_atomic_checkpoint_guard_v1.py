"""Atomic checkpoint authority validator for current V5 roots and neutral telemetry."""
from __future__ import annotations
import hashlib, json
from typing import Any, Mapping, Sequence
from .current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS
from .production_protected_registry_authority_v1 import ProductionProtectedRegistryAuthorityV1

def _sha(v:object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _id(v:object,name:str)->str:
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{name} must be nonempty")
    return v.strip()
def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _roots(v:object)->dict[str,str]:
    if not isinstance(v,Mapping) or set(v)!=set(CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS): raise ValueError('authority_roots must exactly match current upstream roots')
    return {name:_sha(v[name],name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS}
def _telemetry(v:object)->dict[str,str]:
    if not isinstance(v,Mapping) or not v: raise ValueError('telemetry sections must be a nonempty mapping')
    return {str(_id(k,'telemetry section')):_sha(value,f'telemetry {k}') for k,value in sorted(v.items())}
def _gates(v:object)->dict[str,bool]:
    if not isinstance(v,Mapping) or not v: raise ValueError('forbidden_gate_states must be a nonempty mapping')
    out={}
    for k,value in sorted(v.items()):
        key=_id(k,'forbidden gate')
        if not isinstance(value,bool): raise ValueError('forbidden gate states must be boolean')
        if value: raise ValueError(f'forbidden gate {key} is open')
        out[key]=False
    return out
def _core(*,authority_roots:object,preexecution_authority_sha256:str,protected_registry:ProductionProtectedRegistryAuthorityV1,critical_test_authority_sha256:str,telemetry_section_sha256_by_name:object,forbidden_gate_states:object)->dict[str,Any]:
    protected_registry.validate()
    return {'kind':'v5_current_atomic_checkpoint_v1','authority_roots':_roots(authority_roots),'preexecution_authority_sha256':_sha(preexecution_authority_sha256,'preexecution_authority_sha256'),'protected_registry_authority_sha256':protected_registry.canonical_digest(),'protected_tensor_count':protected_registry.expected_tensors,'critical_test_authority_sha256':_sha(critical_test_authority_sha256,'critical_test_authority_sha256'),'telemetry_section_sha256_by_name':_telemetry(telemetry_section_sha256_by_name),'forbidden_gate_states':_gates(forbidden_gate_states),'training_authorized':False}
def seal_current_atomic_checkpoint_v1(**kwargs:Any)->dict[str,Any]:
    core=_core(**kwargs); return {**core,'checkpoint_digest':_digest(core)}
def validate_current_atomic_checkpoint_v1(checkpoint:Mapping[str,Any],*,expected_authority_roots:Mapping[str,str],expected_preexecution_authority_sha256:str,protected_registry:ProductionProtectedRegistryAuthorityV1,expected_critical_test_authority_sha256:str,required_telemetry_sections:Sequence[str],forbidden_gate_names:Sequence[str])->dict[str,Any]:
    if not isinstance(checkpoint,Mapping): raise ValueError('checkpoint must be a mapping')
    expected_fields={'kind','authority_roots','preexecution_authority_sha256','protected_registry_authority_sha256','protected_tensor_count','critical_test_authority_sha256','telemetry_section_sha256_by_name','forbidden_gate_states','training_authorized','checkpoint_digest'}
    if set(checkpoint)!=expected_fields: raise ValueError('checkpoint fields must exactly match current schema')
    if checkpoint.get('kind')!='v5_current_atomic_checkpoint_v1': raise ValueError('checkpoint kind mismatch')
    if checkpoint.get('training_authorized') is not False: raise ValueError('checkpoint cannot authorize training')
    protected_registry.validate()
    if checkpoint.get('protected_tensor_count')!=protected_registry.expected_tensors: raise ValueError('protected_tensor_count mismatch')
    telemetry=checkpoint.get('telemetry_section_sha256_by_name')
    if not isinstance(telemetry,Mapping) or set(telemetry)!=set(required_telemetry_sections): raise ValueError('telemetry sections mismatch')
    gates=checkpoint.get('forbidden_gate_states')
    if not isinstance(gates,Mapping) or set(gates)!=set(forbidden_gate_names): raise ValueError('forbidden gate names mismatch')
    core=_core(authority_roots=checkpoint.get('authority_roots'),preexecution_authority_sha256=checkpoint.get('preexecution_authority_sha256'),protected_registry=protected_registry,critical_test_authority_sha256=checkpoint.get('critical_test_authority_sha256'),telemetry_section_sha256_by_name=telemetry,forbidden_gate_states=gates)
    if core['authority_roots']!=_roots(expected_authority_roots): raise ValueError('authority_roots mismatch')
    if core['preexecution_authority_sha256']!=_sha(expected_preexecution_authority_sha256,'expected_preexecution_authority_sha256'): raise ValueError('preexecution authority mismatch')
    if core['critical_test_authority_sha256']!=_sha(expected_critical_test_authority_sha256,'expected_critical_test_authority_sha256'): raise ValueError('critical-test authority mismatch')
    if checkpoint.get('protected_registry_authority_sha256')!=protected_registry.canonical_digest(): raise ValueError('protected registry authority mismatch')
    digest=_sha(checkpoint.get('checkpoint_digest'),'checkpoint_digest')
    if digest!=_digest(core): raise ValueError('checkpoint digest mismatch')
    return {**core,'checkpoint_digest':digest}
