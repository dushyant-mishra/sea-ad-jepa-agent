#!/usr/bin/env python3
"""Build the F1 producer/replay pre-freeze manifest and root.

Runs as the LAST mutation. Digests are taken from the bytes git holds, never the
working tree, because a text-classified source is checked out with CRLF on
Windows and its digest would then differ from the immutable blob by one byte per
line. This project has already had a package rejected for exactly that.

Every manifested path must be tracked. An untracked member fails loudly rather
than being hashed from disk.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "outputs" / "f1_real_producer_replay_prefreeze_20260907"

FROZEN_SOURCES = (
    "scripts/v4/f1_real_producer_v1.py",
    "scripts/v4/f1_real_replay_v1.py",
    "tests/test_f1_real_producer_replay_parity_v1.py",
    "scripts/v4/build_f1_prefreeze_package_v1.py",
)

BOUND_UPSTREAM = (
    "scripts/v4/contextual_target_f1_preflight_executor_v1.py",
    "scripts/v4/validate_f1_production_mechanics_acceptance_v1.py",
    "docs/agent/F1_PRODUCTION_MECHANICS_ACCEPTANCE_CONTRACT_20260903.md",
    "docs/agent/F1_REAL_READER_FORWARD_EXECUTOR_PREFLIGHT_CONTRACT_20260903.md",
    "docs/agent/f1_real_reader_forward_executor_preflight_20260903/F1_PREFLIGHT_AUTHORITY_BINDING.json",
    "docs/agent/f1_real_reader_forward_executor_preflight_20260903/F1_PREFLIGHT_REAL_FORWARD_ROOT.json",
    "docs/agent/f1_real_reader_forward_executor_preflight_20260903/F1_PREFLIGHT_READER_PLAN_BINDING.json",
)

CONTRACTS = (
    "docs/agent/F1_REAL_PRODUCER_REPLAY_PREFREEZE_CONTRACT_20260907.md",
    "docs/agent/F1_DATA_ONLY_CLOSURE_DESIGN_20260907.md",
)


def git_bytes(relative: str) -> bytes:
    """Exact bytes git holds for a tracked path. Platform-independent."""
    subprocess.run(["git", "-C", str(ROOT), "add", "--", relative],
                   capture_output=True, check=True)
    result = subprocess.run(["git", "-C", str(ROOT), "show", ":" + relative],
                            capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            "STOP_F1_PREFREEZE_UNTRACKED_MEMBER: %s must be tracked so its digest "
            "is platform-independent" % relative)
    return result.stdout


def main() -> int:
    PACKAGE.mkdir(parents=True, exist_ok=True)
    rows = ["role,path,sha256,bytes"]
    digests: list[str] = []
    for role, group in (("frozen_source", FROZEN_SOURCES),
                        ("bound_upstream", BOUND_UPSTREAM),
                        ("contract", CONTRACTS)):
        for relative in group:
            if not (ROOT / relative).is_file():
                raise RuntimeError("STOP_F1_PREFREEZE_MISSING_MEMBER: " + relative)
            payload = git_bytes(relative)
            digest = hashlib.sha256(payload).hexdigest()
            rows.append("%s,%s,%s,%d" % (role, relative, digest, len(payload)))
            digests.append(digest)

    manifest = PACKAGE / "F1_PREFREEZE_MANIFEST.csv"
    with io.open(manifest, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(rows) + "\n")
    root = hashlib.sha256("".join(sorted(digests)).encode("utf-8")).hexdigest()
    with io.open(PACKAGE / "F1_PREFREEZE_ROOT_SHA256.txt", "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(root + "\n")

    print(json.dumps({
        "schema": "F1_REAL_PRODUCER_REPLAY_PREFREEZE_PACKAGE_V1",
        "bytes_authority": "GIT_BLOB_BYTES_PLATFORM_INDEPENDENT",
        "members": len(rows) - 1,
        "frozen_sources": len(FROZEN_SOURCES),
        "prefreeze_root_sha256": root,
        "producer_sha256": hashlib.sha256(
            git_bytes("scripts/v4/f1_real_producer_v1.py")).hexdigest(),
        "replay_sha256": hashlib.sha256(
            git_bytes("scripts/v4/f1_real_replay_v1.py")).hexdigest(),
        "terminal": "PRODUCER_AND_REPLAY_SOURCE_FROZEN__REAL_F1_STILL_UNAUTHORIZED",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
