"""Prospective deep-model measurement-robustness decision authority."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json
from typing import Any, Mapping

def _nonempty(v: object, name: str) -> str:
    if not isinstance(v, str) or not v.strip(): raise ValueError(f"{name} must be nonempty")
    return v.strip()
def _sha(v: object, name: str) -> str:
    if not isinstance(v, str) or len(v)!=64 or v != v.lower(): raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try: int(v,16)
    except ValueError as exc: raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return v
def _nonnegative_int(v: object, name: str) -> int:
    if isinstance(v,bool) or not isinstance(v,int) or v < 0: raise ValueError(f"{name} must be a nonnegative integer")
    return v
def _positive_int(v: object, name: str) -> int:
    if isinstance(v,bool) or not isinstance(v,int) or v < 1: raise ValueError(f"{name} must be a positive integer")
    return v
def _digest(payload: Mapping[str,Any]) -> str:
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()
@dataclass(frozen=True)
class MeasurementRobustnessDecisionAuthorityV1:
    authority_id: str
    representation_authority_sha256: str
    teacher_target_semantics_sha256: str
    perturbation_protocol_authority_sha256: str
    primary_metric_id: str
    acceptance_margin_numerator: int
    acceptance_margin_denominator: int
    stratification_guardrail_authority_sha256: str
    failure_semantics_id: str
    training_authorized: bool=False
    @property
    def acceptance_margin(self) -> float:
        return self.acceptance_margin_numerator/self.acceptance_margin_denominator
    def validate(self)->None:
        _nonempty(self.authority_id,'authority_id')
        _sha(self.representation_authority_sha256,'representation_authority_sha256')
        _sha(self.teacher_target_semantics_sha256,'teacher_target_semantics_sha256')
        _sha(self.perturbation_protocol_authority_sha256,'perturbation_protocol_authority_sha256')
        _nonempty(self.primary_metric_id,'primary_metric_id')
        n=_nonnegative_int(self.acceptance_margin_numerator,'acceptance_margin_numerator')
        d=_positive_int(self.acceptance_margin_denominator,'acceptance_margin_denominator')
        if n>d: raise ValueError('acceptance_margin must lie in the closed unit interval')
        _sha(self.stratification_guardrail_authority_sha256,'stratification_guardrail_authority_sha256')
        _nonempty(self.failure_semantics_id,'failure_semantics_id')
        if self.training_authorized is not False: raise ValueError('measurement-robustness authority cannot authorize training')
    def canonical_digest(self)->str:
        self.validate(); return _digest({'schema':'V5_MEASUREMENT_ROBUSTNESS_DECISION_AUTHORITY_V1',**asdict(self),'training_authorized':False})
