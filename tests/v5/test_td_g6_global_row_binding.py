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


def test_sample_a_derives_global_row_from_freeze_position_without_source_column():
    g6 = load_g6()
    freeze = pd.DataFrame([
        {"sample": "A_NATURAL_MIXTURE", "sample_row": "0", "source": "HVS"},
        {"sample": "A_NATURAL_MIXTURE", "sample_row": "1", "source": "NPH52"},
        {"sample": "B_COVERAGE_DISCOVERY", "sample_row": "0", "source": "HVS"},
        {"sample": "B_COVERAGE_DISCOVERY", "sample_row": "1", "source": "SEA_AD"},
    ])
    assert "global_row" not in freeze.columns

    selected = g6.select_sample_a(freeze, enforce_geometry=False)

    assert selected["sample_row"].astype(int).tolist() == [0, 1]
    assert selected["global_row"].astype(int).tolist() == [0, 1]


def test_global_row_is_assigned_before_filtering_not_from_reset_sample_row():
    g6 = load_g6()
    freeze = pd.DataFrame([
        {"sample": "A_NATURAL_MIXTURE", "sample_row": "0", "source": "HVS"},
        {"sample": "B_COVERAGE_DISCOVERY", "sample_row": "0", "source": "SEA_AD"},
        {"sample": "A_NATURAL_MIXTURE", "sample_row": "1", "source": "NPH52"},
    ])

    selected = g6.select_sample_a(freeze, enforce_geometry=False)

    # The second A row was physically row 2 in the freeze. A generic sample_row->CSR
    # alias would incorrectly call it global row 1.
    assert selected["sample_row"].astype(int).tolist() == [0, 1]
    assert selected["global_row"].astype(int).tolist() == [0, 2]
