# Contextual JEPA — learning biological state from partial RNA

> **Can a model recover biologically meaningful cell state from incomplete RNA evidence without solving the task through gene identity, measurement artifacts, or answer leakage?**

This repository is a pathology-blind, donor-aware JEPA research project built around a **41,238-address Molecular Ledger**. It keeps gene/address identity, physical measurement state, evidence visibility, donor structure, and provenance explicit.

For the live scientific boundary, read [`START_HERE.md`](START_HERE.md) first. Historical v1–v75 artifacts remain in the repository as evidence and provenance; filenames or old “current” labels do not make them present authority.

## Current status — October 5, 2026

The current controlling state is intentionally fail-closed:

- **V75 100K measurement architecture is qualified within its declared scope.**
- **500K promotion is not authorized.**
- **No production teacher target is currently qualified.**
- **Training and multimodal training are OFF.**
- **Stage 4 is not authorized.**
- **`width=160` is network/token capacity, not a biological-dimension result.**
- **The synthetic learned-state scaling ladder is stopped.**

The immediate scientific task is to finish the target-authority lineage reconstruction and identify the last genuinely unresolved target-design question before running another target experiment.

See:

- [`docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`](docs/agent/JEPA_LATEST_HANDOFF_POINTER.json)
- [`docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md`](docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md)
- [`docs/agent/CURRENT_AUTHORITY_INDEX.md`](docs/agent/CURRENT_AUTHORITY_INDEX.md)
- [`docs/agent/CURRENT_SUPERSESSION_MAP.md`](docs/agent/CURRENT_SUPERSESSION_MAP.md)

## Scientific objective

The project is **not** primarily an exact missing-expression imputation project. The objective is to learn state/program structure that remains useful when RNA evidence is partial and measurement support differs across assays and datasets.

A convincing representation must separate biological information from easier shortcuts such as gene/address identity, source/operator support patterns, sequencing depth and normalization leakage, direct or indirect access to the hidden answer, and cell-level pseudoreplication. The donor is the primary inferential unit for biological claims.

## Observation semantics

Missingness is explicit rather than collapsed into one mask. The project distinguishes physical observation states such as `MEASURED_SCALAR`, `STRUCTURALLY_UNMEASURED`, and `MEASURED_COLLISION_UNRESOLVED`. A measured zero is evidence. A structurally unmeasured feature is not a zero. Artificial model masking changes view visibility; it does not rewrite what the assay physically measured.

## Implemented neural runtime versus scientific authority

The repository contains a canonical token-preserving IPB teacher/student runtime over the 41,238-address vocabulary. The encoder emits contextual gene states and a 160-wide cell token. The current runtime's JEPA loss predicts teacher gene/block representations using a predictor that can access both student gene states and the student cell token.

Those are **implemented mechanics**, not proof that the target or the 160-wide cell token is the correct biological state.

Current evidence says:

- `cell_state` exists and participates in the computation, but is **not yet identified as the unique or sufficient global biological state**;
- gene/block states are directly targeted by the current loss, but are **not automatically qualified as the global biological state**;
- earlier T0/T1/TCTX target families did not qualify;
- strict donor-cross-fitted residual targeting was later executed and returned `RESIDUAL_TARGET_DOES_NOT_RESCUE`;
- later competing value-blind target constructions were defined prospectively, but no winner was selected;
- a corrected synthetic T_A/T_B comparison was `NOT_INFORMATIVE` and could not choose the target without real RNA.

Therefore the architecture should be described as **implemented runtime under unresolved target authority**, not as a qualified production biological-state model.

## Synthetic measurement architecture

V73–V75 built a FULL104-like synthetic measurement substrate to stress observation geometry, donor/operator support, empirical QC realization, fragment linkage, and matched control worlds.

The current narrow V75 terminal is:

`PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED__500K_PROMOTION_INDETERMINATE`

This qualifies the **measurement architecture at 100K**, not a learned biological state.

The V75 observer uses 96 anonymous synthetic features. The canonical neural runtime uses learned identities for 41,238 addresses. Arbitrarily assigning those 96 features to canonical gene slots is scientifically invalid; a lawful identity bridge would have to be defined prospectively for any future cross-use.

## Data scale

The authenticated FULL104 reader-fit population contains 4,553,407 cells, 104 donors, 42 measurement operators, 1,400 donor × operator strata, and 41,238 molecular addresses.

Protected validation/oracle, DEV/SEALED, pathology, correspondence, and other restricted populations remain governed by their lane-specific release authorities.

## Dimensionality

Architectural width and biological rank are deliberately separated. A 160-wide token space may contain a much lower-dimensional stable biological subspace. Historical `D_shared`, `D_private`, `D_total`, `D_obs`, rank/stability, held-donor, and shortcut-control programs exist to estimate evidence-supported dimensional structure. Their existence does not make `160` a biological result.

## Why the project is fail-closed

The project has stopped or revised work for provenance mismatches, shortcut channels, invalid null geometry, target leakage, stale authority pointers, numerical defects, and controls that could not falsify the intended failure mode.

A lower loss, green CI, a smoke checkpoint, or successful infrastructure execution is never sufficient for a biological claim. Historical failed mechanisms are retained because they constrain what should not be repeated.

## Compute philosophy

The project is developed under constrained GPU resources and therefore emphasizes immutable/hash-bound inputs, streaming rather than loading the full corpus at once, exact row lineage and restart semantics, reuse of sufficient statistics where scientifically lawful, and bounded prospective experiments rather than unconstrained sweeps.

## Historical evidence

Older Graph-JEPA, T0/T1/TCTX, Contextual Target/F1, masking, regulatory, SCENIC+, perturbation, dimension, and multimodal infrastructure work remains preserved in branches, PRs, results, and handoffs.

Use historical artifacts for provenance and mechanism evidence, but resolve their status through the current authority and supersession files before acting on an old next-action statement.

## Related work

The project takes a complementary direction to major single-cell foundation models, including Geneformer, scGPT, and scFoundation. The goal is not simply larger pretraining scale, but a representation whose biological claims survive explicit identity, measurement, donor, and leakage controls.
