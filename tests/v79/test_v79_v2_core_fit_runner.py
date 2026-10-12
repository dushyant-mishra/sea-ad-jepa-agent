from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import v79_v2_core_fit_runner as R  # noqa: E402


def _contract():
    p = Path(__file__).resolve().parents[2] / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_sampler_policy_is_parsed_only_from_contract():
    p = R.sampler_policy(_contract())
    assert p.chains == 4 and p.warmup == 1000 and p.draws == 1000 and p.max_tree_depth == 10
    assert p.target_accept_primary == pytest.approx(0.90)
    assert p.target_accept_escalation == pytest.approx(0.99)
    assert p.rhat_max == pytest.approx(1.01)
    assert p.ess_min == 400


def test_recovery_path_is_finite_and_predeclared():
    c = _contract()
    bad_div = {"divergences": 1, "worst_rhat": 1.0, "worst_ess_bulk": 1000, "worst_ess_tail": 1000}
    bad_ess = {"divergences": 0, "worst_rhat": 1.0, "worst_ess_bulk": 399, "worst_ess_tail": 1000}
    good = {"divergences": 0, "worst_rhat": 1.0, "worst_ess_bulk": 800, "worst_ess_tail": 800}
    assert R.next_recovery_action(c, [], bad_div) == "ESCALATE"
    assert R.next_recovery_action(c, [{"stage":"PRIMARY"}], bad_ess) == "EXTEND"
    assert R.next_recovery_action(c, [{"stage":"PRIMARY"}], good) == "COMPLETE"
    assert R.next_recovery_action(c, [{"stage":"PRIMARY"},{"stage":"ESCALATION"}], bad_div) == "NOT_DIAGNOSED"
    assert R.next_recovery_action(c, [{"stage":"PRIMARY"},{"stage":"EXTENSION"}], bad_ess) == "NOT_DIAGNOSED"
    assert R.next_recovery_action(c, [{"stage":"PRIMARY"},{"stage":"EXTENSION"}], bad_div) == "NOT_DIAGNOSED"
    assert R.next_recovery_action(c, [{"stage":"PRIMARY"},{"stage":"ESCALATION"}], bad_ess) == "EXTEND"
    assert R.next_recovery_action(c, [{"stage":"PRIMARY"},{"stage":"ESCALATION"},{"stage":"EXTENSION"}], bad_ess) == "NOT_DIAGNOSED"


def test_benchmark_mode_never_counts_as_qualification():
    r = R.new_fit_receipt(execution_mode="ENGINEERING_BENCHMARK", fit_id="abc", opaque_world_id="0123456789ab", gene_index=1, part="detection", input_manifest_sha="0"*64, contract_sha="1"*64, code_sha="2"*40)
    assert r["benchmark_run"] is True
    assert r["qualification_fits_run"] == 0
    assert r["scoring_run"] is False
    assert r["truth_accessed"] is False


def test_fit_identity_is_deterministic_and_stage_independent():
    a = R.fit_identity("0123456789ab", "a"*64, "detection", 3)
    b = R.fit_identity("0123456789ab", "a"*64, "detection", 3)
    assert a == b and len(a) == 64


def test_execution_mode_refuses_unknown_value():
    with pytest.raises(R.FitRunnerRefused):
        R.new_fit_receipt(execution_mode="QUALIFICATIONISH", fit_id="x", opaque_world_id="0123456789ab", gene_index=0, part="detection", input_manifest_sha="0"*64, contract_sha="1"*64, code_sha="2"*40)
