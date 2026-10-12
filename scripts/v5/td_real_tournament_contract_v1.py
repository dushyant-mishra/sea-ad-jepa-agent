"""Outcome-blind execution contract for the real target tournament.

This module binds the already-frozen candidate/gate/falsifier system to a
physical execution registry.  It opens no biological values and grants no
scientific authority.
"""
from __future__ import annotations

import json
from pathlib import Path


class RealTournamentContractError(ValueError):
    pass


SCHEMA = "JEPA_TD_REAL_TARGET_TOURNAMENT_CONTRACT_V1"
CANDIDATE_IDS = [
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C6_SHARED_QUERY_COMPOSITE",
    "C4_STRUCTURED_COMPOSITE",
    "C5_REGULATORY_SPECIALIST",
]

PROMOTION_GATES = [
    "G1_INTEGRITY_LINEAGE", "G2_NONTRIVIAL_BIOLOGICAL_CONTENT",
    "G3_CORRECT_CELL_SPECIFICITY", "G4_DONOR_RECURRENCE",
    "G5_SOURCE_REPLICATION", "G6_TEACHER_INFORMATION_ADVANTAGE",
    "G7_EVIDENCE_CONVERGENCE", "G8_MEASUREMENT_ROBUSTNESS",
    "G9_LEARNED_TEACHER_CONTINUITY", "G10_COLLAPSE_SHORTCUT_RESISTANCE",
    "G11_TRANSFER", "G12_COVERAGE_ABSTENTION",
]
SHARED_GATES = [
    "S1_DISJOINT_VIEW_RECURRENCE", "S2_DONOR_BALANCED_SUBSPACE_STABILITY",
    "S3_IDENTITY_SUPPORT_BASELINE_DEFEAT",
]
RELATIONAL_GATES = [
    "R1_SCALE_FREE_RELATIONAL_RECURRENCE", "R2_LOCALITY_RULE_FROZEN_NO_FINE_MINING",
    "R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT", "R4_INCREMENT_OVER_C1_SHARED",
]
QUERY_GATES = [
    "Q1_Q_SCALAR_STUDENT_ABSENT", "Q2_Q_EXCLUDED_TEACHER_PRIMARY_ANCHOR",
    "Q3_TARGET_NORMALIZATION_Q_SCALAR_FREE", "Q4_Q_COUNT_ONLY_DEFEAT",
    "Q5_Q_ADDRESS_ONLY_DEFEAT", "Q6_QUERY_AGNOSTIC_DEFEAT",
    "Q7_WRONG_Q_DEFEAT", "Q8_TECHNICAL_PLUS_Q_DEFEAT",
]
SPECIALIST_GATES = [
    "M1_CIRCULARITY_CONTROL", "M2_INDEPENDENT_PROVENANCE",
    "M3_CAUSAL_CLAIM_FALSE", "M4_SUPPORT_ABSTENTION",
]

C1_GATES = PROMOTION_GATES + SHARED_GATES
C2_GATES = C1_GATES + RELATIONAL_GATES
C3_GATES = [g for g in PROMOTION_GATES if g != "G9_LEARNED_TEACHER_CONTINUITY"] + QUERY_GATES
C6_GATES = list(dict.fromkeys(C1_GATES + C3_GATES + ["C6_INCREMENT_OVER_C1_C3"]))
C4_GATES = list(dict.fromkeys(C2_GATES + C3_GATES + ["C4_INCREMENT_OVER_CONSTITUENTS"]))
C5_GATES = PROMOTION_GATES[:5] + PROMOTION_GATES[9:12] + SPECIALIST_GATES

MANDATORY_FALSIFIERS = [
    "constant_train_mean", "technical_operator_only", "address_support_operator",
    "matched_wrong_cell", "fine_neighborhood_wrong_cell", "q_count_only",
    "q_address_only", "query_agnostic", "wrong_q", "technical_plus_q",
    "q_excluded_teacher", "identity_support_only",
]

AUTHORITY_KEYS = {
    "value_read_authorized", "real_tournament_authorized",
    "target_selection_authorized", "representation_selection_authorized",
    "td60_authorized", "stage4_authorized", "training_authorized",
}

_EXPECTED = {
    "C1_SHARED_EMERGENT": {
        "parents": [], "required_gates": C1_GATES,
        "mandatory_falsifiers": [
            "constant_train_mean", "technical_operator_only", "address_support_operator",
            "matched_wrong_cell", "identity_support_only",
        ],
        "relational_dependent": False, "foundation_rescue": False,
    },
    "C2_RELATIONAL_SHARED": {
        "parents": ["C1_SHARED_EMERGENT"], "required_gates": C2_GATES,
        "mandatory_falsifiers": [
            "constant_train_mean", "technical_operator_only", "address_support_operator",
            "matched_wrong_cell", "fine_neighborhood_wrong_cell", "identity_support_only",
        ],
        "relational_dependent": True, "foundation_rescue": False,
    },
    "C3_QUERY_MEASURED": {
        "parents": [], "required_gates": C3_GATES,
        "mandatory_falsifiers": [
            "constant_train_mean", "technical_operator_only", "address_support_operator",
            "matched_wrong_cell", "q_count_only", "q_address_only", "query_agnostic",
            "wrong_q", "technical_plus_q", "q_excluded_teacher",
        ],
        "relational_dependent": False, "foundation_rescue": False,
    },
    "C6_SHARED_QUERY_COMPOSITE": {
        "parents": ["C1_SHARED_EMERGENT", "C3_QUERY_MEASURED"], "required_gates": C6_GATES,
        "mandatory_falsifiers": [
            "constant_train_mean", "technical_operator_only", "address_support_operator",
            "matched_wrong_cell", "identity_support_only", "q_count_only", "q_address_only",
            "query_agnostic", "wrong_q", "technical_plus_q", "q_excluded_teacher",
        ],
        "relational_dependent": False, "foundation_rescue": False,
    },
    "C4_STRUCTURED_COMPOSITE": {
        "parents": ["C2_RELATIONAL_SHARED", "C3_QUERY_MEASURED"], "required_gates": C4_GATES,
        "mandatory_falsifiers": [
            "constant_train_mean", "technical_operator_only", "address_support_operator",
            "matched_wrong_cell", "fine_neighborhood_wrong_cell", "identity_support_only",
            "q_count_only", "q_address_only", "query_agnostic", "wrong_q",
            "technical_plus_q", "q_excluded_teacher",
        ],
        "relational_dependent": True, "foundation_rescue": False,
    },
    "C5_REGULATORY_SPECIALIST": {
        "parents": [], "required_gates": C5_GATES,
        "mandatory_falsifiers": [
            "constant_train_mean", "technical_operator_only", "address_support_operator",
            "matched_wrong_cell",
        ],
        "relational_dependent": False, "foundation_rescue": False,
    },
}

_CONTRACT_FIELDS = {
    "schema", "candidates", "replication_unit", "source_semantics",
    "support_semantics", "synthetic_evidence_consumed", "mandatory_falsifiers",
    "authority",
}


def _contract_path() -> Path:
    return Path(__file__).resolve().parents[2] / "results" / "target_discovery" / "real_tournament" / "TD_REAL_TOURNAMENT_CONTRACT_V1.json"


def load_real_tournament_contract(path: str | Path | None = None) -> dict:
    target = Path(path) if path is not None else _contract_path()
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_candidate_registry(contract: dict) -> dict:
    if not isinstance(contract, dict) or set(contract) != _CONTRACT_FIELDS:
        raise RealTournamentContractError("real tournament contract fields differ from frozen schema")
    if contract.get("schema") != SCHEMA:
        raise RealTournamentContractError("wrong real tournament contract schema")
    if contract.get("replication_unit") != "donor":
        raise RealTournamentContractError("donor must remain the biological replication unit")
    if contract.get("source_semantics") != "observation_operator_not_biological_replicate":
        raise RealTournamentContractError("source semantics drift")
    if contract.get("support_semantics") != {
        "measured_zero": "VALID_MEASUREMENT",
        "structurally_unsupported": "ABSTAIN",
        "imputation": "FORBIDDEN",
    }:
        raise RealTournamentContractError("support semantics drift")
    if contract.get("synthetic_evidence_consumed") is not False:
        raise RealTournamentContractError("real executor may not consume synthetic evidence")
    if contract.get("mandatory_falsifiers") != MANDATORY_FALSIFIERS:
        raise RealTournamentContractError("mandatory falsifier catalog drift")
    authority = contract.get("authority")
    if not isinstance(authority, dict) or set(authority) != AUTHORITY_KEYS or any(v is not False for v in authority.values()):
        raise RealTournamentContractError("contract must carry exact no-authority flags")

    candidates = contract.get("candidates")
    if not isinstance(candidates, dict) or list(candidates) != CANDIDATE_IDS:
        raise RealTournamentContractError("candidate registry/order drift")
    for candidate_id in CANDIDATE_IDS:
        record = candidates[candidate_id]
        if record != _EXPECTED[candidate_id]:
            raise RealTournamentContractError(f"candidate registry drift: {candidate_id}")
        if not set(record["mandatory_falsifiers"]) <= set(MANDATORY_FALSIFIERS):
            raise RealTournamentContractError(f"unknown falsifier in {candidate_id}")
    return {candidate_id: dict(candidates[candidate_id]) for candidate_id in CANDIDATE_IDS}
