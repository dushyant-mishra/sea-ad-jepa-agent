"""Item 5: G7 requires a genuine, complete, same-authority G6 PASS execution, not merely a JSON object with the right
status and authority trace. The positive control is a real G6 run on the synthetic world; every negative corrupts one
piece of that genuine execution. Synthetic inputs only."""
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_synthetic_world as W  # noqa: E402

VALUES = "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz"
META = "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz"


def load(w):
    return w.g7.load_g6_pass_receipt(w.g6_receipt, W.g7_expected_trace(w), **W.g7_prerequisite_inputs(w))


def edit_json(path: Path, change) -> None:
    rec = json.loads(path.read_text(encoding="utf-8"))
    change(rec)
    path.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def flip_last_byte(path: Path) -> None:
    raw = bytearray(path.read_bytes())
    raw[-1] ^= 1
    path.write_bytes(bytes(raw))


def test_genuine_g6_pass_execution_is_accepted_and_its_trace_matches_g7s_own_expectation(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    rec = load(w)
    assert rec["status"] == "PASS_TD_G6_SOURCE_LIBRARY_EXACT"
    receipt = json.loads(w.g6_receipt.read_text(encoding="utf-8"))
    assert receipt["authority_trace"] == W.g7_expected_trace(w)


def test_fabricated_minimal_pass_receipt_is_refused(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    fake_dir = Path(tmp_path) / "fabricated"
    fake_dir.mkdir()
    fake = fake_dir / "G6_RECEIPT.json"
    fake.write_text(json.dumps({
        "schema": "JEPA_TD_RELATIONAL_G6_RECEIPT_V2", "status": "PASS_TD_G6_SOURCE_LIBRARY_EXACT",
        "authority_trace": W.g7_expected_trace(w), "biological_replay_authorized": False,
        "target_selection_authorized": False, "td60_authorized": False, "training_authorized": False}) + "\n",
        encoding="utf-8")
    with pytest.raises(RuntimeError):
        w.g7.load_g6_pass_receipt(fake, W.g7_expected_trace(w), **W.g7_prerequisite_inputs(w))


@pytest.mark.parametrize("name", [VALUES, META, "MANIFEST.json", "G6_EXECUTION_START.json"])
def test_missing_g6_artifact_is_refused(tmp_path, monkeypatch, name):
    w = W.build_g7_world(tmp_path, monkeypatch)
    (w.g6_out / name).unlink()
    with pytest.raises(RuntimeError):
        load(w)


@pytest.mark.parametrize("name", [VALUES, META])
def test_altered_g6_artifact_bytes_are_refused(tmp_path, monkeypatch, name):
    w = W.build_g7_world(tmp_path, monkeypatch)
    flip_last_byte(w.g6_out / name)
    with pytest.raises(RuntimeError):
        load(w)


@pytest.mark.parametrize("change", [
    lambda r: r.update(status="STARTED_AND_PASSED"),
    lambda r: r.update(schema="JEPA_TD_RELATIONAL_G6_EXECUTION_START_V0"),
    lambda r: r["authority_trace"].update(owner_decision_sha256="0" * 64),
    lambda r: r.update(training_authorized=True),
], ids=["status", "schema", "trace", "flag"])
def test_wrong_start_marker_is_refused(tmp_path, monkeypatch, change):
    w = W.build_g7_world(tmp_path, monkeypatch)
    edit_json(w.g6_out / "G6_EXECUTION_START.json", change)
    with pytest.raises(RuntimeError):
        load(w)


@pytest.mark.parametrize("change", [
    lambda r: r.update(values_sha256="0" * 64),
    lambda r: r.update(meta_sha256="0" * 64),
    lambda r: r.update(values_path="OTHER.npz"),
    lambda r: r.update(g6_receipt="OTHER.json"),
    lambda r: r.update(status="MATERIALIZED_G6_V1"),
    lambda r: r["authority_trace"].update(g6_script_sha256="0" * 64),
    lambda r: r["input_authority_hashes"].update(provenance_sha256="0" * 64),
    lambda r: r.update(verified_source_h5ad_sha256={}),
], ids=["values_sha", "meta_sha", "values_path", "receipt_name", "status", "trace", "inputs", "sources"])
def test_mismatched_manifest_is_refused(tmp_path, monkeypatch, change):
    w = W.build_g7_world(tmp_path, monkeypatch)
    edit_json(w.g6_out / "MANIFEST.json", change)
    with pytest.raises(RuntimeError):
        load(w)


@pytest.mark.parametrize("change", [
    lambda r: r["authority_trace"].update(owner_decision_sha256="0" * 64),
    lambda r: r["input_authority_hashes"].update(sample_freeze_sha256="0" * 64),
    lambda r: r["input_authority_hashes"]["historical_csr_sha256"].update({"data.npy": "0" * 64}),
    lambda r: r.update(nph52_authenticated_historical_passthrough_rows=r.get(
        "nph52_authenticated_historical_passthrough_rows", 0) + 1),
    lambda r: r.update(total_sample_a_rows=r.get("total_sample_a_rows", 0) - 1),
    lambda r: r.update(source_library_exact_rows=r.get("total_sample_a_rows")),
    lambda r: r.update(values_sha256="0" * 64),
    lambda r: r.update(td60_authorized=True),
], ids=["trace", "inputs", "hist_csr", "nph_rows", "total_rows", "old_all_rows_claim", "values_sha", "flag"])
def test_corrupted_g6_receipt_is_refused(tmp_path, monkeypatch, change):
    w = W.build_g7_world(tmp_path, monkeypatch)
    edit_json(w.g6_receipt, change)
    with pytest.raises(RuntimeError):
        load(w)


def test_wrong_expected_authority_trace_is_refused(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    trace = W.g7_expected_trace(w)
    trace["mapping_receipt_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="same"):
        w.g7.load_g6_pass_receipt(w.g6_receipt, trace, **W.g7_prerequisite_inputs(w))


def test_foreign_file_in_the_g6_namespace_is_refused(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    (w.g6_out / "notes.txt").write_text("x\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        load(w)


def test_g6_execution_copied_without_its_start_marker_is_refused(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    copy = Path(tmp_path) / "copied"
    shutil.copytree(w.g6_out, copy)
    (copy / "G6_EXECUTION_START.json").unlink()
    with pytest.raises(RuntimeError):
        w.g7.load_g6_pass_receipt(copy / "G6_RECEIPT.json", W.g7_expected_trace(w), **W.g7_prerequisite_inputs(w))
