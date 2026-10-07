# JEPA Premise V3 external-asset freshness — Nott reconciliation

Date: 2026-10-07

Status: `AUDIT_CORRECTION__NO_SELECTION_AUTHORITY__TRAINING_OFF`

## Finding

The V3 external-validation asset matrix drafted at commit `7018edea1ca58e9cfd42a5e83b625fddb5b15ad1` is scientifically careful overall, but its Nott row is stale relative to later/recovered project evidence.

The matrix currently classifies Nott Table S5 / related microglia regulatory resource as:

`REQUIRES_CURRENT_CUSTODY_RECHECK`

and describes prior retrieval as blocked with custody only possibly existing later.

That is no longer the best current classification.

## Current recovered Nott state

Nott Table S5 has been directly authenticated in current project custody:

- file size: `36,876,140` bytes
- SHA-256: `81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e`
- workbook contact counts:
  - microglia: 104,802
  - neuronal: 93,290
  - oligodendrocyte: 61,895
- expected 14-column schema observed.

This hash matches the historical V64 custody record.

The V64 lineage also contains development/execution exposure to Nott:

1. P1S prospective same-study substrate qualification was frozen and independently audited PASS for its narrow substrate-fit claim.
2. P3 negative/control construction was independently audited PASS.
3. E2 Nott-centered candidate edges were instantiated and audited as a prevalidation object.

These results do not qualify a JEPA teacher target and do not constitute independent biological validation of a later RNA representation.

## Corrected role classification

Recommended current classification:

`AUTHENTICATED_CURRENT_CUSTODY__DEVELOPMENT_EXPOSED_REGULATORY_RESOURCE__NOT_PRISTINE_INDEPENDENT_CONFIRMATION`

Nott may still be useful prospectively for:

- regulatory-support diagnostics with explicit exposure accounting;
- orthogonal mechanistic context where the tested endpoint was not used in development;
- challenge/supporting evidence under a separately frozen authority.

It must not be described as pristine independent confirmation merely because it is external to FULL104.

## Important distinction

The same-study P1S result showed strong microglia-vs-neuron/oligodendrocyte enrichment under the frozen Nott substrate geometry. That qualifies a narrow substrate specificity property. It is not target biology validation, causal support, or a free pass from `RNA_REPRESENTATION` to `REGULATORY_SUPPORT`.

## Matrix-level implication

Any future machine-readable external-asset registry should separate at least:

- `custody_status`
- `authentication_status`
- `development_exposure_status`
- `independence_from_target_construction`
- `independence_from_representation_selection`
- `allowed_claim_transition`

A resource can be fully authenticated and still be development-exposed/non-pristine.

## Current boundaries

No target or representation is selected by this correction.

`TRAINING=OFF`
`STAGE_A_EXECUTION=NOT_AUTHORIZED`
`MULTIMODAL_TRAINING=OFF`
`MORABITO=PROTECTED`
`TEST=SEALED`
