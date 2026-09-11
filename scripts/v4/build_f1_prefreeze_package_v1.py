#!/usr/bin/env python3
"""Build the F1 producer/replay pre-freeze manifest and root.

Runs as the LAST mutation. Digests are taken from the bytes committed at HEAD,
never the working tree or mutable index, because a text-classified source can be
checked out with platform-specific line endings. Every manifested path must
already be tracked and clean relative to HEAD. Dirty, staged, or untracked input
is a hard STOP; the builder never stages anything on the caller's behalf.
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
    "scripts/v4/f1_execution_authorization_v1.py",
    "scripts/v4/f1_production_runtime_adapter_v1.py",
    "scripts/v4/f1_evidence_mask_authority_v1.py",
    "tests/test_f1_real_producer_replay_parity_v1.py",
    "tests/test_f1_evidence_mask_authority_v1.py",
    "tests/test_f1_u0_adapter_smoke_v1.py",
    "scripts/v4/build_f1_prefreeze_package_v1.py",
)

BOUND_UPSTREAM = (
    "scripts/v4/contextual_target_f1_preflight_executor_v1.py",
    "src/sea_ad_jepa/v4/contextual_query_local.py",
    "src/sea_ad_jepa/v4/ipb_jepa.py",
    "src/sea_ad_jepa/v4/gene_tokenizer.py",
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
    "docs/agent/F1_REAL_PRODUCER_REPLAY_EXTERNAL_REVIEW_HANDOFF_20260907.md",
    "docs/agent/F1_EXECUTION_AUTHORIZATION_DESIGN_20260907.md",
    "docs/agent/F1_EA35_REPAIR_RESPONSE_20260907.md",
)


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)


def git_bytes(relative: str) -> bytes:
    """Return exact ``HEAD:<path>`` bytes without mutating git state.

    Package creation is intentionally stricter than an ordinary source read:
    the requested member must already be tracked at HEAD and both the index and
    working tree must agree with HEAD. This prevents a dirty or staged repair
    from being silently absorbed into a supposedly immutable package.
    """
    tracked = _git("ls-files", "--error-unmatch", "--", relative)
    if tracked.returncode != 0:
        raise RuntimeError(
            "STOP_F1_PREFREEZE_UNTRACKED_MEMBER: %s must already be tracked at HEAD"
            % relative)

    dirty = _git("diff", "--quiet", "HEAD", "--", relative)
    if dirty.returncode == 1:
        raise RuntimeError(
            "STOP_F1_PREFREEZE_DIRTY_MEMBER: %s differs from HEAD; commit or discard "
            "the change before building the immutable package" % relative)
    if dirty.returncode != 0:
        raise RuntimeError(
            "STOP_F1_PREFREEZE_GIT_DIFF_ERROR: unable to verify %s is clean: %s"
            % (relative, dirty.stderr.decode("utf-8", errors="replace")))

    result = _git("show", "HEAD:" + relative)
    if result.returncode != 0:
        raise RuntimeError(
            "STOP_F1_PREFREEZE_HEAD_MEMBER_MISSING: HEAD:%s is not readable: %s"
            % (relative, result.stderr.decode("utf-8", errors="replace")))
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
        "bytes_authority": "GIT_HEAD_BLOB_BYTES_PLATFORM_INDEPENDENT",
        "members": len(rows) - 1,
        "frozen_sources": len(FROZEN_SOURCES),
        "prefreeze_root_sha256": root,
        "producer_sha256": hashlib.sha256(
            git_bytes("scripts/v4/f1_real_producer_v1.py")).hexdigest(),
        "replay_sha256": hashlib.sha256(
            git_bytes("scripts/v4/f1_real_replay_v1.py")).hexdigest(),
        "terminal": ("PASS_F1_U0_PRODUCTION_MECHANICS_PREFREEZE_READY_FOR_"
                     "INDEPENDENT_REVIEW__REAL_F1_STILL_UNAUTHORIZED"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
