"""The resource monitor must attach to the fit, never to itself: its own command line carries the same pattern
(self-audit 54). Fake process tables only; no process is started."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import measure_v79_fit_resources as MR  # noqa: E402


class FakeProc:
    def __init__(self, pid, name, cmdline):
        self.pid = pid
        self.info = {"pid": pid, "name": name, "cmdline": cmdline}


def table(*procs):
    return lambda attrs=None: iter(procs)


def test_the_monitor_never_attaches_to_itself(monkeypatch):
    me = FakeProc(os.getpid(), "python.exe", ["python", "measure_v79_fit_resources.py", "bernoulli --fits S4_operator_only"])
    fit = FakeProc(4242, "python.exe", ["python", "run_v79_recovery.py", "--likelihood", "bernoulli", "--fits", "S4_operator_only"])
    monkeypatch.setattr(MR.psutil, "process_iter", table(me, fit))
    assert MR.find("bernoulli --fits S4_operator_only").pid == 4242


def test_only_a_fitting_runner_is_a_target(monkeypatch):
    other = FakeProc(7, "python.exe", ["python", "some_other_tool.py", "bernoulli --fits S4_operator_only"])
    monkeypatch.setattr(MR.psutil, "process_iter", table(other))
    assert MR.find("bernoulli --fits S4_operator_only") is None
