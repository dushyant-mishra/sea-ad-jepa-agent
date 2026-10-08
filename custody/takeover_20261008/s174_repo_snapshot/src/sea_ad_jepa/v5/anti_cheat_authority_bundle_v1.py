"""Hash-bound bundle of independent anti-shortcut qualification authorities."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json
from typing import Any, Mapping

def _id(v:object,name:str)->str:
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{name} must be nonempty")
    return v.strip()
def _sha(v:object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
@dataclass(frozen=True)
class AntiCheatAuthorityBundleV1:
    authority_id: str
    target_identity_gate_authority_sha256: str
    masking_authority_sha256: str
    measurement_robustness_authority_sha256: str
    observation_gradient_firewall_authority_sha256: str
    critical_test_authority_sha256: str
    training_authorized: bool=False
    def validate(self)->None:
        _id(self.authority_id,'authority_id')
        for name in ('target_identity_gate_authority_sha256','masking_authority_sha256','measurement_robustness_authority_sha256','observation_gradient_firewall_authority_sha256','critical_test_authority_sha256'):
            _sha(getattr(self,name),name)
        if self.training_authorized is not False: raise ValueError('anti-cheat bundle cannot authorize training')
    def canonical_digest(self)->str:
        self.validate(); return _digest({'schema':'V5_ANTI_CHEAT_AUTHORITY_BUNDLE_V1',**asdict(self),'training_authorized':False})
