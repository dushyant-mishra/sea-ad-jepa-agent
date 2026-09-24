# Leakage-aware computational benchmarking specification — V1

Date: 2026-09-23
Status: **SPECIFICATION ONLY — not executed, no model trained, no result claimed**

This defines how a future intervention-response method will be evaluated against
the measured perturbation datasets. Nothing here has been run. Where a number
appears it is a dataset property already measured in this lane, not a result.

---

## 0. The correction this specification is built on

Failed historical computational experiments do **not** invalidate the underlying
experimental datasets. The Kampmann CROP-seq comparison defeated an earlier JEPA
pipeline — several targets anti-aligned (CSF1R, TGFBR2, CDK8), CDK12 positive —
but that is a fact about the *method*, not about the *data*.

Those datasets are therefore retained for development, analysis and retrospective
benchmarking. What changes is not their eligibility but the **claim** they can
support: any dataset that influenced method development cannot also serve as
evidence of independent predictive performance. That is handled by declaring
exposure, not by discarding studies.

## 1. Three evaluation questions, never conflated

### Q1 — Historical reproduction
*Can a new method reproduce the experimental observations that defeated the
earlier pipelines?*

Scored on the datasets that produced the historical failure. **Exposure is
total**: these observations are known, and a pass here is a sanity check, not
evidence of generalization. Reporting a Q1 result as predictive performance would
be the central error this specification exists to prevent.

### Q2 — Within-study generalization
*Can it predict held-out perturbation targets, replicates or other appropriate
partitions inside a characterized study?*

The held-out axis must be stated explicitly, because "held out" means different
things here and they are not interchangeable (§2).

### Q3 — Cross-study / cross-context transport
*Can it predict responses in a different experimental system, donor population or
treatment context?*

The only question that supports a claim of transportable prediction. It is also
the hardest: the studies differ in cell model, modality, dose and timepoint
simultaneously, so a single Q3 number confounds several shifts at once. Q3 must
therefore be reported **per shift axis**, never pooled into one headline score.

## 2. Partition units — the failure mode to avoid

**Cells from the same biological replicate are not independent donors.** A random
cell-level split leaks donor, guide and batch identity simultaneously and will
report near-perfect performance for a method that has learned nothing
transferable.

The legitimate partition units, in increasing order of difficulty:

| unit | what is held out | what it tests |
|---|---|---|
| **guide** | held-out guides for a *seen* target | robustness to guide-level off-target and efficiency variation |
| **target** | held-out perturbation targets entirely | generalization to unseen interventions — the Q2 unit of interest |
| **donor / line** | held-out donor or cell line | biological-replicate transport |
| **study** | held-out study | Q3 |

Rules:

1. A target's guides must never straddle a train/test boundary in a target-held-out
   split. Guide-level and target-level splits answer different questions.
2. Donor splits must respect the donor as the unit. In GSE301119 that means D1
   and D2, giving exactly **two** donor folds — a real and severe limit on donor
   transport power in that study, which must be stated rather than worked around
   by cell-level resampling.
3. Control cells are shared infrastructure. Non-targeting controls may appear on
   both sides of a target split — they define the reference, not the prediction
   target — but this must be declared, because a method that merely reproduces the
   control mean will otherwise look competent.
4. Multiply-assigned cells (GSE293118 has a substantial multiplet fraction) are
   excluded from single-perturbation evaluation, not reassigned to one of their
   guides.

## 3. Exposure ledger

Every study carries an exposure status, declared before any benchmark runs:

| status | meaning | strongest claim it can support |
|---|---|---|
| `DEVELOPMENT` | used to build or tune the method | Q1 only |
| `HISTORICALLY_EXPOSED` | outcomes were inspected in a prior failed analysis | Q1; Q2 only with the exposure stated inline |
| `RETROSPECTIVE_BENCHMARK` | used for comparison after the method was fixed | Q2 |
| `HELD_OUT` | never inspected, method frozen before first look | Q2 and Q3 |

`HELD_OUT` is destroyed by a single inspection, including a "quick sanity check".
A study that has been looked at is downgraded permanently and the ledger records
when and why. This is the same discipline the FULL104 lane applies to its
confirmation sets.

Current status, as of this specification:

| study | system | exposure |
|---|---|---|
| GSE301119 | primary human macrophage | `RETROSPECTIVE_BENCHMARK` — ETL-qualified in this lane; target engagement inspected |
| GSE293118 | HMC3 line, noncoding CRISPRi | `RETROSPECTIVE_BENCHMARK` — ETL in progress in this lane |
| GSE178317 | iPSC microglia CRISPRi/a | `HELD_OUT` — not yet ETL-qualified, outcomes uninspected |
| GSE311359 | iPSC microglia Perturb-seq | `HELD_OUT` |
| GSE175721 | engineered microglia in organoids | `HELD_OUT` |
| GSE254205 | APOE / amyloid / GNE317 | `HELD_OUT` |
| GSE241858 | TREM2 R47H, cytokine | `HELD_OUT` |
| GSE240609 | APOE3ch coculture | `HELD_OUT` |
| Kampmann CROP-seq | historical | `HISTORICALLY_EXPOSED` — defeated the earlier pipeline |

Inspecting target engagement during ETL is enough to move a study off `HELD_OUT`.
That is deliberate: engagement is an outcome, and pretending otherwise is how a
holdout quietly stops being one.

## 4. Baselines before any model

A learned method is only interesting relative to what a trivial rule achieves.
These are mandatory and must be reported alongside any model number:

1. **Global mean shift** — predict every perturbation's effect as the mean effect
   across all perturbations. Catches datasets where one direction dominates.
2. **Control-only** — predict no change. On sparse-effect datasets this is a
   surprisingly strong baseline and its score sets the floor.
3. **Target-identity** — predict only that the targeted gene itself moves in the
   modality's direction, everything else unchanged. Given the engagement measured
   here (CRISPRi median −0.811, CRISPRa median +2.115) this baseline alone will
   score respectably on any metric dominated by the target gene, which is exactly
   why metrics must exclude the target gene when scoring downstream effects.
4. **Program-based** — project onto a small set of expression programs derived
   from control cells only, and predict program-level shifts.

A method that does not beat (2) and (3) on downstream, target-excluded effects
has not demonstrated anything, regardless of its correlation with the full
response vector.

## 5. Metrics

* Effects are compared in **expression space**, on the measured feature
  intersection, with per-assay measurement masks applied. An unmeasured feature is
  excluded from scoring, never treated as zero.
* Report **per-target** scores and their distribution, not only a pooled score.
  A pooled correlation over all targets is dominated by the few strongest
  perturbations.
* **Exclude the targeted gene** when scoring downstream response. Including it
  measures target engagement, which the baselines already capture.
* Report **sign agreement** separately from magnitude agreement. The GSE301119
  CRISPRi/CRISPRa comparison in this lane is the concrete reason: 177 of 203
  targets oppose in sign while magnitudes correlate at only +0.096, because
  knockdown magnitude is bounded by baseline expression and activation magnitude
  by baseline silence. A single correlation would have hidden that.
* Report **uncertainty and n** for every cell of every table: guides per target,
  cells per guide, donors contributing.

## 6. What this specification forbids

* No pooled Q3 headline number across mixed shift axes.
* No cell-level random splits.
* No metric that includes the targeted gene when the claim is about downstream
  effects.
* No promotion of a `DEVELOPMENT` or `HISTORICALLY_EXPOSED` result to a
  generalization claim.
* No therapeutic ranking, disease-state reversal or drug-efficacy claim from any
  benchmark defined here. Those are separate reviewed steps.

```
STATUS: SPECIFICATION_ONLY__NOT_EXECUTED
JEPA_TRAINING=OFF · THERAPEUTIC_RANKING=OFF · PROTECTED_FULL104_OUTCOMES=UNOPENED
```
