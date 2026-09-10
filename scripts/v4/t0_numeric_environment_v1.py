#!/usr/bin/env python3
"""Record the numeric stack a run was executed on.

The T0 V20 provenance hole was not a missing digest. Every input was bound by
SHA-256. What no summary recorded was the arithmetic: which Python, NumPy,
SciPy and BLAS produced the frozen bytes. Because the frozen target verifier
compares float arrays with `np.array_equal`, that omission is what made the run
unreplayable — the result is verified to the last bit against an environment
nobody wrote down.

So this exists to be called from every run record from now on. It is cheap,
reads nothing but the interpreter's own state, and makes the difference between
"this replay disagrees in the last bit" and "this replay disagrees in the last
bit *and here is the stack difference that explains it*".

Why the BLAS threading fields are here and not just the versions. OpenBLAS
splits a reduction across threads, and the number of threads changes the
association order of the sums. Different thread counts on the same library and
the same inputs can therefore differ in the final bits, so a recorded version
alone does not pin the arithmetic. `threadpoolctl` is used when present and its
absence is recorded rather than passed over in silence.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from typing import Any

# Variables that change BLAS reduction order, and so the last bits.
THREADING_VARIABLES = (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    "KMP_DUPLICATE_LIB_OK", "MKL_THREADING_LAYER",
)


def _package_versions() -> dict[str, Any]:
    versions: dict[str, Any] = {}
    for name in ("numpy", "scipy", "pandas", "sklearn"):
        try:
            module = __import__(name)
        except Exception as error:                   # pragma: no cover
            versions[name] = "unavailable: %r" % error
            continue
        versions[name] = getattr(module, "__version__", "unknown")
    return versions


def _numpy_build() -> dict[str, Any]:
    """BLAS and LAPACK as NumPy itself reports them, plus its SIMD dispatch."""
    try:
        import numpy as np
        config = np.show_config("dicts") or {}
    except Exception as error:                       # pragma: no cover
        return {"unavailable": "%r" % error}

    build = config.get("Build Dependencies", {})
    report: dict[str, Any] = {}
    for library in ("blas", "lapack"):
        entry = build.get(library)
        if isinstance(entry, dict):
            report[library] = {key: entry.get(key) for key in
                               ("name", "version", "detection method")}
    simd = config.get("SIMD Extensions", {})
    if isinstance(simd, dict):
        # The baseline and the dispatched set both bear on which kernel runs.
        report["simd"] = {key: simd.get(key)
                          for key in ("baseline", "found", "not_found")
                          if key in simd}
    machine = config.get("Machine Information", {})
    if isinstance(machine, dict):
        host = machine.get("host")
        if isinstance(host, dict):
            report["build_host_cpu"] = {k: host.get(k)
                                        for k in ("cpu", "family", "endian")
                                        if k in host}
    return report


def _threadpools() -> dict[str, Any]:
    """The loaded BLAS pools and their thread counts, which set reduction order."""
    try:
        import threadpoolctl
    except Exception as error:
        return {"threadpoolctl": "unavailable: %r" % error,
                "note": "BLAS thread count not observed; reduction order for "
                        "this run is therefore not fully pinned"}
    try:
        pools = threadpoolctl.threadpool_info()
    except Exception as error:                       # pragma: no cover
        return {"threadpoolctl": "failed: %r" % error}
    return {"threadpoolctl": getattr(threadpoolctl, "__version__", "unknown"),
            "pools": [{key: pool.get(key) for key in
                       ("user_api", "internal_api", "prefix", "version",
                        "num_threads", "threading_layer")
                       if key in pool} for pool in pools]}


def numeric_environment() -> dict[str, Any]:
    """Everything about this process that can move a floating-point result."""
    record: dict[str, Any] = {
        "schema": "JEPA_T0_NUMERIC_ENVIRONMENT_V1",
        "why": "The frozen T0 target verifier compares float arrays bit-exactly, "
               "so a replay is only interpretable alongside the arithmetic that "
               "produced it. No earlier T0 summary recorded this.",
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "packages": _package_versions(),
        "numpy_build": _numpy_build(),
        "threading": _threadpools(),
        "threading_environment_variables": {
            name: os.environ.get(name) for name in THREADING_VARIABLES},
        "platform": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
    }
    # A digest so a run record can bind the environment the way it binds inputs.
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"),
                           default=str).encode("utf-8")
    record["environment_sha256"] = hashlib.sha256(canonical).hexdigest()
    return record


def main() -> int:
    print(json.dumps(numeric_environment(), indent=2, sort_keys=True,
                     default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
