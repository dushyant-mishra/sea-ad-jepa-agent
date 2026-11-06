"""Only source-level checks. NEVER collect historical V5 optimizer/EMA tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ".github/workflows/v64-runtime-core-reconciliation.yml",
    ".github/workflows/v5-inactive-runtime-step-guard.yml",
    ".github/workflows/jepa-synth2048-v5-guarded-readiness.yml",
    ".github/workflows/current-authority-surface-guard.yml",
)
GUARD = "python scripts/v5/jepa_v5_legacy_step_ci_quarantine_v1.py --verify"


class HistoricalStepTestsQuarantined(unittest.TestCase):
    def test_all_four_automatic_v5_routes_have_static_quarantine(self):
        for name in WORKFLOWS:
            with self.subTest(workflow=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn(GUARD, source)

    def test_no_historical_step_capable_test_execution(self):
        for name in WORKFLOWS[:3]:
            with self.subTest(workflow=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                self.assertNotIn("python -m pytest", source)
                self.assertNotIn("pip install", source)
        current = (ROOT / WORKFLOWS[3]).read_text(encoding="utf-8")
        runtime = current.split("  inactive-runtime-step-guard:", 1)[1]
        self.assertNotIn("python -m pytest", runtime)
        self.assertNotIn("pip install", runtime)

    def test_quarantine_guard_is_present(self):
        path = ROOT / "scripts/v5/jepa_v5_legacy_step_ci_quarantine_v1.py"
        self.assertTrue(path.is_file(), "LEGACY_STEP_CI_GUARD_MISSING")
        contents = path.read_text(encoding="utf-8")
        self.assertIn("def verify_quarantine(", contents)
        self.assertIn("ast.parse(", contents)


if __name__ == "__main__":
    unittest.main()
