# V64 frozen statistical red-team — depth ablation **A**, out-of-span **B**

Executed on branch `claude/v64-frozen-execution-20260929` from canonical head
`2d6fa8a1`. Estimator **imported unmodified** from
`e2_continuous_adjustment_estimator_v1.py`; the two interventions are applied
from outside it. donors=18, seeds=24 throughout.
`TRAINING=OFF`, `TD60=BLOCKED`, synthetic only.

**Harness fidelity, stated with its configuration.** The baseline run through the
new runner (18 donors, 24 seeds) reproduces the committed `c4e78de2` primary to
the last digit: POS_BIO_1 `0.2282527590455996`, TECH margin
`0.01995560304936889`, LCB `0.01948446698612133`, ESS `935.4469599793607`. The
comparisons below are therefore like-for-like.

---

## Test 1 — depth-sensitivity leakage ablation: **A_pass_survives**

Contract: `V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_LEAKAGE_DIAGNOSTIC_V1`.
Removed **only** `rna_depth_sensitivity` and `atac_depth_sensitivity`
(14 → 12 features). Nothing else moved; the six nonlinear terms never involved
those columns.

| quantity | baseline (14) | ablated (12) | Δ |
|---|---|---|---|
| POS_BIO_1 | +0.22825 | +0.22822 | **−0.00003** |
| POS_BIO_2 | +0.03140 | +0.03139 | **−0.00001** |
| NEG_TECH_2 | +0.01185 | +0.01183 | −0.00002 |
| TECH margin / LCB95 | +0.01996 / +0.01948 | +0.01994 / +0.01946 | ~0 |
| Kish ESS | 935 (97.4%) | 935 (97.4%) | 0 |
| top 1/5/10% | 0.013/0.066/0.128 | 0.013/0.066/0.128 | 0 |
| families passing | 6 / 6 | **6 / 6** | — |

**The risk was real in principle and empirically negligible.** The concern — that
covariates computed from each arm's own signals could absorb planted biology
while wearing a nuisance label — was correct to raise and is mine to own: I built
those features from the raw pre-residualisation signals precisely so they would
"carry information", and the information they carry includes the planted effect.

But the measurement says they carried almost none. Reading **C** (positives
materially restored once the suspect covariates are gone, implying
over-adjustment) is **ruled out**: the positives move by 3 parts in 100,000. The
estimator does not depend on them.

This also retro-explains the near-zero out-of-fold R²: these two features
contributed essentially no predictive weight, so their removal costs nothing.

> **Reading A is strengthened. The `c4e78de2` pass is no longer provisional on
> this ground.**

---

## Test 2 — out-of-span stress: **B_outspan_fails_only**

Contract: `V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_CONTRACT_V1`. One new
negative, `NEG_TECH_OUTSPAN_1`, identical to `NEG_TECH_2` in hidden-quality
mixing (`0.6·z_meas + 0.8·orthogonal`) and amplitude (0.60), differing **only**
in the ATAC-side geometry function:

```
g = zscore( sin(2.5·z_log_distance)
            + 0.5·tanh(z_degree · z_anchor_frequency)
            + 0.35·z_accessibility · z_re_density )
```

**No sin or tanh term was added to the ridge basis.** That is the test.

| family | margin | LCB95 | |
|---|---|---|---|
| NULL | +0.03228 | +0.03206 | PASS |
| TECH | +0.01996 | +0.01948 | PASS |
| GEO | +0.02556 | +0.02517 | PASS |
| ACC | +0.03166 | +0.03031 | PASS |
| ANCHOR | +0.03700 | +0.03578 | PASS |
| DONOR | +0.03202 | +0.03161 | PASS |
| **OUTSPAN_TECH** | **−0.03211** | **−0.03558** | **FAIL** |
| held-out ambient | +0.03233 | +0.03174 | generalises |

`NEG_TECH_OUTSPAN_1` scores **+0.06135** — roughly **double the positive floor**
(POS_BIO_2 at +0.03140) and **five times** what the in-span `NEG_TECH_2` scores
(+0.01185) under identical latent and amplitude. The ordering check correctly
reports `False`, because a negative now outranks a positive.

**Same latent. Same amplitude. Same everything but the geometry function.** The
ridge can absorb `geom` and cannot absorb `g`, and the gap between those two
outcomes is the entire finding.

Classification against the frozen readings:

- **A_outspan_passes** — no.
- **B_outspan_fails_only** — **yes.** Every pre-existing family still passes,
  support is unchanged (ESS 935, top-10% 0.128), the twin stays identical and the
  held-out ambient family still generalises. The failure is confined to the
  out-of-span arm.
- **C_existing_family_breaks** — no.
- **D_support_concentrates** — no; support is bit-identical to baseline.

> **The estimator is qualified ONLY for nuisance surfaces within or near its
> frozen model span. It must not be generalised to arbitrary hidden-quality
> geometry.**

---

## What this does to the Branch 2 result

It bounds it, exactly where I said it needed bounding and by more than I
expected. When reporting classification A I wrote that the frozen feature set
spans `NEG_TECH_2`'s latent almost exactly, so A's scope was *"within the span of
the frozen adjustment model"*, and that an out-of-span nuisance would either
widen that scope or bound it.

It bounds it. And not marginally — the out-of-span negative does not merely
survive, it **outscores the positives**.

So the two results compose into a single honest statement:

> Continuous adjustment resolves geometry-coupled hidden quality **whose
> functional form lies within the frozen basis**, with broad support and without
> depending on outcome-derived covariates. It does **not** resolve
> geometry-coupled hidden quality in general, and a smooth non-monotonic
> geometry outside the basis defeats it outright.

**The forbidden repair is forbidden for a good reason.** Adding `sin`/`tanh`
terms would make OUTSPAN pass, and would prove nothing: one can always extend a
basis to cover a nuisance one has already seen. The span limitation is a
**property of the estimator**, not a bug awaiting a patch, and the honest response
is to carry it as a scope condition on any real-data use.

## Consequence for the NIH-CARD phase

Before the continuous-adjustment estimator is used for validation-cohort
correspondence, someone has to answer: **is real capture-quality geometry within
or outside this basis?** That question is now sharp and answerable, where before
it was a caveat. Two honest routes exist and neither is taken here:

1. argue from measured NIH-CARD QC structure that the relevant geometry
   dependence is low-order in distance and degree — an empirical claim, testable
   on the already-authenticated schema without opening correspondence;
2. accept the bound and state it in the claim scope.

What is **not** available is assuming route 1 without checking it.

## Self-audit

**S-V64-1.** The depth-sensitivity leakage risk was identified by the parallel
lane, not by me, and it was a real hole in my design: I introduced two
arm-dependent covariates and labelled them nuisance. The ablation shows it cost
nothing here, but "it turned out not to matter" is not the same as "it was
sound", and the diagnostic existing at all is why that distinction can be made.

**S-V64-2.** I reported the smoke-configuration numbers as reproducing "the
earlier run" without naming the artifact or the configuration, which cost a real
investigation for no defect. The full-configuration comparison above is stated
with both configurations for exactly that reason.
