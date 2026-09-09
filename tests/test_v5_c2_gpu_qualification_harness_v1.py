import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v5_anticheat" / "run_v5_c2_gpu_qualification_v1.py"
MANIFEST = ROOT / "docs" / "agent" / "TEACHER_STUDENT_V5_C2_GPU_CRITICAL_TEST_EXECUTION_MANIFEST_V1.json"
spec = importlib.util.spec_from_file_location("gpuq", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def manifest():
    return json.loads(MANIFEST.read_text())


def test_current_gpu_manifest_passes_static_validation():
    out = m.validate_manifest(manifest())
    assert len(out["expected_test_ids"]) == 6


def test_cpu_green_cannot_be_promoted():
    x = manifest()
    x["cpu_ci_success_may_satisfy_gpu_receipt"] = True
    with pytest.raises(RuntimeError, match="CPU_MASQUERADE"):
        m.validate_manifest(x)


def test_skip_policy_cannot_be_relaxed():
    x = manifest()
    x["requirements"]["skipped_allowed"] = True
    with pytest.raises(RuntimeError, match="FAIL_OPEN"):
        m.validate_manifest(x)


def test_128x8_geometry_and_48_counts_are_frozen_in_gpu_receipt_contract():
    x = manifest()
    x["requirements"]["exact_historical_geometry"]["microbatch"] = 4
    with pytest.raises(RuntimeError, match="GEOMETRY"):
        m.validate_manifest(x)
    x = manifest()
    x["requirements"]["adam_exp_avg_sq_live_expected"] = 47
    with pytest.raises(RuntimeError, match="PROTECTED_COUNT"):
        m.validate_manifest(x)


def test_training_authority_escalation_is_rejected():
    x = manifest()
    x["training_authorized"] = True
    with pytest.raises(RuntimeError, match="AUTHORITY_ESCALATION"):
        m.validate_manifest(x)
