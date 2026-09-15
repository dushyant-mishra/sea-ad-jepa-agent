# V5_TEACHER_STUDENT_EMA_ARCHITECTURE — canonical draft

Date: 2026-09-15
Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`

This document consolidates the current teacher/student/EMA architecture and the unresolved scientific authority boundaries. It is a design/governance document only.

It does **not** authorize production training, D_shared execution, protected-outcome inspection, representation changes, residualization, or target substitution.

Standing terminals remain:

- `TRAINING_OFF`
- `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`
- `CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`
- `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`
- `SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN`
- `PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`
- `MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN`
- `BATCH_TECHNICAL_VS_BIOLOGICAL_DECOMPOSITION_NOT_IDENTIFIABLE_IN_FULL104`

## 1. Bound evidence lineage

### 1.1 Existing consolidated mechanics

Mechanics lineage is preserved on:

`repair/v5-dshared-authority-v2-20260914 @ 3717c9c0a292dfcd883949d5d0bf36d263f79300`

Key files:

- `src/sea_ad_jepa/v4/teacher_student_runtime.py`
- `src/sea_ad_jepa/v4/ema.py`
- `src/sea_ad_jepa/v5/qualified_teacher_student_runtime_v1.py`
- `src/sea_ad_jepa/v5/qualified_teacher_target_receipt_v1.py`

The V4 runtime is the consolidated historical mechanics implementation. Its numerical configuration is historical mechanics evidence, not current V5 scientific authority.

The V5 wrapper explicitly fails closed on the legacy V21/T0 target receipt, requires an explicit current-V5 dataset-derived runtime configuration, and leaves `production_training_authorized = false`.

### 1.2 Current Layer-2 empirical evidence

Claude closeout:

`analysis/v5-layer2-cross-view-shortcut-claude-20260915 @ 219831b899b914984369c7a41828bf750554d1d9`

Established there:

- measurement-state shortcut not demonstrated at the tested linear model class;
- recurrent within-donor molecular-view predictive information beyond measured Q_DEPTH/Q_DETECT across all three sources;
- donor-generalizable linear cross-view signal demonstrated in SEA_AD at this model class, not demonstrated in HVS/NPH52;
- context decomposition independently reproduced;
- strong estimand sensitivity characterized;
- the earlier pooled “context dominance” interpretation is not a population-level authority;
- residual-over-context remains specification-only;
- training remained OFF and D_shared remained sealed.

### 1.3 Target-identity red-team draft

`docs/agent/V5_TARGET_IDENTITY_SHORTCUT_AUDIT_SPEC_DRAFT_20260915.md`

This identifies a distinct shortcut family not closed by the Layer-2 context/measurement analysis.

## 2. Architecture already considered mechanically strong

The following mechanics are retained as the candidate production skeleton unless future review discovers a direct defect.

### 2.1 Online/student encoder

- receives gradient from the JEPA objective;
- updated by AdamW only after fail-closed gradient validation;
- hidden target expression values/tokens are absent from the student encoder input;
- scientific selection and weighting must be supplied externally by separately frozen authority.

### 2.2 Predictor

- predicts hidden teacher block states from target-address query information plus visible student state;
- receives optimizer gradients;
- must not receive teacher hidden states, hidden target expression values, protected outcomes, or unapproved context metadata as inputs.

### 2.3 EMA teacher

- initialized as an exact copy of the online encoder;
- remains `eval()`;
- all teacher parameters have `requires_grad=False`;
- teacher outputs are no-grad/detached targets;
- teacher updates only after a proved successful online optimizer step;
- floating parameters/buffers follow EMA, non-floating buffers are copied exactly;
- optimizer and EMA progress must remain synchronized.

### 2.4 Required chronology

The repaired fail-closed sequence remains:

`fp16 forward -> backward outside autocast -> unscale -> protected-gradient gate -> optimizer step proved -> Adam exp_avg live -> Adam exp_avg_sq live -> EMA -> checkpoint/telemetry acceptance`

Mixed-precision step skips must never advance EMA.

## 3. Historical numerical geometry is not V5 authority

Historical mechanics currently preserve values including:

- width 160;
- 4 heads;
- 6 blocks;
- effective batch 128;
- microbatch 8;
- 4 views;
- mask fraction 0.40;
- 16 target blocks;
- EMA momentum 0.996.

These numbers remain useful for forensic/mechanics replay only.

Current V5 numerical authority must be derived from the authenticated FULL104 substrate and the separately frozen support/rank/schedule/masking authority. No historical default may silently become V5 biological authority.

## 4. Teacher target semantics remain the central unresolved authority

The existence of a mechanically correct EMA teacher does not establish what its target should mean scientifically.

Current inherited candidate semantics are approximately:

For cell i, measured support M_i and hidden target block B_ib:

`H_i^T = E_bar_theta(full measured support M_i)`

`z_ib^T = LN(mean_{g in B_ib} H_ig^T)`

and the predictor minimizes a weighted squared error to `stopgrad(z_ib^T)`.

This is inherited mechanics, not yet frozen V5 target authority.

Before freezing, the authority must decide whether final-layer normalized block means are actually the intended target object, rather than merely a historical implementation convenience.

## 5. Newly elevated blocker: target-identity shortcut

The inherited predictor currently builds hidden-target queries from the online encoder's trainable gene-identity embedding table.

This permits the direct parameter path:

`hidden target gene ID -> predictor query -> JEPA gradient -> online gene-identity embedding -> EMA teacher -> future teacher target`

Hidden target expression remains absent, so this is not value leakage. The concern is different: target address identity may become a co-adapting solution channel shared by predictor and future teacher.

A second related issue remains even if the direct shared-parameter path is removed: teacher states themselves contain stable gene/address identity information. An identity-only predictor may therefore explain a nontrivial fraction of target loss without using cell-specific molecular evidence.

Current terminal:

`TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

### 5.1 Preferred design candidate — NOT YET FROZEN

Preferred candidate for independent review:

**decouple target-address conditioning from the online encoder's trainable molecular gene-identity table.**

Target identity remains available as an addressing signal, but the predictor query should use a replay-stable fixed/separate address representation that cannot receive JEPA gradients into the online encoder embedding table.

This candidate is preferred over deleting target identity entirely because the predictor must know which hidden address/block is requested.

It is also preferred over residualizing the teacher target by gene identity because that would redefine the target before evidence shows such surgery is necessary.

### 5.2 Required qualification

The architecture must be compared under identical frozen teacher targets, cells, masks, folds, weights and loss geometry using at least:

- identity-only/shared-current query;
- identity-only/fixed-address query;
- full molecular/shared-current query;
- full molecular/fixed-address query;
- detached-online-identity diagnostic;
- cell-permuted molecular memory while retaining target IDs;
- target-ID perturbation where support/shape makes it lawful.

Primary scientific question:

Does visible cell-specific molecular memory produce a prospectively meaningful improvement beyond target address identity under the same target/loss geometry?

Do not label that increment biology.

No numerical pass threshold is invented in this document. It must be frozen prospectively before objective-aligned results are inspected.

## 6. Context shortcut handling after Claude closeout

Claude's closeout changes the design pressure substantially.

The strong pooled context R2 observed in reconnaissance is estimand-sensitive. Under empirical/FULL104 weighting the context R2 falls materially and the molecular increment increases substantially.

Therefore:

- do not erase source/operator-associated structure from the representation;
- do not make measurement-decorrelation a default objective;
- do not promote residual-over-context merely because pooled reconnaissance appeared context-dominated.

Residual-over-context remains a defensible optional credit-assignment mechanism:

`prediction = stopgrad(frozen_context_baseline(context)) + molecular_increment(visible_molecular_state)`

with loss against the complete unmodified target.

But it should be implemented only if a prospective objective-aligned qualification demonstrates that context rediscovery remains an actionable shortcut under the final target geometry and frozen production estimand.

Current status:

`CONTEXT_SHORTCUT_HANDLING_NOT_YET_FROZEN`

Recommended current posture:

`QUALIFY_FIRST__DO_NOT_HARD_CODE_RESIDUAL_BASELINE_YET`

## 7. Masking remains an independent anti-cheat authority

Context/measurement/target-identity shortcut controls do not solve local correlated-gene interpolation.

Historical V4 contains graph-expanded Pearson masking. Current repaired runtime contains graph-free uniform masking. Neither is current V5 authority.

Required masking audit remains outcome-blind and should compare:

- graph-free uniform masking;
- historical graph-expanded masking as a diagnostic;
- donor/source-recurrent or cross-source-consensus dependency-aware hybrid masking.

Required metrics include:

- correlated-partner exposure;
- address coverage;
- mask-budget concentration;
- rare-address coverage;
- source/operator dependence;
- deterministic replay;
- failure behavior under sparse measured support.

Do not choose structural ratio from D_shared or protected downstream outcomes.

## 8. Scientific training estimand must remain external to mechanics

Claude demonstrated materially different context/molecular magnitudes under different lawful weightings.

Therefore mechanics must accept externally frozen scientific weights and must never infer the estimand from observed representation quality.

At minimum preserve separate consideration of:

- empirical/FULL104;
- source-uniform;
- donor-primary/operator-balanced.

No averaging of these estimands into a synthetic compromise is authorized by this document.

## 9. EMA authority: preserve mechanics, replace historical time convention prospectively

The EMA mechanism itself is retained.

The historical fixed `0.996` is not V5 authority.

Preferred prospective convention is presentation-normalized EMA half-life:

`m_u = exp(log(0.5) * p_u / H)`

where:

- `p_u` = authorized scientific presentation mass consumed by the accepted update;
- `H` = frozen half-life measured in the same presentation unit.

This makes teacher timescale invariant to changes in packing/microbatch/update geometry.

The exact presentation unit and half-life remain unresolved until the scientific schedule/estimand is frozen.

Current status:

`EMA_MECHANICS_ESTABLISHED__V5_TIMESCALE_AUTHORITY_NOT_YET_FROZEN`

## 10. Canonical separation of authority

The future executable V5 training authority should bind these layers independently:

1. authenticated FULL104 substrate root;
2. primary representation authority;
3. scientific estimand / cell-weight authority;
4. teacher-target semantic authority;
5. target-address query authority;
6. masking authority;
7. objective-aligned shortcut-gate authority;
8. production model/rank geometry;
9. schedule/packing geometry;
10. presentation-normalized EMA timescale;
11. fail-closed optimizer/gradient/EMA mechanics;
12. immutable receipt binding all upstream roots.

No one layer may silently widen another.

## 11. Proposed architecture decision tree — NOT FROZEN

### Candidate A — inherited shared trainable target identity

Keep current shared online gene-identity query.

Advantages: minimum code change; historical mechanics directly preserved.

Risk: direct co-adaptation path between target query and future EMA teacher.

Recommendation: diagnostic comparator only unless it independently clears the target-identity shortcut gate.

### Candidate B — decoupled/fixed target-address conditioning

Keep target address information but move predictor query construction to a fixed/separate replay-stable address representation with no JEPA gradient path into online encoder identity parameters.

Advantages:

- preserves address conditioning;
- removes direct shared-parameter shortcut channel;
- minimally alters teacher/student semantics;
- lets objective-aligned audit determine whether teacher target itself is too identity-dominated.

Risk: fixed address representation design must avoid arbitrary geometry becoming biological authority.

Recommendation: **leading candidate for review**.

### Candidate C — redefine teacher target to remove address identity component

Advantages: strongest attack on identity-only predictability.

Risks:

- changes the target object itself;
- may remove legitimate gene-specific structure;
- difficult to distinguish identity removal from biological information loss.

Recommendation: reserve only for evidence that Candidate B still leaves the target identity-dominated.

## 12. Prospective acceptance structure

Before any implementation is allowed to become production authority:

- independently review the target-identity audit specification;
- freeze its null, metric and superiority/non-inferiority margins prospectively;
- freeze teacher target semantics;
- freeze masking authority;
- freeze scientific estimand;
- bind V5 model/rank geometry from dataset authority;
- bind presentation-normalized EMA timescale;
- build/modify the executable runtime only after these design decisions are approved;
- run mechanics and anti-cheat qualification with `TRAINING_OFF` still in force;
- authorize production training only through a separate explicit governance action.

## 13. Current terminals

`V5_TEACHER_STUDENT_EMA_ARCHITECTURE_DRAFTED_NOT_FROZEN`

`TEACHER_STUDENT_EMA_MECHANICS_RECOVERED_AND_FAIL_CLOSED`

`CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`

`TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

`CONTEXT_SHORTCUT_HANDLING_NOT_YET_FROZEN`

`SCIENTIFIC_TRAINING_ESTIMAND_NOT_YET_FROZEN`

`PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`TRAINING_OFF`
