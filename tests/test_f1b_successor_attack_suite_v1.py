"""The attacks must discriminate, and absent machinery must never read as a pass."""

from __future__ import annotations

from scripts.v4.f1b_reference_candidates_v1 import (
    reference_correct, reference_empty, reference_vulnerable)
from scripts.v4.f1b_successor_attack_suite_v1 import (
    ATTACKS, DEFENDED, NOT_APPLICABLE, VULNERABLE, prove_polarity, run_suite)


def test_every_attack_discriminates_in_both_directions() -> None:
    """An attack that always passes or always fails is not evidence."""
    proof = prove_polarity(reference_vulnerable(), reference_correct())
    assert proof["terminal"] == "PASS_ATTACK_POLARITY", proof["attacks"]
    assert proof["defective"] == []
    assert len(proof["attacks"]) == len(ATTACKS)
    for name, row in proof["attacks"].items():
        assert row["on_vulnerable"] == VULNERABLE, name
        assert row["on_correct"] == DEFENDED, name


def test_vulnerable_reference_is_stopped() -> None:
    report = run_suite(reference_vulnerable())
    assert report["terminal"] == "STOP_F1B_ATTACK_SUITE"
    assert sorted(report["vulnerable"]) == sorted(name for name, _ in ATTACKS)
    assert report["not_applicable"] == []


def test_correct_reference_passes() -> None:
    report = run_suite(reference_correct())
    assert report["terminal"] == "PASS_F1B_ATTACK_SUITE"
    assert report["vulnerable"] == []
    assert report["not_applicable"] == []


def test_absent_machinery_is_not_a_pass() -> None:
    """A candidate implementing nothing must not clear the suite."""
    report = run_suite(reference_empty())
    assert report["terminal"] == "STOP_F1B_ATTACK_SUITE"
    assert report["vulnerable"] == []
    assert sorted(report["not_applicable"]) == sorted(name for name, _ in ATTACKS)
    for row in report["results"].values():
        assert row["verdict"] == NOT_APPLICABLE


def test_predictor_gate_is_not_satisfied_by_a_healthy_backbone_alone() -> None:
    """The specific historical shape: backbone live, predictor dead."""
    from scripts.v4.f1b_successor_attack_suite_v1 import attack_predictor_mechanics_ungated

    assert attack_predictor_mechanics_ungated(reference_vulnerable())["verdict"] == VULNERABLE
    assert attack_predictor_mechanics_ungated(reference_correct())["verdict"] == DEFENDED


def test_routing_attack_actually_separates_the_two_cells() -> None:
    """Guard the attack's own premise: the correct reference must report distinct stats."""
    from scripts.v4.f1b_reference_candidates_v1 import _ok_routing, _vuln_routing

    weights = [[0.25, 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.25]]
    ok = _ok_routing(weights, [4, 1])
    vuln = _vuln_routing(weights, [4, 1])
    # Identical rows: only per-cell support may change the statistic.
    assert abs(ok[0] - 4.0) < 1e-6 and abs(ok[1] - 1.0) < 1e-6, ok
    assert abs(vuln[0] - 4.0) < 1e-6 and abs(vuln[1] - 4.0) < 1e-6, vuln


def test_late_refusal_after_stepping_is_still_vulnerable() -> None:
    """Refusing after the optimizer has stepped is not a gate."""
    from scripts.v4.f1b_successor_attack_suite_v1 import attack_optimizer_steps_before_gate

    result = attack_optimizer_steps_before_gate(reference_vulnerable())
    assert result["verdict"] == VULNERABLE
    assert result["ledger"]["stepped"] is True
    assert "after the optimizer had stepped" in result["note"]

    ok = attack_optimizer_steps_before_gate(reference_correct())
    assert ok["verdict"] == DEFENDED
    assert ok["ledger"]["stepped"] is False
    assert ok["ledger"]["optimizer_state_entries"] == 0


def test_endpoint_registry_leak_names_the_unauthorised_keys() -> None:
    from scripts.v4.f1b_successor_attack_suite_v1 import attack_implicit_endpoint_registry

    leak = attack_implicit_endpoint_registry(reference_vulnerable())
    assert leak["verdict"] == VULNERABLE
    assert set(leak["leaked"]) == {
        "l2__recurrent_5pct", "l2__recurrent_1pct", "l2__unregistered_experimental"}

    ok = attack_implicit_endpoint_registry(reference_correct())
    assert ok["verdict"] == DEFENDED
    assert set(ok["selected"]) == {"l2__broad_common", "l2__local"}
