#!/usr/bin/env python3
"""Hash-bind every C2 artifact into a handoff-safe package.

The causal result must not depend on local-only /tmp or unmanifested worktree
files. This walks the preserved C2 outputs plus the sources, configs and
contracts they were produced by, writes a manifest and a package root digest,
and prints the registry rows for the work checkpoint.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "outputs" / "c2_t1_gradient_forensic_20260906"

BOUND_SOURCES = (
    "configs/v4/c2_t1_gradient_forensic_v1.json",
    "configs/v4/c2_t1_gradient_forensic_v2.json",
    "docs/agent/C2_T1_GRADIENT_FORENSIC_CONTRACT_20260905.md",
    "docs/agent/C2_V3_HISTORICAL_PATH_CORRESPONDENCE.md",
    "scripts/v4/run_c2_t1_exact_path_forensic_v3.py",
    "scripts/v4/c2_synthetic_loader_v3.py",
    "scripts/v4/c2_attention_cast_variant_v3.py",
    "scripts/v4/c2_corrective_run_update_v3.py",
    "scripts/v4/c2_probe_attention_boundary_v3.py",
    "scripts/v4/c2_mandatory_gradient_gate_v1.py",
    "scripts/v4/run_c2_t1_gradient_forensic_v1.py",
    "tests/test_c2_t1_gradient_forensic_v1.py",
    "tests/test_c2_synthetic_loader_v3.py",
    "tests/test_c2_t1_checkpoint_gradient_provenance_v1.py",
    "tests/test_c2_mandatory_gradient_gate_v1.py",
)

CLOSURE_CRITICAL = (
    "v3_exact_path/C2_V3_K0_HISTORICAL.json",
    "v3_exact_path/C2_V3_K1_BACKWARD_AUTOCAST_DISABLED.json",
    "v3_exact_path/C2_V3_K1_PRE_CRITERION_REPAIR.json",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rows = ["role,path,sha256,bytes"]
    digests = []

    for relative in sorted(BOUND_SOURCES):
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError("bound source missing: " + relative)
        digest = sha256_file(path)
        rows.append("bound_source,%s,%s,%d" % (relative, digest, path.stat().st_size))
        digests.append(digest)

    results = sorted(
        p for p in PACKAGE.rglob("*")
        if p.is_file() and p.name not in ("C2_RESULT_MANIFEST.csv", "C2_PACKAGE_ROOT_SHA256.txt")
    )
    for path in results:
        relative = path.relative_to(PACKAGE).as_posix()
        role = "closure_critical" if relative in CLOSURE_CRITICAL else "result"
        digest = sha256_file(path)
        rows.append("%s,%s,%s,%d" % (role, relative, digest, path.stat().st_size))
        digests.append(digest)

    missing = [name for name in CLOSURE_CRITICAL if not (PACKAGE / name).is_file()]
    if missing:
        raise RuntimeError("closure-critical artifact missing: " + str(missing))

    manifest = PACKAGE / "C2_RESULT_MANIFEST.csv"
    with io.open(manifest, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(rows) + "\n")

    root = hashlib.sha256("".join(sorted(digests)).encode("utf-8")).hexdigest()
    with io.open(PACKAGE / "C2_PACKAGE_ROOT_SHA256.txt", "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(root + "\n")

    registry = [
        {
            "path": "outputs/c2_t1_gradient_forensic_20260906/" + name,
            "sha256": sha256_file(PACKAGE / name),
            "authority": "C2_CLOSURE_CRITICAL",
        }
        for name in CLOSURE_CRITICAL
    ]
    registry.append({
        "path": "outputs/c2_t1_gradient_forensic_20260906/C2_RESULT_MANIFEST.csv",
        "sha256": sha256_file(manifest),
        "authority": "C2_PACKAGE_MANIFEST",
    })
    print(json.dumps({
        "package_root_sha256": root,
        "files": len(rows) - 1,
        "bound_sources": len(BOUND_SOURCES),
        "registry": registry,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
