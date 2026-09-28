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

**SALL1, CTSD, CTSS, HLA-DMB** — extracted into the artifact as raw counts.
As of 2026-09-27 no statistic over them had been computed by me. **That ceased
to be true on 2026-09-28; see CORRECTION 4.** The sentence is left standing
here, unedited, because the record should show what was believed at the time
rather than quietly becoming right in hindsight.

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

## CORRECTION 4, 2026-09-28 — I computed statistics on all six myself

Found by independent source review of PR #178 at `bf5dc220`, not by me.

`full104_candidate_pool_census_v1.py` mapped every decoded CSR entry, computed
the normalised value `y`, and folded it into per-address accumulators **before**
anything excluded the forbidden set. The exclusion happened later, in
`eligible_mask`, at candidate-selection time. Excluding a gene from selection
does not un-compute a statistic that has already been taken.

**What was computed.** For each of the six reserved readouts, per source, over
114,041 fitting nuclei: mean raw count, detection fraction, Fano factor,
correlation with log depth, and correlation with the housekeeping score. Across
three sources and five statistics that is 90 slots, of which **80 were finite,
i.e. actually computed**. This happened in both the void first run and the
reported second run. The values were verified to exist without being printed.

**These are on authenticated, decoded coordinates.** Unlike R7's 150 scored R²
values, which were computed on scrambled columns and therefore describe unknown
genes, these really are about SALL1, CTSD, CTSS, LPL, CSF1R and HLA-DMB.

**What limits it, stated without using it as an excuse:**

- **Nothing was published.** The three committed receipts contain counts and
  availability only; the analysis excluded all 48 forbidden addresses and the
  audit deliberately declines to compare the reserved six. The arrays exist
  only in a local `.npz`.
- **No value was ever displayed** in this session or any report, and none was
  read back by me.
- **Nothing consumed them.** No candidate was selected using them, no threshold
  was set from them, no tier was chosen against them.

**Why that distinction is worth drawing, and where it stops.** The harm a
hold-out guards against is that knowledge of an outcome steers a later choice.
A number written to a local file and never read cannot steer anything. So this
is a **computation-level** exposure, not a **disclosure-level** one, and it is
materially less severe than the CSF1R entry, where detection fractions were
published in a committed receipt and did influence my confidence in the decoder.

But this ledger's own rule is that a hold-out is spent the moment any statistic
is computed on it. By that rule these are spent, and pretending otherwise would
be exactly the "we only looked to check the pipeline" claim the rule exists to
refuse. **The four previously strict readouts — SALL1, CTSD, CTSS, HLA-DMB —
are no longer strict.** They are recorded here as computation-exposed.

**Whether that changes their confirmatory usability is a scientific judgment
for the owner, not one I should make silently.** My reading is that it should
not, because the causal pathway by which exposure does damage demonstrably did
not operate and is now blocked by construction. That reading should be
challenged rather than adopted.

**The repair, and how it is enforced.** Protected addresses are dropped from
the CSR entries *before* normalisation and *before* any accumulator sees them.
Their output slots carry an explicit `NOT_COMPUTED` sentinel of `-1` rather
than a zero, because a zero reads as "measured and absent" — the precise error
this project keeps making. A **poison-invariance** adversary plants absurd
counts at every protected address and requires every accumulator to be
bit-identical; if a protected value could influence any statistic, it fails.
The other 42 forbidden addresses remain accumulated deliberately: they are
already published in the 29-address artifact, and the cross-path audit needs
them to verify the decoder end to end.

**The general lesson, which is not the one I would have guessed.** I built a
firewall and placed it at the point of *use* rather than the point of
*measurement*. A firewall downstream of the computation protects the decision
and not the hold-out. Exclusion has to happen at the earliest point where the
protected value physically enters the pipeline — here, immediately after
address decoding and before normalisation.

## OWNER RULING, 2026-09-28 — all six retired as strict endpoints

Issued after reviewing `d183fbed`. This supersedes the tiering in section 3 of
the Consequence block above, and it is the governing status.

> "All six reserved RNA readouts should now be retired as strict independent
> confirmatory endpoints. That does not mean they are useless."

| gene | exposure | what it may now support |
|---|---|---|
| **CSF1R** | **Value-exposed.** Decoded gene-specific values were inspected and did influence plausibility reasoning. | **Secondary / sensitivity evidence only.** |
| **SALL1, CTSD, CTSS, HLA-DMB** | **Computation-exposed.** Statistics computed on authenticated coordinates; never printed, never selected on. | **Prespecified secondary evidence.** May **not** be described as previously unseen confirmation. |
| **LPL** | **Availability-exposed**, and now also computation-exposed in the void census runs. | Same secondary status. |

**No replacement set is to be drawn.** The ruling is explicit:

> "I would not replace them with six fresh genes now. Doing that after
> discovering the failure mode would create a new post hoc confirmation set and
> invite another round of selection. Preserve the original six, document
> exactly what happened, and downgrade the claim they can support."

This is the right call and worth stating plainly, because the tempting repair is
the wrong one. A hold-out's value comes from being fixed *before* anyone saw how
the analysis would behave. Six genes chosen *now* would be selected by people
who have just learned which genes were awkward, and that contamination leaves no
written trace — whereas this spent set has a full exposure history. Keeping a
documented spent hold-out beats manufacturing a clean-looking one.

**The consequence that must not be buried.** With every internal reserved
readout downgraded, **this study has no strictly independent internal
confirmation left.** That raises the weight on a genuinely external modality —
specifically the already-designed donor-level ATAC evaluation — as the real
confirmation layer. Any report that downgrades the six must say this in the same
breath, rather than leaving a reader to discover that nothing independent
remains.

## CORRECTION 5, 2026-09-28 — a reserved readout is recorded as measured where it was never measured

Found by the Lane B reader-provenance repair and verified independently here.

**Address 26659 (HLA-DMB) is absent from NPH52's authenticated feature axis.**
It is the only one of the six reserved readouts that is. Yet the corrected
29-address artifact marks it `address_available = True` for all **15,264 NPH52
nuclei**, so any consumer reading it there would be reading 15,264 structural
absences as measured zeros.

| reserved readout | in NPH52 authenticated axis |
|---|---|
| SALL1 (2810), CTSD (4748), CTSS (10846), LPL (13734), CSF1R (14980) | yes |
| **HLA-DMB (26659)** | **NO** |

This is the same root cause as the HLA-DPA1 defect in Correction 4's companion
report: `load_addr_to_col` returns early for identity-verified matrices with an
empty unreachable list, so NPH52 availability was asserted rather than derived.
Verifying *where* an address sits in the object was treated as also answering
*whether* the object carries it.

### Why no existing audit could have caught it, and the tension that creates

My census auditor deliberately excludes the six reserved readouts from every
comparison — that exclusion is the exposure firewall and it is correct. But it
also made the auditor **structurally incapable** of noticing that a reserved
readout's availability flag was false. The firewall that protects the hold-out
also blinded the audit of it.

The resolution is not to weaken the firewall. It is that **availability can be
audited without reading values**: compare the artifact's `address_available`
mask against the authenticated feature axis directly. That check touches no
count, so it is firewall-safe, and it is what found this.

**This is now a standing requirement.** Any protected variable still needs its
*structural* metadata audited even while its values stay sealed. "We cannot
look at it" must never become "we cannot check whether the file is lying about
it."

### Consequence for HLA-DMB as secondary evidence

Under the owner ruling, HLA-DMB is already downgraded to prespecified secondary
evidence. It now carries an additional, separate limitation: **it is not
measurable in NPH52 at all.** Any secondary analysis using HLA-DMB must exclude
NPH52 rather than treat its zeros as observations — the same handling LPL
already requires for HVS. This is an availability fact, not a value, and
recording it opens nothing.

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
