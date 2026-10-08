# FULL104 candidate-pool census — results and feasibility decision

**Date 2026-09-28, revised the same day after three independent-review repairs.
Branch `review/v27-authority-root-inventory-20260925`. `TRAINING=OFF`. Real
teacher-fidelity evaluation CLOSED. No reserved readout opened; from this run
none was even computed on.**

> **This supersedes the first version of this report.** Three defects were
> repaired between them — protected readouts were being accumulated before
> exclusion, NPH52 availability was taken from observed nonzeros rather than its
> authenticated axis, and the combined population was a pooled average rather
> than a per-source intersection. The third changes the headline numbers
> drastically. §6 records what moved and why.

## Decision

| program | verdict in the combined population |
|---|---|
| **APOE_LIPID** | **INFEASIBLE.** Exactly **1** gene-disjoint panel at the loosest tier, 0 from the dispersion tier onward. |
| **P2RY12_HOMEOSTATIC** | **INFEASIBLE.** **0** at every tier; CX3CR1 has no eligible candidate even on mean alone. |
| **HLA_DRA_ANTIGEN** | **INFEASIBLE.** **0** at every tier; CD74 and HLA-DPA1 both empty. |

**No program reaches 199 gene-disjoint panels in the combined population at any
tier.** The first version of this report said HLA_DRA was infeasible and the
other two were feasible at loose tiers. That was an artefact of pooling sources;
corrected, **all three are infeasible**.

This is a statement about **sham construction**. The count-based null could not
be assembled, so it was never run and did not fail.

---

## 1. What was run

All 8,915 Level-4 manifest blocks streamed; **5,211 count blocks** contained
fitting nuclei and were read; **303,849,232 nonzero entries** folded.
**114,041 fitting nuclei** from **60 fitting donors**, each folded exactly once
and asserted so. 32 evaluation donors and their 73,868 nuclei never touched.

Structurally measurable addresses, from authenticated axes:

| source | measurable | eligible after exclusions | fitting nuclei |
|---|---:|---:|---:|
| HVS | 18,731 | 18,692 | 1,415 |
| NPH52 | 31,616 | 31,575 | 9,391 |
| SEA_AD | 34,236 | 34,195 | 103,235 |
| **intersection** | — | **16,718** | — |

---

## 2. Exact Hall capacity against the frozen target of 199

Gene-disjoint means no gene reused in any panel. Computed with the independent
workstream's exact Hall/bipartite tool, not a greedy construction. **Disjointness
is a conservative feasibility criterion and does not by itself establish
statistical independence of the sham draws.**

| population | program | T1 mean | T2 +detect | T3 +Fano | T4 +depth | T5 all five |
|---|---|---:|---:|---:|---:|---:|
| HVS | APOE_LIPID | 293 | 219 | 115 | 111 | 102 |
| HVS | P2RY12 | 423 | 320 | 226 | 149 | 148 |
| HVS | HLA_DRA | 64 | 48 | 37 | 13 | 4 |
| NPH52 | APOE_LIPID | 877 | 855 | 13 | 13 | 13 |
| NPH52 | P2RY12 | 64 | 62 | 59 | 59 | 59 |
| NPH52 | HLA_DRA | **0** | 0 | 0 | 0 | 0 |
| SEA_AD | APOE_LIPID | 630 | 318 | 57 | 57 | 36 |
| SEA_AD | P2RY12 | 340 | 278 | 258 | 258 | 14 |
| SEA_AD | HLA_DRA | 174 | 157 | 128 | 117 | **0** |
| **COMBINED** | **APOE_LIPID** | **1** | **1** | **0** | **0** | **0** |
| **COMBINED** | **P2RY12** | **0** | **0** | **0** | **0** | **0** |
| **COMBINED** | **HLA_DRA** | **0** | **0** | **0** | **0** | **0** |

Reaches 199 without reuse: HVS APOE (T1–T2), HVS P2RY12 (T1–T3), NPH52 APOE
(T1–T2), SEA_AD APOE (T1–T2), SEA_AD P2RY12 (T1–T4). **Never in the combined
population, for any program, at any tier.**

---

## 3. Why the combined pools collapse — and it is not small-sample noise

A combined-eligible gene must satisfy the matching band **separately in every
source**. The band is 1.25 / 0.80 = **1.56× wide**. But each partner's own mean
moves between sources by more than that:

| partner | HVS | NPH52 | SEA_AD | max/min |
|---|---:|---:|---:|---:|
| APOC1 | 0.323 | 0.183 | 0.610 | 3.34× |
| ABCA1 | 1.441 | 0.284 | 1.298 | 5.07× |
| GPNMB | 0.192 | 0.140 | 0.396 | 2.83× |
| TREM2 | 0.152 | 0.640 | 0.309 | 4.21× |
| TMEM119 | 0.122 | 0.350 | 0.232 | 2.88× |
| **CX3CR1** | 0.651 | **4.691** | 1.207 | **7.21×** |
| GPR34 | 1.095 | 1.807 | 1.033 | 1.75× |
| C1QA | 0.534 | 1.055 | 1.019 | 1.97× |
| CD74 | 3.777 | 6.169 | 3.477 | 1.77× |
| HLA-DPA1 | 0.541 | *not measured* | 0.643 | 1.19× |
| HLA-DMA | 0.336 | 0.389 | 0.437 | 1.30× |
| IFI30 | 0.173 | 0.169 | 0.192 | 1.14× |

Median cross-source spread **2.40×**, and **9 of 12 partners exceed the matching
band itself**. To match such a partner everywhere, a candidate would have to
reproduce not just its level but its *cross-source pattern* — rising 7-fold into
NPH52 for CX3CR1, falling 5-fold for ABCA1. Almost nothing does.

**This is the real finding, and it is more general than pool size.** The three
sources do not place these genes on a common scale. Whether that reflects
protocol, dissection, nuclear isolation or cohort composition is not resolved
here, and it is an outcome-blind, structural fact about the corpus rather than
anything about the shams.

### An interpretive question this raises, which I am not resolving alone

v7 says donors are split "by hash of the source-specific donor identity. Sources
never pooled." If that means a single frozen sham roster must serve all three
sources, the combined row governs and **all three programs are infeasible**. If
per-source rosters are admissible, the per-source rows govern and APOE and
P2RY12 remain feasible **only at T1/T2** — tiers the counterexample already
proves insufficient for latent capture.

**The count-route verdict is the same either way**, which is why this is
reported rather than treated as a blocker. But the two readings license
different sentences about *why*, and the distinction should be settled before
the closeout is frozen.

---

## 4. HLA_DRA: the two reasons, now both structural

**CD74 is unmatchable** at the strictest tier: 99.6th abundance percentile in HVS
and 99.85th in NPH52; nothing in 34,195 eligible SEA-AD addresses falls inside
its bands at T5, and nothing in the combined population at any tier.

**HLA-DPA1 is not in NPH52's authenticated feature axis.** Now established from
the stage81a2r provenance table filtered to the MG object — 32,176 rows, 31,621
distinct addresses — rather than inferred from observed zeros. CD74, PGK1, LPL
and APOE are in that axis; address 23673 is not.

The MHC class II locus caveat stands: HLA-DRA, HLA-DPA1, HLA-DMA and HLA-DMB are
physically linked and CIITA-co-regulated, so a random-gene null lacks coherence
the real panel has by construction. Even a feasible pool would have been an
unfair comparison here.

---

## 5. A defect in the corrected artifact, now doubly confirmed

The audit **fails on exactly one disagreement**, deliberately:

```
NPH52 | address 23673 (HLA-DPA1): artifact n=9391 available, census n=0
```

| source | nuclei | artifact says available | nonzero counts |
|---|---:|---|---:|
| HVS | 2,117 | True | 777 (36.7%) |
| **NPH52** | **15,264** | **True** | **0 (0.0%)** |
| SEA_AD | 170,528 | True | 64,642 (37.9%) |

Two independent routes agree it is absent: the authenticated provenance axis,
and the NPH52 pilot's reading of the historical archive. **Root cause:** the
extractor treats NPH52 as identity-verified and returns every requested address
as reachable *without checking its feature axis per address*. HVS and SEA-AD
availability came from a verified decoder; NPH52's was assumed.

**Blast radius stays small.** `total_excluding_29` subtracted address 23673 for
NPH52 nuclei and it contributed exactly 0, so no denominator is numerically
wrong, and no analysis has read those 15,264 zeros as measurement. Address 40452
is **not** substituted: same symbol, different address, unverified identity.

---

## 6. What the three repairs moved

| repair | effect on the numbers |
|---|---|
| Protected readouts excluded **before** accumulation | No effect on any pool. Restores blindness; the exposure is recorded in the ledger as Correction 4. |
| NPH52 availability from the **authenticated axis** | **Raised** NPH52 eligibility from 28,053 to 31,575 addresses — 3,522 genes were measured but zero in every myeloid nucleus and had been wrongly treated as unmeasured. NPH52 APOE T1 rose from ≥398 to 877. |
| Combined = **per-source intersection**, not pooled average | **Collapsed** every combined figure. APOE T5 28 → 0; P2RY12 T4 203 → 0; HLA_DRA T1 139 → 0. The pooled average had been hiding source-specific matching failure exactly as the review predicted. |
| Exact Hall capacity replacing greedy | Agreed with greedy in every cell checked. Greedy was a valid constructive lower bound; the numbers are now exact rather than merely sufficient. |

---

## 7. What this does and does not license

**No exchangeability claim.** The 2026-09-28 counterexample matched two panels to
within 0.003 on mean, detection and depth correlation and 0.0005 on within-panel
covariance, and they still differed +0.809 versus +0.002 on residual capture
coupling. Every tier here is built from those same observables.

**Disjointness ≠ independence.** No cross-panel gene reuse is a conservative
feasibility criterion. It does not establish that the sham statistics are
statistically independent.

**The type-I figures remain scenario calculations**, from an assumed correlation
rule applied to the pilot's measured reuse — not a qualified pipeline error rate.

**No candidate list is emitted**, no tier is preferred, no gene selected.
Selection used fitting donors only.

---

## 8. Decision under frozen protocol v7

**`SHAM_CONSTRUCTION_INFEASIBLE`** for all three programs in the combined
population, at every matching tier. Where per-source construction is feasible it
is feasible only at tiers already shown insufficient.

**The count-based teacher-fidelity procedure is recorded as
`INSUFFICIENTLY_IDENTIFIABLE_UNDER_TESTED_NUISANCE`** per the v7 stopping rule.
Bands, thresholds and pools are not to be retuned to induce a pass.

That verdict is about the **validation strategy**. It is not evidence that the
per-nucleus biological state is absent, and must never be reported as such.

**Next, in order:**

1. Repair the NPH52 availability flag in the artifact itself, deriving it from
   the provenance axis rather than assuming it, and re-audit. One flag is wrong
   today; the method that produced it would produce more.
2. Freeze the v7 count-route closeout, with §3's interpretive question settled.
3. **Conditional composition as a new developmental validation strategy**, with a
   **differential-capture negative control mandatory from the start**. The
   independent CPU work already showed why: 5/120 positives under uniform
   capture but **119/120 under gene-specific differential capture with no
   biological association**, and a per-donor conditional binomial GLM at
   **0/80 uniform versus 80/80 false positives under differential capture**.
   Supplying the true hidden capture factor — unavailable in real data — cut
   those to 2/80. Observed depth does not control gene-specific capture.
4. Same-nucleus thinning may contribute a **post-capture measurement-robustness
   diagnostic** only. It cannot establish equivalence with respect to the
   original hidden biochemical capture process.

**With every internal reserved readout downgraded to secondary evidence (see the
exposure ledger's owner ruling), this study has no strictly independent internal
confirmation left.** The donor-level ATAC evaluation becomes the genuine
confirmation layer, and that shift should be stated wherever these results are
reported.
