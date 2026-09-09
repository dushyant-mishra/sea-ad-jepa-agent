# T0 V20 reproducibility: what closing the provenance actually found

Three findings, in increasing order of consequence. The first two are fixed in
this branch. The third is not fixed and needs a decision.

## 1. The computation lived only in a session scratchpad

Every frozen V20 module — including `t0_adjudicator_v2`, which produced the
decision — was resolved at runtime through a hardcoded absolute path into
`.../Temp/claude/d--Jepa-project/<session-id>/scratchpad/v20_recovery/current/code`.
So did the input authorities: the feature-role split and the primary membership.

The evidence bytes were fully committed and byte-verified, but the code and the
inputs behind them were one temp cleanup from being unrecoverable, and no clean
clone could run them. **Fixed**: 79 files published and verified twice against
the recovery package's own manifest, with a standing seven-test suite.

## 2. The runs record digests but no paths and no environment

Every T0 summary binds its inputs by SHA-256 and records neither the path nor
the invocation. Reconstructing what Stage 3 was actually run against meant
matching digests back to files by hand — the pathology source turned out to be
`data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv` (`ebbe9bc0…`)
and the feature split `29116c16…`. No summary records the Python, NumPy, SciPy
or BLAS the run used either, which matters for the third finding.

Digest binding is the right primitive and should stay. Recording the path and
the numeric stack alongside it costs nothing and removes the guesswork.

## 3. T0 is verified by bit-exact float equality, and does not replay here

This is the one that needs a decision.

`verify_target_v2_against_raw` compares the recomputed discovery target to the
frozen one with `np.array_equal` on float arrays — bit-exact equality. Replaying
frozen Stage 3 on this machine fails there:

```
ValueError: frozen target beta mismatch canonical recomputation
```

**This is not a scientific failure.** Measured on identical inputs — `provenance`
is compared before `beta` and matches, so the raw discovery matrix, donor set and
feature split are provably the same bytes:

| quantity | frozen vs recomputed |
| --- | --- |
| `beta` | max abs 5.9e-21, max rel **2.8e-12**, 22286/28061 differ |
| `sigma` | max abs 2.2e-16, max rel **8.2e-16** (machine epsilon) |
| `cv_mse_by_multiplier` | max rel **2.6e-15**, all 17 differ |
| `final_lambda` | 2360764.285714286 vs 2360764.2857142864 — one ulp |
| `response_residual_sd` | 1.2245513389820333 vs …335 — one ulp |
| `mu` | **identical** |
| `decision_gene_mask` | **identical** |
| `selected_multiplier_index` / `exponent` | **16 / 2.0 — identical** |
| `discovery_age_center` | **identical** |
| `canonical_donor_order` | **identical** |

Every quantity that any decision depends on is identical. The ridge grid still
selects exponent 2.0, the decision gene set is the same set, the donor order is
the same order. What differs is the last bit of floating-point accumulation,
which is what changing a BLAS or a NumPy version does.

Environments available here: NumPy 2.4.6 raises the clean mismatch above; NumPy
1.26.4 dies at the same step with no traceback (exit 127); NumPy 1.24.2 is the
only other full stack. None reproduces the frozen bytes, and nothing recorded
which stack did.

### Why this matters

The T0 result is sound and its evidence is committed. But "reproduce T0 from a
clean clone" is currently unachievable by anyone whose numeric stack differs in
the last ulp from an unrecorded original — which is essentially everyone. A
verifier that demands bit-exactness on float arrays does not certify the science;
it certifies the arithmetic environment, and it fails closed on a difference of
5.9e-21.

### What it blocks

The missing state sensitivity statistics cannot be recovered by replaying frozen
Stage 3, because the replay stops at this gate before reaching the adjudicator.
The repair that surfaces them is written, tested and committed
(`t0_sensitivity_recovery_v1`); it is the replay underneath it that cannot
complete.

### The decision needed

Recovering the sensitivities requires accepting a reproduction check at
floating-point tolerance rather than bit-exact equality — the recomputed
`state_primary` agreeing to roughly 1e-12 relative and both terminals matching
exactly, instead of every float matching bit for bit. That is a change to what
counts as a verified replay in this lane, so it is not mine to make quietly.

The alternative is to locate or rebuild the exact original numeric stack. That
is worth doing regardless, and recording it in every future summary is the
durable fix.
