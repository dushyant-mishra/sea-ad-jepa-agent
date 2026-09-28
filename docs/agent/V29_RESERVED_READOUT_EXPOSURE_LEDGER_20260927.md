# Reserved-readout exposure ledger

Date 2026-09-27. **Correcting a claim I made repeatedly: that the six reserved
readouts were "untouched" and "unspent". That statement was too broad.**

The six are SALL1, CTSD, CTSS, LPL, CSF1R, HLA-DMB — two per program.

> ## CORRECTION 2, later on 2026-09-27
>
> The first version of this ledger got section A **materially wrong**. It said
> R7's treatment of the held-out readouts was "an **availability** measure — how
> often the genes are measurable — not an outcome association."
>
> That is false. It was true only of one statistic, `heldout_support_fraction`,
> which I then generalised to R7's whole treatment of the readouts. R7 in fact
> **fitted and scored five nested predictive models whose dependent variable was
> the held-out readout pair**, for all three programs, across five folds, in both
> target modes — and published the out-of-sample R². That is a full
> teacher-to-held-out-readout outcome analysis, not an availability count.
>
> I found this only by opening the result files and the producer source rather
> than trusting my own summary of them. Section A below is rewritten; the
> superseded claim is quoted above so the record shows what was corrected.

## What was actually exposed, by whom, and when

### A. Pre-existing, in R7 — before any of my work

`JEPA_R7_PROGRAM_FALSIFIER_COMPOSITION_RESULTS_20260926.json` and its
`LOG_RAW` companion contain **all six**, in three ways of increasing severity.

**1. Design disclosure.** The `programs_predeclared_before_run` block names each
program's held-out pair. A statement of design, not an inspection of data.

**2. An availability statistic.** Per fold, per program, R7 recorded
`heldout_support_fraction` — how often both readouts are measurable:

| program | held-out pair | support fraction |
|---|---|---|
| APOE_LIPID | CTSD, LPL | 0.889 |
| P2RY12_HOMEOSTATIC | SALL1, CSF1R | 1.000 |
| HLA_DRA_ANTIGEN | HLA-DMB, CTSS | 1.000 |

**3. A full outcome analysis on all three readout pairs.** This is the part the
first ledger missed. In `JEPA_R7_BIOLOGICAL_PROGRAM_FALSIFIER_20260926.py`, the
held-out readout pair is loaded as `h`, log-transformed and support-masked as
`hlog`, and then used as the **response variable** in five fitted models:

```
h_teacher     = fit_predict(Y[trh],            hlog[trh], wh, Y[teh])
h_tech        = fit_predict(trtec,             hlog[trh], wh, tetec)
h_plus_tech   = fit_predict(np.c_[Y,trtec],    hlog[trh], wh, ...)
h_plus_tech_q = fit_predict(np.c_[Y,trtec,q],  hlog[trh], wh, ...)
h_q           = fit_predict(np.log1p(qc[trh]), hlog[trh], wh, np.log1p(qc[teh]))
```

Each is scored out-of-sample against a weighted train-mean reference and written
to `records` under `section: TEACHER_FIDELITY_RNA_ONLY`. That is 5 arms x 3
programs x 5 folds = **75 scored R² values per target mode, 150 across the two
published files**, every one of them a model *of the reserved readouts*.

The `section: TEACHER_READOUT_ESTIMABILITY` row with `r2: null` is **not** a
refusal to compute, and must not be read as one. It is a bookkeeping header
recording the design size of the readout analysis — `n_train_micro`,
`n_test_micro`, `n_test_donors` — with `r2` hard-coded `None` in the literal.
The values it describes sit in the `TEACHER_FIDELITY_RNA_ONLY` rows written
immediately below it in the same loop. I first read that `null` as evidence
that nothing had been computed. It is the opposite: it is the label on the
analysis that was.

Fold-averaged R², COMPOSITION mode (LOG_RAW is materially the same):

| program (readout pair) | PROGRAM_ONLY | TECH_ONLY | PROG+TECH | PROG+TECH+Q | Q_ONLY |
|---|---|---|---|---|---|
| APOE_LIPID (CTSD, LPL) | −0.0857 | −0.2061 | −0.2959 | −0.3854 | −0.0314 |
| P2RY12_HOMEOSTATIC (SALL1, CSF1R) | −0.0949 | −0.0376 | −0.1072 | −0.1166 | −0.0075 |
| HLA_DRA_ANTIGEN (HLA-DMB, CTSS) | −0.0572 | −0.0049 | −0.0431 | −0.0475 | +0.0002 |

**What these numbers are not.** R7 ran on the historical sample whose gene
coordinates are scrambled — established in
`V29_R7_R8_INPUT_LINEAGE_UNVERIFIABLE_20260927.md` and upgraded there to
`DEFECTIVE_INPUT_DEMONSTRATED`. The columns labelled CTSD, LPL, SALL1, CSF1R,
HLA-DMB and CTSS were not those genes. **These R² values therefore cannot be
interpreted as measurements of the named genes**, in either direction: they are
not evidence that the teacher fails to predict the real readouts, and not
evidence that it succeeds.

**What survives the scramble, and matters.** The gene labels were wrong, but the
*design* was real: 59–145 training micro-units per fold, predicting a
two-dimensional response. Nearly every arm is negative, including `TECH_ONLY` —
a technical-covariate-only model doing worse than simply predicting the training
mean. A negative out-of-sample R² for a technical-only model is a statement
about estimator variance at this sample size, not about biology, and it is
gene-label independent. **This is a live warning for the six directed tests:**
at comparable numbers of independent units this readout design overfits, and the
real protocol will reproduce that failure unless its unit count is materially
larger. That inference is legitimate precisely because it does not depend on
which genes the columns actually were.

R7 also recorded `same_assay_heldout_readouts_are_not_external_biology: true`
and `protected_opened: false`, so the original design never claimed these were
independent biological validation, and no protected outcome was touched.

### B. Mine — 2026-09-27

**CSF1R is the significant one.** I used it repeatedly as a marker-plausibility
diagnostic while verifying the gene-identity decoder:

| where | what was computed | value |
|---|---|---|
| `AUDIT_MASKED_MYELOID_ARTIFACT_V1.json`, committed | CSF1R detection fraction per source | HVS 65.9%, NPH52 90.0%, SEA-AD 81.7% |
| decoder validation, reported in-session | CSF1R naive vs decoded detection, HVS | 0.0% → 63.7% |
| discovery shard op19 probe, reported in-session | CSF1R naive vs decoded detection | 0.0% → 76.6% |

These were computed on **decoded, authenticated** coordinates. Unlike R7's
numbers, they really are about the real CSF1R. That is what makes this the most
severe exposure in the ledger despite being the smallest in volume.

**LPL** — its *structural absence* from the HVS object was established and
reported. That is an availability fact, not a value, and it is unavoidable:
the extractor cannot decide whether to refuse a matrix without knowing whether
the gene exists in it.

**SALL1, CTSD, CTSS, HLA-DMB** — extracted into the artifact as raw counts, but
no statistic over them has been computed or published by me.

**The artifact physically contains all six.** That was deliberate — they were
extracted so an independent-readout test would be possible later — but
"contained in the file" and "not inspected" are different claims and I conflated
them.

## Did the exposure influence a decision?

**CSF1R: yes, partially, and the dependency is removable.** It contributed to my
confidence that the decoder was correct. But the decoder was verified
independently by cell-by-cell agreement against the authenticated source files
at 100.00%, a check that involves no marker plausibility at all. The decoder
would stand with every CSF1R number struck out. No teacher was fitted on it, and
no program was selected or rejected using it.

**LPL: yes, structurally.** Its absence drove the panel-scoped refusal rule —
refuse on a missing query or panel gene, record a missing readout. That rule is
about availability, not values.

**R7's outcome analysis, all six: not in a gene-specific way, but not nothing.**
Because the coordinates were scrambled, nothing gene-specific could transfer.
The design lesson stated in A.3 did transfer, and I am recording it as
transferred rather than pretending the files were never opened.

**SALL1, CTSD, CTSS, HLA-DMB, beyond R7: no.**

## Consequence

Three separate questions, which the first version of this ledger ran together.
Keeping them apart is the whole point.

### 1. Membership of the frozen v7 denominator — UNCHANGED, all six

> **All six reserved genes remain in `EXCLUDED(P,Q)`.** This is not revisited
> here and is not revisitable here.

The denominator is a **definition of the measured quantity**: every activity
value in the experiment is a ratio against a reference library that omits these
six. Removing CSF1R from it would silently redefine the estimand in all six
directed tests, under cover of an exposure fix — the numbers would move, the
protocol digest would still look frozen, and the change would be nearly
impossible to detect afterwards. Exposure is a governance fact; denominator
membership is an estimand fact. A governance correction never licenses an
estimand change.

### 2. The exposure register — all six stay on it

Nothing is deleted from this ledger. My earlier phrasing, **"Four genes, not
six"**, was wrong in a way worth naming: it read as though two genes had been
struck off the record, when what was actually being decided was their
*confirmatory usability*. The register lists six and will keep listing six.

### 3. Readout identities — all six retained, behind an exposure firewall

> **CORRECTION 3, 2026-09-28.** An earlier version of this section removed CSF1R
> from the readout set. That was wrong, and the instruction it followed has been
> withdrawn by its author:
>
> > "Your decision to retain all six readouts with a documented exposure
> > firewall is consistent with the original 30 KB mission. My subsequent
> > copy-paste instructions contradicted that document by recommending CSF1R's
> > removal; that recommendation should be superseded. Retaining CSF1R does not
> > restore an untouched holdout, so its previous diagnostic use must remain
> > visible and excluded from future adaptive choices."
>
> The frozen mission document governs over a later chat instruction. All six
> originally frozen RNA readout identities are restored.

| gene | exposure | how it is handled |
|---|---|---|
| CSF1R | **VALUE-EXPOSED** on authenticated coordinates, by me | **Retained, firewalled — and not relabelled untouched.** The decoder-QC detection fractions stay published and visible. Any result using CSF1R must be accompanied by a **prospectively fixed sensitivity analysis that isolates its contribution**, and must not be described as independent previously-unseen validation. |
| LPL | **AVAILABILITY-EXPOSED** — presence/absence known, values not | **Retained, conditional.** HVS must be excluded from any test requiring an observed LPL value, since LPL is structurally unmeasured there. |
| SALL1, CTSD, CTSS, HLA-DMB | **PROCEDURE-EXPOSED** in R7 only, on scrambled coordinates | **Retained, strict.** No gene-specific value information about them has been released by anyone. |

All six additionally carry the R7 procedure exposure described in section A.3.
Because that exposure is gene-label independent, it does not compromise any of
the four strict readouts for gene-specific inference — but it is on the record,
and any future claim that these readouts were "never looked at" is false and
must not be made.

**Restoring membership does not restore innocence.** CSF1R is back in the set
because removing it was not the instruction and because a shrunken set is not
automatically the safer one — a hold-out register that quietly drops its
inconvenient members stops being a register. What removal would have bought,
the firewall must now buy instead: the exposure stays visible, and CSF1R is
**excluded from every future adaptive choice** — panel composition, thresholds,
exclusions and endpoint weights must all be fixed without reference to it.

## The rule this should have followed

A hold-out is spent the moment any statistic is computed on it, including a
diagnostic that seems harmless and is not used for fitting. "We looked at it
only to check the pipeline" is exactly the claim that cannot be verified after
the fact. The correct discipline is to choose plausibility markers from
**outside** the reserved set — CD74, P2RY12, C1QA and CX3CR1 were all available
and would have served identically.

## The rule this correction adds

**Do not characterise a historical analysis from its summary rollup, or from a
field name.** Both failure modes fired here, in the same document: I read
`heldout_support_fraction` and called R7's whole treatment "availability", and I
read `TEACHER_READOUT_ESTIMABILITY: null` and called it uncomputed. The analysis
was in neither place — it was in the `records` array under a different section
name, and only the producer source made that unambiguous. Open the producer and
enumerate what was actually fitted before writing down what a prior run did or
did not look at.
