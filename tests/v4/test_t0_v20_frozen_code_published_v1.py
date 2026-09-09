"""The code that computed T0 V20 is in the branch, byte-for-byte.

The evidence bytes were already committed and verified. The *computation* was
not. Every frozen V20 module -- the adjudicator that produced the decision
included -- was resolved at runtime through a hardcoded absolute path into a
session scratchpad under the system temp tree:

    .../Temp/claude/d--Jepa-project/<session-id>/scratchpad/v20_recovery/current/code

So a clean clone could verify the numbers but could not run the code that made
them, an external reviewer could not read the adjudicator, and a routine temp
cleanup would have left a fully evidenced result with no recoverable
computation behind it.

These tests are the standing proof that the published copy is that code and
stays that code. They check the digests against the recovery package's own
manifest, which was written before this publication, so the check is against an
independent record rather than against a digest computed from the same copy it
is validating.

The blob-versus-disk check is the one that matters, for the same reason it
matters for the evidence bytes: every digest here is over raw bytes, and a
tracked-as-text checkout on Windows would rewrite LF to CRLF and break all of
them while the files still looked present.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "docs" / "agent" / "T0_V20_FROZEN_CODE_PUBLICATION.json"

PUBLISHED_DIRS = (
    "scripts/v4/t0_v20_frozen",
    "configs/v4/t0_v20_frozen_contract",
    "configs/v4/t0_v20_frozen_authority",
    "docs/agent/t0_v20_frozen_package",
)

# The adjudicator that produced the decision, and the constants the whole
# design is frozen against. Named so a future move fails loudly.
MUST_BE_PRESENT = (
    "scripts/v4/t0_v20_frozen/t0_adjudicator_v2.py",
    "scripts/v4/t0_v20_frozen/t0_adjudicator_v1.py",
    "configs/v4/t0_v20_frozen_contract/T0_V18_FROZEN_CONSTANTS.json",
    "configs/v4/t0_v20_frozen_contract/T0_V20_EXECUTION_AUTHORITY_CONSTANTS.json",
    # The inputs the code runs against. Publishing the modules without these
    # would leave the run still unreproducible from a clean clone.
    "configs/v4/t0_v20_frozen_authority/T0_MTG_FEATURE_ROLE_SPLIT_V2.csv",
    "configs/v4/t0_v20_frozen_authority/"
    "T0_PRIMARY_MTG_READER_FIT_IMMUNE_CELL_MEMBERSHIP_V1.csv",
)

git_available = True
try:
    subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                   capture_output=True, check=True)
except Exception:  # pragma: no cover
    git_available = False

pytestmark = pytest.mark.skipif(not git_available, reason="not a git checkout")


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", *PUBLISHED_DIRS], cwd=str(ROOT),
                         capture_output=True, text=True, check=True)
    return out.stdout.split()


def _blob(path: str) -> bytes:
    return subprocess.run(["git", "cat-file", "blob", "HEAD:" + path],
                          cwd=str(ROOT), capture_output=True,
                          check=True).stdout


def _record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_publication_record_exists() -> None:
    record = _record()
    assert record["files"] == 79, record["files"]
    assert len(record["entries"]) == 79


def test_the_adjudicator_and_constants_are_present() -> None:
    """Without these, nothing else in the publication reproduces T0."""
    for path in MUST_BE_PRESENT:
        assert (ROOT / path).is_file(), path


def test_every_published_file_is_tracked() -> None:
    tracked = set(_tracked())
    for entry in _record()["entries"]:
        assert entry["published_path"] in tracked, entry["published_path"]


def test_no_pycache_was_published() -> None:
    assert not [p for p in _tracked() if "__pycache__" in p or p.endswith(".pyc")]


def test_every_published_blob_equals_the_bytes_on_disk() -> None:
    """The check that would catch a line-ending rewrite."""
    mismatched = [path for path in _tracked()
                  if _blob(path) != (ROOT / path).read_bytes()]
    assert not mismatched, mismatched


def test_the_published_bytes_match_the_recovery_package_manifest() -> None:
    """Digests recorded before this publication, so the check is independent."""
    for entry in _record()["entries"]:
        blob = _blob(entry["published_path"])
        assert hashlib.sha256(blob).hexdigest() == entry["sha256"], \
            entry["published_path"]
        assert len(blob) == entry["bytes"], entry["published_path"]


def test_the_text_rules_cover_every_published_directory() -> None:
    """Without these the digests break on a Windows checkout."""
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for directory in PUBLISHED_DIRS:
        assert "%s/** -text" % directory in attributes, directory
