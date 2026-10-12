from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import run_v79_v2_core_benchmark as B  # noqa: E402


def _contract():
    p = Path(__file__).resolve().parents[2] / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_benchmark_plan_is_exactly_two_genes_two_parts_and_engineering_only():
    plan = B.benchmark_plan(_contract(), opaque_world_id="0123456789ab", world_manifest_sha="a"*64)
    assert len(plan) == 4
    assert [(x["gene_index"], x["part"]) for x in plan] == [(0,"detection"),(0,"positive"),(1,"detection"),(1,"positive")]
    assert all(x["execution_mode"] == "ENGINEERING_BENCHMARK" for x in plan)


def test_benchmark_receipt_cannot_claim_qualification_or_truth():
    r = B.benchmark_receipt_skeleton(_contract(), code_sha="b"*40, package_hashes={"root_manifest":"c"*64,"directory_digest":"d"*64,"blinded_index":"e"*64})
    assert r["benchmark_run"] is True
    assert r["qualification_fits_run"] == 0
    assert r["scoring_run"] is False
    assert r["truth_accessed"] is False
    assert r["training_authorized"] is False


def test_projection_over_contract_ceiling_stops():
    c = _contract()
    with pytest.raises(B.BenchmarkRefused):
        B.check_projected_hours(c, 72.0001)
    assert B.check_projected_hours(c, 72.0) == 72.0


def test_active_lineage_discards_primary_after_escalation():
    p = {"stage":"PRIMARY","divergences":1,"mean_tree_steps":40.0}
    e = {"stage":"ESCALATION","divergences":0,"mean_tree_steps":50.0}
    x = {"stage":"EXTENSION","divergences":0,"mean_tree_steps":60.0}
    assert B._active_lineage([p, x]) == [p, x]
    assert B._active_lineage([p, e, x]) == [e, x]


def test_benchmark_module_does_not_import_model_before_runtime_configuration():
    text = (HERE / "run_v79_v2_core_benchmark.py").read_text(encoding="utf-8")
    before_execute = text.split("def execute_benchmark", 1)[0]
    assert "import v79_v2_core_fit_model" not in before_execute
