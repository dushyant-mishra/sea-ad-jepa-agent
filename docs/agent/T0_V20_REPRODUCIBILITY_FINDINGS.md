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

## 4. Q_DEPTH against Q_DETECT — diagnostic only

Requested as a diagnostic, and reported as one. Nothing here changes the T0 V20
design, thresholds, nuisance columns, adjudication rule or result.

The two QC metrics enter T0 as a single reduced model — `measurements` is one
fit with both appended at once, named `Q_DEPTH+Q_DETECT` — so how much
independent information they carry decides how much purchase that sensitivity
actually has on measurement confounding.

Computed on the 28 discovery donors from the frozen scalar matrix (35,076
addresses). Pathology-blind: no AT8 value is read, since both metrics are
properties of the expression data alone.

| quantity | value |
| --- | --- |
| Pearson r | **0.9232** (r² = 0.8523) |
| Spearman r | 0.9146 |
| Q_DEPTH | mean 8.6062, sd 0.2279 |
| Q_DETECT | mean 0.0760, sd 0.0107 |
| condition number, frozen nuisance `[1, age_c, age_c², sex]` | 310.6 |
| condition number, nuisance + both QC columns | **37,671** |
| Q_DEPTH variance left after nuisance alone | 0.686 |
| Q_DETECT variance left after nuisance alone | 0.755 |
| Q_DEPTH variance left after nuisance **and Q_DETECT** | **0.087** |
| Q_DETECT variance left after nuisance **and Q_DEPTH** | **0.096** |

### Reading

The two are strongly associated but not redundant. The last two rows are the
ones that matter: each metric retains only about nine percent of its variance
once the other and the frozen nuisance columns are projected out. So the pair
does add a real second dimension, but a thin one — the `Q_DEPTH+Q_DETECT`
sensitivity is close to a single depth-of-sequencing adjustment wearing two
columns, and appending both multiplies the design's condition number by about
121.

This is expected from what they measure. Depth is log library size; detection is
the fraction of the address space seen at all, and deeper libraries detect more
addresses, with the relation flattening as detection rises. At a mean detection
of 0.076 the pair is far from that saturation, which is why nine percent
survives rather than nothing.

### What follows, and what does not

It does not follow that the sensitivity was uninformative or that the T0
terminal should be re-read. The sensitivity is a directional test at α = 0.05
and it is unaffected by the columns being correlated; collinearity inflates
standard errors, which makes such a test harder to pass, not easier.

What does follow is a design note for any successor: two nearly-parallel columns
buy one direction of protection at the cost of a much worse-conditioned design.
A successor that wants genuine measurement-confounding coverage should choose
metrics that are close to orthogonal after the nuisance design, and should
derive that choice from the data before freezing — not adopt this pair because
T0 used it.

Record: `outputs/t0_qc_diagnostic_20260909/T0_QC_METRIC_DIAGNOSTIC.json`.

## 5. The block store is now identified, and the missing-path gap bit

Finding 2 said the T0 summaries bind every input by digest and record no path.
Running the V2 replay produced a concrete instance of what that costs.

The store argument I reconstructed for the V1 run was
`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level0`.
It is the wrong store. The V1 replay never revealed that, because it stopped at
step 4 on the equivalence policy and the store is not read until step 5.

Once V2 passed step 4, the frozen population authority rejected it immediately:

```
STOP_T0_B2_BLOCK_MANIFEST_DIGEST_MISMATCH
  block manifest is 2928167527609a5e...  expected 66f589e56badb148...
```

The correct store is **`expression_level4`**, not `expression_level0`. Verified
against the two digests the authority pins, both of which now match exactly:

| authority | value |
| --- | --- |
| `PHASE2_EXPRESSION_BLOCK_MANIFEST.csv` | `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29` |
| membership (`MEMBERSHIP_SHA`) | `d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529` |
| op31 count blocks present | 1,247 |

Two things worth taking from this.

The fail-closed design worked exactly as intended. A wrong store did not produce
a plausible-looking confirmation matrix from the wrong expression level; it
produced a refusal naming the digest that disagreed. That is the difference
between an authority and a comment.

And it is the missing-path gap, not bad luck. Nothing in any T0 record said
which expression level the run read, so the store had to be guessed from a
directory listing, and the guess survived undetected through an entire replay
because the first four steps do not touch it. Recording the resolved input paths
alongside their digests — which costs nothing — would have made this a
non-event.

Resolved inputs for the T0 V20 Stage 3 replay, for whoever runs it next:

| argument | path |
| --- | --- |
| `--store` | `D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4` |
| `--pathology-source` | `D:/Jepa project/data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv` (`ebbe9bc0…`) |
| `--membership` | `configs/v4/t0_v20_frozen_authority/T0_PRIMARY_MTG_READER_FIT_IMMUNE_CELL_MEMBERSHIP_V1.csv` (`d4714998…`) |
| `--feature-split` | `configs/v4/t0_v20_frozen_authority/T0_MTG_FEATURE_ROLE_SPLIT_V2.csv` (`29116c16…`) |
