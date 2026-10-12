from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import v79_v2_core_fit_surface as F  # noqa: E402


def _jbytes(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _write_json(path: Path, obj: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _jbytes(obj)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _write_npy(path: Path, value) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        np.save(f, np.asarray(value), allow_pickle=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path, *, mode="ENGINEERING_TEST_ONLY"):
    root = tmp_path / ("worlds_eng" if mode == "ENGINEERING_TEST_ONLY" else "realized_worlds_v1")
    oid = "0123456789ab"
    w = root / "blinded_fit_inputs" / oid
    outputs = {}
    outputs["design/src.npy"] = _write_npy(w / "design/src.npy", [0, 1, 2])
    outputs["design/donor.npy"] = _write_npy(w / "design/donor.npy", [0, 1, 2])
    outputs["design/cls.npy"] = _write_npy(w / "design/cls.npy", [0, 1, 2])
    outputs["design/log_lib.npy"] = _write_npy(w / "design/log_lib.npy", [1.0, 2.0, 3.0])
    outputs["support.npy"] = _write_npy(w / "support.npy", [[True, True], [True, False], [True, True]])
    for rep in ("train", "same_donor", "new_donor"):
        outputs[f"observations/{rep}/observed.npy"] = _write_npy(
            w / f"observations/{rep}/observed.npy", [[0.0, 2.0], [3.0, 0.0], [1.0, 4.0]])
        outputs[f"observations/{rep}/detected.npy"] = _write_npy(
            w / f"observations/{rep}/detected.npy", [[0, 1], [1, 0], [1, 1]])
    wm = {
        "schema": "V79_V2_CORE_BLINDED_WORLD_DATA_MANIFEST_V1",
        "opaque_world_id": oid,
        "final_contract_sha256": F.FINAL_CONTRACT_SHA256,
        "pairing_amendment_sha256": "a" * 64,
        "generator_bundle_sha256": "b" * 64,
        "generated_outputs": dict(sorted(outputs.items())),
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    wm_sha = _write_json(w / "manifest.json", wm)
    index = {
        "schema": "V79_V2_CORE_BLINDED_FIT_INDEX_V1",
        "final_contract_sha256": F.FINAL_CONTRACT_SHA256,
        "pairing_amendment_sha256": "a" * 64,
        "generator_bundle_sha256": "b" * 64,
        "world_count": 1,
        "worlds": [{"opaque_world_id": oid, "manifest_path": f"{oid}/manifest.json", "manifest_sha256": wm_sha}],
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    index_sha = _write_json(root / "blinded_fit_inputs" / F.FIT_INDEX_NAME, index)
    # Deliberately poison the controller root with identity/truth information. The fit loader may hash these bytes,
    # but must never JSON-decode or return them.
    root_manifest = {
        "schema": "V79_V2_CORE_WORLD_SET_MANIFEST_V1",
        "mode": mode,
        "seed_root": 123456,
        "world_count": 1,
        "worlds": [{"world_name": "Q00_BASELINE", "world_index": 0, "opaque_world_id": oid,
                    "truth_manifest_path": f"controller_truth/{oid}/manifest.json"}],
        "blinded_fit_root": "blinded_fit_inputs",
        "blinded_fit_index_path": f"blinded_fit_inputs/{F.FIT_INDEX_NAME}",
        "blinded_fit_index_sha256": index_sha,
        "controller_truth_root": "controller_truth",
        "final_contract_sha256": F.FINAL_CONTRACT_SHA256,
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    root_sha = _write_json(root / F.ROOT_MANIFEST_NAME, root_manifest)
    return root, oid, root_sha, index_sha


def _engineering_index(root, root_sha, index_sha):
    return F.load_blinded_index(root, expected_mode="ENGINEERING_TEST_ONLY",
                                expected_root_manifest_sha=root_sha, expected_index_sha=index_sha)


def test_loader_exposes_only_blinded_surface_and_never_parses_controller_root(tmp_path):
    root, oid, rsha, isha = _fixture(tmp_path)
    idx = _engineering_index(root, rsha, isha)
    assert idx.opaque_world_ids == (oid,)
    assert "root_manifest" not in idx.__dict__
    assert "Q00_BASELINE" not in json.dumps(idx.index)
    world = F.load_blinded_world(idx, oid)
    assert set(world.design) == {"src", "donor", "cls", "log_lib"}
    assert set(world.observations) == {"train", "same_donor", "new_donor"}
    assert world.support.shape == (3, 2)
    forbidden = {"op", "operator", "matrix", "truth", "seed_root", "world_name", "world_index", "package_root"}
    assert forbidden.isdisjoint(world.__dict__)


def test_qualification_mode_requires_exact_frozen_realization_hashes(tmp_path):
    root, _, rsha, isha = _fixture(tmp_path, mode="QUALIFICATION_TRUTH_FREEZE")
    with pytest.raises(F.FitSurfaceRefused, match="immutable realized"):
        F.load_blinded_index(root, expected_mode="QUALIFICATION_TRUTH_FREEZE",
                             expected_root_manifest_sha=rsha, expected_index_sha=isha)


def test_engineering_mode_refuses_qualification_authority_hashes(tmp_path):
    root, _, _, _ = _fixture(tmp_path)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_index(root, expected_mode="ENGINEERING_TEST_ONLY",
                             expected_root_manifest_sha=F.QUALIFICATION_ROOT_MANIFEST_SHA256,
                             expected_index_sha=F.QUALIFICATION_INDEX_SHA256)


def test_loader_refuses_q_label_nonopaque_and_unvalidated_world_load(tmp_path):
    root, _, rsha, isha = _fixture(tmp_path)
    idx = _engineering_index(root, rsha, isha)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_world(idx, "Q00_BASELINE")
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_world(idx, "../controller_truth")
    with pytest.raises(F.FitSurfaceRefused, match="BlindedIndex"):
        F.load_blinded_world(root, "0123456789ab")


def test_loader_refuses_hash_tamper_before_return(tmp_path):
    root, oid, rsha, isha = _fixture(tmp_path)
    idx = _engineering_index(root, rsha, isha)
    p = root / "blinded_fit_inputs" / oid / "design/src.npy"
    raw = bytearray(p.read_bytes()); raw[-1] ^= 1; p.write_bytes(bytes(raw))
    with pytest.raises(F.FitSurfaceRefused, match="hash"):
        F.load_blinded_world(idx, oid)


def test_loader_refuses_unknown_manifest_output(tmp_path):
    root, oid, rsha, _ = _fixture(tmp_path)
    mp = root / "blinded_fit_inputs" / oid / "manifest.json"
    m = json.loads(mp.read_text())
    m["generated_outputs"]["design/op.npy"] = "0" * 64
    _write_json(mp, m)
    ip = root / "blinded_fit_inputs" / F.FIT_INDEX_NAME
    i = json.loads(ip.read_text())
    i["worlds"][0]["manifest_sha256"] = hashlib.sha256(mp.read_bytes()).hexdigest()
    new_i_sha = _write_json(ip, i)
    idx = _engineering_index(root, rsha, new_i_sha)
    with pytest.raises(F.FitSurfaceRefused, match="forbidden|unexpected"):
        F.load_blinded_world(idx, oid)


def test_loader_refuses_object_dtype(tmp_path):
    root, oid, rsha, _ = _fixture(tmp_path)
    p = root / "blinded_fit_inputs" / oid / "design/src.npy"
    with p.open("wb") as f:
        np.save(f, np.asarray([{"x": 1}], dtype=object), allow_pickle=True)
    mp = root / "blinded_fit_inputs" / oid / "manifest.json"
    m = json.loads(mp.read_text()); m["generated_outputs"]["design/src.npy"] = hashlib.sha256(p.read_bytes()).hexdigest()
    new_m_sha = _write_json(mp, m)
    ip = root / "blinded_fit_inputs" / F.FIT_INDEX_NAME
    i = json.loads(ip.read_text()); i["worlds"][0]["manifest_sha256"] = new_m_sha
    new_i_sha = _write_json(ip, i)
    idx = _engineering_index(root, rsha, new_i_sha)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_world(idx, oid)


def test_gene_inputs_apply_structural_support_and_positive_detection(tmp_path):
    root, oid, rsha, isha = _fixture(tmp_path)
    w = F.load_blinded_world(_engineering_index(root, rsha, isha), oid)
    g0 = F.load_gene_inputs(w, gene_index=0, replicate="train")
    assert g0.detection_mask.tolist() == [True, True, True]
    assert g0.positive_mask.tolist() == [False, True, True]
    g1 = F.load_gene_inputs(w, gene_index=1, replicate="train")
    assert g1.detection_mask.tolist() == [True, False, True]
    assert g1.positive_mask.tolist() == [True, False, True]


def test_index_requires_both_authority_hashes(tmp_path):
    root, _, rsha, isha = _fixture(tmp_path)
    F.load_blinded_index(root, expected_mode="ENGINEERING_TEST_ONLY",
                         expected_root_manifest_sha=rsha, expected_index_sha=isha)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_index(root, expected_mode="ENGINEERING_TEST_ONLY",
                             expected_root_manifest_sha=None, expected_index_sha=isha)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_index(root, expected_mode="ENGINEERING_TEST_ONLY",
                             expected_root_manifest_sha=rsha, expected_index_sha=None)
