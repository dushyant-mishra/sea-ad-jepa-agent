"""The REAL G6 V2 entrypoint, end to end, on a tiny synthetic world (td_g6g7_synthetic_world).

Item 7: the G6 receipt reports HVS/SEA physically reread and source-library verified rows separately from NPH52
authenticated historical pass-through rows, and never claims all Sample-A rows were physically reread.
Also preserved: exact materialized values, a spent namespace, and a library mismatch STOP that keeps its marker.
Synthetic inputs only; no real authorization, owner decision or expression data."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_synthetic_world as W  # noqa: E402

G6_FILES = {"G6_EXECUTION_START.json", "G6_RECEIPT.json", "MANIFEST.json",
            "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz", "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz"}


def receipt(w):
    return json.loads((w.g6_out / "G6_RECEIPT.json").read_text(encoding="utf-8"))


def test_g6_end_to_end_materializes_exact_values_on_the_synthetic_world(tmp_path, monkeypatch):
    w = W.build_g6_world(tmp_path, monkeypatch)
    assert W.run_g6(w, monkeypatch) == 0
    assert {p.name for p in w.g6_out.iterdir()} == G6_FILES
    rec = receipt(w)
    assert rec["status"] == "PASS_TD_G6_SOURCE_LIBRARY_EXACT"
    values = sparse.load_npz(w.g6_out / "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz").tocoo()
    got = {(int(r), int(c)): np.float32(v) for r, c, v in zip(values.row, values.col, values.data)}
    assert got == W.expected_values()
    with np.load(w.g6_out / "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz", allow_pickle=True) as meta:
        assert meta["source_library"].tolist() == [W.library(sr) for sr in range(W.N_SAMPLE_A)]
        assert meta["cell_id"].tolist() == [W.cell_id(sr) for sr in range(W.N_SAMPLE_A)]
    assert rec["values_sha256"] == W.sha(w.g6_out / "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz")


def test_g6_receipt_separates_physical_reread_from_nph52_passthrough(tmp_path, monkeypatch):
    w = W.build_g6_world(tmp_path, monkeypatch)
    assert W.run_g6(w, monkeypatch) == 0
    rec = receipt(w)
    physical = W.SOURCE_COUNTS["HVS"] + W.SOURCE_COUNTS["SEA_AD"]
    assert rec["hvs_sea_physically_reread_source_library_verified_rows"] == physical
    assert rec["nph52_authenticated_historical_passthrough_rows"] == W.SOURCE_COUNTS["NPH52"]
    assert rec["total_sample_a_rows"] == W.N_SAMPLE_A == physical + W.SOURCE_COUNTS["NPH52"]
    assert "source_library_exact_rows" not in rec  # never claim every Sample-A row was physically reread
    assert "not independently" in rec["source_library_verification_scope"]


def test_production_coverage_is_23690_reread_plus_1310_passthrough():
    g6 = W.load_script(W.G6_SCRIPT, "td_g6_coverage_constants")
    assert g6.SOURCE_COUNTS["HVS"] + g6.SOURCE_COUNTS["SEA_AD"] == 23_690
    assert g6.SOURCE_COUNTS["NPH52"] == 1_310
    assert g6.N_SAMPLE_A == 25_000


def test_g6_library_mismatch_stops_and_keeps_the_spent_marker(tmp_path, monkeypatch):
    w = W.build_g6_world(tmp_path, monkeypatch, library_offsets={4: 1})
    with pytest.raises(RuntimeError, match="source-library mismatch"):
        W.run_g6(w, monkeypatch)
    rec = receipt(w)
    assert rec["status"] == "STOP_TD_G6_SOURCE_LIBRARY_MISMATCH" and rec["mismatch_count"] == 1
    assert (w.g6_out / "G6_EXECUTION_START.json").exists()
    with pytest.raises(RuntimeError, match="already spent"):
        W.run_g6(w, monkeypatch)
