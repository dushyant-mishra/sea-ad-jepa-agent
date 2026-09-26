"""Adversarial synthetic tests for V40 physical preflight, NEVER B2 positives."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
from xml.etree import ElementTree as ET

import pytest

from sea_ad_jepa.v5.critical_test_physical_preflight_research_v40 import (
    MANIFEST_SCHEMA,
    verify_critical_test_physical_preflight_v40 as verify,
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True,
        stderr=subprocess.PIPE,
    ).strip()


def junit(*, ids=("test_source::test_a", "test_source::test_b"),
          status=None, declared_tests=None, duplicates=False):
    root = ET.Element("testsuite", {
        "tests": str(len(ids) if declared_tests is None else declared_tests),
        "errors": "0", "failures": "0", "skipped": "0",
    })
    for identifier in ids:
        cls, name = identifier.split("::")
        case = ET.SubElement(root, "testcase", {"classname": cls, "name": name})
        if status:
            ET.SubElement(case, status)
    if duplicates:
        ET.SubElement(root, "testcase", {
            "classname": "test_source", "name": "test_a",
        })
        root.set("tests", str(len(ids) + 1))
    return ET.tostring(root, encoding="utf-8")


@pytest.fixture
def physical_fixture(tmp_path):
    checkout = tmp_path / "repo"
    checkout.mkdir()
    git(checkout, "init", "-q")
    git(checkout, "config", "user.name", "Synthetic Tester")
    git(checkout, "config", "user.email", "tests@invalid.example")
    src = checkout / "tests" / "test_source.py"
    src.parent.mkdir()
    src.write_text("def test_a(): assert True\ndef test_b(): assert True\n")
    runner = checkout / "scripts" / "runner.py"
    runner.parent.mkdir()
    runner.write_text("print('synthetic runner, not a physical CI run')\n")
    git(checkout, "add", ".")
    git(checkout, "commit", "-qm", "fixture")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "source_commit": git(checkout, "rev-parse", "HEAD"),
        "required_test_ids": ["test_source::test_a", "test_source::test_b"],
        "suite_files": [{"path": "tests/test_source.py", "sha256": sha(src.read_bytes())}],
        "runner_source": {"path": "scripts/runner.py", "sha256": sha(runner.read_bytes())},
        "training_authorized": False,
    }
    return checkout, manifest, junit()


def check(checkout, manifest, xml, *, external=None):
    blob = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return verify(
        manifest_bytes=blob,
        externally_trusted_manifest_sha256=external or sha(blob),
        repo_root=checkout,
        junit_bytes=xml,
    )


def test_exact_frozen_manifest_real_checkout_and_machine_junit_local_only(physical_fixture):
    repo, manifest, xml = physical_fixture
    report = check(repo, manifest, xml)
    assert report["executed_unique_test_count"] == 2
    assert report["locally_verified"] is True
    assert report["external_ci_origin_authenticated"] is False
    assert report["training_authorized"] is False
    print("V40_PHYSICAL_LOCAL_PARITY_PASS_EXTERNAL_CI_AUTHORITY_FALSE")


def test_original_suite_byte_tamper_fails(physical_fixture):
    repo, manifest, xml = physical_fixture
    (repo / "tests/test_source.py").write_text("def test_a(): assert False\n")
    with pytest.raises(ValueError, match="original suite source byte mismatch"):
        check(repo, manifest, xml)


def test_original_runner_byte_tamper_fails(physical_fixture):
    repo, manifest, xml = physical_fixture
    (repo / "scripts/runner.py").write_text("print('changed')\n")
    with pytest.raises(ValueError, match="original suite source byte mismatch"):
        check(repo, manifest, xml)


def test_forged_self_consistent_manifest_rejected_by_external_anchor(physical_fixture):
    repo, manifest, xml = physical_fixture
    original = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    changed = copy.deepcopy(manifest)
    changed["required_test_ids"] = ["test_source::test_a"]
    with pytest.raises(ValueError, match="does not match independently supplied digest"):
        check(repo, changed, xml, external=sha(original))


def test_replaced_checkout_head_fails_even_same_file_bytes(physical_fixture):
    repo, manifest, xml = physical_fixture
    git(repo, "commit", "--allow-empty", "-qm", "unreviewed new commit")
    with pytest.raises(ValueError, match="HEAD does not match"):
        check(repo, manifest, xml)


def test_junit_missing_required_test_fails(physical_fixture):
    repo, manifest, _ = physical_fixture
    with pytest.raises(ValueError, match="exact test identities mismatch"):
        check(repo, manifest, junit(ids=("test_source::test_a",)))


def test_junit_surplus_test_fails(physical_fixture):
    repo, manifest, _ = physical_fixture
    with pytest.raises(ValueError, match="exact test identities mismatch"):
        check(repo, manifest, junit(ids=(
            "test_source::test_a", "test_source::test_b", "test_source::test_extra"
        )))


def test_junit_duplicate_test_fails_even_when_count_matches(physical_fixture):
    repo, manifest, _ = physical_fixture
    with pytest.raises(ValueError, match="duplicate JUnit test IDs"):
        check(repo, manifest, junit(duplicates=True))


@pytest.mark.parametrize("status", ["skipped", "failure", "error"])
def test_junit_hidden_nonpass_fails_even_with_zero_summary(physical_fixture, status):
    repo, manifest, _ = physical_fixture
    with pytest.raises(ValueError, match="failure/skip/nested"):
        check(repo, manifest, junit(status=status))


def test_junit_fake_summary_count_fails(physical_fixture):
    repo, manifest, _ = physical_fixture
    with pytest.raises(ValueError, match="tests count mismatch"):
        check(repo, manifest, junit(declared_tests=999))


def test_symlinked_suite_source_fails_even_same_bytes(physical_fixture):
    repo, manifest, xml = physical_fixture
    source = repo / "tests/test_source.py"
    other = repo / "tests" / "other.py"
    other.write_bytes(source.read_bytes())
    source.unlink()
    try:
        source.symlink_to(other)
    except OSError:
        pytest.skip("filesystem does not support symlink creation")
    with pytest.raises(ValueError, match="traverses a symlink"):
        check(repo, manifest, xml)


def test_path_escape_manifest_rejected_before_source_read(physical_fixture):
    repo, manifest, xml = physical_fixture
    manifest["suite_files"][0]["path"] = "../outside.py"
    with pytest.raises(ValueError, match="unsafe/noncanonical"):
        check(repo, manifest, xml)


def test_duplicate_frozen_required_ids_fail(physical_fixture):
    repo, manifest, xml = physical_fixture
    manifest["required_test_ids"] = ["test_source::test_a", "test_source::test_a"]
    with pytest.raises(ValueError, match="unique qualified IDs"):
        check(repo, manifest, xml)


def test_manifest_cannot_claim_training_true(physical_fixture):
    repo, manifest, xml = physical_fixture
    manifest["training_authorized"] = True
    with pytest.raises(ValueError, match="training boundary"):
        check(repo, manifest, xml)


def test_junit_doctype_rejected(physical_fixture):
    repo, manifest, xml = physical_fixture
    with pytest.raises(ValueError, match="DTD/entities"):
        check(repo, manifest, b"<!DOCTYPE foo [<!ENTITY x 'bad'>]>" + xml)
