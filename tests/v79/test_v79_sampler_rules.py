"""Every branch of the shared sampler rules on fabricated runs: pass first time; extension rescues a
no-divergence miss; divergences escalate target_accept and are never extended; a run still failing after one
extension, or divergent at 0.99, stays NOT_DIAGNOSED; thresholds are the contract's."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_sampler_rules as SR  # noqa: E402


def scripted(outcomes):
    """outcomes: list of (divergences, rhat, ess) consumed in call order."""
    calls = []

    def run(ta, extend_from):
        div, rhat, ess = outcomes[len(calls)]
        calls.append((ta, extend_from is not None))
        return dict(divergences=[div, 0, 0, 0], seconds=1.0, mean_steps=10, rhat=rhat, ess=ess)

    def diagnose(r):
        return dict(worst_rhat=r["rhat"], worst_ess=r["ess"])
    return run, diagnose, calls


def test_thresholds_are_the_contracts():
    assert (SR.RHAT_MAX, SR.ESS_MIN, SR.RETRY_ACCEPT) == (1.01, 400, (0.9, 0.95, 0.99))


def test_pass_first_time_needs_one_run():
    run, diag, calls = scripted([(0, 1.004, 900)])
    _, _, att = SR.fit_with_rules(run, diag)
    assert calls == [(0.9, False)] and att[-1]["diagnosed"]


def test_no_divergence_miss_is_extended_once():
    run, diag, calls = scripted([(0, 1.013, 1000), (0, 1.006, 2100)])
    _, _, att = SR.fit_with_rules(run, diag)
    assert calls == [(0.9, False), (0.9, True)]
    assert [a["extended"] for a in att] == [False, True] and att[-1]["diagnosed"]


def test_extension_that_still_fails_is_not_diagnosed_and_not_retried():
    run, diag, calls = scripted([(0, 1.03, 100), (0, 1.02, 250)])
    _, _, att = SR.fit_with_rules(run, diag)
    assert calls == [(0.9, False), (0.9, True)] and not att[-1]["diagnosed"]


def test_divergences_escalate_and_are_never_extended():
    run, diag, calls = scripted([(3, 1.004, 900), (0, 1.004, 900)])
    _, _, att = SR.fit_with_rules(run, diag)
    assert calls == [(0.9, False), (0.95, False)] and att[-1]["diagnosed"]


def test_divergent_at_every_target_accept_is_not_diagnosed():
    run, diag, calls = scripted([(1, 1.0, 900), (2, 1.0, 900), (1, 1.0, 900)])
    _, _, att = SR.fit_with_rules(run, diag)
    assert [c[0] for c in calls] == [0.9, 0.95, 0.99] and not att[-1]["diagnosed"]


def test_divergence_in_the_extension_fails():
    run, diag, calls = scripted([(0, 1.02, 300), (1, 1.004, 900)])
    _, _, att = SR.fit_with_rules(run, diag)
    assert calls == [(0.9, False), (0.9, True)] and not att[-1]["diagnosed"]
