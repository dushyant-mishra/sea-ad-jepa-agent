import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "agent" / "TEACHER_STUDENT_V5_C2_GPU_CRITICAL_TEST_EXECUTION_MANIFEST_V1.json"


def test_gpu_c2_receipt_cannot_be_satisfied_by_cpu_green():
    x = json.loads(PATH.read_text())
    assert x["status"] == "GPU_EXECUTION_REQUIRED__NO_TRAINING_AUTHORITY"
    assert x["requirements"]["cuda_required_for_execution_receipt"] is True
    assert x["requirements"]["skipped_allowed"] is False
    assert x["cpu_ci_success_may_satisfy_gpu_receipt"] is False
    assert x["execution_receipt"] is None
    assert x["training_authorized"] is False


def test_exact_128x8_and_48_moment_motion_regression_is_mandatory():
    x = json.loads(PATH.read_text())
    expected = x["expected_test_ids"]
    assert x["required_production_geometry_test"] in expected
    assert x["requirements"]["exact_historical_geometry"] == {
        "effective_batch": 128,
        "microbatch": 8,
    }
    assert x["requirements"]["protected_tensors_expected"] == 48
    assert x["requirements"]["adam_exp_avg_live_expected"] == 48
    assert x["requirements"]["adam_exp_avg_sq_live_expected"] == 48
    assert x["requirements"]["protected_parameter_motion_expected"] == 48


def test_declared_gpu_test_ids_exist_in_source():
    x = json.loads(PATH.read_text())
    source = (ROOT / x["source_test_file"]).read_text()
    for test_id in x["expected_test_ids"]:
        assert f"def {test_id}(" in source
