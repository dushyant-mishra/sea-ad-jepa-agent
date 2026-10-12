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


def _fixture(tmp_path: Path):
    root = tmp_path / "realized_worlds_v1"
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
    root_manifest = {
        "schema": "V79_V2_CORE_WORLD_SET_MANIFEST_V1",
        "mode": "QUALIFICATION_TRUTH_FREEZE",
        "world_count": 1,
        "blinded_fit_root": "blinded_fit_inputs",
        "blinded_fit_index_path": f"blinded_fit_inputs/{F.FIT_INDEX_NAME}",
        "blinded_fit_index_sha256": index_sha,
        "controller_truth_root": "controller_truth",
        "final_contract_sha256": F.FINAL_CONTRACT_SHA256,
        "benchmark_run": False,
        "qualification_fits_run": 0,
        "training_authorized": False,
    }
    _write_json(root / F.ROOT_MANIFEST_NAME, root_manifest)
    return root, oid


def test_loader_exposes_only_blinded_surface(tmp_path):
    root, oid = _fixture(tmp_path)
    idx = F.load_blinded_index(root, expected_root_manifest_sha=None, expected_index_sha=None)
    assert idx.opaque_world_ids == (oid,)
    world = F.load_blinded_world(root, oid)
    assert set(world.design) == {"src", "donor", "cls", "log_lib"}
    assert set(world.observations) == {"train", "same_donor", "new_donor"}
    assert world.support.shape == (3, 2)
    forbidden = {"op", "operator", "matrix", "truth", "seed_root", "world_name", "world_index"}
    assert forbidden.isdisjoint(world.__dict__)


def test_loader_refuses_q_label_and_nonopaque_identifier(tmp_path):
    root, _ = _fixture(tmp_path)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_world(root, "Q00_BASELINE")
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_world(root, "../controller_truth")


def test_loader_refuses_hash_tamper_before_return(tmp_path):
    root, oid = _fixture(tmp_path)
    p = root / "blinded_fit_inputs" / oid / "design/src.npy"
    raw = bytearray(p.read_bytes()); raw[-1] ^= 1; p.write_bytes(bytes(raw))
    with pytest.raises(F.FitSurfaceRefused, match="hash"):
        F.load_blinded_world(root, oid)


def test_loader_refuses_unknown_manifest_output(tmp_path):
    root, oid = _fixture(tmp_path)
    mp = root / "blinded_fit_inputs" / oid / "manifest.json"
    m = json.loads(mp.read_text())
    m["generated_outputs"]["design/op.npy"] = "0" * 64
    _write_json(mp, m)
    ip = root / "blinded_fit_inputs" / F.FIT_INDEX_NAME
    i = json.loads(ip.read_text())
    i["worlds"][0]["manifest_sha256"] = hashlib.sha256(mp.read_bytes()).hexdigest()
    new_i_sha = _write_json(ip, i)
    rp = root / F.ROOT_MANIFEST_NAME
    r = json.loads(rp.read_text()); r["blinded_fit_index_sha256"] = new_i_sha; _write_json(rp, r)
    with pytest.raises(F.FitSurfaceRefused, match="forbidden|unexpected"):
        F.load_blinded_world(root, oid)


def test_loader_refuses_object_dtype(tmp_path):
    root, oid = _fixture(tmp_path)
    p = root / "blinded_fit_inputs" / oid / "design/src.npy"
    with p.open("wb") as f:
        np.save(f, np.asarray([{"x": 1}], dtype=object), allow_pickle=True)
    mp = root / "blinded_fit_inputs" / oid / "manifest.json"
    m = json.loads(mp.read_text()); m["generated_outputs"]["design/src.npy"] = hashlib.sha256(p.read_bytes()).hexdigest()
    _write_json(mp, m)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_world(root, oid)


def test_gene_inputs_apply_structural_support_and_positive_detection(tmp_path):
    root, oid = _fixture(tmp_path)
    w = F.load_blinded_world(root, oid)
    g0 = F.load_gene_inputs(w, gene_index=0, replicate="train")
    assert g0.detection_mask.tolist() == [True, True, True]
    assert g0.positive_mask.tolist() == [False, True, True]
    g1 = F.load_gene_inputs(w, gene_index=1, replicate="train")
    assert g1.detection_mask.tolist() == [True, False, True]
    assert g1.positive_mask.tolist() == [True, False, True]


def test_index_can_pin_realization_hashes(tmp_path):
    root, _ = _fixture(tmp_path)
    rsha = hashlib.sha256((root / F.ROOT_MANIFEST_NAME).read_bytes()).hexdigest()
    isha = hashlib.sha256((root / "blinded_fit_inputs" / F.FIT_INDEX_NAME).read_bytes()).hexdigest()
    F.load_blinded_index(root, expected_root_manifest_sha=rsha, expected_index_sha=isha)
    with pytest.raises(F.FitSurfaceRefused):
        F.load_blinded_index(root, expected_root_manifest_sha="0" * 64, expected_index_sha=isha)
