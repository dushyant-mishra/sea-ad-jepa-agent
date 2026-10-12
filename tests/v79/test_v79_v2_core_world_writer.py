"""RED/GREEN tests for deterministic, blinded physical world-package writing.

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
    a = w.generator_bundle_sha256(ROOT); b = w.generator_bundle_sha256(ROOT)
    assert a == b and isinstance(a, str) and len(a) == 64
    print(f"GENERATOR_BUNDLE_SHA256={a}")


def _write_eng(w, tmp_path, payload, designs, amendment, name="set"):
    return w.write_engineering_world_set(root=ROOT, payload=payload, cal=CAL,
        designs=designs, amendment=amendment, out_dir=tmp_path / name)


def test_engineering_world_set_roundtrip_is_byte_deterministic(tmp_path, engineering_payload, engineering_designs, amendment):
    w = _writer()
    ma = _write_eng(w, tmp_path, engineering_payload, engineering_designs, amendment, "a")
    mb = _write_eng(w, tmp_path, engineering_payload, engineering_designs, amendment, "b")
    assert ma["schema"] == "V79_V2_CORE_WORLD_SET_MANIFEST_V1"
    assert ma["mode"] == "ENGINEERING_TEST_ONLY" and ma["seed_root"] == TEST_ROOT
    assert ma["world_count"] == 12 and ma["qualification_fits_run"] == 0
    assert ma["benchmark_run"] is False and ma["training_authorized"] is False
    assert ma["final_contract_sha256"] == G.FINAL_CONTRACT_SHA256
    assert ma["pairing_amendment_sha256"] == G.PAIRING_AMENDMENT_SHA256
    assert len(ma["worlds"]) == 12 and ma == mb
    da = w.directory_digest(tmp_path / "a"); db = w.directory_digest(tmp_path / "b")
    assert da == db
    print(f"ENGINEERING_WORLD_SET_DIGEST={da}")
    assert w.verify_world_set(tmp_path / "a") == ma
    assert w.verify_world_set(tmp_path / "b") == mb


def test_blinded_fit_package_has_no_truth_world_names_operator_or_seed(tmp_path, engineering_payload, engineering_designs, amendment):
    w = _writer(); out = tmp_path / "set"
    root_manifest = _write_eng(w, tmp_path, engineering_payload, engineering_designs, amendment)
    fit_index_path = out / root_manifest["blinded_fit_index_path"]
    fit_index_raw = fit_index_path.read_text(encoding="utf-8")
    fit_index = json.loads(fit_index_raw)
    assert fit_index["schema"] == "V79_V2_CORE_BLINDED_FIT_INDEX_V1"
    assert len(fit_index["worlds"]) == 12
    for q in [f"Q{i:02d}" for i in range(12)]:
        assert q not in fit_index_raw

    for rec in root_manifest["worlds"]:
        opaque = rec["opaque_world_id"]
        assert rec["world_name"].startswith("Q")
        assert opaque in rec["fit_manifest_path"]
        assert rec["world_name"] not in rec["fit_manifest_path"]
        fm_path = out / rec["fit_manifest_path"]
        fm_raw = fm_path.read_text(encoding="utf-8")
        fm = json.loads(fm_raw)
        assert fm["opaque_world_id"] == opaque
        for forbidden in ("world_name", "world_index", "seed_root", "truth", "operator", "op.npy"):
            assert forbidden not in fm_raw
        names = set(fm["generated_outputs"])
        assert names >= {
            "design/src.npy", "design/donor.npy", "design/cls.npy", "design/log_lib.npy",
            "support.npy", "observations/train/observed.npy",
            "observations/same_donor/observed.npy", "observations/new_donor/observed.npy"
        }
        assert "design/op.npy" not in names
        assert not any(x.startswith("truth/") for x in names)

        tm = json.loads((out / rec["truth_manifest_path"]).read_text(encoding="utf-8"))
        assert tm["world_name"] == rec["world_name"]
        assert tm["world_index"] == rec["world_index"]
        assert tm["opaque_world_id"] == opaque
        truth_names = set(tm["generated_outputs"])
        assert "design/op.npy" in truth_names
        assert "truth/detection/intercept.npy" in truth_names
        assert "truth/positive/donor_effects.npy" in truth_names
        assert "truth/new_donor/detection/donor_effects.npy" in truth_names

    # The entire blinded root must have opaque directory names and no controller truth files.
    fit_root = out / root_manifest["blinded_fit_root"]
    opaque_ids = {r["opaque_world_id"] for r in root_manifest["worlds"]}
    assert {p.name for p in fit_root.iterdir() if p.is_dir()} == opaque_ids
    assert not any("truth" in str(p.relative_to(fit_root)).lower() for p in fit_root.rglob("*"))


def test_tamper_in_bound_fit_or_truth_file_fails_closed(tmp_path, engineering_payload, engineering_designs, amendment):
    w = _writer(); out = tmp_path / "set"
    root_manifest = _write_eng(w, tmp_path, engineering_payload, engineering_designs, amendment)
    rec = root_manifest["worlds"][0]
    fm = json.loads((out / rec["fit_manifest_path"]).read_text(encoding="utf-8"))
    fit_target = (out / rec["fit_manifest_path"]).parent / sorted(fm["generated_outputs"])[0]
    fit_target.write_bytes(fit_target.read_bytes() + b"tamper")
    with pytest.raises(SystemExit):
        w.verify_world_set(out)

    out2 = tmp_path / "set2"
    root_manifest = _write_eng(w, tmp_path, engineering_payload, engineering_designs, amendment, "set2")
    rec = root_manifest["worlds"][0]
    tm = json.loads((out2 / rec["truth_manifest_path"]).read_text(encoding="utf-8"))
    truth_target = (out2 / rec["truth_manifest_path"]).parent / sorted(tm["generated_outputs"])[0]
    truth_target.write_bytes(truth_target.read_bytes() + b"tamper")
    with pytest.raises(SystemExit):
        w.verify_world_set(out2)


def test_engineering_writer_refuses_frozen_qualification_seed(tmp_path, qualification_payload, amendment):
    w = _writer(); designs = G.build_world_designs(ROOT, qualification_payload)
    with pytest.raises(SystemExit):
        w.write_engineering_world_set(root=ROOT, payload=qualification_payload, cal=CAL, designs=designs,
            amendment=amendment, out_dir=tmp_path / "forbidden")


def test_qualification_loader_owns_all_frozen_scientific_inputs(qualification_payload, amendment):
    w = _writer()
    contract, payload, cal, designs, loaded_amendment = w.load_frozen_qualification_inputs(ROOT)
    assert payload == qualification_payload and int(payload["seeds"]["root"]) == QUAL_ROOT
    assert loaded_amendment == amendment
    assert set(designs) == {x["name"] for x in payload["worlds"]["world_list"]}
    assert hashlib.sha256(CAL_PATH.read_bytes()).hexdigest() == CAL_SHA and cal == CAL
    assert contract["inputs"]["planting_calibration_masked"]["sha256"] == CAL_SHA
    assert set(inspect.signature(w.realize_qualification_worlds).parameters) == {"root", "out_dir", "authorization"}


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
