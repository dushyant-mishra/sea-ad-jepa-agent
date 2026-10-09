"""The context shortcut audit must be able to see what it is for: an identity code that a linear
probe misses but a nonlinear probe reads, a field that carries only donor signal, and a field that
carries nothing. Raw identity is a forbidden control by name, whatever the probes say."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("shortcut", ROOT / "scripts" / "v77" / "audit_v77_context_shortcuts.py")
A = importlib.util.module_from_spec(spec)
sys.modules["shortcut"] = A
spec.loader.exec_module(A)

N, K_OPS = 800, 8
OPS = np.repeat(np.arange(K_OPS), N // K_OPS)
SRC = OPS // 2
# consecutive cell pairs share a donor, so every donor sits in both halves of the parity split,
# and donors cycle independently of the operator blocks (crossed, not nested)
DONOR = (np.arange(N) // 2) % 10
GCI = np.arange(N)
TARGETS = dict(source=SRC, study=SRC, operator=OPS, donor=DONOR)


def _field(X, discrete, binary=False):
    return dict(X=np.asarray(X, dtype=np.float64).reshape(N, -1), discrete=discrete, binary=binary, visibility="TEST")


def test_hash_code_is_missed_by_linear_and_read_by_nonlinear_probes():
    code = ((OPS * 7919) % 97).astype(np.float64)
    res = A.audit_field("hash_code", _field(code, discrete=True), TARGETS, GCI)
    assert res["probes"]["LINEAR"]["operator"]["lift"] < 0.5
    assert res["probes"]["KNN"]["operator"]["lift"] > 0.9 and res["probes"]["LOOKUP"]["operator"]["lift"] > 0.9
    assert res["risk_class"] == "HIGH_IDENTITY_PROXY_RISK"


def test_a_field_carrying_nothing_is_low_risk():
    rng = np.random.default_rng(5)
    res = A.audit_field("noise", _field(rng.normal(size=N), discrete=False), TARGETS, GCI)
    assert res["risk_class"] == "LOW_SHORTCUT_RISK", res["probes"]


def test_donor_only_signal_is_conditional():
    rng = np.random.default_rng(6)
    x = DONOR * 3.0 + rng.normal(scale=0.3, size=N)
    res = A.audit_field("donor_signal", _field(x, discrete=False), TARGETS, GCI)
    assert res["risk_class"] == "CONDITIONAL", res["probes"]


def test_raw_identity_is_a_forbidden_control_by_name():
    res = A.audit_field("operator_index", _field(OPS, discrete=True), TARGETS, GCI)
    assert res["risk_class"] == "FORBIDDEN_RAW_IDENTITY_CONTROL"


def test_binary_support_patterns_are_read_by_hamming_neighbours_and_lookup():
    rng = np.random.default_rng(7)
    base = rng.random((K_OPS, 300)) < 0.5
    pattern = base[OPS]
    res = A.audit_field("support_pattern", _field(pattern, discrete=True, binary=True), TARGETS, GCI)
    assert res["probes"]["LOOKUP"]["operator"]["lift"] == 1.0 and res["probes"]["KNN"]["operator"]["lift"] > 0.95
    assert res["risk_class"] == "HIGH_IDENTITY_PROXY_RISK"


def test_permuted_labels_sit_at_chance():
    code = ((OPS * 7919) % 97).astype(np.float64)
    res = A.audit_field("hash_code", _field(code, discrete=True), TARGETS, GCI)
    for probe in ("LINEAR", "KNN", "LOOKUP"):
        assert abs(res["probes"][probe]["operator"]["null_mean_lift"]) < 0.15, probe


def test_the_audit_is_deterministic():
    rng = np.random.default_rng(8)
    f = _field(rng.normal(size=(N, 3)), discrete=False)
    assert A.audit_field("x", f, TARGETS, GCI) == A.audit_field("x", f, TARGETS, GCI)


def test_lift_reports_test_classes_the_probe_never_saw():
    r = A.lift_of(np.array([0, 1, 2]), np.array([0, 1, 1]), np.array([0, 1, 1]))
    assert r["n_test_classes_unseen_in_train"] == 1


def test_summary_reports_lift_against_the_raw_identity_ceiling():
    def res(cls, operator_lift):
        lifts = dict(source=1.0, study=1.0, operator=operator_lift, donor=0.0)
        return dict(risk_class=cls, visibility="TEST", probes={"LOOKUP": {t: dict(lift=v) for t, v in lifts.items()}})
    world = dict(results={"operator_index": res("FORBIDDEN_RAW_IDENTITY_CONTROL", 0.8),
                          "x": res("HIGH_IDENTITY_PROXY_RISK", 0.4)})
    s = A.summarize({"W": world})
    assert s["x"]["identity_lift"]["operator"]["raw_identity_ceiling"] == 0.8
    assert s["x"]["identity_lift"]["operator"]["fraction_of_ceiling"] == 0.5
    assert s["x"]["risk_class"] == "HIGH_IDENTITY_PROXY_RISK"
