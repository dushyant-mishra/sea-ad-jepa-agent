# V75 next action pointer

Current phase: **STOP. The synthetic state-qualification ladder has no defined objective.**

Do not run 500K. Do not run 4.553M. Do not build a further synthetic substrate for state
qualification.

## Why this pointer changed

A previous version of this file named "the learned 160-D state" as the next action. That
was wrong and it was written by transcribing a forward plan without auditing whether its
prerequisites existed. Five independent blockers were all true at once:

1. **No defined target.** `AGENTS.md:61` and `ACTIVE_STATE.md:134` both say so. This is a
   closed negative result, not an open choice: three candidate families (T0 block mean, T1
   full gene H_g, TCTX query-self-masked H_g) were causally tested and all three were
   rejected, with complete-H mean R2 deltas of -0.0766 / -0.0939 / -0.0943. The real
   production forward gate found the target ~99% predictable from gene identity alone
   (T1 0.9114 conditional versus 0.9105 identity-only). Three critics: STOP/STOP/STOP.
2. **No trained model.** The only canonical-vocabulary IPB checkpoint,
   `exports/prod41k_teacher_t1_20260823/phase_e_restart_checkpoint.pt`, has
   `global_update_step = 10` and is an engineering smoke.
3. **Wrong vocabulary.** The V75 observer uses 96 `ENSG_SYN_*` placeholders; the encoder
   carries 41,238 canonical addresses.
4. **No dimensional claim to qualify.** 160 is token width. The authority index denies
   5/96/160/224/320/512 as production D authority.
5. **Circularity.** A synthetic-trained model judged against its own generator.

Any one of these blocks the plan.

## What still stands

The V75 100K measurement-architecture qualification is **valid for its own narrow claim** —
that the synthetic generator preserves empirical donor/source/operator/QC geometry at scale.
That claim never depended on a target and is not retracted. Authority remains
`results/v75/V75_100K_MEASUREMENT_ARCHITECTURE_CLOSEOUT_V3_REPAIRED_AUTHORITY.json`,
status `PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED__500K_PROMOTION_INDETERMINATE`.

## The actual next action

The **real TRAIN-only forward target/evidence gate** already specified in
`docs/agent/ACTIVE_STATE.md` under "Next authorized experiment". It is inside
`TRAINING = OFF`:

- zero encoder optimizer updates, zero EMA updates
- TRAIN only, no pathology, no DEV/SEALED
- production-first (~41K addresses), not 4K-first
- distinguish representation loss from identifiability loss
- stratify by N_eff, physical support and retained evidence
- named prerequisite: strict donor-cross-fitted per-address centering of H
- **predeclared promotion criterion: incremental evidence OVER identity**

It produces a target winner, or another qualified STOP. Everything downstream — training,
the representation-role identifiability experiments, the choice among z_cell / {h_g} /
a program subspace, and any dimensional claim — is blocked on its outcome.

Full reasoning and the corrected dependency order:
`results/v76/V76_PLAN_PREMISE_STOP_V3.json`.

TRAINING = OFF. Stage 4 = NOT AUTHORIZED. Real correspondence = UNOPENED.
Morabito = PROTECTED. Recoverability TEST = SEALED.

---

## Superseded text, retained

Kept so the transition is auditable rather than silently overwritten.

> Next action is NOT 500K. It is the learned 160-D state: audit the canonical
> `IPBEncoder(width=160)` in `src/sea_ad_jepa/v4/ipb_jepa.py` and the production
> configuration in `src/sea_ad_jepa/v4/teacher_student_runtime.py`, then freeze a
> prospective measurement-null versus biology-positive state-qualification contract. Do not
> build a second arbitrary 160-D architecture before that audit accepts or rejects this one.

The audit was performed (`results/v76/V76_STATE_PREMISE_REDTEAM_AUDIT_V1.json` and
`_V2_AMENDED.json`) and rejected the premise. The contract must not be frozen.

An earlier version of this file, before provider run 37252622570, described an intentional
RED pre-repair gate and said not to run 100K yet. Both expected RED failures were repaired
and that gate went green at execution head `f863215358772d55fb1b1c9f285e33d2c33e7083`.
