from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "v5" / "verify_jepa_lane_takeover_manifest_v1.py"
SPEC = importlib.util.spec_from_file_location("verify_jepa_lane_takeover_manifest_v1", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

HISTORICAL_PATH = ROOT / "results" / "target_discovery" / "JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.json"
READINESS_PATH = ROOT / "results" / "target_discovery" / "JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class TakeoverManifestTests(unittest.TestCase):
    def setUp(self):
        self.historical = load(HISTORICAL_PATH)
        self.readiness = load(READINESS_PATH)

    def run_values(self, historical, readiness):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            hp = tmp / "historical.json"
            rp = tmp / "readiness.json"
            hp.write_text(json.dumps(historical), encoding="utf-8")
            rp.write_text(json.dumps(readiness), encoding="utf-8")
            return M.validate_takeover_manifests(hp, rp)

    def test_current_manifests_pass(self):
        result = M.validate_takeover_manifests(HISTORICAL_PATH, READINESS_PATH)
        self.assertEqual(result["status"], "PASS_JEPA_LANE_TAKEOVER_MANIFEST_V1")
        self.assertEqual(result["td_repair_sha"], M.EXPECTED_TD_REPAIR_SHA)
        self.assertEqual(result["synthetic_v2_1_sha"], M.EXPECTED_SYNTHETIC_SHA)

    def test_rejects_training_authority_flip(self):
        value = copy.deepcopy(self.readiness)
        value["authority"]["training_authorized"] = True
        with self.assertRaisesRegex(M.TakeoverManifestError, "training_authorized"):
            self.run_values(self.historical, value)

    def test_rejects_stage4_authority_flip(self):
        value = copy.deepcopy(self.historical)
        value["authority"]["stage4_authorized"] = True
        with self.assertRaisesRegex(M.TakeoverManifestError, "stage4_authorized"):
            self.run_values(value, self.readiness)

    def test_rejects_stale_td_repair_sha(self):
        value = copy.deepcopy(self.historical)
        value["current_td_chain"]["td_repair_pr320_sha"] = "0" * 40
        with self.assertRaisesRegex(M.TakeoverManifestError, "td_repair_pr320_sha"):
            self.run_values(value, self.readiness)

    def test_rejects_stale_synthetic_sha(self):
        value = copy.deepcopy(self.readiness)
        value["current_td_dependency"]["synthetic_v2_1_sha"] = "0" * 40
        with self.assertRaisesRegex(M.TakeoverManifestError, "synthetic_v2_1_sha"):
            self.run_values(self.historical, value)

    def test_rejects_controller_adjudication_authority(self):
        value = copy.deepcopy(self.readiness)
        value["current_td_dependency"]["controller_adjudication_authorized"] = True
        with self.assertRaisesRegex(M.TakeoverManifestError, "controller adjudication"):
            self.run_values(self.historical, value)

    def test_rejects_unresolved_gene_identity_promoted_active(self):
        value = copy.deepcopy(self.historical)
        item = next(x for x in value["entries"] if x["id"] == "H19_TEACHER_VIEW_COUNT")
        item["current_status"] = "ACTIVE_PRIMARY"
        with self.assertRaisesRegex(M.TakeoverManifestError, "unresolved gene-identity evidence promoted"):
            self.run_values(value, self.readiness)

    def test_allows_unresolved_identity_only_as_replay_required(self):
        value = copy.deepcopy(self.historical)
        item = next(x for x in value["entries"] if x["id"] == "H19_TEACHER_VIEW_COUNT")
        self.assertEqual(item["current_status"], "REPLAY_REQUIRED")
        result = self.run_values(value, self.readiness)
        self.assertEqual(result["status"], "PASS_JEPA_LANE_TAKEOVER_MANIFEST_V1")

    def test_rejects_duplicate_historical_id(self):
        value = copy.deepcopy(self.historical)
        value["entries"].append(copy.deepcopy(value["entries"][0]))
        with self.assertRaisesRegex(M.TakeoverManifestError, "unique"):
            self.run_values(value, self.readiness)

    def test_rejects_biological_execution_claim(self):
        value = copy.deepcopy(self.historical)
        value["current_td_chain"]["biological_test_of_test_executed"] = True
        with self.assertRaisesRegex(M.TakeoverManifestError, "biological test-of-test"):
            self.run_values(value, self.readiness)


if __name__ == "__main__":
    unittest.main()
