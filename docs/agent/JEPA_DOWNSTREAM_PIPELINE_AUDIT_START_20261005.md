# JEPA downstream-pipeline audit start — 2026-10-05

## Purpose

This is a successor audit workstream, separate from Macha's V77 synthetic-world rebuild. Its purpose is to determine whether the repository contains one coherent, current, production-geometry execution path from the canonical 41,238-address input through training mechanics, checkpointing and representation extraction, and to repair reproducible implementation defects without changing scientific authority.

**Training remains OFF.** This audit does not authorize a synthetic or real JEPA run.

## Why this audit is now necessary

The project has substantially repaired measurement architecture, synthetic-world realism and target-authority governance, but a future known-truth synthetic checkpoint rehearsal is only useful if it actually exercises the same downstream machinery intended for the real system. Historical versioned paths, legacy T1/PROD41K artifacts, hot-patched update primitives, 96-feature assumptions, or incomplete checkpoint semantics could otherwise make a green synthetic result non-diagnostic.

A preliminary default-branch code search on 2026-10-05 did not expose an obvious single canonical execution entrypoint for `optimizer.step`, `torch.save`, `run_update`, or `teacher_student_runtime`. This is an audit signal, **not proof that the functionality does not exist**: history, versioned files or unindexed code may contain it. The successor must trace the repository and commit/PR history rather than infer absence from search alone.

## Audit order

1. **Canonical input identity.** Verify the 41,238-address registry, frozen ordering, tokenizer/index mapping, registry digest and any source-family/support metadata consumed by the runtime. Reject arbitrary 96→41K mapping or identity reordering.
2. **Loader and normalization contract.** Trace sparse/dense formats, counts/log transforms, zero-library behavior, library normalization, support masks and any hidden query-value dependence. Ensure the training reader is compatible with the current production geometry and does not inherit v1 synthetic assumptions.
3. **Mask/view construction.** Identify exactly how teacher and student views are built, what is lawful for each to see, how query addresses are withheld, and whether total count, support, missingness or normalization leaks the hidden value.
4. **Encoder path.** Establish the current encoder class/function actually intended for future execution. Record tensor shapes, address embeddings, cell/global tokens and any representation families exposed.
5. **Predictor/target path.** Trace how predictor inputs and teacher targets are produced. For future synthetic rehearsal, planted truth/module memberships/oracle statistics must be forbidden from optimizer inputs and target construction.
6. **EMA teacher mechanics.** Locate the authoritative EMA implementation, update ordering, decay schedule, initialization, dtype/device behavior and serialization. Verify no target-selection experiment can update EMA.
7. **Optimizer and gradient flow.** Identify parameter groups and actual optimizer step. Add/locate tests that prove every mandatory trainable tensor receives valid gradients under the intended mixed-precision path. Explicitly prevent recurrence of the historical PROD41K/T1 state where loss fell while 48/48 required pre-attention tensors were gradient-dead.
8. **Mixed precision / numerical path.** Audit fp16/bf16/autocast/scaler and attention kernels. Separate environment invocation defects from actual numerical/mechanical defects; do not revive the retracted S9 BLAS diagnosis.
9. **Checkpoint serialization.** Define what a scientifically reproducible checkpoint must contain: model weights, online/EMA distinction, predictor, optimizer/scaler if resumable, step/update number, RNG states, tokenizer/registry digest, model config, masking contract, code/commit provenance and data/split identifiers.
10. **Checkpoint reload and resume equivalence.** Verify save→load preserves exact semantics and that resumed training matches uninterrupted execution within prospectively declared tolerance. Never use legacy T1/PROD41K as biological warm-start authority.
11. **Representation extraction.** Identify explicit APIs for online versus EMA, cell/global, gene/query-local and program-level representations. Do not pre-authorize `cell_state`; extraction availability is not scientific qualification.
12. **Evaluation isolation.** Ensure evaluation cannot feed planted synthetic truth, module memberships, oracle sufficient statistics, TEST outcomes or protected external assets back into training. Known synthetic truth is an answer key, not a training target.
13. **Synthetic checkpoint ladder readiness.** Only after V77 world qualification is complete, define a prospective initialization/early/mid/late/final checkpoint schedule and qualification metrics. Do not select interesting checkpoints post hoc.
14. **Workflow/entrypoint audit.** Map all CI/workflow/runtime entrypoints and historical versioned alternatives. Mark superseded paths clearly and identify or construct one canonical future rehearsal command instead of allowing ambiguous lineage selection.
15. **96-feature / legacy assumption sweep.** Search constants, fixtures, tensor shapes, masks, gene counts, index ranges and config defaults for assumptions inherited from World A, old synthetic fixtures or legacy 700/96-gene target panels.
16. **Authority-surface synchronization.** Any repair that changes the actual next authorized technical action must update the canonical authority/startup surfaces in the same change set or an immediate successor, under the October-5 authority-freshness rule.

## Fail-closed audit outcomes

Each downstream component should end in one of:

- `CURRENT_AND_VERIFIED`
- `CURRENT_BUT_UNVERIFIED`
- `LEGACY_FORENSIC_ONLY`
- `SUPERSEDED`
- `DEFECT_CONFIRMED__REPAIR_REQUIRED`
- `MISSING_CANONICAL_SUCCESSOR`
- `INDETERMINATE__EVIDENCE_REQUIRED`

Absence of a discovered defect is not a PASS until the current path is positively identified and exercised by an appropriate test.

## Relationship to V77

Macha's current V77 work is upstream of model evaluation. Verified commit `d028aef25a4d0d8ca87d638ec6f3eda0307656c4` freezes component-specific sufficient statistics and records the status `SPARSE_LOADER_QUALIFIED__COMPONENT_STATISTICS_FROZEN_AND_CONTROLLED__FULL_V2_REBUILD_PENDING`. The full production-count B/C/D/E rebuild, complete recoverability matrix and D1 graph recovery remain pending. Model evaluation is not yet authorized.

The downstream audit can proceed in parallel because it should not inspect or tune qualification thresholds to future JEPA outcomes. However, **no synthetic checkpoint rehearsal should start until both conditions are satisfied:**

- V77 simulator/oracle qualification has reached a frozen admissible state; and
- this downstream audit has identified a coherent, mechanically qualified execution/checkpoint path.

## Separate real-RNA target workstream

Synthetic worlds must not choose the production teacher target. The real target remains a separate TRAIN-only, zero-encoder-update, zero-EMA-update discrimination gate over the frozen candidate constructions (`T_A`, `T_B1`, `T_B2`, `T_C`, with `T_D` only as its defined modifier), with leakage and shortcut controls. Do not mix this target-selection work into the downstream mechanical audit.
