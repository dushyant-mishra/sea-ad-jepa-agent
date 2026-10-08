# Cross-audit interactions

Date: 2026-09-20

Status of every channel this lane examined, and what each does and does not
block. **Closure is not overstated**: a channel is marked `CLOSED` only where the
audit actually settled it, and `PARTIALLY_AUDITED` where a real number exists but
does not answer the whole question.

Legend for the blocking columns: `YES` = this finding must be resolved before
that item can be settled; `NO` = independent; `—` = not applicable.

---

## Status table

| channel | state | changes current authority? | blocks G4? | blocks G5? | blocks G3? | blocks terminal masking? | requires training? |
|---|---|---|---|---|---|---|---|
| global measured-zero sparsity (0.8329826626244999) | `ALREADY_AUDITED` / `CLOSED` | no — it is the authority | no | no | no | no | no |
| outside-ledger denominator influence | `NEW_FINDING` / `OPEN` — A1/A2 established, model recoverability open | **not yet** — see §2 | no | no | **YES** | **YES** | no |
| per-address burden heterogeneity | `ESTABLISHED` / FULL104 reconnaissance | no | no | no | no | no | no |
| reduced-pool screening burden enrichment | `ESTABLISHED` / `REDUCED_POOL_DIAGNOSTIC` | no | no | **YES** as motivation | no | no | no |
| actual fold-specific policy burden | `OPEN` / not yet measured | no | no | **YES** | no | **YES** | no |
| source-specific target support | `NEW_FINDING` / FULL104 reconnaissance | **not yet** | no | no | no | **YES** | no |
| fold-aware scorer estimability (C2) | `OPEN` — authenticated rerun required | **not yet** | no | no | no | **YES** | no |
| held-out-donor standardization / score scope | `NEW_FINDING` / `OPEN` | no — regime unchanged | no | no | **YES** | no | no |
| attacker fit-objective weighting | `NEW_FINDING` / `OPEN` | no — attacker unchanged | no | no | **YES** | **YES** | no |
| H3 donor-vs-target precision decomposition | `DESIGN_OPEN` / outcome-blind | no | no | no | no | **YES** after G5 | no |
| co-detection/quantitative partner decomposition | `PARTIALLY_AUDITED` / reduced-pool, estimand-mismatched | no | **YES** | no | no | no | no |
| current V5 query-local latent decomposition | `DESIGN_OPEN` | no | **YES** | no | no | no | **YES** (needs a real teacher) |
| calibration-cache tail coverage | **`NO_ISSUE_FOUND`** — behaves exactly as designed | no — role unchanged | no | no | no | no | no |

---


## Scope firewall

This lane is governed by `FULL104_SCOPE_AND_HISTORICAL_FIREWALL.md`. In
particular, `REDUCED_POOL_DIAGNOSTIC`, `FIXTURE_ONLY`, and
`HISTORICAL_SUPPORTING_ONLY` results may motivate tests but may not set current
FULL104 thresholds, margins, policies, target eligibility, or terminal claims.

## 1. Why so few `CLOSED`

Two rows settle. The sparsity value was already audited and stands. The cache
audit **found no issue**: the cache is equal-donor-weighted by design and matches
that target to within 0.05%, and the two defects an earlier revision reported
were artifacts of comparing it against the population marginal, which the design
explicitly rejects. A separate and narrower question — whether equal-donor
weighting is right for *capacity* calibration — is left open and assigned to G3.

Everything else is `OPEN` because these audits were built to **establish whether
a mechanism exists**, not to decide what to do about it. Establishing the
mechanism is the deliverable; the policy response is a separate decision that
must not be made in the same step.

## 2. Why nothing changes current authority yet

Several findings *would* justify a change. None is applied, on purpose:

- **The denominator channel** (Audit A) is a real, strongly source-dependent
  influence on every visible feature. But repairing it means choosing between
  re-deriving `source_library` from ledger mass, keeping the biological library
  and modelling the channel, or masking differently — three different scientific
  positions with different consequences for what the representation means.
- **Burden asymmetry** (Audit B) is measurable, but "fix it by equalising
  detected-token burden instead of address count" is a redefinition of the
  masking contract, not a bug fix.
- **Source estimability** (Audit C) may imply the eligibility universe and the
  source-balanced guardrails measure different populations. Shrinking the target
  set after seeing which targets are weak is exactly the move that must not be
  made casually.

Each is recorded as `PROPOSED_REPAIR_REQUIRED` in its own report where it
applies, with the repair options stated and none selected.

## 3. Interactions that matter

**A → D → G3.** The denominator channel is partly source-level. Audit D
establishes that the primary score is blind to **pure between-donor/source
location-scale structure**
— not because of the standardization, but because the score correlates
*within-donor centred* target and prediction. So the attacker's estimand cannot
express the part of the denominator channel that lives between donors, however
much capacity a G3 attacker is given. **G3 must settle the estimand, not only
capacity and functional form.** This is the single most consequential interaction
in this lane.

**A → G, withdrawn as a concern.** An earlier revision claimed the cache was
distorted because it over-represents HVS — the one source whose outside-ledger
fraction is exactly zero — relative to the population. That comparison used the
wrong baseline. The cache is equal-donor-weighted **by design**, so that large
sources cannot dominate by cell count alone, and it matches that design target to
within 0.05%. Its composition is a deliberate choice, not a distortion, and the
denominator channel does not make it one. What remains genuinely open is narrower
and belongs to G3: whether equal-donor weighting is the right weighting for
*capacity* calibration specifically, as distinct from for a source-balanced
score.

**G3 fit objective.** The full-data ridge is cell-weighted even though the frozen
production scientific mass is donor-uniform. A separate source/donor-balanced
fit would instead optimize the anti-cheat score. These are distinct questions;
G3 must compare `CURRENT_CELL_WEIGHTED`, `PRODUCTION_OBJECTIVE_MATCHED`, and
`SOURCE_DONOR_BALANCED_DIAGNOSTIC` prospectively before selecting any replacement.

**H3 precision.** NPH52 contributes only 4–5 held-out donors per fold while each
source gets 1/3 of the primary score. H3 therefore needs target-only,
donor-only-within-source, and paired target+donor bootstrap contrasts to determine
whether precision is donor-limited. No per-source eligibility threshold is
invented from this geometry.

**G4 technical-only decoy.** Historical support/source shortcut findings motivate
—but do not numerically calibrate—a prospective `F-technical-only-decoy`. Any G4
content functional must outperform lawful source/operator/depth/sparsity/support
geometry alone before it can be frozen.

**B → G5.** The reduced-pool diagnostic establishes a plausible burden-enrichment
mechanism, not the production burden difference. G5 remains blocked until the
actual fold-specific full-universe policy masks are measured prospectively. If
those burdens differ at equal address count, a single margin δ would compare
conditions that removed different amounts of evidence. The equivalence claim would be
conditional on burden, not on policy alone.

**C → terminal masking.** If a target does not vary within a donor, the frozen
scorer returns `r = 0`, contributing `r² = 0` — numerically identical to an
estimable zero-correlation result. The terminal raw evidence schema currently
loses that distinction. A source guardrail can therefore pass
because the target was unvarying there. This is the clearest path by which the
terminal verdict could be right for the wrong reason.

**E → F.** The old scalar seam is historical motivation only. Audit E must first
be recomputed under production-aligned donor/source conditioning; the future F
measurement is instead the multivariate query-local latent decomposition required
by current V5 authority.

## 4. What is not claimed

- No biological claim is made by any audit in this lane.
- **Audit G found no issue.** The calibration cache behaves exactly as designed.
  An earlier revision of that report claimed two defects; both were measured
  against the population marginal, which the design explicitly rejects, and both
  are withdrawn. The error and its cause are recorded in that report rather than
  removed.
- No audit inspected a terminal masking outcome, D_shared, pathology, or any
  DEV/SEALED outcome.
- Audit F's scalar fixtures are `HISTORICAL_SUPPORTING_ONLY`; they do not define
  the current V5 target. The real query-local latent decomposition is `DESIGN_OPEN`
  and requires a lawful teacher.
- Audit E's partners are selected within a deterministic address pool, not the
  full 17,186-address universe, and that is stated wherever its numbers appear.
  It is not a claim about which partners production would choose.

## 5. Revised dependency order

The expected order is now: finish production-aligned A/B/C/E instrument closure →
settle masking burden/estimability/attacker estimands → freeze G4 including the
technical-only decoy → justify G5 → H3 target-vs-donor precision → H4/G2 → G4
execution → G3 capacity/functional-form/fit-objective challenge → current V5 F
latent-state decomposition and remaining F13/F14/F15 → terminal masking → training.

Audit D changes one step. G3 was scoped as capacity and functional form; it now
also requires settling the estimand, because a capacity-matched attacker
inheriting the current within-donor centred score inherits its blindness to
donor- and source-level channels. That is a design question, and it sits upstream
of building any stronger attacker.

Nothing here justifies proceeding to G4/G5 mechanically. Audits B and C both bear
on whether the current masking estimand is well posed, and that question should
be settled before a margin is attached to it.

```
TRAINING_OFF
```
