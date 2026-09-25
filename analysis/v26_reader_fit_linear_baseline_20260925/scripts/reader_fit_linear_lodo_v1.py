"""Outcome-blind 104-donor FULL104 VALUE-only linear LODO comparator.

A NEW comparator, not a replay of the historical 94-donor z5_lodo analysis.
It consumes only the SHA-bound V0/V1 expression-view arrays and the frozen
104-reader-fit pass1 donor/source roster in exact selection_row order. It
requires separately independently certified pass1-to-Level4 physical lineage.
No pathology, sealed outcomes, oracle, external studies, or perturbation labels.

Primary metric: leave-one-donor-out within each source, train with equal mass
per other donor, score held-out per-cell error and macro-average equally over
held-out donors. The target is the other view's 256 VALUE channels of the SAME
cell. There is deliberately NO OPERATOR CENTERING: the physical operator-vector
for all selection rows has not been bound here, so the historical operator-
centred R2 is NOT a head-to-head comparator. Optionally add a separately
qualified operator-centred successor, not a guessed operator vector.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Iterable

import numpy as np

FROZEN_PASS1_SHA256 = "37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1"
V0_SHA256 = "3b3f102c6767727ca4ab56832f8e70baf203676d6b65973c42903b22b6d56ada"
V1_SHA256 = "c41df46d842d643f04566b8523a8aa711fa54bec1c836e0b394c0146017f231c"
EXPECTED_ROWS, EXPECTED_DONORS = 4_553_407, 104
EXPECTED_SHAPE = (EXPECTED_ROWS, 512)
EXPECTED_SOURCE_COUNTS = {"HVS": 41, "NPH52": 17, "SEA_AD": 46}
SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
WIDTH = 256
RIDGE = 0.01


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(8 << 20), b""):
            h.update(part)
    return h.hexdigest()


def require_exact_file(path: Path, expected: str) -> None:
    if not path.is_file():
        raise ValueError("required input absent: " + path.name)
    if sha256_file(path) != expected:
        raise ValueError("SHA-256 mismatch: " + path.name)


@dataclass
class Moments:
    n: int
    sx: np.ndarray
    sy: np.ndarray
    xx: np.ndarray
    xy: np.ndarray
    yy: float

    @classmethod
    def empty(cls, width: int) -> "Moments":
        return cls(0, np.zeros(width, np.float64), np.zeros(width, np.float64),
                   np.zeros((width, width), np.float64),
                   np.zeros((width, width), np.float64), 0.0)

    def add_block(self, X: np.ndarray, Y: np.ndarray) -> None:
        if X.shape != Y.shape or X.ndim != 2 or X.shape[1] != len(self.sx):
            raise ValueError("feature/target dimensionality mismatch")
        if not np.isfinite(X).all() or not np.isfinite(Y).all():
            raise ValueError("nonfinite VALUE-only features/targets")
        self.n += len(X)
        self.sx += X.sum(axis=0)
        self.sy += Y.sum(axis=0)
        self.xx += X.T @ X
        self.xy += X.T @ Y
        self.yy += float(np.einsum("ij,ij->", Y, Y))


def sum_moments(moments: Iterable[Moments], *, donor_uniform: bool) -> Moments:
    items = list(moments)
    if not items or any(m.n <= 0 for m in items):
        raise ValueError("cannot fit with zero donors/cells")
    width = len(items[0].sx)
    out = Moments.empty(width)
    for m in items:
        if len(m.sx) != width:
            raise ValueError("mixed molecular widths")
        scale = 1.0 / m.n if donor_uniform else 1.0
        out.n += m.n
        out.sx += scale * m.sx
        out.sy += scale * m.sy
        out.xx += scale * m.xx
        out.xy += scale * m.xy
        out.yy += scale * m.yy
    # For donor_uniform the mass of each donor is 1; for ordinary, its cells.
    return out


def fit_ridge(items: Iterable[Moments], *, ridge: float = RIDGE,
              donor_uniform: bool = True) -> tuple[np.ndarray, np.ndarray]:
    ms = list(items)
    if len(ms) < 2:
        raise ValueError("at least two TRAIN donors needed")
    if not (isinstance(ridge, (int, float)) and np.isfinite(ridge) and ridge > 0):
        raise ValueError("ridge must be finite and strictly positive")
    ag = sum_moments(ms, donor_uniform=donor_uniform)
    mass = float(len(ms) if donor_uniform else ag.n)
    mux, muy = ag.sx / mass, ag.sy / mass
    gram = ag.xx / mass - np.outer(mux, mux)
    cov = ag.xy / mass - np.outer(mux, muy)
    # Correct tiny negative numerical noise but never convert a materially
    # negative variance into a plausible training result.
    v = np.diag(gram)
    if np.any(v < -1e-8 * np.maximum(1., np.abs(np.diag(ag.xx / mass)))):
        raise ValueError("invalid negative train covariance diagonal")
    sd = np.maximum(np.sqrt(np.maximum(v, 0.)), 1e-12)
    g = gram / np.outer(sd, sd)
    c = cov / sd[:, None]
    standardized_B = np.linalg.solve(g + ridge * np.eye(len(mux)), c)
    B = standardized_B / sd[:, None]
    b = muy - mux @ B
    if not np.isfinite(B).all() or not np.isfinite(b).all():
        raise ValueError("nonfinite ridge solution")
    return B, b


def score_moments(test: Moments, B: np.ndarray, b: np.ndarray,
                  *, train_target_mean: np.ndarray) -> tuple[float, float]:
    """SSE vs ridge prediction; SST vs train-side mean (not leaked test mean)."""
    if test.n < 1:
        raise ValueError("empty held-out donor")
    sse = (test.yy - 2 * np.einsum("ij,ij->", B, test.xy)
           - 2 * b @ test.sy + np.einsum("ij,ij->", B, test.xx @ B)
           + 2 * b @ (test.sx @ B) + test.n * (b @ b))
    mu = np.asarray(train_target_mean)
    sst = test.yy - 2 * mu @ test.sy + test.n * (mu @ mu)
    tol = 1e-8 * max(test.yy, 1.0)
    if sse < -tol or sst < -tol:
        raise ValueError("material negative held-out quadratic score")
    return max(0., float(sse)), max(0., float(sst))


def train_target_mean(moments: list[Moments], donor_uniform: bool) -> np.ndarray:
    ag = sum_moments(moments, donor_uniform=donor_uniform)
    return ag.sy / (len(moments) if donor_uniform else ag.n)


def evaluate_donor_lodo(moments: dict[str, Moments], *, ridge: float = RIDGE,
                        donor_uniform: bool = True) -> dict[str, object]:
    if len(moments) < 3:
        raise ValueError("LODO requires three or more donors for independent train folds")
    results = []
    for donor in sorted(moments):
        train = [m for name, m in moments.items() if name != donor]
        B, b = fit_ridge(train, ridge=ridge, donor_uniform=donor_uniform)
        sse, sst = score_moments(moments[donor], B, b,
                                train_target_mean=train_target_mean(train, donor_uniform))
        if sst <= 1e-12:
            raise ValueError("held-out donor has no target variance against train mean")
        results.append({"donor": donor, "n_cells": moments[donor].n,
                        "sse": sse, "sst": sst, "r2": 1. - sse/sst})
    sse = sum(r["sse"] for r in results)
    sst = sum(r["sst"] for r in results)
    donor_macro_sse = sum(r["sse"]/r["n_cells"] for r in results)
    donor_macro_sst = sum(r["sst"]/r["n_cells"] for r in results)
    return {"n_donors": len(results), "n_cells": sum(r["n_cells"] for r in results),
            "cell_pooled_r2": 1. - sse/sst,
            "donor_uniform_r2": 1. - donor_macro_sse/donor_macro_sst,
            "donor_median_r2": float(np.median([r["r2"] for r in results])),
            "donor_min_r2": min(r["r2"] for r in results),
            "frac_donors_positive": sum(r["r2"] > 0 for r in results)/len(results),
            "per_donor": results}


def gather_moments(V0: np.ndarray, V1: np.ndarray, cell_donor: np.ndarray,
                   donor_ids: np.ndarray, *, chunk_rows: int) -> dict[str, Moments]:
    if V0.shape != V1.shape or len(V0) != len(cell_donor):
        raise ValueError("view/donor row shape mismatch")
    if V0.ndim != 2 or V0.shape[1] < WIDTH:
        raise ValueError("source view width insufficient")
    if chunk_rows < 1:
        raise ValueError("chunk_rows must be positive")
    if len(set(map(str, donor_ids))) != len(donor_ids):
        raise ValueError("duplicate donor IDs")
    out = {str(d): Moments.empty(WIDTH) for d in donor_ids}
    # Crucial: the first 256 columns alone. Visibility columns are QC-bearing.
    for start in range(0, len(cell_donor), chunk_rows):
        stop = min(len(cell_donor), start + chunk_rows)
        dchunk = cell_donor[start:stop]
        for code in np.unique(dchunk):
            idx = np.flatnonzero(dchunk == code)
            x = np.asarray(V0[start:stop, :WIDTH][idx], np.float64)
            y = np.asarray(V1[start:stop, :WIDTH][idx], np.float64)
            out[str(donor_ids[int(code)])].add_block(x, y)
    return out


def verify_binding_receipt(path: Path, expected_sha256: str) -> dict[str, object]:
    """External independently reviewed whole-file hash is mandatory.

    A user-supplied unsigned JSON alone is NOT evidence of physical validation.
    The receipt's exact SHA must be fixed outside this result and independently
    reviewed before invoking this script. This does not re-run its raw-block audit.
    """
    if len(expected_sha256) != 64 or any(c not in '0123456789abcdef' for c in expected_sha256):
        raise ValueError("missing independently pinned 64-character receipt SHA")
    require_exact_file(path, expected_sha256)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V5_FULL104_PASS1_PHYSICAL_BINDING_RECEIPT_V1":
        raise ValueError("not a physical pass1-to-Level4 receipt")
    if (payload.get("pass1_npz_sha256") != FROZEN_PASS1_SHA256
        or payload.get("block_count") != 8915
        or payload.get("row_count") != EXPECTED_ROWS
        or payload.get("donor_count") != EXPECTED_DONORS
        or payload.get("protected_outcomes_authorized") is not False
        or payload.get("training_authorized") is not False):
        raise ValueError("physical pass1 binding receipt scope mismatch")
    return payload


def run(*, pass1: Path, v0: Path, v1: Path, physical_receipt: Path,
        physical_receipt_sha: str, out: Path, chunk_rows: int = 4096) -> dict[str, object]:
    if out.exists():
        raise ValueError("output already exists; use a fresh immutable result path")
    binding = verify_binding_receipt(physical_receipt, physical_receipt_sha)
    for path, digest in ((pass1, FROZEN_PASS1_SHA256), (v0, V0_SHA256), (v1, V1_SHA256)):
        require_exact_file(path, digest)
    with np.load(pass1, allow_pickle=False) as p:
        required = {'cell_donor', 'duniq', 'donor_src'}
        if not required.issubset(p.files):
            raise ValueError('frozen pass1 missing exact donor/source arrays')
        codes = np.asarray(p['cell_donor'])
        ids = np.asarray(p['duniq']).astype(str)
        sources = np.asarray(p['donor_src'])
    if (codes.shape != (EXPECTED_ROWS,) or ids.shape != (EXPECTED_DONORS,)
        or sources.shape != (EXPECTED_DONORS,)
        or codes.dtype.kind not in 'iu' or sources.dtype.kind not in 'iu'
        or np.any(codes < 0) or np.any(codes >= EXPECTED_DONORS)
        or np.any(sources < 0) or np.any(sources >= len(SOURCE_NAMES))):
        raise ValueError('pass1 donor/source shape, type or code invalid')
    counts = np.bincount(codes.astype(np.int64), minlength=EXPECTED_DONORS)
    if (len(set(ids)) != EXPECTED_DONORS or np.any(counts <= 0)
        or {name: int(np.sum(sources == i)) for i, name in enumerate(SOURCE_NAMES)} != EXPECTED_SOURCE_COUNTS):
        raise ValueError('pass1 donor roster or source composition invalid')
    X = np.load(v0, mmap_mode='r', allow_pickle=False)
    Y = np.load(v1, mmap_mode='r', allow_pickle=False)
    if X.shape != EXPECTED_SHAPE or Y.shape != EXPECTED_SHAPE or X.dtype != np.float32 or Y.dtype != np.float32:
        raise ValueError('VIEW arrays are not exact current FULL104 512-column float32')
    # Binding receipt plus exact view hashes enforce selection_row agreement with
    # authenticated FULL104 assembly. Caller must independently attest the
    # assembled-view row-order lineage; raw pass1 receipt alone does not prove it.
    mom = gather_moments(X, Y, codes, ids, chunk_rows=chunk_rows)
    results = {}
    for si, name in enumerate(SOURCE_NAMES):
        roster = {str(ids[d]): mom[str(ids[d])] for d in range(EXPECTED_DONORS)
                  if int(sources[d]) == si}
        results[name] = evaluate_donor_lodo(roster)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], check=False,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True).stdout.strip()
    receipt = {
        'executing_script_sha256': sha256_file(Path(__file__)),
        'executing_git_head': commit if len(commit) == 40 else 'NOT_AVAILABLE',
        'python_version': platform.python_version(),
        'numpy_version': np.__version__,
        'schema': 'V26_NEW_104_READER_FIT_VALUE_ONLY_RIDGE_LODO_V1',
        'status': 'NEW_DEVELOPMENT_BASELINE_NOT_HISTORICAL_REPLAY',
        'pass1_sha256': FROZEN_PASS1_SHA256, 'v0_sha256': V0_SHA256,
        'v1_sha256': V1_SHA256,
        'physical_pass1_binding_receipt_sha256': physical_receipt_sha,
        'physical_pass1_binding_scope': binding['schema'],
        'population': 'FULL104_READER_FIT_104', 'n_donors': EXPECTED_DONORS,
        'n_cells': EXPECTED_ROWS, 'molecular_value_width': WIDTH,
        'prediction_target': 'same-cell view1 VALUE_ONLY_256',
        'weighting': 'equal donor train mass within each source',
        'metric': 'source-specific held-out donor-uniform and cell-pooled R2 against train target mean',
        'ridge_lambda_mean_scaled': RIDGE,
        'operator_centering': 'NOT_PERFORMED_OPERATOR_VECTOR_NOT_IN_PASS1',
        'note': 'NOT DIRECTLY COMPARABLE TO HISTORICAL 94-DONOR OPERATOR-CENTRED R2',
        'view_selection_row_lineage': 'MUST_BE_INDEPENDENTLY_ATTESTED_BEFORE_SCIENTIFIC_PROMOTION',
        'training_authorized': False, 'protected_outcomes_opened': False,
        'results_by_source': results,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    return receipt


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('pass1','v0','v1','physical-receipt','physical-receipt-sha','out'):
        p.add_argument('--'+flag, required=True)
    p.add_argument('--chunk-rows', type=int, default=4096)
    a = p.parse_args()
    res = run(pass1=Path(a.pass1), v0=Path(a.v0), v1=Path(a.v1),
              physical_receipt=Path(a.physical_receipt),
              physical_receipt_sha=a.physical_receipt_sha,
              out=Path(a.out), chunk_rows=a.chunk_rows)
    print(json.dumps({'status': res['status'], 'output':a.out,
                      'sources':list(res['results_by_source'])}))


if __name__ == '__main__':
    main()