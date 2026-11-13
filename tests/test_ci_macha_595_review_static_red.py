"""Macha independent review of Sol #595 (exact head 37dc2469).

Static/mocked only: inert workflow text in temporary directories and a mocked
subprocess. No pytest collection, torch import, model, optimizer, backward
or EMA. #595's own two changes are controls here and must stay green.

RED 1: an automatic push-to-main route running `python -m pytest -q`,
`pytest .`, `pytest tests/v5` or `--pyargs` collects whole directories but
passes the scan (the shape check is Macha's own from #594).
RED 2: `.pytest.ini` and config files inside tests/ are not refused.
RED 3: the guarded runner does not pin its pytest config or rootdir, so an
ini found upward from the test paths can still add tests.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PUSH_MAIN = "  push:\n    branches:\n      - main\n"


def _workflow(run: str, on: str = PUSH_MAIN) -> str:
    return (f"name: t\non:\n{on}\njobs:\n  j:\n    runs-on: ubuntu-latest\n"
            f"    steps:\n      - uses: actions/checkout@v4\n      - run: {run}\n")


class Review595(unittest.TestCase):
    def setUp(self):
        from scripts.v5 import jepa_v5_ci_explicit_nonstepping_allowlist_v1 as gate
        self.gate = gate
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / ".github/workflows").mkdir(parents=True)

    def _scan(self, run: str, on: str = PUSH_MAIN):
        (self.tmp / ".github/workflows/a.yml").write_text(_workflow(run, on))
        return self.gate.verify_no_wildcard_pytest_routes(self.tmp)

    def test_control_595_main_branch_glob_still_refused(self):
        with self.assertRaisesRegex(RuntimeError, "WILDCARD_OR_DIRECTORY"):
            self._scan("python -m pytest -q tests/test_x*.py")

    def test_control_explicit_files_with_options_and_node_ids_pass(self):
        self._scan("python -m pytest -q -rA --noconftest -p no:cacheprovider "
                   "tests/test_a.py::test_x tests/test_b.py")
        self._scan("python -m pip install pytest==9.0.2")
        self._scan("python scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py "
                   "--suite full --pytest")

    def test_control_every_current_repository_workflow_passes(self):
        self.gate.verify_no_wildcard_pytest_routes(ROOT)

    def test_red_broad_collection_without_a_wildcard_is_refused(self):
        for run in ("python -m pytest -q", "pytest .", "python -m pytest -q tests/v5",
                    "python -m pytest -q --pyargs scripts", "py.test -q tests"):
            with self.subTest(run=run):
                with self.assertRaisesRegex(RuntimeError, "PYTEST_ROUTE"):
                    self._scan(run)

    def test_red_hidden_and_tests_dir_pytest_config_refused(self):
        (self.tmp / "tests").mkdir()
        for name in (".pytest.ini", "tests/pytest.ini", "tests/.pytest.ini"):
            with self.subTest(config=name):
                (self.tmp / name).write_text("[pytest]\naddopts = tests/test_unreviewed.py\n")
                with self.assertRaisesRegex(RuntimeError, "IMPLICIT_PYTEST_CONFIG"):
                    self.gate._refuse_implicit_collection_inputs(self.tmp)
                (self.tmp / name).unlink()

    def test_red_runner_pins_reviewed_config_and_rootdir(self):
        with mock.patch.dict(os.environ, {"PYTEST_ADDOPTS": "tests/x.py", "PYTEST_PLUGINS": "p"}), \
             mock.patch.object(self.gate, "verify_inventory", return_value=("tests/a.py",)), \
             mock.patch.object(self.gate.subprocess, "run") as run, \
             mock.patch.object(sys, "argv", ["g", "--suite", "thread", "--pytest"]):
            self.gate.main()
        argv, env = run.call_args.args[0], run.call_args.kwargs["env"]
        self.assertEqual((env["PYTEST_ADDOPTS"], env["PYTEST_PLUGINS"]), ("", ""))  # #595 control
        self.assertIn("-c", argv)
        self.assertIn("--rootdir", argv)
        self.assertEqual(argv[argv.index("--rootdir") + 1], str(self.gate.ROOT))
        self.assertEqual(argv[-1], "tests/a.py")


if __name__ == "__main__":
    unittest.main()
