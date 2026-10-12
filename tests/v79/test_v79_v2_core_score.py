from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import v79_v2_core_score as S  # noqa: E402


def _contract():
    return json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text(encoding="utf-8"))


def test_gate_authority_reproduces_frozen_counts_and_limit_set():
    g = S.gate_authority(_contract())
    assert len(g["gates"]) == 292
    assert g["counts"] == {"hard_statistical":260,"hard_rule":28,"limit_statistical":4,"limit_rule":0}
    assert len(g["limit_gates"]) == 4
    assert all(x["verdict_class"] == "FAIL" for x in g["gates"] if x["world"] == "Q11_OMITTED_OPERATOR")


def test_first_hard_fail_is_terminal_and_later_results_cannot_rescue():
    rows = [
        {"gate":"a","verdict_class":"FAIL","passed":True},
        {"gate":"b","verdict_class":"LIMIT","passed":False},
        {"gate":"c","verdict_class":"FAIL","passed":False},
        {"gate":"d","verdict_class":"FAIL","passed":True},
    ]
    t = S.terminal_from_gate_results(_contract(), rows)
    assert t["terminal"] == "V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED"
    assert t["first_hard_fail_index"] == 2
    assert t["post_terminal_count"] == 1
    assert t["limit_failures"] == 1
    labeled=S.label_post_terminal_rows(_contract(),rows)
    assert [x["interpretation"] for x in labeled]==["CONFIRMATORY","CONFIRMATORY","CONFIRMATORY","POST_TERMINAL_DIAGNOSTIC_ONLY"]


def test_incomplete_campaign_is_refused():
    with pytest.raises(S.ScoreRefused):
        S.require_complete_campaign(_contract(), fit_receipts=[])


def test_one_sided_t_lower_exact_frozen_logic():
    alpha=0.05/260
    a=S.one_sided_t_lower_across_genes(np.array([1.0]*44), nominal=0.9, alpha=alpha)
    assert a["passed"] is True
    b=S.one_sided_t_lower_across_genes(np.array([0.79]*44), nominal=0.9, alpha=alpha)
    assert b["passed"] is False and b["zero_sd_rule"] is True
    c=S.one_sided_t_lower_across_genes(np.array([0.81]*44), nominal=0.9, alpha=alpha)
    assert c["passed"] is True


def test_two_sided_bias_requires_significance_and_materiality():
    alpha=0.05/260
    noisy=np.array([2.0,-0.8]*22)
    a=S.two_sided_t_across_genes_and_materiality(noisy, alpha=alpha, materiality=0.50)
    assert a["material"] is True and a["passed"] is True
    b=S.two_sided_t_across_genes_and_materiality(np.array([0.75]*44), alpha=alpha, materiality=0.50)
    assert b["passed"] is False
    c=S.two_sided_t_across_genes_and_materiality(np.array([0.25]*44), alpha=alpha, materiality=0.50)
    assert c["passed"] is True


def test_binomial_tail_gates_use_frozen_upper_tail_definition():
    alpha=0.05/260
    low=S.binomial_tail_gate(count=0,n=44,nominal=0.10,alpha=alpha)
    assert low["passed"] is True
    failing=[k for k in range(45) if not S.binomial_tail_gate(count=k,n=44,nominal=0.10,alpha=alpha)["passed"]]
    assert failing and failing == list(range(failing[0],45))


def test_type_s_none_excluded_passes_and_reports_zero_power():
    r=S.type_s_gate(wrong_sign_count=0,excluded_count=0,alpha=0.05/260)
    assert r["passed"] is True and r["power"] == 0.0


def test_ppc_extreme_rate_counts_gene_statistic_pvalues():
    alpha=0.05/260
    p=np.ones(440)
    assert S.ppc_extreme_rate(p,alpha=alpha)["passed"] is True
    p[:100]=0.001
    assert S.ppc_extreme_rate(p,alpha=alpha)["passed"] is False


def test_population_donor_sd_ratio_uses_frozen_bounds():
    assert S.population_donor_sd_ratio(np.array([1,2,3.]),np.array([1,2,3.]),bounds=(0.8,1.25))["passed"] is True
    assert S.population_donor_sd_ratio(np.array([2,4,6.]),np.array([1,2,3.]),bounds=(0.8,1.25))["passed"] is False


def test_convergence_rule_requires_every_fit_diagnosed():
    assert S.convergence_all_fits_diagnosed(["COMPLETE"]*44)["passed"] is True
    assert S.convergence_all_fits_diagnosed(["COMPLETE"]*43+["NOT_DIAGNOSED"])["passed"] is False


def test_fit_side_has_no_scorer_import():
    for name in ("v79_v2_core_fit_surface.py","v79_v2_core_fit_model.py","v79_v2_core_fit_runner.py",
                 "run_v79_v2_core_benchmark.py","run_v79_v2_core_qualification.py","run_v79_v2_core_qualification_world.py"):
        p = HERE / name
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert "import v79_v2_core_score" not in text
            assert "from v79_v2_core_score" not in text
