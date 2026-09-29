# V60 — Data Set 9 authentication, and the honest benchmark verdict

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
`79c40f89`. `TRAINING=OFF`. `TD60=BLOCKED`. No regulatory molecular outcome
opened. No protected readout touched. Nothing was joined to any gene.**

Two findings, both negative, both load-bearing. Neither is a failure of the
biology; both are failures of things I had assumed rather than checked.

---

## Finding 1 — Supplementary Data Set 9 **cannot instantiate the frozen object**

The frozen object is

> `E = HiChIP contact edge ∩ Cluster-24 accessible regulatory element ∩
> hg38-stable coordinate identity`

frozen with the exclusion, stated before any target inspection: **no
disease-locus filtering as a construction criterion.**

Data Set 9's HiChIP sheet says, verbatim, in its own banner:

> "This page of the table shows the FitHiChIP loop calls **that overlap SNPs
> derived from analysis** of H3K27ac HiChIP data."

and its own column dictionary defines the flags, verbatim:

> `Anchor1_hasSNP` — "A boolean variable determining whether the first anchor
> overlaps a SNP from **our AD/PD GWAS analysis**."

Counted rather than inferred:

| quantity | value |
|---|---|
| HiChIP rows distributed | **11,542** |
| rows where ≥1 anchor overlaps an AD/PD GWAS SNP | **11,542 — 100.00%** |
| rows where **neither** anchor overlaps a GWAS SNP | **0** |
| rows where both anchors do | 2,839 (24.60%) |
| loops the paper describes genome-wide | 833,975 |
| **fraction of the described map distributed here** | **1.384%** |

Same on the other sheet: 9,795 Cicero rows, 100% SNP-overlapping, 0.347% of the
described 2,822,924.

**There is no admissible row filter.** The work order anticipated "the admissible
HiChIP rows need to be selected by method/type", and that part is easier than
expected — HiChIP and Cicero are separated **by sheet**, so no method selector is
needed at all. But disease-locus conditioning is not a column you can filter
**out**; it is the table's **inclusion criterion**. Every row is present
*because* of a GWAS overlap. Filtering to the unconditioned rows leaves zero.

**What this is not.** This is not a finding that the Corces HiChIP experiment is
disease-selected. It is genome-wide, and the donors are cognitively healthy —
P6 in the V60 rubric still stands for the *study*. It is a finding about the
**distributed artifact**: Data Set 9 publishes the GWAS-overlapping excerpt, not
the map. That is exactly the distinction my own standing note required me to
check — confirm that the distributed object is the one the paper describes, "not
symbol-filtered or disease-locus-filtered" — and here it is not.

**What is NOT yet blocked.** The 833,975 genome-wide loops may be distributed
somewhere else that is fully public — `GSE147672_RAW.tar`, another GEO
supplementary file, or another Data Set in this series. **I have not checked, and
I am not assuming it either way.** The Corces route is blocked *through Data Set
9*; whether it is blocked *entirely* is an open, answerable, DUA-free question.

### Incidental structural facts, recorded because they will matter if the
### genome-wide set is found

- HiChIP anchors are **uniform 5,001 bp bins**, not peaks. They are FitHiChIP
  bin-pairs. Intersecting them with Cluster-24 peaks is a bin↔peak overlap, not
  an identity join.
- Cis spans: min 15 kb, **median 105 kb**, max 1.95 Mb. 22 chromosomes.
- `Score` is −log10(q) from FitHiChIP, range 1.000 – 163.536.
- The Cicero sheet carries `Peak_ID` values (`sc_18453`) described as "unique
  number that identifies the peak **across supplementary tables**". A stable
  cross-table peak key exists in this supplement series. **The HiChIP sheet does
  not carry it.**

---

## Finding 2 — the V60 benchmark is **NOT a pass**, and my rule was defective

The first run printed `PASS_AT_N18`. It must not be read as a pass, for three
reasons. The first is mine.

**(a) The frozen rule was missing its second condition.** The work order said
"retain the semantic twin as an explicit impossibility boundary." I implemented
the twin as a *reported arm* and then wrote a verdict that checked only
`margin > 0`. A boundary that the verdict does not consult is not a boundary.
The rule is now two conditions, and condition B is new:

```
(A)  q10(min mandatory POS) - q90(max NEG) > 0      at n=18
(B)  twin_median < q10(min mandatory POS)           at n=18   <- was missing
```

This tightening is recorded in the script's own docstring and in its JSON output
(`frozen_rule_repair`) rather than silently applied, because a rule changed after
a run has to be auditable **in the direction it moved**. It moved toward
strictness, and it flips the script's own earlier result from PASS to RED.

**(b) The twin fails on the original numbers.** At n=18 the contact-aware
nuisance twin sat at **+0.03233** against a positive floor of **+0.03138**. The
twin is *above* the floor. A purely technical latent, handed the same external
contact graph, scores at or above the genuine positives — so the design does not
separate biology from nuisance-with-the-same-information.

**(c) The margin is inside noise and non-monotonic.**

| n | margin | |
|---|---|---|
| 9 | +0.03548 | |
| 12 | **−0.00656** | **RED** |
| 15 | +0.00639 | |
| 18 | +0.00561 | decisive |

A sequence that crosses zero and comes back is the same wobble the V57
donor-count diagnostic showed, and the project's standing rule — "do not
reinterpret the near miss as qualification" — applies directly. A +0.006 margin
at the decisive n, below the n=9 value, is not a separation.

**Governing consequence:** the user's instruction was "if it fails, we should
stop the Corces route without opening Morabito." Between Finding 1 and Finding 2,
**Morabito stays closed.**

---

## Finding 3 — the one positive result: microglial depth is fine

Data Set 2's `scATAC Cluster Residence` sheet resolves V60 open item 1.

**Cluster 24 = "Microglia" = 4,655 cells, 6.59% of the atlas.** Present in
**all six donor tokens** (03: 651, 04: 380, 06: 779, 09: 1,275, 11: 415,
14: 1,155), min/max ratio 3.36×, across all six regions.

**Cross-validation that the sheet is authentic:** summing the sample columns over
all 24 clusters gives **70,631** — exactly the cell count in the GEO barcodes
file. Data Set 2 and the distributed barcodes describe the same cells.

Combined with the 54,330 unique hg38 Cluster24 intervals already measured, the
accessibility half of `E` is adequate. **Accessibility was never the blocker.**

### Self-audit S-V60-1: I first reported 9,310 and it was wrong

My first pass summed every column after `Cluster_Description`. The sheet has a
**`Total` column**, so I added the row's own total to its parts and exactly
doubled the count. Caught immediately because the atlas-wide sum came to 141,262
= 2 × 70,631, and 70,631 was independently known from the barcodes file.

Same family as the barcodes header off-by-one earlier in V60: **a spreadsheet
whose column semantics I assumed instead of reading.** Twice in one workstream.
The check that caught it both times was tying the derived number to an
independently known quantity — that is the habit worth keeping, not the
inspection.

---

## Where the Corces route now stands

| item | status |
|---|---|
| Cluster-24 microglial depth | **RESOLVED — adequate** (4,655 cells, 6/6 donors) |
| Data Set 9 as the contact source | **BLOCKED — 100% GWAS-locus-conditioned** |
| Genome-wide 833,975 loops, public elsewhere? | **UNCHECKED — the live question** |
| UW / SEA-AD source-institution overlap | **UNRESOLVED — carried** |
| n=18 synthetic specificity benchmark | **RED** under the repaired rule |
| Morabito | **CLOSED. Not opened.** |

The honest summary is that the Corces object failed on **artifact availability**,
not on biology, and that the benchmark would not have licensed it anyway.

## Self-audit

**Starting SHA** `79c40f89`; ending SHA in the commit. Branch/worktree as above.
**Changed files:** this document, `results/v60/V60_CORCES_DS2_DS9_AUTHENTICATION_V1.json`,
`scripts/v60/corces_external_contact_specificity_benchmark_v1.py`,
`results/v60_rulefix/` — classes **docs**, **results**, **code**.

**Inputs:** two user-supplied public XLSX files, digests recorded in the JSON.
Both are the published Nature Genetics supplement, `OPEN_PUBLIC`. No controlled
data requested or downloaded.

**Protected outcomes opened: NO.** No gene symbol, Ensembl ID, target gene,
program gene or Stage75F edge was read, joined or enumerated from either
workbook. The only content read from Data Set 9 was coordinates, widths, scores
and the two boolean SNP flags — the flags were **counted**, and no SNP identity,
locus name or gene was resolved.

**Provenance of the two runs — corrected before commit.** I first wrote here
that the defective-rule run's JSON was preserved at
`results/v60/V60_EXTERNAL_CONTACT_BENCHMARK_V1.json`. **That file does not exist
anywhere on disk**, and I confirmed this by searching the worktree and the
session scratchpad before committing. The first run's only surviving record is
its console output, transcribed verbatim in the margin table above; the run
either wrote to a scratch location since cleaned, or never reached its write
step. The claim was wrong and is retracted rather than quietly deleted, because
this is the exact class of defect the project's provenance rule exists for: an
artifact asserting a preservation that did not happen.

The **repaired** run writes to `results/v60_rulefix/` and that output is real and
committed. It executed **from the working tree, not from a committed head** —
`git status` was not clean when it started. The file that actually executed has
SHA-256 `667a2ee5f4dda72371b0ce7675749ec63bef97493efc04b2f6d38ff74f2830ee`, and
that digest, not the branch, is what identifies the code behind the numbers. The
script's own `STOP_OUTPUT_EXISTS` guard is what forced the separate output
directory — it fired on the first attempt to write into `results/v60/`.

**Strongest alternative explanation for Finding 1:** that Data Set 9 is simply
the wrong supplementary file and the full map is one file away, making this a
navigation error rather than a finding. Possible, and that is precisely why the
verdict is scoped to "cannot instantiate **from Data Set 9**" and the
genome-wide question is left explicitly unchecked rather than declared closed.

**Strongest criticism of my own work here:** the twin condition should have been
binding in the first implementation — the work order said so plainly, and I read
it, and I still wrote a verdict that ignored it. The benchmark ran and printed a
PASS that a reviewer glancing at the verdict field would have believed. It was
caught by my own reading of the arm table before it was reported, but the
artifact on disk said `PASS_AT_N18`, and that is the more honest way to describe
how close this came to being wrong.

**What remains unknown:** whether the 833,975 genome-wide loops are publicly
distributed anywhere; whether Corces UW donors overlap SEA-AD at the person
level; whether any admissible external contact object exists that clears both
conditions of the repaired rule.
