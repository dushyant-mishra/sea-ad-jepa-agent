from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "v5"
sys.path.insert(0, str(SCRIPTS))


def test_estimability_requires_five_neighbors_and_frozen_donor_support_without_calling_zero_donors_failures():
    module_path = SCRIPTS / "td_relational_successor_estimability_v1.py"
    assert module_path.is_file(), "relational successor estimability router not implemented"
    E = importlib.import_module("td_relational_successor_estimability_v1")

    neighbor_counts = {
        "D1": [5, 6, 7],
        "D2": [5, 5, 5],
        "D3": [8, 7, 6],
        "D4": [5, 9, 5],
        "D5": [6, 6, 6],
        "D6_ZERO_TRUTH": [],
    }
    result = E.assess_relational_stratum_estimability(
        neighbor_counts_by_donor=neighbor_counts,
        min_neighbors=5,
        min_recurring_donors=5,
        min_estimable_focal_cells_per_donor=3,
    )
    assert result.status == "PASS_TO_TEST"
    assert result.eligible_donors == ("D1", "D2", "D3", "D4", "D5")
    assert "D6_ZERO_TRUTH" not in result.failed_donors

    neighbor_counts["D5"] = [4, 4, 4]
    result = E.assess_relational_stratum_estimability(
        neighbor_counts_by_donor=neighbor_counts,
        min_neighbors=5,
        min_recurring_donors=5,
        min_estimable_focal_cells_per_donor=3,
    )
    assert result.status == "NOT_ESTIMABLE"
    assert result.reason == "INSUFFICIENT_RECURRENT_DONOR_SUPPORT"
