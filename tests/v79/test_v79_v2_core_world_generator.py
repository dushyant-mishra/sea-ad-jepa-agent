from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import generate_v79_v2_core_worlds as G  # noqa: E402

FINAL = ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
FINAL_SHA = "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"  # canonical Contract V2 (rebind 6115340528)
PAYLOAD = ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json"
PAYLOAD_SHA = "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3"


def _fixture_design() -> dict[str, np.ndarray]:
    src = np.repeat(np.arange(3), 8)
    donor = np.repeat(np.arange(6), 4)
    cls = np.tile(np.arange(3), 8)
    op = src * 2 + (donor % 2)
    loglib = np.linspace(-1.0, 1.0, len(src))
    return {"src": src.astype(np.int64), "donor": donor.astype(np.int64),
            "cls": cls.astype(np.int64), "op": op.astype(np.int64),
            "log_lib": loglib.astype(np.float64)}


def _support_design() -> dict[str, np.ndarray]:
    # Source 0/1/2 have 24/7/11 matrix levels respectively, matching S174 support geometry.
    src = np.concatenate([np.full(24, 0), np.full(7, 1), np.full(11, 2)]).astype(np.int64)
    op = np.arange(42, dtype=np.int64)
    donor = np.arange(42, dtype=np.int64)
    cls = np.arange(42, dtype=np.int64) % 3
    loglib = np.linspace(-1.0, 1.0, 42)
    return {"src": src, "op": op, "donor": donor, "cls": cls, "log_lib": loglib}


def _payload() -> dict:
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def _mini_payload() -> dict:
    # Keep the authoritative contract G=44 untouched. Toy tests that need six genes
    # pass genes=6 explicitly; mutating genes_per_world would incorrectly invoke the
    # full frozen five-gene structural-support composition on the tiny fixture.
    return _payload()


def _truth_fixture(genes: int = 6, donors: int = 4) -> dict:
    z = np.arange(donors * genes, dtype=float).reshape(donors, genes)
    z = (z - z.mean(0, keepdims=True)) / np.maximum(z.std(0, keepdims=True), 1e-9)
    return {
        "detection": {
            "prevalence": np.linspace(0.1, 0.8, genes),
            "depth1": np.linspace(0.5, 1.0, genes),
            "depth2": np.linspace(0.05, 0.2, genes),
            "class_contrasts": np.tile(np.array([[0.2, -0.3]]), (genes, 1)),
            "source_contrasts": np.tile(np.array([[0.4, -0.5]]), (genes, 1)),
            "donor_sd": np.linspace(0.3, 0.6, genes),
            "donor_raw_centered": z.copy(),
            "donor_effects": z * np.linspace(0.3, 0.6, genes),
        },
        "positive": {
            "intercept": np.linspace(0.2, 0.8, genes),
            "depth1": np.linspace(0.1, 0.5, genes),
            "depth2": np.linspace(0.01, 0.08, genes),
            "class_contrasts": np.tile(np.array([[0.1, -0.15]]), (genes, 1)),
            "source_contrasts": np.tile(np.array([[0.08, -0.09]]), (genes, 1)),
            "donor_sd": np.linspace(0.1, 0.2, genes),
            "donor_raw_centered": z.copy(),
            "donor_effects": z * np.linspace(0.1, 0.2, genes),
            "sigma": np.linspace(0.3, 0.6, genes),
        },
    }


def test_realization_requires_separate_authorization(tmp_path: Path):
    with pytest.raises(SystemExit):
        G.realize_worlds(_mini_payload(), _fixture_design(), tmp_path, authorization=None)


def test_seed_is_keyed_by_scientific_identity_not_file_layout():
    a = G.seed_for(world_index=3, gene_index=2, stream=17, root=31000000)
    b = G.seed_for(world_index=3, gene_index=2, stream=17, root=31000000)
    c = G.seed_for(world_index=3, gene_index=3, stream=17, root=31000000)
    assert a == b
    assert a != c


def test_q00_q09_share_base_design_and_q10_q11_share_s174_design():
    payload = _mini_payload()
    base = _fixture_design()
    s174 = {k: v[::-1].copy() for k, v in base.items()}
    designs = G.build_designs(payload, base_design=base, s174_design=s174)
    base_hashes = {G.array_bundle_sha(designs[f"Q{i:02d}_{name}"]) for i, name in [
        (0, "BASELINE"), (1, "WEAK_DONOR"), (2, "STRONG_DONOR"), (3, "WEAK_SOURCE"),
        (4, "SOURCE_ABSENT"), (5, "CLASS_ABSENT"), (6, "QUADRATIC_DEPTH_ABSENT"),
        (7, "DONOR_ABSENT"), (8, "SPARSE_DETECTION"), (9, "POSITIVE_TAIL")
    ]}
    assert len(base_hashes) == 1
    assert G.array_bundle_sha(designs["Q10_S174_DESIGN_IMBALANCE"]) == G.array_bundle_sha(designs["Q11_OMITTED_OPERATOR"])


def test_structural_support_truth_and_poison_are_separate():
    payload = _mini_payload()
    design = _fixture_design()
    support = G.build_structural_support(payload, design, world_index=0, genes=6)
    assert support.shape == (len(design["src"]), 6)
    assert support.dtype == np.bool_
    counts = np.ones(support.shape, dtype=np.int64)
    poisoned_a = G.apply_poison(counts, support, poison=-1)
    poisoned_b = G.apply_poison(counts, support, poison=2_147_483_647)
    assert np.array_equal(poisoned_a[support], poisoned_b[support])
    assert np.all(poisoned_a[~support] == -1)
    assert np.all(poisoned_b[~support] == 2_147_483_647)


def test_manifest_binds_final_contract_payload_truth_and_zero_fits(tmp_path: Path):
    truth = {"world": "Q00_BASELINE", "opaque_id": hashlib.sha256(b"V2CORE|Q00_BASELINE").hexdigest()[:12]}
    manifest = G.build_manifest(world_name="Q00_BASELINE", world_index=0, truth=truth,
        final_contract_sha=FINAL_SHA, payload_sha=PAYLOAD_SHA,
        generated_files={"truth.json": "abc", "world.npz": "def"})
    assert manifest["final_contract_sha256"] == FINAL_SHA
    assert manifest["qualification_payload_sha256"] == PAYLOAD_SHA
    assert manifest["qualification_fits_run"] == 0
    assert manifest["benchmark_run"] is False
    assert manifest["opaque_world_id"] == hashlib.sha256(b"V2CORE|Q00_BASELINE").hexdigest()[:12]


def test_pairing_amendment_is_required_and_controller_bound():
    amendment = G.load_pairing_amendment(ROOT)
    assert amendment["schema"] == "V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1"
    assert amendment["controller_comment"] == 6114906562
    assert amendment["final_contract_sha256"] == FINAL_SHA
    assert amendment["qualification_payload_sha256"] == PAYLOAD_SHA
    assert amendment["worlds_generated_at_freeze"] == 0
    assert amendment["qualification_fits_at_freeze"] == 0


def test_q11_reuses_q10_seed_identity_except_operator_offset_streams():
    amendment = G.load_pairing_amendment(ROOT)
    for stream in [1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 24]:
        assert G.effective_seed_world_index(11, stream, amendment) == 10
    assert G.effective_seed_world_index(11, 22, amendment) == 11
    assert G.effective_seed_world_index(11, 23, amendment) == 11


def test_q10_q11_pairing_validator_allows_only_operator_fields_to_differ():
    amendment = G.load_pairing_amendment(ROOT)
    base = {"design_sha": "d", "support_sha": "s", "core_parameters_sha": "p",
        "donor_effects_sha": "u", "factor_loading_sha": "f", "base_detection_noise_sha": "nd",
        "base_positive_noise_sha": "np", "operator_offsets_detection_sha": None,
        "operator_offsets_positive_sha": None}
    q11 = dict(base)
    q11["operator_offsets_detection_sha"] = "od"
    q11["operator_offsets_positive_sha"] = "op"
    G.validate_q10_q11_pairing(base, q11, amendment)
    bad = dict(q11); bad["donor_effects_sha"] = "changed"
    with pytest.raises(SystemExit): G.validate_q10_q11_pairing(base, bad, amendment)


def test_full_G_structural_support_has_frozen_1_3_1_composition():
    payload = _payload(); design = _support_design()
    support = G.build_structural_support(payload, design, world_index=0, genes=44)
    affected = np.where((~support).any(0))[0]
    assert len(affected) == 5
    single_source, one_absent, partial = 0, 0, 0
    for g in affected:
        measured_by_source = [bool(support[design["src"] == s, g].any()) for s in range(3)]
        full_by_source = [bool(support[design["src"] == s, g].all()) for s in range(3)]
        if sum(measured_by_source) == 1:
            single_source += 1
        elif sum(full_by_source) == 2 and sum(measured_by_source) == 2:
            one_absent += 1
        else:
            partial += 1
            assert full_by_source[0] and full_by_source[2]
            assert int((~support[design["src"] == 1, g]).sum()) == 3
    assert (single_source, one_absent, partial) == (1, 3, 1)


def test_world_modifications_match_frozen_semantics():
    payload = _payload(); base = _truth_fixture()
    by_name = {w["name"]: w for w in payload["worlds"]["world_list"]}
    q1 = G.apply_world_modifications(base, by_name["Q01_WEAK_DONOR"], payload)
    q2 = G.apply_world_modifications(base, by_name["Q02_STRONG_DONOR"], payload)
    q3 = G.apply_world_modifications(base, by_name["Q03_WEAK_SOURCE"], payload)
    q4 = G.apply_world_modifications(base, by_name["Q04_SOURCE_ABSENT"], payload)
    q5 = G.apply_world_modifications(base, by_name["Q05_CLASS_ABSENT"], payload)
    q6 = G.apply_world_modifications(base, by_name["Q06_QUADRATIC_DEPTH_ABSENT"], payload)
    q7 = G.apply_world_modifications(base, by_name["Q07_DONOR_ABSENT"], payload)
    q8 = G.apply_world_modifications(base, by_name["Q08_SPARSE_DETECTION"], payload)
    q9 = G.apply_world_modifications(base, by_name["Q09_POSITIVE_TAIL"], payload)
    fixed = payload["worlds"]["planting_magnitudes"]["fixed_magnitudes"]
    assert np.all(q1["detection"]["donor_sd"] == pytest.approx(fixed["weak_donor_sd"]["detection"]))
    assert np.all(q1["positive"]["donor_sd"] == pytest.approx(fixed["weak_donor_sd"]["positive"]))
    assert np.all(q2["detection"]["donor_sd"] == pytest.approx(fixed["strong_donor_sd"]["detection"]))
    assert np.all(np.abs(q3["detection"]["source_contrasts"]) == pytest.approx(fixed["weak_abs_source"]["detection"]))
    assert np.count_nonzero(q4["detection"]["source_contrasts"]) == 0
    assert np.count_nonzero(q4["positive"]["source_contrasts"]) == 0
    assert np.count_nonzero(q5["detection"]["class_contrasts"]) == 0
    assert np.count_nonzero(q6["detection"]["depth2"]) == 0
    assert np.count_nonzero(q6["positive"]["depth2"]) == 0
    assert np.count_nonzero(q7["detection"]["donor_sd"]) == 0
    assert np.count_nonzero(q7["positive"]["donor_effects"]) == 0
    assert np.all((q8["detection"]["prevalence"] >= 0.005) & (q8["detection"]["prevalence"] <= 0.05))
    assert np.all(q9["positive"]["sigma"] == pytest.approx(fixed["tail_sigma"]))


def test_operator_offsets_are_deterministic_scaled_and_centered_within_source():
    payload = _payload(); amendment = G.load_pairing_amendment(ROOT); design = _fixture_design()
    for part in ("detection", "positive"):
        x1 = G.generate_operator_offsets(design, donor_sd=0.8, world_index=11, gene_index=3,
                                         part=part, payload=payload, amendment=amendment)
        x2 = G.generate_operator_offsets(design, donor_sd=0.8, world_index=11, gene_index=3,
                                         part=part, payload=payload, amendment=amendment)
        assert np.array_equal(x1, x2)
        for s in np.unique(design["src"]):
            ops = np.unique(design["op"][design["src"] == s])
            assert float(np.mean(x1[ops])) == pytest.approx(0.0, abs=1e-12)
        assert np.max(np.abs(x1)) > 0
