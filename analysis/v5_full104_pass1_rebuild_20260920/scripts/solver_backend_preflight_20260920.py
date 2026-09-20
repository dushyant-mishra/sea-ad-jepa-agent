"""Subprocess-isolated dense-solver preflight for the canonical environment.

`np.linalg.solve` terminates the canonical interpreter (Windows fatal exception
0xc06d007f) rather than raising, so every probe must run in its own subprocess:
an in-process try/except cannot observe the failure, and catching a fatal
process error and continuing would be unsafe anyway.

This script DIAGNOSES ONLY. It changes no production solver code, installs
nothing, and selects no estimator. Its output is evidence for deciding whether
the environment can be qualified, not a repair.

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
                "stderr": proc.stderr.strip()[-400:]}
    payload["exit_code"] = proc.returncode
    payload["failure_mode"] = None if payload.get("ok") else "RAISED"
    payload["stderr"] = proc.stderr.strip()[-400:]
    return payload


def environment(python: str) -> dict:
    code = r"""
import json, sys, platform
out = {"python": sys.version.split()[0], "platform": platform.platform(), "executable": sys.executable}
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
        with_err = [r for r in results if r.get("stderr")]
        print("  sample stderr                 :",
              (with_err[0]["stderr"][:200] if with_err else "(empty on every probe - hard process kill, not a Python exception)"))
    print()
    print("  DIAGNOSIS ONLY. No production solver code was changed, nothing was")
    print("  installed, and no estimator was selected.")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"schema": "V5_DENSE_SOLVER_BACKEND_PREFLIGHT_V1",
             "environment": env, "probes": results,
             "methods_completed": usable, "methods_fatal": fatal,
             "diagnosis_only": True, "production_solver_changed": False},
            indent=2) + "\n", encoding="utf-8")
        print("\n  written:", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
