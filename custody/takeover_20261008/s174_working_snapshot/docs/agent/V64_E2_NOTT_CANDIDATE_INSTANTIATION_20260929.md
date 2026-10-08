# E2_NOTT_CANDIDATE instantiated — 20,709 regulatory edges over 5,253 genes

Mechanical instantiation only, from canonical parent `4af69aeb`. No target was
redesigned, no threshold tuned, no qualification criterion added, and no NIH-CARD
correspondence begun. **Stopping here for independent audit.**

```
E2 edges                     20,709
distinct genes (Nearest Ensembl)   5,253
distinct promoter anchors     7,390
edge table uncompressed sha256
  bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c
```

## All four mandated upstream cross-checks reproduce exactly

| quantity | expected | observed | |
|---|---|---|---|
| original microglia interactions | 104,802 | 104,802 | OK |
| C3 retained | 102,701 | 102,701 | OK |
| P1S source-oriented promoter-distal | 62,890 | 62,890 | OK |
| pre-C3 unique-Ensembl source-side | 61,624 | 61,624 | OK |

The script raises `STOP_UPSTREAM_CROSSCHECK_FAILED` and writes nothing if any of
these misses, so the artifacts cannot exist without all four holding.

Orientation and gene identity are **not reimplemented** — the builder imports the
already-audited P3 executor's functions, so the semantics are provably identical
to the code that produced P3 and, through P3's own cross-check, to the code that
produced P1S. C3 is **not re-run**: the frozen result and per-anchor disposition
are read from canonical, because re-lifting would create a second, differently
derived coordinate set for the same frozen gate.

## Attrition funnel — mutually exclusive, reconciling to the source denominator

| stage | n | % of 104,802 |
|---|---|---|
| `DROP_C3_NOT_EXACT_IDENTITY` | 2,101 | 2.005% |
| `DROP_NOT_SOURCE_ORIENTED_PROMOTER_DISTAL` | 39,811 | 37.987% |
| `DROP_GENE_ENSEMBL_UNRESOLVED` | 2,550 | 2.433% |
| `DROP_DISTAL_NOT_ACCESSIBLE_IN_MICROGLIA` | 39,631 | 37.815% |
| **`E2_EDGE`** | **20,709** | **19.760%** |
| sum | 104,802 | 100.000% |

Derived denominators: C3-qualified 102,701 → source-oriented promoter-distal
62,890 → unique-Ensembl resolved 60,340 → accessibility-qualified **20,709**.

Gene identity is **unique-Ensembl only**. Per P3 self-audit S26, which canonical
ruled must stay fixed, a unique Gene Name is *not* additionally required on the
microglia population — that rule governs only the P3 candidate side, where a
symbol is needed for the GSE73721 join. Gene Name travels as secondary metadata
with its status labelled: 20,675 edges carry a unique symbol, 34 are
`ABSENT_OR_AMBIGUOUS` and are **retained**, exactly as S26 requires.

## Structure of the object

It is a set of **pairs**, not a gene list, and nothing was collapsed:

| | |
|---|---|
| genes with more than one edge | 3,528 |
| edges belonging to multi-edge genes | 18,984 (91.7%) |
| max edges for a single gene | 68 |
| edges per gene | median 2, p75 5, p95 13, mean 3.94 |
| promoter degree (edges per promoter anchor) | median 2, p75 3, p95 8, max 29 |
| contact distance, hg38 | median 155 kb, p25 80 kb, p75 290 kb, p95 620 kb |
| distal PU.1 peaks overlapped | median 1, max 4, mean 1.19 |
| chromosomes | 22 |

## Two structural findings that were not previously recorded

**1. The source interactome contains no sex chromosomes.** E2 covers chr1–chr22
only. This is *inherited*: the deposited Nott microglia interactome itself has no
chrX or chrY rows. No sex chromosome was dropped by any step of this construction.
Recording it so nobody later reads the 22-chromosome coverage as a filtering
artifact.

**2. C3 exact identity does not constrain contact distance — only anchors.**
C3 requires each *anchor* to keep its chromosome, its exact length, and an exact
round trip. It says nothing about the *separation between* the two anchors of a
pair: both can land in different chain blocks with different offsets, so a C3-PASS
pair can still have its contact distance shifted.

Measured across the 20,709 E2 edges:

| | n | % |
|---|---|---|
| distance preserved **exactly** | 18,522 | 89.439% |
| \|change\| ≤ 1,000 bp | 20,470 | 98.846% |
| \|change\| > 1,000 bp | 239 | 1.154% |
| \|change\| > 10,000 bp | 206 | 0.995% |
| exceeding 1 Mb after lift | 4 | 0.019% |
| falling below 10 kb after lift | 0 | 0.000% |

Max increase +395,597 bp, max decrease −344,505 bp. The **hg19 source span is
exactly 10 kb – 1 Mb**, reproducing the frozen contract's recorded cis window to
the base pair; the small out-of-window tail appears only after harmonization.

**Reported only.** No edge was trimmed, no tolerance introduced, and P1S was not
reopened — any of those would be the post-hoc retuning the contract forbids. Both
the source hg19 and lifted hg38 distances are carried per edge so a successor can
condition on either without re-deriving them.

## Scope — what this object is not

Following the successor contract verbatim, `E2_NOTT_CANDIDATE` must **not** be
called an independently replicated contact set, multi-source supported contacts, a
causal enhancer–gene map, proof of universal microglia specificity, independent
cross-study replication, or disease-specific regulation.

P1S established **internal** microglial substrate compatibility against same-study
comparators and the frozen geometry null — not independent replication. P3
established that hard neuron/oligodendrocyte negatives exist where the gene is
expressed in microglia and the distal region is accessible in microglia, yet the
same gene–distal relationship is absent from the qualified microglia map.

### Accessibility-source limitation, stated rather than buried

V63 C5 names **Kosoy** aged primary-microglia ATAC as the intended accessibility
source and records it `UNVERIFIED`, listing Nott ATAC as a *sensitivity* layer. On
this single-source path the successor contract requires only that the chosen
source's bytes and terms be verified, and the already-qualified P1S/P3 path uses
the authenticated Nott PU.1 track — so that is what this build uses.

Because contacts and accessibility then come from the **same study and the same
PU.1-sorted nuclei**, `E2_NOTT_CANDIDATE` does **not** satisfy V63's *"externally
defined microglial accessibility"* wording and must not be described as if it did.
The pre-accessibility population (60,340) is reported, so the unrestricted object
is reconstructible if a verified external accessibility source becomes available.

## P1S density state carried forward unchanged

Primary P1S remains **PASS**. No single local-density operator is authoritative;
the six-definition panel is descriptive and outcome-exposed. Excluding superseded
D6, all reported quartile contrasts remain positive at roughly +0.08 to +0.22.
D1's flatness is **consistent with** offsetting observed-arm and null-arm
dependencies and is *not* a proven arithmetic cancellation of the D2/D3 quartile
trends, because those strata contain different pairs. **No density stratum was
used to select, trim or reweight E2.**

## Self-audit lane (continuing from S27)

**S28 — I found the contact-distance distortion above, and it is a gap in the C3
gate's coverage, not in its execution.** C3 is doing exactly what it was frozen to
do; the point is that "exact identity" is a per-anchor property and readers may
reasonably assume it implies a per-pair one. 10.6% of E2 edges have a shifted
contact distance and 4 leave the source cis window. Recorded, not acted on.

**S29 — my first build reported `worktree clean at start: False`, which was
true but misleading.** `git status --porcelain` counts untracked files, and the
only untracked file was the builder itself. A receipt field that reads "not clean"
without saying why would send an auditor looking for a contamination that does not
exist. Fixed to separate tracked modifications (0, and the script now exits if any
appear) from untracked new files, with the untracked paths listed.

**Examined and clean:** the funnel reconciles to 104,802 exactly; the four upstream
cross-checks are hard tripwires that abort the run; two independent runs of the
builder produced byte-identical output (gzip written with `mtime=0`); no edge was
collapsed by gene; no protected data was opened.

## Artifacts

| path | sha256 |
|---|---|
| `results/v64/V64_E2_NOTT_CANDIDATE_CONSTRUCTION_RECEIPT_V1.json` | receipt |
| `results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz` | `e4c44b9435e7c6e08caca693a718f618c9f9c5f0bc6df227e11c98d9823bb0bb` |
| edge table, uncompressed (authoritative) | `bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c` |

17 columns per edge: source row index, chromosome, promoter side, promoter and
distal hg38 intervals, promoter and distal hg19 intervals, `Nearest Ensembl`,
`Gene Name` and its status, distal PU.1 peak overlap count, and both the lifted and
source contact distances — enough to reconstruct every retained pair and its
lineage.

## Governance

No protected validation data, AD locus list, target registry, NIH-CARD outcome or
Morabito outcome was read, joined or used in any way. `TRAINING=OFF`.
`TD60=BLOCKED`. NIH-CARD correspondence **not started**; target integration **not
started**. `E2_NOTT_CANDIDATE` = `INSTANTIATED_PENDING_INDEPENDENT_AUDIT`.
