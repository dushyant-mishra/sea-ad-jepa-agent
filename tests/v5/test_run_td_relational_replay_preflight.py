import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "run_td_relational_replay_preflight.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_preflight_driver", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_canonical_paths_are_explicit_and_cross_lane_collision_path_is_separate():
    m = load_module()
    p = m.canonical_paths(Path("D:/Jepa project"), Path("D:/Jepa project-stage81a3r-20260814"))
    assert p["sample_freeze"].as_posix().endswith("exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv")
    assert p["provenance"].as_posix().endswith("results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz")
    assert "Jepa project-stage81a3r-20260814" in p["collision_ledger"].as_posix()
    assert p["calibration_zip"].name == "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip"
    assert p["td_artifacts_zip"].name == "JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip"


def test_output_namespace_is_fixed_and_immutable(tmp_path):
    m = load_module()
    out = m.default_output_dir(tmp_path)
    assert out.as_posix().endswith(
        "results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split"
    )
    out.mkdir(parents=True)
    (out / "PREFLIGHT_RESULT.json").write_text("{}\n", encoding="utf-8")
    try:
        m.assert_fresh_output(out)
    except RuntimeError as e:
        assert "immutable" in str(e).lower()
    else:
        raise AssertionError("existing preflight result must fail closed")


def test_output_namespace_rejects_partial_failed_run_artifacts(tmp_path):
    m = load_module()
    out = m.default_output_dir(tmp_path)
    out.mkdir(parents=True)
    (out / "JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv").write_bytes(b"partial\r\n")
    try:
        m.assert_fresh_output(out)
    except RuntimeError as e:
        text = str(e).lower()
        assert "immutable" in text
        assert "non-empty" in text or "artifact" in text
    else:
        raise AssertionError("partial failed-run artifacts must fail closed")


def test_static_archive_authorities_are_exact_hash_gates(tmp_path):
    m = load_module()
    cal = tmp_path / "cal.zip"
    td = tmp_path / "td.zip"
    cal.write_bytes(b"calibration-authority")
    td.write_bytes(b"td-authority")
    m.EXPECTED_CALIBRATION_SHA256 = hashlib.sha256(cal.read_bytes()).hexdigest()
    m.EXPECTED_TD_ARTIFACTS_SHA256 = hashlib.sha256(td.read_bytes()).hexdigest()
    got = m.verify_static_archives({"calibration_zip": cal, "td_artifacts_zip": td})
    assert got == {
        "calibration_zip_sha256": m.EXPECTED_CALIBRATION_SHA256,
        "td_artifacts_zip_sha256": m.EXPECTED_TD_ARTIFACTS_SHA256,
    }
    td.write_bytes(b"changed")
    try:
        m.verify_static_archives({"calibration_zip": cal, "td_artifacts_zip": td})
    except RuntimeError as e:
        assert "td41" in str(e).lower() or "sha mismatch" in str(e).lower()
    else:
        raise AssertionError("changed TD archive must fail closed")


def test_mapping_command_is_value_blind_and_complete(tmp_path):
    m = load_module()
    paths = m.canonical_paths(Path("D:/Jepa project"), Path("D:/Jepa project-stage81a3r-20260814"))
    out = tmp_path / "preflight_v4"
    cmd = m.mapping_command(Path("python"), Path("D:/repo"), paths, out, out / "S174_REBUILD_FREEZE_V1.json")
    text = " ".join(map(str, cmd))
    assert "audit_td_relational_replay_mapping_preflight.py" in text
    assert "--source-root D:/Jepa project" in text.replace("\\", "/")
    assert "--sample-freeze" in text
    assert "--provenance" in text
    assert "--collision-ledger" in text
    assert "--macha-freeze" in text
    assert "--out" in text


def test_mapping_failure_receipt_is_structured_and_non_authorizing(tmp_path):
    m = load_module()
    out = tmp_path / "preflight_v4"
    out.mkdir()
    receipt_path = m.write_failure_receipt(
        out,
        phase="G4_G5_MAPPING_PREFLIGHT",
        terminal="FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_AT_G4_G5_MAPPING",
        error="example failure",
        command=["python", "mapping.py"],
        inputs={"replay_manifest_sha256": "abc"},
    )
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "JEPA_TD_RELATIONAL_PREFLIGHT_FAILURE_RECEIPT_V1"
    assert payload["status"].startswith("FAIL_")
    assert payload["phase"] == "G4_G5_MAPPING_PREFLIGHT"
    assert payload["real_value_replay_authorized"] is False
    assert payload["training_authorized"] is False
