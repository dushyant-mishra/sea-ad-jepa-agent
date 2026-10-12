import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

from td_corrected_replay_authority_v1 import BoundReplayAuthority  # noqa: E402
from td_corrected_replay_execute_v1 import StageOutcome  # noqa: E402
from run_td_corrected_replay_once import LaunchError, launch_replay  # noqa: E402


def _bound(ns):
    return BoundReplayAuthority("1" * 64, "2" * 64, "abc123", ns, ("owner", "runtime", "operational"))


def _qual(ns):
    return {
        "schema": "JEPA_TD_CORRECTED_REPLAY_QUALIFICATION_RECEIPT_V1",
        "terminal": "PASS_TD_CORRECTED_REPLAY_TURNKEY_QUALIFICATION__NO_BIOLOGICAL_REPLAY_RUN__LAUNCH_AUDIT_REQUIRED",
        "namespace_probe": str(ns),
        "start_marker_created": False,
        "biological_replay_run": False,
    }


def _audit(bound):
    return {
        "schema": "JEPA_TD_CORRECTED_REPLAY_LAUNCH_AUDIT_ACCEPTANCE_V1",
        "classification": "ACCEPT_TD_CORRECTED_REPLAY_LAUNCH_PACKAGE__EXECUTE_ONCE_ALLOWED",
        "implementation_commit": bound.implementation_commit,
        "contract_sha256": bound.contract_sha256,
        "qualification_receipt_sha256": bound.qualification_receipt_sha256,
        "namespace": str(bound.namespace),
        "authority_ids": list(bound.authority_ids),
        "replay_execution_authorized": True,
        "g6_execution_authorized": False,
        "g7_execution_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


def _runner(tmp_path):
    statuses = {"TD56": "PASS", "TD57B": "PASS", "TD57C": "FAIL", "TD59": "PASS"}
    def run(stage):
        p = tmp_path / f"{stage}.txt"
        p.write_text(stage)
        return StageOutcome(statuses[stage], f"{stage}_{statuses[stage]}", (p,))
    return run


def test_qualify_never_creates_marker(tmp_path):
    ns = tmp_path / "ns"
    out = launch_replay("QUALIFY", _bound(ns), _qual(ns), None, None)
    assert out["mode"] == "QUALIFY"
    assert out["start_marker_created"] is False
    assert not ns.exists()


def test_execute_requires_launch_audit_and_runs_once(tmp_path):
    ns = tmp_path / "ns"
    bound = _bound(ns)
    with pytest.raises(LaunchError, match="launch-audit"):
        launch_replay("EXECUTE_ONCE", bound, _qual(ns), None, _runner(tmp_path))
    out = launch_replay("EXECUTE_ONCE", bound, _qual(ns), _audit(bound), _runner(tmp_path))
    assert out["terminal"] == "CORRECTED_REPLAY_COMPLETE__ROUTING_PROJECTION_REQUIRED__NO_TARGET_AUTHORITY"
    assert (ns / "TD_CORRECTED_REPLAY_EXECUTION_START.json").exists()
    with pytest.raises(Exception):
        launch_replay("EXECUTE_ONCE", bound, _qual(ns), _audit(bound), _runner(tmp_path))


def test_reject_stale_audit_or_dirty_namespace(tmp_path):
    ns = tmp_path / "ns"
    bound = _bound(ns)
    audit = _audit(bound)
    audit["qualification_receipt_sha256"] = "3" * 64
    with pytest.raises(LaunchError, match="qualification_receipt_sha256"):
        launch_replay("EXECUTE_ONCE", bound, _qual(ns), audit, _runner(tmp_path))
    ns.mkdir()
    with pytest.raises(LaunchError, match="namespace"):
        launch_replay("QUALIFY", bound, _qual(ns), None, None)


def test_reject_zero_comparison_qualification_and_forbidden_command_paths(tmp_path):
    ns = tmp_path / "ns"
    bound = _bound(ns)
    qual = _qual(ns)
    qual["stages"] = [{"id": "TD56", "comparison_population_n": 0}]
    with pytest.raises(LaunchError, match="zero comparison"):
        launch_replay("QUALIFY", bound, qual, None, None)
    qual = _qual(ns)
    qual["stage_commands"] = {"TD56": ["python", "scripts/v5/td_g6_real.py"]}
    with pytest.raises(LaunchError, match="G6/G7"):
        launch_replay("QUALIFY", bound, qual, None, None)
