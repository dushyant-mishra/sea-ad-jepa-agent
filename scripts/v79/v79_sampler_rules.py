#!/usr/bin/env python3
"""The contract's sampler rules in one place, used by every fitting runner (recovery, real phases, held-out
PPC, Phase C). JAX-free so CI tests every branch.

  diagnostics   every checked site: rank-normalized split R-hat <= 1.01, bulk and tail ESS >= 400, and zero
                divergences (contract diagnostics section; thresholds unchanged)
  retry         any divergence: refit at target_accept 0.95, then 0.99 (contract inference.retry)
  extension     (amendment A5, before any real data) no divergence but R-hat or ESS missed: continue the same
                chains once for the same number of draws, with no new warm-up, and diagnose all draws. The
                maximum R-hat over several hundred per-gene sites fluctuates near 1.01 at ESS ~1,000 even when
                chains mix (about 1 + c / ESS-per-chain); more draws shrink that noise without moving a threshold.
                Divergences in the extension count. Applied once; a fit still failing is NOT_DIAGNOSED.
"""
from __future__ import annotations

RHAT_MAX, ESS_MIN = 1.01, 400
RETRY_ACCEPT = (0.9, 0.95, 0.99)


def converged(run: dict, diag: dict) -> bool:
    return sum(run["divergences"]) == 0 and diag["worst_rhat"] <= RHAT_MAX and diag["worst_ess"] >= ESS_MIN


def fit_with_rules(run, diagnose, accepts=RETRY_ACCEPT):
    """run(target_accept, extend_from) -> run record (divergences, seconds, mean_steps, ...);
    diagnose(run) -> dict with worst_rhat and worst_ess. Returns (final run, its diagnosis, attempts)."""
    attempts, r, d = [], None, None
    for ta in accepts:
        r = run(ta, None)
        d = diagnose(r)
        attempts.append(_attempt(ta, r, d, extended=False))
        if sum(r["divergences"]) > 0:
            continue                                   # retry rule: escalate target_accept
        if not attempts[-1]["diagnosed"]:
            r = run(ta, r)                             # A5: extend the same chains once
            d = diagnose(r)
            attempts.append(_attempt(ta, r, d, extended=True))
        break
    return r, d, attempts


def _attempt(ta, r, d, extended):
    return dict(target_accept=ta, extended=extended, seconds=r["seconds"], divergences=list(r["divergences"]),
                mean_steps=r.get("mean_steps"), draws_per_chain=r.get("draws_per_chain"),
                worst_rhat=d["worst_rhat"], worst_ess=d["worst_ess"], diagnosed=converged(r, d))
