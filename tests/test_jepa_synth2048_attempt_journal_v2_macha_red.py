"""Macha RED tests for the V2 attempt journal (#570). FAKE BYTES ONLY.

No neural model, optimizer step, GPU, controller truth or RNA. Every state is
an opaque byte string and every probe is a simulated, caller-reported receipt.

Each test names the scientific failure it guards against:
  1 loss of the first evidence of collapse
  2 wrong identification of the last healthy state
  3 loss or corruption of checkpoints
  4 false claims of a successful (probe-passing) update
  5 a recovered state silently continued without a verified restart

The helpers adapt to the #570 call signatures so that each RED fails at #570
for the behaviour it names, not because of a missing keyword.
"""
from __future__ import annotations

from hashlib import sha256
import inspect
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_checkpoint_capture_prefreeze_v1 import complete_update

REPO = str(Path(__file__).resolve().parents[1])
PANEL = "1" * 64
U0_METRICS = {
    "cell_centered_energy": 0.25,
    "same_gene_cross_cell_variance": 0.5,
    "same_cell_expression_shuffle_delta": 0.125,
}


def _accepts(fn, name):
    return name in inspect.signature(fn).parameters


def probe(update, raw, **metrics):
    values = dict(U0_METRICS)
    values.update(metrics)
    return {
        "state_update": update,
        "state_payload_sha256": sha256(raw).hexdigest(),
        "probe_panel_sha256": PANEL,
        "operator_homogeneous_eval_mode": True,
        "identical_gene_sets": True,
        "metrics": values,
        "cell_distinct_row_count": 1 if values["cell_centered_energy"] == 0 else 64,
        "probe_cells": 64,
        "nonfinite_values": 0,
        "measurement_origin": "CALLER_REPORTED__NOT_PHYSICALLY_PROVED",
    }


def open_run(tmp_path, horizon=6):
    root, backup = tmp_path / "run", tmp_path / "outside-head"
    kw = dict(run_id="macha-red", horizon=horizon, panel_sha256=PANEL,
              config_sha256="2" * 64, rights_sha256="3" * 64,
              initial_state_bytes=b"U0_STATE")
    if _accepts(v.open_journal, "initial_probe"):
        kw["initial_probe"] = probe(0, b"U0_STATE")
    v.open_journal(root, backup, **kw)
    return root, backup


def commit(root, backup, update):
    raw = f"GOOD_STATE_U{update}".encode()
    v.begin_attempt(root, backup, update=update)
    kw = dict(update=update, state_bytes=raw)
    if _accepts(v.commit_reported_update, "probe"):
        kw["probe"] = probe(update, raw)
    else:
        kw["panel_sha256"] = PANEL
    v.commit_reported_update(root, backup, **kw)
    return raw


def collapse_receipt(update, panel=PANEL, u0=0.25):
    row = complete_update(update)
    row.update(success=False, failure_cause="CELL_CONSTANT", collapse_evidence={
        "metric": "cell_centered_energy", "observed": 0.0, "u0_reference": u0,
        "probe_panel_sha256": panel, "operator_homogeneous_eval_mode": True,
        "identical_gene_sets": True,
    })
    return row


def collapse(root, backup, update):
    raw = f"COLLAPSED_STATE_U{update}".encode()
    v.begin_attempt(root, backup, update=update)
    v.record_collapsed_state(root, backup, update=update, state_bytes=raw,
                             reported_receipt=collapse_receipt(update))
    return raw


def local_records(root):
    return sorted(p.name for p in root.glob("j*.json"))


def kill_write(monkeypatch, directory, name):
    """Simulate the process dying exactly when this file was about to be written."""
    original = v._write_once

    def dying(d, n, raw, maximum):
        if Path(d) == Path(directory).absolute() and n == name:
            raise RuntimeError("SIMULATED_PROCESS_DEATH")
        return original(d, n, raw, maximum)
    monkeypatch.setattr(v, "_write_once", dying)
    return original


def flip_last_byte(path):
    data = bytearray(path.read_bytes())
    data[-1] ^= 0x01
    path.write_bytes(bytes(data))


# ---------------------------------------------------------------- 1, 2, 3

@pytest.mark.parametrize("damaged", ["u00001.state.bin", "u00001.telemetry.json"])
def test_red_damaged_older_checkpoint_must_not_hide_later_collapse_or_last_good(
        tmp_path, damaged):
    root, backup = open_run(tmp_path)
    for u in (1, 2, 3):
        commit(root, backup, u)
    collapse(root, backup, 4)
    v.close_run(root, backup)
    flip_last_byte(root / damaged)
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)
    report = v.inspect_forensic_prefix(root, backup)
    # The journal records after u1 are intact and mirrored outside the run.
    assert report["collapsed_state_updates_nonresumable"] == [4]
    assert report["last_reported_probe_pass_checkpoint_update"] == 3
    assert "STOPPED_COLLAPSED" in report["status"]
    assert report["anomalies"]
    assert v.read_forensic_opaque_state(root, backup, update=3) == b"GOOD_STATE_U3"
    assert v.read_forensic_collapsed_state(root, backup, update=4) == b"COLLAPSED_STATE_U4"
    if damaged.endswith("state.bin"):
        with pytest.raises(v.JournalRefusal):
            v.read_forensic_opaque_state(root, backup, update=1)


@pytest.mark.parametrize("damage", ["remove", "corrupt"])
def test_red_one_lost_or_corrupt_local_record_must_not_hide_later_collapse(
        tmp_path, damage):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    commit(root, backup, 2)
    collapse(root, backup, 3)
    v.close_run(root, backup)
    # j4 is UPDATE_COMMITTED(u2); its outside-run copy is intact.
    target = root / "j00000004.json"
    if damage == "remove":
        target.unlink()
    else:
        flip_last_byte(target)
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)
    report = v.inspect_forensic_prefix(root, backup)
    assert report["collapsed_state_updates_nonresumable"] == [3]
    assert report["last_reported_probe_pass_checkpoint_update"] == 2
    assert "STOPPED_COLLAPSED" in report["status"]
    assert any(a.get("sequence") == 4 for a in report["anomalies"])
    assert v.read_forensic_opaque_state(root, backup, update=2) == b"GOOD_STATE_U2"


@pytest.mark.parametrize("where", ["run", "outside-head"])
@pytest.mark.parametrize("damage", ["remove", "corrupt"])
def test_red_one_damaged_run_lock_copy_must_not_hide_the_whole_run(tmp_path, where, damage):
    """Self-audit round 3: every record carries the run-lock SHA."""
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    collapse(root, backup, 2)
    v.close_run(root, backup)
    target = (root if where == "run" else backup) / "run.lock.json"
    if damage == "remove":
        target.unlink()
    else:
        flip_last_byte(target)
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, backup)
    report = v.inspect_forensic_prefix(root, backup)
    assert "STOPPED_COLLAPSED" in report["status"]
    assert report["collapsed_state_updates_nonresumable"] == [2]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1
    assert v.read_forensic_opaque_state(root, backup, update=1) == b"GOOD_STATE_U1"


def test_red_erasing_both_record_copies_must_not_erase_the_collapse_cause(tmp_path):
    """Self-audit round 2: without a signed external head (owner decision D1)
    the erased records cannot be proved, but the durable cause must stay visible."""
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    collapse(root, backup, 2)
    v.close_run(root, backup)
    for name in local_records(root)[-2:]:          # STATE_COLLAPSED, RUN_CLOSED
        (root / name).unlink()
        (backup / name).unlink()
    report = v.inspect_forensic_prefix(root, backup)
    assert report["status"].startswith("TERMINATED_UNEXPECTEDLY")
    assert report["uncommitted_collapse_evidence_updates"] == [2]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1


# ---------------------------------------------------------------- 4

def test_red_commit_without_a_state_bound_probe_must_be_refused(tmp_path):
    root, backup = open_run(tmp_path)
    v.begin_attempt(root, backup, update=1)
    with pytest.raises(v.JournalRefusal):
        v.commit_reported_update(root, backup, update=1,
                                 state_bytes=b"NEVER_PROBED", panel_sha256=PANEL)
    assert not list(root.glob("u00001.*"))


def test_red_commit_whose_own_probe_shows_collapse_must_be_refused(tmp_path):
    if not _accepts(v.commit_reported_update, "probe"):
        pytest.fail("A commit cannot carry any measurement, so the journal writes "
                    "NOT_COLLAPSED_ONLY for a state that was never probed")
    root, backup = open_run(tmp_path)
    v.begin_attempt(root, backup, update=1)
    raw = b"STATE_U1"
    bad = [
        probe(1, raw, cell_centered_energy=0.0),
        probe(1, raw, same_gene_cross_cell_variance=0.0),
        probe(1, raw, same_cell_expression_shuffle_delta=0.0),
        dict(probe(1, raw), cell_distinct_row_count=1),   # naive float32 energy
        dict(probe(1, raw), nonfinite_values=3),
        dict(probe(1, raw), state_payload_sha256="e" * 64),
        dict(probe(1, raw), state_update=0),
        dict(probe(1, raw), probe_panel_sha256="f" * 64),
    ]
    for receipt in bad:
        with pytest.raises(v.JournalRefusal):
            v.commit_reported_update(root, backup, update=1, state_bytes=raw,
                                     probe=receipt)
    assert not list(root.glob("u00001.*"))


def test_red_initial_state_must_be_probed_before_it_counts_as_a_pass(tmp_path):
    root, backup = tmp_path / "run", tmp_path / "outside-head"
    with pytest.raises(v.JournalRefusal):
        v.open_journal(root, backup, run_id="unprobed", horizon=2,
                       panel_sha256=PANEL, config_sha256="2" * 64,
                       rights_sha256="3" * 64, initial_state_bytes=b"U0_STATE")


@pytest.mark.parametrize("bad", [{"panel": "b" * 64}, {"u0": 0.3}])
def test_red_collapse_must_be_measured_on_the_run_panel_against_run_u0(tmp_path, bad):
    root, backup = open_run(tmp_path)
    v.begin_attempt(root, backup, update=1)
    with pytest.raises(v.JournalRefusal):
        v.record_collapsed_state(root, backup, update=1, state_bytes=b"S",
                                 reported_receipt=collapse_receipt(1, **bad))


# ---------------------------------------------------------------- crashes

def test_red_crash_between_link_and_unlink_must_not_strand_collapse_record(
        tmp_path, monkeypatch):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    name = f"j{len(local_records(root)) + 1:08d}.json"   # after BEGIN(2)
    original = kill_write(monkeypatch, backup, name)
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        collapse(root, backup, 2)
    monkeypatch.setattr(v, "_write_once", original)
    # The local record was linked; the temp name was never unlinked.
    os.link(root / name, root / (".uncommitted-" + "c" * 32))
    before = (root / name).read_bytes()
    v.reconcile_one_unmirrored_record(root, backup)
    assert (root / name).read_bytes() == before == (backup / name).read_bytes()
    report = v.inspect_journal(root, backup)
    assert report["collapsed_state_updates_nonresumable"] == [2]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1
    assert v.close_run(root, backup)["status"] == "STOPPED_COLLAPSED"


@pytest.mark.parametrize("twin", [False, True])
def test_red_crash_after_collapse_evidence_is_durable_must_keep_typed_collapse(
        tmp_path, monkeypatch, twin):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    name = f"j{len(local_records(root)) + 1:08d}.json"
    original = kill_write(monkeypatch, root, name)
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        collapse(root, backup, 2)
    monkeypatch.setattr(v, "_write_once", original)
    assert (root / "u00002.state.bin").read_bytes() == b"COLLAPSED_STATE_U2"
    if twin:
        os.link(root / "u00002.state.bin", root / (".uncommitted-" + "d" * 32))
    recovered = v.recover_interrupted_attempt(root, backup)
    assert recovered["status"] == "STATE_COLLAPSED"
    report = v.inspect_journal(root, backup)
    assert report["collapsed_state_updates_nonresumable"] == [2]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1
    assert v.read_forensic_collapsed_state(root, backup, update=2) == b"COLLAPSED_STATE_U2"
    assert v.close_run(root, backup)["status"] == "STOPPED_COLLAPSED"


def test_red_crash_during_outside_copy_must_leave_a_closable_run(tmp_path, monkeypatch):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    name = f"j{len(local_records(root)):08d}.json"   # BEGIN(2)
    original = kill_write(monkeypatch, backup, name)
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        v.begin_attempt(root, backup, update=2)
    monkeypatch.setattr(v, "_write_once", original)
    raw = (root / name).read_bytes()
    (backup / (".uncommitted-" + "e" * 32)).write_bytes(raw[: len(raw) // 2])
    v.reconcile_one_unmirrored_record(root, backup)
    assert v.recover_interrupted_attempt(root, backup)["status"] == "ATTEMPT_ABORTED"
    assert v.close_run(root, backup)["status"] == "ABORTED_RECOVERED"
    assert v.inspect_journal(root, backup)["status"] == "ABORTED_RECOVERED"


def test_red_crash_during_recovery_must_not_strand_or_hide_collapse_cause(
        tmp_path, monkeypatch):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    v.begin_attempt(root, backup, update=2)
    # The typed collapse cause became durable; the process died before the state.
    cause_bytes = v._json(collapse_receipt(2))
    (root / "u00002.telemetry.json").write_bytes(cause_bytes)
    name = f"j{len(local_records(root)):08d}.json"   # the ABORTED record
    original = kill_write(monkeypatch, root, name)
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        v.recover_interrupted_attempt(root, backup)
    monkeypatch.setattr(v, "_write_once", original)
    result = v.recover_interrupted_attempt(root, backup)
    assert result["status"] == "ATTEMPT_ABORTED"
    kept = [p.read_bytes() for p in (root / "quarantine").iterdir()]
    assert cause_bytes in kept
    v.close_run(root, backup)
    report = v.inspect_journal(root, backup)
    assert report["uncommitted_collapse_evidence_updates"] == [2]
    assert report["last_reported_probe_pass_checkpoint_update"] == 1


# ---------------------------------------------------------------- 5

def test_red_a_fresh_process_must_not_continue_an_interrupted_run(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v\n"
        "try:\n"
        "    v.begin_attempt(Path(sys.argv[1]), Path(sys.argv[2]), update=2)\n"
        "except v.JournalRefusal as exc:\n"
        "    print('REFUSED', exc)\n"
        "    sys.exit(3)\n"
        "print('CONTINUED_WITHOUT_VERIFIED_RESTART')\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO + os.pathsep + env.get("PYTHONPATH", "")
    run = subprocess.run([sys.executable, "-c", code, str(root), str(backup)],
                         cwd=REPO, env=env, capture_output=True, text=True,
                         timeout=120)
    assert run.returncode == 3, run.stdout + run.stderr
    assert "RESUME_NOT_AUTHORIZED" in run.stdout
    # The process that opened the run may still continue it.
    commit(root, backup, 2)
    assert v.inspect_journal(root, backup)["last_reported_probe_pass_checkpoint_update"] == 2
