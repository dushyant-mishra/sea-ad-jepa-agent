"""Regression for the real G6 failure discovered by first physical execution.

The authenticated 50K sample freeze does not carry a physical ``global_row`` column.
Historical target-discovery authority requires global row to be the freeze-file row
position, assigned before filtering/merging. Sample B resets ``sample_row`` and must
therefore never be used as a generic CSR row address.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
G6 = ROOT / "scripts" / "v5" / "materialize_td_relational_corrected_sampleA_v2.py"


def load_g6():
    spec = importlib.util.spec_from_file_location("td_g6_global_row_binding", G6)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def row(sample: str, sample_row: int, source: str, *, suffix: str) -> dict:
    """Minimal production-schema row: every physical column G6 dereferences, no global_row."""
    return {
        "sample": sample,
        "sample_row": str(sample_row),
        "source": source,
        "matrix_id": f"{source}::{suffix}",
        "operator_index": "0",
        "local_row": "0",
        "donor_id": f"donor_{suffix}",
        "cell_id": f"cell_{suffix}",
    }


def test_sample_a_derives_global_row_from_freeze_position_without_source_column():
    g6 = load_g6()
    freeze = pd.DataFrame([
        row("A_NATURAL_MIXTURE", 0, "HVS", suffix="a0"),
        row("A_NATURAL_MIXTURE", 1, "NPH52", suffix="a1"),
        row("B_COVERAGE_DISCOVERY", 0, "HVS", suffix="b0"),
        row("B_COVERAGE_DISCOVERY", 1, "SEA_AD", suffix="b1"),
    ])
    assert "global_row" not in freeze.columns

    selected = g6.select_sample_a(freeze, enforce_geometry=False)

    assert selected["sample_row"].astype(int).tolist() == [0, 1]
    assert selected["global_row"].astype(int).tolist() == [0, 1]


def test_global_row_is_assigned_before_filtering_not_from_reset_sample_row():
    g6 = load_g6()
    freeze = pd.DataFrame([
        row("A_NATURAL_MIXTURE", 0, "HVS", suffix="a0"),
        row("B_COVERAGE_DISCOVERY", 0, "SEA_AD", suffix="b0"),
        row("A_NATURAL_MIXTURE", 1, "NPH52", suffix="a1"),
    ])

    selected = g6.select_sample_a(freeze, enforce_geometry=False)

    # The second A row was physically row 2 in the freeze. A generic sample_row->CSR
    # alias would incorrectly call it global row 1.
    assert selected["sample_row"].astype(int).tolist() == [0, 1]
    assert selected["global_row"].astype(int).tolist() == [0, 2]
