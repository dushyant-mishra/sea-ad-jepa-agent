# Reserved-readout exposure ledger

Date 2026-09-27. **Correcting a claim I made repeatedly: that the six reserved
readouts were "untouched" and "unspent". That statement was too broad.**

The six are SALL1, CTSD, CTSS, LPL, CSF1R, HLA-DMB — two per program.

## What was actually exposed, by whom, and when

### A. Pre-existing, in R7 — before any of my work

`JEPA_R7_PROGRAM_FALSIFIER_COMPOSITION_RESULTS_20260926.json` and its
`LOG_RAW` companion contain **all six**, in two ways:

1. **Design disclosure** — the `programs_predeclared_before_run` block names each
   program's held-out pair. That is a statement of design, not an inspection of
   data.
2. **A computed statistic on the held-out genes.** Per fold, per program, R7
   recorded `heldout_support_fraction`:

   | program | held-out pair | support fraction |
   |---|---|---|
   | APOE_LIPID | CTSD, LPL | 0.889 |
   | P2RY12_HOMEOSTATIC | SALL1, CSF1R | 1.000 |
   | HLA_DRA_ANTIGEN | HLA-DMB, CTSS | 1.000 |

   This is an **availability** measure — how often the genes are measurable —
   not an outcome association. It is a weak exposure, but it is an exposure.

   One qualification that cuts both ways: R7 ran on the **scrambled** gene
   coordinates, so those numbers are not actually about those genes. They
   neither informed anything true nor leaked anything true.

   R7 also recorded `same_assay_heldout_readouts_are_not_external_biology: true`,
   so the original design never claimed these were independent validation.

### B. Mine — 2026-09-27

**CSF1R is the significant one.** I used it repeatedly as a marker-plausibility
diagnostic while verifying the gene-identity decoder:

| where | what was computed | value |
|---|---|---|
| `AUDIT_MASKED_MYELOID_ARTIFACT_V1.json`, committed | CSF1R detection fraction per source | HVS 65.9%, NPH52 90.0%, SEA-AD 81.7% |
| decoder validation, reported in-session | CSF1R naive vs decoded detection, HVS | 0.0% → 63.7% |
| discovery shard op19 probe, reported in-session | CSF1R naive vs decoded detection | 0.0% → 76.6% |

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

**The other four: no.**

## Consequence, and the conservative call

> **CSF1R is now EXPOSED and is removed from the reserved set.** Any future
> independent-readout test must either exclude it, or report results both with
> and without it and treat the with-CSF1R version as non-independent.
>
> **LPL is AVAILABILITY-EXPOSED**: its presence/absence pattern is known, its
> values are not. Usable as a readout, with the exposure recorded.
>
> **SALL1, CTSD, CTSS, HLA-DMB remain reserved.** Four genes, not six.

Shrinking the reserved set is the cost of the exposure and is cheaper than
defending a hold-out that was not held out.

## The rule this should have followed

A hold-out is spent the moment any statistic is computed on it, including a
diagnostic that seems harmless and is not used for fitting. "We looked at it
only to check the pipeline" is exactly the claim that cannot be verified after
the fact. The correct discipline is to choose plausibility markers from **outside**
the reserved set — CD74, P2RY12, C1QA and CX3CR1 were all available and would
have served identically.
