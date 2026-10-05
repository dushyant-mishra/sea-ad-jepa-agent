"""Prospective authority for integrating the recurrent RNA backbone with validated E2.

This binds the scientific ingredients and integration semantics. It deliberately does
not instantiate a trained teacher and cannot authorize training.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json
from typing import Any, Mapping, Tuple

APPROVED_GLOBAL_STATE = ("SOURCE_BALANCED_COMMON_RNA_STATE_BACKBONE_V1",)
APPROVED_REGULATORY_STATE = ("VALIDATED_E2_QUERY_LOCAL_REGULATORY_STATE_V1",)
APPROVED_MULTIEDGE = ("PRESERVE_EDGES__NO_GENE_COLLAPSE__SUPPORT_WEIGHT_REPORTED_V1",)
APPROVED_UNCERTAINTY = ("CARRY_MEASUREMENT_SUPPORT_AND_VALIDATION_SCOPE_V1",)
APPROVED_DOUBLE_COUNT = ("NO_SAME_STUDY_EVIDENCE_DOUBLE_COUNT_AS_INDEPENDENT_V1",)
APPROVED_TARGET = ("QUERY_LOCAL_PLUS_GLOBAL_BIOLOGICAL_STATE_V1",)

def _sha(v: object, name: str) -> str:
    if not isinstance(v, str) or len(v) != 64 or v != v.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256")
    int(v, 16)
    return v

def _enum(v: object, allowed: Tuple[str,...], name: str) -> str:
    if v not in allowed:
        raise ValueError(f"{name} must be one of {allowed!r}")
    return str(v)

def _digest(p: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",",":"),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class RnaE2TargetIntegrationAuthorityV1:
    authority_id: str
    rna_backbone_authority_sha256: str
    validated_e2_authority_sha256: str
    target_construction_authority_sha256: str
    teacher_target_semantics_authority_sha256: str
    feature_support_authority_sha256: str
    implementation_source_sha256: str
    global_state_policy_id: str
    regulatory_state_policy_id: str
    multiedge_policy_id: str
    uncertainty_policy_id: str
    double_counting_policy_id: str
    integrated_target_semantics_id: str
    protected_outcomes_used_for_integration: bool = False
    disease_labels_used_for_integration: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.authority_id, str) or not self.authority_id.strip():
            raise ValueError("authority_id must be nonempty")
        for name in (
            "rna_backbone_authority_sha256","validated_e2_authority_sha256",
            "target_construction_authority_sha256","teacher_target_semantics_authority_sha256",
            "feature_support_authority_sha256","implementation_source_sha256",
        ):
            _sha(getattr(self, name), name)
        _enum(self.global_state_policy_id, APPROVED_GLOBAL_STATE, "global_state_policy_id")
        _enum(self.regulatory_state_policy_id, APPROVED_REGULATORY_STATE, "regulatory_state_policy_id")
        _enum(self.multiedge_policy_id, APPROVED_MULTIEDGE, "multiedge_policy_id")
        _enum(self.uncertainty_policy_id, APPROVED_UNCERTAINTY, "uncertainty_policy_id")
        _enum(self.double_counting_policy_id, APPROVED_DOUBLE_COUNT, "double_counting_policy_id")
        _enum(self.integrated_target_semantics_id, APPROVED_TARGET, "integrated_target_semantics_id")
        if self.protected_outcomes_used_for_integration is not False:
            raise ValueError("protected outcomes may not construct the integrated target")
        if self.disease_labels_used_for_integration is not False:
            raise ValueError("disease labels may not construct the integrated target")
        if self.training_authorized is not False:
            raise ValueError("integration authority cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        return _digest({"schema":"V5_RNA_E2_TARGET_INTEGRATION_AUTHORITY_V1", **asdict(self),
                        "training_authorized":False})
