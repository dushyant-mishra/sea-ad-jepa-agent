# V64 C3 descriptive evidence — liftover, round trip, ATAC provenance

Branch `claude/v64-frozen-execution-20260929`, parent canonical authority
`chatgpt/v64-e2-single-source-successor-20260929` @ `2d6fa8a1`, **verified live at
execution time**. `TRAINING=OFF`, `TD60=BLOCKED`. Coordinates only; no gene
annotation joined.

## Carried forward unchanged

The two frozen statistical tests are **closed**:

- depth-sensitivity ablation → `A_pass_survives`
- out-of-span TECH → `B_outspan_fails_only`

> **Continuous adjustment is qualified for nuisance surfaces within or near its
> frozen basis, with broad support and without material dependence on the two
> outcome-derived depth-sensitivity covariates. It is not qualified against
> arbitrary hidden-quality geometry.**

No `sin`/`tanh` terms were added. The out-of-span failure is not repaired.

## Implementation actually used

UCSC `liftOver`, **archived build `linux.x86_64.v479`**, sha256
`80c77de53b8bbd5fec661242f24d4b2f0ac54446df6954d934d1a838927dd19c`, run under WSL
Ubuntu. The *current* `linux.x86_64` build could not execute — it requires GLIBC
2.32/2.33/2.34 and the available Ubuntu provides 2.31 — so the most recent
archived build that runs was used and its digest recorded.

`-minMatch=0.95`. No `-multiple` for the authoritative mapping; a separate
`-multiple -noSerial` pass is used **only to detect** anchors with more than one
destination, which are then **rejected as ambiguous**. No nearest-neighbour
rescue, no `-fudgeThick`, no `-minBlocks` relaxation. **Identical rules forward
and reverse.**

All five inputs verified against the recorded V64 custody digests before use —
both chains and all three ATAC tracks matched byte-for-byte.

---

## 1. Forward liftover hg19 → hg38

| quantity | value |
|---|---|
| pairs attempted | **104,802** |
| anchor instances attempted | **209,604** |
| single successful mappings | 209,528 |
| unmapped anchors | **73** — *Partially deleted in new* 50, *Split in new* 23 |
| ambiguous / split rejected | **15** |
| duplicate names in output | 0 |
| chromosome-changing mappings | **6** |
| interval length unchanged | 207,289 (**98.9314%**) |
| interval length changed | 2,239 (1.0686%), **delta range −223 … +74,685 bp** |
| pairs with both anchors mapped | **104,728** |
| **retained-pair fraction of 104,802** | **0.999294** |
| anchor accounting reconciles | **True** |

**The number that needs adjudicating is the tail, not the centre.** 98.93% of
anchors keep their exact 5,000 bp length, but the largest single expansion is
**+74,685 bp** — a 5 kb anchor becoming roughly 80 kb. Six anchors also change
chromosome. Whether either is acceptable is precisely what the unfrozen
interval-length-change tolerance exists to decide, and I am not deciding it.

## 2. Round trip hg38 → hg19

Performed on the anchors of the 104,728 forward-retained pairs.

| quantity | value |
|---|---|
| anchors attempted | 209,456 |
| mapped back, single | 209,425 |
| unmapped on return | 25 — *Split in new* 14, *Partially deleted* 11 |
| ambiguous on return | 14 |
| **exact anchor recoveries** | **209,408** |
| same-chromosome discordant | **17** |
| chromosome discordant | **0** |
| **exact both-anchor pair recoveries** | **104,680** |
| exact round-trip fraction of forward-retained pairs | **0.999542** |
| **exact round-trip fraction of the original 104,802** | **0.998836** |

Every non-exact same-chromosome recovery, all 17 of them:

| delta | n |
|---|---|
| start +4, end +0 | 6 |
| start +0, end −4 | 5 |
| start +0, end −223 | 3 |
| start +0, end −124 | 2 |
| start +0, end −3 | 1 |

Five distinct patterns, all small except the −223 and −124 cases, and **no
chromosome ever changes on return**.

## 3. ATAC coordinate-provenance audit — the gap I raised is closed

This was Gap 1 from my V64 verification: FILER lifted the ATAC tracks to hg38
under an unrecorded chain while the contact map is lifted by us, so a peak and an
anchor could disagree for reasons that are not biological. Testable because the
files retain their hg19 source coordinates in columns 4–6.

Re-lifted those columns with **our** authenticated UCSC chain under **identical**
frozen semantics and compared to FILER's hg38 columns 1–3. **Primary test is
exact coordinate equality; no overlap tolerance was defined and none was
introduced.**

| track | rows | exact matches | discordant (same chr) | chr-discordant | unmapped | ambiguous | **exact fraction** |
|---|---|---|---|---|---|---|---|
| PU1 microglia | 50,199 | **50,199** | 0 | 0 | 0 | 0 | **1.000000** |
| NeuN neuron | 55,932 | **55,932** | 0 | 0 | 0 | 0 | **1.000000** |
| Olig2 oligodendrocyte | 38,476 | **38,476** | 0 | 0 | 0 | 0 | **1.000000** |

**100.0000% exact, all three tracks, denominators preserved, accounting
reconciles.** FILER's lift is indistinguishable from ours.

One thing worth stating so it is not misread: 100/71/81 rows respectively show a
source→re-lift interval-length change (range −21 … +958 bp). Those are properties
of the **chain**, not discrepancies — FILER's output contains the identical
changed intervals, which is why the match is exact.

**Consequence:** the mixed-liftover-provenance hazard is eliminated. Contact
anchors and ATAC peaks will sit in the same coordinate frame produced by the same
chain, so a later contact ∩ accessibility disagreement cannot be attributed to
divergent harmonisation.

---

## 4. Data-use record, carried forward

Recorded as verified by the V64 lane; **I did not independently re-verify these
terms** and am not restating them as my own verification.

| artifact | terms |
|---|---|
| FILER Nott ATAC tracks | **explicitly verified** |
| UCSC chain files | **explicitly verified, with non-commercial restrictions** |
| Nott Table S5 spreadsheet licence | **UNKNOWN** |

Public availability was not converted into a licence claim anywhere. Table S5's
licence stays `UNKNOWN` despite the file being in hand and authenticated.

---

## 5. Qualification status — deliberately withheld

> **C3 qualification: `NOT_YET_ADJUDICABLE`. `PASS = null`.**

The historical C3 contract requires two prospectively declared numeric gates that
remain unfrozen:

1. **allowable interval-length-change tolerance** — and the forward pass produced
   a tail reaching +74,685 bp plus 6 chromosome changes, so this gate is not
   academic;
2. **required exact round-trip recovery fraction** — the observed value is
   0.998836 against the original denominator.

Both numbers are now visible. Choosing either threshold at this point would be
selecting it after seeing the result, which is the move this project has spent
several cycles refusing. They must be frozen prospectively by someone who has not
just read this page, or frozen with that exposure stated.

## 6. Stopping here

Per the execution brief, work stops before P1S and P3. Neither has the operational
authority it needs.

**P1S still lacks:** the exact binary ATAC-support rule for a distal anchor; the
promoter-fixed shuffle implementation; the number of shuffles and Monte Carlo
precision authority; the exact paired contrast and uncertainty estimator; the
exact nuisance-adjustment implementation. The later NIH-CARD continuous-adjustment
estimator is **not** imported into P1S — no authority document says to, and its
own qualification is span-bounded.

**P3 still lacks:** the microglial expression source; the expression/detection
rule; the gene annotation version; the promoter→gene mapping authority; and the
exact post-liftover definition of "relationship absent". Promoter chromatin
activity is **not** substituted for measured gene expression to make P3
executable.

`E2_NOTT_CANDIDATE` is not instantiated.
