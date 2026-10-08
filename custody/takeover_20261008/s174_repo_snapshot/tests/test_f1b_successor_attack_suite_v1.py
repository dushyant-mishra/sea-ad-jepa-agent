"""All fifteen findings must be covered by attacks that demonstrably discriminate."""

from __future__ import annotations

import math

from scripts.v4.f1b_reference_candidates_v1 import (
    reference_correct, reference_empty, reference_vulnerable)
from scripts.v4.f1b_successor_attack_suite_v1 import (
    ALL_FINDINGS, ATTACKS, DEFENDED, NOT_APPLICABLE, VULNERABLE, Candidate,
    prove_polarity, registry_audit, run_suite)


def test_every_attack_discriminates_in_both_directions() -> None:
    """An attack that always passes or always fails is not evidence."""
    proof = prove_polarity(reference_vulnerable(), reference_correct())
    assert proof["terminal"] == "PASS_ATTACK_POLARITY", proof["attacks"]
    assert proof["defective"] == []
    for name, row in proof["attacks"].items():
        assert row["on_vulnerable"] == VULNERABLE, (name, row)
        assert row["on_correct"] == DEFENDED, (name, row)


def test_registry_audit_passes_before_freeze() -> None:
    """Exactly 15 findings, each discriminating, none source-text, none NA-passing."""
    audit = registry_audit(reference_vulnerable(), reference_correct())
    failed = [c for c in audit["checks"] if not c["passed"]]
    assert audit["terminal"] == "PASS_F1B_ATTACK_REGISTRY", failed
    assert sorted(int(k) for k in audit["coverage"]) == list(ALL_FINDINGS)
    for finding, names in audit["coverage"].items():
        assert names, "finding %s has no attack" % finding


def test_vulnerable_reference_is_stopped_on_every_attack() -> None:
    report = run_suite(reference_vulnerable())
    assert report["terminal"] == "STOP_F1B_ATTACK_SUITE"
    assert sorted(report["vulnerable"]) == sorted(name for name, _, _ in ATTACKS)
    assert report["not_applicable"] == [] and report["attack_defective"] == []


def test_correct_reference_passes_every_attack() -> None:
    report = run_suite(reference_correct())
    assert report["terminal"] == "PASS_F1B_ATTACK_SUITE"
    assert report["vulnerable"] == []
    assert report["not_applicable"] == [] and report["attack_defective"] == []


def test_absent_machinery_is_not_a_pass() -> None:
    report = run_suite(reference_empty())
    assert report["terminal"] == "STOP_F1B_ATTACK_SUITE"
    assert report["vulnerable"] == []
    assert sorted(report["not_applicable"]) == sorted(name for name, _, _ in ATTACKS)


def test_metric_collision_uses_a_case_where_the_metrics_truly_disagree() -> None:
    """Guard finding 7's analytic premise."""
    p = [0.5, 0.25, 0.25]
    entropy = math.exp(-sum(x * math.log(x) for x in p))
    participation = 1.0 / sum(x * x for x in p)
    assert abs(entropy - participation) > 1e-2
    assert abs(entropy - 2.8284271) < 1e-5
    assert abs(participation - 2.6666667) < 1e-5


def test_routing_mutations_have_the_expected_analytic_answers() -> None:
    from scripts.v4.f1b_reference_candidates_v1 import _ok_routing_metrics

    out = _ok_routing_metrics(
        [[1.0, 1.0, 0.0, 100.0], [3.0, 1.0, 0.0, 100.0]],
        [[True, True, False, False], [True, True, False, False]],
    )
    assert out["valid_keys"] == [2, 2]
    assert abs(out["N_eff_entropy"][0] - 2.0) < 1e-6
    assert abs(out["N_eff_participation"][1] - 1.6) < 1e-6
    assert abs(out["top1_mass"][1] - 0.75) < 1e-6
    assert abs(out["query_map_cosine"] - 0.8944271909999159) < 1e-6


def test_refusal_only_candidate_cannot_pass_any_attack() -> None:
    def refuse(*args, **kwargs):
        raise RuntimeError("stub")

    candidate = Candidate(
        name="refusal-only", gate_mandatory_gradients=refuse, movement_gate=refuse,
        routing_report=refuse, routing_metrics=refuse, refit=refuse,
        frozen_horizon=refuse, directional_claim=refuse, target_equivalence=refuse,
        amp_smoke=refuse, protected_update=refuse, select_endpoints=refuse,
    )
    report = run_suite(candidate)
    assert report["terminal"] == "STOP_F1B_ATTACK_SUITE"
    assert report["defended"] == []

def test_refit_depends_on_the_fit_split() -> None:
    from scripts.v4.f1b_reference_candidates_v1 import _ok_refit, _vuln_refit

    a = {"fit_donors": ["a1", "a2"], "fit_values": [0.0, 0.0],
         "eval_donors": ["e1"], "eval_values": [7.0]}
    b = {"fit_donors": ["b1", "b2"], "fit_values": [2.0, 4.0],
         "eval_donors": ["e1"], "eval_values": [7.0]}
    assert _ok_refit(a)["predictions"] == [0.0]
    assert _ok_refit(b)["predictions"] == [3.0]
    assert _vuln_refit(a)["predictions"] == _vuln_refit(b)["predictions"]


def test_g5_metadata_only_mutation_still_fails() -> None:
    from scripts.v4.f1b_successor_attack_suite_v1 import attack_g5_refit_is_not_a_refit

    def fake_refit(payload):
        return {"fit_signature": tuple(payload["fit_donors"]),
                "predictions": [0.0 for _ in payload["eval_values"]]}

    result = attack_g5_refit_is_not_a_refit(Candidate(name="metadata-only", refit=fake_refit))
    assert result["verdict"] == VULNERABLE

def test_target_equivalence_must_detect_both_equality_and_inequality() -> None:
    from scripts.v4.f1b_reference_candidates_v1 import (
        _ok_target_equivalence, _vuln_target_equivalence)

    assert _ok_target_equivalence([1.0, 2.0], [1.0, 2.0])["equivalent"] is True
    assert _ok_target_equivalence([1.0, 2.0], [1.0, 9.0])["equivalent"] is False
    # The defective reference asserts equivalence in both cases.
    assert _vuln_target_equivalence([1.0, 2.0], [1.0, 9.0])["equivalent"] is True


def test_amp_attack_requires_real_operation_trace() -> None:
    from scripts.v4.f1b_successor_attack_suite_v1 import attack_amp_smoke_is_declarative

    vuln = attack_amp_smoke_is_declarative(reference_vulnerable())
    assert vuln["verdict"] == VULNERABLE
    ok = attack_amp_smoke_is_declarative(reference_correct())
    assert ok["verdict"] == DEFENDED
    assert ok["healthy_events"][-2:] == ["optimizer_step", "ema_step"]
    assert ok["dead_events"][-1] == "gradient_gate"


def test_amp_self_report_spoof_cannot_pass() -> None:
    from scripts.v4.f1b_successor_attack_suite_v1 import attack_amp_smoke_is_declarative

    def spoof(harness):
        return {"autocast_enabled": True, "unscaled_before_gate": True,
                "gate_before_step": True, "ema": True}

    result = attack_amp_smoke_is_declarative(Candidate(name="amp-spoof", amp_smoke=spoof))
    assert result["verdict"] == VULNERABLE

def test_directional_claim_withheld_only_when_a_control_explains_it() -> None:
    from scripts.v4.f1b_reference_candidates_v1 import _ok_directional
    from scripts.v4.f1b_successor_attack_suite_v1 import attack_directional_claim_too_strong

    cell = _ok_directional({"observed": 1.0, "cell_only_control": 1.0,
                            "identity_only_control": 0.0})
    identity = _ok_directional({"observed": 1.0, "cell_only_control": 0.0,
                                "identity_only_control": 1.0})
    clean = _ok_directional({"observed": 1.0, "cell_only_control": 0.0,
                             "identity_only_control": 0.0})
    assert cell["structural"] is False
    assert identity["structural"] is False
    assert clean["structural"] is True

    def ignores_identity(obs):
        return {"structural": abs(float(obs.get("cell_only_control", 0.0)))
                              < 0.5 * abs(float(obs["observed"]))}

    result = attack_directional_claim_too_strong(
        Candidate(name="ignores-identity", directional_claim=ignores_identity))
    assert result["verdict"] == VULNERABLE

def test_movement_gate_is_per_tensor_and_handles_zero_baseline() -> None:
    """Finding 3 has two poles: no pooling, and a moved zero-baseline tensor passes."""
    import pytest

    from scripts.v4.f1b_reference_candidates_v1 import _ok_movement, _vuln_movement

    masking = {"relative_movement": {"a": 1.0, "b": 1.0, "c": 1.0, "dead": 1e-6},
               "decay_only_prediction": 1e-6,
               "absolute_movement": {"a": 1.0, "b": 1.0, "c": 1.0, "dead": 0.0},
               "baseline_norm": {"a": 1.0, "b": 1.0, "c": 1.0, "dead": 1.0}}
    with pytest.raises(RuntimeError):
        _ok_movement(masking)             # per-tensor: the dead one is caught
    assert _vuln_movement(masking)        # pooled mean: the dead one is masked

    zero_baseline = {"relative_movement": {"bias": None},
                     "decay_only_prediction": 1e-6,
                     "absolute_movement": {"bias": 1e-3},
                     "baseline_norm": {"bias": 0.0}}
    assert _ok_movement(zero_baseline)    # moved, so it passes on absolute movement
