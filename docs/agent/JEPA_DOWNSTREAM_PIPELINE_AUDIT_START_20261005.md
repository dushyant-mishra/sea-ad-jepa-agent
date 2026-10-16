# JEPA downstream-pipeline audit — active control point

Date: 2026-10-05 / updated 2026-10-06
Status: `AUDIT_IN_PROGRESS__NO_EXECUTION_AUTHORITY__TRAINING_OFF`

## Purpose

This is the downstream-pipeline audit workstream, separate from Macha's V77 synthetic-world rebuild and separate from real-RNA target qualification. Its purpose is to recover and reconcile the existing qualified JEPA execution pieces into one coherent production-geometry path from the canonical 41,238-address input through view construction, encoder/predictor/teacher mechanics, guarded optimizer update, EMA, checkpointing/resume and representation extraction.

**Training remains OFF.** This audit does not authorize a synthetic or real JEPA run.

## Duplicate-work guard

Do not create a new trainer, a parallel handoff branch, or another downstream-audit PR without first checking this branch/PR and the historical lineages listed below. The repository already contains substantial qualified mechanics and anti-cheat work. The current problem is reconciliation/canonicalization of those pieces, not a blank implementation.

This document is the active downstream-audit ledger for draft PR #218. Historical documents remain evidence and must not be rewritten to appear current.

## Historical audit inheritance

The user-supplied September-27 independent Claude audit has now been reviewed and folded prospectively at:

`docs/agent/JEPA_V46_INDEPENDENT_AUDIT_RETROSPECTIVE_20261005.md`

Its old teacher-fidelity action routing is superseded, but the current downstream audit inherits these durable anti-cheat requirements:

- physical/byte custody does not establish semantic feature-axis correctness;
- narrow-panel repair does not establish full 41K reader authority;
- removing q's visible token is insufficient if q survives in normalization denominators, QC or transformed descendants;
- verdict code must enforce the exact required execution cardinality and reject empty/partial subsets;
- required ablations must be verdict-bearing rather than merely logged;
- execution authority must bind physical execution evidence rather than caller-declared PASS strings;
- historical receipts must remain bound to the exact producer that created them and must not be relabeled as outputs of later repaired code.

These are downstream test/lineage requirements, not a revival of the V46 experimental plan.

## Confirmed historical implementation spine

The audit has recovered the following existing pieces:

1. **V5 inactive mechanics reference** — `src/sea_ad_jepa/v5/inactive_update_reference.py`
   - online encoder, EMA teacher, predictor and AdamW;
   - support-aware packing and scientific weights;
   - keyed dropout addressed by scientific identity;
   - teacher no-grad;
   - gradient gate;
   - exactly one optimizer step per update;
   - EMA after the optimizer step;
   - deterministic checkpoint/restart proof state.
   - Important boundary: the module explicitly identifies itself as a bounded inactive mechanics harness, not a production training runtime.

2. **Authenticated FULL104 streaming/measurement path** — including `full104_masking_streaming_executor_v1.py` and the terminal one-rung executor lineage.
   - authenticates physical block manifests/hashes;
   - binds donor/fold/source identity;
   - binds canonical address registry and target identities;
   - checks raw nonnegative integer-count semantics;
   - applies the frozen read-only normalization/measurement path;
   - cannot authorize training.

3. **V61 q-safe preprocessing successor** — `q_safe_student_preprocessing_v1.py`.
   - removes queried feature q before normalization and every student-visible summary;
   - permits only q-excluded-total or independently fixed-reference normalization;
   - supplies a q-blind teacher-side counts view.

4. **V61 current training-policy successor** — `CurrentTrainingAuthorityV2` plus `CurrentOptimizerStepGuardV4`.
   - new execution code is required to use the V2 authority rather than historical authority schemas;
   - optimizer guard revalidates authority, requires explicit arm-for-step, binds schedule cursor and consumes authorization exactly once;
   - historical direct optimizer calls are not automatically current-authority compliant.

5. **Historical checkpoint/authority guards** exist, including an atomic-checkpoint V2 schema and crash-safe/runtime lineages. They are valuable evidence, but their exact compatibility with the later V3 authority-root graph is not established by their existence alone.

## Concrete findings already established

### F-DP-1 — The downstream implementation is not missing

Earlier searches that did not reveal a default-branch `teacher_student_runtime` entrypoint were insufficient. History contains a substantial qualified V4→V5 teacher/student implementation and later FULL104/runtime/authority successors. Do not rebuild JEPA from scratch.

Disposition: `CURRENT_COMPONENTS_RECOVERED__CANONICAL_CONSUMER_NOT_YET_PROVED`.

### F-DP-2 — Historical neural mechanics and current optimizer authority are not yet visibly reconciled

The recovered V5 mechanics harness performs a direct `optimizer.step()` followed by EMA. The later current policy requires new execution code to pass through `CurrentTrainingAuthorityV2` + `OptimizerGuardV4` and an explicitly armed schedule cursor.

Therefore the old harness cannot simply be declared the current production consumer.

Disposition: `MISSING_CANONICAL_SUCCESSOR_OR_INTEGRATION_PROOF`.

Required closure: positively identify a later consumer that combines the current guard with the qualified mechanics, or construct a thin successor that composes the existing modules without reimplementing JEPA.

### F-DP-3 — Checkpoint authority generation mismatch is open

A recovered atomic checkpoint guard is V2 and binds the older V2 authority-root graph. The later current training authority uses the V3 root graph that introduced first-class biological-specificity, q-safety and provider-backed critical-test authority.

No V3-compatible atomic checkpoint successor has yet been positively identified in this audit.

Disposition: `INDETERMINATE__V3_CHECKPOINT_SUCCESSOR_SEARCH_REQUIRED`.

Do not silently reuse the V2 checkpoint schema under V3 authority.

### F-DP-4 — Physical/runtime adapter branches are not evidence of the neural seam

The N1 physical-lineage adapter authenticates corrected physical inputs and deliberately keeps N1/training unauthorized. The crash-safe synthetic/corrected-source adapter is likewise part of measurement/qualification lineage. Neither should be mislabeled as proof that reader → neural update → current guard → EMA → checkpoint is closed.

Disposition: `QUALIFIED_IN_OWN_SCOPE__NOT_NEURAL_CONSUMER_PROOF`.

### F-DP-5 — Historical semantic-axis and narrow-panel repairs must not leak into current identity authority

The V46 independent audit records an HVS/SEA-AD feature-axis defect in historical gene-labelled analyses and a separate 29-address masked-myeloid repair. The former means byte-reproducible artifacts can still be semantically wrong; the latter was explicitly scoped and does not qualify the remaining 41,209 addresses.

Disposition: `HISTORICAL_SEMANTIC_DEFECT_PRESERVED__SCOPED_REPAIR_NOT_GENERALIZED`.

Required closure: current 41K identity/order/tokenizer mapping must be authenticated directly; no current path may inherit authority merely from the historical 29-address repair.

## Candidate minimal successor architecture — not yet implementation authority

If history does not reveal an already-complete later consumer, the preferred repair is a **thin current-runtime successor**, not a new trainer and not mutation of the historical inactive reference.

Prospective composition:

`41K reader envelope`
→ `q-safe view construction`
→ existing qualified encoder/predictor/teacher mechanics
→ gradient assertions
→ `OptimizerGuardV4.arm_for_step()`
→ guarded optimizer step
→ guard completion assertion
→ EMA
→ V3-compatible atomic checkpoint
→ reload/resume equivalence
→ explicit representation extraction.

Any such successor must initially remain mechanical/synthetic-only and cannot confer real training authority by itself.

## Audit order

1. **Canonical input identity.** Verify the 41,238-address registry, frozen ordering, tokenizer/index mapping, registry digest and any source-family/support metadata consumed by the runtime. Reject arbitrary 96→41K mapping or identity reordering. Include negative tests for historical feature-axis/rank-vs-column mistakes.
2. **Loader and normalization contract.** Trace sparse/dense formats, counts/log transforms, zero-library behavior, library normalization, support masks and any hidden query-value dependence. Ensure the future consumer is compatible with the current production geometry and does not inherit World-A/v1 assumptions.
3. **Mask/view construction.** Identify exactly how teacher and student views are built, what is lawful for each to see, how query addresses are withheld, and whether total count, support, missingness or normalization leaks the hidden value. Test descendants, not just token absence.
4. **Encoder path.** Establish the encoder class/function actually intended for future execution. Record tensor shapes, address embeddings, cell/global tokens and exposed representation families.
5. **Predictor/target path.** Trace predictor inputs and teacher targets. Planted truth/module memberships/oracle statistics are forbidden from optimizer inputs and target construction.
6. **EMA teacher mechanics.** Establish authoritative EMA implementation, ordering, schedule, initialization, dtype/device behavior and serialization. Target-selection experiments must perform zero EMA updates.
7. **Optimizer and gradient flow.** Reconcile the qualified mechanics with `CurrentTrainingAuthorityV2` and `OptimizerGuardV4`. Prove every mandatory trainable tensor receives valid gradients under the intended numerical path. Prevent recurrence of the historical PROD41K/T1 gradient-dead failure.
8. **Mixed precision / numerical path.** Audit fp16/bf16/autocast/scaler and attention kernels. Do not revive the retracted S9 BLAS diagnosis.
9. **Checkpoint serialization.** Resolve the V2→V3 authority mismatch and define a scientifically reproducible current checkpoint containing online/EMA/predictor/optimizer/scaler as applicable, update cursor, RNG state, registry/tokenizer digest, model config, masking/view contract, code provenance and data/split identities.
10. **Checkpoint reload and resume equivalence.** Verify save→load preserves exact semantics and resumed execution matches uninterrupted execution under a prospectively declared tolerance. Legacy T1/PROD41K checkpoints remain forensic only.
11. **Representation extraction.** Provide explicit extraction for online vs EMA and global/cell, gene/query-local and program-level representations. Availability does not qualify `cell_state` or any representation as biology.
12. **Evaluation isolation.** Known synthetic truth is an answer key only. It may not flow into training, target construction or checkpoint selection.
13. **Synthetic checkpoint ladder readiness.** Only after V77 world/instrument qualification is frozen, define checkpoint times and metrics prospectively; never choose interesting checkpoints post hoc.
14. **Workflow/entrypoint audit.** Map historical/current CI and runtime entrypoints and identify one canonical future rehearsal command. Any gate/runner that can issue PASS must reject empty/partial required execution and bind required ablations into its verdict.
15. **Legacy-assumption sweep.** Search constants, shapes, masks, feature counts and configs for 96-feature/700-gene/historical assumptions.
16. **Authority-surface synchronization.** If this audit changes the next authorized technical action, canonical startup surfaces must be updated in the same merge or immediate successor governance change.

## Fail-closed downstream outcomes

Each component ends in one of:

- `CURRENT_AND_VERIFIED`
- `CURRENT_BUT_UNVERIFIED`
- `LEGACY_FORENSIC_ONLY`
- `SUPERSEDED`
- `DEFECT_CONFIRMED__REPAIR_REQUIRED`
- `MISSING_CANONICAL_SUCCESSOR`
- `INDETERMINATE__EVIDENCE_REQUIRED`

Absence of a discovered defect is not a PASS until the current path is positively identified and exercised.

## V77 synthetic-world dependency — updated after S127

The V77 lane is upstream of model rehearsal and is presently **not admissible for checkpoint evaluation**.

Important current evidence:

- `9e0a7d3674fdc6db1df78ad7b1b1c5bff20169c2` built the same-cell 40,000-region ATAC observer and froze real TRAIN RNA geometry from 4,726 cells, 149 donors and 41,238 addresses.
- Marginal RNA sparsity is close, but synthetic dependence is much too weak: median HVG `|corr|` 0.068 synthetic vs 0.329 real; 2.3% vs 56.2% of HVG pairs exceed `|corr| > 0.3`; top-10-PC variance 0.310 vs 0.509.
- Real geometry/random content remains the intended protection: match structural geometry while keeping planted program identity seeded/random so real biological priors cannot leak the answer.
- `831e1c9eac2451e38785c48c8561aed91fd8b11e` found S127: the frozen unweighted module mean under-reads mixed-sign planted modules by construction. Existing affected oracle ceilings are superseded; off-twin REJECT results and the real-vs-synthetic covariance gap remain informative.
- The same S127 commit repairs the ATAC realization-noise scale from 1.0× Gumbel to 0.35×, without changing D2 thresholds/effect sizes, but the signed-projection oracle amendment still requires formal landing and control reruns.

### Frozen ordering for the synthetic lane

1. repair the oracle statistic by explicit signed-projection amendment;
2. rerun unchanged off-twin/negative controls on existing generated data;
3. extract/freeze additional topology targets: correlation degree, community-size distribution, clustering/transitivity, redundancy/nearest-substitute structure and class-conditional covariance;
4. recalibrate background/class covariance against global and local real-TRAIN geometry;
5. regenerate/rebuild all deciding worlds and remeasure every component against unchanged designed recoverability classes;
6. only then resolve S126/C2, run exact-head CI and consider the encoder/checkpoint rehearsal.

The currently generated weak-covariance worlds may be retained for instrument-repair regression/custody, but their ceilings must not be promoted as final scientific evidence.

## Separate real-RNA target workstream

Synthetic worlds must not choose the production teacher target. The real target remains a separate TRAIN-only, zero-encoder-update, zero-EMA-update discrimination gate over prospectively frozen target/representation candidates with leakage, identity and shortcut controls. Do not mix that scientific target-selection work into this mechanical downstream audit.

## Hard boundaries

- `TRAINING = OFF`
- `MULTIMODAL_TRAINING = OFF`
- `500K_PROMOTION = NOT_AUTHORIZED`
- `STAGE4 = NOT_AUTHORIZED`
- `RECOVERABILITY_TEST = SEALED`
- `MORABITO = PROTECTED`
- no production target winner
- no representation winner
- `width=160` is architecture capacity, not biological dimensionality authority
- `cell_state` is not qualified as the designated global biological state
