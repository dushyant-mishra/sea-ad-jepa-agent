from __future__ import annotations

import hashlib
import importlib
import json
import platform
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Mapping, Sequence

from .artifact_binding_v1 import seal_artifact, validate_artifact


class EnvironmentPreflightStop(RuntimeError):
    pass


ENVIRONMENT_PREFLIGHT_ARTIFACT_SCHEMA = "JEPA_V5_ENVIRONMENT_PREFLIGHT_ARTIFACT_V1"
RECEIPT_SCHEMA = "JEPA_V5_ENVIRONMENT_PREFLIGHT_RECEIPT_V1"
PASS_TERMINAL = "PASS_V5_ENVIRONMENT_PREFLIGHT_V1"


def _run_git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise EnvironmentPreflightStop(
            f"STOP_V5_ENVIRONMENT_PREFLIGHT_GIT:{' '.join(args)}:{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _is_sha(value: object, length: int) -> bool:
    if not isinstance(value, str) or len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _parse_junit(junit_path: Path) -> tuple[dict[str, int], dict[str, str]]:
    try:
        root = ET.parse(junit_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_JUNIT_UNREADABLE") from exc

    cases = list(root.iter("testcase"))
    statuses: dict[str, str] = {}
    failures = errors = skipped = 0
    for case in cases:
        name = case.attrib.get("name", "")
        if not name:
            raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_JUNIT_TEST_ID_MISSING")
        if case.find("failure") is not None:
            status = "failure"
            failures += 1
        elif case.find("error") is not None:
            status = "error"
            errors += 1
        elif case.find("skipped") is not None:
            status = "skipped"
            skipped += 1
        else:
            status = "passed"
        if name in statuses and statuses[name] != status:
            raise EnvironmentPreflightStop(f"STOP_V5_ENVIRONMENT_PREFLIGHT_DUPLICATE_TEST_ID:{name}")
        statuses[name] = status

    total = len(cases)
    passed = total - failures - errors - skipped
    return {
        "tests_collected": total,
        "tests_passed": passed,
        "tests_failures": failures,
        "tests_errors": errors,
        "tests_skipped": skipped,
    }, statuses


def _parse_critical_manifest(path: Path) -> list[str]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_CRITICAL_MANIFEST_UNREADABLE") from exc
    ids = obj.get("expected_test_ids") if isinstance(obj, Mapping) else None
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or not x for x in ids):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_CRITICAL_MANIFEST_INVALID")
    if len(ids) != len(set(ids)):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_CRITICAL_MANIFEST_DUPLICATE")
    return ids


def _authority_byte_state(root: Path, authority_paths: Sequence[str]) -> tuple[bool, bool, str]:
    if not authority_paths:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_AUTHORITY_PATHS_EMPTY")
    normalized: list[str] = []
    blob_map: dict[str, str] = {}
    for raw in authority_paths:
        if not isinstance(raw, str) or not raw:
            raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_AUTHORITY_PATH_INVALID")
        rel = Path(raw).as_posix()
        path = root / rel
        if not path.is_file():
            raise EnvironmentPreflightStop(f"STOP_V5_ENVIRONMENT_PREFLIGHT_AUTHORITY_FILE_MISSING:{rel}")
        head_blob = _run_git(root, "rev-parse", f"HEAD:{rel}")
        current_blob = _run_git(root, "hash-object", "--no-filters", rel)
        normalized.append(rel)
        blob_map[rel] = head_blob
        if current_blob != head_blob:
            bytes_match = False
            break
    else:
        bytes_match = True

    status = _run_git(root, "status", "--porcelain", "--", *normalized)
    clean = status == ""
    bundle = hashlib.sha256(
        (json.dumps(blob_map, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    return clean, bytes_match, bundle


def collect_environment_preflight_v1(
    *,
    root: Path | str,
    expected_head: str,
    junit_path: Path | str,
    critical_manifest_path: Path | str,
    authority_paths: Sequence[str],
    cuda_required: bool,
    environment_name: str = "sea-ad-jepa-v3",
) -> dict[str, object]:
    repo_root = Path(root).resolve()
    if not _is_sha(expected_head, 40):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_EXPECTED_HEAD_INVALID")

    test_counts, statuses = _parse_junit(Path(junit_path))
    critical_ids = _parse_critical_manifest(Path(critical_manifest_path))
    critical_missing = sum(1 for x in critical_ids if x not in statuses)
    critical_skipped = sum(1 for x in critical_ids if statuses.get(x) == "skipped")
    critical_executed_passed = sum(1 for x in critical_ids if statuses.get(x) == "passed")

    try:
        importlib.import_module("sea_ad_jepa.v5")
        import_ok = True
    except Exception:
        import_ok = False

    try:
        import torch  # type: ignore

        torch_version: str | None = str(torch.__version__)
        cuda_available = bool(torch.cuda.is_available())
        cuda_device_name = str(torch.cuda.get_device_name(0)) if cuda_available else None
    except Exception:
        torch_version = None
        cuda_available = False
        cuda_device_name = None

    head = _run_git(repo_root, "rev-parse", "HEAD")
    head_matches = head == expected_head.lower()
    clean, bytes_match, source_bundle_sha = _authority_byte_state(repo_root, authority_paths)
    autocrlf = _run_git(repo_root, "config", "--get", "core.autocrlf", check=False) or "<unset>"
    gitattributes_present = (repo_root / ".gitattributes").is_file()

    receipt: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "environment_name": environment_name,
        "python_version": platform.python_version(),
        "torch_version": torch_version,
        "cuda_required": bool(cuda_required),
        "cuda_available": cuda_available,
        "cuda_device_name": cuda_device_name,
        "sea_ad_jepa_v5_import_ok": import_ok,
        **test_counts,
        "critical_expected": len(critical_ids),
        "critical_executed_passed": critical_executed_passed,
        "critical_skipped": critical_skipped,
        "critical_missing": critical_missing,
        "git_head": head,
        "expected_git_head": expected_head.lower(),
        "git_head_matches_expected": head_matches,
        "authority_files": [Path(x).as_posix() for x in authority_paths],
        "authority_files_clean": clean,
        "authority_bytes_match_head": bytes_match,
        "authority_source_bundle_sha256": source_bundle_sha,
        "core_autocrlf": autocrlf,
        "gitattributes_present": gitattributes_present,
        "terminal": PASS_TERMINAL,
    }
    _validate_payload(receipt)
    return receipt


def _validate_payload(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_SCHEMA")
    if not isinstance(receipt.get("environment_name"), str) or not receipt.get("environment_name"):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_ENVIRONMENT_NAME")
    if not isinstance(receipt.get("python_version"), str) or not receipt.get("python_version"):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_PYTHON")
    if not isinstance(receipt.get("torch_version"), str) or not receipt.get("torch_version"):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_TORCH")
    if receipt.get("sea_ad_jepa_v5_import_ok") is not True:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_IMPORT")

    for field in (
        "tests_collected",
        "tests_passed",
        "tests_failures",
        "tests_errors",
        "tests_skipped",
        "critical_expected",
        "critical_executed_passed",
        "critical_skipped",
        "critical_missing",
    ):
        value = receipt.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EnvironmentPreflightStop(f"STOP_V5_ENVIRONMENT_PREFLIGHT_BAD_COUNT:{field}")
    if receipt.get("tests_collected") <= 0:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_NO_TESTS_COLLECTED")
    if receipt.get("tests_failures") != 0:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_TEST_FAILURES")
    if receipt.get("tests_errors") != 0:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_TEST_ERRORS")
    if receipt.get("tests_skipped") != 0:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_TEST_SKIPS")
    if receipt.get("critical_expected") <= 0:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_CRITICAL_TEST_SET_EMPTY")
    if (
        receipt.get("critical_skipped") != 0
        or receipt.get("critical_missing") != 0
        or receipt.get("critical_executed_passed") != receipt.get("critical_expected")
    ):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_CRITICAL_TEST_INCOMPLETE")
    if receipt.get("tests_passed") != receipt.get("tests_collected"):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_TEST_ACCOUNTING")

    if not _is_sha(receipt.get("git_head"), 40) or not _is_sha(receipt.get("expected_git_head"), 40):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_HEAD_INVALID")
    if receipt.get("git_head") != receipt.get("expected_git_head") or receipt.get("git_head_matches_expected") is not True:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_HEAD_MISMATCH")
    files = receipt.get("authority_files")
    if not isinstance(files, list) or not files or any(not isinstance(x, str) or not x for x in files):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_AUTHORITY_FILE_SET")
    if receipt.get("authority_files_clean") is not True:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_DIRTY_AUTHORITY_FILES")
    if receipt.get("authority_bytes_match_head") is not True:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_EOL_OR_BYTE_MISMATCH")
    if not _is_sha(receipt.get("authority_source_bundle_sha256"), 64):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_SOURCE_BUNDLE_SHA")
    if receipt.get("gitattributes_present") is not True:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_GITATTRIBUTES_MISSING")
    if not isinstance(receipt.get("core_autocrlf"), str):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_AUTOCRLF_UNRECORDED")

    cuda_required = receipt.get("cuda_required")
    if not isinstance(cuda_required, bool) or not isinstance(receipt.get("cuda_available"), bool):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_CUDA_STATE")
    if cuda_required and (
        receipt.get("cuda_available") is not True
        or not isinstance(receipt.get("cuda_device_name"), str)
        or not receipt.get("cuda_device_name")
    ):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_CUDA_REQUIRED")
    if receipt.get("terminal") != PASS_TERMINAL:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_TERMINAL")

    out = dict(receipt)
    out["d_shared_real_outcome_access_authorized"] = False
    out["training_authorized"] = False
    return out


def _parents(payload: Mapping[str, object]) -> dict[str, str]:
    return {
        "git_head": str(payload["git_head"]),
        "authority_source_bundle_sha256": str(payload["authority_source_bundle_sha256"]),
    }


def seal_environment_preflight_receipt_v1(receipt: Mapping[str, object]) -> dict[str, object]:
    payload = _validate_payload(receipt)
    return seal_artifact(ENVIRONMENT_PREFLIGHT_ARTIFACT_SCHEMA, payload, _parents(payload))


def validate_environment_preflight_v1(envelope: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(envelope, Mapping):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_ENVELOPE_NOT_MAPPING")
    raw_payload = envelope.get("payload")
    if not isinstance(raw_payload, Mapping):
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_PAYLOAD_NOT_MAPPING")
    try:
        payload = validate_artifact(
            envelope,
            expected_schema=ENVIRONMENT_PREFLIGHT_ARTIFACT_SCHEMA,
            expected_parents=_parents(raw_payload),
        )
    except (ValueError, RuntimeError, KeyError) as exc:
        raise EnvironmentPreflightStop("STOP_V5_ENVIRONMENT_PREFLIGHT_ARTIFACT_INVALID") from exc
    return _validate_payload(payload)
