from __future__ import annotations

import copy
import importlib.util

from scripts.v5 import td_qualification_registry_v1 as R


def _load():
    name = "scripts.v5.td_execution_manifest_v1"
    spec = importlib.util.find_spec(name)
    assert spec is not None, f"required execution manifest module missing: {name}"
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_synthetic_rehearsal_manifest_freezes_exact_executor_identities():
    M = _load()
    registry = R.load_registry()
    manifest = M.build_execution_manifest(registry, mode="SYNTHETIC_REHEARSAL", requested_gates=["G2", "G6", "R1"])
    assert manifest["schema"] == "JEPA_TD_EXECUTION_MANIFEST_V1"
    assert manifest["mode"] == "SYNTHETIC_REHEARSAL"
    assert list(manifest["gates"]) == ["G2", "G6", "R1"]
    assert manifest["gates"]["G2"]["executor"] == registry["gates"]["G2"]["executor"]
    assert manifest["gates"]["G6"]["lifecycle_state"] == "SYNTHETIC_KNOWN_TRUTH_QUALIFIED"
    assert "branch" not in repr(manifest["gates"])
    assert len(manifest["manifest_sha256"]) == 64
    assert M.validate_execution_manifest(manifest) == manifest


def test_human_execution_manifest_fails_closed_on_current_registry():
    M = _load()
    registry = R.load_registry()
    try:
        M.build_execution_manifest(registry, mode="HUMAN_TD", requested_gates=["G8"])
    except M.ManifestError as exc:
        text = str(exc).lower()
        assert "g8" in text
        assert "human" in text or "block" in text
    else:
        raise AssertionError("current G8 must not be manifestable for human TD")


def test_manifest_binds_canonical_registry_digest_and_changes_on_scientific_mutation():
    M = _load()
    registry = R.load_registry()
    one = M.build_execution_manifest(registry, mode="SYNTHETIC_REHEARSAL", requested_gates=["G7"])
    mutated = copy.deepcopy(registry)
    mutated["gates"]["G7"]["statistical_law"] += "__MUTATED"
    two = M.build_execution_manifest(mutated, mode="SYNTHETIC_REHEARSAL", requested_gates=["G7"])
    assert len(one["registry_sha256"]) == 64
    assert one["registry_sha256"] != two["registry_sha256"]
    assert one["manifest_sha256"] != two["manifest_sha256"]


def test_manifest_self_digest_detects_executor_or_policy_tampering():
    M = _load()
    manifest = M.build_execution_manifest(
        R.load_registry(), mode="SYNTHETIC_REHEARSAL", requested_gates=["G2", "G6"]
    )
    for mutate in ("executor", "statistical_law"):
        bad = copy.deepcopy(manifest)
        if mutate == "executor":
            bad["gates"]["G2"]["executor"]["commit_sha"] = "0" * 40
        else:
            bad["gates"]["G6"]["statistical_law"] += "__FORGED"
        try:
            M.validate_execution_manifest(bad)
        except M.ManifestError as exc:
            assert "digest" in str(exc).lower() or "manifest" in str(exc).lower()
        else:
            raise AssertionError(f"tampered manifest validated: {mutate}")


def test_manifest_rejects_unknown_or_duplicate_requested_gates():
    M = _load()
    registry = R.load_registry()
    for requested in (["G2", "G2"], ["NOT_A_GATE"]):
        try:
            M.build_execution_manifest(registry, mode="SYNTHETIC_REHEARSAL", requested_gates=requested)
        except M.ManifestError:
            pass
        else:
            raise AssertionError(f"invalid gate request accepted: {requested}")


def test_manifest_authority_remains_closed():
    M = _load()
    manifest = M.build_execution_manifest(R.load_registry(), mode="SYNTHETIC_REHEARSAL", requested_gates=["G2"])
    assert all(v is False for v in manifest["authority"].values())
