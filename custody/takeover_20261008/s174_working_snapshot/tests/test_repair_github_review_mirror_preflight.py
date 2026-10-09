import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "v4" / "repair_github_review_mirror_preflight.py"
SPEC = importlib.util.spec_from_file_location("repair_github_preflight", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RepairGithubReviewMirrorPreflightTests(unittest.TestCase):
    def test_normalize_boolean_repairs_match_repr_and_blank(self):
        self.assertEqual(MODULE.normalize_boolean("True"), "True")
        self.assertEqual(MODULE.normalize_boolean("False"), "False")
        self.assertEqual(MODULE.normalize_boolean(""), "False")
        self.assertEqual(
            MODULE.normalize_boolean("<re.Match object; span=(1, 9), match='manifest'>"),
            "True",
        )
        with self.assertRaises(ValueError):
            MODULE.normalize_boolean("yes")

    def test_pytest_staging_failed_and_retry_outputs_are_excluded(self):
        for path in (
            "outputs/v4/pytest-run/test_x/a.json",
            "results/v4/.pytest-run/test_x/a.json",
            "outputs/full104/_staging_x/a.json",
            "outputs/full104/prepublication/a.json",
            "outputs/full104/failed_review/a.json",
            "outputs/full104/retry_1/a.json",
        ):
            reason = MODULE.default_exclusion_reason(path)
            self.assertIsNotNone(reason, path)

    def test_donor_and_filter_altered_candidates_are_ledger_only(self):
        donor = MODULE.disposition_for(
            {"source_local_path": "x", "sensitive_class": "DONOR_LEVEL_HUMAN_DATA_REVIEW_REQUIRED", "git_filter_alters_bytes": "False"}
        )
        filtered = MODULE.disposition_for(
            {"source_local_path": "x", "sensitive_class": "REVIEW_SAFE", "git_filter_alters_bytes": "True"}
        )
        self.assertEqual(donor, "LEDGER_HASH_ONLY_DONOR_LEVEL")
        self.assertEqual(filtered, "LEDGER_HASH_ONLY_GIT_FILTER_ALTERED")

    def test_historical_destination_preserves_full_run_identity(self):
        first = MODULE.historical_destination(
            "outputs/full104_v014/02_expression_interface_preflight_v3/FREEZE.json"
        )
        second = MODULE.historical_destination(
            "outputs/full104_v014/02_expression_interface_preflight_v4/FREEZE.json"
        )
        self.assertNotEqual(first, second)
        self.assertEqual(
            first,
            "docs/history/full104_v014/02_expression_interface_preflight_v3/FREEZE.json",
        )

    def test_conflicting_paths_are_disambiguated_and_unique(self):
        rows = [
            {"source_local_path": "outputs/a/file.json", "filesystem_sha256": "a" * 64},
            {"source_local_path": "outputs/A/file.json", "filesystem_sha256": "b" * 64},
        ]
        paths = MODULE.assign_unique_destinations(rows)
        self.assertEqual(len(paths), 2)
        self.assertEqual(len({p.casefold() for p in paths}), 2)

    def test_zip_member_identifier_is_never_a_repo_path(self):
        row = {
            "source_local_path": "archive.zip::folder/a.json",
            "sensitive_class": "REVIEW_SAFE",
            "git_filter_alters_bytes": "False",
        }
        self.assertEqual(MODULE.disposition_for(row), "LEDGER_HASH_ONLY_ARCHIVE_MEMBER")


if __name__ == "__main__":
    unittest.main()
