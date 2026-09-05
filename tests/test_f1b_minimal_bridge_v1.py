"""Tests for the F1-B minimal mechanism bridge.

Every mutation here is designed to reproduce a defect the project actually suffered, or a
shortcut the contract forbids. Synthetic only; no expression, no protected data.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = Path("D:/Jepa project")
SPEC = ROOT / "scripts/v4/run_f1b_minimal_bridge_v1.py"

spec = importlib.util.spec_from_file_location("f1b", SPEC)
f1b = importlib.util.module_from_spec(spec)
sys.modules["f1b"] = f1b
spec.loader.exec_module(f1b)


# --------------------------------------------------------------------------------------
# Authority binding
# --------------------------------------------------------------------------------------

def test_frozen_authority_table_is_complete_and_partitioned():
    assert set(f1b.FROZEN) == set(f1b.RELATIVE)
    assert f1b.LF_NORMALISED | f1b.RAW_BYTES == set(f1b.FROZEN)
    assert not (f1b.LF_NORMALISED & f1b.RAW_BYTES)


def test_recovered_component_hash_is_the_authenticated_historical_file():
    """The planned components must be the exact recovered bytes, never reconstructed."""
    assert f1b.FROZEN["full104_model_components_v2.py"] == \
        "c69ed6abb68f31e6177170ebafa1b412b0780d47d83e00776707a4c8cd4ae342"


def test_authenticate_rejects_a_mutated_authority(tmp_path, monkeypatch):
    monkeypatch.setitem(f1b.FROZEN, "u0_checkpoint", "0" * 64)
    with pytest.raises(RuntimeError, match="STOP_F1B_AUTHORITY_MISMATCH"):
        f1b.authenticate(CANONICAL)


def test_authenticate_rejects_a_missing_authority(tmp_path):
    with pytest.raises(RuntimeError, match="STOP_F1B_AUTHORITY_MISSING"):
        f1b.authenticate(tmp_path)


def test_source_hash_is_lf_normalised_and_file_hash_is_not():
    a = tmp = Path(__file__).parent / "_crlf_probe.tmp"
    tmp.write_bytes(b"line\r\nline\r\n")
    lf = f1b.sha256_source(tmp)
    raw = f1b.sha256_file(tmp)
    tmp.write_bytes(b"line\nline\n")
    assert f1b.sha256_source(tmp) == lf, "LF normalisation must make CRLF and LF agree"
    assert f1b.sha256_file(tmp) != raw, "raw hashing must remain line-ending sensitive"
    tmp.unlink()


# --------------------------------------------------------------------------------------
# Launch guard: production paths must fail closed
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["technical-fixture", "real"])
def test_non_synthetic_modes_fail_closed_without_authority(tmp_path, mode):
    with pytest.raises(RuntimeError, match=f1b.STOP_UNAUTHORIZED):
        f1b.validate_launch_authority(None, mode, tmp_path, {}, ROOT)


def test_truthy_non_boolean_authorization_is_rejected(tmp_path):
    path = tmp_path / "auth.json"
    path.write_text(json.dumps({"schema": f1b.LAUNCH_SCHEMA, "f1b_execution_authorized": 1,
                                "mode": "real", "output_root": str(tmp_path)}), encoding="utf-8")
    with pytest.raises(RuntimeError, match=f1b.STOP_UNAUTHORIZED):
        f1b.validate_launch_authority(path, "real", tmp_path, {}, ROOT)


def test_real_mode_requires_f1a_population_disjointness(tmp_path):
    """F1-B must not train on cells F1-A will evaluate."""
    auth = {"schema": f1b.LAUNCH_SCHEMA, "f1b_execution_authorized": True, "mode": "real",
            "output_root": str(tmp_path), "executor_sha256": f1b.sha256_source(SPEC),
            "contract_sha256": f1b.sha256_source(ROOT / f1b.CONTRACT_RELATIVE),
            "frozen_authorities": {}, "reader_partition": "reader_fit"}
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(RuntimeError, match=f1b.STOP_UNAUTHORIZED):
        f1b.validate_launch_authority(path, "real", tmp_path, {}, ROOT)
    auth["population_disjoint_from_f1a"] = True
    path.write_text(json.dumps(auth), encoding="utf-8")
    assert f1b.validate_launch_authority(path, "real", tmp_path, {}, ROOT)["mode"] == "real"


def test_authority_bound_to_executor_bytes(tmp_path):
    auth = {"schema": f1b.LAUNCH_SCHEMA, "f1b_execution_authorized": True, "mode": "real",
            "output_root": str(tmp_path), "executor_sha256": "0" * 64,
            "contract_sha256": f1b.sha256_source(ROOT / f1b.CONTRACT_RELATIVE),
            "frozen_authorities": {}, "reader_partition": "reader_fit",
            "population_disjoint_from_f1a": True}
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(RuntimeError, match=f1b.STOP_UNAUTHORIZED):
        f1b.validate_launch_authority(path, "real", tmp_path, {}, ROOT)


# --------------------------------------------------------------------------------------
# Query-self leakage
# --------------------------------------------------------------------------------------

def _population():
    frozen = f1b.Frozen(cells=2, queries_per_cell=3)
    return frozen, f1b.synthetic_population(frozen, torch.device("cpu"))


def test_frozen_population_has_no_query_leakage():
    _, pop = _population()
    f1b.assert_no_query_leakage(pop)


def test_query_visible_to_teacher_is_rejected():
    _, pop = _population()
    pop["teacher_visible"][0, int(pop["queries"][0, 0])] = True
    with pytest.raises(RuntimeError, match="QUERY_SELF_LEAKAGE:teacher_visible"):
        f1b.assert_no_query_leakage(pop)


def test_query_visible_to_student_is_rejected():
    _, pop = _population()
    pop["student_visible"][0, int(pop["queries"][0, 1])] = True
    with pytest.raises(RuntimeError, match="QUERY_SELF_LEAKAGE:student_visible"):
        f1b.assert_no_query_leakage(pop)


def test_student_evidence_must_be_a_subset_of_teacher_evidence():
    _, pop = _population()
    unlawful = int(torch.nonzero(~pop["teacher_visible"][0]).flatten()[0])
    pop["student_visible"][0, unlawful] = True
    with pytest.raises(RuntimeError, match="STUDENT_EVIDENCE_NOT_LAWFUL_SUBSET"):
        f1b.assert_no_query_leakage(pop)


def test_every_query_is_measured_scalar():
    _, pop = _population()
    rows = torch.arange(len(pop["queries"]))[:, None]
    assert bool(pop["measured"][rows, pop["queries"]].all())


# --------------------------------------------------------------------------------------
# Gradient coverage: the exact T1 defect must be caught
# --------------------------------------------------------------------------------------

class _FakeParam:
    def __init__(self, grad):
        self.grad = grad


class _FakeEncoder:
    """Six blocks x eight pre-attention tensors, mirroring the real parameter names."""
    def __init__(self, dead=(), missing=()):
        self._p = {}
        for b in range(6):
            for leaf in ("attention_norm.weight", "attention_norm.bias",
                         "attention.query.weight", "attention.query.bias",
                         "attention.key.weight", "attention.key.bias",
                         "attention.value.weight", "attention.value.bias"):
                name = f"blocks.{b}.{leaf}"
                g = None if name in missing else torch.zeros(2) if name in dead else torch.ones(2)
                self._p[name] = _FakeParam(g)
            self._p[f"blocks.{b}.attention.output.weight"] = _FakeParam(torch.ones(2) * 99)
        self._p["final_norm.weight"] = _FakeParam(torch.ones(2))

    def named_parameters(self):
        return list(self._p.items())


def test_gradient_coverage_counts_exactly_the_48_pre_attention_tensors():
    report = f1b.gradient_coverage(_FakeEncoder())
    assert report["tensors"] == f1b.EXPECTED_PRE_ATTENTION_TENSORS == 48
    assert report["zero_norm"] == 0


def test_gradient_coverage_detects_the_historical_t1_defect():
    """T1 had all 48 exactly zero while the pooled IPB_shared norm read 2.43."""
    dead = [f"blocks.{b}.{leaf}" for b in range(6)
            for leaf in ("attention_norm.weight", "attention_norm.bias",
                         "attention.query.weight", "attention.query.bias",
                         "attention.key.weight", "attention.key.bias",
                         "attention.value.weight", "attention.value.bias")]
    report = f1b.gradient_coverage(_FakeEncoder(dead=dead))
    assert report["zero_norm"] == 48
    gates = f1b.evaluate_gates(report, {"tensors": 48, "zero_moments": 48, "zero_tensors": []},
                               {"ratio_over_decay": 1.017, "pure_decay_prediction": 2e-4,
                                "mean_relative_movement": 2.08e-4, "min_relative_movement": 2e-4},
                               {"min_per_query_routing_spread": 1e-3, "mean_n_eff_over_n": 0.997},
                               {}, {}, f1b.Frozen(), {"mean_n_eff_over_n": 0.997}, True)
    assert gates["G1_gradient_coverage"] is False
    assert gates["G2_optimizer_moments"] is False
    assert gates["G3_movement_beyond_decay"] is False, "1.017x decay must not pass"
    assert gates["all_mechanics_pass"] is False


def test_a_single_dead_tensor_is_enough_to_fail():
    report = f1b.gradient_coverage(_FakeEncoder(dead=["blocks.3.attention.key.weight"]))
    assert report["zero_norm"] == 1


def test_none_gradient_is_treated_as_dead_not_merely_missing():
    """`grad is None` must fail the same way zero does; T1's gate only counted None."""
    report = f1b.gradient_coverage(_FakeEncoder(missing=["blocks.0.attention.value.bias"]))
    assert report["zero_norm"] == 1 and report["rows"][0] is not None


def test_pooling_would_have_hidden_the_defect():
    """Demonstrates why per-tensor reporting is mandatory."""
    dead = [f"blocks.{b}.attention.{r}.{s}" for b in range(6)
            for r in ("query", "key", "value") for s in ("weight", "bias")]
    enc = _FakeEncoder(dead=dead)
    pooled = sum(float(p.grad.norm()) ** 2 for _, p in enc.named_parameters()
                 if p.grad is not None) ** 0.5
    assert pooled > 0, "a pooled norm looks healthy"
    assert f1b.gradient_coverage(enc)["zero_norm"] == 36, "per-tensor sees the dead ones"


# --------------------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------------------

def _healthy():
    return (f1b.gradient_coverage(_FakeEncoder()),
            {"tensors": 48, "zero_moments": 0, "zero_tensors": []},
            {"ratio_over_decay": 500.0, "pure_decay_prediction": 2e-4,
             "mean_relative_movement": 0.1, "min_relative_movement": 0.05},
            {"min_per_query_routing_spread": 1e-3, "mean_n_eff_over_n": 0.99},
            {"rare": {"retention": 1.0, "magnitude": 1.0, "spread": 0.5, "saturated": False}},
            {"rare": {"retention": 1.0, "magnitude": 1.0, "spread": 0.5, "saturated": False}})


def test_healthy_run_passes_all_mechanics_gates():
    c, m, mv, r, e, b = _healthy()
    gates = f1b.evaluate_gates(c, m, mv, r, e, b, f1b.Frozen(), {"mean_n_eff_over_n": 0.99}, True)
    assert gates["all_mechanics_pass"] is True


def test_retention_is_immune_to_global_rescaling():
    """A magnitude endpoint fires on any rescaling; retention must not."""
    import numpy as _np
    frozen = f1b.Frozen()
    states = torch.randn(3, 64, 16)
    weights = {"p": _np.random.default_rng(0).normal(size=64).astype("float32")}
    base, base_proj = f1b.endpoint_report(states, weights, frozen)
    scaled, _ = f1b.endpoint_report(states * 7.5, weights, frozen, base_proj)
    assert scaled["p"]["retention"] == pytest.approx(1.0, abs=1e-5), "rescaling must not degrade retention"
    assert scaled["p"]["magnitude"] != pytest.approx(base["p"]["magnitude"], rel=1e-3)


def test_retention_detects_a_real_direction_change():
    import numpy as _np
    frozen = f1b.Frozen()
    states = torch.randn(3, 64, 16)
    weights = {"p": _np.random.default_rng(0).normal(size=64).astype("float32")}
    _, base_proj = f1b.endpoint_report(states, weights, frozen)
    rotated, _ = f1b.endpoint_report(torch.randn(3, 64, 16), weights, frozen, base_proj)
    assert rotated["p"]["retention"] < 0.9


def test_g5_aborts_on_endpoint_degradation():
    c, m, mv, r, e, b = _healthy()
    e = {"rare": {"retention": 0.90, "magnitude": 1.0, "spread": 0.5, "saturated": False}}
    gates = f1b.evaluate_gates(c, m, mv, r, e, b, f1b.Frozen(), {"mean_n_eff_over_n": 0.99}, True)
    assert gates["G5_rare_non_degradation"] is False
    assert gates["degraded_endpoints"] == ["rare"]


def test_saturated_endpoints_are_not_decision_bearing():
    """T1's R2 endpoints sat at 0.9999 and could not register damage."""
    c, m, mv, r, _, _ = _healthy()
    base = {"sat": {"retention": 1.0, "magnitude": 0.9999, "spread": 1e-9, "saturated": True}}
    now = {"sat": {"retention": 0.10, "magnitude": 0.5, "spread": 1e-9, "saturated": True}}
    gates = f1b.evaluate_gates(c, m, mv, r, now, base, f1b.Frozen(), {"mean_n_eff_over_n": 0.99}, True)
    assert gates["G5_rare_non_degradation"] is True, "saturated endpoints must be excluded"


def test_g4_rejects_identical_routing_across_queries():
    c, m, mv, _, e, b = _healthy()
    r = {"min_per_query_routing_spread": 0.0, "mean_n_eff_over_n": 0.99}
    gates = f1b.evaluate_gates(c, m, mv, r, e, b, f1b.Frozen(), {"mean_n_eff_over_n": 0.99}, True)
    assert gates["G4_routing_diversity"] is False


def test_routing_outcome_names_all_three_states():
    c, m, mv, r, e, b = _healthy()
    frozen = f1b.Frozen()
    sharp = f1b.evaluate_gates(c, m, mv, {"min_per_query_routing_spread": 1e-3,
                                          "mean_n_eff_over_n": 0.50}, e, b, frozen,
                               {"mean_n_eff_over_n": 0.99}, True)
    assert sharp["routing_outcome"] == "ROUTING_SHARPENED"
    diffuse = f1b.evaluate_gates(c, m, mv, r, e, b, frozen, {"mean_n_eff_over_n": 0.99}, True)
    assert diffuse["routing_outcome"] == "ROUTING_DIFFUSE_WITH_HEALTHY_GRADIENTS"
    dead = f1b.evaluate_gates(f1b.gradient_coverage(_FakeEncoder(dead=["blocks.0.attention.key.weight"])),
                              {"tensors": 48, "zero_moments": 1, "zero_tensors": []},
                              {"ratio_over_decay": 1.0, "pure_decay_prediction": 2e-4,
                               "mean_relative_movement": 2e-4, "min_relative_movement": 2e-4},
                              r, e, b, frozen, {"mean_n_eff_over_n": 0.99}, True)
    assert dead["routing_outcome"] == "ROUTING_UNRESOLVED"


def test_movement_gate_uses_the_exact_decoupled_decay_formula():
    frozen = f1b.Frozen()
    enc = _FakeEncoder()
    baseline = {n: torch.ones(2) for n, _ in enc.named_parameters()}

    class P:
        def __init__(self, v): self._v = v
        def detach(self): return self._v
    class E:
        def named_parameters(self):
            return [(n, P(torch.ones(2))) for n in baseline]
    report = f1b.movement_report(E(), baseline, frozen, 205)
    expected = 1.0 - (1.0 - frozen.learning_rate * frozen.weight_decay) ** 205
    assert report["pure_decay_prediction"] == pytest.approx(expected, rel=1e-12)
    assert report["pure_decay_prediction"] == pytest.approx(2.049791e-04, rel=1e-5)


# --------------------------------------------------------------------------------------
# Objective
# --------------------------------------------------------------------------------------

def test_directional_loss_is_blind_to_a_cell_global_shift():
    """The objective must not be solvable through the CELL/global pathway."""
    mod = f1b.load_recovered_components(CANONICAL)
    torch.manual_seed(0)
    predicted = torch.randn(4, 6, 16)
    target = torch.randn(4, 6, 16)
    pairs = torch.tensor([[0, 1], [2, 3]])
    base, _ = mod.directional_pair_context_loss(predicted, target, pairs)
    shifted = predicted + torch.randn(4, 1, 16) * 5.0
    after, _ = mod.directional_pair_context_loss(shifted, target, pairs)
    assert float(base) == pytest.approx(float(after), rel=1e-5, abs=1e-6)


def test_centering_removes_the_per_cell_mean():
    mod = f1b.load_recovered_components(CANONICAL)
    x = torch.randn(3, 5, 8)
    centred = mod.center_queries(x)
    assert torch.allclose(centred.mean(dim=1), torch.zeros(3, 8), atol=1e-6)


def test_g5_is_not_terminal_in_synthetic_mode():
    """Synthetic expression carries no biology and no probe can be refit on it."""
    c, m, mv, r, _, b = _healthy()
    collapsed = {"rare": {"retention": 0.10, "magnitude": 1.0, "spread": 0.5, "saturated": False}}
    gates = f1b.evaluate_gates(c, m, mv, r, collapsed, b, f1b.Frozen(),
                               {"mean_n_eff_over_n": 0.99}, biology_evaluable=False)
    assert gates["G5_rare_non_degradation"] == "NOT_EVALUABLE_SYNTHETIC"
    assert gates["G5_terminal"] is False
    assert gates["all_mechanics_pass"] is True, "G1-G4 must still decide in synthetic mode"


def test_g5_is_terminal_where_biology_is_evaluable():
    c, m, mv, r, _, b = _healthy()
    collapsed = {"rare": {"retention": 0.10, "magnitude": 1.0, "spread": 0.5, "saturated": False}}
    gates = f1b.evaluate_gates(c, m, mv, r, collapsed, b, f1b.Frozen(),
                               {"mean_n_eff_over_n": 0.99}, biology_evaluable=True)
    assert gates["G5_rare_non_degradation"] is False
    assert gates["G5_terminal"] is True
    assert gates["all_mechanics_pass"] is False
