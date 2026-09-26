"""Physical, NON-AUTHORIZING critical-test preflight successor research.

This module consumes an OUTSIDE-trusted exact manifest SHA, the manifest bytes,
a real local source checkout and machine-readable JUnit XML bytes. It never
issues CurrentTrainingAuthorityV1, never mutates V1 or V2 closure and never
asserts that a caller-supplied CI URL proves externally authenticated execution.

A trusted caller must obtain the expected manifest digest independently.
A separate future verifier must authenticate CI run identity/artifacts against
the CI provider. Passing this preflight alone is NOT B1/B2 authorization.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Mapping
from xml.etree import ElementTree as ET

SCHEMA = "V5_CRITICAL_TEST_PHYSICAL_PREFLIGHT_RESEARCH_V40"
MANIFEST_SCHEMA = "V5_CRITICAL_TEST_FROZEN_SUITE_MANIFEST_RESEARCH_V40"
_HEX64 = re.compile(r"^[a-f0-9]{64}$")
_HEX40 = re.compile(r"^[a-f0-9]{40}$")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact_sha(value: Any, name: str, *, git: bool = False) -> str:
    pattern = _HEX40 if git else _HEX64
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase {'Git SHA-1' if git else 'SHA-256'}")
    return value


def _object(value: Any, name: str, fields: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} fields must exactly match the frozen schema")
    return value


def _safe_repo_file(repo: Path, posix_path: Any) -> Path:
    if not isinstance(posix_path, str) or not posix_path:
        raise ValueError("suite source path must be nonempty")
    rel = PurePosixPath(posix_path)
    if (rel.is_absolute() or str(rel) != posix_path or
            any(part in (".", "..", "") for part in rel.parts)):
        raise ValueError("suite source path is unsafe/noncanonical")
    if rel.parts[0] == ".git":
        raise ValueError("suite source path points into .git")
    candidate = repo
    for part in rel.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("suite source path traverses a symlink")
    if not candidate.is_file():
        raise ValueError(f"required suite source is missing: {posix_path}")
    if not candidate.resolve().is_relative_to(repo.resolve()):
        raise ValueError("suite source escapes checkout")
    return candidate


def _manifest(manifest_bytes: bytes, *, trusted_sha256: str) -> Mapping[str, Any]:
    if _sha(manifest_bytes) != _exact_sha(trusted_sha256, "external trusted manifest SHA"):
        raise ValueError("frozen manifest does not match independently supplied digest")
    try:
        parsed = json.loads(manifest_bytes)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("manifest is invalid JSON") from exc
    man = _object(parsed, "manifest", {
        "schema", "source_commit", "required_test_ids",
        "suite_files", "runner_source", "training_authorized",
    })
    if man["schema"] != MANIFEST_SCHEMA or man["training_authorized"] is not False:
        raise ValueError("manifest schema or training boundary mismatch")
    _exact_sha(man["source_commit"], "frozen source commit", git=True)
    ids = man["required_test_ids"]
    if (not isinstance(ids, list) or not ids or
            any(not isinstance(i, str) or not re.fullmatch(r"[A-Za-z0-9_.]+::test_[A-Za-z0-9_\[\]-]+", i)
                for i in ids) or len(set(ids)) != len(ids)):
        raise ValueError("frozen test identifiers must be unique qualified IDs")
    files = man["suite_files"]
    if not isinstance(files, list) or not files:
        raise ValueError("frozen suite source list is empty")
    normalized_files = []
    for rec in [*files, man["runner_source"]]:
        rec = _object(rec, "source file", {"path", "sha256"})
        normalized_files.append(rec["path"])
        _exact_sha(rec["sha256"], "frozen source file digest")
    if len(set(normalized_files)) != len(normalized_files):
        raise ValueError("duplicate suite or runner path in frozen manifest")
    return man


def _junit_cases(xml_bytes: bytes) -> list[str]:
    # ElementTree does not resolve external DTD entities. Reject all XML
    # DOCTYPE/entity constructs anyway to enforce a small, auditable format.
    if b"<!DOCTYPE" in xml_bytes.upper() or b"<!ENTITY" in xml_bytes.upper():
        raise ValueError("JUnit XML DTD/entities are not accepted")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError("JUnit is not parseable XML") from exc
    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        suites = list(root)
        if not suites or any(x.tag != "testsuite" for x in suites):
            raise ValueError("JUnit testsuites contains non-testsuite entries")
    else:
        raise ValueError("JUnit root must be testsuite(s)")
    observed: list[str] = []
    for suite in suites:
        cases = list(suite.findall("testcase"))
        if any(elem.tag not in {"testcase", "properties", "system-out", "system-err"}
               for elem in suite):
            raise ValueError("JUnit suite contains unrecognized nodes")
        if not cases:
            raise ValueError("JUnit suite is empty")
        expected_counts = {
            "tests": len(cases),
            "errors": 0,
            "failures": 0,
            "skipped": 0,
        }
        for name, expected in expected_counts.items():
            raw = suite.attrib.get(name)
            if raw is None or not raw.isdecimal() or int(raw) != expected:
                raise ValueError(f"JUnit suite {name} count mismatch")
        for case in cases:
            if list(case) or not case.attrib.get("classname") or not case.attrib.get("name"):
                raise ValueError("JUnit testcase has failure/skip/nested content or missing identity")
            if (case.attrib["name"].startswith("test_") is False or
                    not re.fullmatch(r"[A-Za-z0-9_.]+", case.attrib["classname"])):
                raise ValueError("JUnit testcase identity is not canonical")
            observed.append(f"{case.attrib['classname'].split('.')[-1]}::{case.attrib['name']}")
    if len(observed) != len(set(observed)):
        raise ValueError("duplicate JUnit test IDs are forbidden")
    if root.tag == "testsuites":
        # Some CI producers omit aggregate attributes. If present, all must
        # match the sum across suites, not a self-consistent but empty header.
        for key, expected in {
            "tests": len(observed), "errors": 0, "failures": 0, "skipped": 0
        }.items():
            raw = root.attrib.get(key)
            if raw is not None and (not raw.isdecimal() or int(raw) != expected):
                raise ValueError(f"JUnit aggregate {key} count mismatch")
    return observed


def verify_critical_test_physical_preflight_v40(
    *, manifest_bytes: bytes, externally_trusted_manifest_sha256: str,
    repo_root: str | Path, junit_bytes: bytes,
) -> dict[str, Any]:
    """Verify physical source/JUnit parity against externally pinned manifest.

    A caller-supplied manifest SHA is NOT an independent trust anchor merely
    because its argument contains the word 'trusted'. Actual reviewer custody
    of that digest and CI-origin verification are OUTSIDE this function.
    """
    manifest = _manifest(
        manifest_bytes, trusted_sha256=externally_trusted_manifest_sha256
    )
    repo = Path(repo_root).resolve(strict=True)
    if not repo.is_dir():
        raise ValueError("checkout root must be a directory")
    try:
        head = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("physical source checkout has no verifiable Git HEAD") from exc
    if head != manifest["source_commit"]:
        raise ValueError("checkout HEAD does not match frozen source commit")
    source_hashes: dict[str, str] = {}
    for rec in [*manifest["suite_files"], manifest["runner_source"]]:
        path = _safe_repo_file(repo, rec["path"])
        observed = _sha(path.read_bytes())
        if observed != rec["sha256"]:
            raise ValueError(f"original suite source byte mismatch: {rec['path']}")
        source_hashes[rec["path"]] = observed
    actual = _junit_cases(junit_bytes)
    expected = set(manifest["required_test_ids"])
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError(
            "JUnit exact test identities mismatch: "
            f"missing={sorted(expected-set(actual))} extra={sorted(set(actual)-expected)}"
        )
    return {
        "schema": SCHEMA,
        "manifest_sha256": externally_trusted_manifest_sha256,
        "source_commit": head,
        "source_sha256_by_path": source_hashes,
        "junit_sha256": _sha(junit_bytes),
        "executed_unique_test_count": len(actual),
        "skips_errors_failures": 0,
        "locally_verified": True,
        "external_ci_origin_authenticated": False,
        "full_v5_graph_qualified": False,
        "training_authorized": False,
    }
