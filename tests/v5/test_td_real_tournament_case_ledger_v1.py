from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_real_tournament_case_ledger_v1 as L  # noqa: E402


def _rows():
    return [
        {"cell_id":"c1","donor_id":"d1","source":"HVS","operator":"op1","split":"TRAIN","support_state":"MEASURED_POSITIVE","query_id":"q1","neighborhood_id":"n1"},
        {"cell_id":"c2","donor_id":"d2","source":"HVS","operator":"op1","split":"TRAIN","support_state":"MEASURED_ZERO","query_id":"q1","neighborhood_id":"n1"},
        {"cell_id":"c3","donor_id":"d3","source":"HVS","operator":"op1","split":"EVAL","support_state":"MEASURED_POSITIVE","query_id":"q1","neighborhood_id":"n1"},
        {"cell_id":"c4","donor_id":"d4","source":"SEA_AD","operator":"op2","split":"EVAL","support_state":"STRUCTURALLY_UNSUPPORTED","query_id":"q2","neighborhood_id":"n2"},
    ]


def test_case_ledger_is_deterministic_and_preserves_support_semantics():
    a = L.build_case_ledger(_rows())
    b = L.build_case_ledger(list(reversed(_rows())))
    assert a.sha256 == b.sha256
    assert [r.case_id for r in a.rows] == [r.case_id for r in b.rows]
    states = {r.cell_id: r.support_state for r in a.rows}
    assert states["c2"] == "MEASURED_ZERO"
    assert states["c4"] == "STRUCTURALLY_UNSUPPORTED"
    assert next(r for r in a.rows if r.cell_id == "c4").eligible_for_value is False


def test_case_ledger_is_donor_disjoint_across_splits():
    rows = _rows()
    rows.append({**rows[0], "cell_id":"c5", "split":"EVAL"})
    with pytest.raises(L.CaseLedgerError, match="donor appears in multiple splits"):
        L.build_case_ledger(rows)


def test_matched_wrong_cell_partner_is_cross_donor_and_support_safe():
    ledger = L.build_case_ledger(_rows())
    c1 = next(r for r in ledger.rows if r.cell_id == "c1")
    c2 = next(r for r in ledger.rows if r.cell_id == "c2")
    assert c1.matched_wrong_cell_case_id == c2.case_id
    assert c2.matched_wrong_cell_case_id == c1.case_id
    assert c1.donor_id != c2.donor_id
    assert c1.source == c2.source and c1.operator == c2.operator


def test_no_legal_partner_is_not_estimable_not_silently_repaired():
    rows = [_rows()[0], _rows()[3]]
    ledger = L.build_case_ledger(rows)
    c1 = next(r for r in ledger.rows if r.cell_id == "c1")
    assert c1.matched_wrong_cell_case_id is None
    assert c1.matched_wrong_cell_status == "NOT_ESTIMABLE"


def test_duplicate_cell_identity_refuses():
    rows = _rows()
    rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(L.CaseLedgerError, match="duplicate cell_id"):
        L.build_case_ledger(rows)
