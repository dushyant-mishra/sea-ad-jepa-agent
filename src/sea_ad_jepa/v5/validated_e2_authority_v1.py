"""Fail-closed authority for promoting E2_NOTT_CANDIDATE after independent validation.

This schema may exist prospectively, but an instance is valid only after the exact
frozen candidate, NIH-CARD design/execution, precondition bundle, and realism
qualification are all bound. It cannot authorize training.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json
from typing import Any, Mapping

PROMOTION_STATUS = "VALIDATED_WITHIN_TESTED_SCOPE"
CLAIM_SCOPE = "INDEPENDENT_NIH_CARD_RNA_ATAC_CORRESPONDENCE__TESTED_NUISANCE_CLASS_ONLY"

def _sha(v: object, name: str) -> str:
    if not isinstance(v, str) or len(v) != 64 or v != v.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256")
    int(v, 16)
    return v

def _digest(p: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",",":"),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class ValidatedE2AuthorityV1:
    authority_id: str
    e2_candidate_uncompressed_sha256: str
    e2_construction_receipt_sha256: str
    e2_independent_audit_sha256: str
    nihcard_design_contract_sha256: str
    nihcard_precondition_bundle_sha256: str
    realism_qualification_result_sha256: str
    nihcard_correspondence_result_sha256: str
    independent_correspondence_audit_sha256: str
    promotion_status: str
    claim_scope: str
    out_of_span_limitation_acknowledged: bool
    same_study_nott_accessibility_limitation_acknowledged: bool
    passed: bool
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        for name in (
            "e2_candidate_uncompressed_sha256",
            "e2_construction_receipt_sha256",
            "e2_independent_audit_sha256",
            "nihcard_design_contract_sha256",
            "nihcard_precondition_bundle_sha256",
            "realism_qualification_result_sha256",
            "nihcard_correspondence_result_sha256",
            "independent_correspondence_audit_sha256",
        ):
            _sha(getattr(self, name), name)
        if self.promotion_status != PROMOTION_STATUS:
            raise ValueError("E2 promotion status is not an approved validated state")
        if self.claim_scope != CLAIM_SCOPE:
            raise ValueError("validated E2 claim scope drift")
        if self.out_of_span_limitation_acknowledged is not True:
            raise ValueError("out-of-span limitation must be carried forward")
        if self.same_study_nott_accessibility_limitation_acknowledged is not True:
            raise ValueError("same-study Nott accessibility limitation must be carried forward")
        if self.passed is not True:
            raise ValueError("validated E2 authority requires an executed PASS")
        if self.training_authorized is not False:
            raise ValueError("validated E2 authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema":"V5_VALIDATED_E2_AUTHORITY_V1", **asdict(self),
                        "training_authorized":False})
