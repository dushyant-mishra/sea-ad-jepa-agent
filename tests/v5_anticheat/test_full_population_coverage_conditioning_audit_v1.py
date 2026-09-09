from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5_anticheat" / "audit_full_population_coverage_conditioning_v1.py"
spec = importlib.util.spec_from_file_location("coverage_audit", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def test_full_coverage_ratio_lower_bound_and_minimum_cap_are_exact():
    donors = {"small": 81, "large": 174_111}
    lower = m.full_coverage_weight_ratio_lower_bound(donors, cell_cap=32)
    assert lower == pytest.approx((174_111 / 81) / 32)
    assert lower == pytest.approx(67.17245370370371)
    assert m.minimum_cell_cap_for_weight_ratio_ceiling(
        donors, weight_ratio_ceiling=64.0
    ) == 34


def test_requested_ratio_ceiling_is_reported_infeasible_not_silently_relaxed():
    groups = [m.Group("D1", 1, "S1", 1), m.Group("D2", 2, "S2", 100)]
    result = m.build_result(
        metadata_sqlite_sha256="0" * 64,
        partition="reader_fit",
        groups=groups,
        donor_n={"D1": 1, "D2": 100},
        source_n={"S1": 1, "S2": 100},
        population_cells=101,
        group_floor=1,
        cell_cap=2,
        ess_floor=0.01,
        weight_ratio_ceiling=40.0,
    )
    f = result["full_coverage_feasibility"]
    assert f["importance_weight_ratio_lower_bound_under_cell_cap"] == pytest.approx(50.0)
    assert f["requested_ratio_ceiling_is_feasible_under_full_coverage_and_cell_cap"] is False
    assert f["requested_weight_ratio_ceiling"] == 40.0
    assert result["training_authorized"] is False


def test_coverage_only_and_balanced_candidate_preserve_group_floor_and_cap():
    groups = [
        m.Group("D1", 1, "S1", 2),
        m.Group("D1", 2, "S1", 1),
        m.Group("D2", 3, "S2", 8),
    ]
    result = m.build_result(
        metadata_sqlite_sha256="0" * 64,
        partition="reader_fit",
        groups=groups,
        donor_n={"D1": 3, "D2": 8},
        source_n={"S1": 3, "S2": 8},
        population_cells=11,
        group_floor=4,
        cell_cap=8,
        ess_floor=0.20,
        weight_ratio_ceiling=8.0,
    )
    assert result["all_cells_guaranteed_at_least_once"] is True
    for name in (
        "coverage_plus_group_topup_only",
        "greedy_donor_balanced_full_coverage_candidate",
    ):
        x = result[name]
        assert x["minimum_group_presentations"] >= 4
        assert x["max_cell_multiplicity"] <= 8
        assert x["total_presentations"] >= 11


def test_geometry_reader_requires_unique_stable_keys(tmp_path: Path):
    db = tmp_path / "bad.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        "create table cells(source text, operator_index integer, donor_id text, "
        "partition text, stable_key text)"
    )
    con.executemany(
        "insert into cells values(?,?,?,?,?)",
        [("S", 1, "D", "reader_fit", "k"), ("S", 1, "D", "reader_fit", "k")],
    )
    con.commit()
    con.close()
    with pytest.raises(RuntimeError, match="stable_key is not unique"):
        m.load_geometry(db, "reader_fit")


def test_cli_has_no_scientific_constraint_defaults():
    source = SCRIPT.read_text(encoding="utf-8")
    for flag in (
        '"--partition", required=True',
        '"--group-floor", type=int, required=True',
        '"--cell-cap", type=int, required=True',
        '"--ess-floor", type=float, required=True',
        '"--weight-ratio-ceiling", type=float, required=True',
    ):
        assert flag in source


def test_committed_full_population_result_if_present():
    path = ROOT / "docs" / "agent" / "v5_anticheat" / "results" / "FULL_POPULATION_COVERAGE_CONDITIONING_AUDIT_V1.json"
    if not path.is_file():
        pytest.skip("full population result not materialized in this checkout")
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert obj["population_cells"] == 4_553_407
    assert obj["donors"] == 104
    assert obj["groups"] == 1_400
    f = obj["full_coverage_feasibility"]
    assert f["importance_weight_ratio_lower_bound_under_cell_cap"] == pytest.approx(67.17245370370371)
    assert f["requested_ratio_ceiling_is_feasible_under_full_coverage_and_cell_cap"] is False
    assert f["minimum_integer_cell_cap_for_requested_ratio_ceiling"] == 34
    b = obj["greedy_donor_balanced_full_coverage_candidate"]
    assert b["importance_ess_fraction"] >= 0.5
    assert b["max_cell_multiplicity"] <= 32
    assert b["minimum_group_presentations"] >= 16
    assert obj["training_authorized"] is False
