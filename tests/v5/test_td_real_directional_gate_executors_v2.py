from __future__ import annotations

import pytest

import scripts.v5.td_real_directional_gate_executors_v2 as D


CLEARED = {
    "G3_CORRECT_CELL_SPECIFICITY",
    "G4_DONOR_RECURRENCE",
    "G5_SOURCE_REPLICATION",
    "G10_COLLAPSE_SHORTCUT_RESISTANCE",
    "S3_IDENTITY_SUPPORT_BASELINE_DEFEAT",
    "R3_FINE_NEIGHBOR_WRONG_CELL_DEFEAT",
    "Q4_Q_COUNT_ONLY_DEFEAT",
    "Q5_Q_ADDRESS_ONLY_DEFEAT",
    "Q6_QUERY_AGNOSTIC_DEFEAT",
    "Q7_WRONG_Q_DEFEAT",
    "Q8_TECHNICAL_PLUS_Q_DEFEAT",
    "M1_CIRCULARITY_CONTROL",
    "M2_INDEPENDENT_PROVENANCE",
    "M3_CAUSAL_CLAIM_FALSE",
    "M4_SUPPORT_ABSTENTION",
}

BLOCKED = {
    "G2_NONTRIVIAL_BIOLOGICAL_CONTENT",
    "G6_TEACHER_INFORMATION_ADVANTAGE",
    "G7_EVIDENCE_CONVERGENCE",
    "G8_MEASUREMENT_ROBUSTNESS",
    "G9_LEARNED_TEACHER_CONTINUITY",
    "G11_TRANSFER",
    "G12_COVERAGE_ABSTENTION",
    "S1_DISJOINT_VIEW_RECURRENCE",
    "S2_DONOR_BALANCED_SUBSPACE_STABILITY",
    "R1_SCALE_FREE_RELATIONAL_RECURRENCE",
    "R4_INCREMENT_OVER_C1_SHARED",
    "C6_INCREMENT_OVER_C1_C3",
    "C4_INCREMENT_OVER_CONSTITUENTS",
}


def _deltas(value: float, n=10, prefix="D"):
    return [
        {"donor_id": f"{prefix}{i:03d}", "delta": float(value)}
        for i in range(n)
    ]


def _positive(n=10, prefix="D"):
    return _deltas(1.0, n=n, prefix=prefix)


def _negative(n=10, prefix="D"):
    return _deltas(-1.0, n=n, prefix=prefix)


def test_exact_v2_scope_is_frozen():
    assert D.CLEARED_V2_GATES == CLEARED
    assert D.BLOCKED_V2_GATES == BLOCKED
    assert D.CLEARED_V2_GATES.isdisjoint(D.BLOCKED_V2_GATES)


def test_blocked_gate_has_no_direction_only_fallback():
    with pytest.raises(D.DirectionalGateError, match="blocked prospective rule"):
        D.evaluate_directional_gate(
            "G2_NONTRIVIAL_BIOLOGICAL_CONTENT",
            {"donor_deltas": _positive()},
        )


def test_g4_is_donor_primary_directional_recurrence_only():
    passed = D.evaluate_directional_gate("G4_DONOR_RECURRENCE", {"donor_deltas": _positive()})
    failed = D.evaluate_directional_gate("G4_DONOR_RECURRENCE", {"donor_deltas": _negative()})
    unresolved = D.evaluate_directional_gate("G4_DONOR_RECURRENCE", {"donor_deltas": _positive(7)})
    assert passed["status"] == "PASS"
    assert failed["status"] == "FAIL"
    assert unresolved["status"] == "NOT_ESTIMABLE"
    assert passed["claim_boundary"] == "DIRECTIONAL_OR_STRUCTURAL_QUALIFICATION_ONLY__NO_BIOLOGICAL_MAGNITUDE_CLAIM"
    assert not any(passed["authority"].values())


def test_g3_relational_requires_b3_and_b4_noncompensating():
    out = D.evaluate_directional_gate(
        "G3_CORRECT_CELL_SPECIFICITY",
        {
            "candidate_id": "C2_RELATIONAL_SHARED",
            "subtests": {
                "matched_wrong_cell": _positive(prefix="B3"),
                "fine_neighborhood_wrong_cell": _negative(prefix="B4"),
            },
        },
    )
    assert out["status"] == "FAIL"
    assert out["subtests"]["matched_wrong_cell"]["status"] == "PASS"
    assert out["subtests"]["fine_neighborhood_wrong_cell"]["status"] == "FAIL"


def test_g3_missing_required_relational_b4_is_not_estimable():
    out = D.evaluate_directional_gate(
        "G3_CORRECT_CELL_SPECIFICITY",
        {
            "candidate_id": "C2_RELATIONAL_SHARED",
            "subtests": {"matched_wrong_cell": _positive(prefix="B3")},
        },
    )
    assert out["status"] == "NOT_ESTIMABLE"


def test_g5_requires_exact_current_sources_without_pooling():
    out = D.evaluate_directional_gate(
        "G5_SOURCE_REPLICATION",
        {
            "source_donor_deltas": {
                "HVS": _positive(prefix="H"),
                "NPH52": _positive(prefix="N"),
                "SEA_AD": _negative(prefix="S"),
            }
        },
    )
    assert out["status"] == "FAIL"
    assert set(out["strata"]) == {"HVS", "NPH52", "SEA_AD"}


def test_g10_requires_exact_candidate_mandatory_falsifier_set():
    evidence = {
        "candidate_id": "C1_SHARED_EMERGENT",
        "falsifier_donor_deltas": {
            "constant_train_mean": _positive(prefix="B0"),
            "technical_operator_only": _positive(prefix="B1"),
            "address_support_operator": _positive(prefix="B2"),
            "matched_wrong_cell": _positive(prefix="B3"),
            "identity_support_only": _positive(prefix="B5"),
        },
    }
    assert D.evaluate_directional_gate("G10_COLLAPSE_SHORTCUT_RESISTANCE", evidence)["status"] == "PASS"
    bad = dict(evidence)
    bad["falsifier_donor_deltas"] = dict(evidence["falsifier_donor_deltas"])
    bad["falsifier_donor_deltas"].pop("matched_wrong_cell")
    assert D.evaluate_directional_gate("G10_COLLAPSE_SHORTCUT_RESISTANCE", bad)["status"] == "NOT_ESTIMABLE"


def test_m1_requires_disjoint_construction_and_deciding_evidence():
    passed = D.evaluate_directional_gate(
        "M1_CIRCULARITY_CONTROL",
        {"construction_evidence_ids": ["A", "B"], "deciding_evidence_ids": ["C"]},
    )
    failed = D.evaluate_directional_gate(
        "M1_CIRCULARITY_CONTROL",
        {"construction_evidence_ids": ["A", "B"], "deciding_evidence_ids": ["B", "C"]},
    )
    assert passed["status"] == "PASS"
    assert failed["status"] == "FAIL"
    assert D.evaluate_directional_gate("M1_CIRCULARITY_CONTROL", {})["status"] == "NOT_ESTIMABLE"


def test_m2_requires_authenticated_independent_provenance():
    passed = D.evaluate_directional_gate(
        "M2_INDEPENDENT_PROVENANCE",
        {"provenance_authenticated": True, "independent_of_target_selection": True},
    )
    exposed = D.evaluate_directional_gate(
        "M2_INDEPENDENT_PROVENANCE",
        {"provenance_authenticated": True, "independent_of_target_selection": False},
    )
    assert passed["status"] == "PASS"
    assert exposed["status"] == "FAIL"
    assert D.evaluate_directional_gate("M2_INDEPENDENT_PROVENANCE", {})["status"] == "NOT_ESTIMABLE"


def test_m3_only_passes_explicit_noncausal_claim_scope():
    assert D.evaluate_directional_gate("M3_CAUSAL_CLAIM_FALSE", {"causal_claim_asserted": False})["status"] == "PASS"
    assert D.evaluate_directional_gate("M3_CAUSAL_CLAIM_FALSE", {"causal_claim_asserted": True})["status"] == "FAIL"
    assert D.evaluate_directional_gate("M3_CAUSAL_CLAIM_FALSE", {})["status"] == "NOT_ESTIMABLE"


def test_m4_preserves_missing_and_unsupported_as_abstention():
    passed = D.evaluate_directional_gate(
        "M4_SUPPORT_ABSTENTION",
        {
            "unsupported_converted_to_numeric": False,
            "missing_evidence_treated_as_zero": False,
            "imputation_used": False,
        },
    )
    failed = D.evaluate_directional_gate(
        "M4_SUPPORT_ABSTENTION",
        {
            "unsupported_converted_to_numeric": False,
            "missing_evidence_treated_as_zero": True,
            "imputation_used": False,
        },
    )
    assert passed["status"] == "PASS"
    assert failed["status"] == "FAIL"
    assert D.evaluate_directional_gate("M4_SUPPORT_ABSTENTION", {})["status"] == "NOT_ESTIMABLE"
