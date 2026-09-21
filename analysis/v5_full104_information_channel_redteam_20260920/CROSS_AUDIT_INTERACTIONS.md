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
| outside-ledger denominator fraction | `NEW_FINDING` / `OPEN` | **not yet** — see §2 | no | no | **YES** | **YES** | no |
| actual mask detected-token burden | `NEW_FINDING` / `OPEN` | **not yet** | no | **YES** | no | **YES** | no |
| actual mask UMI burden | `NEW_FINDING` / `OPEN` | **not yet** | no | **YES** | no | **YES** | no |
| source-specific target support | `NEW_FINDING` / `OPEN` | **not yet** | no | no | no | **YES** | no |
| source-specific zero target variance | `NEW_FINDING` / `OPEN` | **not yet** | no | no | no | **YES** | no |
| held-out-donor standardization | `NEW_FINDING` / `OPEN` | no — regime unchanged | no | no | **YES** | no | no |
| co-detection partner selection | `PARTIALLY_AUDITED` / `OPEN` | no | **YES** | no | no | no | no |
| target identity × target-zero | `OPEN` | no | **YES** | no | no | no | **YES** (needs a real teacher) |
| calibration-cache tail coverage | `NEW_FINDING` / `CLOSED` for its current role | no — role unchanged | no | no | **YES** | no | no |

---

## 1. Why so few `CLOSED`

Only two rows close. The sparsity value was already audited and stands. The cache
audit closes its own question — *is the cache suitable for its current control-
calibration role?* — and answers yes, while opening a separate question about
capacity calibration that it does not close.

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
establishes that the primary score is blind to donor- and source-level structure
— not because of the standardization, but because the score correlates
*within-donor centred* target and prediction. So the attacker's estimand cannot
express the part of the denominator channel that lives between donors, however
much capacity a G3 attacker is given. **G3 must settle the estimand, not only
capacity and functional form.** This is the single most consequential interaction
in this lane.

**A → G.** The cache over-represents HVS by 9.1× and retains SEA_AD at 1.14%.
HVS has an outside-ledger fraction of exactly zero while SEA_AD's is ~4%. So the
cache's *denominator-channel* composition differs from the population's even more
than its source composition does — the cache is enriched in precisely the source
where the channel is absent.

**B → G5.** If detected-token burden differs across policies at equal address
count, then a margin δ compared across policies is comparing conditions that
removed different amounts of evidence. The equivalence claim would be
conditional on burden, not on policy alone.

**C → terminal masking.** If a target does not vary within a donor, the frozen
scorer returns `r = 0`, contributing `r² = 0` — a *perfect* "no shortcut
detected" score, not a missing value. A source guardrail can therefore pass
because the target was unvarying there. This is the clearest path by which the
terminal verdict could be right for the wrong reason.

**E → F.** Both decompose the same seam — co-detection versus quantitative
co-expression — at different points in the pipeline. A consistent answer across
both would be considerably stronger than either alone.

## 4. What is not claimed

- No biological claim is made by any audit in this lane.
- No audit inspected a terminal masking outcome, D_shared, pathology, or any
  DEV/SEALED outcome.
- Audit F reports **no real number at all**, because no lawful teacher
  representation exists. It is marked
  `CHANGED_INPUT_REQUIRES_REAL_TEACHER_REQUALIFICATION` rather than estimated.
- Audit E's partners are selected within a deterministic address pool, not the
  full 17,186-address universe, and that is stated wherever its numbers appear.
  It is not a claim about which partners production would choose.

## 5. Revised dependency order

The expected order was: close these audits → decide whether masking burden,
estimability or the attacker need repair → freeze G4 → justify G5 → H3 → H4/G2 →
G4 execution → G3 → F13/F14/F15 → terminal masking → training.

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
