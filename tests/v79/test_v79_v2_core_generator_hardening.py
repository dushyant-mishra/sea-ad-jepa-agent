from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import generate_v79_v2_core_worlds as G  # noqa: E402
import v79_v2_core_observation as O  # noqa: E402
import v79_v2_core_planting as P  # noqa: E402


def _design() -> dict[str, np.ndarray]:
    src = np.repeat(np.arange(3), 6).astype(np.int64)
    donor = np.repeat(np.arange(6), 3).astype(np.int64)
    cls = np.tile(np.arange(3), 6).astype(np.int64)
    op = np.repeat(np.arange(6), 3).astype(np.int64)
    log_lib = np.linspace(-1.5, 1.5, len(src))
    return {"src": src, "donor": donor, "cls": cls, "op": op, "log_lib": log_lib}


def _production_shaped_part(donors: int = 6, genes: int = 4) -> dict:
    raw = np.arange(donors * genes, dtype=float).reshape(donors, genes)
    raw -= raw.mean(axis=0, keepdims=True)
    sd = np.linspace(0.2, 0.5, genes)
    return {
        "donor_sd": sd.copy(),
        "raw_centered": raw.copy(),
        "donor_effects": raw * sd[None, :],
    }


def _truth(genes: int = 4) -> dict:
    design = _design()
    donors = len(np.unique(design["donor"]))
    det = _production_shaped_part(donors, genes)
    pos = _production_shaped_part(donors, genes)
    det.update({
        "prevalence": np.linspace(0.15, 0.45, genes),
        "depth1": np.linspace(0.4, 0.8, genes),
        "depth2": np.linspace(0.03, 0.12, genes),
        "class_contrasts": np.tile(np.array([[0.2, -0.1]]), (genes, 1)),
        "source_contrasts": np.tile(np.array([[0.15, -0.05]]), (genes, 1)),
    })
    pos.update({
        "intercept": np.linspace(0.3, 0.8, genes),
        "depth1": np.linspace(0.1, 0.4, genes),
        "depth2": np.linspace(0.01, 0.04, genes),
        "class_contrasts": np.tile(np.array([[0.08, -0.03]]), (genes, 1)),
        "source_contrasts": np.tile(np.array([[0.05, -0.02]]), (genes, 1)),
        "sigma": np.linspace(0.25, 0.55, genes),
    })
    return {"detection": det, "positive": pos}


def _fixed_detection_predictor(design: dict[str, np.ndarray], part: dict) -> np.ndarray:
    z, q = O.depth_basis(design["log_lib"])
    cls = np.asarray(design["cls"], dtype=np.int64)
    src = np.asarray(design["src"], dtype=np.int64)
    Hc = O.normalized_helmert(len(np.unique(cls)))
    Hs = O.normalized_helmert(len(np.unique(src)))
    eta = np.broadcast_to(np.asarray(part["intercept"], dtype=float)[None, :], (len(z), len(part["intercept"]))).copy()
    eta += z[:, None] * np.asarray(part["depth1"], dtype=float)[None, :]
    eta += q[:, None] * np.asarray(part["depth2"], dtype=float)[None, :]
    eta += Hc[cls] @ np.asarray(part["class_contrasts"], dtype=float).T
    eta += Hs[src] @ np.asarray(part["source_contrasts"], dtype=float).T
    return eta


def test_rescale_donor_effects_uses_real_raw_centered_representation():
    part = _production_shaped_part()
    new_sd = np.full(4, 0.9)
    G._rescale_donor_effects(part, new_sd)
    assert np.allclose(part["donor_effects"], part["raw_centered"] * new_sd[None, :])


def test_detection_intercepts_are_recalibrated_on_final_measured_support_without_donor():
    assert hasattr(G, "calibrate_detection_intercepts")
    design = _design()
    truth = _truth()
    support = np.ones((len(design["src"]), 4), dtype=bool)
    support[design["src"] == 1, 0] = False
    support[::2, 1] = False
    out = G.calibrate_detection_intercepts(truth, design, support)
    eta = _fixed_detection_predictor(design, out["detection"])
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -40.0, 40.0)))
    for g, target in enumerate(out["detection"]["prevalence"]):
        assert float(p[support[:, g], g].mean()) == pytest.approx(float(target), abs=1e-10)


def test_new_donor_effects_use_reserved_streams_and_change_effects():
    assert hasattr(P, "build_new_donor_effects")
    src_by_donor = np.array([0, 0, 1, 1, 2, 2], dtype=np.int64)
    sd = np.linspace(0.2, 0.5, 4)
    train = P.build_donor_effects(src_by_donor, sd, world_index=3, part="detection", root=31000000)
    hold = P.build_new_donor_effects(src_by_donor, sd, world_index=3, part="detection", root=31000000)
    assert np.array_equal(train["lambda"], hold["lambda"])
    assert not np.array_equal(train["shared_factor"], hold["shared_factor"])
    assert not np.array_equal(train["raw_centered"], hold["raw_centered"])
    for s in np.unique(src_by_donor):
        m = src_by_donor == s
        assert np.allclose(hold["effects"][m].mean(axis=0), 0.0, atol=1e-12)


def test_new_donor_observation_uses_reserved_noise_streams():
    design = _design()
    truth = _truth()
    support = np.ones((len(design["src"]), 4), dtype=bool)
    truth = G.calibrate_detection_intercepts(truth, design, support)
    train = O.generate_observation(design, truth, support, world_index=2, root=31000000, replicate="train")
    same = O.generate_observation(design, truth, support, world_index=2, root=31000000, replicate="same_donor")
    new = O.generate_observation(design, truth, support, world_index=2, root=31000000, replicate="new_donor")
    assert not np.array_equal(train["base_uniform"], same["base_uniform"])
    assert not np.array_equal(same["base_uniform"], new["base_uniform"])
    assert not np.array_equal(same["base_normal"], new["base_normal"])


def test_full_support_identifies_nph52_by_7_matrix_geometry_not_numeric_code():
    payload = {
        "worlds": {"genes_per_world": 44, "structural_support_rule": {"genes_with_structural_absence_per_world": 5}},
        "seeds": {"root": 31000000},
    }
    # Deliberately permute source codes: code 2 has seven matrices and is therefore NPH52.
    src = np.concatenate([np.full(24, 1), np.full(7, 2), np.full(11, 0)]).astype(np.int64)
    design = {"src": src, "op": np.arange(42, dtype=np.int64)}
    support = G.build_structural_support(payload, design, world_index=0, genes=44)
    affected = np.where((~support).any(axis=0))[0]
    partial = []
    for g in affected:
        missing = [(s, int((~support[src == s, g]).sum()), int((src == s).sum())) for s in np.unique(src)]
        if any(0 < nmiss < ntotal for _, nmiss, ntotal in missing):
            partial.append((g, missing))
    assert len(partial) == 1
    _, missing = partial[0]
    assert [x for x in missing if x[0] == 2][0][1:] == (3, 7)


def test_s174_design_normalization_accepts_canonical_log_lib_centered_key(tmp_path: Path):
    assert hasattr(G, "load_s174_design")
    p = tmp_path / "design.npz"
    np.savez(p,
             log_lib_centered=np.array([-0.2, 0.1, 0.1]),
             cls=np.array([0, 1, 2], dtype=np.int64),
             src=np.array([0, 1, 2], dtype=np.int64),
             donor=np.array([0, 1, 2], dtype=np.int64),
             op=np.array([0, 24, 35], dtype=np.int64))
    d = G.load_s174_design(p, expected_cells=3, expected_donors=3, expected_operators=3)
    assert np.array_equal(d["log_lib"], np.array([-0.2, 0.1, 0.1]))
    assert set(d) >= {"log_lib", "cls", "src", "donor", "op"}


def test_poison_integrity_refuses_poison_in_measured_entry():
    assert hasattr(G, "validate_poison_integrity")
    support = np.array([[True, False], [True, True]], dtype=bool)
    observed = np.array([[0.0, -1.0], [2.0, 1.0]])
    G.validate_poison_integrity(observed, support, poison=-1.0)
    bad = observed.copy()
    bad[1, 0] = -1.0
    with pytest.raises(SystemExit):
        G.validate_poison_integrity(bad, support, poison=-1.0)
