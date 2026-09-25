# Can the CRISPRbrain microglia screens be our benchmark truth?

Date: 2026-09-25 · Branch `result/crisprbrain-screen-reliability-20260925`
Producer `scripts/assess_crisprbrain_screen_reliability_v1.py`
Receipt `evidence/crisprbrain_reliability/CRISPRBRAIN_SCREEN_RELIABILITY_RECEIPT_V1.json`

---

## The verdict, in plain language

**No. These two screens cannot be used as the answer key for scoring the model.**

**Is this good news or bad news?** Mixed, and it leans good. It is bad news in
that a data source we hoped to grade the model against will not do that job. It
is good news in that we found out **before** any model was scored against it. If
we had gone ahead, the model would have been marked wrong for failing to predict
numbers that the experiments themselves do not agree on — we would have been
grading an exam whose answer key contradicts itself, and we would have had no way
to tell a genuinely bad model from a bad answer key.

**What does it mean for the project?** One planned use of this dataset is off the
table: CRISPRbrain's two microglia CROP-seq screens cannot supply the
gold-standard "what really happens when you knock down gene X" that a
perturbation benchmark needs. Nothing else in the project is affected. No
training has run against these screens, no result depends on them, and no claim
we have published rests on them. The cost is the plan, not any finished work.

**What is still fine?**

* The data themselves are authentic and intact. Every file's fingerprint matches
  what was recorded when it was downloaded.
* We know exactly *which* genes were targeted and *with which* guide sequences.
  That part of the deposit is solid and stays usable as background information —
  which genes are druggable handles, which were tested — as long as it is never
  used as the scoring key.
* A third CRISPRbrain screen in the identical file format (the "Day 8" screen)
  *does* show that knocking a gene down reduces that gene's own transcript, in
  17 of 39 genes. So the problem is specific to these two screens, not to
  CRISPRbrain, not to the file format, and not to how we measured it.
* The whole analysis is reproducible from a clean checkout and is defended by 24
  adversarial tests, including controls that prove the analysis can detect
  agreement when agreement is really there.

**Three findings worth stating up front, because they change what the word
"disagreement" means here.**

1. **The two screens are not independent experiments.** Same lab, same
   publication, same guide library — the two deposited guide files are
   row-for-row identical — same vector, same starting cell line, same analysis
   pipeline. They differ only in *how* the stem cells were turned into microglia.
   So this was never going to be "two labs checked each other". It is one lab's
   two recipes. That makes their disagreement *more* worrying, not less: if two
   arms that share everything except a differentiation protocol cannot agree,
   nothing looser will.

2. **We cannot show that the knockdowns worked.** In a CRISPRi screen the first
   thing to check is whether switching off gene X actually lowers X's own
   transcript. In the iTF screen that is demonstrated for 3 of 31 genes; in the
   iPSC screen, for 3 of 31; in **both**, for exactly **one** (STAT2). A screen
   that cannot show its own interventions took effect cannot be truth about what
   those interventions do.

3. **Low power is part of the story but not all of it.** Where the two screens
   are compared row by row, a majority of the failures to replicate are
   consistent with one screen simply being too small to see the effect. But a
   substantial minority are formally *inconsistent* — the two estimates are
   further apart than their combined uncertainty allows. And of the 54 rows both
   screens call significant, 50 are formally inconsistent. The deposited data
   cannot fully separate "too weak to see it" from "actively disagrees", and that
   inability is itself a reason not to use the screens as truth.

---

## What was measured, and against what

Five CRISPRbrain microglia tables plus the two deposited guide libraries and the
screen catalogue were verified by SHA-256 before any value was read. The digest
for each screen table is taken of the **decompressed** bytes, so re-zipping a
file cannot satisfy the check.

| input | rows | sha256 of decompressed content |
|---|---:|---|
| `outputs/crisprbrain/iTF-Microglia-CROP-seq-CRISPRi.csv.gz` | 505,527 | `6f65d728699863d207012227c72ac88cc2033cc1277ee6a74132bac8f3afbea8` |
| `outputs/crisprbrain/iPSC-Microglia-CROP-seq-CRISPRi.csv.gz` | 417,630 | `1efd4d840a46f0de32ce7839043df33e07db04d92f826855923e24f8fd36cdd2` |
| `outputs/crisprbrain/iTF-Microglia-CITE-seq-CRISPRi.csv.gz` | 5,270 | `7b97a1098fb6144ba5c053620a18d6ab9d9fcb9fc50cf07124c6e3139c8014c8` |
| `outputs/crisprbrain/iPSC-Microglia-CITE-seq-CRISPRi.csv.gz` | 5,270 | `94cee8ca5ccb24057dcd98226f8fd58472151e6799d3aa7e46491d152f64f412` |
| `outputs/crisprbrain/iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz` | 343,707 | `41eb533dfd50852d0ebd8f2c27d42d5f6bb3b1f1264ab0c721106cfbaed9fc39` |
| `reference/gse335887/GSE335887_itf_feature_reference.csv.gz` | 245 | container `fd2c3fa5b517c81bbd158516dacb00416f1883a654c795e126916620f77f225f` |
| `reference/gse335887/GSE335887_img_feature_reference.csv.gz` | 245 | container `cbc733178cefa49f660e2728debb834eed4520a3691834ba212102b3a0f6c533` |
| `evidence/crisprbrain/crisprbrain_catalog_v1.json` | 54 screens | `1b1cc32aa67cafe2cd2fcb7eb1ff80bf273c96ca38baa7473e272b1c57f2ae56` |

The two committed `.csv.gz` copies in the repo decompress to exactly the SHA-256
values recorded in the acquisition receipt at download time, and to the same
bytes as the loose copies under `/d/jepa_perturb_outputs_20260923/crisprbrain/`.
The 188 MB `__crisprbrain.sqlite` at the project root was opened read-only and is
a `requests-cache` HTTP response store (two tables, `responses` and `redirects`);
it holds no screen metadata of its own and was **not** used as a source.

Every number below was recomputed in this run. None was carried in.

---

## 1. Shared gene identity

**Rule used.** A target's identity is the Ensembl gene ID recorded in the
deposited CRISPR-guide feature reference (`target_gene_id`), joined on
`target_gene_name` — not the display name. Display-name matching is reported
alongside so the two can be compared.

```
targets in iTF-Microglia CROP-seq                          31
targets in iPSC-Microglia CROP-seq                         31
shared by display symbol                                   31
shared by Ensembl-anchored guide evidence                  30
symbols mapping to more than one Ensembl ID                 0
guides per target in the deposited library                  2  (all 30)
non-targeting control guides                                5
the two deposited feature references are identical        yes  (row for row)
```

**The one correction to the "31 shared targets" figure.** `ARID5B` appears as a
target in both analysis outputs but has **no guide sequence in either deposited
feature reference**. It is a name in a results table with no authenticated
intervention behind it. The honest phrasing is *30 authenticated shared targets
plus one unevidenced*. (This matches the repo's existing GSE335887 metadata
identity contract, which reached the same conclusion from the GEO records; it is
independently re-derived here from the two feature-reference files.)

**A limitation that cannot be fixed with the deposited data.** The readout genes
— the ~14,000 genes whose response is measured — are given as **display symbols
only**. No Ensembl, Entrez or HGNC identifier is deposited for them. So the
gene-to-gene join between the two screens has to be done on symbols. Checks that
*can* be run were run and are clean: no case collisions, no Ensembl-style
identifiers mixed in, no whitespace padding, at most 3 version-suffixed symbols
per screen. But symbol matching is what the deposit permits, and that is a
limitation of the deposit, recorded rather than papered over.

```
readout genes measured in iTF                          16,398
readout genes measured in iPSC                         13,936
shared                                                 13,489
iTF only                                                2,909
iPSC only                                                 447
is the smaller set a subset of the larger?                 no
```

The 447 genes measured only in the *smaller* screen show the two universes are
not nested, so the difference is not simply depth.

**No third screen can arbitrate.** The Day-8 iTF screen shares **zero** targets
with either McQuade screen (39 targets, none in common). There is no independent
third measurement of any of these 31 interventions anywhere in the CRISPRbrain
deposit.

---

## 2. Target engagement — did the knockdowns actually work?

For a CRISPRi screen the minimum evidence is: silencing gene X lowers X's own
transcript. That is testable whenever X is itself among the measured readout
genes.

| screen | targets | self-row present | self-log2FC < 0 | **engaged** (FDR<0.05 **and** down) |
|---|---:|---:|---:|---:|
| iTF-Microglia CROP-seq | 31 | 30 | 27 | **3** — DNMT1, MEF2C, STAT2 |
| iPSC-Microglia CROP-seq | 31 | 29 | 27 | **3** — STAT2, ZNF532, ZNF644 |
| **both screens** | 31 | 29 | — | **1** — STAT2 |

**Where engagement is not measurable, stated explicitly.** `POU5F1` has no
self-row in either screen and `SMAD3` has none in iPSC, so engagement cannot be
assessed for those — 2 of 31. The two CITE-seq screens measure 170 *proteins*,
none of which is a target's own transcript, so **target engagement is not
measurable at all in either CITE-seq screen**; that is reported as "0 self-rows",
not as "0 engagement".

**The directional evidence is better than the significance evidence.** 27 of 30
(iTF) and 27 of 29 (iPSC) self-effects point downward, which is the right
direction and is unlikely by chance. What is missing is that they are almost all
far too weak to call: the FDR for most self-rows is exactly 1.0. So the fair
summary is *the guides probably do something, but the screens do not establish
by how much for 28 of 31 genes.*

**The magnitudes also disagree where both are measurable.** Across the 29 targets
measurable in both, the self-knockdown sizes correlate at Pearson **0.062** and
Spearman **−0.010** — no relationship at all. Examples:

```
target    iTF self-log2FC (FDR)        iPSC self-log2FC (FDR)
DNMT1     -1.288  (6.2e-11)            -0.198  (1.00)
ZNF644    -0.128  (1.00)               -2.546  (1.4e-17)
MEF2C     -1.536  (3.5e-03)            -0.718  (1.00)
ZNF532    -0.878  (1.00)               -2.192  (2.0e-02)
STAT2     -1.710  (4.9e-30)            -1.686  (2.1e-03)
RUNX1     -0.075  (1.00)               +1.764  (1.00)
```

STAT2 is the only row where the two screens agree on both the direction and the
size of the knockdown.

---

## 3. Continuous-effect concordance

Significant-hit overlap on its own confuses "the effects disagree" with "the
threshold fell in a different place", so the continuous effect sizes were
compared directly over all 406,118 paired (target × readout gene) rows.

```
pooled Pearson  of log2FC                                0.0723
pooled Spearman of log2FC                                0.0438
pooled sign agreement                                    0.5181   (chance = 0.50)
median per-target Pearson                                0.0277
best  per-target Pearson                                 0.2117   CEBPD
worst per-target Pearson                                -0.0280   ZNF532
per-target Pearson positive / negative                     26 / 5
median per-target sign agreement                         0.5116
```

A correlation of 0.07 means the two screens share about **half of one percent**
of their variance. Direction agreement of 0.518 against a 0.50 coin flip is the
same statement in different units.

**The tiny correlation is mostly not even target-specific.** A label-permutation
control (200 permutations, seed 20260925) pairs each target's profile in one
screen with a *different* target's profile in the other:

```
mean per-target Pearson, correct pairing                 0.0469
mean per-target Pearson, shuffled pairing                0.0257  (sd 0.0049)
permutation p                                            0.005
```

So the correct pairing does beat the shuffled one — the effect is statistically
detectable — but **more than half of an already negligible correlation is shared
structure that has nothing to do with which gene was perturbed**. The
target-specific increment is 0.021 in correlation. That is a real signal and a
scientifically useless one, and both halves of that sentence matter.

**Effects are not even on the same scale.** Median |log2FC| is 0.129 in iTF and
0.379 in iPSC — 2.9× larger — and the regression slope of iPSC on iTF is 0.197,
nowhere near 1. A truth standard whose effect sizes are three times larger in one
arm cannot score a model's predicted magnitudes.

### Significant-hit overlap, and the threshold that produced it

```
FDR cut   sig iTF   sig iPSC   both   iTF->iPSC   iPSC->iTF   sign agr (iTF sig)   sign agr (both sig)
0.05          854      2,011     54      0.0632      0.0269               0.5187                0.3889
0.10        1,000      2,580     72      0.0720      0.0279               0.5180                0.4583
0.25        1,336      4,162    128      0.0958      0.0308               0.5225                0.5000
```

54 jointly significant rows is 12.8× more than the 4.2 expected if the two
screens were independent (hypergeometric p = 5.6e-41). That is the *only*
statistic in this report that looks favourable, and the next line destroys it.

**All of the apparent overlap is one target.**

```
jointly significant rows by target:   ZNF644  50 · ZNF532  3 · STAT2  1
targets contributing any jointly significant row:      3 of 31
targets contributing none:                            28 of 31
largest single target's share:                         92.6%
```

And ZNF644 — the target supplying 50 of the 54 rows — has a per-target profile
correlation between the two screens of **0.0016**. Its two response profiles are
uncorrelated. The overlap is not a weak broad signal; it is one gene, and even
that gene's two profiles do not resemble each other.

**Among the rows both screens call significant, they mostly point opposite
ways.** Sign agreement is **0.389** at FDR<0.05 — 33 of 54 rows have opposite
signs. The Pearson among those same rows is +0.475, which looks contradictory
until you see that it is carried by a handful of large concordant rows (STAT2's
own self-row at −1.71 vs −1.69, plus two large ZNF644 rows) while the majority of
smaller rows disagree. The magnitudes among the *sign-agreeing* joint rows still
differ by 5.7× (median |log2FC| 0.152 in iTF vs 0.872 in iPSC).

---

## 4. Power — is this disagreement, or just too few cells?

**What the deposit does not contain, stated plainly.** There are no per-target
cell counts, no per-target guide counts and no per-cell detection rates anywhere
in any deposited CRISPRbrain table. Those quantities are recorded in the receipt
as `NOT_DEPOSITED` / `UNMEASURED_NOT_IN_DEPOSIT`. They were **not** estimated.

**What the depositors state in their own prose** (read verbatim out of the
authenticated catalogue; these are their claims, not our measurements, and no
statistic in this report is derived from them):

```
                                iTF-Microglia        iPSC-Microglia
cells with a single sgRNA              23,826                 8,349
mean reads per cell                     8,975                 2,870
median genes per cell                   3,150                 1,400
10x chemistry                              v3                    v2
harvest day                                12                    28
```

The iTF arm has ~2.9× the cells and ~3.1× the depth. If power were the whole
story, iTF would find more hits. **It finds fewer** — 854 against 2,011 at
FDR<0.05. The two screens' significance columns are therefore not on a common
scale, and cannot be compared as if they were.

**What can be measured from the deposit.** Each screen's own p-value implies a
standard error for each effect: for a two-sided z-test,
`SE = |log2FC| / Φ⁻¹(1 − p/2)`. This reconstruction was **validated before being
used**: on well-determined rows the implied SE must fall as the gene's abundance
rises, and it does, at Spearman −0.768 (iTF, 4,510 rows) and −0.689 (iPSC, 17,735
rows). With SEs in hand, every paired row can be tested for whether the two
estimates actually differ:
`z_diff = (β_iPSC − β_iTF) / √(SE_iTF² + SE_iPSC²)`, disagreement at |z| > 1.96.

```
rows significant in iTF but not iPSC                         800
   consistent with iTF, i.e. iPSC underpowered               577   (72.1%)
   formally inconsistent                                     223   (27.9%)

rows significant in iPSC but not iTF                       1,957
   consistent with iPSC, i.e. iTF underpowered               781   (39.9%)
   formally inconsistent                                   1,176   (60.1%)

rows significant in BOTH screens                              54
   consistent                                                  4
   formally inconsistent                                      50   (92.6%)
```

**Reading this honestly.** Most iTF-only hits (72%) *are* explainable as the
iPSC arm being too small to see them — power is a real contributor. But the
reverse direction is dominated by genuine inconsistency (60%), and nearly every
row the two screens *both* call significant is formally inconsistent. Both
mechanisms are operating. Because the deposit withholds the cell- and
guide-level counts, the two cannot be fully separated, and the correct statement
is: **this deposit does not permit the separation, and either mechanism alone
disqualifies the pair as a truth standard.**

One further calibration note, reported descriptively and not as a conclusion:
the median |z| implied across all rows is 0.255 (iTF) and 0.433 (iPSC), both
*below* the 0.674 expected under a correctly calibrated null. Both tests are
conservative overall, and unequally so. This statistic cannot separate a
conservative test from an absence of signal and must not be read as evidence of
either; it is reported because the two screens differ on it, which is one more
reason their FDR columns are not interchangeable.

---

## 5. Is the concordance a function of baseline expression?

Yes, and the effect is far too small to rescue anything.

```
mean log2CPM bin    rows    Pearson   sign agr   frac sig iTF   frac sig iPSC   frac sig both
<0.5             163,299     0.0605     0.5214       0.000239        0.001831        0.000000
0.5-1             72,499     0.0583     0.5161       0.000952        0.003807        0.000000
1-2               78,053     0.0636     0.5151       0.001627        0.005778        0.000090
2-3               38,690     0.0795     0.5139       0.004006        0.007961        0.000129
3-4               22,053     0.0647     0.5182       0.005623        0.011291        0.000272
4-5               12,015     0.1029     0.5094       0.009488        0.014482        0.000416
>5                19,509     0.0848     0.5226       0.011584        0.013020        0.001589
```

Concordance does rise with abundance (Spearman across bins 0.893). But it rises
from 0.060 to 0.085. **Even among the best-expressed genes in the transcriptome
the two screens correlate at 0.085.** Low expression is not the explanation.

Baseline abundance itself agrees far better than the effects do — log2CPM
correlates at Pearson 0.826 / Spearman 0.798 across all 406,118 paired rows. The
two screens agree about *what is expressed* and disagree about *what happens when
you perturb it*, which rules out a gross gene-identity or join error as the
cause.

**But the target genes themselves are a different story.** Across the 29 targets
measurable in both, baseline abundance correlates at only Pearson 0.222 /
Spearman 0.511, with differences of several log2 units:

```
gene     iTF log2CPM    iPSC log2CPM
SPI1            0.15            6.10
MEF2C           0.92            4.12
STAT1           8.06            0.78
MAF             7.87            3.84
ZNF644          3.92            0.39
```

The two differentiation protocols produce cells in which the *perturbed genes
themselves* sit at very different expression levels. No mechanism is asserted
here — the deposit does not contain what would be needed to attribute this
between protocol, differentiation age, chemistry and depth, all of which change
together. The measurement stands; the cause does not.

---

## 6. Are the two screens independent? No.

This is the finding that reframes everything above, and it is the answer to the
question the task asked us to check: **the GSE178317 CRISPRbrain comparison is
the depositors' own analysis of the same experiment rather than independent
replication — is the same true of the iTF/iPSC pair?** It is, in a slightly
different way, and the answer is nearly as weak.

| | iTF-Microglia CROP-seq | iPSC-Microglia CROP-seq |
|---|---|---|
| lab | Kampmann (UCSF) | Kampmann (UCSF) |
| reference | McQuade et al. 2026 | McQuade et al. 2026 |
| library | 31 TFs / transcriptional regulators | 31 TFs / transcriptional regulators |
| deposited guide file | **identical row for row** | **identical row for row** |
| vector | CROP-seq pMK1334 | CROP-seq pMK1334 |
| parental line | WTC11 | WTC11 |
| starting material | CRISPRi iPSCs | CRISPRi iPSCs |
| controls | non-targeting sgRNA | non-targeting sgRNA |
| analysis | modified Mixscale | modified Mixscale |
| **differentiation** | **six-TF dox-induced, Day 12** | **cytokine-directed, Day 28** |
| chemistry / depth | 10x v3, ~8,975 reads/cell | 10x v2, ~2,870 reads/cell |

Everything is shared except the differentiation route — and the differentiation
route is confounded with harvest age, 10x chemistry and sequencing depth, which
all change together and cannot be separated.

**Why this matters for the word "concordance".** Two arms that share a lab, a
library, a vector, a cell line, a control design and a pipeline should agree
*better* than genuinely independent replicates, because every shared step removes
a source of variation. Agreement between them would therefore have been weak
evidence of reproducibility. **Disagreement between them is strong evidence
against it.** We observe disagreement.

The library was re-derived here from the two deposited feature-reference files:
245 features, 65 distinct protospacers, 30 targeting genes at exactly 2 guides
each, 5 non-targeting controls, and the iTF and iMG files identical row for row.
The WTC11 parental-line statement is **cited** from this repo's existing
GSE335887 metadata identity contract (sourced from GEO SOFT records); no GEO
access was made in this run, and the receipt marks that one line as cited rather
than measured.

**Two guide-support facts that bound what the screens could ever have shown.**
Each target carries **2 guides**. There are **5** non-targeting controls. Two
guides per gene is the floor for a CROP-seq design; it leaves no room to check
whether the two guides for a gene agree with each other, which is the
within-screen version of the question this whole report is about. The deposit
does not carry per-guide results, so that check is **not possible** here.

**Number of independent differentiation preparations per model: UNMEASURED.** It
is not in the deposit. Without it we cannot say whether the two arms are two
biological preparations or two aliquots, and therefore cannot say what the
effective sample size of either arm is.

---

## 7. Do the two screens share cells, a library, or a pooled analysis?

```
paired CROP-seq rows compared                             406,118
rows with bit-identical log2FC                                  0
rows with log2FC within 1e-12                                   0
paired CITE-seq rows compared                               5,177
rows with bit-identical log2FC                                  0
```

The two deposited tables are genuinely separate numerical outputs — this is not
one analysis served twice under two names. That rules out the most trivial
explanation for any apparent agreement, and it does **not** make them independent
experiments; see §6.

One observation on the CITE-seq pair worth recording: both tables have exactly
5,270 rows and 170 protein features, but only **5,177** (target, protein) pairs
join, so the two protein panels are not identical despite the identical shape.
And the deposited catalogue description for `iPSC-Microglia-CITE-seq-CRISPRi`
states the **iTF** differentiation method (six-TF dox-induced) while the
matching CROP-seq entry states the cytokine-directed method, and repeats the
iPSC CROP-seq analysis numbers verbatim. The deposited metadata for the CITE-seq
screens is internally inconsistent. This is reported as an observation about the
deposit's documentation; no CITE-seq statistic in this report depends on it.

---

## Controls — why you should believe the null result

A report that finds "no agreement" has to show it could have found agreement.

**Positive control 1 — the analysis detects perfect agreement.** Comparing the
iTF screen to itself: Pearson 1.0000, Spearman 1.0000, sign agreement 1.000 over
505,527 rows.

**Positive control 2 — the schema can demonstrate engagement.** The Day-8
CROP-seq screen, an identical six-column CRISPRbrain table from the same portal:
39 targets, 35 with a self-row, **17 engaged (43.6%)** against 3/31 (9.7%) in the
iTF screen. So the engagement test works, and the low engagement in the McQuade
pair is a property of those screens rather than of our definition.

**Positive control 3 — the verdict is not hard-wired.** The verdict is computed
from five stated criteria. Fed a fixture of screens that agree, are engaged and
are independent, the same function returns **YES**; fed a fixture where only a
subset qualifies, it returns **ONLY_FOR_THIS_SUBSET**. Both are covered by tests.
On the real data it returns NO with **0 of 5** criteria passed.

**Negative control.** Two independently simulated screens score |Pearson| < 0.10
and sign agreement within 0.05 of chance — the behaviour we observe on the real
pair.

**Permutation control.** Described in §3; the observed concordance is compared
against a shuffled-target null rather than against zero.

### The five criteria and the result

| criterion | requirement | observed | pass |
|---|---|---:|---|
| C1 engagement | ≥ half of shared targets engaged in both screens | 0.032 (1/31) | no |
| C2 profile concordance | median per-target Pearson ≥ 0.30 | 0.028 | no |
| C3 direction | pooled sign agreement ≥ 0.70 | 0.518 | no |
| C4 breadth | ≥ half of targets contribute a jointly significant gene | 0.097 (3/31) | no |
| C5 independence | the two screens are independent experiments | false | no |

**Threshold provenance, stated honestly.** These cuts were chosen *after* the
statistics were computed. They are `POST_HOC_DESCRIPTIVE`, not a prospective
freeze, and they are recorded so the verdict is reproducible — not because they
carry independent authority. The verdict does not depend on where they sit: the
highest per-target correlation observed anywhere is 0.2117, so C2 fails at any
threshold above that; joint engagement is 1 of 31, so C1 fails at any threshold
above 0.032; and C5 is a fact about the experimental design, not a measurement.

**Is there a usable subset?** A target would qualify only if it is engaged in
both screens **and** its two response profiles correlate at ≥ 0.30. **Zero
targets qualify.** STAT2 is engaged in both but its profiles correlate at 0.051;
CEBPD has the best profile correlation (0.212) but is engaged in neither. So
"only for this subset" was genuinely available as an answer and the data did not
support it.

---

## The preliminary numbers, checked

Every figure carried into this task was treated as a claim and recomputed. Four
of seven disagreed, and **all four disagreements have the same single cause**.

| claim | reported | recomputed (FDR<0.05) | verdict |
|---|---:|---:|---|
| shared targets | 31 | 31 by symbol, **30 Ensembl-anchored** | confirmed, with correction |
| overlap iTF→iPSC | 0.072 | **0.0632** | discrepancy — explained |
| overlap iPSC→iTF | 0.028 | **0.0269** | discrepancy — explained |
| sign agreement among iTF-significant | 0.52 | **0.5187** | confirmed |
| joint sign agreement | 0.458 | **0.3889** | discrepancy — **worse** than reported |
| jointly significant rows | 72 | **54** | discrepancy — explained |
| jointly engaged targets | STAT2 only | **STAT2 only** | confirmed |

**Root cause.** The preliminary figures were computed at a **10% FDR** cut; this
report's headline figures use 5%. Every discrepant value is reproduced *exactly*
at the looser cut — 0.0720, 0.0279, 0.4583 and 72 — so the disagreement is a
threshold difference, not an arithmetic error. Both cuts are in the receipt.

Note the direction: **the looser cut flatters the screens.** At the stricter,
conventional 5% cut, both the overlap and the sign agreement are worse, and the
joint sign agreement drops to 0.389 — meaning the two screens point in *opposite*
directions on 33 of the 54 rows they both call significant. The corrected
numbers strengthen the verdict rather than softening it.

---

## What we recommend

1. **Do not use these two screens as benchmark truth**, jointly or singly, for
   scoring perturbation predictions.
2. **Do not treat agreement between them as replication** in any future write-up.
   They share everything but the differentiation protocol.
3. **Keep using the deposit for identity**: which genes were targeted, with which
   guide sequences, in which cell models. That part is authenticated and sound.
   Treat `ARID5B` as unevidenced until its guides are sourced from the
   publication's Table S2.
4. **Consider the screens as a negative control for the benchmark.** A model that
   reproduces these tables closely is fitting their noise, and that is worth
   knowing.
5. **Do not attempt a rescue by loosening thresholds.** The threshold-sensitivity
   table shows exactly what loosening buys: at FDR<0.25 the joint sign agreement
   reaches 0.500, which is a coin flip.

---

## Blocked, and the exact missing source

* **Per-target cell counts, per-target guide counts, per-cell detection.**
  `NOT_DEPOSITED` in any CRISPRbrain table. Exact missing source: the per-cell
  guide-assignment matrices behind GSE335887 (the `.h5mu` / `.h5ad` /
  `feature_bc_matrix.h5` assets, which are listed on the FTP directory and have
  not been downloaded). With those, power and disagreement could be separated
  properly instead of bounded through implied standard errors.
* **Per-guide results.** Not deposited. Guide-to-guide agreement within a screen —
  the within-screen version of this report's question — cannot be assessed.
* **Number of independent differentiation preparations per model.** Not in the
  deposit. Exact missing source: the publication's methods or a per-sample
  metadata table distinguishing preparations from aliquots.
* **`ARID5B` protospacers.** Absent from both feature references. Exact missing
  source: Table S2 of McQuade et al.
* **A third, genuinely independent measurement of these 31 interventions.** None
  exists in CRISPRbrain; the Day-8 screen shares zero targets.

---

## Reproducing this

```
python analysis/therapeutic_perturbation_etl/scripts/\
assess_crisprbrain_screen_reliability_v1.py --repo .

python -m pytest analysis/therapeutic_perturbation_etl/scripts/tests/ -q

python analysis/therapeutic_perturbation_etl/scripts/\
reproduce_crisprbrain_screen_reliability_v1.py --repo .
```

The reproducer reads the committed receipt, creates a git worktree at the commit
that receipt says it ran from, refuses to proceed unless that worktree is clean
and its HEAD matches, checks the producer file's SHA-256 against the receipt, runs
it, and then compares every output CSV digest and every scientific field of the
receipt. The receipt records `git_dirty: false` and the anchor commit, so the
result is bound to a commit rather than to a working directory.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
