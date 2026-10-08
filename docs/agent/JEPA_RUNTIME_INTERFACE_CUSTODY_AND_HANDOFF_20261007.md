# JEPA runtime/interface custody and handoff — 2026-10-07

Status: **AUDITED CUSTODY CHECKPOINT — NON-AUTHORIZING**

This document is a durable handoff for the current runtime/shared-interface convergence work and the cross-lane scientific constraints recovered during the 2026-10-07 audit. It is intended to let a new agent continue without reconstructing the state from chat history.

## Canonical live surfaces

### Runtime

- Draft PR #224: `Converge canonical V5 runtime safety path`
- Accepted runtime checkpoint: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
- At that checkpoint all three relevant GitHub workflows were GREEN:
  - `v5-inactive-runtime-step-guard`
  - `v64-runtime-core-reconciliation`
  - `Current authority surface guard`
- Runtime remains non-authorizing. No production training or protected-data execution authority is granted.

### Shared qualification interface

- Old PR #223 is superseded for handoff purposes by a clean successor restack.
- Draft PR #226: `Validate shared qualification V2 on canonical V5 runtime`
- PR #226 is stacked directly on accepted runtime checkpoint `9d00684e...`.
- The restack deliberately transplanted only qualification/interface code, qualification tests, the two V5 runtime-binding integration tests, and the shared-interface workflow. No older `src/sea_ad_jepa/v5/*` files from #223 were transplanted.
- PR #226 is mergeable and its `shared-qualification-interface-v1` workflow passed on the stacked runtime tree.
- `BoundRuntimeMutationProofV1` is diagnostic-only; mutation-proof promotion requires the typed presentation-EMA V2 proof.
- Executed q-safety remains a separate proof and is not upgraded by runtime provenance alone.

## Authenticated low-level architecture lineage

The current reusable mechanical lineage was re-audited against later scientific branches before handoff.

Accepted reusable mechanics:

- V5 keyed student encoder implementation (`KeyedIPBEncoderV2Reference`): unchanged through later V47/V48/V63 branches checked in the audit.
- V4 IPB/predictor mechanics: unchanged through V63.
- V4 gene tokenizer mechanics: unchanged through V63.
- Teacher encoder structural mechanics: initialized as a parameter-identical copy of the authenticated student encoder and advanced by guarded EMA.

Important limitation: this authenticates low-level mechanics only. It does **not** select a biological teacher target, scientific target representation, or production objective.

V43 and later target-discovery work are research/scientific target layers, not a replacement low-level encoder authority.

## EMA authority correction

A historical-spillover audit found that a fixed scalar EMA momentum `.996` could not be carried forward as current authority.

Recovered project history distinguishes:

- older V3 authority: `.996`, constant schedule, one EMA update after each proven valid optimizer step;
- later V5 authority: EMA timescale remained OPEN and historical `.996` was explicitly not to be silently inherited;
- candidate half-life `16,249` successful presentations: candidate evidence only, not frozen authority.

The current canonical rehearsal mechanics therefore use presentation-normalized EMA:

`momentum = exp(log(0.5) * presentations_this_update / half_life_presentations)`

with teacher age measured in successful base-cell presentations.

The numerical half-life remains an explicit rehearsal input and is **not** a selected production value.

The runtime now binds:

- presentation unit;
- half-life identity;
- parent checkpoint/runtime source;
- completed guard receipt;
- actual presentations in the update;
- parent/child teacher-age arithmetic;
- physical persisted/reloaded typed continuation proof.

Direct legacy dictionary persistence and constant-momentum successor paths were retired from the canonical surface. Private implementation modules are fail-closed against direct import and are themselves included in transitive runtime provenance/CI.

## Runtime mechanics proved so far

The accepted runtime path physically exercises:

1. actual V5 AdamW optimizer;
2. GradScaler finite path;
3. unscale-before-gradient-validation;
4. physical GradScaler non-finite skip detection;
5. optimizer-step completion before EMA;
6. no EMA advance after rejected/incomplete/skipped optimizer step;
7. presentation-normalized EMA;
8. online/predictor/teacher/optimizer/scaler/cursor checkpoint state;
9. deterministic bounded interruption/reload for the tested AMP trajectory;
10. physical checkpoint write;
11. artifact SHA-256 verification before deserialization;
12. verified reload against current premise and runtime provenance;
13. typed presentation-EMA continuation with configuration and teacher-age binding.

The physical proof remains explicitly non-authorizing for execution, training and production promotion.

## Rich-teacher / partial-student scientific invariant

The runtime audit incorporated the target-program correction recorded elsewhere in project history:

**RICH_TEACHER_DESIRABLE__FULL_RICH_STATE_NOT_GENERALLY_IDENTIFIABLE_FROM_PARTIAL_RNA**

If teacher evidence is `T`, student evidence is `C`, and query is `q`, a deterministic squared-error student is bounded by the conditional expectation of the teacher target given the student's evidence. Teacher-private realization-level information cannot be recovered when it is genuinely absent from the student's observations.

Therefore:

- richer teacher evidence is desirable;
- the student should predict only the shared/predictable component supported by its admitted evidence;
- teacher-private state may require distributional prediction, uncertainty, or abstention;
- adding ATAC, SCENIC+, or other modalities to the teacher does **not** license penalizing the RNA-only student for failure to guess an unrecoverable realization;
- the deterministic teacher-block loss inside the V5 runtime is a **mechanics fixture only**, not target-semantic authority.

No target, representation, uncertainty model, estimand, weighting rule or deciding threshold is selected by runtime convergence.

## Historical row/provenance invariant

The audit explicitly recovered two historical failure classes that must constrain the joined adapter/runtime path.

### TD23 / TD33 row-addressing corruption

B-side `sample_row` reset to local `0..24999`. Treating that reset/local coordinate as the preserved global expression row produced a false RNA relationship around `0.3906061`; correct global-row addressing produced about `0.0062546`.

Durable classification: older analyses with unproven B-side addressing are `ROW_BINDING_UNVERIFIED`.

### September-8 source-row/value authority repair

Historical execution code could authenticate metadata or a payload without proving that the values consumed came from the intended physical source row. The repair required, among other checks:

- `source_row_index == expression_row`;
- source cell identity and donor identity match the bound logical row;
- source-global `expression_row` remains distinct from block-local `row_index`;
- the selected block-local row is the row actually validated;
- source digest/matrix slot/feature-space are authenticated;
- consumed values are parsed from and coupled to the authenticated payload bytes.

Standing invariant:

**coordinates, logical identity, payload provenance, and consumed expression values must form one inseparable proof chain.**

The final joined audit must attack at least:

- global-row versus local-row substitution;
- reset-index substitution;
- correct digest / wrong selected row;
- correct metadata / wrong values;
- correct logical row / wrong physical payload location;
- query leakage;
- raw source/operator shortcut leakage.

## Macha / V77 lane state relevant to handoff

The Macha synthetic lane remains scientifically useful but must stay inside its authority boundary.

Key accepted results/constraints:

- repaired S146/S147 support work remains useful synthetic evidence;
- S149 supports strong measurement-composition confounding of pooled topology, but the ~88.85% value is cell-mixture-specific rather than a qualified donor-population estimand;
- current within-cohort envelope/S159 machinery is diagnostic and `NEEDS_REPAIR`, not calibration authority;
- 24 bootstrap replicates do not provide unexplained sealed-challenge tail-quantile authority;
- S157 establishes an important negative result: exact same-assay RNA semantic twins remain `NON_IDENTIFIABLE_BY_DESIGN`;
- raw source/operator identity is an exploratory shortcut positive control, not an automatically authorized production covariate;
- lawful physical measurement descriptors must be audited for dataset/operator identity-proxy behavior;
- SCENIC+, ATAC and other regulatory objects are not automatically independent evidence; circular construction from the same RNA must be classified explicitly;
- Macha should not do independent optimizer/EMA/checkpoint architecture work.

The next Macha mutation work is blocked only on the final joined adapter execution audit, not on further core runtime redesign.

## Immediate next gate

Before handing Macha bounded synthetic mutation authority, execute one joined path:

`repaired V77 synthetic world -> authenticated adapter -> QualificationBatchV1 -> shared qualification V2 -> canonical V5 runtime -> ZERO_UPDATE q-safety/row-value attacks`

Required outcomes:

1. actual adapter physically executes every q-safety transformation required by the interface;
2. q-safety proof is generated from executed transformations, not policy metadata;
3. row/value provenance attacks above fail closed;
4. V1 runtime proof cannot promote mutation proof;
5. only typed V2 physical continuation proof can promote runtime mutation status;
6. rich-teacher target semantics remain science-lane owned;
7. final bypass/historical-spillover audit is clean.

Only after those gates are GREEN should the exact runtime/interface/adapter SHAs be frozen for a **small bounded synthetic mutation rehearsal**.

## Hard boundaries

Still unchanged:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`

No target, representation, estimand, weighting rule, deciding threshold, uncertainty model, production EMA timescale or biological winner is selected here.

## Custody references

Large scientific/chat-runtime files were already independently hashed and recorded in immutable GitHub custody commit:

`cb7a98d00359eecece8525b23c43fbc8578c69ef` — `V73 custody: record all chat-runtime artifacts with exact hashes`

That custody record includes exact sizes/SHA-256 values and, where applicable, ZIP inventories for:

- `WSL execution issue.txt`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
- `checkpoints.zip`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `expression.zip`
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
- `t1_checkpoint_u0200.zip`
- `Status and Repair Plan.txt`

The two expression parts reassemble to SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7` and the supplied checksum table matched that assembly in the prior custody audit.

Large binary bytes are deliberately not duplicated into ordinary Git history. Exact cryptographic custody plus recovery provenance is the repository authority for those artifacts; hash custody alone does not imply scientific validity.

## Newly recovered local-only / external candidates reported on 2026-10-07

These were reported from the user's local machine and are scientifically relevant to architecture history. They are recorded here so their existence is not lost. Unless separately present in GitHub custody, paths/hashes marked `USER_REPORTED` are not claimed to have been independently rehashed by this runtime session.

- `C:\Users\dushy\Downloads\JEPA_CHAT_EXCLUSIVE_FINAL_SOURCES_20261005.zip`
  - reported SHA-256: `7A036B5CCF9965088D7730A54715E257E478D9BB7D768D34FE37E4BA3441BF34`
  - contains text describing an approximately frozen runtime with `.996`, but also states that online-versus-EMA state authority is unresolved;
  - classification: historical/custody evidence, not current EMA-timescale authority.

- `C:\Users\dushy\Downloads\JEPA_NEW_CHAT_HANDOFF_20260916_V5_CURRENT.zip`
  - reported content: V5 has EMA mechanics but not final EMA-timescale authority and prohibits inheriting historical `.996`;
  - classification: high-value current-authority historical evidence.

- `C:\Users\dushy\Downloads\TEACHER_STUDENT_V5_ELIGIBLE_DONOR_ESTIMATOR_CANDIDATE_20260909.zip`
  - reported content includes `ema_scale_authority_v1.py`, tests, and candidate half-life `16,249` successful presentations;
  - accompanying status says criterion/numeric selection were not frozen authority;
  - classification: candidate-only evidence.

- `C:\Users\dushy\Downloads\TEACHER_STUDENT_UNIFIED_V3_SELF_CONTAINED_REVIEW_PACKAGE.zip`
  - reported older V3 configuration: EMA `.996`, constant schedule, one EMA update after each proven valid optimizer step;
  - classification: historical V3 authority, not current V5 authority.

- `C:\Users\dushy\Downloads\JEPA_NEW_CHAT_HANDOFF_20260929_V63_AUDITED.md`
  - reported later governance: `TRAINING=OFF`, `TD60=BLOCKED`, architecture/biological-specificity authority incomplete;
  - classification: later governance evidence.

- local recovery branch `custody/local-only-jepa-recovery-20261006` at `c86dac574bdf99f228d3e2040673855c701b10c4`
  - reported as already pushed to origin after exhaustive local branch/worktree/stash review;
  - old PROD41K/T1 checkpoint classified forensic-only because historical fp16 path contained 48 gradient-dead mandatory tensors.

- `D:/Jepa project/CONTEXTUAL_TEACHER_TARGET_V1_CODEX_PACKET_V2`
  - reported files include `student_singleton_predictor_ema_direct.py` and `student_singleton_predictor_ema_qcontext.py`;
  - recovery audit classifies this packet as forensic reference, not current authority.

## Process / self-audit lessons from this cycle

The following operational errors occurred and are explicitly preserved rather than hidden:

- several no-op/stray refs were accidentally created during early branch operations; they carried no unique runtime content;
- one checkpoint source file was accidentally replaced from an incomplete view and temporarily lost two public functions; self-audit caught it, the exact prior Git blob was restored, and CI was rerun before acceptance;
- an orphan no-op Git commit object was created during a Git-data staging attempt without moving a branch ref;
- a temporary marker file was accidentally added during PR #226 staging and then removed;
- a static provenance test became stale after the canonical wrapper refactor; it was replaced with a behavioral check of the exported runtime-source manifest rather than weakened.

These incidents reinforce the project rule:

**bounded change -> RED -> minimal repair -> GREEN -> adversarial self-audit -> historical spillover check -> GitHub custody checkpoint -> only then advance.**
