# Contextual JEPA — learning biological state from partial RNA

> **Can a model recover biologically meaningful cell state from incomplete RNA evidence without solving the task through gene identity, measurement artifacts, or answer leakage?**

This repository is a pathology-blind, donor-aware JEPA research project built around a **41,238-address Molecular Ledger**. It keeps gene/address identity, physical measurement state, evidence visibility, donor structure, and provenance explicit.

For the live scientific boundary, read [`START_HERE.md`](START_HERE.md) first. Historical artifacts remain evidence/provenance; old “current” labels or next-action text do not override the canonical startup surface.

## Current status — October 6, 2026

- **V75 100K measurement architecture is qualified within its declared scope.**
- **Premise qualification V3 is frozen and merged as governance.**
- **500K promotion is not authorized.**
- **No production teacher target or representation is currently qualified.**
- **Target lineage reconstruction is complete.**
- **Training and multimodal training are OFF.**
- **Stage A execution and Stage 4 are not authorized.**
- **TEST remains sealed and Morabito protected.**
- **`width=160` is network/token capacity, not a biological-dimension result.**
- **The synthetic learned-state scaling ladder is stopped.**

## Current task

The current task is **runtime-safety reconciliation onto the frozen V3 premise**, not model training and not another target-design cycle.

The immediate engineering question is whether the recovered V5 teacher/student mechanics can be composed with fail-closed optimizer-step sequencing on current `main`: gradient validation before stepping, single-use guarded optimizer permission, explicit proof that the optimizer step completed, and only then EMA. The next bounded runtime issue is authority-bound checkpoint/reload semantics.

This work is mechanics only. Historical `CurrentTrainingAuthorityV2` / `OptimizerGuardV4` code can inform the implementation, but historical existence does not grant current training authority. With no qualified production target or representation, final training-authority issuance must remain unreachable.

## Authority freshness

**Authority freshness: update canonical surface when the current task closes or the next authorized task changes.**

A completed, blocked or superseded task must not remain advertised as current. `START_HERE.md`, the latest pointer, current authority index, supersession map, active state and generic next-action router must move with the actual project frontier.

See:

- [`docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`](docs/agent/JEPA_LATEST_HANDOFF_POINTER.json)
- [`docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json`](docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json)
- [`docs/agent/JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V3_FINAL.md`](docs/agent/JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V3_FINAL.md)
- [`docs/agent/CURRENT_AUTHORITY_INDEX.md`](docs/agent/CURRENT_AUTHORITY_INDEX.md)
- [`docs/agent/CURRENT_SUPERSESSION_MAP.md`](docs/agent/CURRENT_SUPERSESSION_MAP.md)

## Scientific objective

The project is **not** primarily an exact missing-expression imputation project. The objective is to determine what transcriptomic structure is recoverable from lawful partial RNA, which parts transfer across biological/measurement contexts, and which stronger regulatory or causal claims require independent evidence.

A convincing RNA representation must separate recoverable structure from easier shortcuts such as gene/address identity, source/operator support patterns, sequencing depth and normalization leakage, direct or indirect access to the hidden answer, and cell-level pseudoreplication. Success at this level does not automatically establish transferable biological state.

## Observation semantics

Missingness is explicit rather than collapsed into one mask. A measured zero is evidence; a structurally unmeasured feature is not a zero. Artificial model masking changes view visibility; it does not rewrite what the assay physically measured.

## Implemented runtime versus scientific authority

The repository contains a canonical token-preserving IPB teacher/student runtime over the 41,238-address vocabulary. The encoder emits contextual gene states and a 160-wide cell token. The current runtime's JEPA loss predicts teacher gene/block representations using a predictor that can access both student gene states and the student cell token.

Those are implemented mechanics, not proof that the target or the 160-wide cell token is the correct biological state.

Current evidence says:

- `cell_state` exists structurally but is **not qualified as the unique or sufficient global biological state**;
- gene/block states are directly objective-constrained but are **not automatically qualified as the global biological state**;
- earlier T0/T1/TCTX target families did not qualify;
- strict donor-cross-fitted residual targeting returned `RESIDUAL_TARGET_DOES_NOT_RESCUE`;
- competing value-blind target constructions were defined prospectively, but no winner was selected;
- the corrected synthetic T_A/T_B comparison was `NOT_INFORMATIVE` and could not choose the target.

Therefore the architecture is an **implemented runtime under unresolved target/state authority**, not a qualified production biological-state model.

## V75 measurement architecture

V73–V75 built a FULL104-like synthetic measurement substrate to stress observation geometry, donor/operator support, empirical QC realization, fragment linkage, and matched controls.

Current narrow terminal:

`PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED__500K_PROMOTION_INDETERMINATE`

This qualifies the measurement architecture at 100K, not learned biology.

The V75 observer uses 96 anonymous synthetic features. The canonical neural runtime uses learned identities for 41,238 addresses. Arbitrarily assigning those 96 features to canonical gene slots remains scientifically invalid.

## Data scale

The authenticated FULL104 reader-fit population contains **4,553,407 cells, 104 donors, 42 measurement operators, 1,400 donor × operator strata, and 41,238 molecular addresses**.

Protected validation/oracle, DEV/SEALED, pathology, correspondence and other restricted populations remain governed by their lane-specific release authorities.

## Dimensionality

Architectural width and biological rank are deliberately separated. A 160-wide token space may contain a much lower-dimensional stable biological subspace. Historical D_shared/D_private/D_total/D_obs machinery remains methodology; its existence does not make `160` a biological result.

## Why the project is fail-closed

The project has stopped or revised work for provenance mismatches, shortcut channels, invalid null geometry, target leakage, stale authority pointers, numerical defects and controls that could not falsify the intended failure mode.

A lower loss, green CI, smoke checkpoint or successful infrastructure execution is never sufficient for a biological claim.
