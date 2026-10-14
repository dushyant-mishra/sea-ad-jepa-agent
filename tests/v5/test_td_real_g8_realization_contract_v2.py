from __future__ import annotations

import pytest

import scripts.v5.td_real_g8_realization_contract_v2 as G


BINDING = "a" * 64
METRIC_SHA = "b" * 64
SUPPORT_SHA = "c" * 64


def _manifest(**updates):
    manifest = {
        "schema": G.UNIT_SCHEMA,
        "candidate_id": "C1",
        "source": "SEA_AD",
        "donor_id": "D001",
        "operator_scope_id": "DONOR_AGGREGATE_WITH_FROZEN_OPERATOR_PRESERVATION",
        "endpoint_id": "PRIMARY_STATE",
        "input_binding_sha256": BINDING,
        "metric_manifest_sha256": METRIC_SHA,
        "support_universe_sha256": SUPPORT_SHA,
        "atomic_support_unit": "FROZEN_TARGET_ATOM",
        "biological_replication_unit": "DONOR",
        "calibration_realization": "INDEPENDENT_TECHNICAL_MONTE_CARLO_PAIR_CONDITIONAL_ON_FIXED_REAL_UNIT",
        "calibration_draws_are_biological_replicates": False,
        "metric_orientation": "SMALLER_IS_MORE_STABLE",
        "metric_frozen_before_values": True,
        "support_denominator_frozen_before_thinning": True,
        "measured_zero_is_supported_measurement": True,
        "unsupported_atoms_are_abstentions": True,
    }
    manifest.update(updates)
    return manifest


def test_realization_is_technical_not_biological_replication():
    out = G.validate_unit_manifest(_manifest())
    assert out["biological_replication_unit"] == "DONOR"
    assert out["calibration_draws_are_biological_replicates"] is False
    assert out["calibration_realization"].startswith("INDEPENDENT_TECHNICAL_MONTE_CARLO_PAIR")


def test_metric_and_support_manifests_are_exactly_hash_bound():
    with pytest.raises(G.G8ContractError, match="metric"):
        G.validate_unit_manifest(_manifest(metric_manifest_sha256="not-a-hash"))
    with pytest.raises(G.G8ContractError, match="support"):
        G.validate_unit_manifest(_manifest(support_universe_sha256="not-a-hash"))


def test_support_fraction_uses_frozen_prethinning_denominator_and_keeps_measured_zero():
    eligible = ["A", "B", "C", "D"]
    state = {
        "A": "RESOLVED_NONZERO",
        "B": "RESOLVED_MEASURED_ZERO",
        "C": "MEASUREMENT_UNRESOLVED",
        "D": "MEASUREMENT_UNRESOLVED",
    }
    out = G.support_fraction(eligible_atoms=eligible, atom_states=state)
    assert out["denominator"] == 4
    assert out["resolved_count"] == 2
    assert out["support_fraction"] == 0.5
    assert out["measured_zero_count"] == 1
    assert out["abstained_count"] == 2


def test_structural_or_contract_blocked_atoms_are_upstream_blockers_not_g8_thinning_outcomes():
    for blocked_state in ("UNSUPPORTED_STRUCTURAL", "BLOCKED_EVIDENCE_CONTRACT"):
        with pytest.raises(G.G8ContractError, match="upstream"):
            G.support_fraction(
                eligible_atoms=["A", "B"],
                atom_states={"A": "RESOLVED_NONZERO", "B": blocked_state},
            )


def test_support_denominator_cannot_shrink_after_thinning():
    with pytest.raises(G.G8ContractError, match="exactly match"):
        G.support_fraction(
            eligible_atoms=["A", "B", "C"],
            atom_states={"A": "RESOLVED_NONZERO", "B": "RESOLVED_NONZERO"},
        )


def test_calibration_plan_has_599_independent_seed_indices_per_depth_but_donor_n_is_one():
    plan = G.build_calibration_plan(
        unit_manifest=_manifest(),
        family_alpha=0.01,
        calibration_namespace="g8/cal/C1/SEA_AD/D001/PRIMARY_STATE",
        deciding_namespace="g8/decide/C1/SEA_AD/D001/PRIMARY_STATE",
        null_namespace="g8/null/C1/SEA_AD/D001/PRIMARY_STATE",
    )
    assert plan["required_calibration_draws_per_depth"] == 599
    assert len(plan["draw_indices"]) == 599
    assert len(set(plan["draw_indices"])) == 599
    assert plan["biological_donor_count_contributed"] == 1
    assert plan["technical_draws_do_not_increase_biological_n"] is True


def test_calibration_deciding_and_null_namespaces_must_be_disjoint():
    with pytest.raises(G.G8ContractError, match="disjoint"):
        G.build_calibration_plan(
            unit_manifest=_manifest(),
            family_alpha=0.01,
            calibration_namespace="same",
            deciding_namespace="same",
            null_namespace="other",
        )


def test_candidate_specific_metric_is_allowed_only_when_frozen_and_same_metric_serves_reference_and_decision():
    out = G.validate_metric_contract({
        "schema": G.METRIC_SCHEMA,
        "metric_id": "C1_STATE_DISTANCE_V1",
        "candidate_id": "C1",
        "metric_manifest_sha256": METRIC_SHA,
        "orientation": "SMALLER_IS_MORE_STABLE",
        "same_metric_reference_and_decision": True,
        "frozen_before_values": True,
        "outcome_adaptive_parameters": False,
        "invariance_class": "CANDIDATE_DECLARED_REPRESENTATION_INVARIANCE",
    })
    assert out["same_metric_reference_and_decision"] is True
    with pytest.raises(G.G8ContractError, match="same metric"):
        G.validate_metric_contract({**out, "same_metric_reference_and_decision": False})


def test_human_g8_is_not_executable_without_both_metric_and_support_bindings():
    ready = G.execution_readiness(
        unit_manifest=_manifest(),
        metric_contract_qualified=True,
        support_universe_qualified=True,
    )
    assert ready["status"] == "READY_FOR_OUTCOME_BLIND_G8_REFERENCE_GENERATION_ONLY"
    blocked = G.execution_readiness(
        unit_manifest=_manifest(),
        metric_contract_qualified=False,
        support_universe_qualified=True,
    )
    assert blocked["status"] == "BLOCKED_G8_CONTRACT_DEPENDENCY"
    assert blocked["human_g8_adjudication_authorized"] is False


def test_all_authority_remains_false():
    out = G.execution_readiness(
        unit_manifest=_manifest(),
        metric_contract_qualified=True,
        support_universe_qualified=True,
    )
    assert all(value is False for value in out["authority"].values())
