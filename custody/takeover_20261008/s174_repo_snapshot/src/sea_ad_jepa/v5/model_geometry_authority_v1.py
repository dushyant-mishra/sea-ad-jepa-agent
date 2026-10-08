"""Production geometry binding downstream of separately qualified dimension authority."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json
from typing import Any, Mapping

def _nonempty(v: object,name:str)->str:
    if not isinstance(v,str) or not v.strip(): raise ValueError(f"{name} must be nonempty")
    return v.strip()
def _sha(v: object,name:str)->str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _digest(p:Mapping[str,Any])->str:
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
@dataclass(frozen=True)
class ModelGeometryAuthorityV1:
    authority_id: str
    qualified_dimension_authority_sha256: str
    dimension_selection_artifact_sha256: str
    rank_to_geometry_rule_authority_sha256: str
    geometry_schema_id: str
    geometry_artifact_sha256: str
    protected_registry_authority_sha256: str
    training_authorized: bool=False
    def validate(self)->None:
        _nonempty(self.authority_id,'authority_id')
        _sha(self.qualified_dimension_authority_sha256,'qualified_dimension_authority_sha256')
        _sha(self.dimension_selection_artifact_sha256,'dimension_selection_artifact_sha256')
        _sha(self.rank_to_geometry_rule_authority_sha256,'rank_to_geometry_rule_authority_sha256')
        _nonempty(self.geometry_schema_id,'geometry_schema_id')
        _sha(self.geometry_artifact_sha256,'geometry_artifact_sha256')
        _sha(self.protected_registry_authority_sha256,'protected_registry_authority_sha256')
        if self.training_authorized is not False: raise ValueError('model-geometry authority cannot authorize training')
    def canonical_digest(self)->str:
        self.validate(); return _digest({'schema':'V5_MODEL_GEOMETRY_AUTHORITY_V1',**asdict(self),'training_authorized':False})
