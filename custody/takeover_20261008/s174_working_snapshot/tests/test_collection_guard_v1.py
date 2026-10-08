"""Guard against the project's recurring 'green because nothing executed' mode.

THREE RECORDED INSTANCES, all in this project:

  1. V29 census tests were listed as CI *path triggers* while no workflow step
     executed them. A grep for the filename matched the trigger lines and read
     as confirmation.
  2. The conditional-composition portable bundle raised ModuleNotFoundError at
     COLLECTION, so all four of its test files ran zero tests.
  3. tests/test_regulatory_exposure_ledger_v1.py passed 7/7 only under
     PYTHONPATH=src; bare pytest gave a collection error, and a collection
     error runs zero tests.

A collection error is not a failure in any summary that counts only failures.
These assertions make the count itself the assertion, so a suite cannot pass by
not running.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Decision-bearing suites and the exact number of tests each MUST collect.
# Raising a count here is a deliberate act; a silent drop to zero is the defect.
REQUIRED_COLLECTION = {
    "tests/test_regulatory_exposure_ledger_v1.py": 7,
}


def _bare_env() -> dict:
    """The environment a plain CI invocation has: no inherited PYTHONPATH."""
    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


def _collected(path: str) -> int:
    """Count tests pytest actually collects, in a FRESH process with no
    inherited PYTHONPATH — i.e. exactly what a bare CI invocation does."""
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", path],
                       cwd=ROOT, capture_output=True, text=True,
                       env=_bare_env(), timeout=300)
    # pytest exit 5 == "no tests collected". That is a legitimate zero, NOT a
    # collection error, and conflating the two is how a guard stops guarding:
    # it would report -1 for an empty file and never verify it can see zero.
    if r.returncode == 5:
        return 0
    if "error" in r.stdout.lower() or r.returncode != 0:
        return -1
    n = 0
    for line in r.stdout.splitlines():
        if "::" in line and not line.startswith(("=", "<", " ")):
            n += 1
    return n


def test_conftest_is_what_makes_the_import_resolve():
    """REPAIRED. The previous version of this test ran a subprocess that did
    `sys.path.insert(0, 'src')` ITSELF, which bypasses conftest.py entirely —
    so it could not have detected conftest.py being deleted, despite its name
    and docstring claiming exactly that. It proved only that the module exists
    on disk.

    This version writes a probe that performs the bare import with NO manual
    path manipulation and NO inherited PYTHONPATH, then runs pytest on it from
    the repository root. conftest.py is then the only thing that can place src/
    on sys.path, so a pass here is attributable to the fix.
    """
    probe = ROOT / "tests" / "_conftest_attribution_probe.py"
    body = (
        "from sea_ad_jepa.regulatory.regulatory_exposure_ledger_v1 import (\n"
        "    seed_historical_regulatory_exposure)\n"
        "\n"
        "\n"
        "def test_import_resolved_without_manual_path():\n"
        "    assert seed_historical_regulatory_exposure() is not None\n"
    )
    probe.write_text(body)
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q",
             "tests/_conftest_attribution_probe.py"],
            cwd=ROOT, capture_output=True, text=True,
            env=_bare_env(), timeout=300)
        assert r.returncode == 0, (
            "the bare import did not resolve, so conftest.py is not doing its "
            "job:\n" + r.stdout[-600:])
        assert "1 passed" in r.stdout
    finally:
        probe.unlink(missing_ok=True)


def test_decision_bearing_suites_collect_their_required_count_bare():
    """The load-bearing assertion. -1 means a collection error, i.e. ZERO tests
    ran, which must fail loudly rather than read as 'no failures'."""
    problems = []
    for path, expected in REQUIRED_COLLECTION.items():
        got = _collected(path)
        if got == -1:
            problems.append(f"{path}: COLLECTION ERROR — zero tests would run")
        elif got != expected:
            problems.append(f"{path}: collected {got}, required {expected}")
    assert not problems, "; ".join(problems)


def test_the_guard_can_actually_fail():
    """A guard that cannot fail is the defect it guards against. A file with no
    tests must be detected as collecting zero, not silently accepted."""
    empty = ROOT / "tests" / "_collection_guard_probe_empty.py"
    empty.write_text("# deliberately contains no tests\n")
    try:
        assert _collected("tests/_collection_guard_probe_empty.py") == 0
    finally:
        empty.unlink(missing_ok=True)
