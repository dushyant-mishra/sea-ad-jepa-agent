from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import v79_v2_core_fit_model as M  # noqa: E402


def _contract():
    p = Path(__file__).resolve().parents[2] / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _gene():
    design = {
        "src": np.array([0, 0, 0, 1, 1, 1, 2, 2, 2], dtype=np.int16),
        "donor": np.array([0, 1, 2, 3, 4, 5, 6, 7, 8], dtype=np.int16),
        "cls": np.array([0, 1, 2, 0, 1, 2, 0, 1, 2], dtype=np.int8),
        "log_lib": np.array([1.,2.,3.,1.5,2.5,3.5,0.5,1.5,2.5]),
    }
    class G: pass
    g = G(); g.design=design
    g.detected=np.array([0,1,1,0,1,1,0,1,1], dtype=np.int8)
    g.observed=np.array([0.,2.,3.,0.,4.,5.,0.,6.,7.])
    g.detection_mask=np.array([1,1,1,1,1,1,1,1,0], dtype=bool)
    g.positive_mask=g.detection_mask & (g.observed > 0)
    return g


def test_model_fingerprint_is_contract_derived_and_excludes_forbidden_terms():
    fp = M.model_fingerprint(_contract())
    assert fp["name"] == "V2_CORE"
    assert fp["parts"] == ["detection", "positive"]
    assert fp["terms"] == ["depth1", "depth2", "class", "source", "donor_within_source"]
    text = json.dumps(fp).lower()
    assert "operator" not in text
    assert "matrix" not in text
    assert "donor_x_class" not in text
    assert "source_x_class" not in text


def test_prepare_design_uses_population_depth_and_orthonormal_sum_zero_bases():
    d = M.prepare_design(_gene().design)
    assert np.isclose(float(np.mean(d["z"])), 0.0, atol=1e-12)
    assert np.isclose(float(np.std(d["z"], ddof=0)), 1.0, atol=1e-12)
    assert np.allclose(d["q"], d["z"] ** 2 - 1.0)
    for key in ("class_basis", "source_basis"):
        b = np.asarray(d[key])
        assert b.shape[1] == 2
        assert np.allclose(b.T @ b, np.eye(2), atol=1e-12)
        assert np.allclose(b.sum(0), 0.0, atol=1e-12)
    w = np.asarray(d["donor_basis_by_donor"])
    assert w.shape == (9, 6)
    assert np.allclose(w.T @ w, np.eye(6), atol=1e-12)
    for src in range(3):
        donors = np.where(np.asarray(d["donor_source"]) == src)[0]
        assert np.allclose(w[donors].sum(0), 0.0, atol=1e-12)


def test_masks_enforce_structural_measurement_and_positive_observed_only():
    g = _gene()
    det = M.prepare_detection_data(g)
    pos = M.prepare_positive_data(g)
    assert det["y"].tolist() == [0,1,1,0,1,1,0,1]
    assert pos["y_log"].tolist() == pytest.approx(np.log([2,3,4,5,6]).tolist())
    assert len(det["z"]) == 8
    assert len(pos["z"]) == 5


def test_num_pyro_graph_instantiates_exact_frozen_sites_without_forbidden_terms():
    import jax.random as jr
    from numpyro import handlers

    c = _contract(); g = _gene()
    det = handlers.trace(handlers.seed(M.build_detection_model(c, g), jr.PRNGKey(1))).get_trace()
    pos = handlers.trace(handlers.seed(M.build_positive_model(c, g), jr.PRNGKey(2))).get_trace()

    det_samples = {k for k, v in det.items() if v.get("type") == "sample"}
    pos_samples = {k for k, v in pos.items() if v.get("type") == "sample"}
    assert det_samples == {"alpha", "beta_depth1", "beta_depth2", "class_contrasts",
                           "source_contrasts", "donor_sd", "donor_raw", "obs"}
    assert pos_samples == {"alpha", "gamma_depth1", "gamma_depth2", "class_contrasts",
                           "source_contrasts", "donor_sd", "donor_raw", "sigma", "obs"}
    assert det["obs"]["is_observed"] is True and pos["obs"]["is_observed"] is True
    assert tuple(det["obs"]["value"].shape) == (8,)
    assert tuple(pos["obs"]["value"].shape) == (5,)
    text = " ".join(sorted(det_samples | pos_samples)).lower()
    for forbidden in ("operator", "matrix", "dataset", "interaction"):
        assert forbidden not in text


def test_model_builders_refuse_non_v2_core_contract():
    c = _contract(); c["model"]["name"] = "OTHER"
    with pytest.raises(M.FitModelRefused):
        M.model_fingerprint(c)
