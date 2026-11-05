"""Sol independent RED on Macha #577: mirror reconciliation must not race a live
writer or promote a corrupted newly committed payload. Synthetic bytes ONLY.
No forward, optimizer, EMA, GPU, controller, real biological data, or training.
Original Macha REDs stay untouched.
"""
from pathlib import Path

import pytest

from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v
from tests.test_jepa_synth2048_attempt_journal_v2_macha_red import (
    commit, flip_last_byte, kill_write, open_run, probe,
)
from tests.test_jepa_synth2048_attempt_journal_v2_io_cache_macha_red import (
    run_python,
)


def half_mirrored_success(tmp_path, monkeypatch):
    root, outside = open_run(tmp_path, horizon=4)
    commit(root, outside, 1)
    v.begin_attempt(root, outside, update=2)
    original = kill_write(monkeypatch, outside, "j00000004.json")
    raw = b"GOOD_STATE_U2"
    with pytest.raises(RuntimeError, match="SIMULATED_PROCESS_DEATH"):
        v.commit_reported_update(root, outside, update=2,
                                 state_bytes=raw, probe=probe(2, raw))
    monkeypatch.setattr(v, "_write_once", original)
    assert (root / "j00000004.json").exists()
    assert not (outside / "j00000004.json").exists()
    return root, outside


def test_red_second_process_cannot_reconcile_while_opening_writer_is_alive(
        tmp_path, monkeypatch):
    """A second process must not interfere with a live writer's mirror commit."""
    root, outside = half_mirrored_success(tmp_path, monkeypatch)
    code = (
        "import sys\nfrom pathlib import Path\n"
        "from scripts.v5 import jepa_synth2048_attempt_journal_v2 as v\n"
        "try:\n"
        "    print(v.reconcile_one_unmirrored_record(Path(sys.argv[1]), Path(sys.argv[2])))\n"
        "except v.JournalRefusal as exc:\n"
        "    print('REFUSED', exc)\n    sys.exit(3)\n"
        "print('UNSAFE_NONOWNER_RECONCILED_LIVE_WRITER')\n"
    )
    result = run_python(code, str(root), str(outside))
    assert result.returncode == 3, result.stdout + result.stderr
    assert "WRITER_PROCESS_STILL_ALIVE" in result.stdout
    assert not (outside / "j00000004.json").exists()
    # The owner itself is permitted to repair an interrupted mirror.
    assert v.reconcile_one_unmirrored_record(root, outside)["status"] == (
        "ONE_VERIFIED_LOCAL_RECORD_MIRRORED"
    )
    assert v.inspect_journal(root, outside)["last_reported_probe_pass_checkpoint_update"] == 2


@pytest.mark.parametrize("bad", ["state", "telemetry"])
def test_red_a_damaged_new_success_cannot_be_mirrored_as_verified(
        tmp_path, monkeypatch, bad):
    root, outside = half_mirrored_success(tmp_path, monkeypatch)
    damaged_path = (root / "u00002.state.bin" if bad == "state"
                    else root / "u00002.telemetry.json")
    flip_last_byte(damaged_path)
    with pytest.raises(v.JournalRefusal, match="UNMIRRORED_NEW_RECORD_EVIDENCE_DAMAGED"):
        v.reconcile_one_unmirrored_record(root, outside)
    assert not (outside / "j00000004.json").exists()
    # History remains forensic-only and cannot become a successful strict run.
    with pytest.raises(v.JournalRefusal):
        v.inspect_journal(root, outside)
    assert v.inspect_forensic_prefix(root, outside)["resume_authorized"] is False
