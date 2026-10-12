from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_v2_core_observation as O  # noqa: E402

PAYLOAD = json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json").read_text())


def test_normalized_helmert_is_orthonormal_and_sum_to_zero():
    H = O.normalized_helmert(3)
    assert H.shape == (3,2)
    assert np.allclose(H.T @ H, np.eye(2), atol=1e-14)
    assert np.allclose(H.sum(0), 0.0, atol=1e-14)


def test_depth_basis_uses_population_standardization_and_q_z2_minus_1():
    loglib = np.array([1.,2.,4.,8.])
    z, q = O.depth_basis(loglib)
    assert float(z.mean()) == pytest.approx(0.0, abs=1e-14)
    assert float(z.std(ddof=0)) == pytest.approx(1.0, abs=1e-14)
    assert np.allclose(q, z*z - 1.0)


def _design():
    return {
        "log_lib": np.array([-1.,0.,1.,2.,-2.,0.5]),
        "cls": np.array([0,1,2,0,1,2], dtype=np.int64),
        "src": np.array([0,0,1,1,2,2], dtype=np.int64),
        "donor": np.array([0,0,1,1,2,2], dtype=np.int64),
        "op": np.array([0,0,1,1,2,2], dtype=np.int64),
    }


def _truth(G=2):
    return {
        "detection": {
            "intercept": np.array([-0.4,0.3]),
            "depth1": np.array([0.7,-0.2]),
            "depth2": np.array([0.1,0.05]),
            "class_contrasts": np.array([[0.2,-0.1],[0.1,0.3]]),
            "source_contrasts": np.array([[0.15,-0.2],[-0.1,0.05]]),
            "donor_effects": np.array([[0.1,-0.1],[-0.2,0.2],[0.1,-0.1]]),
        },
        "positive": {
            "intercept": np.array([0.6,1.0]),
            "depth1": np.array([0.2,-0.1]),
            "depth2": np.array([0.03,0.02]),
            "class_contrasts": np.array([[0.08,-0.04],[0.02,0.06]]),
            "source_contrasts": np.array([[0.05,-0.07],[-0.03,0.04]]),
            "donor_effects": np.array([[0.05,-0.03],[-0.04,0.05],[-0.01,-0.02]]),
            "sigma": np.array([0.2,0.4]),
        },
    }


def test_linear_predictor_matches_explicit_model_basis():
    design = _design(); truth = _truth()
    eta = O.linear_predictor(design, truth["detection"])
    z,q = O.depth_basis(design["log_lib"])
    Hc, Hs = O.normalized_helmert(3), O.normalized_helmert(3)
    manual = np.empty_like(eta)
    for i in range(len(z)):
        for g in range(2):
            manual[i,g] = (truth["detection"]["intercept"][g] + truth["detection"]["depth1"][g]*z[i]
                + truth["detection"]["depth2"][g]*q[i]
                + Hc[design["cls"][i]] @ truth["detection"]["class_contrasts"][g]
                + Hs[design["src"][i]] @ truth["detection"]["source_contrasts"][g]
                + truth["detection"]["donor_effects"][design["donor"][i],g])
    assert np.allclose(eta, manual)


def test_observation_respects_measurement_support_and_poison_invariance():
    design = _design(); truth = _truth(); support = np.ones((6,2), dtype=bool)
    support[1,0] = False; support[4,1] = False
    a = O.generate_observation(design, truth, support, world_index=0, root=31000000, poison=-1)
    b = O.generate_observation(design, truth, support, world_index=0, root=31000000, poison=2_147_483_647)
    assert np.array_equal(a["detected"][support], b["detected"][support])
    assert np.array_equal(a["positive_value"][support], b["positive_value"][support])
    assert np.all(a["observed"][~support] == -1)
    assert np.all(b["observed"][~support] == 2_147_483_647)
    assert np.array_equal(a["base_uniform"], b["base_uniform"])
    assert np.array_equal(a["base_normal"], b["base_normal"])


def test_positive_values_are_continuous_lognormal_only_when_detected():
    design = _design(); truth = _truth(); support = np.ones((6,2), dtype=bool)
    out = O.generate_observation(design, truth, support, world_index=0, root=31000000)
    assert np.all(out["observed"][support & ~out["detected"]] == 0.0)
    assert np.all(out["positive_value"][out["detected"] & support] > 0.0)
    assert np.allclose(out["observed"][out["detected"] & support], out["positive_value"][out["detected"] & support])
    assert out["observed"].dtype == np.float64


def test_same_donor_replicate_changes_only_observation_noise_streams():
    design = _design(); truth = _truth(); support = np.ones((6,2), dtype=bool)
    train = O.generate_observation(design, truth, support, world_index=0, root=31000000, replicate="train")
    hold = O.generate_observation(design, truth, support, world_index=0, root=31000000, replicate="same_donor")
    assert np.array_equal(train["eta_detection"], hold["eta_detection"])
    assert np.array_equal(train["mu_positive"], hold["mu_positive"])
    assert not np.array_equal(train["base_uniform"], hold["base_uniform"])
    assert not np.array_equal(train["base_normal"], hold["base_normal"])


def test_q10_q11_common_random_numbers_differ_only_through_operator_offsets():
    design = _design(); truth = _truth(); support = np.ones((6,2), dtype=bool)
    det_offset = np.zeros((3,2)); pos_offset = np.zeros((3,2))
    det_offset[:,0] = np.array([-0.4,0.0,0.4]); pos_offset[:,1] = np.array([0.2,-0.1,-0.1])
    q10 = O.generate_observation(design, truth, support, world_index=10, root=31000000, pairing_parent_world=10)
    q11 = O.generate_observation(design, truth, support, world_index=11, root=31000000, pairing_parent_world=10,
                                 operator_offsets_detection=det_offset, operator_offsets_positive=pos_offset)
    assert np.array_equal(q10["base_uniform"], q11["base_uniform"])
    assert np.array_equal(q10["base_normal"], q11["base_normal"])
    # The no-offset gene/part stays identical at the linear-predictor level.
    assert np.array_equal(q10["eta_detection"][:,1], q11["eta_detection"][:,1])
    assert np.array_equal(q10["mu_positive"][:,0], q11["mu_positive"][:,0])
    # Offset-bearing components move exactly by the operator offsets indexed per cell.
    assert np.allclose(q11["eta_detection"][:,0]-q10["eta_detection"][:,0], det_offset[design["op"],0])
    assert np.allclose(q11["mu_positive"][:,1]-q10["mu_positive"][:,1], pos_offset[design["op"],1])
