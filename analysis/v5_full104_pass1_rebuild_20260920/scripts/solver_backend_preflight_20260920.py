"""Subprocess-isolated dense-solver preflight for the canonical environment.

Dense LAPACK can terminate the interpreter outright (Windows fatal exception
0xc06d007f) rather than raising, so every probe must run in its own subprocess:
an in-process try/except cannot observe a hard process kill, and catching a
fatal process error and continuing would be unsafe anyway.

What 0xc06d007f actually means
------------------------------
``0xC06D007F`` is the Visual C++ delay-load/forwarder helper exception carrying
Win32 status ``127 = ERROR_PROC_NOT_FOUND`` -- *a module that loaded but did not
supply a required export*. It is **not** ``126 = ERROR_MOD_NOT_FOUND``. The
distinction matters: the observed failure is a resolution failure, not a missing
file, and an earlier revision of this project's diagnosis misread it as evidence
of an incoherent package stack.

In this environment the concrete mechanism is:

* ``Library\\bin\\liblapack.dll`` and ``libblas.dll`` are *pure forwarder* DLLs --
  every one of their 1949 / 151 exports forwards to ``mkl_rt.3.dll``;
* forwarder targets are resolved by the loader at **first call**, using the
  loader's own search order, which does **not** consult directories registered
  through ``os.add_dll_directory``;
* so if ``<env>\\Library\\bin`` is not on ``PATH``, ``import numpy`` succeeds and
  the first BLAS or LAPACK call kills the process.

That is an **invocation** defect, not a broken numerical stack. This preflight
therefore records DLL-directory reachability alongside the probe results, so the
two can never again be confused.

This script DIAGNOSES ONLY. It changes no production solver code, installs
nothing, and selects no estimator.

Usage:
    python solver_backend_preflight_20260920.py [--python <interpreter>] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Deterministic symmetric positive-definite systems at the geometries the frozen
# masking ridge actually uses.
PROBE = r"""
import json, sys
import numpy as np

n = {n}
method = "{method}"
rng = np.random.default_rng(20260920)
A = rng.normal(size=(n * 4, n))
gram = A.T @ A + 0.01 * (n * 4) * np.eye(n)
b = gram @ np.ones(n)

out = {{"n": n, "method": method}}
try:
    if method == "numpy_solve":
        x = np.linalg.solve(gram, b)
    elif method == "numpy_cholesky":
        L = np.linalg.cholesky(gram)
        y = np.linalg.solve(L, b)
        x = np.linalg.solve(L.T, y)
    elif method == "numpy_lstsq":
        x = np.linalg.lstsq(gram, b, rcond=None)[0]
    elif method == "scipy_solve_pos":
        import scipy.linalg as sla
        x = sla.solve(gram, b, assume_a="pos")
    elif method == "scipy_cho":
        import scipy.linalg as sla
        c = sla.cho_factor(gram)
        x = sla.cho_solve(c, b)
    else:
        raise SystemExit("unknown method")
    residual = float(np.linalg.norm(gram @ x - b) / max(np.linalg.norm(b), 1e-30))
    out.update(ok=True, residual=residual,
               max_abs_err_vs_ones=float(np.max(np.abs(x - 1.0))),
               finite=bool(np.all(np.isfinite(x))))
except Exception as exc:
    out.update(ok=False, error=f"{{type(exc).__name__}}: {{exc}}")
print("RESULT " + json.dumps(out))
"""

METHODS = ("numpy_solve", "numpy_cholesky", "numpy_lstsq", "scipy_solve_pos", "scipy_cho")
SIZES = (4, 32, 64)


#: Win32 statuses the VC++ delay-load/forwarder helper reports, and the plain
#: exit codes CPython yields when the loader kills it. Decoding these is what
#: separates "a DLL is missing" from "a DLL loaded but lacked an export".
_WIN32_STATUS = {
    126: "ERROR_MOD_NOT_FOUND (a required DLL could not be found)",
    127: "ERROR_PROC_NOT_FOUND (a DLL loaded but did not supply a required export)",
}


def _decode_win32(code: int | None) -> str | None:
    if code is None:
        return None
    low = code & 0xFFFF
    if (code & 0xFFFFFFFF) == 0xC06D007F or low in _WIN32_STATUS:
        return _WIN32_STATUS.get(low, f"unmapped win32 status {low}")
    return None


def run_probe(python: str, n: int, method: str, timeout: int = 120) -> dict:
    code = PROBE.format(n=n, method=method)
    try:
        proc = subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"n": n, "method": method, "ok": False, "exit_code": None,
                "failure_mode": "TIMEOUT", "stderr": ""}
    payload = None
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT "):
            payload = json.loads(line[len("RESULT "):])
            break
    if payload is None:
        return {"n": n, "method": method, "ok": False, "exit_code": proc.returncode,
                "failure_mode": "PROCESS_TERMINATED_WITHOUT_RESULT",
                "win32_status": _decode_win32(proc.returncode),
                "stderr": proc.stderr.strip()[-400:]}
    payload["exit_code"] = proc.returncode
    payload["failure_mode"] = None if payload.get("ok") else "RAISED"
    payload["stderr"] = proc.stderr.strip()[-400:]
    return payload


def environment(python: str) -> dict:
    code = r"""
import json, sys, platform, os
out = {"python": sys.version.split()[0], "platform": platform.platform(), "executable": sys.executable}

# The determinant of the 0xC06D007F failure: is the environment's native DLL
# directory reachable by the loader when it resolves forwarder targets?
prefix = os.path.dirname(sys.executable)
libbin = os.path.join(prefix, "Library", "bin")
path_entries = [p.rstrip("\\/").lower() for p in os.environ.get("PATH", "").split(os.pathsep) if p]
out["library_bin"] = libbin
out["library_bin_exists"] = os.path.isdir(libbin)
out["library_bin_on_path"] = libbin.rstrip("\\/").lower() in path_entries
out["mkl_rt_present"] = sorted(
    f for f in (os.listdir(libbin) if os.path.isdir(libbin) else []) if f.lower().startswith("mkl_rt")
)
try:
    import numpy
    out["numpy"] = numpy.__version__
    try:
        cfg = numpy.__config__.show(mode="dicts")
        bd = cfg.get("Build Dependencies", {})
        out["blas"] = {k: bd.get("blas", {}).get(k) for k in ("name", "version", "detection method")}
        out["lapack"] = {k: bd.get("lapack", {}).get(k) for k in ("name", "version", "detection method")}
    except Exception as exc:
        out["numpy_config_error"] = str(exc)
except Exception as exc:
    out["numpy_error"] = str(exc)
try:
    import scipy
    out["scipy"] = scipy.__version__
except Exception as exc:
    out["scipy_error"] = str(exc)
print("ENV " + json.dumps(out))
"""
    proc = subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=180)
    for line in proc.stdout.splitlines():
        if line.startswith("ENV "):
            return json.loads(line[len("ENV "):])
    return {"error": "environment probe produced no result", "stderr": proc.stderr[-400:]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    env = environment(args.python)
    print("=" * 78)
    print("ENVIRONMENT")
    print("=" * 78)
    for key, value in env.items():
        print("  %-12s %s" % (key, value))

    print()
    print("=" * 78)
    print("DENSE SOLVER PROBES (each in its own subprocess)")
    print("=" * 78)
    print("  %-18s %-5s %-6s %-10s %-12s %s"
          % ("method", "n", "ok", "exit", "residual", "failure_mode"))
    results = []
    for method in METHODS:
        for n in SIZES:
            r = run_probe(args.python, n, method)
            results.append(r)
            res = r.get("residual")
            print("  %-18s %-5d %-6s %-10s %-12s %s"
                  % (method, n, r.get("ok"), str(r.get("exit_code")),
                     ("%.3e" % res) if isinstance(res, float) else "-",
                     r.get("failure_mode") or ""))

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    usable = sorted({r["method"] for r in results if r.get("ok")})
    fatal = sorted({r["method"] for r in results
                    if r.get("failure_mode") == "PROCESS_TERMINATED_WITHOUT_RESULT"})
    print("  methods that completed        :", usable or "none")
    print("  methods that killed the process:", fatal or "none")
    if fatal:
        codes = sorted({r.get("exit_code") for r in results
                        if r.get("failure_mode") == "PROCESS_TERMINATED_WITHOUT_RESULT"})
        print("  fatal exit codes              :",
              [(c, hex(c & 0xFFFFFFFF) if isinstance(c, int) else None) for c in codes])
        for c in codes:
            print("  win32 status                  :", _decode_win32(c) or "(not a loader status)")
        with_err = [r for r in results if r.get("stderr")]
        print("  sample stderr                 :",
              (with_err[0]["stderr"][:200] if with_err else "(empty on every probe - hard process kill, not a Python exception)"))

    # The determinant, printed next to the result so the two are never separated.
    reachable = env.get("library_bin_on_path")
    print()
    print("  Library\\bin                    :", env.get("library_bin"))
    print("  Library\\bin on PATH            :", reachable)
    print("  mkl_rt builds present          :", env.get("mkl_rt_present"))

    if fatal and reachable is False:
        classification = ("INVOCATION_DEFECT__DLL_DIRECTORY_NOT_ON_PATH "
                          "(forwarder exports into mkl_rt cannot resolve; "
                          "the numerical stack itself is not implicated)")
    elif fatal:
        classification = "UNEXPLAINED__DLL_DIRECTORY_REACHABLE_BUT_PROBES_STILL_DIED"
    elif reachable is False:
        classification = "PASSED_WITHOUT_PATH__BACKEND_DOES_NOT_DEPEND_ON_LIBRARY_BIN"
    else:
        classification = "ALL_PROBES_COMPLETED__DLL_DIRECTORY_REACHABLE"
    print("  classification                 :", classification)

    print()
    print("  DIAGNOSIS ONLY. No production solver code was changed, nothing was")
    print("  installed, and no estimator was selected.")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"schema": "V5_DENSE_SOLVER_BACKEND_PREFLIGHT_V2",
             "environment": env, "probes": results,
             "methods_completed": usable, "methods_fatal": fatal,
             "classification": classification,
             "diagnosis_only": True, "production_solver_changed": False},
            indent=2) + "\n", encoding="utf-8")
        print("\n  written:", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
