"""Residual repair: G7's G6 prerequisite must semantically validate the G6 materialized NPZ payloads, not only their
hashes and linkage. Software/custody tests only: the synthetic world is a test fixture, not biological evidence.

Every attack starts from a genuine synthetic G6 PASS namespace written by the real G6 entrypoint, replaces the
values or metadata NPZ, and rewrites every corresponding SHA (and the manifest nnz) in G6_RECEIPT.json and
MANIFEST.json so the namespace stays byte-hash self-consistent. The real G7 entrypoint then runs on a world whose
independent physical-H5AD vs S174 cross-check would otherwise PASS; it must refuse before spending its attempt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_synthetic_world as W  # noqa: E402

VALUES = "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz"
META = "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz"
META_FIELDS = ("source", "donor", "operator", "global_row", "cell_id", "source_library", "detected_historical",
               "detected_corrected")
N, A = W.N_SAMPLE_A, W.N_ADDR
REFUSAL = r"G6 (values|metadata) artifact"


def genuine_values(w) -> dict:
    with np.load(w.g6_out / VALUES, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def genuine_meta(w) -> dict:
    with np.load(w.g6_out / META, allow_pickle=True) as z:  # test side only; reads the synthetic fixture
        return {k: (np.asarray(z[k].tolist(), dtype=str) if z[k].dtype == object else z[k].copy()) for k in z.files}


def _edit(path: Path, **updates) -> None:
    rec = json.loads(path.read_text(encoding="utf-8"))
    rec.update(updates)
    path.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def forge(w, *, values=None, meta=None, raw_values: bytes | None = None, raw_meta: bytes | None = None) -> None:
    """Replace G6 artifact contents, then rewrite every SHA so the namespace stays hash self-consistent."""
    ns = w.g6_out
    if values is not None:
        np.savez_compressed(ns / VALUES, **values)
    if raw_values is not None:
        (ns / VALUES).write_bytes(raw_values)
    if meta is not None:
        np.savez_compressed(ns / META, **meta)
    if raw_meta is not None:
        (ns / META).write_bytes(raw_meta)
    vs, ms = W.sha(ns / VALUES), W.sha(ns / META)
    _edit(ns / "G6_RECEIPT.json", values_sha256=vs, meta_sha256=ms)
    manifest = {"values_sha256": vs, "meta_sha256": ms}
    if values is not None and "data" in values:
        manifest["nnz"] = int(np.asarray(values["data"]).size)
    _edit(ns / "MANIFEST.json", **manifest)


def assert_g7_refuses_before_spending(w, monkeypatch, tmp_path) -> None:
    with pytest.raises(RuntimeError, match=REFUSAL):
        W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    out = Path(tmp_path) / "g7_out" / "G7_RECEIPT.json"
    assert not out.exists() and not out.with_name(out.name + ".STARTED_NOT_A_PASS.json").exists()


# ---------------------------------------------------------------- values artifact attacks
def _row_shape_plus_one(g):
    g["shape"] = np.asarray([N + 1, A], dtype=g["shape"].dtype)
    g["indptr"] = np.append(g["indptr"], g["indptr"][-1]).astype(g["indptr"].dtype)


def _set(key, index, value):
    def change(g):
        g[key] = g[key].copy()
        g[key][index] = value
    return change


VALUE_ATTACKS = {
    "shape_wrong_rows": _row_shape_plus_one,
    "shape_wrong_columns_minus": lambda g: g.update(shape=np.asarray([N, A - 1], dtype=g["shape"].dtype)),
    "shape_wrong_columns_plus": lambda g: g.update(shape=np.asarray([N, A + 1], dtype=g["shape"].dtype)),
    "shape_not_two_dimensional": lambda g: g.update(shape=np.asarray([N, A, 1], dtype=g["shape"].dtype)),
    "indptr_non_monotone": _set("indptr", 1, 5),
    "indptr_wrong_length": lambda g: g.update(indptr=g["indptr"][:-1]),
    "indptr_nonzero_start": _set("indptr", 0, 1),
    "index_out_of_range": _set("indices", 0, A),
    "index_negative": _set("indices", 0, -1),
    "data_indices_length_mismatch": lambda g: g.update(data=g["data"][:-1]),
    "indptr_end_inconsistent_with_payload": lambda g: g.update(
        data=np.append(g["data"], np.float32(1.0)).astype(np.float32),
        indices=np.append(g["indices"], 8).astype(g["indices"].dtype)),
    "duplicate_address_in_row": _set("indices", 1, 3),          # row 0 holds addresses (3, 5) -> (3, 3)
    "unsorted_addresses_in_row": lambda g: g.update(indices=np.concatenate([[5, 3], g["indices"][2:]]).astype(g["indices"].dtype)),
    "nan_value": _set("data", 0, np.nan),
    "inf_value": _set("data", 0, np.inf),
    "negative_inf_value": _set("data", 0, -np.inf),
    "value_at_non_replay_address": _set("indices", 0, 0),        # in range, sorted, but not a replay address
    "csc_format": lambda g: g.update(format=np.asarray(b"csc")),
    "extra_payload_key": lambda g: g.update(extra=np.zeros(1)),
    "missing_indptr": lambda g: g.pop("indptr"),
    "data_dtype_float64": lambda g: g.update(data=g["data"].astype(np.float64)),
    "indices_float_dtype": lambda g: g.update(indices=g["indices"].astype(np.float64)),
    "pickled_object_data": lambda g: g.update(data=np.asarray(list(g["data"]), dtype=object)),
}


@pytest.mark.parametrize("attack", sorted(VALUE_ATTACKS))
def test_self_consistent_forged_values_artifact_is_refused(tmp_path, monkeypatch, attack):
    w = W.build_g7_world(tmp_path, monkeypatch)
    g = genuine_values(w)
    VALUE_ATTACKS[attack](g)
    forge(w, values=g)
    assert_g7_refuses_before_spending(w, monkeypatch, tmp_path)


def test_values_artifact_that_is_not_an_npz_is_refused(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    forge(w, raw_values=b"not an npz archive\n")
    assert_g7_refuses_before_spending(w, monkeypatch, tmp_path)


# ---------------------------------------------------------------- metadata artifact attacks
def _swap_rows(m):
    for k in META_FIELDS:
        m[k] = m[k].copy()
        m[k][[0, 1]] = m[k][[1, 0]]


def _meta_set(key, index, value):
    def change(m):
        m[key] = m[key].copy()
        m[key][index] = value
    return change


META_ATTACKS = {
    **{f"missing_{f}": (lambda f: lambda m: m.pop(f))(f) for f in META_FIELDS},
    "all_fields_one_row_short": lambda m: m.update({k: m[k][:-1] for k in META_FIELDS}),
    "one_field_one_row_long": lambda m: m.update(donor=np.append(m["donor"], "donor_x")),
    "row_order_swapped_consistently": _swap_rows,
    "cell_id_changed": _meta_set("cell_id", 0, "h1_cell1"),
    "source_changed": _meta_set("source", 0, "SEA_AD"),
    "donor_changed": _meta_set("donor", 0, "donor_9"),
    "operator_changed": _meta_set("operator", 0, 7),
    "global_row_changed": _meta_set("global_row", 0, 999),
    "global_row_float_dtype": lambda m: m.update(global_row=m["global_row"].astype(np.float64)),
    "pickled_object_cell_id": lambda m: m.update(cell_id=np.asarray(list(m["cell_id"]), dtype=object)),
    "extra_field": lambda m: m.update(extra=np.zeros(N)),
    "nonpositive_source_library": _meta_set("source_library", 0, 0),
    "negative_detected": _meta_set("detected_corrected", 0, -1),
    "nph52_detected_corrected_diverges_from_historical": _meta_set("detected_corrected", 2, 6),  # row 2 is NPH52
}


@pytest.mark.parametrize("attack", sorted(META_ATTACKS))
def test_self_consistent_forged_metadata_artifact_is_refused(tmp_path, monkeypatch, attack):
    w = W.build_g7_world(tmp_path, monkeypatch)
    m = genuine_meta(w)
    META_ATTACKS[attack](m)
    forge(w, meta=m)
    assert_g7_refuses_before_spending(w, monkeypatch, tmp_path)


def test_metadata_artifact_that_is_not_an_npz_is_refused(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    forge(w, raw_meta=b"not an npz archive\n")
    assert_g7_refuses_before_spending(w, monkeypatch, tmp_path)


# ---------------------------------------------------------------- the writer must be validatable without pickle
def test_genuine_g6_artifacts_load_without_pickle(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    for name in (VALUES, META):
        with np.load(w.g6_out / name, allow_pickle=False) as z:
            for k in z.files:
                z[k]


# ---------------------------------------------------------------- independence of the G7 biological cross-check
def test_g7_cross_check_does_not_use_g6_values_as_its_reference(tmp_path, monkeypatch):
    """G6's values are inspected for structure only. A structurally valid, hash-consistent change to them must not
    change G7's physical-H5AD vs S174 comparison (G6 never becomes the reference that proves itself)."""
    w = W.build_g7_world(tmp_path, monkeypatch)
    g = genuine_values(w)
    g["data"] = (g["data"] * np.float32(2.0)).astype(np.float32)
    forge(w, values=g)
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    rec = json.loads(Path(out).read_text(encoding="utf-8"))
    assert rc == 0 and rec["status"] == "PASS_TD_G7_S174_EXACT_OVERLAP"
    assert (rec["natural_overlap_cells"], rec["checked_cell_address_entries"], rec["mismatches"]) == (4, 12, 0)
