# V65 nested RNA + multimodal student architecture contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE ARCHITECTURE ONLY — NO MULTIMODAL TRAINING AUTHORIZED

## 1. Purpose

The project will support two student observation regimes:

1. a universal RNA-only student that scales across the large RNA corpus;
2. a multimodal student for cells/datasets where richer modalities are actually measured.

The multimodal student is an information extension of the RNA model. It does not replace the universal RNA backbone and it does not redefine universal state merely because richer assays exist on a smaller paired subset.

Conceptually:

`Z_RNA ⊆ Z_MULTIMODAL`

where subset means shared biological content plus additional modality-private content, not literal coordinate containment.

## 2. Universal RNA student

Input:

`X_RNA`

Conceptual output:

`Z_RNA = Z_global ⊕ Z_query ⊕ Z_reg_shared`

Only states carrying current RNA-recoverability authority may become compulsory universal RNA-student supervision.

The current universal teacher remains the RNA EMA teacher until an explicit successor runtime is independently qualified.

## 3. Multimodal student

Initial lawful paired input:

`(X_RNA, X_ATAC, modality_mask)`

Future extensions may add other declared modalities only through successor contracts.

Conceptual output:

`Z_MULTI = Z_global ⊕ Z_query ⊕ Z_reg_shared ⊕ Z_reg_private`

The multimodal model may retain useful state that is not RNA-recoverable.

That private state is a scientific object, not an error term to be deleted until the RNA model can predict it.

## 4. Shared/private authority

A multimodal factor does not become `Z_reg_shared` because the multimodal model represents it.

Shared authority is granted only by the project's prospective recoverability machinery.

Possible states remain:

- `RNA_RECOVERABLE`
- `PARTIALLY_RNA_RECOVERABLE`
- `PRIVILEGED_PRIVATE`
- `UNQUALIFIED`

For a partially recoverable factor, only the locked recoverable projection belongs to `Z_reg_shared`.

The residual remains private or unqualified according to independent biological evidence.

Poor RNA prediction alone can never create `PRIVILEGED_PRIVATE` authority.

## 5. Shared-state alignment is not raw coordinate equality

The project must not require:

`Z_RNA_shared == Z_MULTI_shared`

coordinate by coordinate.

Latent bases may rotate while representing the same biological subspace.

Alignment must operate on a prospectively locked shared object such as:

`P_shared Z_RNA` and `P_shared Z_MULTI`

or an equivalent qualified geometry.

Eligible alignment objects include:

- locked recoverable target-space projections;
- relational geometry;
- query-conditioned predictive behavior;
- donor-held-out neighborhood/subspace structure.

Raw latent-coordinate MSE is not automatically a scientifically valid alignment loss.

Any exact alignment loss must be frozen before outcome inspection and must be invariant to irrelevant basis rotations when the scientific object is a subspace.

## 6. Private state must not leak into compulsory RNA supervision

For `Z_reg_private`:

- no compulsory loss on RNA-only cells;
- no zero target;
- no pseudo-target derived solely from modality absence;
- no requirement that the RNA student imitate the multimodal private state;
- no post-hoc rotation of the private state to make it easier for RNA to predict.

If a private factor later obtains RNA-recoverability authority, only a prospectively locked recoverable projection may move into the shared state.

## 7. Missing-modality semantics

For an RNA-only cell:

`X_ATAC = NOT_MEASURED`

therefore:

`Z_reg_private = NOT_OBSERVED / NOT_IDENTIFIABLE_FROM_CURRENT_EVIDENCE`

not zero.

A future probabilistic missing-modality model may return:

`p(Z_reg_private | X_RNA)`

with uncertainty, but it must be labelled inferred rather than measured.

The project must preserve at least:

- MEASURED_AND_SUPPORTED
- MEASURED_AND_NOT_SUPPORTED
- NOT_MEASURED
- UNRESOLVED

Availability masks may control whether a loss is applied. They may not be silently used as a biological feature unless explicitly qualified in a shortcut analysis.

## 8. Nested comparability

RNA-only and multimodal cells must remain comparable in the shared biological coordinates.

A paired multimodal cell therefore has:

`(Z_shared, Z_private)`

while an RNA-only cell has:

`(Z_shared, private_mask=NOT_MEASURED)`.

Multimodal cells must not be moved into a wholly separate latent universe merely because extra assays are present.

Conversely, preserving a common shared space must not require discarding modality-specific information.

## 9. Modality-gain object

A future scientific analysis may quantify the incremental information made identifiable by a measured modality.

For ATAC this is conceptually:

`ΔI_ATAC = information(Z_MULTI ; biology | RNA) - information already present in Z_RNA`

or a prospectively defined shared/private subspace comparison.

Literal coordinate subtraction:

`Z_MULTI - Z_RNA`

is not authorized as the scientific definition unless a future contract proves the coordinate systems make that operation meaningful.

The scientific question is:

> What biological state becomes identifiable when regulatory measurements are actually observed rather than inferred from RNA?

## 10. Initial model-family topology

### Universal RNA path

`X_RNA -> E_RNA -> Z_shared`

with the existing RNA EMA teacher semantics retained unless explicitly superseded.

### Multimodal path

`(X_RNA, X_ATAC, modality_mask) -> E_MULTI -> (Z_shared_multi, Z_private)`

### Privileged/teacher-side evidence

Privileged biological measurements may:

- construct candidate factors;
- validate factors;
- provide modality-private targets to the multimodal path;
- supervise a locked recoverable shared projection after qualification;
- act as critics or geometry constraints.

They may not force the universal RNA path to reproduce the full rich state.

## 11. Training sequence, when training is eventually authorized

The prospective order is:

1. qualify privileged factor construction;
2. qualify RNA recoverability/shared rank;
3. lock `P_shared` and the private residual definition;
4. build multimodal student on paired TRAIN donors;
5. train shared alignment only on locked qualified shared objects;
6. train modality-private capacity only where the modality is measured;
7. evaluate modality gain on held-out biological units;
8. audit uncertainty/missing-modality behavior;
9. only then consider extending the multimodal input set beyond RNA+ATAC.

No stage may use TEST to choose rank, basis, rotation, loss weight or architecture.

## 12. Minimum future baselines

Any future multimodal-student experiment must compare against:

- RNA-only student;
- ATAC-only or modality-only baseline where lawful;
- simple concatenation/integration baseline;
- technical/availability baselines;
- a rich multimodal model without shared/private separation.

This determines whether the nested architecture adds biological structure rather than merely extra capacity.

## 13. Behavioral requirements

A future trained system should satisfy, prospectively tested:

1. removing ATAC from a paired cell cannot fabricate measured private state;
2. adding real ATAC may change private/regulatory state without arbitrarily rotating shared universal state;
3. RNA-only and paired cells remain comparable in qualified shared geometry;
4. private-state uncertainty rises when its supporting modality is missing;
5. technical depth/availability alone must not explain multimodal gain;
6. modality gain is evaluated donor-held-out and, where possible, study/technology-held-out.

## 14. Relation to current recoverability experiment

The current `Z_priv_ATAC_V1` experiment is not merely a side analysis.

It is the first qualification mechanism for deciding which part of a real ATAC-derived state may enter:

`Z_reg_shared`

and which part must remain:

`Z_reg_private` or `UNQUALIFIED`.

Until that experiment is lawfully executed and audited, the dimensions of the real shared/private multimodal interface remain unresolved.

Therefore this contract freezes topology and semantics, not a biological shared rank.

## 15. Runtime consequence

Do not silently modify the current V5 RNA runtime into a joint multimodal model.

A future runtime successor must explicitly represent:

- modality mask;
- shared-state output;
- private-state output;
- shared alignment authority/digest;
- private-loss mask;
- uncertainty for missing privileged state;
- provenance of every teacher/critic factor.

The existing V5 RNA runtime remains historically interpretable as RNA-to-RNA unless a successor is explicitly introduced.

## 16. Governance

This contract does NOT authorize:

- multimodal training;
- modification of the current production runtime;
- teacher replacement;
- full rich-teacher imitation;
- real privileged recoverability execution;
- TEST opening;
- Stage 4 correspondence;
- Morabito;
- TD60;
- JEPA training.

`TRAINING = OFF`

Measurement-only Phase B may proceed under its separate audited authority. That does not authorize multimodal learning or RNA-ATAC correspondence.
