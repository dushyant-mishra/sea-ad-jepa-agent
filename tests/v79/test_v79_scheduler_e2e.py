"""End-to-end scheduler test on harmless jobs (local only: needs Windows, Git Bash and WSL; set V79_E2E=1).
Every outcome class is produced through the real entrypoint and recorded in the ledger, and the machine-wide fit
count is readable. A launch or runtime failure is classified as such, never as a statistical result."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHED = ROOT / "scripts" / "v79" / "run_v79_scheduler.py"
pytestmark = pytest.mark.skipif(os.environ.get("V79_E2E") != "1", reason="local end-to-end test; set V79_E2E=1")


def msys(p: Path) -> str:
    """Windows forward-slash path (C:/...): readable by Git Bash and by Windows Python alike."""
    return p.resolve().as_posix()


def wsl(p: Path) -> str:
    s = p.resolve().as_posix()
    return f"/mnt/{s[0].lower()}{s[2:]}"


def test_scheduler_records_every_outcome_class(tmp_path):
    out = {k: tmp_path / f"{k}.out" for k in ("ok", "fail", "noout", "timeout", "gpu")}
    jobs = [dict(name="ok", cmd=f"echo fine > {msys(out['ok'])}", log=msys(tmp_path / "ok.log"), out=msys(out["ok"])),
            dict(name="fail", cmd="exit 3", log=msys(tmp_path / "fail.log"), out=msys(out["fail"])),
            dict(name="noout", cmd="true", log=msys(tmp_path / "noout.log"), out=msys(out["noout"])),
            dict(name="timeout", cmd="sleep 30", log=msys(tmp_path / "t.log"), out=msys(out["timeout"])),
            dict(name="gpu", device="gpu", cmd=f"echo from-wsl > {wsl(out['gpu'])}", log=msys(tmp_path / "g.log"),
                 out=msys(out["gpu"]))]
    jf, ledger = tmp_path / "jobs.json", tmp_path / "ledger.jsonl"
    jf.write_text(json.dumps(jobs), encoding="utf-8")
    subprocess.run([sys.executable, str(SCHED), str(jf), msys(ledger), "--slots", "99", "--timeout", "5",
                    "--settle", "1"], check=True)
    deadline = time.time() + 120
    while time.time() < deadline:
        ends = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if '"end"' in x]
        if len(ends) == len(jobs):
            break
        time.sleep(2)
    cls = {e["name"]: e["class"] for e in ends}
    assert cls == {"ok": "OUTPUT_WRITTEN", "fail": "LAUNCH_OR_RUNTIME_FAILURE", "noout": "LAUNCH_OR_RUNTIME_FAILURE",
                   "timeout": "TIMEOUT", "gpu": "OUTPUT_WRITTEN"}, cls
    starts = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if '"start"' in x]
    assert {s["name"] for s in starts} == set(cls)
    # every written output is bound by its exact SHA-256 (an empty or placeholder value is a provenance failure)
    import hashlib
    for e in ends:
        if e["class"] == "OUTPUT_WRITTEN":
            assert e["out_sha256"] == hashlib.sha256(out[e["name"]].read_bytes()).hexdigest(), e
        else:
            assert e["out_sha256"] == "none", e


def test_machine_wide_fit_count_is_readable():
    sys.path.insert(0, str(ROOT / "scripts" / "v79"))
    import run_v79_scheduler as S
    assert S.windows_fits() >= 0 and S.wsl_fits() >= 0 and S.running_fits() < 10 ** 6
