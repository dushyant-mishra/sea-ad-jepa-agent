# NIH-CARD ↔ E2 correspondence: the frozen prospective design

**Written for: the independent auditor of this design, before execution is authorised.**

This is the design only. **No E2 correspondence outcome was opened.** Nothing in
this document, the contract, or the precondition script computes an RNA–ATAC
relationship for an E2 edge.

Canonical parent `211e3d7c` (live HEAD verified at takeover, not assumed).

---

## The question being frozen

> Do the independently constructed Nott-centered E2 regulatory relationships
> correspond to RNA–ATAC biology in NIH-CARD microglia, in a way that survives
> technical and generic-accessibility explanations?

Everything below is fixed *before* the answer exists.

---

## The blocker I found, and it is the important part of this report

**NIH-CARD nucleus pairing is formally UNRESOLVED on canonical, and the entire
estimand depends on it.**

`NIHCARD_SCHEMA_RECEIPT_V2` records `state: PAIRING_NAMESPACE_UNRESOLVED` and
`QUALIFIED_FOR_PAIRED_USE: false`. Exact index overlap between the RNA and ATAC
files is **0 of 1,501,089**, because the ATAC index repeats the sample suffix:

```
RNA   AAACAGCCACGTGCTG-1_HBCC-1193
ATAC  CCTATAGCAATATAGG-1_HBCC-1193_HBCC-1193
```

The `(sample, raw_barcode)` composite matches **1,501,089 of 1,501,089 with no
residual** — but the receipt marks it `AUTHORITATIVE: false`, with a reason I think
is exactly right:

> "raw 10x barcodes repeat across samples and the sample qualifier is taken from a
> column whose correspondence between the two files has not been independently
> established. A composite match is consistent with shared nuclei; it is not
> evidence of them."

The project-level brief I was given states the composite bridge "is the valid
identity bridge." **The canonical receipt does not say that**, and I was told to
verify against canonical rather than inherit stated facts. So I have not treated it
as settled. The correspondence estimand is a *same-nucleus* quantity: if the bridge
is wrong, every score is computed across mismatched nuclei and the test measures
nothing at all.

**What the design does instead of asserting it.** Stage 1 is a blocking,
outcome-blind corroboration using independent metadata:

| check | requirement |
|---|---|
| C-1 cardinality + composite-key uniqueness in both files | exact |
| C-2 `RNA.SampleID` == `ATAC.sample_id` per joined nucleus | **0 mismatches** |
| C-3 `RNA.cell_type` == `ATAC.cell_type` per joined nucleus | **≥ 0.99** |
| C-4 `RNA.cohort` == `ATAC.cohort` per joined nucleus | **0 mismatches** |
| C-5 raw-barcode collision audit across samples | computed and reported |

C-3 carries a tolerance rather than a zero requirement because RNA-derived and
ATAC-derived cell-type calls are *separate classifications of the same nucleus* and
need not agree perfectly even when the pairing is correct. A value below 0.99 is
evidence against the bridge, not evidence about biology. C-3 is the strongest check
of the five precisely because the two labels come from different modalities.

If it fails: **STOP and escalate for a depositor-provided key.** If it passes, the
verdict is recorded as `PAIRING_QUALIFIED_BY_COMPOSITE_WITH_METADATA_CORROBORATION`
and travels as a *named assumption* in every downstream claim. Corroboration beats
assertion; it is still not a depositor key.

---

## Independent unit and aggregation

**The donor is the independent unit. 357 donors, not 87,384 nuclei.** Every interval
names the donor count behind it, and Kish effective sample size over donors is
reported alongside. Nucleus count is never reported as effective N.

**Primary aggregation: within-donor, RNA-only metacells.** Formed inside each donor
separately by k-means on the first 20 PCs of that donor's microglia RNA matrix
(CP10K → log1p, 2,000 within-donor variable genes), `k = floor(n/25)`, seed
`20260929`. ATAC is then summed over *exactly* the nuclei assigned to each metacell.

A joint RNA+ATAC embedding is forbidden by V63 C8 because it manufactures the
correspondence under test. No ATAC value influences metacell membership.

**The one property worth stating plainly:** an RNA-derived partition can inflate RNA
variance structure. That is not a threat here, because linked pairs and their
matched controls are scored on the *same metacells of the same donors*, so any
partition-induced structure enters both arms identically and cancels. This is
exactly why the primary estimand is a **contrast** and never a raw linked
correlation.

Declared sensitivity arm: donor pseudobulk with donor-level QC residualisation.

---

## What "correspondence" means for one edge

For E2 edge (gene *g*, distal interval *d*), within donor *j*:

**Pearson correlation between the metacell-level RNA value of *g* and the
metacell-level ATAC value of the peak set assigned to *d*, across donor *j*'s
metacells.**

- **RNA**: `.X` counts → metacell sum → CP10K → log1p. The layout is **reversed**
  from normal AnnData — `.X` is count-like uint16 and `raw/X` is log-like float32 —
  so the executor asserts integrality and stops if violated. Genes join on
  `var['gene_ids']` (Ensembl), **never** on the var index, which mixes symbols and
  Ensembl IDs in one namespace.
- **ATAC**: all consensus peaks overlapping the 5 kb distal interval by ≥1 bp are
  summed. No widening, no nearest-peak rescue. Peak count per edge is recorded.
- **Sign**: positive means more accessibility accompanies more RNA. One-sided
  hypothesis: linked > matched control. Fixed now, not flippable later.
- **Zero coverage → MISSING, never zero.** Zero would assert an observed absence of
  correspondence where there was no measurement.

---

## Distance convention

**Primary = source hg19 separation. Sensitivity = harmonized hg38.**

The rationale is recorded prospectively rather than adopted on instruction. E2 audit
item **S28** established that C3 guarantees exact identity per *anchor* but nothing
about the *separation between* a pair's two anchors — the two can fall in different
chain blocks with different offsets. Measured on the 20,709 edges: 89.439% preserved
exactly, 1.154% shifted >1 kb, extremes +395,597 / −344,505 bp, 4 edges left the
source window. The Nott calls, their threshold and the 10 kb–1 Mb window are all
hg19 properties, and the hg19 coordinates reproduce that window to the base pair.
The harmonized value carries transformation error the source value does not, so
matching on it would inject that error into the definition of which units are
comparable.

**No edge is excluded because its hg38 separation leaves the hg19 window.** The 4
such edges are retained; trimming them would be post-hoc retuning against a filter
that was never imposed.

**Controls are placed in hg19 source space** at the matched separation, then lifted
hg19→hg38 under the same frozen liftOver rule — so both arms are treated
identically in coordinate space.

---

## Linked vs control

Promoter-fixed, distal-matched, per V63 C4 (promoters must not move; moving them
destroys activity and degree structure). One control per linked edge, same promoter,
same chromosome, 5 kb wide, source-hg19 separation matched within ±10% or 10 kb
(whichever is larger).

A control must **not** overlap any E2 distal partner of that promoter, must contain
≥1 NIH-CARD consensus peak, must pass the same C3 exact-identity lift, and **must
overlap ≥1 Nott PU.1 peak**. That last requirement matters: E2 edges were *required*
to be accessible, so a control without it would differ from linked edges on
accessibility by construction and the contrast would measure accessibility rather
than linkage.

If no admissible control exists, the linked edge is **trimmed and counted** — never
matched to a distant substitute (V63 C6).

A **second independent control draw** is reserved solely for the control-vs-control
null.

---

## Nuisance adjustment, and the limitation that constrains the claim

The frozen continuous-adjustment estimator is imported **unmodified**: 14 features
(log-distance, degree, promoter activity, distal accessibility, RE density, anchor
frequency, RNA and ATAC depth sensitivity, plus ld², deg², acc², ld·deg, ld·acc,
deg·anc), ridge α=1.0, 5-fold cross-fitting by promoter.

**The out-of-span stress failed.** `V64_FROZEN_STRESS_OUTSPAN_V1` recorded
`OUTSPAN_TECH` margin −0.03211, LCB95 −0.03558, against `M_MIN` 0.010 — while every
other family passed. Interpretation **B** of that contract is therefore in force:
*the estimator is qualified only for nuisance surfaces within or near its frozen
model span.* NIH-CARD correspondence may **not** be called universally
deconfounded.

So the design requires an **outcome-blind span diagnostic** before execution:
standardise NIH-CARD's realised 14 features against the synthetic qualification
run's own mean and SD; report per-feature out-of-range fractions, the centroid
Mahalanobis distance, and the fraction of pairs beyond the synthetic 99th-percentile
radius. Predeclared verdict: `IN_SPAN` if ≤10% exceed that radius **and** every
feature's NIH-CARD IQR sits inside the synthetic range; otherwise `OUT_OF_SPAN`.

`OUT_OF_SPAN` **narrows the claim and is reported**. It does not add basis functions
and does not retune the model. That is the whole point of running it blind.

---

## Measurement support — symmetric, and derived rather than chosen

Every support rule applies identically to linked and control pairs. NIH-CARD support
may never be used to selectively retain linked edges.

| rule | value | derivation |
|---|---|---|
| minimum microglia per donor | 100 | `floor(100/25) = 4` metacells, the minimum for a correlation with more than one residual d.f. |
| target metacell size | 25 | enough aggregated counts for a moderately expressed gene to be non-degenerate at snRNA depth |
| minimum metacells per donor | 4 | same derivation |
| minimum donors per edge | 30 | below this a donor-clustered nonparametric interval is dominated by a few clusters |

From the committed counts, 75 of 357 donors have <100 microglia, so roughly **282
donors** are expected to qualify — the executor must recompute this from
authenticated bytes and report the actual figure. Edges failing the donor minimum
are labelled `LOW_DONOR_SUPPORT` and reported as a **separate stratum**, not
silently dropped, so "no signal" and "no measurement" stay distinguishable.

Results are additionally reported stratified by donor depth quartile and by donors
per edge. Large attrition is a finding about the object and the cohort, not
something to rescue.

**Cohort and depth are confounded** — HBCC 155 donors / median 157 microglia vs
NABEC 202 / median 256.5 — so cohort is never compared naively.

---

## Primary estimand and success criterion

**Δ = the donor-averaged, gene-balanced mean difference between the residualised
correspondence of linked E2 edges and their matched controls.**

Gene balancing — within a donor, the mean over genes of the within-gene mean over
edges — is primary because 3,528 of 5,253 genes carry more than one edge, one carries
68, and 91.7% of edges belong to multi-edge genes. Edge-equal weighting would let a
single high-degree promoter region decide the result. Edge-equal is a declared
sensitivity.

Uncertainty: nonparametric **cluster bootstrap over donors**, 4,000 replicates, seed
`20260929` (matching the frozen P1S configuration). One-sided LCB95.

**PASS requires all of:** LCB95(Δ) > 0; control-vs-control indistinguishable from
zero; worst |SMD| across the 14 features ≤ 0.25; top 1% of donors contributing ≤10%
of the statistic's weight; and the attrition funnel reconciling to 20,709.

**No minimum effect size is imposed, deliberately.** `M_MIN = 0.010` is the frozen
margin for the *synthetic* score scale; transferring it to a real
correlation-difference scale would be a change of units dressed up as a frozen
threshold. Nothing currently frozen justifies a minimum effect on this scale. So the
magnitude is reported without a threshold, and **a statistically positive but
negligibly small Δ must be reported as exactly that, not as biological
confirmation.** `p < 0.05` alone is explicitly not the success definition.

The primary is a **single set-level test**, so no multiplicity correction is needed.
Any edge-level statistic is descriptive only and may not be converted into a success
claim by selecting significant edges.

---

## Interpretation asymmetry, frozen before execution

A **PASS** may support: independent RNA–ATAC correspondence of the Nott-centered E2
object in NIH-CARD microglia, *for the tested nuisance classes only*.

A PASS does **not** support causal enhancer→gene regulation, universal microglia
specificity, disease relevance or AD mechanism, universal hidden-confounder
robustness, independent contact-map replication, or externally defined accessibility
support — E2 remains internally accessibility-restricted within the Nott study.

A **FAIL does not prove E2 is biologically false.** It could reflect aged postmortem
versus surgical/young tissue, cell-state rewiring, sparse ATAC support at 500 bp
peaks, limited donor power, measurement attrition, or a resolution mismatch between
5 kb PLAC-seq anchors and 500 bp peaks. Power, coverage and attrition are reported
with any fail.

Structural evidence (Nott contacts, C3, P1S, P3, E2 construction) and biological
validation evidence (NIH-CARD correspondence) are reported in **separate sections**
and never summed into one score.

---

## Ambiguities I found in the historical contracts

1. **Pairing status conflict** — the brief states the composite bridge is valid; the
   canonical receipt says `QUALIFIED_FOR_PAIRED_USE: false`. Resolved by making it a
   blocking, corroborated, outcome-blind precondition rather than choosing a side.
2. **V63 C4's P1 is not executable here.** It specifies *cross-source* concordance;
   the single-source successor already ruled that `NOT_APPLICABLE` and replaced it
   with P1S. The 10 kb overlap window in C4 therefore has no role in this design, and
   I have not repurposed it as a correspondence window — repurposing a frozen
   parameter into a different test would be exactly the kind of quiet reuse these
   contracts exist to prevent.
3. **V63 C5's accessibility source was never satisfied.** Kosoy remains
   `UNVERIFIED`; E2 uses same-study Nott PU.1. Already recorded in the E2 audit and
   carried here as a claim-scope limitation.
4. **No prospective effect-size threshold exists for a real-data correspondence
   scale.** `M_MIN` is synthetic-scale only. I declined to invent one and instead
   froze the reporting rule above.
5. **The ATAC consensus peak genome build is not stated** in the committed receipt.
   Made an explicit precondition, verified against hg38 lengths taken from the
   already-authenticated chain headers rather than a fresh download.
6. **The local ATAC copy is truncated** (6,059,254,368 of 14,508,702,462 bytes, with
   `curl` exiting 0). Execution requires full-byte md5 verification against the
   Zenodo published digests; the design fails closed on this.

---

## Artifacts

- `results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json`
- `results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_EXECUTION_PLAN_V1.json`
- `scripts/v64/nihcard_e2_outcome_blind_preconditions_v1.py` — stages 0–3 only; it
  contains no code path that pairs a gene's RNA with its distal element's ATAC.

## Stop point

`TRAINING=OFF`. `TD60=BLOCKED`. `Morabito=PROTECTED`. NIH-CARD biological
correspondence **not executed**. Stage 4 requires explicit authorisation after this
design is independently audited.
