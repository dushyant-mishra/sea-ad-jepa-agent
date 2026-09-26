#!/usr/bin/env python3
"""Independent current-V5 candidate artifact audit, NOT final authority issuance.

Role isolation: exactly six explicit path -> exact defining class adapters; no
filename similarity matching, no promotion of historical JSON to closure root.
Uses installed source validators, checks nested registry provenance separately.
Read-only; does not open real expression or protected outcomes.
"""
from __future__ import annotations
import dataclasses, hashlib, json, pathlib, sys
from typing import Any
from sea_ad_jepa.v5.primary_representation_authority_v1 import PrimaryRepresentationAuthorityV1
from sea_ad_jepa.v5.support_estimability_authority_v1 import SupportEstimabilityAuthorityV1
from sea_ad_jepa.v5.canonical_address_registry_authority_v1 import (
    CanonicalAddressRegistryAuthorityV1, MODEL_FACING_FIELDS, PROVENANCE_ONLY_FIELDS, PROHIBITED_FIELDS,
)
from sea_ad_jepa.v5.base_training_estimand_authority_v1 import BaseTrainingEstimandAuthorityV1
from sea_ad_jepa.v5.masking_rng_replay_authority_v3 import MaskingRngReplayAuthorityV3
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v3 import MaskingQualificationParametersAuthorityV3

CANDIDATES = {
    "representation_authority_sha256": ("docs/agent/V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json", "V5_PRIMARY_REPRESENTATION_AUTHORITY_V1", PrimaryRepresentationAuthorityV1),
    "support_estimability_authority_sha256": ("docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json", "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1", SupportEstimabilityAuthorityV1),
    "canonical_address_registry_authority_sha256": ("docs/agent/V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json", "V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1", CanonicalAddressRegistryAuthorityV1),
    "base_training_estimand_sha256": ("docs/agent/V5_BASE_TRAINING_ESTIMAND_AUTHORITY_20260915.json", "V5_BASE_TRAINING_ESTIMAND_AUTHORITY_V1", BaseTrainingEstimandAuthorityV1),
    "masking_rng_replay_authority_sha256": ("analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/MASKING_RNG_REPLAY_AUTHORITY_V3.json", "V5_MASKING_RNG_REPLAY_AUTHORITY_V3", MaskingRngReplayAuthorityV3),
    "masking_qualification_parameters_authority_sha256": ("analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3.json", "V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3", MaskingQualificationParametersAuthorityV3),
}
SUBSTRATE = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
ADDRESS = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
OBSERVATION = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
SUPPORT_DIGEST = "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08"

def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _instance(root: str, data: dict[str, Any], cls: type) -> Any:
    if root == "canonical_address_registry_authority_sha256":
        a, s, o = data["ADDRESS_REGISTRY"], data["FULL104_SUBSTRATE"], data["OPERATOR_ADDRESS_OBSERVATION_STATE"]
        assert s["sha256"] == SUBSTRATE and a["sha256"] == ADDRESS and o["sha256"] == OBSERVATION, "wrong parent roles"
        assert data["field_safety"]["model_facing"] == list(MODEL_FACING_FIELDS), "unsafe model-facing fields"
        assert data["field_safety"]["provenance_only"] == list(PROVENANCE_ONLY_FIELDS), "wrong provenance fields"
        assert data["field_safety"]["prohibited"] == list(PROHIBITED_FIELDS), "unsafe prohibited field list"
        return cls(authority_id=data["authority_id"], registry_sha256=a["sha256"],
                   registry_row_count=a["row_count"], full104_block_manifest_sha256=s["sha256"],
                   observation_state_sha256=o["sha256"], recovery_provenance=a["recovery_provenance"],
                   informative_path=a["informative_path"], ordering_invariant=a["ordering_invariant"],
                   identifier_invariant=a["identifier_invariant"], training_authorized=data["training_authorized"])
    allowed = {f.name for f in dataclasses.fields(cls)}
    supplied = set(data) & allowed
    missing = {f.name for f in dataclasses.fields(cls) if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING} - supplied
    assert not missing, f"missing constructor fields: {sorted(missing)}"
    return cls(**{k: data[k] for k in supplied})

def audit(root: str, repo: pathlib.Path) -> dict:
    relative, schema, cls = CANDIDATES[root]
    p = repo / relative
    raw = p.read_bytes()
    d = json.loads(raw)
    assert d["schema"] == schema, f"schema mismatch for role {root}"
    assert d.get("training_authorized") is False, "candidate must not authorize training"
    obj = _instance(root, d, cls)
    obj.validate()
    digest = obj.canonical_digest()
    # Validate role parents; self-declared schema and hash formatting alone are insufficient.
    if root == "representation_authority_sha256":
        assert d["substrate_authority_sha256"] == SUBSTRATE and d["support_authority_sha256"] == ADDRESS
    elif root == "support_estimability_authority_sha256":
        assert d["full104_substrate_sha256"] == SUBSTRATE and d["measurement_support_authority_sha256"] == ADDRESS
    elif root == "canonical_address_registry_authority_sha256":
        assert digest == d["canonical_authority_digest"], "registry canonical digest does not match document"
        assert obj.verify_artifact(sha256=ADDRESS, row_count=41238, ordered=True, unique=True)
        assert not obj.verify_artifact(sha256=OBSERVATION, row_count=41238, ordered=True, unique=True)
    elif root == "base_training_estimand_sha256":
        assert d["population_authority_sha256"] == "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
        assert d["support_estimability_authority_sha256"] == SUPPORT_DIGEST
        assert d["support_eligibility_authority_sha256"] == ADDRESS
    elif root == "masking_rng_replay_authority_sha256":
        assert digest == d["authority_sha256"], "mask RNG canonical digest mismatch"
        assert obj.global_seed == d["global_seed"], "mask RNG seed mismatch"
        assert d["target_panel_dependency"] == "NONE__PANEL_SELECTION_MUST_NOT_REROLL_MASKS"
    elif root == "masking_qualification_parameters_authority_sha256":
        assert digest == d["parameter_authority_sha256"], "mask parameters canonical digest mismatch"
        assert d["support_estimability_authority_sha256"] == SUPPORT_DIGEST
        assert d["terminal_full104_masking_outcomes_inspected"] is False
    # Syntactic validation is not full parent-byte validation or CURRENT closure.
    return {"root_name":root, "path":relative, "file_sha256":sha_bytes(raw),
            "own_schema_validator": "PASS", "canonical_digest":digest,
            "current_full104_role_checks": "PASS", "complete_parent_bytes_rehashed":False,
            "current_v5_closure_validated":False, "training_authorized":False,
            "qualification":"CANDIDATE_SCHEMA_VALID__NOT_CLOSED"}

def run(repo: pathlib.Path, out: pathlib.Path | None = None) -> dict:
    rows = []
    for root in CANDIDATES:
        try:
            rows.append(audit(root, repo))
        except Exception as exc:
            rows.append({"root_name":root, "own_schema_validator":"FAIL",
                         "error":f"{type(exc).__name__}: {exc}",
                         "qualification":"UNVALIDATED__NOT_CLOSED","training_authorized":False})
    result={"schema":"V27_SIX_CANDIDATE_CURRENT_AUTHORITY_AUDIT_V1",
            "status":"CANDIDATE_VALIDATION_ONLY__NO_TRAINING_AUTHORITY",
            "roots_checked":len(rows),
            "candidate_valid":sum(r["own_schema_validator"]=="PASS" for r in rows),
            "closed_roots":0, "heavy_source_rehashed":False,
            "training_authorized":False,"rows":rows}
    if out: out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["candidate_valid"]!=6: raise SystemExit("STOP_CANDIDATE_VALIDATION_FAILED")
    return result

if __name__=="__main__":
    if len(sys.argv) not in (2,3): raise SystemExit("USAGE: audit.py REPO_ROOT [OUTPUT_JSON]")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]) if len(sys.argv)==3 else None)
