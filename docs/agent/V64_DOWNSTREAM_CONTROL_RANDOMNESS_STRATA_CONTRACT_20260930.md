# V64 downstream control-randomness strata contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE — freeze before Phase B matrix values are opened

## Why

The repaired exact Phase-A sampler retained 13,510 edges.

For 344 retained edges, CONTROL_A was drawn from an exact admissible set of cardinality 1. The control is structurally lawful, but there is no random choice within that selected side.

For 167 edges, A and B are structurally forced to coincide because both draws land on the same singleton admissible side.

This is not a sampler failure. It is a support property of the exact control universe.

It must not be hidden inside an ordinary randomized control-vs-control null.

## Frozen distinction

Every retained edge must carry a structural randomness class determined **before any Phase-B matrix value is opened**.

At minimum:

- `RANDOMIZED_SUPPORT_GT10`
- `SMALL_RANDOMIZED_SUPPORT_2_TO_10`
- `FORCED_SINGLETON_SUPPORT_1`

The exact downstream labels may be refined only from structural Phase-A information, never from Phase-B outcomes.

## Rules

1. A singleton control remains a valid structural matched control.
2. A singleton control is not described as randomized.
3. A/B equality on the same singleton side is structurally forced and contributes no evidence that the null generator is calibrated.
4. Primary linked-vs-CONTROL_A analyses may retain singleton edges if the estimand permits, but results must report the singleton/small-support strata separately.
5. Control-vs-control null calibration must report:
   - all eligible randomized comparisons;
   - forced singleton coincidences separately;
   - small-support comparisons separately.
6. Do not drop, rescue, redraw or reweight singleton edges after inspecting RNA/ATAC correspondence.
7. Any exclusion or weighting rule used for inferential calibration must be frozen before Phase B.

## Phase-B gate

Phase B remains stopped until:

- the per-edge structural cardinality/side fields needed for these strata are bound to the Phase-A artifacts;
- the downstream null/statistical contract states exactly how each stratum enters each test.

No biological matrix values are needed to close this design requirement.

## Governance

TRAINING OFF.  
Phase B STOPPED.  
Stage 4 NOT AUTHORIZED.  
Morabito PROTECTED.
