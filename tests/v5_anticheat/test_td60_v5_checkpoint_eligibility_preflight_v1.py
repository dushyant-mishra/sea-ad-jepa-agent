"""No-training negative controls for TD60/V5 exposure-checkpoint eligibility."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from scripts.v5_anticheat import td60_v5_checkpoint_eligibility_preflight_v1 as M


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.p = {
            "schema": M.V5_SCHEMA,
            "scientific_target_frozen": True,
            "proposal_policy_frozen": False,
            "evidence_schedule_frozen": False,
            "production_compute_kernel_frozen": False,
            "production_training_presentations": None,
            "production_ema_half_life_presentations": None,
            **M.UNAUTHORIZED,
        }

    def run_candidate(self, p):
        return M.assess_v5_candidate(p, source_sha256=hashlib.sha256(b"fixture").hexdigest())

    def test_existing_v5_unfrozen_status_holds(self):
        r = self.run_candidate(self.p)
        self.assertEqual(r["status"], M.STOP)
        self.assertIn("V5_Q40_IS_MECHANICS_ONLY__NOT_TD60_LEARNED_BIOLOGY", r["unresolved"])
        self.assertIn("UNFROZEN_PRODUCTION_TRAINING_PRESENTATIONS", r["unresolved"])
        self.assertEqual(r["td60_evaluable_cases_if_separately_authorized"], 48)
        self.assertTrue(all(v is False for v in r["authority"].values()))

    def test_even_self_declared_fully_frozen_cannot_issue_td60(self):
        p = dict(self.p, proposal_policy_frozen=True, evidence_schedule_frozen=True,
                 production_compute_kernel_frozen=True, production_training_presentations=4553407,
                 production_ema_half_life_presentations=65536)
        r = self.run_candidate(p)
        self.assertEqual(r["status"], M.STOP)
        self.assertFalse(r["external_issuer_authenticated"])
        self.assertIsNone(r["checkpoint_selected"])
        self.assertIn("NO_INDEPENDENTLY_AUTHENTICATED_V5_EXPOSURE_CHECKPOINT_OR_TD60_RELEASE", r["unresolved"])

    def test_boolean_and_float_horizons_cannot_masquerade_as_integers(self):
        for bad in (True, 4.0, "4", 0, -4, None):
            with self.subTest(bad=bad):
                p = dict(self.p, production_training_presentations=bad,
                         production_ema_half_life_presentations=bad)
                r = self.run_candidate(p)
                self.assertIn("UNFROZEN_PRODUCTION_TRAINING_PRESENTATIONS", r["unresolved"])
                self.assertIn("UNFROZEN_PRODUCTION_EMA_HALF_LIFE_PRESENTATIONS", r["unresolved"])

    def test_any_authority_flag_or_unknown_schema_refuses(self):
        for flag in M.UNAUTHORIZED:
            with self.subTest(flag=flag):
                p = copy.deepcopy(self.p)
                p[flag] = True
                with self.assertRaisesRegex(ValueError, "claims authority"):
                    self.run_candidate(p)
        with self.assertRaisesRegex(ValueError, "schema"):
            self.run_candidate({**self.p, "schema": "older"})

    def test_digest_validation(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            M.assess_v5_candidate(self.p, source_sha256="0" * 63)

    def test_committed_v5_candidate_is_still_hold(self):
        root = Path(__file__).resolve().parents[2]
        raw = (root / "docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_AUTHORITY_CANDIDATE.json").read_bytes()
        r = M.assess_v5_candidate(json.loads(raw), source_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(r["status"], M.STOP)
        self.assertFalse(r["biological_outcomes_opened"])
        self.assertFalse(r["external_issuer_authenticated"])
        self.assertEqual(r["source_candidate_sha256"], hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
