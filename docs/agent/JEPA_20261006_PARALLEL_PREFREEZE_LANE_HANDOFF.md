# JEPA parallel premise-prefreeze lane handoff — 2026-10-06

Role: takeover/progress ledger for the scientific prefreeze lane running in parallel with runtime reconciliation and Macha V77 work.

This file does not authorize training or Stage-A execution.

## Current branch

Scientific-prefreeze working branch:

`design/premise-qualification-contract-v3-20261006`

Base:

`main@102aa26730e4c2eda8b52a7532adee5332971e8b`

Current first commit:

`b149de6e60aa2b068453dd7926217af5e107667a`

Created:

`docs/superpowers/specs/2026-10-06-premise-qualification-contract-v3-design.md`

## What V3 changes relative to the Oct-5 V2 design

V3 preserves the existing P1-P6 contract, representation neutrality, claim ladder, Stage-A TRAIN-only prefreeze, external-asset separation, synthetic-vs-real firewall and `selected_estimand=UNSET_REQUIRES_APPROVAL`.

It adds four explicit governance layers that had been developed in chat/project history but were not fully captured in V2:

1. **Observation-operator contract**
   - conceptual separation `z_biology -> O_t -> X_observed`;
   - lawful measurement descriptors may include assay type, platform/chemistry, measured vocabulary/support, depth/detection characteristics and documented acquisition properties;
   - donor ID, arbitrary dataset ID and arbitrary matrix/file ID are not unrestricted model covariates;
   - technology should not be forced to be universally unidentifiable from representation; instead measure residual technical imprint conditional on comparable biology.

2. **Basis/subspace stability contract**
   - donor-balanced resampling / leave-donor-group-out;
   - principal angles, canonical correlations, Procrustes stability and spectral gaps;
   - if the subspace is stable but axes rotate, report stable subspaces/blocks rather than biological meaning for individual coordinates.

3. **Separate biological-evidence and measurement-depth curves**
   - biological-evidence convergence: representation change as more lawful molecular evidence is revealed;
   - measurement-depth convergence: representation change under count-depth downsampling with information universe held fixed;
   - keep `U_bio` distinct from `U_measurement`.

4. **Separate biological-support and measurement-support OOD**
   - `D_measurement` and `D_biological_support` are separate axes;
   - unusual but well-measured biology must not automatically be corrected away as technical OOD.

## Hard boundaries retained

- `TRAINING=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`
- target winner = none qualified
- representation winner = none qualified
- `cell_state` is implemented, not qualified as default winner
- `width=160` is architecture capacity, not biological dimensionality authority
- Stage A remains prefreeze only and has zero encoder/EMA updates

## Parallel lanes — do not duplicate

Runtime reconciliation is being handled separately on:

`reconcile/v64-runtime-authority-onto-main-20261006`

Do not duplicate its optimizer/EMA/checkpoint/q-safe call-graph work in this lane.

Macha V77 simulator work is separate. Synthetic generator qualification/falsification cannot select the real-RNA target or representation.

## Next scientific-prefreeze tasks

1. Convert the V3 design into the publishable human + machine premise authority artifacts.
2. Freeze the four-family representation tournament with no winner:
   - `GLOBAL_CELL_STATE`
   - `QUERY_LOCAL_STATE`
   - `PROGRAM_STATE`
   - `STRUCTURED_COMBINED_STATE`
3. Freeze the observation-operator declaration schema and forbidden shortcut fields.
4. Freeze basis/subspace stability metrics and fail-closed interpretation rules.
5. Freeze biological-evidence and measurement-depth convergence protocols.
6. Consolidate external-validation asset roles from existing audits PRs #188-#199 rather than repeating those audits.
7. Freeze foundation-population estimand choices while leaving selection unset.
8. Add governance tests/validator only after the contracts are stable; do not open Stage A or training.

## External-asset evidence already known and to preserve

Existing audits contain nontrivial exposure/pairing/independence constraints. Do not call an asset pristine merely because it is external.

Examples already in repository history include:

- GSE214979: same-nucleus RNA+ATAC pairing established in prior audit, but small donor count and identity-conflict exclusions constrain use;
- GSE272082: pairing by construction but important annotation/census facts remained unresolved in prior audit;
- GSE174367/Morabito: separate nuclei and heavily exposed/protected; unavailable for target selection;
- observational multimodal agreement cannot establish causal/interventional validity.

The V3 asset matrix must cite/reuse existing audited evidence rather than rerun it blindly.

## Takeover rule

Before continuing this lane, re-fetch current `main`, this handoff branch, the V3 design branch, and the runtime reconciliation branch. If current authority moved, update the prefreeze branch before publishing new authority artifacts.

Do not merge this handoff branch into implementation work. It is a coordination/takeover ledger only.
