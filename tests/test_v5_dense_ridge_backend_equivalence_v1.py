"""Deterministic dense-ridge backend equivalence qualification.

Purpose
-------
Qualify the numerical environment for the dense linear algebra the FULL104
masking estimators actually perform. The production ridge fit is, verbatim from
``full104_masking_streaming_executor_v1._fit_ridge``::

    regularized = gram + (alpha * n_total) * eye(p)
    solve(regularized, rhs / scale)

that is ``A = X.T @ X + alpha * n * I`` and ``b = X.T @ y / scale``. These tests
build exactly that system and require every available backend to agree on it.

**The estimator is not changed by this file.** These tests qualify a backend for
the existing mathematics; they do not select, replace, or tune an estimator.

Prospective tolerance policy
----------------------------
Every tolerance below is a closed-form function of the problem geometry, fixed
here *before* the comparisons were run, and derived from standard backward-error
analysis rather than from any observed output.

Let ``u = numpy.finfo(float).eps`` (2**-52).

``T1`` normwise relative residual, per method::

        rel_res = ||A x - b|| / (||A|| * ||x|| + ||b||)

    A backward-stable dense solver returns x satisfying (A + dA) x = b + db with
    ||dA|| <= c(n) u ||A||, so rel_res <= c(n) u for a modest polynomial c(n).
    We declare c(n) = 64 n, a deliberately loose constant that bounds LU with
    partial pivoting, Cholesky, and complete-orthogonal least squares alike:

        RESIDUAL_TOL(n) = 64 * n * u

``T2`` pairwise forward agreement between any two methods::

        rel_diff = ||x1 - x2|| / max(||x1||, ||x2||)

    Two backward-stable solutions of the same system differ in the forward sense
    by at most the condition number times their backward error:

        PAIRWISE_TOL(n, kappa) = 64 * n * u * kappa_2(A)

    This is the textbook forward-error bound. It is a function of the generated
    system, never of the computed answers.

``T3`` finiteness: every returned coefficient must be finite. No tolerance.

``kappa_2(A)`` is *recorded* for every geometry, as required, but is not itself
a pass criterion: it is a property of the fixture, not of the backend.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import json
import subprocess
import sys

import numpy as np
import pytest

U = float(np.finfo(np.float64).eps)

#: Geometries the frozen masking ridge actually uses.
SIZES = (4, 32, 64)

#: Ridge penalty scale. Mirrors the production call shape ``alpha * n_total``.
ALPHA = 0.01

#: Prospective backward-error constant. Declared before any comparison was run.
STABILITY_CONSTANT = 64


def residual_tol(n: int) -> float:
    """T1 bound: c(n) * u with c(n) = 64 n."""
    return STABILITY_CONSTANT * n * U


def pairwise_tol(n: int, kappa: float) -> float:
    """T2 bound: c(n) * u * kappa_2(A)."""
    return STABILITY_CONSTANT * n * U * kappa


def build_ridge_system(n_features: int, seed: int = 20260920) -> tuple[np.ndarray, np.ndarray, float]:
    """Construct the production ridge system ``A = X'X + alpha n I``, ``b = X'y / scale``.

    Columns are standardized and the target is a linear combination plus noise,
    mirroring ``_standardized_components`` in the streaming executor.
    """
    rng = np.random.default_rng(seed + n_features)
    n_rows = n_features * 4
    x = rng.normal(size=(n_rows, n_features))
    x -= x.mean(axis=0, keepdims=True)
    sd = x.std(axis=0, ddof=0, keepdims=True)
    x /= np.where(sd > 0.0, sd, 1.0)

    coef = rng.normal(size=n_features)
    y = x @ coef + 0.25 * rng.normal(size=n_rows)
    y -= y.mean()

    gram = x.T @ x
    rhs = x.T @ y
    scale = float(np.sqrt(max(float(y @ y) / n_rows, 0.0)))
    assert scale > 0.0, "degenerate fixture: zero target scale"

    a = gram + (ALPHA * n_rows) * np.eye(n_features, dtype=np.float64)
    b = rhs / scale
    return a, b, scale


def solve_with(method: str, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Solve ``A x = b`` by one backend. The mathematics is identical in each."""
    if method == "numpy_solve":
        return np.linalg.solve(a, b)
    if method == "numpy_cholesky":
        lower = np.linalg.cholesky(a)
        return np.linalg.solve(lower.T, np.linalg.solve(lower, b))
    if method == "numpy_lstsq":
        return np.linalg.lstsq(a, b, rcond=None)[0]
    if method == "scipy_solve_pos":
        import scipy.linalg as sla

        return sla.solve(a, b, assume_a="pos")
    if method == "scipy_cho":
        import scipy.linalg as sla

        return sla.cho_solve(sla.cho_factor(a), b)
    raise ValueError(f"unknown method {method!r}")


METHODS = ("numpy_solve", "numpy_cholesky", "numpy_lstsq", "scipy_solve_pos", "scipy_cho")


def relative_residual(a: np.ndarray, x: np.ndarray, b: np.ndarray) -> float:
    num = float(np.linalg.norm(a @ x - b))
    den = float(np.linalg.norm(a, 2) * np.linalg.norm(x) + np.linalg.norm(b))
    return num / den if den > 0.0 else num


# --------------------------------------------------------------------------- #
# Guard: the DLL-directory hazard that produced the 0xC06D007F evidence.
# --------------------------------------------------------------------------- #

_MKL_PROBE = (
    "import numpy as np;"
    "a=np.eye(8)*2.0;"
    "print('DOT',float((a@a)[0,0]));"
    "print('SOLVE',float(np.linalg.solve(a,np.ones(8))[0]))"
)


def test_blas_backend_is_reachable_in_a_child_process():
    """A child process launched exactly as production launches one must survive BLAS.

    numpy's conda ``libblas``/``liblapack`` are pure forwarder DLLs whose every
    export forwards to ``mkl_rt.3.dll``. Forwarder resolution happens at first
    call and uses the loader's own search order, which does **not** consult
    directories added via ``os.add_dll_directory``. If the environment's
    ``Library\\bin`` is not reachable, the forwarder fails with
    ERROR_PROC_NOT_FOUND (127) and the interpreter is killed outright -- no
    Python exception, no traceback.

    This must be checked in a subprocess: an in-process assertion cannot observe
    a hard process kill, and the kill would take the whole test session with it.
    """
    proc = subprocess.run(
        [sys.executable, "-c", _MKL_PROBE], capture_output=True, text=True, timeout=180
    )
    assert proc.returncode == 0, (
        "child interpreter died running plain numpy BLAS "
        f"(returncode {proc.returncode}). This is the DLL search-path hazard: the "
        "environment's Library\\bin is not reachable, so forwarder exports into "
        "mkl_rt.3.dll cannot resolve. It is an invocation defect, not a broken "
        f"numerical stack. stderr={proc.stderr[-400:]!r}"
    )
    assert "DOT 4.0" in proc.stdout and "SOLVE 0.5" in proc.stdout, proc.stdout


# --------------------------------------------------------------------------- #
# T1 / T3: per-method backward stability and finiteness.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("n_features", SIZES)
@pytest.mark.parametrize("method", METHODS)
def test_ridge_solution_is_backward_stable(method: str, n_features: int):
    a, b, _ = build_ridge_system(n_features)
    x = solve_with(method, a, b)

    assert np.all(np.isfinite(x)), f"{method} n={n_features}: non-finite coefficients"  # T3

    rel_res = relative_residual(a, x, b)
    tol = residual_tol(n_features)
    assert rel_res <= tol, (
        f"{method} n={n_features}: relative residual {rel_res:.3e} exceeds the "
        f"prospectively declared bound 64*n*u = {tol:.3e}"
    )


# --------------------------------------------------------------------------- #
# T2: every backend must agree on the same system.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("n_features", SIZES)
def test_all_backends_agree_on_the_production_ridge_system(n_features: int):
    a, b, _ = build_ridge_system(n_features)
    kappa = float(np.linalg.cond(a, 2))
    assert np.isfinite(kappa) and kappa >= 1.0, f"degenerate fixture: cond={kappa}"

    solutions = {m: solve_with(m, a, b) for m in METHODS}
    for name, x in solutions.items():
        assert np.all(np.isfinite(x)), f"{name} produced non-finite coefficients"

    tol = pairwise_tol(n_features, kappa)
    names = list(solutions)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            x1, x2 = solutions[left], solutions[right]
            denom = max(float(np.linalg.norm(x1)), float(np.linalg.norm(x2)), 1e-300)
            rel_diff = float(np.linalg.norm(x1 - x2)) / denom
            assert rel_diff <= tol, (
                f"n={n_features} cond={kappa:.3e}: {left} vs {right} differ by "
                f"{rel_diff:.3e}, exceeding the prospectively declared forward bound "
                f"64*n*u*cond = {tol:.3e}"
            )


def test_ridge_penalty_is_actually_regularizing():
    """Sanity: alpha*n*I must lift the smallest eigenvalue, else the fixture is vacuous."""
    for n_features in SIZES:
        a, _, _ = build_ridge_system(n_features)
        eigmin = float(np.linalg.eigvalsh(a).min())
        assert eigmin >= ALPHA * (n_features * 4) * 0.99, (
            f"n={n_features}: smallest eigenvalue {eigmin:.3e} is below the ridge "
            f"floor alpha*n={ALPHA * n_features * 4:.3e}; the system is not SPD as assumed"
        )


def emit_qualification_record() -> dict:
    """Machine-readable qualification evidence for every geometry and method."""
    record = {
        "schema": "V5_DENSE_RIDGE_BACKEND_EQUIVALENCE_V1",
        "estimator_changed": False,
        "equations": {"A": "X.T @ X + alpha * n * I", "b": "X.T @ y / scale"},
        "alpha": ALPHA,
        "unit_roundoff_eps": U,
        "stability_constant_c_of_n": "64 * n",
        "tolerances_declared_before_execution": True,
        "geometries": [],
    }
    for n_features in SIZES:
        a, b, scale = build_ridge_system(n_features)
        kappa = float(np.linalg.cond(a, 2))
        entry = {
            "n_features": n_features,
            "n_rows": n_features * 4,
            "target_scale": scale,
            "cond_2_A": kappa,
            "residual_tol": residual_tol(n_features),
            "pairwise_tol": pairwise_tol(n_features, kappa),
            "methods": {},
            "pairwise": {},
        }
        solutions = {}
        for method in METHODS:
            x = solve_with(method, a, b)
            solutions[method] = x
            entry["methods"][method] = {
                "relative_residual": relative_residual(a, x, b),
                "all_finite": bool(np.all(np.isfinite(x))),
                "norm_x": float(np.linalg.norm(x)),
            }
        names = list(solutions)
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                x1, x2 = solutions[left], solutions[right]
                denom = max(float(np.linalg.norm(x1)), float(np.linalg.norm(x2)), 1e-300)
                entry["pairwise"][f"{left}|{right}"] = float(np.linalg.norm(x1 - x2)) / denom
        record["geometries"].append(entry)
    return record


if __name__ == "__main__":
    print(json.dumps(emit_qualification_record(), indent=2))
