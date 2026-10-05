# V64 privileged-information boundary and RNA-recoverability contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE ARCHITECTURE CONTRACT — no training or runtime authority  
**Purpose:** prevent a future multimodal teacher from imposing targets that an RNA-only student cannot lawfully identify.

## 1. Problem statement

The production-scale foundation corpus is predominantly RNA-only. Future teacher-side evidence may include ATAC, active promoter/TSS state, enhancer state, chromatin contact, genetic evidence, or perturbational evidence.

A teacher with privileged modalities can represent biological information that is not statistically recoverable from RNA at the same cell/state/timepoint. Therefore the project must not define the universal student target as the complete rich-teacher embedding.

The central rule is:

> **Privileged evidence may constrain or validate the universal RNA state, but compulsory universal student supervision is limited to teacher structure demonstrated to be recoverable from the student's lawful RNA inputs.**

## 2. Current runtime finding

The current V5 inactive mechanics path is RNA→RNA JEPA:

- teacher and online/student use the same encoder family;
- the teacher receives all measured RNA tokens in the cell;
- the student receives RNA with target blocks hidden;
- teacher target blocks are gathered from the teacher's RNA-derived gene states;
- the current target authority defines one biological/query-local latent state.

There is currently no native representation of:

- multimodal teacher-private state;
- factor-specific observability;
- RNA-recoverability class;
- selective distillation by factor;
- modality-private uncertainty.

Therefore adding regulatory modalities to the teacher is **not** a drop-in enrichment. It requires a successor semantic contract and, if implemented, a runtime extension.

## 3. Conceptual factorization

The current working hypothesis may be expressed as:

- `Z_global(cell)`: broad recurrent biological state whose universal version must be RNA-supported.
- `Z_query(cell,q)`: query-conditioned biology whose universal version must be RNA-supported.
- `Z_reg_shared(cell,q)`: regulatory structure demonstrated to be recoverable from lawful RNA.
- `Z_reg_private(cell,q)`: regulatory structure supported by privileged measurements but not demonstrated RNA-recoverable.
- `Z_response(cell,q/intervention)`: perturbational/functional state; baseline-RNA recoverability is an empirical question, not an assumption.

This is a semantic decomposition, not authorization to create five neural heads.

## 4. Recoverability classes

Every privileged teacher factor proposed for universal supervision must be assigned one of:

1. `RNA_RECOVERABLE`
2. `PARTIALLY_RNA_RECOVERABLE`
3. `PRIVILEGED_PRIVATE`
4. `UNQUALIFIED`

No factor begins as `RNA_RECOVERABLE`.

### RNA_RECOVERABLE

Requires prospective evidence that lawful RNA predicts the factor on held-out biological units beyond technical/generic-cell baselines, with transport evidence at the strongest feasible holdout level.

### PARTIALLY_RNA_RECOVERABLE

Some reproducible subspace/components are RNA-predictable while residual structure is not. Only the qualified recoverable component may enter compulsory universal student supervision.

### PRIVILEGED_PRIVATE

Biologically meaningful privileged structure that is not reproducibly recoverable from RNA. It may be retained for validation, optional multimodal inference, uncertainty, biological adjudication, or geometry constraints. It must not be treated as a missing student answer.

### UNQUALIFIED

Recoverability or biological meaning is unresolved.

## 5. Prospective recoverability experiment

Before a privileged factor can supervise the universal RNA student:

1. **Construct the privileged factor without student-target leakage.**
   - The factor may use its declared privileged evidence.
   - The queried scalar must obey the current query-safety rules wherever applicable.
   - Construction inputs and evidence families must be explicit and hash-bound.

2. **Define lawful RNA student inputs.**
   - No privileged modality features.
   - No availability indicators that reveal the target class unless explicitly part of a separate shortcut test.
   - Query identity/global context only according to frozen authority.

3. **Use biological holdouts.**
   Minimum: donor-held-out evaluation.
   Stronger where available: held-out dataset/study and held-out technology.
   Cell-random splits alone cannot qualify universal recoverability.

4. **Compare against baselines.**
   At minimum:
   - query identity only, where query-conditioned;
   - lawful global RNA state only;
   - technical/measurement descriptors;
   - generic cell-state baseline;
   - simple expression/activity proxy where relevant.

5. **Evaluate factor geometry, not only scalar reconstruction.**
   Candidate measures may include:
   - cross-validated subspace prediction;
   - canonical correlation / principal-angle recovery;
   - held-out pairwise or relational geometry;
   - calibrated prediction error for factor coordinates only when coordinate stability is established.

6. **Test shortcut sensitivity.**
   Recoverability must not be driven only by:
   - RNA detection rate;
   - library depth;
   - promoter/enhancer availability;
   - E2 degree;
   - evidence-present vs NOT_MEASURED status;
   - dataset/operator identity.

7. **Use an independent evidence-family validation where possible.**
   A factor learned/constructed from one set of evidence families should preferably be evaluated on a mechanistically distinct held-out family.

## 6. No fixed numeric pass threshold yet

This contract freezes the logical requirements, not a post-hoc numerical cutoff.

Before execution, a successor precision/decision contract must prospectively define:

- primary recoverability metric;
- confidence/uncertainty procedure;
- minimum donor/dataset support;
- materiality threshold relative to baselines;
- partial-recoverability decomposition rule;
- multiplicity treatment where multiple factors/components are tested.

Thresholds may not be chosen after viewing recoverability outcomes.

## 7. Shared/private decomposition must not be fit to flatter the student

A decomposition such as `Z_reg = Z_reg_shared + Z_reg_private` can itself overfit.

Therefore:

- decomposition is fit only on TRAIN biological units;
- rank/dimensionality selection must be prospective or nested inside TRAIN;
- held-out donors determine recoverability;
- the private residual is not discarded merely because the student cannot predict it;
- components may not be rotated post hoc to maximize student performance on evaluation units.

If axes are unstable but a subspace is stable, recoverability should be judged at the stable-subspace level rather than forcing coordinate-wise interpretation.

## 8. Asymmetric interpretation rule

Failure to recover a privileged factor from RNA means:

> **the factor is not established as a lawful universal RNA-student target under the tested design.**

It does **not** mean:

> the factor is biologically false.

Conversely, successful RNA prediction does not by itself prove biological validity; technical and availability shortcuts must be excluded.

## 9. Authority of FULL104 versus multimodal subsets

The 4.55M-cell FULL104 RNA corpus remains the broad authority for recurrent global biological geometry.

A smaller multimodal subset may:

- constrain;
- annotate;
- test;
- validate;
- factorize;
- reveal privileged-private structure.

It may not silently redefine the entire universal state solely because it carries richer assays.

The desired direction is:

`FULL104 RNA → broad global/query state`

with multimodal subsets used to determine which regulatory structure is:
- shared/recoverable;
- private;
- validation-only.

## 10. Availability-negative probe

The currently identified 379 E2-anchored but NIH-CARD-RNA-unmeasurable genes form a prospective availability-shortcut diagnostic stratum.

They must not be encoded as unsupported.

Future analyses should preserve the distinction:

- measured and supports;
- measured and does not support;
- not measured.

A representation that succeeds only where rich evidence is measurable must be tested for availability leakage.

## 11. Relation to evidence independence

Recoverability and evidence independence are different questions.

A regulatory factor may be RNA-recoverable because both the factor and RNA share an activity/detectability driver. Therefore future recoverability analyses must be interpreted together with:

- shared-selection diagnostics;
- common-support analysis;
- observed-adjustment sensitivity;
- held-out evidence-family validation.

## 12. Runtime consequence

Do not modify the current single-state V5 teacher/student runtime merely by appending multimodal channels.

Any future multimodal runtime successor must make explicit:

- which factor each teacher output represents;
- what evidence constructed that factor;
- whether that factor is eligible for universal distillation;
- what loss applies to shared factors;
- how private factors are retained without penalizing RNA-only students;
- how NOT_MEASURED is masked without becoming an availability shortcut.

## 13. Hard governance

This contract does not authorize:

- training;
- Phase B;
- Stage 4;
- protected correspondence;
- Morabito;
- target-factor selection;
- multimodal teacher implementation.

It exists to prevent an invalid target architecture before those stages open.
