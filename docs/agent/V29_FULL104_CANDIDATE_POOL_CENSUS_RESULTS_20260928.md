# FULL104 candidate-pool census — results and feasibility decision

**Date 2026-09-28. Branch `review/v27-authority-root-inventory-20260925`.
`TRAINING=OFF`. Real teacher-fidelity evaluation CLOSED. No reserved readout
was opened, and no directed outcome was run.**

**Decision, stated first:**

| program | verdict |
|---|---|
| **HLA_DRA_ANTIGEN** | **SHAM CONSTRUCTION INFEASIBLE.** 199 gene-disjoint panels are unreachable in every source and in the combined population, at *every* matching tier including the loosest. |
| **APOE_LIPID** | **FEASIBLE ONLY AT TIERS ALREADY KNOWN TO BE INSUFFICIENT.** 199 reachable at mean and mean+detection; collapses to 57 once dispersion is matched and 28 at all five observables. |
| **P2RY12_HOMEOSTATIC** | **FEASIBLE ONLY AT TIERS ALREADY KNOWN TO BE INSUFFICIENT.** 199 reachable through the depth tier; collapses to 10 at all five observables. |

This is a statement about **sham construction**, not about the biology. The
count-based null could not be assembled; it was not run and failed.

---

## 1. What was run

Streamed all 8,915 Level-4 blocks, decoded every column through each matrix's
authenticated decoder, folded per-address marginals into streaming accumulators.
No dense matrix. **114,041 fitting nuclei** of 187,909, from **60 fitting
donors**; 32 evaluation donors and their 73,868 nuclei were never touched.

Donor split declared in code before any pool size existed:
`sha256('<source>|<donor_id>')[:8]`, ranked ascending within source, lowest
`ceil(n/3)` to evaluation. Sources never pooled. Verified stable across three
`PYTHONHASHSEED` values in separate processes.

Structurally available addresses per source, from the verified decoders:

| source | addresses measurable | fitting nuclei |
|---|---:|---:|
| HVS | 18,736 | 1,415 |
| NPH52 | 28,099 (observed union; lower bound on 32,176) | 9,391 |
| SEA_AD | 34,242 | 103,235 |
| **intersection (combined-eligible)** | **16,276** | — |

The combined-eligible universe is **16,276 of 41,238 addresses — 39%**. HVS is
the binding source: a panel that must be measurable everywhere is confined to
what a filtered CELLxGENE object of 18,736 genes contains.

---

## 2. Maximum gene-disjoint panels, against the frozen target of 199

Gene-disjoint means **no gene reused in any panel** — the only construction for
which the 199 sham draws are even plausibly independent. `>=398` is the greedy
search cap, meaning ample.

| population | program | T1 mean | T2 +detect | T3 +Fano | T4 +depth | T5 all five | binding slot at T5 |
|---|---|---:|---:|---:|---:|---:|---|
| HVS | APOE_LIPID | 293 | 219 | 115 | 111 | 102 | — |
| HVS | P2RY12 | ≥398 | 320 | 226 | 149 | 148 | — |
| HVS | HLA_DRA | 64 | 48 | 37 | 13 | **4** | — |
| NPH52 | APOE_LIPID | ≥398 | ≥398 | 13 | 13 | 13 | — |
| NPH52 | P2RY12 | 64 | 62 | 59 | 59 | 59 | — |
| NPH52 | HLA_DRA | **0** | **0** | **0** | **0** | **0** | HLA-DPA1 absent |
| SEA_AD | APOE_LIPID | ≥398 | 318 | 57 | 57 | 36 | — |
| SEA_AD | P2RY12 | 340 | 278 | 258 | 258 | 14 | — |
| SEA_AD | HLA_DRA | 174 | 157 | 128 | 117 | **0** | CD74 |
| **COMBINED** | **APOE_LIPID** | **≥398** | **291** | **57** | **57** | **28** | — |
| **COMBINED** | **P2RY12** | **370** | **295** | **203** | **203** | **10** | — |
| **COMBINED** | **HLA_DRA** | **139** | **123** | **102** | **89** | **0** | CD74 |

Reaches 199 without any gene reuse:

- APOE_LIPID — T1, T2 only (every population)
- P2RY12 — T1–T4 in SEA_AD and combined; T1–T3 in HVS; **never** in NPH52
- HLA_DRA — **never, in any population, at any tier**

199 panels can of course be *manufactured* anywhere the pools are non-empty, by
reusing genes. The table says what can be built **without** reuse, because reuse
is what creates the sham-sham dependence that decalibrates the rank p-value.

---

## 3. Why HLA_DRA fails, and it is two separate reasons

**CD74 is unmatchable.** It is the most abundant partner in the panel and sits
at the 99.6th percentile of abundance in HVS and the 99.85th in NPH52. At the
all-five tier nothing in 34,195 eligible SEA-AD addresses, or 16,276 combined,
falls inside its bands. This is not a tuning problem: there is almost nothing
else expressed that highly in myeloid nuclei.

**HLA-DPA1 is not measured in NPH52 at all** — see §4. The program's contract
requires exactly four partners, so the HLA program cannot be evaluated on NPH52
under any sham design.

The MHC class II locus caveat compounds both: HLA-DRA, HLA-DPA1, HLA-DMA and
HLA-DMB are physically linked and CIITA-co-regulated, so a random-gene null
lacks coherence the real panel has by construction. Even a feasible pool would
have given an unfair comparison for this program.

---

## 4. A defect in the corrected artifact, found by this census

The audit compares the census against the published 29-address artifact, which
was built by an entirely different code path. It now **fails on exactly one
disagreement**:

```
NPH52 | address 23673 (HLA-DPA1): artifact n=9391 available, census n=0
```

Detection of HLA-DPA1, from the artifact's own counts:

| source | nuclei | artifact says available | nonzero counts | max |
|---|---:|---|---:|---:|
| HVS | 2,117 | True | 777 (36.7%) | 11 |
| **NPH52** | **15,264** | **True** | **0 (0.0%)** | **0** |
| SEA_AD | 170,528 | True | 64,642 (37.9%) | 41 |

A gene detected in ~37% of nuclei in two sources and in **exactly zero of
15,264** in the third is not biology. It is structural absence recorded as a
measured zero — the same class of defect the availability mask was built to
prevent, recurring for NPH52.

**Root cause.** The extractor treats NPH52 as identity-verified and returns
every requested address as reachable *without checking the NPH52 feature axis
per address*. HVS and SEA-AD availability comes from a verified decoder;
NPH52's was assumed. The independent NPH52 pilot reached the same conclusion
from the historical archive — address 23673 structurally unmeasured, a
`legacy_exact` HLA-DPA1 recorded at 40452 instead — and correctly refused to
substitute. Two independent routes, same answer.

**Blast radius, deliberately small.** `total_excluding_29` subtracted address
23673 for NPH52 nuclei, and it contributed exactly 0, so **no denominator is
numerically wrong**. The 10-check artifact audit still stands on every other
claim. What is wrong is one availability flag, and any analysis that would have
read those 15,264 zeros as measurement. None has.

**Not a reason to substitute address 40452.** Same symbol, different address,
unverified identity; the pilot's refusal is the correct posture and this census
does not overturn it.

---

## 5. Self-audit: the first run of this census was void

The first census completed, the audit passed 7/7 with 66 of 66 comparisons
agreeing, and the pool tables were wrong.

I built the per-matrix availability mask as `lut >= 0`. `lut` is indexed by
**block column** and holds the **address**, so that is a mask over columns, and
availability is a property of the address. The SEA-AD decoders are complete
permutations — identity fraction **0.0000** — so the error was maximal: 1,469
addresses marked available that are not and 1,469 absent that are, *per matrix*.
It reported CD74 structurally unmeasured in SEA-AD (false) and PGK1 measured
(false; PGK1's absence from all eleven SEA-AD matrices is separately
established).

**Why the audit missed it, which is the more serious half.** A permutation maps
n columns onto n addresses, so the *count* is preserved: my "availability is
source-specific" check compared counts per source and passed. And the cross-path
comparison **skipped** any address where either side had zero cells — so the two
cases that would have exposed it instantly, CD74 and PGK1, were silently
dropped. A comparison that skips when one side is zero cannot detect "present in
one path, absent in the other", which is exactly this class of error.

Both fixed. The audit now fails on availability disagreement rather than
skipping it — which is how the genuine NPH52 finding in §4 surfaced. The
regression test uses a non-identity decoder and asserts the two masks have the
same count and different contents, so it fails against the old construction.

---

## 6. What this does and does not license

**Does not establish exchangeability for anything.** The 2026-09-28
counterexample showed two panels matched to within 0.003 on mean, detection,
depth correlation and 0.0005 on within-panel covariance still differing +0.809
versus +0.002 on residual capture coupling. Every tier in §2 is built from those
same observables. A large pool is necessary, never sufficient.

**The type-I figures remain scenario calculations.** The 4.87–6.49% range I
derived earlier comes from an assumed correlation rule (ρ ≈ shared genes / 4)
applied to the pilot's measured reuse. It is exploratory, not an empirically
qualified full-pipeline error rate, and nothing here upgrades it.

**No candidate list is emitted**, no tier is preferred, and no gene was selected.
Selection used fitting donors only; evaluation donors and all six reserved
readouts were never read.

---

## 7. Decision under frozen protocol v7

For **HLA_DRA_ANTIGEN**, record
`SHAM_CONSTRUCTION_INFEASIBLE__NO_GENE_DISJOINT_PANEL_SET_EXISTS`. CD74 is
unmatchable at every tier and HLA-DPA1 is unmeasured in NPH52. This is not the
biological null failing — that null could not be built, so it was never tested.

For **APOE_LIPID** and **P2RY12_HOMEOSTATIC**, 199 gene-disjoint panels exist
only at mean and mean+detection matching (and through the depth tier for
P2RY12). Those are precisely the tiers the counterexample proves insufficient
for latent capture. Running the six directed tests on them would produce a
number whose null validity is already known to be undefended.

**Therefore the count-based teacher-fidelity procedure is recorded as
`INSUFFICIENTLY_IDENTIFIABLE_UNDER_TESTED_NUISANCE`** per the v7 stopping rule.
Matching bands, thresholds and candidate pools are not to be retuned to induce a
pass.

That verdict concerns the **validation strategy**. It is not evidence that the
per-nucleus biological state is absent, and must never be reported as such.

**The preregistered alternative** — the conditional-composition readout — now
becomes the next object, and it inherits none of this scrutiny automatically. At
one to four molecules a centred log-ratio with a pseudocount is not
nuisance-free, and its measurement reliability has to be established before it
is trusted.

**Two things worth doing first, both outcome-blind and both cheap relative to a
directed test:**

1. Repair the NPH52 availability flag by deriving it from the provenance table
   rather than assuming it, and re-audit. One flag is wrong today; the method
   that produced it would produce more.
2. Qualify same-nucleus binomial thinning as a latent-capture instrument on a
   properly matched fixture, per the standing caveat that thinning is a
   measurement-robustness diagnostic and not an intervention on original capture
   efficiency. If it qualifies, the exchangeability question becomes answerable
   rather than merely hard; if it does not, that is worth knowing before the
   composition route is built on the same ground.
