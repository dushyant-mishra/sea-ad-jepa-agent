from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))
import run_v79_v2_core_benchmark as B  # noqa: E402
import prepare_v79_v2_core_engineering_benchmark as P  # noqa: E402


def _contract():
    p = ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _fit_view():
    return P.build_fit_contract_view(_contract())


def test_benchmark_plan_is_exactly_two_genes_two_parts_and_engineering_only():
    plan = B.benchmark_plan(_fit_view(), opaque_world_id="0123456789ab", world_manifest_sha="a"*64)
    assert len(plan) == 4
    assert [(x["gene_index"], x["part"]) for x in plan] == [(0,"detection"),(0,"positive"),(1,"detection"),(1,"positive")]
    assert all(x["execution_mode"] == "ENGINEERING_BENCHMARK" for x in plan)


def test_fit_contract_projection_preserves_only_needed_resource_authority():
    v = _fit_view()
    assert v["source_contract_sha256"] == "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
    assert v["resources"]["estimate"] == {"n_fits": 1056}
    assert v["resources"]["qualification_world_count"] == 12
    assert v["resources"]["xla_host_devices"] == v["inference"]["chains"] == 4
    raw = json.dumps(v)
    assert "Q00_BASELINE" not in raw and "Q11_OMITTED_OPERATOR" not in raw
    assert '"world_name"' not in raw and '"world_index"' not in raw and '"gates"' not in raw


def test_projection_over_contract_ceiling_stops():
    c = _fit_view()
    with pytest.raises(B.BenchmarkRefused):
        B.check_projected_hours(c, 72.0001)
    assert B.check_projected_hours(c, 72.0) == 72.0


def test_active_lineage_discards_primary_after_escalation():
    p = {"stage":"PRIMARY","divergences":1,"mean_tree_steps":40.0}
    e = {"stage":"ESCALATION","divergences":0,"mean_tree_steps":50.0}
    x = {"stage":"EXTENSION","divergences":0,"mean_tree_steps":60.0}
    assert B._active_lineage([p, x]) == [p, x]
    assert B._active_lineage([p, e, x]) == [e, x]


def test_benchmark_fit_process_imports_no_controller_world_or_scoring_authority():
    text = (HERE / "run_v79_v2_core_benchmark.py").read_text(encoding="utf-8")
    before_execute = text.split("def execute_benchmark", 1)[0]
    assert "import v79_v2_core_fit_model" not in before_execute
    for forbidden in (
        "generate_v79_v2_core_worlds", "v79_v2_core_world_writer", "v79_v2_core_launch",
        "v79_v2_core_score", "controller_truth", "world_name", "world_index",
    ):
        assert forbidden not in text
    assert "v79_v2_core_fit_custody" in text
    assert "expected_prep_receipt_sha256" in text
