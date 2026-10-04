from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/audit_phase_b_t6_t7_references_v1.py"

def _load():
    spec=importlib.util.spec_from_file_location("t6t7",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_all_r3_enumeration_rows_resolve_to_frozen_t7_reference():
    x=_load().audit()
    assert x["t7_records"]==21
    assert x["r3_enum_rows"]==17
    assert x["r3_enum_rows_with_reference_id"]==17
    assert x["unresolved_reference_ids"]==[]
    assert x["semantic_mismatches"]==[]
    assert x["all_r3_enum_rows_resolve_exactly"] is True
