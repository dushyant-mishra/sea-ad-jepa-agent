import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/v64/validate_v71_synthetic_pipeline_readiness.py"
CONTRACT = ROOT / "results/v64/V71_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("v71_readiness", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def materialize_minimal_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    readiness_dst = root / "results/v64/V71_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json"
    readiness_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CONTRACT, readiness_dst)
    c = json.loads(CONTRACT.read_text())
    for rel in c["required_components"].values():
        src = ROOT / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    required_files = [
        "scripts/v64/build_v71_small_synthetic_etl_fixture.py",
        "scripts/v64/validate_v71_small_synthetic_etl_fixture.py",
        "tests/test_v71_small_synthetic_etl_fixture.py",
        "scripts/v64/teacher_regulatory_candidate_gate_v1.py",
        "scripts/v64/build_regulatory_program_coverage_tensor_v1.py",
        "scripts/v64/validate_teacher_feature_producer_interface_v1.py",
        "scripts/v64/validate_macha_scenicplus_return_manifest_v1.py",
    ]
    for rel in required_files:
        src = ROOT / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return root


def test_v71_readiness_current_repo_passes():
    errors = load_validator().validate(ROOT)
    assert errors == []


def test_v71_readiness_rejects_small_failure_library(tmp_path):
    root = materialize_minimal_repo(tmp_path)
    p = root / "results/v64/V71_SYNTHETIC_ETL_FAILURE_INJECTION_MATRIX_V1.json"
    d = json.loads(p.read_text())
    d["cases"] = d["cases"][:3]
    p.write_text(json.dumps(d))
    errors = load_validator().validate(root)
    assert "FAILURE_LIBRARY_TOO_SMALL" in errors


def test_v71_readiness_rejects_duplicate_failure_ids(tmp_path):
    root = materialize_minimal_repo(tmp_path)
    p = root / "results/v64/V71_SYNTHETIC_ETL_FAILURE_INJECTION_MATRIX_V1.json"
    d = json.loads(p.read_text())
    d["cases"].append(d["cases"][0])
    p.write_text(json.dumps(d))
    errors = load_validator().validate(root)
    assert "DUPLICATE_FAILURE_CASE_ID" in errors


def test_v71_readiness_rejects_weak_truth_firewall(tmp_path):
    root = materialize_minimal_repo(tmp_path)
    p = root / "results/v64/V71_SYNTHETIC_TRUTH_FIREWALL_CONTRACT_V1.json"
    d = json.loads(p.read_text())
    d["forbidden_to_pipeline"] = ["some hidden values"]
    p.write_text(json.dumps(d))
    errors = load_validator().validate(root)
    assert "TRUTH_FIREWALL_NOT_EXPLICIT_ENOUGH" in errors


def test_v71_readiness_rejects_missing_executable_interface(tmp_path):
    root = materialize_minimal_repo(tmp_path)
    missing = root / "scripts/v64/build_v71_small_synthetic_etl_fixture.py"
    missing.unlink()
    errors = load_validator().validate(root)
    assert any(x.startswith("MISSING_EXECUTABLE_INTERFACE:") for x in errors)
