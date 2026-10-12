"""End-to-end in-memory generator hardening tests.

These tests deliberately replace the qualification RNG root with TEST_ROOT=4242.
They never realize or write the frozen qualification worlds.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import generate_v79_v2_core_worlds as G  # noqa: E402
import v79_v2_core_world_assembly as A  # noqa: E402

TEST_ROOT = 4242
CAL = json.loads((ROOT / "results/v79/development/v2_core_planting_calibration/"
                         "V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json").read_text(encoding="utf-8"))


def _engineering_payload() -> dict:
    _, payload = G.load_launch_contract(ROOT)
    out = copy.deepcopy(payload)
    out["seeds"]["root"] = TEST_ROOT
    return out


def _packages():
    payload = _engineering_payload()
    amendment = G.load_pairing_amendment(ROOT)
    designs = G.build_world_designs(ROOT, payload)
    by_name = {}
    for world in payload["worlds"]["world_list"]:
        by_name[world["name"]] = A.assemble_world_in_memory(payload, CAL, designs, copy.deepcopy(world), amendment)
    return payload, designs, by_name


def test_all_twelve_worlds_assemble_with_three_replicates_and_no_execution_authority():
    payload, designs, worlds = _packages()
    expected = [w["name"] for w in payload["worlds"]["world_list"]]
    assert list(worlds) == expected
    assert len(worlds) == 12
    for name, pkg in worlds.items():
        design = designs[name]
        assert pkg["support"].shape == (len(design["src"]), 44)
        assert set(pkg["observations"]) == {"train", "same_donor", "new_donor"}
        assert pkg["benchmark_run"] is False
        assert pkg["qualification_fits_run"] == 0
        assert pkg["training_authorized"] is False
        for rep in pkg["observations"].values():
            G.validate_poison_integrity(rep["observed"], pkg["support"], poison=-1.0)


def test_new_donor_replicate_changes_donor_realization_but_not_fixed_truth():
    _, _, worlds = _packages()
    q0 = worlds["Q00_BASELINE"]
    for part in ("detection", "positive"):
        base = q0["truth"][part]
        new = q0["new_donor_truth"][part]
        for key in ("intercept", "depth1", "depth2", "class_contrasts", "source_contrasts"):
            assert np.array_equal(base[key], new[key])
        assert np.array_equal(base["donor_sd"], new["donor_sd"])
        assert np.array_equal(base["factor_loading"], new["factor_loading"])
        assert not np.array_equal(base["donor_raw_centered"], new["donor_raw_centered"])
        assert not np.array_equal(base["donor_effects"], new["donor_effects"])


def test_q07_has_no_active_donor_factor_in_train_or_new_donor_truth():
    _, _, worlds = _packages()
    q7 = worlds["Q07_DONOR_ABSENT"]
    for truth in (q7["truth"], q7["new_donor_truth"]):
        for part in ("detection", "positive"):
            assert np.count_nonzero(truth[part]["donor_sd"]) == 0
            assert np.count_nonzero(truth[part]["donor_raw_centered"]) == 0
            assert np.count_nonzero(truth[part]["donor_effects"]) == 0
            assert np.count_nonzero(truth[part]["factor_loading"]) == 0


def test_q08_sparse_prevalence_is_realized_on_final_measured_fixed_predictor():
    _, designs, worlds = _packages()
    q8 = worlds["Q08_SPARSE_DETECTION"]
    det = q8["truth"]["detection"]
    nonint = G.detection_nonintercept_predictor(designs[q8["world"]], det)
    alpha = np.asarray(det["intercept"], float)
    prob = 1.0 / (1.0 + np.exp(-np.clip(nonint + alpha[None, :], -40.0, 40.0)))
    target = np.asarray(det["prevalence"], float)
    assert np.all((target >= 0.005) & (target <= 0.05))
    achieved = np.asarray([prob[q8["support"][:, g], g].mean() for g in range(44)])
    assert np.allclose(achieved, target, atol=1e-10, rtol=0.0)


def test_q10_q11_are_paired_for_all_non_operator_truth_and_all_three_noise_replicates():
    _, _, worlds = _packages()
    q10 = worlds["Q10_S174_DESIGN_IMBALANCE"]
    q11 = worlds["Q11_OMITTED_OPERATOR"]
    assert np.array_equal(q10["support"], q11["support"])
    assert G.scientific_truth_sha(q10["truth"]) == G.scientific_truth_sha(q11["truth"])
    assert G.scientific_truth_sha(q10["new_donor_truth"]) == G.scientific_truth_sha(q11["new_donor_truth"])
    assert q10["operator_offsets"] is None
    assert q11["operator_offsets"] is not None
    for rep in ("train", "same_donor", "new_donor"):
        assert np.array_equal(q10["observations"][rep]["base_uniform"], q11["observations"][rep]["base_uniform"])
        assert np.array_equal(q10["observations"][rep]["base_normal"], q11["observations"][rep]["base_normal"])
    assert not np.array_equal(q10["observations"]["train"]["eta_detection"],
                              q11["observations"]["train"]["eta_detection"])


def test_complete_assembly_is_deterministic_under_engineering_seed():
    _, _, a = _packages()
    _, _, b = _packages()
    for name in a:
        assert G.scientific_truth_sha(a[name]) == G.scientific_truth_sha(b[name])
