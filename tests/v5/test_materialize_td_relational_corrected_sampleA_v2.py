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
    # Real Sample-A freeze schema (every column G6 requires); like the real file, no physical global_row.
    frame = pd.DataFrame({
        "sample": ["A", "A_NATURAL_MIXTURE", "B_COVERAGE_DISCOVERY"],
        "sample_row": [0, 1, 2],
        "source": ["HVS", "HVS", "SEA_AD"],
        "matrix_id": ["HVS::m0", "HVS::m1", "SEA_AD::m2"],
        "operator_index": [0, 1, 2],
        "local_row": [0, 1, 2],
        "donor_id": ["donor_0", "donor_1", "donor_2"],
        "cell_id": ["cell_0", "cell_1", "cell_2"],
    })
    assert "global_row" not in frame.columns
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


def _force_simultaneous_marker_creation(monkeypatch, marker: Path, parties: int = 2):
    """Hold every starter at the marker-creation primitive (Path.write_text or os.open) until all have arrived."""
    import os
    import threading

    barrier = threading.Barrier(parties)
    original_write_text = Path.write_text
    original_open = os.open

    def synchronized_write_text(self, *args, **kwargs):
        if Path(self) == marker:
            barrier.wait(timeout=5)
        return original_write_text(self, *args, **kwargs)

    def synchronized_open(path, *args, **kwargs):
        if Path(path) == marker:
            barrier.wait(timeout=5)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", synchronized_write_text)
    monkeypatch.setattr(os, "open", synchronized_open)


def _race(start, parties: int = 2):
    import threading

    successes, failures = [], []

    def run():
        try:
            successes.append(start())
        except Exception as exc:  # noqa: BLE001 - the test classifies every outcome
            failures.append(exc)

    threads = [threading.Thread(target=run) for _ in range(parties)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    return successes, failures


def _assert_one_winner(m, out, successes, failures):
    assert len(successes) == 1 and len(failures) == 1, (successes, failures)
    assert isinstance(failures[0], RuntimeError) and "already spent" in str(failures[0]), failures
    marker = out / "G6_EXECUTION_START.json"
    assert marker.exists() and sorted(p.name for p in out.iterdir()) == ["G6_EXECUTION_START.json"]
    import json

    rec = json.loads(marker.read_text(encoding="utf-8"))
    assert rec["status"] == "STARTED_NOT_A_PASS" and rec["training_authorized"] is False


def test_g6_start_forced_race_into_nonexistent_directory_has_one_winner(monkeypatch, tmp_path):
    m = load_module()
    out = tmp_path / "new" / "g6"
    _force_simultaneous_marker_creation(monkeypatch, out / "G6_EXECUTION_START.json")
    successes, failures = _race(lambda: m.begin_namespace(out, {"preflight_result_sha256": "abc"}))
    _assert_one_winner(m, out, successes, failures)


def test_g6_start_forced_race_into_existing_empty_directory_has_one_winner(monkeypatch, tmp_path):
    m = load_module()
    out = tmp_path / "g6"
    out.mkdir()
    _force_simultaneous_marker_creation(monkeypatch, out / "G6_EXECUTION_START.json")
    successes, failures = _race(lambda: m.begin_namespace(out, {"preflight_result_sha256": "abc"}))
    _assert_one_winner(m, out, successes, failures)


def test_g6_spent_namespace_is_rejected_as_already_spent_and_marker_is_permanent(tmp_path):
    m = load_module()
    out = tmp_path / "g6"
    marker = m.begin_namespace(out, {"preflight_result_sha256": "abc"})
    raw = marker.read_bytes()
    for _ in range(2):
        try:
            m.begin_namespace(out, {"preflight_result_sha256": "other"})
        except RuntimeError as e:
            assert "already spent" in str(e)
        else:
            raise AssertionError("a spent G6 namespace must never start again")
    assert marker.read_bytes() == raw


def test_nph_historical_row_rejects_duplicate_address_indices_before_materialization():
    m = load_module()
    data = np.asarray([1.25, 2.5, 3.75], dtype=np.float32)
    indptr = np.asarray([0, 3], dtype=np.int64)
    # duplicate inside the replay set, and duplicate outside it (rejected before any dictionary materialization)
    for indices, replay in (([5, 7, 5], {5, 7}), ([5, 9, 9], {5})):
        try:
            m.nph_historical_row(0, data, np.asarray(indices, dtype=np.int64), indptr, replay)
        except RuntimeError as e:
            assert "duplicate" in str(e).lower() and "nph" in str(e).lower()
        else:
            raise AssertionError(f"duplicate NPH52 CSR address indices must fail closed: {indices}")


def test_nph_historical_row_passes_historical_values_through_unmodified():
    m = load_module()
    data = np.asarray([1.25, 0.0, 3.75, 0.1], dtype=np.float32)
    indices = np.asarray([5, 6, 7, 8], dtype=np.int64)
    indptr = np.asarray([0, 4], dtype=np.int64)
    row = m.nph_historical_row(0, data, indices, indptr, {5, 6, 7})
    assert row == {5: float(np.float32(1.25)), 7: float(np.float32(3.75))}


def test_g6_corrected_row_rejects_duplicate_physical_column_indices():
    m = load_module()
    # column 2 is duplicated and unmapped: the inherited decoder silently double-counts it into the library total
    try:
        m.corrected_row(np.asarray([0, 2, 2]), np.asarray([1.0, 1.0, 1.0]), {0: 10}, {10})
    except RuntimeError as e:
        assert "duplicate" in str(e).lower()
    else:
        raise AssertionError("duplicate physical H5AD column indices must fail closed in G6")
