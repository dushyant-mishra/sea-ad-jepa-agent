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
FINAL_SHA = "8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d"
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


def _mini_payload() -> dict:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    payload["worlds"]["genes_per_world"] = 6
    return payload


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
    assert G.scientific_truth_sha({"support": support, "counts_measured": counts[support]}) == G.scientific_truth_sha({"support": support, "counts_measured": counts[support]})


def test_manifest_binds_final_contract_payload_truth_and_zero_fits(tmp_path: Path):
    truth = {"world": "Q00_BASELINE", "opaque_id": hashlib.sha256(b"V2CORE|Q00_BASELINE").hexdigest()[:12]}
    manifest = G.build_manifest(
        world_name="Q00_BASELINE", world_index=0, truth=truth,
        final_contract_sha=FINAL_SHA, payload_sha=PAYLOAD_SHA,
        generated_files={"truth.json": "abc", "world.npz": "def"},
    )
    assert manifest["final_contract_sha256"] == FINAL_SHA
    assert manifest["qualification_payload_sha256"] == PAYLOAD_SHA
    assert manifest["qualification_fits_run"] == 0
    assert manifest["benchmark_run"] is False
    assert manifest["opaque_world_id"] == hashlib.sha256(b"V2CORE|Q00_BASELINE").hexdigest()[:12]
    assert manifest["generated_outputs"] == {"truth.json": "abc", "world.npz": "def"}


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
    assert G.effective_seed_world_index(10, 22, amendment) == 10


def test_q10_q11_pairing_validator_allows_only_operator_fields_to_differ():
    amendment = G.load_pairing_amendment(ROOT)
    base = {
        "design_sha": "d",
        "support_sha": "s",
        "core_parameters_sha": "p",
        "donor_effects_sha": "u",
        "factor_loading_sha": "f",
        "base_detection_noise_sha": "nd",
        "base_positive_noise_sha": "np",
        "operator_offsets_detection_sha": None,
        "operator_offsets_positive_sha": None,
    }
    q11 = dict(base)
    q11["operator_offsets_detection_sha"] = "od"
    q11["operator_offsets_positive_sha"] = "op"
    G.validate_q10_q11_pairing(base, q11, amendment)
    bad = dict(q11)
    bad["donor_effects_sha"] = "changed"
    with pytest.raises(SystemExit):
        G.validate_q10_q11_pairing(base, bad, amendment)
