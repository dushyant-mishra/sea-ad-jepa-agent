"""Task 6 navigation-only gate inventory, never a qualification registry.

Historical source commit identities locate engineering candidates; they are NOT
complete Task3 unit identities (producer, executor, policy, metric, reference,
falsifier, actor and manifest hashes remain unavailable). The only lawful
initial action is to emit a blocked, nonpromoting registration proposal.
"""
from __future__ import annotations

from copy import deepcopy
from scripts.v5.td_unified.canonical_v1 import canonical_sha256


class GateRegistrationError(ValueError):
    pass


# Closed inventory from the independently reviewed controlling Task 6 plan.
# HEADS ARE NAVIGATION ONLY. Never auto-update them to newer candidate PRs.
_NAVIGATION = (
    ("G8", "95dd474a02ce571722df9e8f08b42e81af2e8736", "ESTIMAND_REFERENCE_PRODUCER"),
    ("G6", "4110d4478c3353d86740dd135d62460ff7a7611f", "MEASUREMENT_MARGIN_RECEIPT"),
    ("G9_S1_S2", "8d6b23a18051f64463ee9b2649f4fe5fc7123f0d", "SUPPORT_NULL_AND_EIGENGAP"),
    ("R1", "949d76ff03cb57c5a88fef9efdb79fced9154024", "Y_CELL_NULL_PRODUCER"),
    ("G2", "42df903d6190b7aa1b8eb65d810ab813cd327445", "CANDIDATE_STATIC_REFERENCE"),
    ("G7", "5a711f9a4ea0328445a05dadc1e011efb16a3c13", "E3_AUTHENTIC_CONTENT_AND_A7"),
    ("R4_C6_C4", "b7c317c640aa231a7d5ec1fa12271a39bfee86e6", "CANDIDATE_ENDPOINTS_AND_REFERENCES"),
    ("G12", "01ebdb9384b42d5cfae3de03c2adf5b6b327ee81", "SCOPED_HUMAN_SUPPORT"),
    ("TD_SYSTEM_BATTERY_V3", "651d7a5a1d4f4047d5ac875cc603f9151c2fed36", "SYSTEM_MECHANICS_NOT_COMPONENT_BIOLOGY"),
)


def current_repaired_unit_descriptors() -> tuple[dict[str, object], ...]:
    """Return detached proposals with no registry effects or implied PASS."""
    out = []
    for unit_id, sha, blocker in _NAVIGATION:
        out.append({
            "schema": "TASK6_INITIAL_GATE_NAVIGATION_DESCRIPTOR_V1",
            "unit_id": unit_id,
            "navigation_commit_sha": sha,
            "max_unreviewed_stage": "FIXTURE_SAME_INTERFACE",
            "effective_stage": "SEMANTICS_ONLY",
            "active_status": "NOT_REGISTERED",
            "required_missing_evidence": [
                blocker, "TASK3_COMPLETE_UNIT_IDENTITY", "MANIFEST_ACCESS_RAW_AUTHORITY",
                "INDEPENDENT_A7_PATH_AND_ISSUER_PROOF",
            ],
            "restrictions": [
                "NO_INHERITED_GATE_PASS", "NO_HUMAN_EXECUTION",
                "NO_TRAINING_AUTHORITY",
            ],
            "externally_authenticated": False,
            "authority_effect": "NONE",
        })
    return tuple(deepcopy(out))


def register_initial_repaired_units(*, caller_promotions=None):
    """Do not mint a fake RegistryUnit by filling missing fields with hashes.

    This does not write or mutate a TDQualificationRegistry. The real promotion
    path is retained in accepted Task3; once independently authenticated source
    identities and A7 receipts exist, that path must be exercised separately.
    """
    if caller_promotions is not None:
        raise GateRegistrationError("caller PASS/stage/code claims cannot register an unqualified unit")
    proposals = current_repaired_unit_descriptors()
    body = {
        "schema":"TASK6_GATE_REGISTRATION_BLOCKED_PROPOSAL_V1",
        "status":"REGISTRATION_BLOCKED_PENDING_AUTHENTICATED_UNIT_IDENTITIES",
        "descriptors":list(proposals),
        "registered_qualification_units":[],
        "registry_mutated":False,
        "system_mechanics_grant_component_authority":False,
        "human_executable":False,
        "training_authorized":False,
        "authority_effect":"NONE",
    }
    body["proposal_sha256"]=canonical_sha256(body)
    return body
