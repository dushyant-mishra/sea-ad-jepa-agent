# Audit handoff — perturbation ETL, 2026-09-24 (Claude lane)

Branch `analysis/perturbation-etl-gse301119-claude-20260923`, head at time of
writing `49c64d77`, rebased onto your merges of PRs #82, #87, #89, #97, #98.

This document exists to be attacked. It states what was claimed, what backs each
claim, and — in the section headed **Weak points I am flagging myself** — the
places where I think the work is most likely to be wrong. Start there.

---

## 1. What changed, in one paragraph

Two GEO studies had been recorded as STOP on 2026-09-23 because their deposited
assets contained no per-cell sgRNA assignment. Both STOPs were reached by
checking only the processed GEO deposit. Re-examining the raw archives and the
papers' supplementary material overturned one of them and re-founded the other
on different evidence. Separately, the CRISPRbrain data commons was acquired for
the first time, and the collection's overlap with the FULL104 training corpus was
measured for the first time.

## 2. Commits, in order

| sha | subject |
|---|---|
| `ab0b5dae` | Recover GSE178317 guide identity from SRA; stage GSE175721 guide reference |
| `c2b018b8` | Add GSE178317 intervention-effects producer |
| `73bd25ad` | GSE175721: STOP stands, but on correct and specific grounds |
| `4aa99089` | Add CRISPRbrain acquisition producer with FULL104 overlap check |
| `f2909380` | Measure the perturbation benchmark against the FULL104 training corpus |
| `518a24ee` | GSE178317 recovery: guide reads PASS, cell assignment FAILED (10 of 58,302) |
| `662639f6` | GSE178317 v2: split count from call, replace share rule with a background model |
| `1a17270b` | Add auditable receipts for the v1 failure and the training-overlap measurement |
| `a59a87a4` | Acquire CRISPRbrain: 54 screens, 352 targets, 4.7M measurements |
| `49c64d77` | v2: producer states its own usability verdict instead of exiting 0 on a dud |

Producer digests at `49c64d77`:

```
recover_gse178317_guide_assignments_v1.py   69bc14ed510d0847...
recover_gse178317_guide_assignments_v2.py   3aa48c6ed33445e5...
build_gse178317_intervention_effects_v1.py  286e6c1fdfd268d2...
acquire_crisprbrain_screens_v1.py           9d9b9caa0eace032...
measure_benchmark_training_overlap_v1.py    e4e63667d510914c...
```

## 3. GSE178317 — STOP overturned at the read layer, assignment failed then repaired

**The 2026-09-23 STOP was correct about the deposit and wrong about the
experiment.** `filelist.txt` for the series matches the acquired assets exactly,
so nothing was missed at download time, and the deposited sgRNA-enrichment
matrices really do carry 33,538 Gene Expression features and zero guides,
because the submitters ran Cell Ranger on the enrichment libraries against the
plain transcriptome. What the STOP missed:

- **The library.** Supplementary Table 5 of Draeger et al. 2022 (Nat Neurosci,
  PMID 35953545) lists all 81 sgRNAs: 39 target genes plus 4 non-targeting, every
  protospacer 20 nt, all unique, all ACGT. Staged at
  `reference/GSE178317_sgrna_library_suppl_table5.csv`, sha256
  `8de1e7e737c8c42ec9a7feff0d6e198b4f09808f09b6238e8b9dfbe276774942`.
- **The barcode read.** SRA stores 127 bases per spot for the enrichment runs:
  8 nt i7, **28 nt cell barcode plus UMI**, 91 nt guide read. The barcode read is
  flagged `TECHNICAL`, which is why the ENA-derived FASTQ serves only 91 bases
  and appears barcode-free. Verified with
  `vdb-dump SRR14828091 -R 1 -C SPOT_LEN,READ_LEN,READ_TYPE`.

**v1 run** (from committed `ab0b5dae`, clean worktree, 47m02s,
2026-09-24T15:13:15Z→16:00:17Z):

```
spots read                  221,434,278
reads on called cells       190,036,621
reads carrying a guide      174,012,015  (91.6%)
guide UMIs after dedup       18,006,495
cells with >=1 guide UMI         54,950  of 58,302
distinct guides                   81/81  in every lane
cells assigned                       10  <-- FAILURE
```

`gex_called_cells` sums to **58,302**, exactly the authors' published figure.
That is an independent check on lane wiring and cell sets.

**Why it failed.** The rule required the top guide to hold ≥70% of a cell's guide
UMIs. These are enrichment libraries built by hemi-nested PCR, which amplifies
ambient guide transcripts, so a typical cell carries ~354 guide UMIs spread
across the whole 81-guide library and nothing approaches a 70% share. The rule
was imported from GSE311359, where direct guide capture makes it appropriate. The
defect is the transfer, not the threshold value. **I did not retune the
threshold**; the pre-declared sensitivity grid in the v1 receipt shows 10 at the
loosest declared point and 0 at the operating point.

**v2** (`662639f6`, hardened at `49c64d77`) changes the method, not the constant:

- `--stage count` persists the cell × guide UMI matrix; `--stage call` assigns.
  v1 conflated them, which is why the defect survived to a full 47-minute run.
- Assignment requires **agreement of two statistics**: a per-guide robust z-score
  of the cell fraction against a median/MAD background, and a Poisson tail test
  against an ambient expectation of cell depth × the guide's share of all guide
  UMIs. Exactly one guide must pass both. This mirrors the authors' stated use of
  demuxEM plus the Tian et al. 2019 z-score cutoff.
- Smoke run over 0.27% of reads: 4,223 cells, 38 of 39 targets, 40 multiplets.
  Sensitivity across z∈[3,10]: 4,597 → 1,392. Compare v1's grid, 10 → 0.

**Status: the full count stage is running at the time of writing.** No v2
assignment against full data exists yet. Do not treat the smoke numbers as a
result.

## 4. GSE175721 — STOP stands, re-founded

Earlier reasoning was wrong: it searched for the `CRISPR Guide Capture` feature
type, which is the wrong thing to look for, because in CROP-seq the sgRNA is a
polyadenylated Pol II transcript and appears as an ordinary Gene Expression
feature if it appears at all. It also never mentioned
`GSE175721_CRISPR_seq.fa.gz`, deposited with the series, which holds 14 CROP-seq
vectors over 13 AD risk genes. All 14 protospacers extract cleanly at 20 nt.

The STOP nonetheless stands: the deposited matrix is stock Cell Ranger
hg19-1.2.0 with no vector contig, and scanning 400,000 of the 17,902,462 unplaced
reads in `BC03.bam.1` found 4 reads containing the sgRNA scaffold and 1
containing a protospacer. Raw barcode `CR` and UMI `UR` tags are present on every
read, so cell identity survives; the guide reads do not exist at usable scale.
Mechanism: this series deposited two plain 3′ GEX samples and **no sgRNA
enrichment library**, which is precisely what GSE178317 has.

The actionable change: the GEO record for GSM5345023 states a tab-separated
**metadata file was provided**. It is absent at series, SuperSeries and both
sample levels (each `filelist.txt` read directly). The ask is now one named file
from Bilal Cakir / In-Hyun Park lab, Yale.

## 5. CRISPRbrain — newly acquired, never previously examined

A search of every worktree found no prior reference. 54 screens; 9 transcriptomic
carrying **4,710,865 gene-level measurements over 352 distinct perturbed genes**
(70 microglia, 284 neuron, 2 shared). Adds glutamatergic neurons, astrocytes and
iPSC, none of which this collection had.

Internal validation nobody tuned: every CRISPRi screen shows the targeted gene
going down (35/35 Day-8 microglia, 25/25 and 23/23 for the 2019 neuron and iPSC
screens, 161/167 for the 2020 neuron screen), while the one CRISPRa screen shows
13/76 down, i.e. 63 up — the opposite direction, correct for activation.

Cross-check on work in flight: the Day-8 iTF-Microglia screen covers **exactly
the 39 targets** reconstructed independently from Supplementary Table 5 (39/39,
nothing missing either way), and its 343,707 rows match that paper's
Supplementary Table 9 at 343,708 including header.

## 6. Benchmark vs training corpus — first measurement

Raised by the owner: a poor match makes a bad score measure the mismatch rather
than the method. Axes are deliberately asymmetric and the receipt says so.

Measured from `full104_pass1_v2_selection_row_keyed.npz` (`core`, `donor_addr_nnz`
104 × 41,238) and the stage81a2r registry:

| set | in space | in core | **detected in 0 donors** | median donors | median cells |
|---|---|---|---|---|---|
| CRISPRbrain microglia (70) | 70 | 64 | **0** | 104/104 | 359,246 |
| CRISPRbrain neuron (284) | 276 | 255 | **0** | 104/104 | 266,514 |
| GSE178317 (39) | 39 | 35 | **0** | 104/104 | 428,411 |

No perturbation target is unobserved in FULL104. The 8 outside the address space
are stale HGNC aliases (ATP5A1→ATP5F1A, ATP5B→ATP5F1B, C6orf203→MTRES1,
FAM57B→TLCD3B, WDR66→CFAP251, plus NDUFAF6, RNF165, SLC2A3). **These are not
resolved.** Your `cross_study_feature_contract_v1.py` refuses to infer synonyms
and requires an authenticated frozen annotation release, which is correct; they
are recorded as test inputs for it, not hand-mapped.

---

## 7. Weak points I am flagging myself — audit these first

1. **z=5.0 and the usability floor were declared after a smoke run.** The
   rationale is external (number of tests; downstream pseudobulk requirement),
   and this is stated in the producer, but a bounded run had already been
   executed when the numbers were fixed. Judge whether that contaminates the
   pre-declaration. If you think it does, the remedy is to re-declare against a
   held-out lane.
2. **The GSE175721 "~45 guide reads in the file" figure is an extrapolation from
   a 2.2% prefix, not a measured total.** Labelled as such in the determination
   document. The prefix may not be representative; I did not sample elsewhere in
   the unplaced region.
3. **Donor / cell-line and cell-barcode overlap are `NOT_CHECKED`**, not zero.
   iPSC lines derive from named individuals and are reused. This matters most for
   GSE301119 and the iPSC-derived studies.
4. **I consumed the v2 selection-row-keyed pass1 for the overlap measurement**
   without confirming it is the currently authoritative artifact. Given the
   source-encoding defect found in the FULL104 derivative earlier, confirm that
   `full104_pass1_v2_selection_row_keyed.npz` is current and that
   `donor_addr_nnz` was unaffected by that defect.
5. **CRISPRbrain differential expression is consumed as produced.** We cannot
   re-normalise it, re-test it, or inspect their cell filtering. Any benchmark
   built on it inherits their pipeline. This is a dependency, not a defect, but
   it should be recorded wherever those numbers are used.
6. **The GSE178317 lane pairing** was established by barcode containment in
   earlier work (diagonal 12–25× off-diagonal) and agrees with filename
   numbering. v2 hard-codes the pairing in `LANES`. Worth re-deriving.
7. **`gse178317_cell_guide_assignments_v1.csv` contains 10 rows and must not be
   used.** It is superseded; the v1 receipt exists only to document the failure.

## 8. Not done / open

- v2 call stage against full data — count stage in flight.
- `build_gse178317_intervention_effects_v1.py` — committed, never executed.
- Transcriptome-wide DE for GSE301119.
- Three unprocessed GSE254205 arms (snRNA-seq, ATAC, LD-sort).
- Baselines. **Nothing has been run that shows any method beats chance on this
  benchmark.** Until that exists, no claim about JEPA is interpretable, and the
  correct order is baselines first.
- GSE175719 (sibling SubSeries, microglia × amyloid 2×2 in organoids) noted as
  available, not acquired.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · MASKS=NONE · BURDEN=NOT_RUN
RARE_TAIL_MOLECULAR=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
