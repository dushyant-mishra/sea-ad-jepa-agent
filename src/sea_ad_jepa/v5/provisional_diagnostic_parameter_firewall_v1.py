"""V26 diagnostic-only parameter provenance firewall; not an execution authorization.

Purpose: stop circular D_shared -> width selection, historical numerical defaults
and unqualified synthetic results from entering current V5 as scientific claims.
This pure CPU contract must be invoked by a later reviewed GPU-laptop entrypoint;
constructing a manifest alone never permits running a model.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import json
from typing import Any, Mapping

SCHEMA = "V26_PROVISIONAL_JEPA_DIAGNOSTIC_PARAMETER_MANIFEST_V1"
PHASES = ("ENGINEERING_SMOKE_ONLY", "READER_FIT_DEVELOPMENT_DIAGNOSTIC")
PROVENANCE = {
    "model_width": "EXPLICIT_RESOURCE_BOUNDED_DIAGNOSTIC_ONLY",
    "model_depth": "EXPLICIT_RESOURCE_BOUNDED_DIAGNOSTIC_ONLY",
    "attention_heads": "EXPLICIT_RESOURCE_BOUNDED_DIAGNOSTIC_ONLY",
    "presentations_per_update": "EXPLICIT_FROZEN_DEVELOPMENT_SCHEDULE",
    "maximum_updates": "EXPLICIT_FROZEN_DEVELOPMENT_SCHEDULE",
    "max_teacher_tokens_per_microbatch": "EXPLICIT_RESOURCE_BOUNDED_DIAGNOSTIC_ONLY",
    "ema_half_life_presentations": "EXPLICIT_FROZEN_DEVELOPMENT_SCHEDULE",
}
SHA_ROOTS = (
    "source_population_sha256",
    "fit_split_sha256",
    "feature_support_sha256",
    "teacher_target_candidate_sha256",
    "target_address_candidate_sha256",
    "masking_candidate_sha256",
    "scientific_weight_law_sha256",
    "schedule_candidate_sha256",
    "rng_candidate_sha256",
    "resource_budget_justification_sha256",
)
G3_ROOTS = ("g3_fit_objective_code_sha256", "g3_six_state_evidence_contract_sha256")


def _sha(v: object, name: str) -> str:
    if not isinstance(v, str) or len(v) != 64 or v.lower() != v:
        raise ValueError(f"{name}: canonical lowercase SHA-256 required")
    try:
        int(v, 16)
    except ValueError as exc:
        raise ValueError(f"{name}: canonical lowercase SHA-256 required") from exc
    return v


def _positive(v: object, name: str) -> int:
    if type(v) is not int or v < 1:
        raise ValueError(f"{name}: explicit positive integer required, no inherited default")
    return v


@dataclass(frozen=True)
class ProvisionalDiagnosticParameterManifestV1:
    phase: str
    population_role: str
    model_width: int
    model_depth: int
    attention_heads: int
    presentations_per_update: int
    maximum_updates: int
    max_teacher_tokens_per_microbatch: int
    ema_half_life_presentations: int
    run_seed: int
    source_population_sha256: str
    fit_split_sha256: str
    feature_support_sha256: str
    teacher_target_candidate_sha256: str
    target_address_candidate_sha256: str
    masking_candidate_sha256: str
    scientific_weight_law_sha256: str
    schedule_candidate_sha256: str
    rng_candidate_sha256: str
    resource_budget_justification_sha256: str
    parameter_provenance: Mapping[str, str]
    d_shared: None
    d_private: None
    d_obs: None
    qualified_dimension_authority_sha256: None
    production_geometry_authority_sha256: None
    g3_fit_objective_code_sha256: str | None
    g3_six_state_evidence_contract_sha256: str | None
    g3_primary_fit_objective: str | None
    training_authorized: bool = False

    def validate(self) -> None:
        if self.phase not in PHASES:
            raise ValueError("unknown diagnostic phase")
        if self.population_role != "READER_FIT_DISCOVERY_ONLY":
            raise ValueError("nonfit/protected population is forbidden in diagnostic")
        for key in PROVENANCE:
            _positive(getattr(self, key), key)
        if type(self.run_seed) is not int or self.run_seed < 0:
            raise ValueError("run_seed: explicit nonnegative integer required")
        if self.model_width % self.attention_heads:
            raise ValueError("diagnostic width must be divisible by declared attention heads")
        if dict(self.parameter_provenance) != PROVENANCE:
            raise ValueError("missing/altered parameter provenance or historical/default import")
        for key in SHA_ROOTS:
            _sha(getattr(self, key), key)
        if any(getattr(self, k) is not None for k in (
            "d_shared", "d_private", "d_obs",
            "qualified_dimension_authority_sha256",
            "production_geometry_authority_sha256",
        )):
            raise ValueError("diagnostic cannot claim qualified dimensions or production geometry")
        if self.training_authorized is not False:
            raise ValueError("parameter manifest never authorizes training")
        if self.phase == "READER_FIT_DEVELOPMENT_DIAGNOSTIC":
            if self.g3_primary_fit_objective != "PRODUCTION_OBJECTIVE_MATCHED":
                raise ValueError("scientific development requires prospective objective-matched G3 primary")
            for key in G3_ROOTS:
                _sha(getattr(self, key), key)
        else:
            if any(getattr(self, k) is not None for k in (*G3_ROOTS, "g3_primary_fit_objective")):
                raise ValueError("engineering-only smoke does not claim G3 scientific evaluation")

    def canonical_digest(self) -> str:
        self.validate()
        raw = json.dumps(
            {"schema": SCHEMA, **{f.name: getattr(self, f.name) for f in fields(self)}},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
        ).encode("utf-8")
        return sha256(raw).hexdigest()

    def nontraining_receipt(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": "PARAMETERS_DECLARED__NO_RUNTIME_SOURCE_ATTESTATION",
            "scope": self.phase,
            "config_sha256": self.canonical_digest(),
            "d_shared_qualified": False,
            "d_private_qualified": False,
            "d_obs_qualified": False,
            "production_geometry_qualified": False,
            "physical_roots_rehashed_here": False,
            "run_previously_started": False,
            "training_authorized": False,
            "protected_outcomes_opened": False,
        }


def from_strict_payload(payload: Mapping[str, Any]) -> ProvisionalDiagnosticParameterManifestV1:
    """Reject unrecognized keys rather than silently dropping stale defaults."""
    if not isinstance(payload, Mapping):
        raise ValueError("diagnostic manifest must be a mapping")
    expected = {f.name for f in fields(ProvisionalDiagnosticParameterManifestV1)}
    if set(payload) != expected:
        raise ValueError(f"manifest keys differ: missing={sorted(expected-set(payload))}, unexpected={sorted(set(payload)-expected)}")
    cfg = ProvisionalDiagnosticParameterManifestV1(**payload)
    cfg.validate()
    return cfg
