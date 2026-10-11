"""Fail-closed family gate (controller ruling 2026-10-11, item 6): once any required world of a family fails under
the frozen rules, the family is NOT_QUALIFIED and its remaining worlds are not run. world_failures must agree with
the frozen suite criteria; the gate refuses mixed parts. Fabricated parts only; no sampler."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_recovery_rules as RR  # noqa: E402

GATE = ROOT / "scripts" / "v79" / "v79_family_gate.py"
WORLDS = RR.SCENARIOS_REQUIRED


def fit(diagnosed=True, covered=18, cls_q=(0.2, 0.3, 0.4), res_q=(0.3, 0.4, 0.5), planted=True):
    comp = lambda q, scored: dict(across_gene_median_q=list(q), planted_and_scored=scored,
                                  covered=[True] * covered + [False] * (20 - covered) if scored else None)
    return dict(components_result={"cls": comp(cls_q, planted), "res": comp(res_q, False)},
                diagnostics=dict(diagnosed=diagnosed))


def good_suite():
    s = {w: fit(cls_q=(0.0, 0.01, 0.05), planted=False) for w in WORLDS}
    s["S1_present"] = fit(cls_q=(0.2, 0.3, 0.4), res_q=(0.3, 0.4, 0.5))
    s["S5_labels_removed"] = fit(cls_q=(0.0, 0.01, 0.05), res_q=(0.6, 0.7, 0.8), planted=False)
    return s


def failing_criteria(suite):
    return sorted(k for k, v in RR.criteria(suite).items() if not v["pass_"])


@pytest.mark.parametrize("break_it", [
    lambda s: s["S4_operator_only"]["diagnostics"].update(diagnosed=False),
    lambda s: s.update(S1_present=fit(covered=12)),
    lambda s: s["S0_class_absent"]["components_result"]["cls"].update(across_gene_median_q=[0.1, 0.2, 0.25]),
    lambda s: s["S5_labels_removed"]["components_result"]["res"].update(across_gene_median_q=[0.45, 0.5, 0.6]),
    lambda s: None,
])
def test_world_failures_agree_with_the_frozen_suite_criteria(break_it):
    s = good_suite()
    break_it(s)
    per_world = RR.world_failures(s)
    flagged = sorted(f"{w}.{c}" for w, cs in per_world.items() for c in cs)
    expected = sorted(k for k in failing_criteria(s) if k != "all_fits_diagnosed")
    expected += sorted(f"{w}.not_diagnosed" for w, d in RR.criteria(s)["all_fits_diagnosed"]["per_fit"].items() if not d)
    assert flagged == sorted(expected)


def test_cross_world_controls_wait_for_s1():
    s = good_suite()
    s["S0_class_absent"]["components_result"]["cls"].update(across_gene_median_q=[0.1, 0.2, 0.25])
    partial = {"S0_class_absent": s["S0_class_absent"]}
    assert RR.world_failures(partial) == {"S0_class_absent": []}


def part(world, f, *, lik="gaussian", snapshot="a" * 40, config="c" * 64, rules="r" * 64):
    return dict(schema="V79_SIMULATION_RECOVERY_V2", likelihood=lik, code_snapshot=snapshot,
                sampler_config=dict(sha256=config), sampler_rules=dict(sha256=rules), fits={world: f})


def run_gate(tmp_path, parts, lik="gaussian"):
    for p in parts:
        world = next(iter(p["fits"]))
        (tmp_path / f"part_{p['likelihood']}_{world}.json").write_text(json.dumps(p), encoding="utf-8")
    return subprocess.run([sys.executable, str(GATE), str(tmp_path), lik], capture_output=True, text=True)


def test_gate_lets_a_clean_family_continue(tmp_path):
    s = good_suite()
    r = run_gate(tmp_path, [part("S1_present", s["S1_present"]), part("S0_class_absent", s["S0_class_absent"])])
    assert r.returncode == 0, r.stderr
    assert not (tmp_path / "FAMILY_STOPPED_gaussian.json").exists()


def test_gate_stops_the_family_after_a_failed_world_and_records_why(tmp_path):
    s = good_suite()
    s["S0_class_absent"]["diagnostics"]["diagnosed"] = False
    r = run_gate(tmp_path, [part("S1_present", s["S1_present"]), part("S0_class_absent", s["S0_class_absent"])])
    assert r.returncode == 10
    rec = json.loads((tmp_path / "FAMILY_STOPPED_gaussian.json").read_text(encoding="utf-8"))
    assert rec["terminal"] == "NOT_QUALIFIED" and rec["failed"] == {"S0_class_absent": ["not_diagnosed"]}


def test_gate_ignores_other_families_and_refuses_mixed_parts(tmp_path):
    s = good_suite()
    bad = dict(s["S0_class_absent"], diagnostics=dict(diagnosed=False))
    r = run_gate(tmp_path, [part("S0_class_absent", bad, lik="ztnb")], lik="gaussian")
    assert r.returncode == 0
    r = run_gate(tmp_path, [part("S1_present", s["S1_present"]),
                            part("S2_class_permuted", s["S2_class_permuted"], snapshot="b" * 40)])
    assert r.returncode == 11 and "mix" in r.stderr
