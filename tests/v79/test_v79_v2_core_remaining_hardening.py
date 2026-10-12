from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import generate_v79_v2_core_worlds as G  # noqa: E402
import v79_v2_core_observation as O  # noqa: E402
import v79_v2_core_planting as P  # noqa: E402

PAYLOAD = json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json").read_text())


def _part(donors: int = 6, genes: int = 4) -> dict:
    raw = np.arange(donors * genes, dtype=float).reshape(donors, genes)
    raw -= raw.mean(axis=0, keepdims=True)
    sd = np.linspace(0.2, 0.5, genes)
    return {
        "donor_sd": sd.copy(),
        "donor_raw_centered": raw.copy(),
        "donor_effects": raw * sd[None, :],
        "factor_loading": np.array([0.6, 0.6, 0.0, 0.0]),
    }


def _observation_design() -> dict[str, np.ndarray]:
    return {
        "log_lib": np.array([-1., 0., 1., 2., -2., 0.5]),
        "cls": np.array([0, 1, 2, 0, 1, 2], dtype=np.int64),
        "src": np.array([0, 0, 1, 1, 2, 2], dtype=np.int64),
        "donor": np.array([0, 0, 1, 1, 2, 2], dtype=np.int64),
        "op": np.array([0, 0, 35, 35, 24, 24], dtype=np.int64),
    }


def _observation_truth() -> dict:
    return {
        "detection": {
            "intercept": np.array([-0.4, 0.3]),
            "depth1": np.array([0.7, -0.2]),
            "depth2": np.array([0.1, 0.05]),
            "class_contrasts": np.array([[0.2, -0.1], [0.1, 0.3]]),
            "source_contrasts": np.array([[0.15, -0.2], [-0.1, 0.05]]),
            "donor_effects": np.array([[0.1, -0.1], [-0.2, 0.2], [0.1, -0.1]]),
        },
        "positive": {
            "intercept": np.array([0.6, 1.0]),
            "depth1": np.array([0.2, -0.1]),
            "depth2": np.array([0.03, 0.02]),
            "class_contrasts": np.array([[0.08, -0.04], [0.02, 0.06]]),
            "source_contrasts": np.array([[0.05, -0.07], [-0.03, 0.04]]),
            "donor_effects": np.array([[0.05, -0.03], [-0.04, 0.05], [-0.01, -0.02]]),
            "sigma": np.array([0.2, 0.4]),
        },
    }


def test_new_donor_effects_use_frozen_streams_3_18_19_and_keep_loading_assignment():
    assert hasattr(P, "build_new_donor_effects")
    src_by_donor = np.array([0, 0, 1, 1, 2, 2], dtype=np.int64)
    sd = np.linspace(0.2, 0.5, 4)
    train = P.build_donor_effects(src_by_donor, sd, world_index=3, part="detection", root=31000000)
    new = P.build_new_donor_effects(src_by_donor, sd, world_index=3, part="detection", root=31000000)
    assert np.array_equal(train["lambda"], new["lambda"])
    assert not np.array_equal(train["shared_factor"], new["shared_factor"])
    assert not np.array_equal(train["raw_centered"], new["raw_centered"])
    for s in np.unique(src_by_donor):
        assert np.allclose(new["effects"][src_by_donor == s].mean(axis=0), 0.0, atol=1e-12)


def test_new_donor_observation_uses_frozen_noise_streams_20_21():
    design = _observation_design()
    truth = _observation_truth()
    support = np.ones((6, 2), dtype=bool)
    same = O.generate_observation(design, truth, support, world_index=2, root=31000000, replicate="same_donor")
    new = O.generate_observation(design, truth, support, world_index=2, root=31000000, replicate="new_donor")
    assert not np.array_equal(same["base_uniform"], new["base_uniform"])
    assert not np.array_equal(same["base_normal"], new["base_normal"])


def test_partial_structural_support_uses_reserved_stream_24():
    payload = copy.deepcopy(PAYLOAD)
    src = np.concatenate([np.full(24, 0), np.full(7, 1), np.full(11, 2)]).astype(np.int64)
    op = np.arange(42, dtype=np.int64)
    design = {"src": src, "op": op}
    amendment = G.load_pairing_amendment(ROOT)
    support = G.build_structural_support(payload, design, world_index=0, genes=44, amendment=amendment)
    affected = np.where((~support).any(axis=0))[0]
    partial_gene = next(int(g) for g in affected if 0 < int((~support[src == G.SOURCE_CODES["NPH52"], g]).sum()) < 7)
    nph_ops = np.unique(op[src == G.SOURCE_CODES["NPH52"]])
    rng = np.random.default_rng(G.seed_for(world_index=0, gene_index=partial_gene, stream=24, root=31000000))
    expected = set(int(x) for x in rng.choice(nph_ops, size=3, replace=False))
    actual = set(int(x) for x in op[(src == G.SOURCE_CODES["NPH52"]) & (~support[:, partial_gene])])
    assert actual == expected


def test_build_world_designs_refuses_unverified_source_name_code_mapping():
    old = dict(G.SOURCE_CODES)
    try:
        G.SOURCE_CODES.clear()
        G.SOURCE_CODES.update({"HVS": 1, "NPH52": 0, "SEA_AD": 2})
        with pytest.raises(SystemExit):
            G.build_world_designs(ROOT, PAYLOAD)
    finally:
        G.SOURCE_CODES.clear()
        G.SOURCE_CODES.update(old)


def test_q07_donor_absent_removes_active_latent_donor_factor():
    truth = {"detection": _part(), "positive": _part()}
    q07 = next(w for w in PAYLOAD["worlds"]["world_list"] if w["name"] == "Q07_DONOR_ABSENT")
    out = G.apply_world_modifications(truth, q07, PAYLOAD)
    for part in ("detection", "positive"):
        assert np.count_nonzero(out[part]["donor_sd"]) == 0
        assert np.count_nonzero(out[part]["donor_effects"]) == 0
        assert np.count_nonzero(out[part]["donor_raw_centered"]) == 0
        assert np.count_nonzero(out[part]["factor_loading"]) == 0


def test_poison_integrity_refuses_sentinel_in_measured_entry():
    assert hasattr(G, "validate_poison_integrity")
    support = np.array([[True, False], [True, True]], dtype=bool)
    observed = np.array([[0.0, -1.0], [2.0, 1.0]])
    G.validate_poison_integrity(observed, support, poison=-1.0)
    bad = observed.copy()
    bad[1, 0] = -1.0
    with pytest.raises(SystemExit):
        G.validate_poison_integrity(bad, support, poison=-1.0)
