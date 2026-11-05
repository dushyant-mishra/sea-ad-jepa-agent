"""Controls for the Macha repair of the V2 journal. FAKE BYTES ONLY.

These check that the repair does not over-correct: low-rank states are not
false alarms, an interrupted success claim is never completed, and crash
cleanup never deletes bytes that exist nowhere else.
"""
from __future__ import annotations

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import (
    PANEL, collapse, commit, kill_write, local_records, open_run, probe,
)


def test_low_rank_but_not_constant_state_commits_without_false_alarm(tmp_path):
    root, backup = open_run(tmp_path)
    v.begin_attempt(root, backup, update=1)
    raw = b"LOW_RANK_STATE"
    tiny = probe(1, raw, cell_centered_energy=1e-30,
                 same_gene_cross_cell_variance=1e-30,
                 same_cell_expression_shuffle_delta=1e-30)
    tiny["cell_distinct_row_count"] = 2
    v.commit_reported_update(root, backup, update=1, state_bytes=raw, probe=tiny)
    report = v.inspect_journal(root, backup)
    assert report["last_reported_probe_pass_checkpoint_update"] == 1
    assert report["last_neurally_healthy_checkpoint_proved"] is False


def test_crashed_commit_is_never_completed_as_a_success(tmp_path, monkeypatch):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    v.begin_attempt(root, backup, update=2)
    name = f"j{len(local_records(root)):08d}.json"
    original = kill_write(monkeypatch, root, name)
    raw = b"GOOD_STATE_U2"
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        v.commit_reported_update(root, backup, update=2, state_bytes=raw,
                                 probe=probe(2, raw))
    monkeypatch.setattr(v, "_write_once", original)
    result = v.recover_interrupted_attempt(root, backup)
    assert result["status"] == "ATTEMPT_ABORTED"
    assert {e["name"] for e in result["quarantined"]} == {
        "u00002.state.bin", "u00002.telemetry.json"}
    v.close_run(root, backup)
    report = v.inspect_journal(root, backup)
    assert report["status"] == "ABORTED_RECOVERED"
    assert report["last_reported_probe_pass_checkpoint_update"] == 1


def test_crash_cleanup_keeps_temp_bytes_that_exist_nowhere_else(tmp_path, monkeypatch):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    name = f"j{len(local_records(root)):08d}.json"
    original = kill_write(monkeypatch, backup, name)
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        v.begin_attempt(root, backup, update=2)
    monkeypatch.setattr(v, "_write_once", original)
    unique = backup / (".uncommitted-" + "f" * 32)
    unique.write_bytes(b"NOT_A_PREFIX_OF_ANY_RETAINED_FILE")
    v.reconcile_one_unmirrored_record(root, backup)
    assert unique.read_bytes() == b"NOT_A_PREFIX_OF_ANY_RETAINED_FILE"
    with pytest.raises(v.JournalRefusal, match="EXTERNAL_CUSTODY_UNCOMMITTED_OR_UNKNOWN"):
        v.inspect_journal(root, backup)


def test_forensic_reader_never_offers_a_collapsed_state_as_a_pass(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    collapse(root, backup, 2)
    with pytest.raises(v.JournalRefusal):
        v.read_forensic_opaque_state(root, backup, update=2)
    with pytest.raises(v.JournalRefusal):
        v.read_forensic_collapsed_state(root, backup, update=1)
    report = v.inspect_journal(root, backup)
    assert report["status"].startswith("TERMINATED_UNEXPECTEDLY")
    assert report["last_reported_probe_pass_checkpoint_update"] == 1


def test_commit_probe_on_another_panel_is_refused_before_any_bytes(tmp_path):
    root, backup = open_run(tmp_path)
    v.begin_attempt(root, backup, update=1)
    raw = b"STATE"
    other = dict(probe(1, raw), probe_panel_sha256="a" * 64)
    with pytest.raises(v.JournalRefusal, match="PROBE_PANEL_NOT_RUN_PANEL"):
        v.commit_reported_update(root, backup, update=1, state_bytes=raw, probe=other)
    assert not list(root.glob("u00001.*"))
    assert PANEL != "a" * 64
