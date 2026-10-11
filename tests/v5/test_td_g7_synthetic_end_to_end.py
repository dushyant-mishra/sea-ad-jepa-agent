"""Item 9: the PR #267 protections, preserved and exercised through the REAL G7 V2 entrypoint on the synthetic world
(td_g6g7_synthetic_world), after a genuine synthetic G6 PASS execution.

PASS only for exact natural overlap on every replay address; a single count mismatch is non-success (exit 2);
zero natural overlap is NOT_ESTIMABLE (exit 3) and never opens S174 counts or physical values; a matrix with no
natural overlap is never count-loaded even when others are; immediate-use hashes are recorded; the attempt is spent.
Synthetic inputs only; the G1b authority read from git in production is replaced by a synthetic freeze here."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_synthetic_world as W  # noqa: E402


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_g7_exact_natural_overlap_passes_and_checks_every_replay_address(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    opened = []
    real_loader = w.g7.load_s174_count_matrix
    monkeypatch.setattr(w.g7, "load_s174_count_matrix",
                        lambda path, sha: (opened.append(Path(path).name), real_loader(path, sha))[1])
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    rec = read(out)
    assert rc == 0 and rec["status"] == "PASS_TD_G7_S174_EXACT_OVERLAP"
    assert rec["natural_overlap_cells"] == 4 and rec["mismatches"] == 0
    assert rec["checked_cell_address_entries"] == 4 * len(W.REPLAY)
    per = {m["matrix_id"]: m for m in rec["per_matrix"]}
    assert per["SEA_AD::s2"]["overlap_cells"] == 0 and per["SEA_AD::s2"]["s174_count_values_opened"] is False
    assert sorted(opened) == ["h1.counts.npz", "s1.counts.npz"]  # the zero-overlap shard is never count-loaded
    for mid in ("HVS::h1", "SEA_AD::s1"):
        assert len(per[mid]["s174_meta_sha256_immediate"]) == 64 and len(per[mid]["s174_counts_sha256_immediate"]) == 64
        assert per[mid]["physical_source_sha256_verified"]
    assert rec["s174_verified_shards"] == 4
    assert set(rec["authority_trace"]["g6_execution_sha256"]) == {"receipt", "values", "meta", "manifest", "start_marker"}
    assert out.with_name(out.name + ".STARTED_NOT_A_PASS.json").exists()


def test_g7_single_count_mismatch_is_non_success(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP, perturb=("s1", "s1_cell1", 5, 1))
    rec = read(out)
    assert rc == 2 and rec["status"] == "STOP_TD_G7_S174_CROSSCHECK_MISMATCH" and rec["mismatches"] == 1


def test_g7_mismatch_at_an_implicit_zero_replay_address_is_caught(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    # address 8 is absent (implicit zero) in both sources for h1_cell0; plant it in S174 only
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP, perturb=("h1", "h1_cell0", 8, 2))
    assert rc == 2 and read(out)["mismatches"] == 1


def test_g7_zero_natural_overlap_is_not_estimable_and_never_opens_counts(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)

    def forbidden(*args, **kwargs):
        raise AssertionError("no S174 count or physical value may be opened without natural overlap")

    monkeypatch.setattr(w.g7, "load_s174_count_matrix", forbidden)
    monkeypatch.setattr(w.g7, "open_authenticated_overlap_count_sources", forbidden)
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_NO_OVERLAP)
    rec = read(out)
    assert rc == 3 and rec["status"] == "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
    assert rec["no_overlap_is_not_pass"] is True
    assert all(m["s174_count_values_opened"] is False and m["physical_h5ad_values_opened"] is False
               for m in rec["per_matrix"])


def test_g7_attempt_is_spent_after_a_completed_run(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP, name="first")
    assert rc == 0
    monkeypatch.setattr(sys, "argv", W.g7_argv(w, out, Path(tmp_path) / "s174_first"))
    with pytest.raises(RuntimeError, match="already spent"):
        w.g7.main()


def test_g7_refuses_a_g1b_shard_whose_bytes_changed(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    cache_root = Path(tmp_path) / "s174_tamper"
    freeze, result = W.build_s174_cache(cache_root, W.S174_CELLS_OVERLAP)
    raw = bytearray((cache_root / "x9.counts.npz").read_bytes())
    raw[-1] ^= 1
    (cache_root / "x9.counts.npz").write_bytes(bytes(raw))
    monkeypatch.setattr(w.g7, "load_g1b_authority_from_pass_commit", lambda anchor: (result, freeze, "r", "f"))
    out = Path(tmp_path) / "tamper_out" / "G7_RECEIPT.json"
    monkeypatch.setattr(sys, "argv", W.g7_argv(w, out, cache_root))
    with pytest.raises(RuntimeError, match="hash mismatch"):
        w.g7.main()
    assert not out.exists()
