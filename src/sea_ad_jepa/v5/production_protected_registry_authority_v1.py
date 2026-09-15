"""Dynamic protected-tensor registry authority for current V5 geometry."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Mapping, Sequence

PROTECTED_ROLES=("attention_norm","attention.query","attention.key","attention.value")
PROTECTED_PARAMETERS=("weight","bias")
PRODUCTION_MECHANICS_CHAIN_V1=(
    "FP16_FORWARD","BACKWARD_AUTOCAST_DISABLED","UNSCALE",
    "PROTECTED_REGISTRY_GRADIENT_GATE","OPTIMIZER_STEP_PROVED_BEYOND_DECAY",
    "ADAM_EXP_AVG_PROVED","ADAM_EXP_AVG_SQ_PROVED","EMA_UPDATE",
    "SUCCESSFUL_PRESENTATION_CURSOR_ADVANCE","ATOMIC_CHECKPOINT_TELEMETRY_COMMIT",
)

def _positive_int(v: object,name:str)->int:
    if isinstance(v,bool) or not isinstance(v,int) or v<1: raise ValueError(f"{name} must be a positive integer")
    return v
def _id(v: object,name:str)->str:
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{name} must be nonempty")
    return v.strip()
def _canonical_sha(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class ProductionProtectedRegistryAuthorityV1:
    authority_id: str
    model_depth: int
    records: Sequence[Mapping[str,Any]]
    training_authorized: bool=False
    @property
    def expected_tensors(self)->int:
        return _positive_int(self.model_depth,'model_depth')*len(PROTECTED_ROLES)*len(PROTECTED_PARAMETERS)
    def normalized_records(self)->list[dict[str,Any]]:
        depth=_positive_int(self.model_depth,'model_depth'); _id(self.authority_id,'authority_id')
        if self.training_authorized is not False: raise ValueError('protected-registry authority cannot authorize training')
        if not isinstance(self.records,Sequence) or isinstance(self.records,(str,bytes)): raise ValueError('records must be a sequence')
        if len(self.records)!=self.expected_tensors: raise ValueError(f'protected registry must contain exactly {self.expected_tensors} tensors for current model_depth={depth}')
        expected={(b,r,p) for b in range(depth) for r in PROTECTED_ROLES for p in PROTECTED_PARAMETERS}
        seen=set(); names=set(); out=[]
        for row in self.records:
            if not isinstance(row,Mapping): raise ValueError('protected registry rows must be mappings')
            b=row.get('block_index'); r=row.get('role'); p=row.get('parameter'); name=row.get('tensor_name')
            if isinstance(b,bool) or not isinstance(b,int) or b not in range(depth): raise ValueError('protected block_index outside current model depth')
            if r not in PROTECTED_ROLES or p not in PROTECTED_PARAMETERS: raise ValueError('protected role/parameter outside current cross-product')
            tensor_name=_id(name,'tensor_name'); key=(b,str(r),str(p))
            if key in seen or tensor_name in names: raise ValueError('protected registry contains duplicate identity or tensor_name')
            seen.add(key); names.add(tensor_name); out.append({'block_index':b,'role':str(r),'parameter':str(p),'tensor_name':tensor_name})
        if seen!=expected: raise ValueError('protected registry is not the exact current depth x role x parameter cross-product')
        out.sort(key=lambda row:(row['block_index'],row['role'],row['parameter'],row['tensor_name']))
        return out
    def registry_sha256(self)->str:
        return _canonical_sha({'schema':'V5_PRODUCTION_PROTECTED_REGISTRY_V1','model_depth':_positive_int(self.model_depth,'model_depth'),'protected_roles':list(PROTECTED_ROLES),'protected_parameters':list(PROTECTED_PARAMETERS),'records':self.normalized_records()})
    def canonical_digest(self)->str:
        return _canonical_sha({'schema':'V5_PRODUCTION_PROTECTED_REGISTRY_AUTHORITY_V1','authority_id':_id(self.authority_id,'authority_id'),'model_depth':_positive_int(self.model_depth,'model_depth'),'expected_tensors':self.expected_tensors,'registry_sha256':self.registry_sha256(),'training_authorized':False})
    def validate(self)->None:
        self.normalized_records(); self.registry_sha256(); self.canonical_digest()
