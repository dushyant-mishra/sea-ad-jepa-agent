from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping


class TakeoverManifestError(ValueError):
    pass


HISTORICAL_SCHEMA = "JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_V1"
READINESS_SCHEMA = "JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_V1"

EXPECTED_TD_REPAIR_SHA = "1f474a44a6baabc667dbfda726e0755426c732e7"
EXPECTED_SYNTHETIC_SHA = "15f519c00137d581e25232c16be52c2b9badd83e"
EXPECTED_PACKAGE_SHA256 = "0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115"
EXPECTED_PREFIT_SHA256 = "ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803"
EXPECTED_CERT_SHA256 = "fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9"
EXPECTED_PREFLIGHT_TERMINAL = "READY_TO_EXECUTE_BLIND_FIT"

FORBIDDEN_TRUE_AUTHORITY = {
    "target_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "multimodal_training_authorized",
    "training_authorized",
}

_ALLOWED_UNRESOLVED_STATUSES = {"REPLAY_REQUIRED", "HISTORICAL_ONLY", "CONTROL_ONLY"}


def _read_json(path: Path | str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TakeoverManifestError(f"JSON root must be an object: {path}")
    return value


def _require_all_false(authority: object, *, label: str) -> None:
    if not isinstance(authority, Mapping):
        raise TakeoverManifestError(f"{label} authority must be an object")
    missing = FORBIDDEN_TRUE_AUTHORITY - set(authority)
    if missing:
        raise TakeoverManifestError(f"{label} authority missing keys: {sorted(missing)}")
    for key in sorted(FORBIDDEN_TRUE_AUTHORITY):
        if authority.get(key) is not False:
            raise TakeoverManifestError(f"{label} illegally authorizes {key}")


def _validate_historical(value: Mapping) -> None:
    if value.get("schema") != HISTORICAL_SCHEMA:
        raise TakeoverManifestError("wrong historical ledger schema")
    _require_all_false(value.get("authority"), label="historical")
    entries = value.get("entries")
    if not isinstance(entries, list) or not entries:
        raise TakeoverManifestError("historical ledger entries missing")
    seen: set[str] = set()
    for item in entries:
        if not isinstance(item, Mapping):
            raise TakeoverManifestError("historical ledger entry must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id or item_id in seen:
            raise TakeoverManifestError("historical ledger ids must be unique non-empty strings")
        seen.add(item_id)
        identity_class = item.get("identity_class")
        status = item.get("current_status")
        if identity_class == "GENE_IDENTITY_PROVENANCE_UNRESOLVED" and status not in _ALLOWED_UNRESOLVED_STATUSES:
            raise TakeoverManifestError(
                f"unresolved gene-identity evidence promoted without replay boundary: {item_id} -> {status}"
            )

    chain = value.get("current_td_chain")
    if not isinstance(chain, Mapping):
        raise TakeoverManifestError("historical current_td_chain missing")
    expected = {
        "td_repair_pr320_sha": EXPECTED_TD_REPAIR_SHA,
        "synthetic_v2_1_pr321_sha": EXPECTED_SYNTHETIC_SHA,
        "package_sha256": EXPECTED_PACKAGE_SHA256,
        "prefit_archive_sha256": EXPECTED_PREFIT_SHA256,
        "compatibility_certification_receipt_sha256": EXPECTED_CERT_SHA256,
        "preflight_terminal": EXPECTED_PREFLIGHT_TERMINAL,
    }
    for key, wanted in expected.items():
        if chain.get(key) != wanted:
            raise TakeoverManifestError(f"historical TD chain mismatch for {key}")
    if chain.get("biological_test_of_test_executed") is not False:
        raise TakeoverManifestError("historical ledger claims biological test-of-test already executed")
    if chain.get("controller_truth_opened") is not False:
        raise TakeoverManifestError("historical ledger claims controller truth already opened")


def _validate_readiness(value: Mapping) -> None:
    if value.get("schema") != READINESS_SCHEMA:
        raise TakeoverManifestError("wrong readiness audit schema")
    _require_all_false(value.get("authority"), label="readiness")
    dependency = value.get("current_td_dependency")
    if not isinstance(dependency, Mapping):
        raise TakeoverManifestError("readiness current_td_dependency missing")
    expected = {
        "td_repair_sha": EXPECTED_TD_REPAIR_SHA,
        "synthetic_v2_1_sha": EXPECTED_SYNTHETIC_SHA,
        "package_sha256": EXPECTED_PACKAGE_SHA256,
        "prefit_archive_sha256": EXPECTED_PREFIT_SHA256,
        "certification_receipt_sha256": EXPECTED_CERT_SHA256,
    }
    for key, wanted in expected.items():
        if dependency.get(key) != wanted:
            raise TakeoverManifestError(f"readiness TD dependency mismatch for {key}")
    if dependency.get("controller_adjudication_authorized") is not False:
        raise TakeoverManifestError("controller adjudication must remain separately unauthorized")
    if value.get("summary_status") != "RUNTIME_MATURE__POST_TD_ARCHITECTURE_INTEGRATION_INCOMPLETE__TRAINING_OFF":
        raise TakeoverManifestError("unexpected readiness summary_status")


def validate_takeover_manifests(historical_path: Path | str, readiness_path: Path | str) -> dict[str, str]:
    historical = _read_json(historical_path)
    readiness = _read_json(readiness_path)
    _validate_historical(historical)
    _validate_readiness(readiness)
    return {
        "status": "PASS_JEPA_LANE_TAKEOVER_MANIFEST_V1",
        "historical_schema": HISTORICAL_SCHEMA,
        "readiness_schema": READINESS_SCHEMA,
        "td_repair_sha": EXPECTED_TD_REPAIR_SHA,
        "synthetic_v2_1_sha": EXPECTED_SYNTHETIC_SHA,
        "package_sha256": EXPECTED_PACKAGE_SHA256,
        "prefit_archive_sha256": EXPECTED_PREFIT_SHA256,
        "certification_receipt_sha256": EXPECTED_CERT_SHA256,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the JEPA lane historical/readiness takeover manifests")
    parser.add_argument(
        "--historical",
        default="results/target_discovery/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.json",
    )
    parser.add_argument(
        "--readiness",
        default="results/target_discovery/JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.json",
    )
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    result = validate_takeover_manifests(args.historical, args.readiness)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
