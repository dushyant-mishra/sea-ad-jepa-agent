"""Macha controls for #579: loader workers, dead owners, dead attempt threads.

FAKE BYTES ONLY. No model, optimizer step, EMA update, GPU, RNA or controller.
These must pass both at #579 and after any Macha repair.
"""
from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
import threading
import time

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red import run_python
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import commit, open_run

CALLS = ("recover", "reconcile", "begin", "commit")


def _try(call: str, root: str, backup: str) -> str:
    """What a loader worker might do by accident. Never raises."""
    r, b = Path(root), Path(backup)
    try:
        if call == "recover":
            v.recover_interrupted_attempt(r, b)
        elif call == "reconcile":
            v.reconcile_one_unmirrored_record(r, b)
        elif call == "begin":
            v.begin_attempt(r, b, update=3)
        else:
            v.commit_reported_update(r, b, update=2, state_bytes=b"WORKER",
                                     probe={})
    except v.JournalRefusal as exc:
        return "REFUSED:" + str(exc)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        return "ERROR:" + repr(exc)
    return "UNSAFE_WORKER_CHANGED_LIVE_RUN"


class _WorkerProbe:
    """Picklable map-style dataset for torch DataLoader workers."""

    def __init__(self, root: str, backup: str):
        self.root, self.backup = root, backup

    def __len__(self):
        return len(CALLS)

    def __getitem__(self, i):
        return _try(CALLS[i], self.root, self.backup)


def _live_run(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)
    v.begin_attempt(root, backup, update=2)  # live attempt in this process
    return root, backup


def _assert_untouched(root, backup, outcomes):
    assert all(o.startswith("REFUSED:") for o in outcomes), outcomes
    assert any("WRITER_PROCESS_STILL_ALIVE" in o for o in outcomes), outcomes
    # The live writer can still record its real outcome.
    raw = b"GOOD_STATE_U2"
    from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import probe
    assert v.commit_reported_update(root, backup, update=2, state_bytes=raw,
                                    probe=probe(2, raw))["status"] == "UPDATE_COMMITTED"


@pytest.mark.parametrize("context", ["fork", "spawn"])
def test_torch_dataloader_workers_cannot_touch_the_live_run(
        tmp_path, context, monkeypatch):
    torch = pytest.importorskip("torch")
    # Conda's mkl-service may set MKL_THREADING_LAYER=INTEL in this process; a
    # spawned worker loading torch's libgomp then exits at import. Environment
    # only, unrelated to the journal (diagnosed 2026-11-05).
    monkeypatch.setenv("MKL_SERVICE_FORCE_INTEL", "1")
    root, backup = _live_run(tmp_path)
    loader = torch.utils.data.DataLoader(
        _WorkerProbe(str(root), str(backup)), batch_size=None, num_workers=2,
        multiprocessing_context=context)
    _assert_untouched(root, backup, list(loader))


@pytest.mark.parametrize("context", ["fork", "spawn", "forkserver"])
def test_multiprocessing_workers_cannot_touch_the_live_run(tmp_path, context):
    root, backup = _live_run(tmp_path)
    ctx = multiprocessing.get_context(context)
    with ctx.Pool(2) as pool:
        outcomes = pool.starmap(_try, [(c, str(root), str(backup)) for c in CALLS])
    _assert_untouched(root, backup, outcomes)


def test_dead_attempt_thread_lets_its_own_process_recover(tmp_path):
    root, backup = open_run(tmp_path)
    commit(root, backup, 1)

    def dies():
        v.begin_attempt(root, backup, update=2)
        raise SystemExit  # the computing thread ends without an outcome
    t = threading.Thread(target=dies)
    t.start()
    t.join(60)
    out = v.recover_interrupted_attempt(root, backup)
    assert out["status"] == "ATTEMPT_ABORTED"
    assert v.inspect_journal(root, backup)["last_reported_probe_pass_checkpoint_update"] == 1


def test_dead_opener_with_a_lingering_forked_loader_is_recovered_after_it_exits(
        tmp_path):
    """Conservative: a forked loader worker keeps the opener lock until it exits."""
    root, backup = tmp_path / "run", tmp_path / "outside-head"
    opener = run_python(
        "import os, sys, time\nfrom pathlib import Path\n"
        "from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import commit, open_run\n"
        "from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v\n"
        "root, backup = open_run(Path(sys.argv[1]))\n"
        "commit(root, backup, 1)\n"
        "v.begin_attempt(root, backup, update=2)\n"
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    null = os.open(os.devnull, os.O_WRONLY)\n"
        "    os.dup2(null, 1)\n"
        "    os.dup2(null, 2)\n"
        "    time.sleep(3)\n"
        "    os._exit(0)\n"
        "print('LOADER', pid, flush=True)\n"
        "os._exit(0)\n",
        str(tmp_path))
    loader = int(opener.stdout.split("LOADER", 1)[1].split()[0])
    with pytest.raises(v.JournalRefusal, match="WRITER_PROCESS_STILL_ALIVE"):
        v.recover_interrupted_attempt(root, backup)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            os.kill(loader, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    time.sleep(0.2)
    out = v.recover_interrupted_attempt(root, backup)
    assert out["status"] == "ATTEMPT_ABORTED"
    assert v.close_run(root, backup)["status"] == "ABORTED_RECOVERED"
