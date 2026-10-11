"""Item 8: the V2 G6/G7 value path keeps strict raw-count semantics (fractional, negative, NaN and infinite counts
are rejected) and contains no rounding or truncation. Synthetic inputs only; no expression data is read."""
import ast
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
V5 = ROOT / "scripts" / "v5"
V2_VALUE_PATH = (
    V5 / "td_relational_value_read_v2_common.py",
    V5 / "materialize_td_relational_corrected_sampleA_v2.py",
    V5 / "audit_td_relational_g7_s174_overlap_v2.py",
)
BAD = (1.5, -1.0, float("nan"), float("inf"), float("-inf"))
ROUNDING = {"round", "around", "rint", "floor", "ceil", "trunc", "fix"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _call_name(node):
    func = node.func
    return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""


def _integrality_comparators(tree):
    """floor(x) used only as the comparator in equal(x, floor(x)) is an exactness test, not a value transform."""
    exempt = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) == "equal" and len(node.args) == 2:
            left, right = node.args
            if (isinstance(right, ast.Call) and _call_name(right) == "floor" and len(right.args) == 1
                    and ast.dump(right.args[0]) == ast.dump(left)):
                exempt.add(id(right))
    return exempt


def test_no_rounding_or_truncating_call_anywhere_in_the_v2_value_path():
    offenders = []
    for path in V2_VALUE_PATH:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        exempt = _integrality_comparators(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_name(node) in ROUNDING and id(node) not in exempt:
                offenders.append(f"{path.name}:{node.lineno}:{_call_name(node)}")
    assert offenders == []


def test_rounding_scanner_catches_a_planted_round():
    planted = ast.parse("x = round(v)\ny = np.around(v)\nz = np.equal(v, np.floor(v))\nw = np.floor(v)\n")
    exempt = _integrality_comparators(planted)
    hits = [_call_name(n) for n in ast.walk(planted)
            if isinstance(n, ast.Call) and _call_name(n) in ROUNDING and id(n) not in exempt]
    assert sorted(hits) == ["around", "floor", "round"]


@pytest.mark.parametrize("bad", BAD)
def test_g6_and_g7_physical_row_decoders_reject_invalid_raw_counts(bad):
    g6 = load("g6_strict", V5 / "materialize_td_relational_corrected_sampleA_v2.py")
    g7 = load("g7_strict", V5 / "audit_td_relational_g7_s174_overlap_v2.py")
    for module in (g6, g7):
        with pytest.raises(RuntimeError):
            module.corrected_row(np.asarray([0, 1]), np.asarray([2.0, bad]), {0: 10}, {10})


@pytest.mark.parametrize("bad", BAD)
def test_s174_reference_rows_and_payload_reject_invalid_raw_counts(bad):
    g7 = load("g7_strict_ref", V5 / "audit_td_relational_g7_s174_overlap_v2.py")

    class Row:
        indices = np.asarray([10, 20], dtype=np.int64)
        data = np.asarray([2.0, bad], dtype=np.float64)

    class X:
        def getrow(self, _):
            return Row()

    with pytest.raises(RuntimeError):
        g7.sparse_row_dict(X(), 0, {10, 20})
    with pytest.raises(RuntimeError):
        g7.validate_s174_payload(np.asarray([bad]), np.asarray([0]), np.asarray([0, 1]), (1, 41_238))


@pytest.mark.parametrize("field", ["source_library", "detected", "global_row"])
@pytest.mark.parametrize("bad", BAD)
def test_historical_td50_sentinels_are_never_truncated(monkeypatch, field, bad):
    g6 = load("g6_strict_td50", V5 / "materialize_td_relational_corrected_sampleA_v2.py")
    monkeypatch.setattr(g6, "N_SAMPLE_A", 3)
    payload = {"global_row": np.asarray([0.0, 1.0, 2.0]), "source_library": np.asarray([100.0, 200.0, 300.0]),
               "detected": np.asarray([10.0, 20.0, 30.0])}
    library, detected = g6.sentinel_maps({"HVS": payload})
    assert library == {0: 100, 1: 200, 2: 300} and detected == {0: 10, 1: 20, 2: 30}
    payload[field] = payload[field].copy()
    payload[field][1] = bad
    with pytest.raises(RuntimeError):
        g6.sentinel_maps({"HVS": payload})
