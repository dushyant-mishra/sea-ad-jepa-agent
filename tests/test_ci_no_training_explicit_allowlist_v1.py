"""Static hosted-safety regression: never discover neural-step tests by wildcard.

This unittest reads only text from the repository. It cannot import torch,
instantiate models, invoke optimizer/backward/EMA or discover pytest tests.
"""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "full": ".github/workflows/jepa-v5-pipeline-identity-contract-macha-no-training.yml",
    "integration": ".github/workflows/jepa-v5-journal-v2-integration-macha-no-training.yml",
    "thread": ".github/workflows/jepa-v5-journal-v2-579-thread-completion-macha-no-training.yml",
}
ALLOWLIST = ROOT / "scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py"


class ExplicitCollectionSafetyTests(unittest.TestCase):
    def test_all_three_workflows_validate_explicit_inventory_before_collection(self):
        for name, path in WORKFLOWS.items():
            with self.subTest(suite=name):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn(
                    "python scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py "
                    f"--suite {name} --verify", source)

    def test_all_three_workflows_execute_only_explicit_guarded_test_inventory(self):
        for name, path in WORKFLOWS.items():
            with self.subTest(suite=name):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn(
                    "python scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py "
                    f"--suite {name} --pytest", source)
                self.assertNotIn("$(ls tests/", source)
                self.assertNotIn("python -m pytest -q tests/test_jepa_v5_*.py", source)
                self.assertNotIn("python -m pytest -q tests/test_jepa_synth2048_attempt_journal_v2*.py", source)

    def test_manifest_exists_and_contains_explicit_only_gate(self):
        self.assertTrue(ALLOWLIST.is_file(), "MISSING_EXPLICIT_TEST_ALLOWLIST")
        source = ALLOWLIST.read_text(encoding="utf-8")
        self.assertIn("def verify_inventory(", source)
        self.assertIn("ast.parse(", source)
        self.assertIn("subprocess.run(", source)
        self.assertIn("NO_TRAINING_TEST_INVENTORY", source)


if __name__ == "__main__":
    unittest.main()
