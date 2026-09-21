"""Audit F -- target identity vs context vs quantitative state, stratified by target zero.

The question
------------
At `core_measured_zero_frequency = 0.8329826626244999`, roughly five out of six
(cell, core address) pairs are measured zeros. When the JEPA is asked to predict
a masked target on such a cell, what can its target representation possibly be
carrying?

Three candidate contributions:

``IDENTITY``      which address is being asked about, independent of the cell
``CONTEXT``       the cell's own state, independent of which address is asked
``QUANTITATIVE``  the target's actual expression level, beyond its detection state

On a target-zero cell the quantitative value is constant by construction, so
QUANTITATIVE cannot contribute there at all. The scientifically live question is
narrower and sharper:

    of the variance in the target representation, how much is IDENTITY +
    CONTEXT -- available without knowing anything target-specific -- versus
    DETECTION (is it on or off) versus QUANTITATIVE (how much, given it is on)?

If IDENTITY + CONTEXT dominates, then for most (cell, address) pairs the
"target representation" is close to a lookup keyed by address and cell state,
and a model can score well on it without learning target-specific biology.

The decomposition
-----------------
For a representation ``T(cell, address)`` the audit fits nested models and
reports incremental variance explained:

    M0: T ~ address identity                       -> R2_identity
    M1: T ~ address identity + context             -> R2_identity_context
    M2: M1 + binary detection state of the target  -> R2_plus_detection
    M3: M2 + quantitative value among detected     -> R2_plus_quantitative

    share_identity    = R2_identity
    share_context     = R2_identity_context - R2_identity
    share_detection   = R2_plus_detection    - R2_identity_context
    share_quantitative= R2_plus_quantitative - R2_plus_detection

Everything is reported stratified by ``target observed zero`` and ``target
observed nonzero``, because the two strata answer different questions and
pooling them hides exactly the effect of interest.

Status of the input
-------------------
**No lawful current teacher representation is available.** Producing one would
require training or protected outcomes, both of which are out of scope. So this
module ships the decomposition and its controls, validated on synthetic
representations with known composition, and the real measurement is marked

    CHANGED_INPUT_REQUIRES_REAL_TEACHER_REQUALIFICATION

The point of committing it now is to make the test unavoidable once a real
teacher exists, rather than negotiable after the fact.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

SCHEMA = "V5_FULL104_TARGET_IDENTITY_ZERO_DECOMPOSITION_V1"
STATUS_NO_TEACHER = "CHANGED_INPUT_REQUIRES_REAL_TEACHER_REQUALIFICATION"
_EPS = 1e-12

#: Authoritative corrected census value. Fixtures reproduce this sparsity so the
#: decomposition is exercised at the geometry it will actually face.
CORE_MEASURED_ZERO_FREQUENCY = 0.8329826626244999


def _r2(y: np.ndarray, design: np.ndarray) -> float:
    """Variance of y explained by an ordinary least-squares fit on `design`.

    Uses lstsq, which is rank-revealing, so collinear or rank-deficient designs
    (an unavoidable consequence of one-hot identity blocks) do not silently
    inflate the fit.
    """
    y = np.asarray(y, dtype=np.float64)
    total = float(((y - y.mean()) ** 2).sum())
    if total <= _EPS:
        return 0.0
    if design.shape[1] == 0:
        return 0.0
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ coef
    return float(1.0 - (resid @ resid) / total)


def _onehot(codes: np.ndarray) -> np.ndarray:
    uniq = np.unique(codes)
    out = np.zeros((codes.size, uniq.size), dtype=np.float64)
    out[np.arange(codes.size), np.searchsorted(uniq, codes)] = 1.0
    return out


def decompose(
    *,
    representation: np.ndarray,
    address_code: np.ndarray,
    context: np.ndarray,
    target_value: np.ndarray,
) -> dict:
    """Nested-model variance decomposition of a target representation.

    Shares are incremental and ordered identity -> context -> detection ->
    quantitative. Ordering matters and is declared here rather than chosen after
    seeing results: identity is the cheapest explanation and quantitative the
    most demanding, so the ordering is deliberately conservative about crediting
    target-specific information.
    """
    y = np.asarray(representation, dtype=np.float64)
    detected = (np.asarray(target_value) > 0).astype(np.float64)

    ident = _onehot(np.asarray(address_code))
    ctx = np.asarray(context, dtype=np.float64)
    if ctx.ndim == 1:
        ctx = ctx[:, None]

    d_ident = ident
    d_ctx = np.hstack([ident, ctx])
    d_det = np.hstack([ident, ctx, detected[:, None]])
    # Quantitative enters only where the target is detected; elsewhere it is
    # identically zero and would merely duplicate the detection column.
    quant = np.asarray(target_value, dtype=np.float64) * detected
    d_quant = np.hstack([ident, ctx, detected[:, None], quant[:, None]])

    r_ident = _r2(y, d_ident)
    r_ctx = _r2(y, d_ctx)
    r_det = _r2(y, d_det)
    r_quant = _r2(y, d_quant)

    return {
        "n": int(y.size),
        "r2_identity": r_ident,
        "r2_identity_context": r_ctx,
        "r2_plus_detection": r_det,
        "r2_plus_quantitative": r_quant,
        # Incremental shares, clipped at zero: lstsq on a rank-deficient design
        # can return a fractionally smaller R2 for a strictly larger model.
        "share_identity": max(r_ident, 0.0),
        "share_context": max(r_ctx - r_ident, 0.0),
        "share_detection": max(r_det - r_ctx, 0.0),
        "share_quantitative": max(r_quant - r_det, 0.0),
    }


def decompose_stratified(
    *,
    representation: np.ndarray,
    address_code: np.ndarray,
    context: np.ndarray,
    target_value: np.ndarray,
) -> dict:
    """Pooled plus the two strata that the pooled number would otherwise hide."""
    value = np.asarray(target_value)
    zero = value <= 0
    out = {
        "pooled": decompose(representation=representation, address_code=address_code,
                            context=context, target_value=target_value),
        "observed_zero_fraction": float(zero.mean()),
    }
    for name, sel in (("target_observed_zero", zero), ("target_observed_nonzero", ~zero)):
        if sel.sum() < 10 or np.unique(np.asarray(address_code)[sel]).size < 2:
            out[name] = {"state": "NOT_MEASURABLE",
                         "reason": f"stratum has {int(sel.sum())} rows / "
                                   f"{int(np.unique(np.asarray(address_code)[sel]).size)} addresses"}
            continue
        ctx = np.asarray(context, dtype=np.float64)
        ctx = ctx[sel] if ctx.ndim > 1 else ctx[sel][:, None]
        out[name] = decompose(
            representation=np.asarray(representation)[sel],
            address_code=np.asarray(address_code)[sel],
            context=ctx,
            target_value=value[sel],
        )
    return out


# --------------------------------------------------------------------------- #
# Synthetic representations with KNOWN composition, at the real sparsity.
# --------------------------------------------------------------------------- #

def make_fixture(kind: str, *, n_cells: int = 1500, n_addresses: int = 12,
                 seed: int = 20260920) -> dict:
    rng = np.random.default_rng(seed)
    n = n_cells * n_addresses
    address_code = np.tile(np.arange(n_addresses), n_cells)
    cell_code = np.repeat(np.arange(n_cells), n_addresses)

    context = rng.normal(size=(n_cells, 3))[cell_code]

    detected = rng.random(n) > CORE_MEASURED_ZERO_FREQUENCY
    value = np.zeros(n)
    value[detected] = rng.gamma(2.0, 1.5, size=int(detected.sum()))

    addr_effect = rng.normal(size=n_addresses)[address_code]
    ctx_effect = context @ rng.normal(size=3)
    noise = 0.05 * rng.normal(size=n)

    if kind == "identity_only":
        rep = addr_effect + noise
    elif kind == "identity_plus_context":
        rep = addr_effect + ctx_effect + noise
    elif kind == "detection_only":
        rep = addr_effect + 2.0 * detected + noise
    elif kind == "quantitative":
        rep = addr_effect + 1.5 * value + noise
    elif kind == "identity_context_detection_quantitative":
        rep = addr_effect + ctx_effect + 1.0 * detected + 0.8 * value + noise
    elif kind == "pure_noise":
        rep = noise
    else:
        raise ValueError(f"unknown fixture kind {kind!r}")

    return {"kind": kind, "representation": rep, "address_code": address_code,
            "context": context, "target_value": value,
            "observed_zero_fraction": float((value <= 0).mean())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    kinds = ("pure_noise", "identity_only", "identity_plus_context", "detection_only",
             "quantitative", "identity_context_detection_quantitative")
    results = {}
    for kind in kinds:
        fx = make_fixture(kind)
        results[kind] = decompose_stratified(
            representation=fx["representation"], address_code=fx["address_code"],
            context=fx["context"], target_value=fx["target_value"])

    payload = {
        "schema": SCHEMA,
        "real_measurement_status": STATUS_NO_TEACHER,
        "real_measurement_reason":
            "No lawful current teacher representation exists. Producing one requires training "
            "or protected outcomes, both out of scope. The decomposition and its controls are "
            "committed so the measurement is unavoidable once a real teacher exists.",
        "core_measured_zero_frequency_used_in_fixtures": CORE_MEASURED_ZERO_FREQUENCY,
        "decomposition_order": ["identity", "context", "detection", "quantitative"],
        "decomposition_order_rationale":
            "Declared before results. Identity is the cheapest explanation and quantitative the "
            "most demanding, so incremental crediting is deliberately conservative about "
            "attributing variance to target-specific information.",
        "fixture_results": results,
        "biological_claim": "NONE",
        "training_authorized": False,
    }
    (args.out_dir / "TARGET_IDENTITY_ZERO_DECOMPOSITION_FIXTURES.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for kind, res in results.items():
        p = res["pooled"]
        print(f"{kind:46s} identity={p['share_identity']:.4f} context={p['share_context']:.4f} "
              f"detection={p['share_detection']:.4f} quant={p['share_quantitative']:.4f}")
    print("\nreal measurement:", STATUS_NO_TEACHER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
