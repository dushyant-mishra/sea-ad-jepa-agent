from __future__ import annotations

import copy
import importlib.util


def _load():
    name = "scripts.v5.td_qualification_registry_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required registry module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_current_registry_validates_and_has_exact_gate_set():
    R = _load()
    registry = R.load_registry()
    out = R.validate_registry(registry)
    assert out["schema"] == "JEPA_TD_QUALIFICATION_REGISTRY_V1"
    assert set(out["gates"]) == {"R1", "G2", "G6", "G7", "G8", "G9_S1_S2", "R4_C6_C4"}


def test_lifecycle_order_is_frozen_and_cannot_skip_human_readiness():
    R = _load()
    assert R.LIFECYCLE == (
        "SEMANTICS_ONLY",
        "FIXTURE_SAME_INTERFACE",
        "SAME_CODE_PATH",
        "SYNTHETIC_KNOWN_TRUTH_QUALIFIED",
        "REAL_REFERENCE_READY",
        "HUMAN_EXECUTABLE",
    )
    registry = R.load_registry()
    bad = copy.deepcopy(registry)
    bad["gates"]["G8"]["lifecycle_state"] = "HUMAN_EXECUTABLE"
    try:
        R.validate_registry(bad)
    except R.RegistryError as exc:
        assert "human executable" in str(exc).lower()
    else:
        raise AssertionError("G8 must not skip unresolved real statistical/reference prerequisites")


def test_exact_code_identity_uses_immutable_commit_and_path_not_branch_tip():
    R = _load()
    registry = R.load_registry()
    for gate in registry["gates"].values():
        executor = gate["executor"]
        assert len(executor["commit_sha"]) == 40
        assert executor["path"].startswith("scripts/v5/")
        assert "branch" not in executor
    bad = copy.deepcopy(registry)
    bad["gates"]["G2"]["executor"]["commit_sha"] = "fix/td-real-g2-policy-status-v2-20261014"
    try:
        R.validate_registry(bad)
    except R.RegistryError:
        pass
    else:
        raise AssertionError("mutable branch names must not satisfy executable identity")


def test_missing_required_producer_blocks_human_execution_but_not_synthetic_qualification():
    R = _load()
    registry = R.load_registry()
    gate = registry["gates"]["G9_S1_S2"]
    assert gate["lifecycle_state"] == "SYNTHETIC_KNOWN_TRUTH_QUALIFIED"
    assert gate["producer"]["status"] == "REQUIRED_UNQUALIFIED"
    assert R.human_readiness(gate)["ready"] is False
    assert "producer" in " ".join(R.human_readiness(gate)["blockers"]).lower()


def test_missing_real_reference_blocks_human_execution():
    R = _load()
    registry = R.load_registry()
    gate = registry["gates"]["G6"]
    assert R.human_readiness(gate)["ready"] is False
    blockers = " ".join(R.human_readiness(gate)["blockers"]).lower()
    assert "reference" in blockers or "margin" in blockers


def test_synthetic_receipt_is_exact_head_and_workflow_bound():
    R = _load()
    registry = R.load_registry()
    for gate in registry["gates"].values():
        receipt = gate["synthetic_qualification"]
        assert receipt["system_pr"] == 369
        assert receipt["system_head_sha"] == "651d7a5a1d4f4047d5ac875cc603f9151c2fed36"
        assert receipt["workflow_run_id"] == 38577104444
        assert receipt["status"] == "PASS_SYSTEM_MECHANICS_FIREWALLS"


def test_authority_is_closed_for_every_gate_and_registry():
    R = _load()
    out = R.validate_registry(R.load_registry())
    assert all(v is False for v in out["authority"].values())
    for gate in out["gates"].values():
        assert all(v is False for v in gate["authority"].values())


def test_unknown_lifecycle_state_rejected():
    R = _load()
    bad = copy.deepcopy(R.load_registry())
    bad["gates"]["R1"]["lifecycle_state"] = "GREEN_CI_SO_HUMAN_READY"
    try:
        R.validate_registry(bad)
    except R.RegistryError as exc:
        assert "lifecycle" in str(exc).lower()
    else:
        raise AssertionError("unknown lifecycle state must fail closed")
