import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[2] / "scripts" / "v4" / "github_complete_preservation_sync.py"
SPEC = importlib.util.spec_from_file_location("complete_preservation", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CompletePreservationClassificationTests(unittest.TestCase):
    def base(self, **updates):
        row = {
            "path": "outputs/run/FINAL_ADJUDICATION.md",
            "bytes": "100",
            "classification": "HISTORICAL_DECISION",
            "decision_bearing": "True",
            "sensitive_class": "REVIEW_SAFE",
            "large_or_generated": "False",
            "git_filter_alters_bytes": "False",
        }
        row.update(updates)
        return row

    def test_generated_python_and_pytest_outputs_are_excluded(self):
        for path in (
            "scripts/v4/__pycache__/x.pyc",
            "outputs/v4/pytest-run/test_x/result.json",
            "results/v4/.pytest-cache/test_x/result.csv",
            "results/v4/.stage81a3_run/test_catalog_is_deterministic_0/first/result.csv",
        ):
            decision = MODULE.classify_row(self.base(path=path))
            self.assertEqual(decision.disposition, "EXCLUDE_GENERATED")

    def test_protected_and_checkpoint_material_are_ledger_only(self):
        protected = MODULE.classify_row(
            self.base(sensitive_class="PROTECTED_HUMAN_DATA_BLOCKED")
        )
        checkpoint = MODULE.classify_row(
            self.base(path="outputs/run/model.pt", classification="CHECKPOINT")
        )
        self.assertEqual(protected.disposition, "LEDGER_HASH_ONLY_PROTECTED")
        self.assertEqual(checkpoint.disposition, "LEDGER_HASH_ONLY_LARGE_REPRODUCIBLE")

    def test_current_code_stays_at_natural_path(self):
        row = self.base(
            path="scripts/v4/current_tool.py",
            classification="CURRENT_SOURCE",
            git_filter_alters_bytes="True",
        )
        decision = MODULE.classify_row(row)
        self.assertEqual(decision.disposition, "SYNC_CURRENT_CANONICAL")
        self.assertEqual(decision.destination, "scripts/v4/current_tool.py")
        self.assertFalse(decision.exact_byte_required)

    def test_historical_filter_altered_file_uses_exact_byte_archive(self):
        row = self.base(git_filter_alters_bytes="True")
        decision = MODULE.classify_row(row)
        self.assertEqual(decision.disposition, "SYNC_HISTORICAL_EXACT_BYTES")
        self.assertEqual(
            decision.destination,
            "docs/history/exact_bytes/outputs/run/FINAL_ADJUDICATION.md",
        )
        self.assertTrue(decision.exact_byte_required)

    def test_decision_bearing_failed_stop_is_preserved(self):
        row = self.base(path="outputs/run_failed/STOP_REPORT.json")
        decision = MODULE.classify_row(row)
        self.assertIn(
            decision.disposition,
            {"SYNC_HISTORICAL_NORMAL", "SYNC_HISTORICAL_EXACT_BYTES"},
        )

    def test_archive_member_identifier_is_never_a_literal_destination(self):
        decision = MODULE.classify_row(self.base(path="packet.zip::inside/report.json"))
        self.assertEqual(decision.disposition, "EXCLUDE_DUPLICATE_NONAUTHORITY")
        self.assertEqual(decision.destination, "")

    def test_secret_scanner_detects_high_confidence_tokens_and_private_keys(self):
        token_fixture = b"OPENAI_API_KEY=sk-" + b"proj-abcdefghijklmnop"
        key_fixture = b"-----BEGIN " + b"PRIVATE KEY-----"
        self.assertTrue(MODULE.detect_secrets(token_fixture))
        self.assertTrue(MODULE.detect_secrets(key_fixture))
        self.assertFalse(MODULE.detect_secrets(b"sha256=0123456789abcdef" * 4))


if __name__ == "__main__":
    unittest.main()
