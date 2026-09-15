# V5 Target-Identity Shortcut Audit Specification — draft

Date: 2026-09-15
Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`
Parent design draft: `V5_TEACHER_STUDENT_OBJECTIVE_AUTHORITY_DRAFT_20260915.md`
Evidence base: Claude Layer-2 closeout `219831b899b914984369c7a41828bf750554d1d9`

No production training is authorized by this document.

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

## 1. Question

Does the candidate V5 target/predictor geometry reward solving the JEPA task from target-gene identity itself, rather than from cell-specific molecular information in the visible student view?

This is distinct from:

- measurement-state shortcut;
- source/operator context shortcut;
- correlated-visible-gene masking shortcut.

## 2. Why the audit is required

Current inherited mechanics have two structural identity channels.

### Channel A — direct shared-parameter path

`BlockPredictor` constructs hidden-target queries from `modules.online.tokenizer.gene_identity`, and that same online encoder parameter table is optimized by AdamW. The EMA teacher later follows the online encoder.

Available path:

`target identity -> predictor query -> loss gradient -> online identity table -> EMA teacher -> future target`.

### Channel B — identity-only target predictability

Teacher target states originate from tokens formed from a trainable gene-identity component plus expression value encoding. Even if Channel A is removed, stable target-address information may explain a substantial fraction of teacher target variance.

A low JEPA loss is therefore insufficient evidence that the student used cell-specific molecular state.

## 3. External architectural precedent — contextual only

The official Meta I-JEPA reference uses fixed, non-trainable sine/cosine positional embeddings for both encoder position and predictor target position (`requires_grad=False`), plus a learned generic mask token. Target position is therefore available to the predictor without directly sharing the encoder's trainable content-embedding table.

This is **not** authority for the gene architecture. It establishes only that address conditioning and content representation need not share trainable parameters.

Reference: `facebookresearch/ijepa`, `src/models/vision_transformer.py`, `VisionTransformerPredictor.predictor_pos_embed`.

## 4. Audit stages

### Stage A — static/mechanical proof, allowed while training remains OFF

A1. Confirm whether hidden target IDs index parameters that receive direct JEPA predictor gradients.

A2. Enumerate every parameter path shared between:

- target-address query construction;
- online molecular encoder;
- EMA teacher target generation.

A3. Confirm that hidden target expression values do not enter student/predictor memory through indexing, padding, mask statistics, packing metadata, or fallback logic.

A4. Define replay-stable target-address representations for each comparator below.

Stage A is code/mechanics only and must not inspect protected outcomes.

### Stage B — objective-aligned identity audit, only after teacher-target semantics are frozen

Run every comparator against **the same frozen teacher targets, masks, cells, folds, scientific weights, and loss geometry**.

Required comparators:

1. `IDENTITY_ONLY_SHARED_CURRENT`
   - inherited current target query;
   - no student molecular memory;
   - diagnostic only.

2. `IDENTITY_ONLY_FIXED_ADDRESS`
   - fixed, non-trainable deterministic address code;
   - no student molecular memory.

3. `FULL_SHARED_CURRENT`
   - inherited shared trainable target-identity query + student molecular memory.

4. `FULL_FIXED_ADDRESS`
   - fixed, non-trainable target-address code + same student molecular memory.

5. `FULL_STOPGRAD_ONLINE_ID`
   - online identity values may seed the query but are detached from predictor gradients;
   - diagnostic only, because EMA coupling remains indirect.

6. `NO_TARGET_ID_CONTROL`
   - only where the target is still mathematically identifiable without address conditioning;
   - otherwise explicitly mark `NOT_ESTIMABLE` rather than invent a substitute.

A teacher-EMA identity query may also be evaluated as a diagnostic but cannot be presumed safe merely because gradients are stopped.

## 5. Primary quantities

For each comparator and lawful evaluation stratum, report:

### 5.1 Identity-only fraction

`F_id = 1 - L(identity_only) / L(null_reference)`

or an equivalent prospectively frozen variance-explained quantity appropriate to the final target loss.

The exact denominator/null must be fixed before results are inspected.

### 5.2 Molecular-memory increment

`Delta_mol = L(identity_only_same_address_code) - L(full_same_address_code)`

Positive `Delta_mol` means visible molecular memory improves prediction beyond address identity under the same query construction.

Do **not** label `Delta_mol` biology.

### 5.3 Parameter-coupling effect

Compare shared versus fixed/detached address construction under the same molecular memory:

`Delta_share = L(full_fixed_address) - L(full_shared_current)`.

A large gain from shared trainable identity is a shortcut warning, not automatically a useful feature.

### 5.4 Target identity structure

Report target variance/predictability by:

- gene/address frequency;
- target-block size;
- source;
- operator;
- donor where lawful;
- rare-address versus common-address strata.

The purpose is to identify whether identity predictability is concentrated in common or cohort-specific addresses.

## 6. Required controls

- shuffle cell-to-visible-memory assignment while retaining target IDs;
- shuffle target IDs while retaining visible molecular memory where shape/support permits;
- preserve target-block size distribution in every shuffle;
- preserve measurement support constraints;
- replay identical masks/cells/scientific weights across comparator variants;
- no threshold widening after seeing results;
- no D_shared/protected outcome involvement.

## 7. Scientific weighting

Because Claude's Layer-2 closeout demonstrated substantial estimand sensitivity, identity-shortcut metrics must be reported under each already-lawful candidate weighting **separately**, not pooled into a single preferred number:

- empirical/FULL104 structure;
- source-uniform;
- donor-primary/operator-balanced;
- any later frozen production estimand.

The audit must not choose the production estimand.

## 8. Decision rule — deliberately not numerically frozen here

This draft does not invent a permissible identity-only fraction after seeing current architecture behavior.

Before Stage B execution, an independent review must prospectively freeze:

- the null/reference loss;
- primary metric;
- superiority/non-inferiority margin for molecular-memory increment;
- allowable identity-only contribution, if any;
- rare-address guardrail;
- whether failure of the shared-current variant automatically disqualifies only the shared query or the teacher target itself.

Until that rule exists, Stage B may characterize but cannot select an architecture.

## 9. Candidate interpretations

Possible outcomes and their meaning:

- **Shared fails, fixed passes:** direct trainable identity sharing is the problem; decoupled address conditioning remains viable.
- **Shared and fixed both identity-dominated:** the teacher target itself carries too much stable address identity; target semantics need redesign before predictor choice matters.
- **Identity-only weak, full molecular increment strong:** target identity is primarily an addressing signal, not the main solution path.
- **Rare-address failure only:** frequency imbalance/coverage must be addressed before production authority.
- **All variants weak:** teacher target may be too hard/uninformative at the tested geometry; do not compensate by loosening anti-cheat gates post hoc.

## 10. Current status

`TARGET_IDENTITY_SHORTCUT_AUDIT_SPEC_DRAFTED_NOT_FROZEN`

`TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

`CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED`

`TRAINING_OFF`
