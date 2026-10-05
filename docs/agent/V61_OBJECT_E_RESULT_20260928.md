# V61 — object `E` is constructed, and the accessibility mask is doing the work

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
`75d98e9b`. `TRAINING=OFF`. `TD60=BLOCKED`. No regulatory molecular outcome
opened. No gene annotation joined at any point.**

Construction ran from the clean committed head `21326f21` against the rule
frozen at `0639a2d3`, which was written before any genome-wide interaction row
was read.

---

## Result

> `E = HiChIP contact edge ∩ Cluster-24 accessible regulatory element ∩
> hg38-stable coordinate identity`

**Primary rule `q<0.01 | ≥2 donors | both anchors accessible`: 49,401 edges.**

| property | value |
|---|---|
| edges | **49,401** |
| chromosomes | 23 — all but chrY |
| distinct 10 kb bins | 23,636 |
| distance | min 40 kb · q25 80 kb · **median 150 kb** · q75 270 kb · max 1.97 Mb |
| donor support | 2→16,173 · 3→9,467 · 4→6,644 · 5→5,145 · 6→4,522 · 7→4,756 · **8→2,694** |
| file | `V61_OBJECT_E_PRIMARY.tsv.gz`, 424,116 bytes, sha256 `61893aeb87c3a5bb86113520e391bca773b58e6dea20adea66b3d28d67af145e` |

Stop conditions **S1, S2, S3 all clear**. Verdict `OBJECT_E_CONSTRUCTED`.

## What the construction verified about its own inputs

70,088,696 contact rows across 12 samples and 8 donors.

- **F4:** zero trans edges and zero self-loops in 70M rows. FitHiChIP emitted
  cis only, so F4 discarded nothing — it is a check that passed, not a filter
  that acted.
- **F6:** every one of 1,304,958 candidate anchors is exactly 10,000 bp wide,
  **zero grid violations**, and chromosome naming matches the peak set
  literally. Combined with the depositors' own `Genome_build: hg38` declaration
  for the contact layer and the hg38 peak set from the same accession, both
  sides of `E` are hg38 without liftover.
- **F5:** observed distances sit inside FitHiChIP's declared 20 kb–2 Mb window
  rather than pressing against it, so the window is inherited rather than
  imposed.
- Accessibility: 205,547 peak rows → 54,330 unique intervals → **45,147
  accessible 10 kb bins**.

**Per-sample yield varies 39-fold** — 7,363 significant edges in the shallowest
library against 290,096 in the deepest. That is the concrete reason F2 counts
donors instead of pooling: pooling would let one deep library define the object.

## The funnel, all 18 frozen cells

| rule | edges | chr | bins |
|---|---|---|---|
| q001 \| d1 \| both | 70,276 | 23 | 28,555 |
| q001 \| d2 \| both | 35,260 | 23 | 20,282 |
| q001 \| d3 \| both | 23,519 | 23 | 16,116 |
| **q01 \| d2 \| both** | **49,401** | **23** | **23,636** |
| q01 \| d1 \| both | 97,402 | 23 | 31,948 |
| q01 \| d3 \| both | 33,228 | 23 | 19,202 |
| q05 \| d2 \| both | 67,215 | 23 | 26,820 |
| q01 \| d2 \| one | 114,268 | 24 | 51,292 |

Monotone in all three directions, and every cell holds 23–24 chromosomes. The
strictest corner (`q001|d3|both`) still yields 23,519 edges, so the object does
not depend on the primary being the permissive choice. The full 18-cell table is
in the JSON.

---

## The check that mattered: is `E` actually microglial?

**The contact layer carries no microglial information whatsoever.** FitHiChIP was
run `peak-to-all` on peaks called from the *one-dimensional* HiChIP data, which
is bulk. So F3 — both anchors accessible in Cluster 24 — is the **only** step
that makes `E` a microglial object. If F3 passed nearly everything, `E` would be
a bulk contact map wearing a microglial label.

The construction report gave survivors without a denominator, so that pass rate
was **unmeasured**. It is now measured, against an interpretation rule declared
in the verification script before the numbers existed.

| | |
|---|---|
| candidate edges, `q<0.01`, ≥2 donors | 165,891 |
| both anchors accessible | **49,401 — 29.78%** |
| exactly one accessible | 64,867 |
| neither accessible | 51,623 |
| **distance-matched null rate** | **5.10%** |
| **enrichment** | **5.84×** |

**F3 rejects 70% of candidates, and what it keeps is 5.84× what chance would
keep.** Both declared conditions hold. Verdict **`F3_IS_A_REAL_FILTER`**.

Two things make this convincing rather than merely favourable:

1. **The null is distance-matched.** Accessible bins are clustered, so nearby
   bin pairs are both-accessible far more often than distant ones. An unmatched
   null would have inflated the enrichment. 988,020 matched draws.
2. **The per-chromosome null rates track gene density**, which is what a null
   capturing real structure should do: chr19 highest at 13.4% (the most
   gene-dense chromosome), chrX lowest at 1.55%. A null that returned a flat
   rate everywhere would have been evidence it was measuring nothing.

Internal consistency: 49,401 + 64,867 = 114,268, which is exactly the
`q01|d2|one` cell of the independently computed construction funnel. The two
runs agree without being made to.

---

## What this does and does not establish

**Established.** A fully public, DUA-free external regulatory object exists and
is built. Its links are contact-defined, not covariance-defined. No RNA enters
it — Corces generates none. No disease locus enters it: the AD/PD GWAS
conditioning that made Supplementary Data Set 9 unusable is absent from the
per-GSM files, which carry no SNP column at all. No measurement of ours enters
it. Its microglial specificity is measured, not assumed.

**Not established, and still carried:**

- **The HiChIP donor key.** Parsed from filenames; GEO exposes no donor
  identifier for any of the 12 samples. `LIKELY_SAME_KEY__UNPROVEN`. The
  stricter reading (5 donors rather than 8) would make F2 *harder*, so the
  current object is the more permissive of the two — and the per-edge donor
  support vector is in the output so F2 can be recomputed without re-reading
  3.73 GB. The next rung is the paper's Supplementary Data Set 1.
- **The University of Washington / SEA-AD source-institution overlap.**
  Unresolved. No public donor-token-to-institution mapping was found.
- **Only 3 of 13 donors are shared between the contact and accessibility
  layers.** `E` is a cross-donor intersection with no within-donor
  contact × accessibility support.
- **The n=18 benchmark is not qualified** and none of its verdicts may be cited.
  `E`'s construction never depended on it.

## Self-audit

**Starting SHA** `75d98e9b`; ending SHA in the commit. **Changed files:** this
document plus `results/v61/` — classes **docs**, **results**.

**Execution provenance.** The construction ran from worktree head `21326f21`
with `git status --porcelain` empty, from script digest
`272394bdb31e695fdbd35376bb7e9335581e7b9c1acf099424d8521e57db9b5b`. The
selectivity check ran from head `75d98e9b`. Both output directories were fresh;
the scripts' own `STOP_OUTPUT_EXISTS` guard enforced that rather than my
remembering to.

**Protected outcomes opened: NO.** No gene symbol, Ensembl ID, target gene,
program gene or Stage75F edge was read, joined or enumerated. `E` is coordinates
only.

**S-V61-1, caught before it could mislead.** The construction report recorded
survivors at the accessibility step but not the denominator, so the F3 pass rate
— the single number that decides whether `E` is microglial at all — was absent
from the artifact. I noticed it only when writing the result up, after the
object was already built and reported. A funnel that reports what survived
without what was attempted is the conditional-on-success reporting this project
has already ruled out once; it should have been in the construction script from
the start.

**Strongest alternative explanation for the 5.84× enrichment.** That H3K27ac
HiChIP anchors are enriched for open chromatin in *any* cell type, so the
enrichment reflects generic regulatory activity rather than microglial identity.
This is not ruled out by the present check, and it is the right next test:
repeat the selectivity measurement against a **non-microglial** Corces cluster's
peak set. If a neuronal cluster gives a similar enrichment, F3 is selecting
"regulatory" rather than "microglial", and the object's specificity claim would
need weakening. The peak sets for all 24 clusters are already downloaded, so
this costs one more pass and no new data.

**What remains unknown:** whether the enrichment is microglia-specific or
generic; the HiChIP donor key; UW/SEA-AD donor-level overlap.
