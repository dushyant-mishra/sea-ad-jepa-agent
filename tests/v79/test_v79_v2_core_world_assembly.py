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

PAYLOAD = json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json").read_text())
CAL = json.loads((ROOT / "results/v79/development/v2_core_planting_calibration/V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json").read_text())
SOURCE_MAP = {"HVS": 0, "NPH52": 1, "SEA_AD": 2}


def _design() -> dict[str, np.ndarray]:
    # Frozen 24/7/11 source geometry, with every operator represented.
    source_ops = {0: np.arange(0, 24), 1: np.arange(35, 42), 2: np.arange(24, 35)}
    rows = []
    donor = 0
    for s, n_donors in [(0, 6), (1, 3), (2, 6)]:
        ops = source_ops[s]
        for j in range(n_donors):
            for k in range(6):
                rows.append((s, donor, (j + k) % 3, int(ops[(j * 6 + k) % len(ops)])))
            donor += 1
    a = np.asarray(rows, dtype=np.int64)
    return {
        "src": a[:, 0], "donor": a[:, 1], "cls": a[:, 2], "op": a[:, 3],
        "log_lib": np.linspace(-1.7, 1.6, len(a), dtype=float),
    }


def _world(name: str) -> dict:
    return next(copy.deepcopy(w) for w in PAYLOAD["worlds"]["world_list"] if w["name"] == name)


def _assemble(name: str, design: dict[str, np.ndarray], amendment: dict) -> dict:
    return A.assemble_world_in_memory(
        PAYLOAD,
        CAL,
        _world(name),
        design,
        source_code_map=SOURCE_MAP,
        amendment=amendment,
    )


def _assert_observation_package(pkg: dict) -> None:
    for key in ("train", "same_donor", "new_donor"):
        assert key in pkg["observations"]
        G.validate_poison_integrity(pkg["observations"][key]["observed"], pkg["support"], poison=-1.0)


def test_complete_world_assembly_enforces_donor_modifications_and_three_replicates():
    design = _design()
    amendment = G.load_pairing_amendment(ROOT)
    q1 = _assemble("Q01_WEAK_DONOR", design, amendment)
    q2 = _assemble("Q02_STRONG_DONOR", design, amendment)
    q7 = _assemble("Q07_DONOR_ABSENT", design, amendment)
    for pkg in (q1, q2, q7):
        _assert_observation_package(pkg)
        assert np.array_equal(pkg["truth"]["detection"]["donor_effects"],
                              pkg["truth"]["detection"]["raw_centered"] * pkg["truth"]["detection"]["donor_sd"][None, :])
        assert np.array_equal(pkg["observations"]["train"]["eta_detection"],
                              pkg["observations"]["same_donor"]["eta_detection"])
        assert not np.array_equal(pkg["observations"]["train"]["base_uniform"],
                                  pkg["observations"]["same_donor"]["base_uniform"])
    assert not np.array_equal(q1["new_donor_truth"]["detection"]["donor_effects"],
                              q1["truth"]["detection"]["donor_effects"])
    assert not np.array_equal(q2["new_donor_truth"]["detection"]["donor_effects"],
                              q2["truth"]["detection"]["donor_effects"])
    assert np.max(np.abs(q1["truth"]["detection"]["donor_effects"])) < np.max(np.abs(q2["truth"]["detection"]["donor_effects"]))
    for donor_truth in (q7["truth"], q7["new_donor_truth"]):
        for part in ("detection", "positive"):
            assert np.count_nonzero(donor_truth[part]["donor_sd"]) == 0
            assert np.count_nonzero(donor_truth[part]["donor_effects"]) == 0
            assert np.count_nonzero(donor_truth[part]["raw_centered"]) == 0
            assert np.count_nonzero(donor_truth[part]["donor_lambda"]) == 0
            assert np.count_nonzero(donor_truth[part]["donor_shared_factor"]) == 0


def test_q08_assembled_world_hits_frozen_sparse_prevalence_on_measured_fixed_predictor():
    design = _design()
    q8 = _assemble("Q08_SPARSE_DETECTION", design, G.load_pairing_amendment(ROOT))
    achieved = A.fixed_detection_prevalence(q8["truth"], design, q8["support"])
    target = q8["truth"]["detection"]["prevalence"]
    assert np.all((target >= 0.005) & (target <= 0.05))
    assert np.allclose(achieved, target, atol=1e-10, rtol=0.0)


def test_q10_q11_complete_assembly_is_paired_except_operator_perturbation():
    design = _design()
    amendment = G.load_pairing_amendment(ROOT)
    q10 = _assemble("Q10_S174_DESIGN_IMBALANCE", design, amendment)
    q11 = _assemble("Q11_OMITTED_OPERATOR", design, amendment)
    assert np.array_equal(q10["support"], q11["support"])
    assert G.scientific_truth_sha(q10["truth"]) == G.scientific_truth_sha(q11["truth"])
    assert G.scientific_truth_sha(q10["new_donor_truth"]) == G.scientific_truth_sha(q11["new_donor_truth"])
    assert q10["operator_offsets_detection"] is None and q10["operator_offsets_positive"] is None
    assert q11["operator_offsets_detection"] is not None and q11["operator_offsets_positive"] is not None
    assert np.max(np.abs(q11["operator_offsets_detection"])) > 0
    for rep in ("train", "same_donor", "new_donor"):
        assert np.array_equal(q10["observations"][rep]["base_uniform"], q11["observations"][rep]["base_uniform"])
        assert np.array_equal(q10["observations"][rep]["base_normal"], q11["observations"][rep]["base_normal"])
    assert not np.array_equal(q10["observations"]["train"]["eta_detection"], q11["observations"]["train"]["eta_detection"])


def test_complete_assembly_is_deterministic_and_in_memory_only(tmp_path: Path):
    design = _design()
    amendment = G.load_pairing_amendment(ROOT)
    a = _assemble("Q03_WEAK_SOURCE", design, amendment)
    b = _assemble("Q03_WEAK_SOURCE", design, amendment)
    assert G.scientific_truth_sha(a) == G.scientific_truth_sha(b)
    assert list(tmp_path.iterdir()) == []


def test_all_twelve_worlds_assemble_in_memory_with_44_genes_and_three_replicates():
    design = _design()
    amendment = G.load_pairing_amendment(ROOT)
    seen = []
    for world in PAYLOAD["worlds"]["world_list"]:
        pkg = A.assemble_world_in_memory(
            PAYLOAD, CAL, copy.deepcopy(world), design,
            source_code_map=SOURCE_MAP, amendment=amendment,
        )
        seen.append(pkg["world_name"])
        assert pkg["support"].shape == (len(design["src"]), 44)
        assert set(pkg["observations"]) == {"train", "same_donor", "new_donor"}
        assert pkg["qualification_fits_run"] == 0
        assert pkg["benchmark_run"] is False
        assert pkg["training_authorized"] is False
        _assert_observation_package(pkg)
    assert seen == [w["name"] for w in PAYLOAD["worlds"]["world_list"]]
