# External-modality specificity protocol V1 — design only

Status: `PROSPECTIVE_DESIGN_ONLY__NO_OUTCOME_OPENING__NO_TRAINING_AUTHORITY`

## Why this moved earlier

The CPU identifiability audit shows that a same-RNA gate cannot distinguish an unrestricted hidden technical latent from an equally structured biological latent when the observable distributions are identical. Therefore a genuinely different measurement channel is the cleanest way to break that equivalence.

## Reuse existing authenticated work; do not redo it

- GSE174367 / Morabito: separate RNA and ATAC nuclei from the same donor cohort; donor-level cross-modal evaluation only. Prior resource-level exposure must be recorded, so this is not described as wholly pristine/unseen.
- GSE214979: conditionally authenticated same-nucleus RNA/ATAC; use the already frozen donor exclusions/identity warnings from the paired-multiome lane. It is complementary to Morabito, not an independent duplicate cohort.
- Do not use Stage75F RNA-derived regulator edges as an external answer key for the same RNA.

## Prospective requirements before any outcome opens

1. Freeze the exact relational statistic and all preprocessing separately for RNA and ATAC.
2. Freeze donor/cell eligibility from authenticated metadata only.
3. Preserve missing/unmeasured as missing, never biological zero.
4. Predefine negative controls that alter cross-modal correspondence while preserving permitted technical strata.
5. Predefine a positive control demonstrating the metric has power to detect planted/known correspondence.
6. Freeze acceptance thresholds and minimum support before reading the biological result; thresholds are intentionally `UNSET_REQUIRES_APPROVAL` here.
7. Report GSE174367 and GSE214979 separately; do not pool people/cells to inflate n.
8. Record all prior exposure in the final interpretation.

No external biological outcome is inspected by this design document.
