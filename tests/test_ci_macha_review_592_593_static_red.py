"""Macha independent review of Sol #592 (7e4c45ae) and #593 (612c1b2f).

Static source checks only: no torch import, no pytest collection, no model,
optimizer, backward or EMA. Temporary copies are read as text.

#592 RED: pytest also executes conftest.py and ini addopts that the explicit
argv never lists; aliased steps pass the AST gate; one automatically
triggered workflow (Macha's own #587 route) still globs pytest argv.
#593 RED: the quarantine recognizes only the literal "python -m pytest",
so `pytest ...`, `python3 -m pytest`, `python -c` or a local action pass.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def _copy(paths, root: Path) -> None:
    for name in paths:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, root / name)


class Review592ExplicitInventory(unittest.TestCase):
    def setUp(self):
        from scripts.v5 import jepa_v5_ci_explicit_nonstepping_allowlist_v1 as gate
        self.gate = gate
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        _copy(gate.NO_TRAINING_TEST_INVENTORY["thread"], self.tmp)

    def test_control_reviewed_thread_inventory_passes(self):
        self.gate.verify_inventory("thread", self.tmp)

    def test_red_implicit_conftest_must_be_refused(self):
        (self.tmp / "tests/conftest.py").write_text(
            "import pytest\n@pytest.fixture(autouse=True)\ndef hidden():\n    yield\n")
        with self.assertRaisesRegex(RuntimeError, "IMPLICIT_CONFTEST"):
            self.gate.verify_inventory("thread", self.tmp)

    def test_red_ini_addopts_must_be_refused(self):
        (self.tmp / "pytest.ini").write_text(
            "[pytest]\naddopts = tests/test_v5_prefreeze_runtime_torch_integration.py\n")
        with self.assertRaisesRegex(RuntimeError, "IMPLICIT_PYTEST_CONFIG"):
            self.gate.verify_inventory("thread", self.tmp)

    def test_red_aliased_or_dynamic_steps_must_be_refused(self):
        sources = {
            "attribute_alias": "s = optimizer.step\ns()\n",
            "getattr": "getattr(optimizer, 'step')()\n",
            "methodcaller": "import operator\noperator.methodcaller('step')(optimizer)\n",
            "autograd_grad_import": "from torch.autograd import grad as g\ng(y, x)\n",
            "backward_alias": "b = loss.backward\nb()\n",
        }
        for label, source in sources.items():
            with self.subTest(case=label):
                with self.assertRaisesRegex(RuntimeError, "FORBIDDEN"):
                    self.gate._check_ast(source, label + ".py")

    def test_control_monkeypatch_strings_and_teacher_eval_stay_allowed(self):
        self.gate._check_ast(
            "patch.object(torch.optim.AdamW, 'step', side_effect=boom)\n"
            "opt.step = lambda *a, **k: None\nteacher.eval()\n", "safe.py")

    def test_red_no_automatic_workflow_globs_pytest_argv(self):
        offenders = []
        for workflow in sorted((ROOT / ".github/workflows").glob("*.y*ml")):
            head, _, jobs = workflow.read_text(encoding="utf-8").partition("\njobs:")
            events = re.findall(r"(?m)^  (pull_request|pull_request_target|push|schedule):", head)
            if events and all(re.search(r"(?m)^  " + e + r":\n(?:    .*\n)*?    branches:", head)
                              for e in events):
                continue  # limited to an old branch: not run by this stack
            for line in jobs.splitlines():
                if "pytest" in line and re.search(r"tests/\S*[*?\[]", line):
                    offenders.append(workflow.name)
        self.assertEqual(offenders, [], "glob-built pytest argv in automatic workflows")


class Review593LegacyQuarantine(unittest.TestCase):
    def setUp(self):
        from scripts.v5 import jepa_v5_legacy_step_ci_quarantine_v1 as guard
        self.guard = guard
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        _copy((*guard.WORKFLOWS, *guard.HISTORICAL_STEP_TESTS), self.tmp)

    def test_control_current_four_routes_pass(self):
        self.guard.verify_quarantine(self.tmp)

    def test_red_any_reintroduced_runner_must_be_refused(self):
        target = self.tmp / ".github/workflows/v5-inactive-runtime-step-guard.yml"
        original = target.read_text(encoding="utf-8")
        steps = {
            "bare_pytest": "      - run: pytest -q tests/test_v5_prefreeze_runtime_torch_integration.py\n",
            "python3_module": "      - run: python3 -m pytest -q tests/test_v5_prefreeze_checkpoint_binding_v1.py\n",
            "python_c": "      - run: python -c \"import tests.test_v5_prefreeze_runtime_torch_integration\"\n",
            "local_action": "      - uses: ./.github/actions/legacy-v5-step-tests\n",
        }
        for label, step in steps.items():
            with self.subTest(case=label):
                target.write_text(original + step, encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "QUARANTINED_ROUTE"):
                    self.guard.verify_quarantine(self.tmp)
        target.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
