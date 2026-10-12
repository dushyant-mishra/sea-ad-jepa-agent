from __future__ import annotations

import json
import sys
from pathlib import Path

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


def test_incomplete_campaign_is_refused():
    with pytest.raises(S.ScoreRefused):
        S.require_complete_campaign(_contract(), fit_receipts=[])


def test_fit_side_has_no_scorer_import():
    for name in ("v79_v2_core_fit_surface.py","v79_v2_core_fit_model.py","v79_v2_core_fit_runner.py","run_v79_v2_core_benchmark.py"):
        p = HERE / name
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert "import v79_v2_core_score" not in text
            assert "from v79_v2_core_score" not in text
