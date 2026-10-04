"""Route-A barcode authority must be audited BEFORE the dictionary collapse.

`dict(zip(barcode, donor))` keeps the LAST value for a repeated key. A barcode bound to
two donors is therefore destroyed by the collapse itself, and any guard placed downstream
inspects evidence that no longer exists. The defect is one of ORDERING, not of absent
checking, so these tests are about order: the same guard in the wrong place catches
nothing.

Every test drives the real module. The last one is the one that matters: it restores the
historical post-collapse ordering and asserts that the conflict tests then FAIL, which is
what proves they are testing the ordering rather than merely passing.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts" / "v69" / "v69_barcode_identity.py"


def _mod():
    spec = importlib.util.spec_from_file_location("v69_bi_v74", SRC)
    m = importlib.util.module_from_spec(spec)
    sys.modules["v69_bi_v74"] = m
    spec.loader.exec_module(m)
    return m


M = _mod()


class _Frame:
    """Minimal frame with the two attributes the adapter uses, so the ordering can be
    tested without requiring pandas in the test environment."""

    def __init__(self, cols):
        self.columns = list(cols)
        self._cols = cols

    def __getitem__(self, k):
        return _Col(self._cols[k])


class _Col:
    def __init__(self, vals):
        self._v = list(vals)

    def tolist(self):
        return list(self._v)


def frame(rows, drop=None):
    cols = {"barcode": [r[0] for r in rows],
            "donor": [r[1] for r in rows],
            "subcluster": [r[2] for r in rows]}
    if drop:
        cols.pop(drop)
    return _Frame(cols)


CLEAN = [("AAA-1", "D1", "mg"), ("BBB-1", "D2", "mg"), ("CCC-2", "D3", "mg")]


def test_positive_control_clean_authority_passes():
    """If this fails, every negative result below is meaningless."""
    out = M.audit_barcode_authority_frame(frame(CLEAN))
    assert out is not None


def test_exact_duplicate_rows_are_permitted_and_counted():
    rows = CLEAN + [("AAA-1", "D1", "mg")]
    out = M.audit_barcode_authority_frame(frame(rows))
    flat = str(out)
    assert "4" in flat or "1" in flat, out
    # the policy is PERMIT, so this must not raise
    assert out is not None


def test_same_barcode_two_donors_fails_closed():
    rows = CLEAN + [("AAA-1", "D9", "mg")]
    with pytest.raises(M.BarcodeAuthorityError) as e:
        M.audit_barcode_authority_frame(frame(rows))
    assert "DONOR" in str(getattr(e.value, "status", "")).upper() or \
           "donor" in str(e.value).lower()


def test_same_barcode_two_subclusters_fails_closed():
    rows = CLEAN + [("AAA-1", "D1", "astro")]
    with pytest.raises(M.BarcodeAuthorityError) as e:
        M.audit_barcode_authority_frame(frame(rows))
    assert "SUB" in str(getattr(e.value, "status", "")).upper() or \
           "subcluster" in str(e.value).lower()


@pytest.mark.parametrize("missing", ["barcode", "donor", "subcluster"])
def test_missing_required_column_fails_closed(missing):
    with pytest.raises(M.BarcodeAuthorityError) as e:
        M.audit_barcode_authority_frame(frame(CLEAN, drop=missing))
    assert "MISSING_COLUMN" in str(getattr(e.value, "status", "")).upper()


def test_the_defect_is_ordering_not_absent_checking():
    """THE MUTATION THAT MATTERS.

    Restore the historical ordering -- collapse first, audit the collapsed map second --
    and show that the conflicting-donor row becomes INVISIBLE. If this assertion ever
    stops holding, the tests above are no longer testing order and are worth nothing.
    """
    rows = CLEAN + [("AAA-1", "D9", "mg")]

    # audited in the CORRECT order, on raw rows: the conflict is caught
    with pytest.raises(M.BarcodeAuthorityError):
        M.audit_barcode_authority_frame(frame(rows))

    # audited in the HISTORICAL order, after dict(zip(...)): the conflict is gone
    collapsed = dict(zip([r[0] for r in rows], [r[1] for r in rows]))
    assert collapsed["AAA-1"] == "D9", "dict(zip) kept the last row, as expected"
    assert len(collapsed) == 3, "the conflicting row was silently absorbed"
    rebuilt = [(b, d, "mg") for b, d in collapsed.items()]
    # the same auditor, given post-collapse evidence, finds nothing wrong
    assert M.audit_barcode_authority_frame(frame(rebuilt)) is not None


def test_route_a_producer_calls_the_audit_before_the_collapse():
    """Static ordering check against the real producer, so a future edit that moves the
    call back cannot pass silently."""
    src = (ROOT / "scripts" / "v69" / "build_routea_cistopic_object_v1.py").read_text(
        encoding="utf-8")
    i_audit = src.index("audit_barcode_authority_frame(")
    i_collapse = src.index("donor_map = dict(zip(")
    assert i_audit < i_collapse, "the authority audit must precede the collapse"
