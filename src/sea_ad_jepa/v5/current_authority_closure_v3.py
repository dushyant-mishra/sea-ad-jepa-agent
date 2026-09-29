"""V3 augmentation closure: promote specificity, q-safety, and provider execution to roots."""
from __future__ import annotations
import hashlib,json
from typing import Any,Mapping
from .biological_specificity_authority_v1 import BiologicalSpecificityAuthorityV1
from .critical_test_execution_authority_v2 import CriticalTestExecutionAuthorityV2
from .current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
from .current_authority_roots_v3 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3
from .q_safety_authority_v1 import QSafetyAuthorityV1

def _sha(v:object,n:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():raise ValueError(f"{n} must be lowercase SHA-256")
    try:int(v,16)
    except ValueError as e:raise ValueError(f"{n} must be lowercase SHA-256") from e
    return v
def _digest(p:Mapping[str,Any])->str:return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def _closure_v2_digest(c:Mapping[str,Any])->str:
    if not isinstance(c,Mapping) or c.get("schema")!="V5_CURRENT_AUTHORITY_CLOSURE_V2" or c.get("training_authorized") is not False:raise ValueError("closure_v2 schema/state mismatch")
    r=c.get("authority_roots")
    if not isinstance(r,Mapping) or tuple(r)!=CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2:raise ValueError("closure_v2 roots mismatch")
    nr={k:_sha(r[k],k) for k in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}; expected=_digest({"schema":"V5_CURRENT_AUTHORITY_CLOSURE_V2","authority_roots":nr,"training_authorized":False})
    observed=_sha(c.get("closure_digest"),"closure_digest")
    if observed!=expected:raise ValueError("closure_v2 digest mismatch")
    return observed
def validate_current_v5_authority_closure_v3(*,closure_v2:Mapping[str,Any],biological_specificity:BiologicalSpecificityAuthorityV1,q_safety:QSafetyAuthorityV1,critical_test_v2:CriticalTestExecutionAuthorityV2)->dict[str,Any]:
    base=_closure_v2_digest(closure_v2); roots=dict(closure_v2["authority_roots"])
    if not isinstance(biological_specificity,BiologicalSpecificityAuthorityV1):raise ValueError("biological_specificity must use V1")
    if not isinstance(q_safety,QSafetyAuthorityV1):raise ValueError("q_safety must use V1")
    if not isinstance(critical_test_v2,CriticalTestExecutionAuthorityV2):raise ValueError("critical_test_v2 must use V2")
    biological_specificity.validate();q_safety.validate();critical_test_v2.validate()
    target=roots["target_construction_authority_sha256"]
    if biological_specificity.target_construction_authority_sha256!=target:raise ValueError("biological-specificity target root mismatch")
    if q_safety.target_construction_authority_sha256!=target:raise ValueError("q-safety target root mismatch")
    if critical_test_v2.predecessor_v1_sha256!=roots["critical_test_authority_sha256"]:raise ValueError("critical-test V2 predecessor mismatch")
    roots["biological_specificity_authority_sha256"]=biological_specificity.canonical_digest()
    roots["q_safety_authority_sha256"]=q_safety.canonical_digest()
    roots["critical_test_v2_authority_sha256"]=critical_test_v2.canonical_digest()
    if tuple(roots)!=CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3:raise RuntimeError("internal V3 root order mismatch")
    core={"schema":"V5_CURRENT_AUTHORITY_CLOSURE_V3","predecessor_closure_v2_sha256":base,"authority_roots":roots,"training_authorized":False}
    return {**core,"closure_digest":_digest(core)}
