import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/v64/validate_v71_synthetic_pipeline_readiness.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("v71_readiness", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def copy_min_repo(tmp_path):
    dst = tmp_path / "repo"
    for rel in [
        "results/v64/V71_SYNTHETIC_PIPELINE_READINESS_CONTRACT_V1.json",
        "results/v64/V71_FULL_SYNTHETIC_TWIN_SYSTEM_CONTRACT_V1.json",
        "results/v64/V71_SYNTHETIC_RAW_ETL_CONTRACT_V1.json",
        "results/v64/V71_SYNTHETIC_ETL_FAILURE_INJECTION_MATRIX_V1.json",
        "results/v64/V71_SYNTHETIC_TRUTH_FIREWALL_CONTRACT_V1.json",
        "results/v64/V66_STAGE4_EXECUTION_AUTHORITY_CONTRACT_V5.json",
        "results/v64/V69_STAGE4_MULTISOURCE_EVIDENCE_INTEGRATION_CONTRACT_V1.json",
        "results/v64/V69_REGULATORY_PROGRAM_NAMESPACE_CONTRACT_V1.json",
        "results/v64/V69_REGULATORY_PROGRAM_CROSSWALK_SCHEMA_V1.json",
        "results/v64/V70_TEACHER_REGULATORY_CANDIDATE_SELECTION_CONTRACT_V1.json",
        "results/v64/V70_PRIVILEGED_TEACHER_FEATURE_PRODUCER_INTERFACE_V1.json",
        "scripts/v64/build_v71_small_synthetic_etl_fixture.py",
        "scripts/v64/validate_v71_small_synthetic_etl_fixture.py",
        "scripts/v64/teacher_regulatory_candidate_gate_v1.py",
        "scripts/v64/build_regulatory_program_coverage_tensor_v1.py",
        "scripts/v64/validate_teacher_feature_producer_interface_v1.py",
        "scripts/v64/validate_macha_scenicplus_return_manifest_v1.py",
        "tests/test_v71_small_synthetic_etl_fixture.py",
    ]:
        src = ROOT / rel
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    return dst


def test_current_repository_is_r0_r1_interface_ready():
    assert load_validator().validate(ROOT) == []


def test_missing_required_contract_fails(tmp_path):
    root = copy_min_repo(tmp_path)
    (root / "results/v64/V69_REGULATORY_PROGRAM_NAMESPACE_CONTRACT_V1.json").unlink()
    errors = load_validator().validate(root)
    assert any(e.startswith("MISSING_COMPONENT:program_namespace:") for e in errors)


def test_duplicate_failure_case_id_fails(tmp_path):
    root = copy_min_repo(tmp_path)
    p = root / "results/v64/V71_SYNTHETIC_ETL_FAILURE_INJECTION_MATRIX_V1.json"
    obj = json.loads(p.read_text())
    obj["cases"].append(obj["cases"][0])
    p.write_text(json.dumps(obj))
    assert "DUPLICATE_FAILURE_CASE_ID" in load_validator().validate(root)


def test_truth_firewall_must_explicitly_forbid_private_partition(tmp_path):
    root = copy_min_repo(tmp_path)
    p = root / "results/v64/V71_SYNTHETIC_TRUTH_FIREWALL_CONTRACT_V1.json"
    obj = json.loads(p.read_text())
    obj["forbidden_to_pipeline"] = [
        x for x in obj["forbidden_to_pipeline"]
        if "recoverable/private" not in x
    ]
    p.write_text(json.dumps(obj))
    assert "TRUTH_FIREWALL_NOT_EXPLICIT_ENOUGH" in load_validator().validate(root)


def test_missing_executable_interface_fails(tmp_path):
    root = copy_min_repo(tmp_path)
    (root / "scripts/v64/validate_macha_scenicplus_return_manifest_v1.py").unlink()
    errors = load_validator().validate(root)
    assert any(e.startswith("MISSING_EXECUTABLE_INTERFACE:") for e in errors)
