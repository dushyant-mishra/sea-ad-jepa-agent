from __future__ import annotations

import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "v5" / "verify_jepa_lane_handoff_state_v1.py"
SPEC = importlib.util.spec_from_file_location("verify_jepa_lane_handoff_state_v1", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

HISTORICAL = ROOT / "results" / "target_discovery" / "JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.json"
READINESS = ROOT / "results" / "target_discovery" / "JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.json"
STATE = ROOT / "docs" / "agent" / "JEPA_LANE_TAKEOVER_STATE_20261013.json"
CUSTODY = ROOT / "docs" / "agent" / "JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows):
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


class HandoffStateTests(unittest.TestCase):
    def setUp(self):
        self.state = read_json(STATE)
        self.custody = read_csv(CUSTODY)

    def run_values(self, state=None, custody=None):
        state = copy.deepcopy(self.state if state is None else state)
        custody = copy.deepcopy(self.custody if custody is None else custody)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            state_path = td / "state.json"
            custody_path = td / "custody.csv"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            write_csv(custody_path, custody)
            return M.validate_handoff(
                historical_path=HISTORICAL,
                readiness_path=READINESS,
                handoff_state_path=state_path,
                custody_path=custody_path,
            )

    def test_current_handoff_passes(self):
        result = M.validate_handoff(
            historical_path=HISTORICAL,
            readiness_path=READINESS,
            handoff_state_path=STATE,
            custody_path=CUSTODY,
        )
        self.assertEqual(result["status"], "PASS_JEPA_LANE_HANDOFF_STATE_V1")

    def test_rejects_training_authority(self):
        value = copy.deepcopy(self.state)
        value["authority"]["training_authorized"] = True
        with self.assertRaisesRegex(M.HandoffStateError, "training_authorized"):
            self.run_values(state=value)

    def test_rejects_controller_adjudication_authority(self):
        value = copy.deepcopy(self.state)
        value["authority"]["controller_adjudication_authorized"] = True
        with self.assertRaisesRegex(M.HandoffStateError, "controller_adjudication_authorized"):
            self.run_values(state=value)

    def test_rejects_controller_transport_in_phase1(self):
        value = copy.deepcopy(self.state)
        value["td_chain"]["phase1"]["controller_transport_allowed_in_environment"] = True
        with self.assertRaisesRegex(M.HandoffStateError, "controller transport"):
            self.run_values(state=value)

    def test_rejects_missing_stop_after_receipt(self):
        value = copy.deepcopy(self.state)
        value["td_chain"]["phase1"]["must_stop_after_receipt"] = False
        with self.assertRaisesRegex(M.HandoffStateError, "STOP-after-receipt"):
            self.run_values(state=value)

    def test_rejects_raw_controller_hash_drift(self):
        value = copy.deepcopy(self.state)
        value["td_chain"]["synthetic_v2_1"]["controller_manifest_raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(M.HandoffStateError, "controller_manifest_raw_sha256"):
            self.run_values(state=value)

    def test_rejects_commitment_hash_drift(self):
        value = copy.deepcopy(self.state)
        value["td_chain"]["synthetic_v2_1"]["controller_semantic_commitment_sha256"] = "0" * 64
        with self.assertRaisesRegex(M.HandoffStateError, "controller_semantic_commitment_sha256"):
            self.run_values(state=value)

    def test_rejects_local_artifact_hash_drift(self):
        rows = copy.deepcopy(self.custody)
        row = next(x for x in rows if x["filename_or_identity"] == "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip")
        row["sha256"] = "0" * 64
        with self.assertRaisesRegex(M.HandoffStateError, "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip"):
            self.run_values(custody=rows)

    def test_rejects_controller_archive_phase1_policy_drift(self):
        rows = copy.deepcopy(self.custody)
        row = next(x for x in rows if x["filename_or_identity"] == "TD_RELATIONAL_SYNTHETIC_V2_1_CONTROLLER_ARCHIVE")
        row["upload_policy"] = "SAFE_HASH_ONLY"
        with self.assertRaisesRegex(M.HandoffStateError, "phase1 custody policy"):
            self.run_values(custody=rows)

    def test_rejects_large_local_binary_public_upload_policy(self):
        rows = copy.deepcopy(self.custody)
        row = next(x for x in rows if x["filename_or_identity"] == "checkpoints.zip")
        row["upload_policy"] = "PUBLIC_UPLOAD_ALLOWED"
        with self.assertRaisesRegex(M.HandoffStateError, "large artifact"):
            self.run_values(custody=rows)


if __name__ == "__main__":
    unittest.main()
