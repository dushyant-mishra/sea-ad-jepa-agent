import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v64"))

import validate_stage4_execution_authority_v1 as v  # noqa: E402


CONTRACT = json.loads(
    (ROOT / "results" / "v64" / "V66_STAGE4_EXECUTION_AUTHORITY_CONTRACT_V1.json")
    .read_text(encoding="utf-8")
)


def valid_manifest():
    return {
        "schema": "V66_STAGE4_AUTHORITY_INPUT_MANIFEST_V1",
        "correspondence_opened": False,
        "stage4_authorized": False,
        "training": "OFF",
        "multimodal_training": "OFF",
        "Morabito": "PROTECTED",
        "TD60": "BLOCKED",
        "phase_b_aggregate_binding":
            CONTRACT["accepted_execution_parent"]["phase_b_aggregate_binding"],
        "qualifying_donors":
            CONTRACT["accepted_execution_parent"]["qualifying_donors"],
        "metacells": CONTRACT["accepted_execution_parent"]["metacells"],
        "t5_rows": CONTRACT["accepted_execution_parent"]["t5_rows"],
        "availability_state_vocabulary": copy.deepcopy(
            CONTRACT["frozen_state_vocabulary"]),
        "statistical_rules": copy.deepcopy(CONTRACT["frozen_statistical_rules"]),
        "missingness_rules": copy.deepcopy(CONTRACT["missingness_rules"]),
        "requested_actions": [],
        "files": {},
    }


class Stage4AuthorityMutationTests(unittest.TestCase):
    def assertFailsWith(self, manifest, token):
        errors = v.validate_manifest_structural(manifest, CONTRACT)
        self.assertTrue(any(token in e for e in errors), errors)

    def test_clean_structural_manifest_passes(self):
        self.assertEqual(v.validate_manifest_structural(valid_manifest(), CONTRACT), [])

    def test_cannot_self_authorize(self):
        m = valid_manifest()
        m["stage4_authorized"] = True
        self.assertFailsWith(m, "STAGE4_MUST_REMAIN_UNAUTHORIZED")

    def test_correspondence_must_remain_unopened(self):
        m = valid_manifest()
        m["correspondence_opened"] = True
        self.assertFailsWith(m, "CORRESPONDENCE_MUST_BE_UNOPENED")

    def test_outcome_field_is_rejected_even_if_nested(self):
        m = valid_manifest()
        m["debug"] = {"delta_gene_balanced": 0.1}
        self.assertFailsWith(m, "OUTCOME_OR_AUTHORIZATION_FIELD_PRESENT")

    def test_primary_weighting_cannot_drift(self):
        m = valid_manifest()
        m["statistical_rules"]["primary_weighting"] = "PROMOTER_EQUAL"
        self.assertFailsWith(m, "RULE_DRIFT:primary_weighting")

    def test_bootstrap_unit_cannot_drift(self):
        m = valid_manifest()
        m["statistical_rules"]["bootstrap_unit"] = "METACELL"
        self.assertFailsWith(m, "RULE_DRIFT:bootstrap_unit")

    def test_bootstrap_count_cannot_drift(self):
        m = valid_manifest()
        m["statistical_rules"]["bootstrap_replicates"] = 1000
        self.assertFailsWith(m, "RULE_DRIFT:bootstrap_replicates")

    def test_r3_semantics_cannot_drift(self):
        m = valid_manifest()
        m["statistical_rules"]["r3"] = "MONTE_CARLO_LARGE_ARM"
        self.assertFailsWith(m, "RULE_DRIFT:r3")

    def test_state_vocabulary_cannot_reorder(self):
        m = valid_manifest()
        m["availability_state_vocabulary"][0:2] = reversed(
            m["availability_state_vocabulary"][0:2])
        self.assertFailsWith(m, "STATE_VOCABULARY_DRIFT")

    def test_not_measured_cannot_be_zero_filled(self):
        m = valid_manifest()
        m["missingness_rules"]["not_measured_may_be_zero_filled"] = True
        self.assertFailsWith(m, "MISSINGNESS_RULE_DRIFT:not_measured_may_be_zero_filled")

    def test_metacell_count_cannot_drift(self):
        m = valid_manifest()
        m["metacells"] = 3230
        self.assertFailsWith(m, "METACELL_COUNT_DRIFT")

    def test_no_execution_action_before_successor_authorization(self):
        m = valid_manifest()
        m["requested_actions"] = ["compute_correspondence"]
        self.assertFailsWith(m, "REQUESTED_ACTIONS_MUST_BE_EMPTY_BEFORE_AUTHORIZATION")


if __name__ == "__main__":
    unittest.main()
