"""Macha integration tests for #575 + #576 + #577/#579/#580 + #578 + #581.

Synthetic only: fake opaque bytes and tiny fake CPU tensors with manually set
Adam slots. No forward, backward, optimizer step, EMA update, GPU, RNA or
controller truth. Each test crosses at least two components, because a green
isolated PR does not show that the combined system works.
"""
from __future__ import annotations

from io import BytesIO
import random
import threading

import pytest

torch = pytest.importorskip("torch")

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as journal  # noqa: E402
from scripts.v5 import jepa_v5_structured_journal_preflight_v1 as bridge  # noqa: E402
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import (  # noqa: E402
    collapse_receipt, commit, flip_last_byte, kill_write, open_run,
)
from tests.test_jepa_v5_structured_journal_preflight_v1 import (  # noqa: E402
    GENES, PANEL, PHILOX, SEED, SOURCES, fake_bundle, fake_bytes, open_synthetic,
    submit,
)

EXPECTED = dict(expected_gene_axis_sha256=GENES,
                expected_source_manifest_sha256=SOURCES,
                expected_philox_contract_sha256=PHILOX,
                expected_keyed_run_seed=SEED)


def structured_run(tmp_path, updates, horizon=6):
    root, backup, _ = open_synthetic(tmp_path, horizon=horizon)
    states = {0: None}
    for u in range(1, updates + 1):
        journal.begin_attempt(root, backup, update=u)
        raw = fake_bytes(u)
        assert submit(root, backup, u, raw)["journal"]["status"] == "UPDATE_COMMITTED"
        states[u] = raw
    return root, backup, states


def inspect(root, backup, u):
    return bridge.inspect_stored_structured_snapshot(root=root, custody=backup,
                                                     update=u, **EXPECTED)


# ------------------------------------------------ forensic reads (#576 x #577 x #575)

def test_structured_state_with_damaged_own_probe_is_not_returned_but_later_ones_are(
        tmp_path):
    root, backup, _ = structured_run(tmp_path, 2)
    flip_last_byte(root / "u00001.telemetry.json")
    with pytest.raises(journal.JournalRefusal, match="UPDATE_NOT_VERIFIED_COMMITTED_STATE"):
        inspect(root, backup, 1)
    assert inspect(root, backup, 2)["state"]["state_update"] == 2
    report = journal.inspect_forensic_prefix(root, backup)
    assert report["probe_pass_states_with_damaged_evidence"] == [1]
    assert report["last_reported_probe_pass_checkpoint_update"] == 2
    assert report["last_neurally_healthy_checkpoint_proved"] is False


def test_first_collapse_recorded_over_damaged_older_structured_checkpoint(tmp_path):
    root, backup, _ = structured_run(tmp_path, 2)
    journal.begin_attempt(root, backup, update=3)
    flip_last_byte(root / "u00001.state.bin")
    collapsed = fake_bytes(3)
    out = journal.record_collapsed_state(root, backup, update=3, state_bytes=collapsed,
                                         reported_receipt=collapse_receipt(3, panel=PANEL))
    assert out["status"] == "STATE_COLLAPSED"
    assert out["historical_evidence_damaged_sequences"] == [2]
    report = journal.inspect_forensic_prefix(root, backup)
    assert report["collapsed_state_updates_nonresumable"] == [3]
    assert report["last_reported_probe_pass_checkpoint_update"] == 2
    assert journal.read_forensic_collapsed_state(root, backup, update=3) == collapsed
    assert inspect(root, backup, 2)["state"]["state_update"] == 2
    with pytest.raises(journal.JournalRefusal):
        inspect(root, backup, 1)
    with pytest.raises(journal.JournalRefusal):  # a collapse is never a probe-pass state
        inspect(root, backup, 3)


@pytest.mark.parametrize("seed", range(12))
def test_forensic_reader_and_report_agree_under_random_accidental_damage(tmp_path, seed):
    """#576 reader vs #572/#577 report, on fake bytes, one accident per state."""
    rng = random.Random(seed)
    root, backup = open_run(tmp_path, horizon=6)
    raws = {0: b"U0_STATE"}
    for u in range(1, 6):
        raws[u] = commit(root, backup, u)
    actions = {u: rng.choice(["intact", "flip_state", "flip_telemetry", "delete_state",
                              "delete_local_record", "delete_outside_record"])
               for u in range(6)}
    for u, act in actions.items():
        record = f"j{0 if u == 0 else 2 * u:08d}.json"
        if act == "flip_state":
            flip_last_byte(root / f"u{u:05d}.state.bin")
        elif act == "flip_telemetry":
            flip_last_byte(root / f"u{u:05d}.telemetry.json")
        elif act == "delete_state":
            (root / f"u{u:05d}.state.bin").unlink()
        elif act == "delete_local_record":
            (root / record).unlink()
        elif act == "delete_outside_record":
            (backup / record).unlink()
    damaged = sorted(u for u, a in actions.items()
                     if a in ("flip_state", "flip_telemetry", "delete_state"))
    readable = sorted(set(actions) - set(damaged))
    report = journal.inspect_forensic_prefix(root, backup)
    assert report["probe_pass_states_with_damaged_evidence"] == damaged, actions
    assert report["last_reported_probe_pass_checkpoint_update"] == (
        readable[-1] if readable else None), actions
    for u in range(6):
        if u in readable:
            assert journal.read_forensic_opaque_state(root, backup, update=u) == raws[u]
        else:
            with pytest.raises(journal.JournalRefusal):
                journal.read_forensic_opaque_state(root, backup, update=u)


# ------------------------------------------------ structure (#578 x #575 x #581)

def test_incomplete_teacher_bytes_are_refused_in_the_integrated_bridge(tmp_path):
    root, backup, _ = open_synthetic(tmp_path)
    journal.begin_attempt(root, backup, update=1)
    bundle = fake_bundle(1)
    for k in [k for k in bundle["modules"]["teacher"] if k.startswith("value_encoder")]:
        bundle["modules"]["teacher"].pop(k)
    stream = BytesIO()
    torch.save(bundle, stream)
    raw = stream.getvalue()
    with pytest.raises(bridge.StructuredJournalRefusal,
                       match="INVALID_FULL_STATE_COMPONENTS") as caught:
        submit(root, backup, 1, raw)
    assert "TEACHER_DOES_NOT_MIRROR_ONLINE" in str(caught.value.__cause__)
    assert not (root / "u00001.state.bin").exists()
    assert not (root / "u00001.telemetry.json").exists()


# ------------------------------------------------ crash recovery (#577/#580 x #575)

def test_crash_before_structured_commit_record_never_becomes_a_success(
        tmp_path, monkeypatch):
    root, backup, _ = structured_run(tmp_path, 1)
    journal.begin_attempt(root, backup, update=2)
    # j0 open, j1 begin1, j2 commit1, j3 begin2, j4 = the commit record of u2
    original = kill_write(monkeypatch, root, "j00000004.json")
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        submit(root, backup, 2, fake_bytes(2))
    monkeypatch.setattr(journal, "_write_once", original)
    out = journal.recover_interrupted_attempt(root, backup)
    assert out["status"] == "ATTEMPT_ABORTED"
    assert {e["name"].split(".")[0] for e in out["quarantined"]} == {"u00002"}
    report = journal.inspect_journal(root, backup)
    assert report["last_reported_probe_pass_checkpoint_update"] == 1
    with pytest.raises(journal.JournalRefusal):
        inspect(root, backup, 2)
    with pytest.raises(journal.JournalRefusal):
        journal.begin_attempt(root, backup, update=3)


# ------------------------------------------------ writer ownership (#573/#577/#580 x #575)

def test_sibling_thread_cannot_recover_a_live_structured_attempt(tmp_path):
    root, backup, _ = structured_run(tmp_path, 1)
    started, release, result = threading.Event(), threading.Event(), {}

    def attempt():
        journal.begin_attempt(root, backup, update=2)
        started.set()
        release.wait(60)
        result["status"] = submit(root, backup, 2, fake_bytes(2))["journal"]["status"]
    t = threading.Thread(target=attempt)
    t.start()
    assert started.wait(60)
    try:
        with pytest.raises(journal.JournalRefusal, match="ATTEMPT_THREAD_STILL_ALIVE"):
            journal.recover_interrupted_attempt(root, backup)
    finally:
        release.set()
        t.join(60)
    assert result["status"] == "UPDATE_COMMITTED"


class _BridgeWorker:
    def __init__(self, root, backup, raw):
        self.root, self.backup, self.raw = str(root), str(backup), raw

    def __len__(self):
        return 2

    def __getitem__(self, i):
        from pathlib import Path
        try:
            if i == 0:
                submit(Path(self.root), Path(self.backup), 2, self.raw)
            else:
                journal.recover_interrupted_attempt(Path(self.root), Path(self.backup))
        except (journal.JournalRefusal, bridge.StructuredJournalRefusal) as exc:
            return "REFUSED:" + str(exc)
        return "UNSAFE_WORKER_CHANGED_LIVE_RUN"


def test_forked_dataloader_workers_cannot_commit_or_recover_structured_run(tmp_path):
    root, backup, _ = structured_run(tmp_path, 1)
    journal.begin_attempt(root, backup, update=2)
    raw = fake_bytes(2)
    loader = torch.utils.data.DataLoader(_BridgeWorker(root, backup, raw), batch_size=None,
                                         num_workers=2, multiprocessing_context="fork")
    outcomes = list(loader)
    assert all(o.startswith("REFUSED:") for o in outcomes), outcomes
    assert submit(root, backup, 2, raw)["journal"]["status"] == "UPDATE_COMMITTED"


# ------------------------------------------------ I/O (#574/#577 x #575)

def test_structured_writer_reads_each_new_checkpoint_about_once(tmp_path, monkeypatch):
    reads = {"n": 0}
    real = journal._read

    def counted(path, limit, *, twin_ok=False):
        raw = real(path, limit, twin_ok=twin_ok)
        if str(path).endswith(".state.bin"):
            reads["n"] += 1
        return raw
    monkeypatch.setattr(journal, "_read", counted)
    structured_run(tmp_path, 5, horizon=6)
    # u0..u5 verified once each on publication; old payloads are not re-read.
    assert reads["n"] <= 6 + 2, reads
