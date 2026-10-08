# V61 successor — the enrichment is **not** microglial, and I retract the claim

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
`9255e4e0`. `TRAINING=OFF`. `TD60=BLOCKED`. No regulatory molecular outcome
opened. No gene annotation joined.**

`docs/agent/V61_OBJECT_E_RESULT_20260928.md` is left byte-for-byte as committed
at `d85a8e81`. This successor carries the correction, following the V58/V59
manifest precedent.

---

## What I retract

In the V61 result document I wrote, in the "Established" section:

> "Its microglial specificity is measured, not assumed."

**That is false and I retract it.** The 5.84× enrichment I cited established that
F3 *filters*. It did not establish that what F3 selects is *microglial*, and I
wrote a sentence that conflated the two. The test I named in that same document
as the strongest competing explanation has now been run, and the competing
explanation wins.

## The measurement

Same 165,891 candidate edges for every mask — candidates do not depend on the
mask. Same distance-matched null pairs for every mask (common random numbers),
so no between-cluster difference can be Monte Carlo noise. 1,658,910 null pairs.

| cluster | cell type | accessible bins | both-accessible | null | **enrichment** |
|---|---|---|---|---|---|
| Cluster23 | Oligodendrocytes | 26,835 | 29.85% | 1.58% | **18.95×** |
| Cluster9 | OPCs | 44,358 | 40.02% | 4.12% | **9.72×** |
| Cluster15 | Astrocytes | 58,059 | 45.41% | 6.45% | **7.04×** |
| **Cluster24** | **Microglia** | **45,147** | **29.78%** | **4.69%** | **6.35×** |
| Cluster1 | Excitatory neurons | 64,877 | 43.19% | 7.48% | **5.77×** |

**Microglia rank fourth of five.** The best non-microglial mask reaches 18.95×,
three times higher. Verdict `ENRICHMENT_IS_GENERIC__WEAKEN_THE_SPECIFICITY_CLAIM`.

### The comparison that removes every confound

Enrichment is a ratio, and a smaller, more concentrated mask can inflate it. So
the ranking alone could be argued with. This pair cannot:

| | accessible bins | both-accessible edges | rate |
|---|---|---|---|
| **Cluster24 microglia** | 45,147 | 49,401 | **29.78%** |
| **Cluster9 OPCs** | 44,358 | 66,395 | **40.02%** |

**The two masks differ in size by 789 bins — 1.7%.** At essentially identical
genomic coverage, OPC accessibility coincides with both anchors of these contact
edges far more often than microglial accessibility does. There is no mask-size
explanation available for that difference.

### Abundance does not explain it either

The obvious story — bulk H3K27ac HiChIP is dominated by abundant cell types — does
not survive the numbers. Oligodendrocyte Cluster23 is **2,559 cells, 3.6%** of the
atlas and has the *highest* enrichment; microglia are **4,655 cells, 6.6%** and
rank fourth. Whatever drives the ranking, it is not simply cell abundance, and I
am not going to invent a mechanism for it. The finding is the ranking.

### Why this run's microglial null differs from the previous one

The earlier single-mask check reported a 5.10% null and 5.84×; this run reports
4.69% and 6.35×, from the **same** observed 29.78%. The difference is entirely in
the null: the earlier one matched distances to the *surviving* edges with 20
draws each, this one matches to the *candidate* edges with 10 draws each. The
candidate-matched null is the correct denominator for a cross-mask comparison,
because candidates are the one thing every mask shares. Neither number is wrong
for its own purpose and they are not in conflict.

---

## What this does and does not do to object `E`

**`E` itself is unchanged and remains exactly the object that was specified.** The
V60 work order was explicit on this point, before any of this was measured:

> "because HiChIP contacts are bulk and the microglial information comes from
> the accessibility mask, the synthetic positive should not assume
> microglia-specific contact strength. The biology we are testing is better
> represented as: a genuine regulatory edge has externally supported 3D contact
> + accessibility in the relevant cell state, not 'microglia have a unique
> HiChIP loop.'"

That is precisely what this result confirms. The design anticipated a generic
contact layer and declined to assume microglial contact strength. My error was
not in the construction — it was in adding a specificity claim on my own
initiative that the design had deliberately not made.

**What must change is the description, not the object:**

- ~~"a microglia-enriched contact map"~~
- **"the microglial slice of a generic regulatory contact map"**

`E` is a set of contact edges, externally supported, whose anchors are accessible
in microglia. It is *not* evidence that microglia have distinctive 3D regulatory
architecture at those edges, and no claim resting on that may be made from it.

**One forward consequence that must be carried.** Because the contact layer is
generic, `E`'s edges are enriched for regulatory architecture shared across brain
cell types. Any downstream inference that reads `E` as "microglial regulatory
edges" will be **biased toward edges microglia share with other glia**, and away
from anything microglia-distinctive. That bias is now measured rather than
suspected, and it belongs in the nuisance class explicitly.

---

## Self-audit

**Starting SHA** `9255e4e0`; ending SHA in the commit. **Changed files:** this
document, `results/v61/V61_CROSS_CLUSTER_SPECIFICITY_V1.json` — classes **docs**,
**results**.

**S-V61-2 — the defect, and it is mine.** I wrote "microglial specificity is
measured, not assumed" into a committed result document on the strength of a
measurement that did not test specificity. The 5.84× number was real and the
sentence was a non-sequitur from it. What saved it was writing the competing
explanation down in the same document and then actually running it — but I
should not have needed rescuing, because the claim and the evidence were one
paragraph apart.

**What was caught before damage:** everything. The claim existed for one commit
and was retracted in the same workstream by my own test, before anything was
built on it.

**The positive control on this method:** the test was capable of returning the
other answer. Its interpretation rule was written into the script before the
numbers existed, the masks were chosen so that Cluster24 was *third of five* by
peak count, and had microglia come out highest the same code would have printed
`ENRICHMENT_IS_MICROGLIA_SPECIFIC`. A check that can only confirm is the failure
mode this project's self-audit lane exists to catch.

**Strongest criticism of this correction:** five masks is a small comparison set,
and I chose them. A fuller test would score all 24 clusters, which costs one more
pass over data already on disk. I report five because five already answers the
question — microglia are not highest, and the matched OPC pair has no confound —
but the full sweep would put the ranking beyond argument and should be run before
`E` is used for anything load-bearing.

**What remains unknown:** whether the ranking holds across all 24 clusters; the
HiChIP donor key; UW/SEA-AD donor-level overlap.
