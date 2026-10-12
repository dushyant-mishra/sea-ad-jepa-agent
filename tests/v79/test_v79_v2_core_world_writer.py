"""RED/GREEN tests for deterministic physical world-package writing.

All successful write tests use engineering seed 4242 only. The frozen
qualification seed (31000000) is exercised only through fail-closed paths.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import generate_v79_v2_core_worlds as G  # noqa: E402

try:
    import v79_v2_core_world_writer as W  # type: ignore  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover
    W = None

CAL_PATH = ROOT / "results/v79/development/v2_core_planting_calibration/V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json"
CAL = json.loads(CAL_PATH.read_text(encoding="utf-8"))
TEST_ROOT = 4242
QUAL_ROOT = 31000000
ENV_LOCK_SHA = "5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782"
CAL_SHA = "49379ee09fcf7496919e570f83710ee772ca407ca0d20268a9af1f4e132f533c"


def _writer():
    assert W is not None, "world writer module is not implemented"
    return W


@pytest.fixture(scope="module")
def launch():
    return G.load_launch_contract(ROOT)


@pytest.fixture(scope="module")
def amendment():
    return G.load_pairing_amendment(ROOT)


@pytest.fixture(scope="module")
def engineering_payload(launch):
    _, payload = launch
    p = copy.deepcopy(payload)
    p["seeds"]["root"] = TEST_ROOT
    return p


@pytest.fixture(scope="module")
def qualification_payload(launch):
    _, payload = launch
    assert int(payload["seeds"]["root"]) == QUAL_ROOT
    return payload


@pytest.fixture(scope="module")
def engineering_designs(engineering_payload):
    return G.build_world_designs(ROOT, engineering_payload)


def _base_auth(w):
    return {
        "schema": G.REALIZATION_AUTH_SCHEMA,
        "final_contract_sha256": G.FINAL_CONTRACT_SHA256,
        "pairing_amendment_sha256": G.PAIRING_AMENDMENT_SHA256,
        "world_generation_authorized": True,
        "qualification_fitting_authorized": False,
        "generator_code_head": "f" * 40,
        "generator_green_ci": {"passed": True},
        "generator_bundle_sha256": w.generator_bundle_sha256(ROOT),
        "environment_lock_sha256": ENV_LOCK_SHA,
        "execution_platform": "WINDOWS_LOCKED_QUALIFICATION_ENVIRONMENT",
    }


def test_generator_bundle_hash_is_explicit_and_stable():
    w = _writer()
    a = w.generator_bundle_sha256(ROOT)
    b = w.generator_bundle_sha256(ROOT)
    assert a == b
    assert isinstance(a, str) and len(a) == 64
    print(f"GENERATOR_BUNDLE_SHA256={a}")


def test_engineering_world_set_roundtrip_is_byte_deterministic(tmp_path, engineering_payload, engineering_designs, amendment):
    w = _writer(); a = tmp_path / "a"; b = tmp_path / "b"
    ma = w.write_engineering_world_set(root=ROOT, payload=engineering_payload, cal=CAL,
        designs=engineering_designs, amendment=amendment, out_dir=a)
    mb = w.write_engineering_world_set(root=ROOT, payload=engineering_payload, cal=CAL,
        designs=engineering_designs, amendment=amendment, out_dir=b)
    assert ma["schema"] == "V79_V2_CORE_WORLD_SET_MANIFEST_V1"
    assert ma["mode"] == "ENGINEERING_TEST_ONLY"
    assert ma["seed_root"] == TEST_ROOT
    assert ma["world_count"] == 12
    assert ma["qualification_fits_run"] == 0
    assert ma["benchmark_run"] is False
    assert ma["training_authorized"] is False
    assert ma["final_contract_sha256"] == G.FINAL_CONTRACT_SHA256
    assert ma["pairing_amendment_sha256"] == G.PAIRING_AMENDMENT_SHA256
    assert len(ma["worlds"]) == 12
    assert ma == mb
    digest_a = w.directory_digest(a); digest_b = w.directory_digest(b)
    assert digest_a == digest_b
    print(f"ENGINEERING_WORLD_SET_DIGEST={digest_a}")
    assert w.verify_world_set(a) == ma
    assert w.verify_world_set(b) == mb


def test_world_manifests_bind_data_support_truth_and_three_replicates(tmp_path, engineering_payload, engineering_designs, amendment):
    w = _writer(); out = tmp_path / "set"
    root_manifest = w.write_engineering_world_set(root=ROOT, payload=engineering_payload, cal=CAL,
        designs=engineering_designs, amendment=amendment, out_dir=out)
    for rec in root_manifest["worlds"]:
        wm = json.loads((out / rec["manifest_path"]).read_text(encoding="utf-8"))
        assert wm["qualification_fits_run"] == 0
        assert wm["benchmark_run"] is False
        assert wm["training_authorized"] is False
        names = set(wm["generated_outputs"])
        assert "support.npy" in names
        assert "observations/train/observed.npy" in names
        assert "observations/same_donor/observed.npy" in names
        assert "observations/new_donor/observed.npy" in names
        assert "truth/detection/intercept.npy" in names
        assert "truth/positive/donor_effects.npy" in names
        assert "truth/new_donor/detection/donor_effects.npy" in names


def test_tamper_in_bound_world_file_fails_closed(tmp_path, engineering_payload, engineering_designs, amendment):
    w = _writer(); out = tmp_path / "set"
    root_manifest = w.write_engineering_world_set(root=ROOT, payload=engineering_payload, cal=CAL,
        designs=engineering_designs, amendment=amendment, out_dir=out)
    rec = root_manifest["worlds"][0]
    wm_path = out / rec["manifest_path"]
    wm = json.loads(wm_path.read_text(encoding="utf-8"))
    target = wm_path.parent / sorted(wm["generated_outputs"])[0]
    target.write_bytes(target.read_bytes() + b"tamper")
    with pytest.raises(SystemExit):
        w.verify_world_set(out)


def test_engineering_writer_refuses_frozen_qualification_seed(tmp_path, qualification_payload, amendment):
    w = _writer(); designs = G.build_world_designs(ROOT, qualification_payload)
    with pytest.raises(SystemExit):
        w.write_engineering_world_set(root=ROOT, payload=qualification_payload, cal=CAL, designs=designs,
            amendment=amendment, out_dir=tmp_path / "forbidden")


def test_qualification_loader_owns_all_frozen_scientific_inputs(qualification_payload, amendment):
    w = _writer()
    contract, payload, cal, designs, loaded_amendment = w.load_frozen_qualification_inputs(ROOT)
    assert payload == qualification_payload
    assert int(payload["seeds"]["root"]) == QUAL_ROOT
    assert loaded_amendment == amendment
    assert set(designs) == {x["name"] for x in payload["worlds"]["world_list"]}
    assert hashlib.sha256(CAL_PATH.read_bytes()).hexdigest() == CAL_SHA
    assert cal == CAL
    assert contract["inputs"]["planting_calibration_masked"]["sha256"] == CAL_SHA
    params = set(inspect.signature(w.realize_qualification_worlds).parameters)
    assert params == {"root", "out_dir", "authorization"}


def test_qualification_authorization_binds_windows_environment_lock():
    w = _writer(); auth = _base_auth(w)
    assert w.validate_qualification_authorization(auth, root=ROOT, runtime_platform="Windows") == auth
    with pytest.raises(SystemExit):
        w.validate_qualification_authorization(auth, root=ROOT, runtime_platform="Linux")
    bad = dict(auth); bad["environment_lock_sha256"] = "0" * 64
    with pytest.raises(SystemExit):
        w.validate_qualification_authorization(bad, root=ROOT, runtime_platform="Windows")
    bad = dict(auth); bad["execution_platform"] = "LINUX"
    with pytest.raises(SystemExit):
        w.validate_qualification_authorization(bad, root=ROOT, runtime_platform="Windows")


def test_qualification_writer_requires_bundle_bound_authorization(tmp_path):
    w = _writer()
    with pytest.raises(SystemExit):
        w.realize_qualification_worlds(root=ROOT, out_dir=tmp_path / "none", authorization=None)
    bad = _base_auth(w); bad["generator_bundle_sha256"] = "0" * 64
    with pytest.raises(SystemExit):
        w.realize_qualification_worlds(root=ROOT, out_dir=tmp_path / "bad", authorization=bad)
    assert not (tmp_path / "bad").exists()
