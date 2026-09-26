"""V40 independent local source/JUnit parity preflight for critical tests.

NON-AUTHORIZING. This deliberately does NOT issue CriticalTestExecutionAuthorityV1,
validate GitHub Actions' identity, or authorize B1/B2. An independent custodian
MUST provide authenticated external SHA/commit/test-identity expectations. A
caller who invents the manifest AND its expected SHA proves nothing.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree as ET

KIND = "V5_CRITICAL_TEST_PHYSICAL_PREFLIGHT_V1"
HEX = re.compile(r"^[0-9a-f]{64}$")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError(f"{field}: expected exact lowercase SHA256")
    return value


def _resolve_regular(root: Path, rel: Any) -> Path:
    if not isinstance(rel, str) or not rel or "\\" in rel:
        raise ValueError("source path must be relative POSIX path")
    parts = rel.split("/")
    if any(p in ("", ".", "..") for p in parts) or ":" in parts[0] or rel.startswith("/"):
        raise ValueError("source path is unsafe")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"source symlink forbidden: {rel}")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"source missing or outside repo: {rel}")
    return path


def _parse_junit(raw: bytes) -> tuple[str, ...]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("invalid JUnit XML") from exc
    suites = [root] if root.tag == "testsuite" else list(root) if root.tag == "testsuites" else []
    if not suites or any(x.tag != "testsuite" for x in suites):
        raise ValueError("JUnit must contain testsuite elements")
    cases: list[str] = []
    for suite in suites:
        # Require explicit counters and independently reconcile each suite.
        counts = {}
        for key in ("tests", "errors", "failures", "skipped"):
            val = suite.get(key)
            if val is None or not val.isdecimal():
                raise ValueError(f"JUnit suite missing/noninteger {key}")
            counts[key] = int(val)
        nodes = list(suite.iter("testcase"))
        if counts != {"tests": len(nodes), "errors": 0, "failures": 0, "skipped": 0}:
            raise ValueError(f"JUnit nonzero failure/skip or incorrect counters: {counts}")
        for node in nodes:
            if any(x.tag in ("failure", "error", "skipped") for x in node.iter()):
                raise ValueError("JUnit testcase contains failure/error/skip")
            cls, name = node.get("classname"), node.get("name")
            if not cls or not name or not cls.strip() or not name.strip():
                raise ValueError("JUnit testcase has missing identity")
            cases.append(f"{cls.split('.')[-1]}::{name}")
    if not cases or len(set(cases)) != len(cases):
        raise ValueError("JUnit empty or duplicate testcase identity")
    return tuple(sorted(cases))


def check_critical_test_physical_evidence(
    *,
    repo_root: Path,
    manifest_path: Path,
    junit_path: Path,
    trusted_manifest_sha256: str,
    trusted_junit_sha256: str,
    trusted_commit_sha: str,
    trusted_test_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Validate real on-disk bytes against *externally supplied* expectations."""
    root = Path(repo_root).resolve(strict=True)
    manifest_file = Path(manifest_path)
    junit_file = Path(junit_path)
    expected_manifest = _require_sha(trusted_manifest_sha256, "trusted manifest")
    expected_junit = _require_sha(trusted_junit_sha256, "trusted JUnit")
    expected_commit = _require_sha(trusted_commit_sha, "trusted commit")
    if manifest_file.is_symlink() or junit_file.is_symlink():
        raise ValueError("manifest/JUnit symlink forbidden")
    manifest_bytes = manifest_file.read_bytes()
    junit_bytes = junit_file.read_bytes()
    if _sha(manifest_bytes) != expected_manifest:
        raise ValueError("trusted manifest SHA mismatch")
    if _sha(junit_bytes) != expected_junit:
        raise ValueError("trusted JUnit SHA mismatch")
    try:
        manifest = json.loads(manifest_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("malformed manifest JSON") from exc
    required = {
        "schema", "checkout_commit_sha256", "source_files_sha256",
        "required_test_ids", "junit_sha256", "training_authorized",
        "status",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError("manifest schema fields mismatch")
    if manifest["schema"] != KIND or manifest["status"] != "PREFLIGHT_ONLY":
        raise ValueError("manifest must be preflight-only V1")
    if manifest["training_authorized"] is not False:
        raise ValueError("manifest cannot authorize training")
    if _require_sha(manifest["checkout_commit_sha256"], "manifest commit") != expected_commit:
        raise ValueError("trusted commit mismatch")
    if _require_sha(manifest["junit_sha256"], "manifest JUnit") != expected_junit:
        raise ValueError("manifest JUnit root mismatch")
    actual_head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"], text=True
    ).strip()
    if actual_head != expected_commit:
        raise ValueError("physical checkout commit mismatch")
    expected_ids = tuple(sorted(trusted_test_ids))
    if (not expected_ids or len(set(expected_ids)) != len(expected_ids) or
        any(not isinstance(x, str) or "::" not in x for x in expected_ids)):
        raise ValueError("trusted exact test-ID set invalid")
    ids = manifest["required_test_ids"]
    if (not isinstance(ids, list) or len(ids) != len(expected_ids) or
        len(set(ids)) != len(ids) or tuple(sorted(ids)) != expected_ids):
        raise ValueError("manifest differs from independently trusted required test IDs")
    source_map = manifest["source_files_sha256"]
    if not isinstance(source_map, dict) or not source_map:
        raise ValueError("source map must be nonempty")
    observed = {}
    for rel, supplied_sha in source_map.items():
        actual_sha = _sha(_resolve_regular(root, rel).read_bytes())
        if actual_sha != _require_sha(supplied_sha, f"source {rel}"):
            raise ValueError(f"physical source SHA mismatch: {rel}")
        observed[rel] = actual_sha
    executed_ids = _parse_junit(junit_bytes)
    if executed_ids != expected_ids:
        raise ValueError("actual JUnit identities differ from trusted required test IDs")
    return {
        "schema": KIND,
        "status": "LOCAL_SOURCE_JUNIT_PARITY_ONLY__NOT_EXTERNAL_CI_ATTESTATION",
        "checkout_commit_sha256": actual_head,
        "manifest_sha256": _sha(manifest_bytes),
        "junit_sha256": _sha(junit_bytes),
        "actual_test_ids": list(executed_ids),
        "physical_source_sha256": dict(sorted(observed.items())),
        "passed_test_count": len(executed_ids),
        "external_runner_identity_authenticated": False,
        "independent_source_custody_authenticated": False,
        "training_authorized": False,
    }
