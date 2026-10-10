#!/usr/bin/env python3
"""GPU (PyTorch CUDA) backend for the D1 Bayesian-bootstrap draws of v79_geometry.geometry.

Same statistics, same definitions; only the three heavy dense operations move to the GPU:
  - weighted correlation (float64, the CPU formula step by step, including the constant-column rule and the
    builders' 1e-9 guard);
  - transitivity's triangle count trace(A^3) = sum((A @ A) * A^T): A is 0/1, so A @ A holds integers at most
    the gene count and is exact in float32 with TF32 disabled; the final sum is taken in float64 (exact);
  - eigenvalues (float64).
Every thresholded count is an exact integer from the same comparisons. Medians use numpy's linear rule
(np.quantile's _lerp) on the two middle order statistics. Communities (connected components), abundance and
depth stay on the CPU path. Equivalence with the CPU path is tested (integer statistics identical, continuous
within 1e-9 relative); the full-data point of D1 is always computed on the CPU path.
"""
from __future__ import annotations

import numpy as np
import torch

import v79_geometry as GE

TC = GE.TC
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False


def device() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available; use the CPU path")
    return torch.device("cuda")


def to_gpu(prep: dict) -> dict:
    dev = device()
    return dict(Ld=torch.as_tensor(prep["Ld_sel"], dtype=torch.float64, device=dev),
                D=torch.as_tensor(prep["D_sel"], dtype=torch.float64, device=dev))


def corr(H: torch.Tensor, w: np.ndarray) -> torch.Tensor:
    """GE.weighted_corr on the GPU, step for step."""
    w = GE.check_weights(w, H.shape[0])
    wt = torch.as_tensor(w, dtype=torch.float64, device=H.device)
    Hc = H - wt @ H
    Hs = H if (w > 0).all() else H[torch.as_tensor(w > 0, device=H.device)]
    const = Hs.amax(0) == Hs.amin(0)
    Hc[:, const] = 0.0
    sd = torch.sqrt(wt @ (Hc * Hc))
    Zs = torch.sqrt(wt)[:, None] * (Hc / (sd + GE.STD_EPS))
    return Zs.T @ Zs


def _median_sorted_pair(lo: float, hi: float) -> float:
    """np.quantile(x, 0.5) for an even count: numpy's _lerp at t = 0.5 uses b - (b - a) * (1 - t)."""
    return float(hi - (hi - lo) * 0.5)


def median_abs_offdiag(C: torch.Tensor) -> float:
    n = C.shape[0]
    a = C.abs()[~torch.eye(n, dtype=torch.bool, device=C.device)]
    m = a.numel()
    if m % 2:
        return float(torch.kthvalue(a, (m + 1) // 2).values)
    lo = float(torch.kthvalue(a, m // 2).values)
    hi = float(torch.kthvalue(a, m // 2 + 1).values)
    return _median_sorted_pair(lo, hi)


def topology(C: torch.Tensor, thr: float = TC.CORR_THRESHOLD):
    """TC.topology: degrees and transitivity of |C| > thr without the diagonal."""
    A = C.abs() > thr
    A.fill_diagonal_(False)
    deg = A.sum(1).to(torch.float64)
    Af = A.to(torch.float32)
    tri = float(((Af @ Af).to(torch.float64) * Af.T.to(torch.float64)).sum()) / 6.0
    triples = float((deg * torch.clamp(deg - 1, min=0) / 2.0).sum())
    trans = (3.0 * tri / triples) if triples > 0 else float("nan")
    return deg, trans


def layer_stats(C: torch.Tensor) -> dict:
    """GE.layer_stats_from_corr with the heavy parts on the GPU."""
    nh = C.shape[0]
    thr = TC.CORR_THRESHOLD
    eye = torch.eye(nh, dtype=torch.bool, device=C.device)
    off = C[~eye]
    a = off.abs()
    deg, trans = topology(C)
    Acomm = (C.abs() > TC.COMMUNITY_THRESHOLD).to(torch.int8).cpu().numpy()
    from scipy import sparse
    _, lab = sparse.csgraph.connected_components(sparse.csr_matrix(Acomm), directed=False)
    sizes = np.bincount(lab)
    Ca = C.abs().masked_fill(eye, 0.0)
    best = Ca.amax(1)
    ev = torch.linalg.eigvalsh(C).flip(0)
    tot = float(ev.sum())
    n_off = off.numel()
    pos = float(int((off > thr).sum())) / n_off
    neg = float(int((off < -thr).sum())) / n_off
    return dict(
        median_abs_corr=median_abs_offdiag(C),
        frac_abs_gt_0p3=float(int((a > thr).sum())) / n_off,
        var_top10_pc=float(ev[:10].sum()) / tot,
        mean_degree=float(int(deg.sum())) / nh,          # exact integer sum / n, as numpy's mean of int degrees
        largest_community_frac=float(np.max(sizes) / nh),
        transitivity=float(trans),
        substitute_frac=float(int((best > TC.SUBSTITUTE_THRESHOLD).sum())) / nh,
        frac_pos_gt_0p3=pos,
        frac_neg_lt_m0p3=neg,
        pos_over_neg_ratio=float(pos / max(neg, 1e-9)),
        mean_signed_corr=float(off.mean()))


def t5(H: torch.Tensor, w: np.ndarray, raw_cls, C: torch.Tensor, min_cells: int = TC.MIN_CLASS_CELLS) -> dict:
    """GE.weighted_t5 with class correlations and topology on the GPU."""
    raw_cls = np.asarray(raw_cls)
    uc, cc = np.unique(raw_cls, return_counts=True)
    per_class = {}
    for c in [c for c, k in zip(uc, cc) if k >= min_cells]:
        m = raw_cls == c
        mass = float(w[m].sum())
        if not mass > 0:
            raise ValueError(f"class {c!r} has no weight")
        idx = torch.as_tensor(np.where(m)[0], device=H.device)
        Cc = corr(H.index_select(0, idx), w[m] / mass)
        n = Cc.shape[0]
        offc = Cc[~torch.eye(n, dtype=torch.bool, device=Cc.device)]
        degc, transc = topology(Cc)
        per_class[str(c)] = dict(
            n_cells=int(m.sum()), class_mass=mass, median_abs_corr=median_abs_offdiag(Cc),
            fraction_gt_0p3=float(int((offc.abs() > TC.CORR_THRESHOLD).sum())) / offc.numel(),
            mean_degree=float(int(degc.sum())) / n, transitivity=float(transc))
        del Cc, offc
    pooled = median_abs_offdiag(C)
    within = float(np.mean([v["median_abs_corr"] for v in per_class.values()])) if per_class else float("nan")
    return dict(classes_used=list(per_class), per_class=per_class,
                pooled_median_abs_corr=pooled, mean_within_class_median_abs_corr=within,
                within_over_pooled_ratio=float(within / pooled) if pooled > 0 else float("nan"))


def geometry(prep: dict, gprep: dict, w) -> dict:
    """GE.geometry with the dense work on the GPU (same keys, same definitions)."""
    w = GE.check_weights(w, prep["n_cells"])
    C_expr = corr(gprep["Ld"], w)
    expression = layer_stats(C_expr)
    t5r = t5(gprep["Ld"], w, prep["raw_cls"], C_expr)
    del C_expr
    C_det = corr(gprep["D"], w)
    detection = layer_stats(C_det)
    del C_det
    return dict(expression_cp10k_log1p=expression, detection_binary=detection, t5_class_conditional=t5r,
                abundance=GE.weighted_abundance(prep["counts_universe"], w), depth=GE.weighted_depth(prep, w))
