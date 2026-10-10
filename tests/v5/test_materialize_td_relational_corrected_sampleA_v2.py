import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "materialize_td_relational_corrected_sampleA_v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_g6_v2", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sample_a_selection_uses_frozen_label_not_literal_A():
    m = load_module()
    frame = pd.DataFrame({
        "sample": ["A", "A_NATURAL_MIXTURE", "B_COVERAGE_DISCOVERY"],
        "sample_row": [0, 1, 2],
        "source": ["HVS", "HVS", "SEA_AD"],
    })
    got = m.select_sample_a(frame, enforce_geometry=False)
    assert got["sample"].tolist() == ["A_NATURAL_MIXTURE"]


def test_corrected_row_strict_integer_and_whole_row_total_before_filter():
    m = load_module()
    indices = np.asarray([0, 1, 2], dtype=np.int64)
    values = np.asarray([2.0, 3.0, 5.0], dtype=np.float64)
    row, total = m.corrected_row(indices, values, {0: 10, 1: 20}, {10})
    assert row == {10: 2}
    assert total == 10


def test_corrected_row_rejects_fractional_nonfinite_negative():
    m = load_module()
    for bad in (1.5, float("nan"), float("inf"), -1.0):
        try:
            m.corrected_row(np.asarray([0]), np.asarray([bad]), {0: 10}, {10})
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"G6 raw value must fail closed: {bad!r}")


def test_output_namespace_is_immutable(tmp_path):
    m = load_module()
    out = tmp_path / "g6"
    out.mkdir()
    (out / "partial.txt").write_text("partial\n", encoding="utf-8")
    try:
        m.assert_empty_output(out)
    except RuntimeError as e:
        assert "immutable" in str(e).lower() or "empty" in str(e).lower()
    else:
        raise AssertionError("partial G6 namespace must never be reused")


def test_begin_namespace_spends_even_initially_empty_directory(tmp_path):
    m = load_module()
    out = tmp_path / "g6"
    out.mkdir()
    marker = m.begin_namespace(out, {"preflight_result_sha256": "abc"})
    assert marker.name == "G6_EXECUTION_START.json"
    assert marker.exists()
    try:
        m.assert_empty_output(out)
    except RuntimeError:
        pass
    else:
        raise AssertionError("a started G6 attempt must permanently spend its namespace")


def test_v2_output_schemas_are_distinct_from_v1():
    m = load_module()
    assert m.G6_RECEIPT_SCHEMA == "JEPA_TD_RELATIONAL_G6_RECEIPT_V2"
    assert m.CACHE_SCHEMA == "JEPA_TD_RELATIONAL_CORRECTED_SAMPLE_A_CACHE_V2"
    assert not m.G6_RECEIPT_SCHEMA.endswith("V1")
    assert not m.CACHE_SCHEMA.endswith("V1")


def test_historical_csr_hash_drift_is_rejected(tmp_path):
    m = load_module()
    root = tmp_path / "csr"
    root.mkdir()
    for name in m.HIST_CSR_SHA:
        (root / name).write_bytes(b"wrong")
    try:
        m.verify_historical_csr(root)
    except RuntimeError as e:
        assert "historical csr authority mismatch" in str(e).lower()
    else:
        raise AssertionError("historical NPH CSR drift must fail")


def test_source_record_sha_helper_is_used_without_size_only_acceptance(tmp_path):
    m = load_module()
    p = tmp_path / "source.h5ad"
    p.write_bytes(b"abcdef")
    rec = {"bytes": 6, "sha256": hashlib.sha256(b"abcdef").hexdigest()}
    assert m.common.verify_source_file(p, rec) == rec["sha256"]
    p.write_bytes(b"abcdeg")
    try:
        m.common.verify_source_file(p, rec)
    except RuntimeError:
        pass
    else:
        raise AssertionError("same-size changed H5AD must fail before G6 value access")


def test_input_authority_ledger_includes_historical_nph_and_td50_hashes():
    m = load_module()
    assert m.INPUT_AUTHORITY_HASHES["historical_csr_sha256"] == m.HIST_CSR_SHA
    assert m.INPUT_AUTHORITY_HASHES["td50_member_sha256"] == m.TD50_SHA
    assert m.INPUT_AUTHORITY_HASHES["sample_freeze_sha256"] == m.EXPECTED_SAMPLE_FREEZE_SHA
