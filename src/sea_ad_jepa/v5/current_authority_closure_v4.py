"""Exact-root current-V5 authority closure V4.

V4 is data-structure closure only: every root must already be an executed/live
authority digest. It cannot authorize training.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Mapping
from .current_authority_roots_v4 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4

def _sha(v: object, name: str) -> str:
    if not isinstance(v,str) or len(v)!=64 or v!=v.lower():
        raise ValueError(f"{name} must be lowercase SHA-256")
    int(v,16); return v

def _digest(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),
                                     ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class CurrentAuthorityClosureV4:
    authority_roots: Mapping[str,str]
    training_authorized: bool=False

    def normalized_roots(self)->dict[str,str]:
        if not isinstance(self.authority_roots, Mapping):
            raise ValueError("authority_roots must be a mapping")
        if tuple(self.authority_roots) != CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4:
            raise ValueError("authority_roots must exactly match V4 root vocabulary and order")
        return {k:_sha(self.authority_roots[k],k) for k in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4}

    def validate(self)->None:
        self.normalized_roots()
        if self.training_authorized is not False:
            raise ValueError("closure V4 cannot authorize training")

    def canonical_digest(self)->str:
        self.validate()
        return _digest({"schema":"V5_CURRENT_AUTHORITY_CLOSURE_V4",
                        "authority_roots":self.normalized_roots(),
                        "training_authorized":False})

    def as_receipt(self)->dict:
        return {"schema":"V5_CURRENT_AUTHORITY_CLOSURE_V4",
                "authority_roots":self.normalized_roots(),
                "training_authorized":False,
                "closure_digest":self.canonical_digest()}
