# GSE301119 matched-NT negative control — result

**Verdict: the negative control failed, and it failed hard.** The descriptive
log2(CPM+1) donor-aware effects for GSE301119 cannot presently be distinguished
from an artifact of comparing a ~50-cell pseudobulk unit against a ~1,425-cell
non-targeting pool. Caught before any predictor, any benchmark use and any
training run.

## Provenance

Executed from a clean worktree at committed head `5260e70ce3c3`
(PR #125, `review/gse301119-matched-nt-null-20260925`); PR #121 head `aaf561cf`
verified as an ancestor. `git status` empty at execution.

```
producer   analysis/therapeutic_perturbation_etl/scripts/gse301119_matched_nt_null_v1.py
           sha256 c2c0ea387ef5b382595ba1b828b6af440724421f1501dc481a45e66f816da5f9
           (identical to the script_sha256 the receipt recorded for itself)

input      D:/jepa_perturb_outputs_20260923/gse301119_neutral_export
           CRISPRi source RDS e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549
           CRISPRa source RDS 9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90
           both match the frozen EXPECTED_RDS constants inside the producer

output     D:/jepa_perturb_outputs_20260923/gse301119_matched_nt_null_v1_twoarm/
           GSE301119_MATCHED_NT_DESCRIPTIVE_NULL_V1.json
           6,663,852 bytes
           sha256 4155670bf29784807e5376b691ff69698054d250800a4a13a87755be90119e85

wall clock 10m07s   exit 0   synthetic suite 16/16 passed on this machine
```

**A superseded earlier run exists and must not be cited.** An execution of the
*single-arm* protocol at the older head `6cd4424b` produced a 4,149,646-byte
receipt (sha256 `5ff0e7b7dd2c9bbd12ad312010654194b649e58430d1e7dbb7130d7e45d66f29`)
in `gse301119_matched_nt_null_v1/`. It predates the depth-only arm and answers a
different question. Every number below comes from the two-arm receipt only.

## What was run

Two independent negative-control arms, both predeclared before execution:

1. **Cell-sampling / composition null.** For each observed target x donor unit,
   build synthetic pseudo-targets from the *same number* of donor-matched NT
   guide groups, matched on cell count only — never on RNA or depth. Each
   pseudo-target is excluded from its own NT reference.
2. **Depth-only binomial-thinning null.** Take the *same* pooled NT composition
   and binomially thin it in read space to the real unit raw depth. Composition
   is held fixed by construction, so this arm isolates read depth, zeros and
   pseudocount behaviour from cell-state heterogeneity.

64 draws per arm, seed 301119, pseudocount 1.0, the exact legacy estimator.
Coverage: 809 estimable target x donor units (409 CRISPRi, 400 CRISPRa) out of
824; 15 were declared not estimable (11 cell support, 4 insufficient matched NT).
5,663 sentinel gene observations across the seven predeclared genes
(CLU, CCL22, MMP12, CXCL10, CXCL11, MT1H, MT1G).

## Result

A null comparing non-targeting cells against non-targeting cells must centre on
zero. Neither arm does, and the cell-sampling arm is not close.

| | observed effects | cell-sampling null | depth-only null |
|---|---|---|---|
| median log2FC | **-1.3446** | **-1.5040** | -0.0461 |
| median, CRISPRi | -1.3446 | -1.4071 | -0.0414 |
| median, CRISPRa | -1.3042 | -1.7461 | -0.0495 |
| fraction with abs(median) > 0.10 | — | **94.0 %** | 47.3 % |
| median 95 % interval width | — | 5.669 | 2.045 |
| unit-level median max abs(log2FC) | — | 4.797 | 3.828 |

**The fake effects are the same size as the real ones.** The cell-sampling null
median (-1.5040) is slightly *larger in magnitude* than the median real effect
(-1.3446), in the same direction.

**Exceedance** — the fraction of null draws whose absolute effect is at least as
large as the real observed absolute effect:

| | cell-sampling | depth-only |
|---|---|---|
| median exceedance | **0.7500** | 0.0938 |
| at or above 0.05 | 96.0 % | 55.9 % |
| **at or above 0.50** | **72.8 %** | 26.4 % |

For roughly three-quarters of sentinel gene x unit observations, at least half of
the NT-versus-NT draws beat the real perturbation.

**The predeclared recurrence statistic has no discriminating power at all.**

| sentinel in extreme tail | observed | cell-sampling null | depth-only null |
|---|---|---|---|
| top-25 **up** | 3.62 % | **4.83 %** | 0.10 % |
| top-25 **down** | 17.69 % | **17.69 %** | 0.31 % |

The down-tail recurrence rate agrees to four significant figures, and the
up-tail rate is *higher* under the null than under the real data.

**These two quantities were checked for collapse and are genuinely distinct.**
Two separately computed numbers agreeing that closely warranted confirming that
the comparator was not returning the same array twice — this project has
previously found a comparator computing the wrong object. It is not:
`observed_top25_down` is a boolean (1002/5663 = 0.176938018718) while
`null_top25_down_fraction` is a float with **118 distinct values**, 3,049 of them
strictly interior to (0, 1), summing to 0.176865600035. They differ by
**7.24e-05**, correlate at 0.548 rather than 1.0, and 4 observations sit in the
observed tail with a null fraction of exactly zero. The agreement is a real
coincidence of two independent computations, not an aliasing artifact. An earlier
draft of this document called them "identical"; they are not.

## Mechanism

The target units are far shallower than the NT reference they are compared
against: the NT pool carries a median **19.8x** the raw depth of a unit (5th-95th
percentile 9.8x-46.7x), with a median unit of 53 cells against 1,425 NT cells.
The bias grows with that disparity:

| NT depth / unit depth | n | cell-sampling null median |
|---|---|---|
| 0-10x | 301 | -1.4594 |
| 10-25x | 3,731 | -1.3866 |
| 25-50x | 1,421 | -2.0483 |
| above 50x | 210 | -2.5423 |

This is the same failure already recorded in the compositional-bias self-audit,
where a planted flat gene with identical raw counts (100 vs 100) read
-0.8073517, matching -log2(525/300) = -0.8073549 exactly. A gene that is zero in
a shallow unit scores log2(0 + 1) = 0, while the deep NT pool scores a small
positive value, so the difference is systematically negative. The effect is a
property of the estimator and the depth imbalance, not of the perturbation.

## Which artifact is responsible

The frozen interpretation was fixed before the numbers were seen. Applying it
honestly, this is the **"both bad"** branch, with a clear ordering inside it:

* Holding composition fixed and varying only depth (depth-only arm) leaves a
  median bias of -0.046 — small, but **not clean**: 47.3 % of medians still sit
  beyond 0.10, 26.4 % of observations still show exceedance at or above 0.50, and
  the arm median max abs(log2FC) is 3.828. Read depth, zeros and pseudocount
  behaviour alone generate substantial apparent signal.
* Letting NT composition vary as well (cell-sampling arm) moves the median from
  -0.046 to -1.504. That roughly thirty-fold increase is attributable to
  heterogeneous cell-state under-sampling across NT guide groups.

So **cell-state under-sampling is the leading explanation**, and depth/zero/
pseudocount behaviour is a smaller but independently non-clean second artifact.
Neither branch of the frozen rule fits alone; reporting only the first would
overstate how clean the depth-only arm is.

### The components have been sized independently

An independent simulation of this null under **pure Poisson counting** at the
measured 19.8x gap — same expression profile, no true effect, only depth varying
— reproduces the depth-only arm at **-0.074** against the **-0.046** measured
here: the same phenomenon at the right order of magnitude. It comes nowhere near
the cell-sampling arm. Counting statistics alone account for roughly **5 %** of
the -1.504 measured. The simulation contains no cell-to-cell structure, so the
missing twenty-fold is exactly what Poisson noise cannot generate: genuine
cell-state heterogeneity between a 53-cell draw and the 1,425-cell pool.

That decomposition rules out two corrections that would otherwise look right:

* **Stratifying by baseline expression** would clean the depth arm convincingly —
  the depth component is strongly expression-dependent, with genes at 50 CPM or
  above carrying a median bias of -0.001 at 19.8x and only -0.007 even at 50x,
  while the bottom deciles carry -0.1 to -0.47. But the composition term does not
  behave that way: genes whose high expression is confined to a subpopulation,
  which is precisely what CLU, CXCL10 and MT1G are, carry large composition
  variance regardless of overall abundance. The correction would have passed its
  own diagnostic and left the dominant term in place.
* **A negative-binomial GLM with library-size offsets** fixes the depth term and
  models the zeros properly, but between-cell state variance is not in that model
  either, so it does not address about 95 % of what was measured.

This is therefore not a parametric estimator swap. See
`GSE301119_EMPIRICAL_NULL_CALIBRATION_DIRECTION_20260925.md` for the direction
that does address the dominant term.

## Consequences

**What this invalidates.** The GSE301119 donor-aware descriptive effects, as
currently specified, are not usable as a JEPA benchmark, as a training target, or
as evidence of intervention direction. The predeclared sentinel and top-25
recurrence readouts are not usable either, since the null reproduces them.

**What this does not invalidate.** Nothing in the software-correctness work is
overturned. P0-3 established that the R producer and the independent Python
reproducer agree to 1.776e-15 over about 22.7 M cells; that remains true. This
result is about the **estimand**, not the implementation — which is precisely the
gap recorded as self-audit **S4**: *a wrong spec would be reproduced faithfully
by both.* S4 named this failure mode in the abstract; this run demonstrates it
concretely. Two faithful implementations of a biased estimator agree perfectly
and are both wrong.

**What is still open and worth checking.** The cross-modality observation from
the overlap analysis — five shared direct targets (CSF1R, CSF2RA, CSF2RB,
TGFBR1, TGFBR2) reading 5/5 down under CRISPRi and 5/5 up under CRISPRa — is only
half-explained by this artifact. The bias is negative in both modalities
(CRISPRi -1.41, CRISPRa -1.75), so the CRISPRi down-calls are exactly what the
artifact produces, but the CRISPRa **up**-calls run *against* the bias direction
and are not accounted for by it. This receipt covers sentinels and tail
recurrence only, not those five target rows, so that is a stated follow-up and
not a claim.

**What this does not license.** No repair of the estimator is authorised by this
document, and no result here is a p-value. The null draws share NT units and are
Monte Carlo references, not independent biological replicates. GSE301119 still
has n=2 donors and licenses no population claim.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
status DEVELOPMENT_ONLY_NO_SCIENTIFIC_QUALIFICATION
```
