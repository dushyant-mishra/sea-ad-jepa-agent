"""V2 live routing: accept date-advanced main without erasing October V1 history."""
import json
from pathlib import Path
import shutil

from scripts.agent.verify_current_authority_surface_v2 import check, POINTER, ROUTER, FRONT


ROOT = Path(__file__).resolve().parents[1]


def _fixture(tmp_path):
    paths = [POINTER, ROUTER, *FRONT,
             "scripts/v5/td_unified/observation_v2c_standalone_student_gate_v1.py",
             "deployment/student_v2c/Dockerfile.v1"]
    for item in paths:
        dest = tmp_path / item
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / item, dest)
    return tmp_path


def test_current_main_route_is_explicitly_non_authorizing():
    assert check(ROOT) == []


def test_fake_training_issuer_or_reviewer_acceptance_rejected(tmp_path):
    root = _fixture(tmp_path)
    p = root / POINTER
    d = json.loads(p.read_text())
    d["current_non_authorizing_implementation"]["real_training_authorized"] = True
    d["current_non_authorizing_implementation"]["source_issuer"] = "VERIFIED"
    d["current_non_authorizing_implementation"]["independent_recheck"] = "ACCEPT"
    p.write_text(json.dumps(d))
    failures = check(root)
    assert any("fixture authority promoted" in item for item in failures)


def test_stale_date_and_wrong_audit_pointer_fail(tmp_path):
    root = _fixture(tmp_path)
    p = root / POINTER
    d = json.loads(p.read_text())
    d["date"] = "2026-10-05"
    d["canonical_audit"]["pr"] = 323
    p.write_text(json.dumps(d))
    failures = check(root)
    assert any("backdated" in item for item in failures)
    assert any("canonical_audit PR" in item for item in failures)


def test_missing_main_router_fails(tmp_path):
    root = _fixture(tmp_path)
    (root / ROUTER).unlink()
    assert any("execution map missing" in item for item in check(root))


def test_old_pending_reviewer_status_now_refused(tmp_path):
    root = _fixture(tmp_path)
    p = root / POINTER
    d = json.loads(p.read_text())
    d["current_task_status"] = "REPAIRED_V2C_D1_CONTAINER_AUTHOR_CI_GREEN__INDEPENDENT_MACHA_RECHECK_PENDING"
    d["current_non_authorizing_implementation"]["independent_recheck"] = "PENDING"
    p.write_text(json.dumps(d))
    assert check(root)


def test_fixture_acceptance_does_not_allow_runtime_or_launcher_attestation(tmp_path):
    root = _fixture(tmp_path)
    p = root / POINTER
    d = json.loads(p.read_text())
    d["current_non_authorizing_implementation"]["runtime_attested"] = True
    d["current_non_authorizing_implementation"]["trusted_launcher_accepted"] = True
    p.write_text(json.dumps(d))
    assert any("fixture authority promoted" in item for item in check(root))
