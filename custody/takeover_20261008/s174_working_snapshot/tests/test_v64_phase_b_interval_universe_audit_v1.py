from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/audit_phase_b_interval_universe_v1.py"

def _load():
    spec=importlib.util.spec_from_file_location("iv_audit",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_phase_b_interval_discrepancy_is_exactly_deduplication():
    x=_load().audit()
    assert x["phase_a_unique_intervals"]==32117
    assert x["enumeration_rows"]==57
    assert x["enumeration_unique_intervals"]==54
    assert x["enumeration_duplicate_excess"]==3
    assert x["enumeration_unique_already_in_phase_a"]==18
    assert x["combined_unique_intervals"]==32153
    assert x["contract_declared_distinct_intervals"]==32174
    assert x["contract_overcount"]==21
    assert x["overcount_decomposition_matches"] is True
