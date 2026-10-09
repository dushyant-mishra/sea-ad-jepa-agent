from __future__ import annotations

import importlib

import numpy as np
import pytest


def _good_gate():
    return {
        "schema": "V78_PREEXECUTION_GATE_V1",
        "status": "READY",
        "blockers": [],
        "training_authorized": False,
        "post_outcome_retuning_authorized": False,
        "details": {
            "e2_reference": {"status": "AUTHENTICATED"},
            "operator_bridge": {
                "status": "AUTHENTICATED",
                "n_operators": 42,
                "operator_indices": list(range(42)),
            },
            "marginal_authority": {
                "status": "AUTHENTICATED",
                "sha256": "a" * 64,
                "canonical_corrected_train": True,
                "training_authorized": False,
            },
            "corrected_train_cache": {
                "status": "AUTHENTICATED",
                "n_count_shards": 42,
                "n_meta_shards": 42,
            },
            "operator_support_2k": {
                "status": "PASS",
                "operators_present": 42,
                "minimum_operator_count": 1,
            },
        },
    }


def test_frozen_execution_driver_surface_exists_and_freezes_arm_order():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    assert m.ARMS == ("F0", "F1", "F2", "F3")
    assert m.DEFAULT_SEED == 7302
    assert m.DEFAULT_MEASUREMENT_SEED == 7302
    assert m.NO_POST_OUTCOME_RETUNING is True
    assert callable(m.run_frozen_tournament)
    assert callable(m.observe_frozen_arm)


def test_execution_driver_refuses_unready_gate():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    with pytest.raises(PermissionError):
        m.require_ready_gate({"status": "BLOCKED", "blockers": ["x"]}, "a" * 64)


def test_execution_driver_refuses_unbound_or_fabricated_ready_gate():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    fake = {
        "status": "READY",
        "blockers": [],
        "training_authorized": False,
        "post_outcome_retuning_authorized": False,
    }
    with pytest.raises(PermissionError):
        m.require_ready_gate(fake, "a" * 64)


def test_execution_driver_binds_ready_gate_to_exact_marginal_authority():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    gate = _good_gate()
    m.require_ready_gate(gate, "a" * 64)
    with pytest.raises(PermissionError):
        m.require_ready_gate(gate, "b" * 64)


def test_execution_driver_rejects_incomplete_physical_cache_authentication():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    gate = _good_gate()
    gate["details"]["corrected_train_cache"]["n_meta_shards"] = 41
    with pytest.raises(PermissionError):
        m.require_ready_gate(gate, "a" * 64)


def test_f3_operator_source_labels_come_from_bridge_bound_depth_authority():
    m = importlib.import_module("scripts.v77.run_v78_frozen_execution")
    depth = {
        "operators": {
            "0": {"source": "HVS"},
            "1": {"source": "NPH52"},
            "2": {"source": "SEA_AD"},
        }
    }
    got = m._operator_source_labels_from_depth_authority(np.array([2, 0, 1]), depth)
    assert got.tolist() == ["SEA_AD", "HVS", "NPH52"]
    with pytest.raises(RuntimeError):
        m._operator_source_labels_from_depth_authority(np.array([3]), depth)
