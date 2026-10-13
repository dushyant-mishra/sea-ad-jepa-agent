from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "agent" / "TD_SYNTHETIC_PHASE2_ADJUDICATION_7659030c_20261013"
RECEIPT = BASE / "output" / "TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4.json"
SOURCE_SHA = BASE / "SOURCE_SHA256.txt"
RUN_RECORD = BASE / "record" / "ADJUDICATE_RUN_RECORD.txt"
INPUT_VERIFICATION = BASE / "record" / "INPUT_VERIFICATION.txt"
AUTH_ORDER = BASE / "record" / "AUTH_ORDER_CHECK.txt"
POST_STATE = BASE / "record" / "POST_RUN_STATE.txt"

EXPECTED_RECEIPT_SHA = "5382034332f24b0e37954b4f8e2cefe958f21ff644e6fd1ffec150d2478aa61b"
EXPECTED_PHASE1_RECEIPT = "e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684"
EXPECTED_PACKAGE = "0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115"
EXPECTED_BINDING = "ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44"
EXPECTED_CONTROLLER_MANIFEST = "87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9"
EXPECTED_HEAD = "7659030cd2fc9a2662c67a9bf4d23e0e8f3f1606"
EXPECTED = {
    "REL_BROAD_MESO_POSITIVE": "PASS",
    "REL_FINE_RECURRENT_POSITIVE": "PASS",
    "REL_RARE_LOCAL_ISLAND_POSITIVE": "PASS",
    "REL_MULTI_ISLAND_POSITIVE": "PASS",
    "REL_DONOR_RESTRICTED_POSITIVE": "PASS",
    "REL_SOURCE_VISIBILITY_STRESS": "PASS",
    "REL_TECHNICAL_TWIN_NEGATIVE": "FAIL",
    "REL_NULL_NEGATIVE": "FAIL",
    "REL_UNDERPOWERED_POSITIVE": "NOT_ESTIMABLE",
}


class Phase2AuditError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _all_false(mapping: dict) -> bool:
    return isinstance(mapping, dict) and bool(mapping) and all(value is False for value in mapping.values())


def audit() -> dict:
    if _sha256(RECEIPT) != EXPECTED_RECEIPT_SHA:
        raise Phase2AuditError("adjudication receipt SHA-256 mismatch")
    source = SOURCE_SHA.read_text(encoding="utf-8")
    if f"{EXPECTED_RECEIPT_SHA}  output/TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4.json" not in source:
        raise Phase2AuditError("source hash ledger does not bind receipt")

    doc = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if doc.get("schema") != "JEPA_TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4":
        raise Phase2AuditError("wrong adjudication schema")
    if doc.get("blinded_fit_receipt_sha256") != EXPECTED_PHASE1_RECEIPT:
        raise Phase2AuditError("phase-1 receipt binding mismatch")
    if doc.get("package_sha256") != EXPECTED_PACKAGE:
        raise Phase2AuditError("package binding mismatch")

    qualification = doc.get("qualification")
    readiness = doc.get("readiness")
    gate = qualification.get("gate_qualification") if isinstance(qualification, dict) else None
    if qualification.get("status") != "QUALIFIED" or qualification.get("missing_requirements") != []:
        raise Phase2AuditError("qualification is not exact QUALIFIED with no missing requirements")
    if readiness.get("status") != "READY_FOR_INDEPENDENT_QUALIFICATION_AUDIT__NO_REAL_EXECUTION_AUTHORITY":
        raise Phase2AuditError("readiness terminal drift")
    if readiness.get("qualification_status") != "QUALIFIED" or readiness.get("real_execution_authorized") is not False:
        raise Phase2AuditError("readiness qualification/authority drift")
    if gate.get("gate_id") != "R_RELATIONAL_SUCCESSOR_TEST_OF_TEST_V2":
        raise Phase2AuditError("gate identity drift")
    if gate.get("candidate_id") != "C2_RELATIONAL_SHARED":
        raise Phase2AuditError("candidate identity drift")
    if gate.get("qualification_status") != "QUALIFIED" or gate.get("failure_scope") != "TEST_QUALIFICATION_ONLY":
        raise Phase2AuditError("test-only qualification scope drift")

    results = gate.get("challenge_results")
    if not isinstance(results, list) or len(results) != 9:
        raise Phase2AuditError("exactly nine challenge results required")
    observed = {}
    for row in results:
        capability = row.get("capability_id")
        if capability in observed or capability not in EXPECTED:
            raise Phase2AuditError("duplicate or unknown challenge capability")
        if row.get("expected_status") != EXPECTED[capability]:
            raise Phase2AuditError(f"controller expected status drift: {capability}")
        if row.get("observed_status") != EXPECTED[capability] or row.get("matched") is not True:
            raise Phase2AuditError(f"challenge mismatch: {capability}")
        observed[capability] = row.get("observed_status")
    if observed != EXPECTED:
        raise Phase2AuditError("challenge capability coverage mismatch")
    if qualification.get("capability_statuses") != EXPECTED:
        raise Phase2AuditError("qualification capability summary mismatch")

    for authority in (
        doc.get("authority"), qualification.get("authority"), gate.get("authority"), readiness.get("authority")
    ):
        if not _all_false(authority):
            raise Phase2AuditError("authority block must be nonempty and all false")

    run_record = RUN_RECORD.read_text(encoding="utf-8")
    if f"head={EXPECTED_HEAD}" not in run_record or "adjudicate_exit=0" not in run_record:
        raise Phase2AuditError("run record head/exit mismatch")
    if run_record.count("cmd=python scripts/v5/td_relational_successor_disk_runner_v4.py adjudicate") != 1:
        raise Phase2AuditError("exactly one adjudicate command required in frozen run record")
    if f"--blinded-receipt-sha256 {EXPECTED_PHASE1_RECEIPT}" not in run_record:
        raise Phase2AuditError("run command receipt binding mismatch")
    if f"--authenticated-package-sha256 {EXPECTED_PACKAGE}" not in run_record:
        raise Phase2AuditError("run command package binding mismatch")

    inputs = INPUT_VERIFICATION.read_text(encoding="utf-8")
    for expected in (EXPECTED_BINDING, EXPECTED_PACKAGE, EXPECTED_CONTROLLER_MANIFEST, EXPECTED_PHASE1_RECEIPT):
        if expected not in inputs:
            raise Phase2AuditError(f"mandatory input identity absent: {expected}")
    if "controller manifest raw:" not in inputs or "-> MATCH" not in inputs:
        raise Phase2AuditError("controller raw-manifest custody check absent")
    if "package and controller file sets identical (as sets) to prior attempt record" not in inputs:
        raise Phase2AuditError("controller transport continuity check absent")

    auth_order = AUTH_ORDER.read_text(encoding="utf-8")
    if "159:    package, fit_receipt, actual_blinded_sha = authenticate_blinded_phase_inputs(" not in auth_order:
        raise Phase2AuditError("pre-controller authentication call not frozen")
    if "167:    controller_manifest = V3._read_controller_json(controller_manifest_path)" not in auth_order:
        raise Phase2AuditError("controller read ordering not frozen")

    post = POST_STATE.read_text(encoding="utf-8")
    if EXPECTED_HEAD not in post:
        raise Phase2AuditError("post-run repaired head not recorded")

    return {
        "status": "PASS_PHASE2_EXECUTION_AND_CUSTODY",
        "receipt_sha256": EXPECTED_RECEIPT_SHA,
        "qualification_status": "QUALIFIED",
        "readiness_status": readiness["status"],
        "challenge_count": len(results),
        "matched_count": sum(row["matched"] is True for row in results),
        "capability_statuses": observed,
        "scientific_scope": "TEST_QUALIFICATION_ONLY",
        "authority": dict(doc["authority"]),
        "real_execution_authorized": False,
        "real_td_authorized": False,
        "target_selection_authorized": False,
        "representation_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
