"""The T0 V20 decision evidence is in the branch, byte-for-byte.

The external reviewer's remaining limitation before calling T0 independently
closed: the result commit recorded hashes and statistics, but the decision and
sensitivity files themselves were not committed, so nobody could verify them.

These tests are the standing proof, and they are written so a reviewer can run
them on their own clone rather than take this run's word for it. They check that
every evidence file is tracked, that its committed blob bytes equal its bytes on
disk, and that the digests recorded in the manifest are the digests of those
bytes.

Why the blob-versus-disk check is the one that matters. Every digest published
for these artifacts is over raw bytes. If the files were committed as tracked
text, a Windows checkout would rewrite LF to CRLF and every recorded SHA-256
would break while the files still looked present. That failure already happened
in this lane once: a committed availability package produced `a4424482…` on a
fresh checkout instead of `e49c4e93…`. The `-text` rules in `.gitattributes`
prevent it, and these tests are what confirm the prevention works rather than
assuming it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "agent" / "T0_V20_EVIDENCE_BYTE_MANIFEST.json"

EVIDENCE_DIRS = (
    "outputs/t0_b2_production_20260909",
    "outputs/t0_technical_completeness_20260909",
    "outputs/t0_eligible_donor_20260909",
    "outputs/t0_estimability_preflight_20260909",
    "outputs/t0_execution_input_readiness_20260909",
    "outputs/t0_stage2a_pre_at8_20260909",
    "outputs/t0_donor_role_20260909",
    "outputs/t0_discovery_stage_20260909",
    "outputs/t0_stage3_prep_20260909",
    "outputs/t0_target_family_20260909",
    "outputs/t0_technical_registry_20260909",
    "outputs/t0_r8_readiness_verify_20260909",
    "outputs/t0_stage3_confirmation_20260909",
)

# The roots the decision rests on, as published in the result commit. Named here
# so the test fails if a future edit moves any of them.
PUBLISHED = {
    "outputs/t0_stage3_confirmation_20260909/T0_V20_ADJUDICATION_DECISION.json":
        "a36081705ed17f3f4656f742ea1e65d8e955a05eaf13cb7a607af01938a36a03",
    "outputs/t0_stage3_confirmation_20260909/T0_STAGE3_CONFIRMATION_RUN_SUMMARY.json":
        "9aa4abbf0e213464d207533e2412d74177b3cc1712a77e6a0aad71bbce1b9ed4",
    "outputs/t0_stage3_confirmation_20260909/T0_CONFIRMATION_NUMERIC_AT8_ACCESS_MANIFEST.json":
        "af884f3de7e37d8eba89139cc2ffdd48a664faf92d6b0738cf6ebac9807012ac",
    "outputs/t0_stage3_confirmation_20260909/tail/T0_TAIL_MANIFEST.csv":
        "c84a76b02d2a29cfc070b04161800d2b7c9b503321b9258bc5c256b55a1597bc",
    "outputs/t0_stage3_confirmation_20260909/pretarget_execution_input/T0_PRETARGET_EXECUTION_INPUT_MANIFEST.csv":
        "3b0b16a364ff1430e28d496ea5586ff1aaf1b2fce58bbe5367c26678b6c6e618",
    "outputs/t0_stage3_confirmation_20260909/preadjudication_execution_input/T0_PREADJUDICATION_EXECUTION_INPUT_MANIFEST.csv":
        "ba87764fa7419eda1119744f206242d0440dc8f41772e3259b87f75f61611f8c",
    "outputs/t0_discovery_stage_20260909/target/T0_TARGET_MANIFEST.csv":
        "b29429021b551f3b26dadbc5ee20f57cec4e84cccc483943b73602f5bcfad8fe",
    "outputs/t0_discovery_stage_20260909/discovery_authority/T0_DISCOVERY_AUTHORITY_MANIFEST.csv":
        "9806de382c75f7a7a12bb952631ed0b6c9b458250e8161a876b470c48898f6f7",
    "outputs/t0_donor_role_20260909/T0_DONOR_ROLE_MANIFEST.csv":
        "db8680e6cef3e0d26ee117a2acbd10ba1f681a53401008128a9bb7a2e6c478e0",
}


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", *EVIDENCE_DIRS], cwd=str(ROOT),
                         capture_output=True, text=True, check=True)
    return out.stdout.split()


def _blob(path: str) -> bytes:
    return subprocess.run(["git", "cat-file", "blob", "HEAD:" + path],
                          cwd=str(ROOT), capture_output=True,
                          check=True).stdout


git_available = True
try:
    subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                   capture_output=True, check=True)
except Exception:  # pragma: no cover
    git_available = False

pytestmark = pytest.mark.skipif(not git_available,
                                reason="not a git checkout")


def test_the_evidence_is_tracked_at_all() -> None:
    """`outputs/` is gitignored, so these had to be force-added."""
    tracked = _tracked()
    assert len(tracked) == 84, len(tracked)
    for directory in EVIDENCE_DIRS:
        assert any(p.startswith(directory) for p in tracked), directory


def test_no_matrix_cache_was_committed() -> None:
    """118 MB of reproducible cache stays out; it is bound by digest instead."""
    assert not [p for p in _tracked() if p.endswith(".npz")]


def test_every_committed_blob_equals_the_bytes_on_disk() -> None:
    """The check that would catch a line-ending rewrite."""
    mismatched = []
    for path in _tracked():
        blob = _blob(path)
        disk = (ROOT / path).read_bytes()
        if blob != disk:
            mismatched.append(path)
    assert not mismatched, mismatched


def test_the_published_decision_digests_are_the_committed_bytes() -> None:
    """The roots quoted in the result commit, verified against the branch."""
    for path, expected in PUBLISHED.items():
        blob = _blob(path)
        assert hashlib.sha256(blob).hexdigest() == expected, path


@pytest.mark.skipif(not MANIFEST.is_file(), reason="byte manifest absent")
def test_the_byte_manifest_matches_the_branch() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["all_blob_bytes_equal_disk_bytes"] is True
    assert manifest["files"] == len(_tracked())
    recorded = {e["path"]: e["sha256"] for e in manifest["entries"]}
    for path in _tracked():
        assert path in recorded, path
        assert hashlib.sha256(_blob(path)).hexdigest() == recorded[path], path


def test_the_text_rules_cover_every_evidence_directory() -> None:
    """Without these the digests break on a Windows checkout."""
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for directory in EVIDENCE_DIRS:
        assert "%s/** -text" % directory in attributes, directory
