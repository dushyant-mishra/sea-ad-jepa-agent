# Runtime target-neutrality invariant — 2026-10-07

Status: **MECHANICS-ONLY RUNTIME; SCIENTIFIC TARGET/LOSS AUTHORITY REMAINS UNRESOLVED**

This checkpoint records a historical-spillover constraint for PR #224 and the later PR #223 / V77 join. It does not select a target, loss, representation, uncertainty model, EMA half-life, or production operating point. Training and Stage A remain OFF.

## Recovered scientific principle

Commit `6c576cec1aa4a8fdab863fae64eacced7945b65b` restores the project-wide rich-teacher / partial-student identifiability principle:

- richer teacher evidence is scientifically desirable when it improves biological fidelity;
- the partial-RNA student should predict only target structure statistically supported by its lawful observations;
- under deterministic squared error the best possible student is a conditional expectation of the teacher state given student evidence, not the realized teacher-only information;
- teacher-private biological evidence remains irreducible uncertainty unless the student observations determine it;
- shortcuts must be controlled independently of teacher richness;
- future multimodal teacher evidence such as ATAC or SCENIC+ does not license deterministic point matching of modality-private realization-level state.

Current classification from that audit:

`RICH_TEACHER_DESIRABLE__FULL_RICH_STATE_NOT_GENERALLY_IDENTIFIABLE_FROM_PARTIAL_RNA`

and TD58 is restricted to:

`EVIDENCE_FOR_SHARED_PREDICTABLE_RELATIONAL_STRUCTURE__NOT_LICENSE_FOR_FULL_RICH_TEACHER_MATCHING`.

## Consequence for the current V5 runtime harness

`src/sea_ad_jepa/v5/inactive_update_reference.py` currently computes a deterministic block-level student-prediction versus EMA-teacher target loss. That remains acceptable only as a **bounded mechanics harness** used to exercise:

- backward/gradient mechanics;
- guarded AdamW stepping;
- GradScaler skip behavior;
- optimizer-completion-before-EMA ordering;
- presentation-normalized EMA mechanics;
- checkpoint/restart determinism and provenance.

The numerical value of that harness loss is **not** scientific evidence that the full teacher state is the correct Stage-A target, and decreasing that loss is not a target-qualification success criterion.

The runtime must remain capable of transporting a later qualified target contract without deciding whether that target is:

1. a shared/cross-view state demonstrably predictable from partial RNA;
2. a conditional mean or distribution over richer teacher state;
3. a central state plus biological uncertainty;
4. an abstention-capable target with teacher-private components explicitly excluded from point prediction.

## Required joined-handoff checks

Before any bounded V77 mutation rehearsal is interpreted scientifically, the joined contract must state explicitly:

1. teacher-visible evidence;
2. student-visible evidence;
3. which target components are intended to be shared/predictable;
4. which teacher-private components are excluded from deterministic point matching;
5. uncertainty or abstention semantics for missing evidence;
6. held-donor / held-source predictability controls;
7. evidence-response behavior as lawful student evidence increases;
8. that runtime/mechanics success is separated from scientific target success.

No runtime receipt, optimizer proof, EMA proof, q-safety proof, checkpoint digest, or loss decrease can substitute for those scientific requirements.

## Standing hard boundaries

`TRAINING=OFF`

`STAGE_A_EXECUTION=OFF`

`MULTIMODAL_TRAINING=OFF`

`500K=NOT_AUTHORIZED`

`STAGE4=NOT_AUTHORIZED`

`TEST=SEALED`

`MORABITO=PROTECTED`

No target, representation, estimand, weighting rule, threshold, or uncertainty model is selected by this runtime work.
