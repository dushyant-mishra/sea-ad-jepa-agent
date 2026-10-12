import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

from td_corrected_replay_authority_v1 import BoundReplayAuthority, begin_attempt  # noqa: E402
from td_corrected_replay_execute_v1 import StageOutcome, execute_replay  # noqa: E402


def _bound(ns: Path):
    return BoundReplayAuthority("1" * 64, "2" * 64, "abc123", ns, ("o", "r", "p"))


def _runner(statuses, tmp_path):
    calls = []
    def run(stage):
        calls.append(stage)
        artifact = tmp_path / f"{stage}.raw.json"
        artifact.write_text(json.dumps({"stage": stage, "status": statuses[stage]}))
        return StageOutcome(status=statuses[stage], terminal=f"{stage}_{statuses[stage]}", artifacts=(artifact,))
    return run, calls


def test_order_and_historical_scale_pattern(tmp_path):
    ns = tmp_path / "ns"
    bound = _bound(ns)
    begin_attempt(bound, ns)
    run, calls = _runner({"TD56": "PASS", "TD57B": "PASS", "TD57C": "FAIL", "TD59": "PASS"}, tmp_path)
    receipt = execute_replay(bound, ns, run)
    assert calls == ["TD56", "TD57B", "TD57C", "TD59"]
    assert receipt["stage_statuses"] == {"TD56": "PASS", "TD57B": "PASS", "TD57C": "FAIL", "TD59": "PASS"}
    assert receipt["terminal"] == "CORRECTED_REPLAY_COMPLETE__ROUTING_PROJECTION_REQUIRED__NO_TARGET_AUTHORITY"
    assert receipt["spent_authority"] is True
    assert receipt["target_selected"] is False and receipt["training_authorized"] is False


def test_early_stop_td56_or_td57b_failure(tmp_path):
    for statuses, expected_calls in [
        ({"TD56": "FAIL"}, ["TD56"]),
        ({"TD56": "PASS", "TD57B": "FAIL"}, ["TD56", "TD57B"]),
    ]:
        ns = tmp_path / ("ns" + str(len(expected_calls)))
        bound = _bound(ns)
        begin_attempt(bound, ns)
        run, calls = _runner(statuses, tmp_path)
        receipt = execute_replay(bound, ns, run)
        assert calls == expected_calls
        assert receipt["terminal"].startswith("CORRECTED_REPLAY_EARLY_STOP")


def test_td57c_pass_divergence_stops_before_td59(tmp_path):
    ns = tmp_path / "ns"
    bound = _bound(ns)
    begin_attempt(bound, ns)
    run, calls = _runner({"TD56": "PASS", "TD57B": "PASS", "TD57C": "PASS"}, tmp_path)
    receipt = execute_replay(bound, ns, run)
    assert calls == ["TD56", "TD57B", "TD57C"]
    assert receipt["terminal"] == "CORRECTED_TD57C_PASS_DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED__NO_TARGET_AUTHORITY"


def test_not_estimable_preserved_and_stops(tmp_path):
    ns = tmp_path / "ns"
    bound = _bound(ns)
    begin_attempt(bound, ns)
    run, calls = _runner({"TD56": "PASS", "TD57B": "NOT_ESTIMABLE"}, tmp_path)
    receipt = execute_replay(bound, ns, run)
    assert calls == ["TD56", "TD57B"]
    assert receipt["stage_statuses"]["TD57B"] == "NOT_ESTIMABLE"
    assert "NOT_ESTIMABLE" in receipt["terminal"]


def test_exception_after_marker_is_spent_failure(tmp_path):
    ns = tmp_path / "ns"
    bound = _bound(ns)
    marker = begin_attempt(bound, ns)
    def boom(stage):
        raise RuntimeError("kernel crashed")
    receipt = execute_replay(bound, ns, boom)
    assert marker.exists()
    assert receipt["spent_authority"] is True
    assert receipt["terminal"] == "POST_MARKER_EXECUTION_FAILURE__AUTHORITY_SPENT__NO_RERUN"
    assert "kernel crashed" in receipt["failure"]
