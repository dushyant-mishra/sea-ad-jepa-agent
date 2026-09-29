# V61 — frozen construction rule for external regulatory object `E`

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
`9d68b074`. `TRAINING=OFF`. `TD60=BLOCKED`.**

**This document is written and committed BEFORE the downloaded interaction files
are inspected.** The 3.73 GB transfer was started first, because transferring
bytes is not inspecting them; no row of any genome-wide FitHiChIP file has been
read beyond the 300 KB header prefix already reported (5,404 rows of
`GSM4441840`, used only to establish the 25-column schema). Every threshold and
combination rule below is fixed here so that no number in the object can have
been chosen after seeing its effect.

---

## The object

> `E = HiChIP contact edge ∩ Cluster-24 accessible regulatory element ∩
> hg38-stable coordinate identity`

`E` is a set of **coordinate pairs**. It is not a set of genes, and no gene
annotation is joined at construction time. This is deliberate and is what keeps
construction clear of any regulatory molecular outcome.

## Inputs, and nothing else

| input | source | access |
|---|---|---|
| contact | GSE147672 per-GSM `*_H3K27ac.FitHiChIP.interactions.bed.gz`, 12 samples | OPEN_PUBLIC |
| accessibility | `Cluster24.idr.optimal.narrowPeak.gz`, 54,330 unique hg38 intervals | OPEN_PUBLIC |

No other input may enter construction.

## Exclusions, restated and binding

Carried unchanged from the V60 work order:

1. **No co-accessibility edges.** The Cicero layer is a covariance estimator over
   ATAC and is excluded by construction, not by threshold.
2. **No RNA-derived links.** Corces generates no RNA; this is structural.
3. **No target-gene or program-gene selection.** No gene list of any kind touches
   construction.
4. **No disease-locus filtering as a construction criterion.** This is why
   Supplementary Data Set 9 is unusable — it is 100% AD/PD GWAS-conditioned. The
   per-GSM files carry no SNP column at all.
5. **No SEA-AD, Morabito, GSE214979 or GSE272082 measurement** is used to
   instantiate `E`.

## Frozen parameters

### F1 — contact significance

`Q-Value_Bias < 0.01` (column 25 of the FitHiChIP output).

**Primary.** Pre-declared sensitivity arms, to be reported alongside and never
substituted for the primary: `< 0.05` and `< 0.001`.

Rationale for 0.01: it is FitHiChIP's own conventional operating point, external
to this project and chosen without reference to our data. Per the project's
standing rule that a frozen constant needs either an external rationale or a
sensitivity label, this one has the external rationale **and** carries the
sensitivity arms.

### F2 — cross-sample reproducibility, counted in DONORS

An edge must be significant in **≥ 2 distinct donors**.

**Not ≥2 samples.** Four donors contribute two samples each, so a two-sample hit
can be one donor measured twice. Donor is the independent unit throughout this
project and it is the unit here. Pre-declared sensitivity arms: **≥1 donor**
(union) and **≥3 donors**.

The HiChIP donor key is parsed from the sample name under the `A_B` convention
proven for scATAC in Data Set 2 and marked `LIKELY_SAME_KEY__UNPROVEN` for
HiChIP. If that parse is later disproved, F2 must be recomputed; the per-sample
support vector is therefore retained per edge so recomputation needs no re-read.

### F3 — accessibility

**Both anchors** must overlap ≥1 bp of a Cluster-24 IDR optimal peak.

Rationale: `E` is a *regulatory* edge, and a regulatory edge has an accessible
element at both ends. Pre-declared sensitivity arm: **≥1 anchor**.

### F4 — cis only, no self-loops

`chr1 == chr2` and the two anchors are not the same bin. The trans and
self-loop counts are recorded, not silently dropped.

### F5 — no additional distance filter

Whatever distance range FitHiChIP emitted is kept. Distance is **recorded per
edge** because any downstream locus-matched decoy set must match on it, but it is
not used to filter `E`. Imposing a distance window here would be a construction
choice with no external justification.

### F6 — coordinate identity

hg38 on both sides, no liftover, no coordinate transformation. Chromosome naming
must match literally (`chr1`) between the two inputs; a mismatch is a stop, not a
thing to normalise silently. Contact bins are 10 kb; Cluster-24 peaks have median
width 964 bp. The intersection is therefore **peak-within-bin**, and that
asymmetry is a property of the object, not a defect to be papered over.

## What will be reported

Unconditionally, for the primary and every sensitivity arm, with the attempted
count in every denominator:

- edges surviving each stage, as a funnel
- distinct contact bins, distinct Cluster-24 peaks participating
- per-donor support distribution
- cis distance distribution
- trans and self-loop counts (excluded, but counted)
- chromosome coverage

## Stop conditions, declared now

The object is declared **not viable** and the Corces route stops — without
opening Morabito — if any of these holds:

- **S1.** Fewer than 1,000 edges survive the primary rule. An object too small to
  support locus-matched decoys cannot support the benchmark either.
- **S2.** Surviving edges are confined to fewer than 10 chromosomes, which would
  indicate the reproducibility filter is selecting a technical artifact rather
  than a genome-wide signal.
- **S3.** The chromosome naming or genome build cannot be reconciled without a
  coordinate transformation.

These are stated before the counts exist so that a disappointing number cannot be
rescued by relaxing a threshold afterwards.

## Separately: the benchmark is not part of this freeze

`E` is being constructed because it is the right object. The n=18 synthetic
specificity benchmark is a **separate instrument** and is currently **not
citable** for two recorded reasons — its nuisance parameters come from the
atlas-wide stratum rather than the microglial one, and its verdict flips across
simulation knobs. Constructing `E` does not depend on repairing the benchmark,
and repairing the benchmark must not be done by reference to anything learned
from `E`.

## Self-audit

**Starting SHA** `9d68b074`; ending SHA in the commit. **Changed files:** this
document — class **docs**.

**Inspection status at time of writing:** the 12 interaction files are
downloading. None has been read. The only interaction content read to date is the
300 KB prefix of `GSM4441840` already reported, which established the column
header and nothing else. No `Q-Value_Bias` distribution, edge count or overlap
count has been computed.

**Strongest criticism of this freeze:** F2's donor key is inferred from filename
structure rather than proven from a metadata table, so the primary rule rests on
an unproven parse. I have mitigated it by retaining the per-sample support vector
so the rule can be recomputed rather than re-derived, and by labelling it
explicitly — but it remains the weakest link in the specification, and if a
HiChIP sample metadata table exists it should be found and the parse confirmed
before any result from `E` is treated as load-bearing.

**What remains unknown:** everything about the contents. That is the point of
freezing first.
