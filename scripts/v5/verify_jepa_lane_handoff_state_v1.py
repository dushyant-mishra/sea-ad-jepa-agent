from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
from typing import Mapping


class HandoffStateError(ValueError):
    pass


ROOT = Path(__file__).resolve().parents[2]
_PARENT_PATH = ROOT / "scripts" / "v5" / "verify_jepa_lane_takeover_manifest_v1.py"
_SPEC = importlib.util.spec_from_file_location("verify_jepa_lane_takeover_manifest_v1", _PARENT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("unable to load takeover manifest validator")
PARENT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(PARENT)

HANDOFF_SCHEMA = "JEPA_LANE_TAKEOVER_STATE_V1"
EXPECTED_TD_REPAIR_SHA = PARENT.EXPECTED_TD_REPAIR_SHA
EXPECTED_SYNTHETIC_SHA = PARENT.EXPECTED_SYNTHETIC_SHA
EXPECTED_PACKAGE_SHA256 = PARENT.EXPECTED_PACKAGE_SHA256
EXPECTED_PREFIT_SHA256 = PARENT.EXPECTED_PREFIT_SHA256
EXPECTED_CERT_SHA256 = PARENT.EXPECTED_CERT_SHA256
EXPECTED_CONTROLLER_ARCHIVE_SHA256 = "f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328"
EXPECTED_CONTROLLER_MANIFEST_RAW_SHA256 = "87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9"
EXPECTED_CONTROLLER_COMMITMENT_SHA256 = "a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293"

EXPECTED_LOCAL_HASHES = {
    "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip": "63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7",
    "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip": "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444",
    "66e64913-959f-4a7c-bbfe-6ff906fb281d.npz": "001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70",
    "expression.zip": "1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4",
    "checkpoints.zip": "ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c",
    "t1_checkpoint_u0200.zip": "0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c",
    "Status and Repair Plan.txt": "cb2befc374e4b594fb6d04bbb7c30a0ca702913ddc9d568fbfbf8ebca7bb7c56",
    "WSL execution issue.txt": "cd1c50bbec4c80b9b35f1824bba9112c7dbb357ede586b0a46e98532f57e474e",
}


def _read_json(path: Path | str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HandoffStateError(f"JSON root must be object: {path}")
    return value


def _require_false(authority: object) -> None:
    required = {
        "real_td_execution_authorized",
        "target_selection_authorized",
        "representation_selection_authorized",
        "td60_authorized",
        "stage4_authorized",
        "multimodal_training_authorized",
        "training_authorized",
        "controller_adjudication_authorized",
    }
    if not isinstance(authority, Mapping):
        raise HandoffStateError("handoff authority must be object")
    if not required.issubset(authority):
        raise HandoffStateError("handoff authority keys missing")
    for key in sorted(required):
        if authority.get(key) is not False:
            raise HandoffStateError(f"handoff illegally authorizes {key}")


def _validate_state(value: Mapping) -> None:
    if value.get("schema") != HANDOFF_SCHEMA:
        raise HandoffStateError("wrong handoff schema")
    _require_false(value.get("authority"))
    if value.get("terminal") != "HISTORICAL_AUDIT_FROZEN__GENE_IDENTITY_RECLASSIFIED__DOWNSTREAM_RUNTIME_AUDITED__TD_PHASE1_READY__TRAINING_OFF":
        raise HandoffStateError("unexpected handoff terminal")

    chain = value.get("td_chain")
    if not isinstance(chain, Mapping):
        raise HandoffStateError("td_chain missing")
    repair = chain.get("td_repair")
    synth = chain.get("synthetic_v2_1")
    phase1 = chain.get("phase1")
    if not isinstance(repair, Mapping) or repair.get("sha") != EXPECTED_TD_REPAIR_SHA:
        raise HandoffStateError("TD repair identity mismatch")
    if not isinstance(synth, Mapping) or synth.get("sha") != EXPECTED_SYNTHETIC_SHA:
        raise HandoffStateError("synthetic V2.1 identity mismatch")
    expected_synth = {
        "package_sha256": EXPECTED_PACKAGE_SHA256,
        "prefit_archive_sha256": EXPECTED_PREFIT_SHA256,
        "controller_archive_sha256": EXPECTED_CONTROLLER_ARCHIVE_SHA256,
        "controller_manifest_raw_sha256": EXPECTED_CONTROLLER_MANIFEST_RAW_SHA256,
        "controller_semantic_commitment_sha256": EXPECTED_CONTROLLER_COMMITMENT_SHA256,
        "certification_receipt_sha256": EXPECTED_CERT_SHA256,
        "preflight_terminal": PARENT.EXPECTED_PREFLIGHT_TERMINAL,
    }
    for key, expected in expected_synth.items():
        if synth.get(key) != expected:
            raise HandoffStateError(f"synthetic custody mismatch: {key}")
    if not isinstance(phase1, Mapping):
        raise HandoffStateError("phase1 state missing")
    if phase1.get("controller_transport_allowed_in_environment") is not False:
        raise HandoffStateError("phase1 cannot contain controller transport")
    if phase1.get("adjudication_allowed") is not False:
        raise HandoffStateError("phase1 cannot authorize adjudication")
    if phase1.get("biological_test_of_test_executed") is not False:
        raise HandoffStateError("handoff claims biological test-of-test executed")
    if phase1.get("controller_truth_opened") is not False:
        raise HandoffStateError("handoff claims controller truth opened")
    if phase1.get("must_stop_after_receipt") is not True:
        raise HandoffStateError("phase1 STOP-after-receipt invariant missing")


def _read_custody(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise HandoffStateError("custody manifest empty")
    return rows


def _validate_custody(rows: list[dict[str, str]]) -> None:
    ids = [row.get("artifact_id", "") for row in rows]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise HandoffStateError("custody artifact IDs must be unique and non-empty")
    by_name = {row.get("filename_or_identity"): row for row in rows}
    for name, digest in EXPECTED_LOCAL_HASHES.items():
        row = by_name.get(name)
        if row is None or row.get("sha256") != digest:
            raise HandoffStateError(f"local artifact hash missing/mismatch: {name}")

    synth_expected = {
        "TD_RELATIONAL_SYNTHETIC_V2_1_PACKAGE_IDENTITY": EXPECTED_PACKAGE_SHA256,
        "TD_RELATIONAL_SYNTHETIC_V2_1_PREFIT_ARCHIVE": EXPECTED_PREFIT_SHA256,
        "TD_RELATIONAL_SYNTHETIC_V2_1_CONTROLLER_ARCHIVE": EXPECTED_CONTROLLER_ARCHIVE_SHA256,
        "TD_RELATIONAL_SYNTHETIC_V2_1_CONTROLLER_MANIFEST_RAW": EXPECTED_CONTROLLER_MANIFEST_RAW_SHA256,
        "TD_RELATIONAL_SYNTHETIC_V2_1_CONTROLLER_SEMANTIC_COMMITMENT": EXPECTED_CONTROLLER_COMMITMENT_SHA256,
        "TD_RELATIONAL_SYNTHETIC_V2_1_CERTIFICATION_RECEIPT": EXPECTED_CERT_SHA256,
    }
    for name, digest in synth_expected.items():
        row = by_name.get(name)
        if row is None or row.get("sha256") != digest:
            raise HandoffStateError(f"synthetic custody hash missing/mismatch: {name}")

    controller = by_name["TD_RELATIONAL_SYNTHETIC_V2_1_CONTROLLER_ARCHIVE"]
    if controller.get("upload_policy") != "FORBIDDEN_FROM_PHASE1_CUSTODY":
        raise HandoffStateError("controller archive phase1 custody policy drift")

    for row in rows:
        raw_size = row.get("size_bytes", "")
        if row.get("artifact_id", "").startswith("LOCAL_") and raw_size:
            try:
                size = int(raw_size)
            except ValueError as exc:
                raise HandoffStateError("invalid local artifact size") from exc
            if size >= 1_000_000 and row.get("upload_policy") not in {
                "EXTERNAL_CUSTODY_ONLY__DO_NOT_PUBLIC_UPLOAD",
                "CONTROLLER_MUST_REMAIN_PHYSICALLY_SEPARATE",
                "FORBIDDEN_FROM_PHASE1_CUSTODY",
            }:
                raise HandoffStateError(f"large artifact lacks external-custody upload policy: {row.get('filename_or_identity')}")


def validate_handoff(
    *, historical_path: Path | str, readiness_path: Path | str,
    handoff_state_path: Path | str, custody_path: Path | str,
) -> dict[str, str]:
    PARENT.validate_takeover_manifests(historical_path, readiness_path)
    state = _read_json(handoff_state_path)
    _validate_state(state)
    _validate_custody(_read_custody(custody_path))
    return {
        "status": "PASS_JEPA_LANE_HANDOFF_STATE_V1",
        "td_repair_sha": EXPECTED_TD_REPAIR_SHA,
        "synthetic_v2_1_sha": EXPECTED_SYNTHETIC_SHA,
        "package_sha256": EXPECTED_PACKAGE_SHA256,
        "prefit_archive_sha256": EXPECTED_PREFIT_SHA256,
        "controller_archive_phase1_allowed": "false",
        "training_authorized": "false",
    }


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate JEPA takeover handoff and external custody state")
    p.add_argument("--historical", default="results/target_discovery/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.json")
    p.add_argument("--readiness", default="results/target_discovery/JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.json")
    p.add_argument("--state", default="docs/agent/JEPA_LANE_TAKEOVER_STATE_20261013.json")
    p.add_argument("--custody", default="docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv")
    return p


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    result = validate_handoff(
        historical_path=args.historical,
        readiness_path=args.readiness,
        handoff_state_path=args.state,
        custody_path=args.custody,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
