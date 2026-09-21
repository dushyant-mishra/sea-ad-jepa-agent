#!/usr/bin/env python3
"""Prepare or validate a fresh current-root-bound FULL104 shakedown runtime."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from sea_ad_jepa.v5.full104_runtime_envelope_v1 import (
    CANONICAL_REGISTRY_SHA256,
    FULL104_BLOCK_MANIFEST_SHA256,
    OBSERVATION_STATE_SHA256,
    live_clean_scientific_head,
    prepare_fresh_runtime,
    sha256_file,
    validate_runtime_envelope,
)


#: Plain BLAS and dense LAPACK, run in a child so a hard loader kill is
#: observable rather than fatal to this process.
_DENSE_LA_PROBE = (
    "import numpy as np;"
    "a=np.eye(8)*2.0;"
    "assert float((a@a)[0,0])==4.0;"
    "assert float(np.linalg.solve(a,np.ones(8))[0])==0.5;"
    "print('DENSE_LA_OK')"
)


def require_dense_linear_algebra() -> None:
    """Fail before a long run starts if BLAS/LAPACK would kill the interpreter.

    On Windows conda environments, ``libblas.dll`` and ``liblapack.dll`` are pure
    forwarder DLLs whose exports all forward to ``mkl_rt.<n>.dll``. Forwarders are
    resolved by the loader at first call and do **not** consult directories
    registered with ``os.add_dll_directory``. So when an interpreter is launched
    by absolute path without activating its environment, ``import numpy``
    succeeds and the first ``@`` or ``np.linalg.solve`` terminates the process
    with Win32 status 127 (ERROR_PROC_NOT_FOUND, surfaced as 0xC06D007F) -- no
    exception, no traceback.

    Every FULL104 estimator solves a dense ridge system, so a run launched that
    way would die partway through with no diagnosable error. This precondition
    converts that into an immediate, explanatory failure.
    """
    proc = subprocess.run(
        [sys.executable, "-c", _DENSE_LA_PROBE], capture_output=True, text=True, timeout=180
    )
    if proc.returncode == 0 and "DENSE_LA_OK" in proc.stdout:
        return
    prefix = Path(sys.executable).parent
    raise SystemExit(
        "dense linear algebra is not usable from this interpreter "
        f"(child returncode {proc.returncode}). Every FULL104 estimator solves a "
        "dense ridge system, so this run would terminate partway through with no "
        "Python traceback.\n"
        f"  interpreter : {sys.executable}\n"
        f"  expected DLL directory: {prefix / 'Library' / 'bin'}\n"
        "  remedy: activate the environment, or prepend that directory to PATH, so "
        "forwarder exports into mkl_rt can resolve. This is an invocation "
        "condition, not a defect in the numerical packages.\n"
        f"  child stderr: {proc.stderr.strip()[-400:]!r}"
    )


def main() -> int:
    require_dense_linear_algebra()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("prepare", "validate"), required=True)
    p.add_argument("--runtime-root", type=Path, required=True)
    p.add_argument("--worktree", type=Path, required=True)
    p.add_argument("--expected-scientific-anchor", required=True)
    p.add_argument("--level4-root", type=Path)
    p.add_argument("--registry", type=Path)
    p.add_argument("--observation-state", type=Path)
    args = p.parse_args()

    live_head = live_clean_scientific_head(args.worktree)
    if args.expected_scientific_anchor.lower() != live_head:
        raise SystemExit(
            "expected scientific anchor does not equal the live clean worktree HEAD"
        )

    if args.mode == "prepare":
        for name in ("level4_root", "registry", "observation_state"):
            if getattr(args, name) is None:
                raise SystemExit(f"--{name.replace('_', '-')} is required in prepare mode")
        manifest = args.level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
        if not manifest.is_file():
            raise SystemExit("FULL104 Level-4 block manifest is missing")
        roots = {
            "full104_block_manifest_sha256": sha256_file(manifest),
            "canonical_registry_sha256": sha256_file(args.registry),
            "observation_state_sha256": sha256_file(args.observation_state),
        }
        expected = {
            "full104_block_manifest_sha256": FULL104_BLOCK_MANIFEST_SHA256,
            "canonical_registry_sha256": CANONICAL_REGISTRY_SHA256,
            "observation_state_sha256": OBSERVATION_STATE_SHA256,
        }
        for role, value in roots.items():
            if value != expected[role]:
                raise SystemExit(
                    f"{role} mismatch: expected {expected[role]}, observed {value}"
                )
        envelope = prepare_fresh_runtime(
            args.runtime_root,
            scientific_anchor_git_oid=live_head,
            **roots,
        )
    else:
        envelope = validate_runtime_envelope(
            args.runtime_root,
            expected_scientific_anchor_git_oid=live_head,
        )

    print(
        json.dumps(
            {
                "status": (
                    "FULL104_FRESH_RUNTIME_PREPARED"
                    if args.mode == "prepare"
                    else "FULL104_RUNTIME_ENVELOPE_VALID"
                ),
                "runtime_root": str(args.runtime_root),
                "runtime_envelope_sha256": envelope.canonical_digest(),
                "target_panel_ladder_authorized": False,
                "terminal_masking_authorized": False,
                "protected_outcomes_authorized": False,
                "training_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
