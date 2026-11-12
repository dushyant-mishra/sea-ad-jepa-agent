"""Sol independent review of #594: static-only CI and inherited pytest env.

All tests use harmless workflow strings and mocks. No torch, pytest discovery,
optimizer step, backward, EMA, model construction or real data access.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from scripts.v5 import jepa_v5_ci_explicit_nonstepping_allowlist_v1 as guard


ROOT = Path(__file__).resolve().parents[1]


class Macha594SafetyRedGreen(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ci-static-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / ".github/workflows").mkdir(parents=True)

    def _workflow(self, name, source):
        p = self.tmp / ".github/workflows" / name
        p.write_text(source, encoding="utf-8")
        return p

    def test_push_main_with_wildcard_is_never_called_a_legacy_branch(self):
        self._workflow("new-main.yml", """name: synthetic example
on:
  push:
    branches:
      - main
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest -q tests/test_*.py
""")
        with self.assertRaisesRegex(RuntimeError, "WILDCARD_OR_DIRECTORY_PYTEST_ROUTE"):
            guard.verify_no_wildcard_pytest_routes(self.tmp)

    def test_pull_request_main_with_wildcard_is_never_skipped(self):
        self._workflow("new-pr.yml", """name: synthetic example
on:
  pull_request:
    branches:
      - main
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest -q tests/test_*.py
""")
        with self.assertRaisesRegex(RuntimeError, "WILDCARD_OR_DIRECTORY_PYTEST_ROUTE"):
            guard.verify_no_wildcard_pytest_routes(self.tmp)

    def test_exact_old_d1_definition_is_preserved_but_not_dispatched(self):
        archived = ROOT / ".github/workflows/d1-independent-closure-ci.yml"
        target = self.tmp / ".github/workflows/d1-independent-closure-ci.yml"
        shutil.copyfile(archived, target)
        self.assertTrue(guard._exact_unchanged_legacy_workflow(
            target, target.read_bytes()))
        self.assertEqual(guard.verify_no_wildcard_pytest_routes(self.tmp),
                         [target.name])

    def test_modified_d1_main_workflow_loses_frozen_exception(self):
        archived = ROOT / ".github/workflows/d1-independent-closure-ci.yml"
        text = archived.read_text(encoding="utf-8")
        self.assertIn("review/d1-independent-closure-20260907", text)
        target = self._workflow(
            "d1-independent-closure-ci.yml",
            text.replace("review/d1-independent-closure-20260907", "main"))
        self.assertFalse(guard._exact_unchanged_legacy_workflow(
            target, target.read_bytes()))
        with self.assertRaisesRegex(RuntimeError, "WILDCARD_OR_DIRECTORY_PYTEST_ROUTE"):
            guard.verify_no_wildcard_pytest_routes(self.tmp)

    def test_inherited_pytest_addopts_and_explicit_plugins_are_cleared(self):
        # Mocked subprocess; no pytest collection or unapproved file execution.
        with mock.patch.dict(os.environ, {
            "PYTEST_ADDOPTS": "tests/test_unapproved.py",
            "PYTEST_PLUGINS": "unapproved_plugin",
        }), mock.patch.object(
            guard, "verify_inventory", return_value=("tests/test_allowed.py",)
        ), mock.patch.object(
            guard.subprocess, "run"
        ) as launch, mock.patch.object(
            sys, "argv", ["script", "--suite", "thread", "--pytest"]
        ):
            self.assertEqual(guard.main(), 0)
        self.assertEqual(launch.call_count, 1)
        args, kw = launch.call_args
        self.assertEqual(args[0][-1], "tests/test_allowed.py")
        self.assertIn("--noconftest", args[0])
        self.assertEqual(kw["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"], "1")
        self.assertEqual(kw["env"]["PYTEST_ADDOPTS"], "")
        self.assertEqual(kw["env"]["PYTEST_PLUGINS"], "")


if __name__ == "__main__":
    unittest.main()
