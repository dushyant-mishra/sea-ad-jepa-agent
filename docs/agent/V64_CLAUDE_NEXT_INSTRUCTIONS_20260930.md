# Claude instructions — V64 final repository-consistency closeout before Phase B

**Date:** 2026-09-30

Continue from:

`claude/v64-exact-sampler-successor-20260930`

Audited head:

`7ad38eaf457d2fbb81f40f57a7b1747eac7776f1`

Do NOT execute Phase B yet.

## What is now accepted

- S57 CLOSED.
- S58 CLOSED.
- S59 CLOSED.
- S60 design CLOSED:
  - T7_R3_CONDITIONING_REFERENCE is materialized;
  - 21 R3 conditioning records;
  - 11 A-small / 10 B-small;
  - 0 same-side / 21 different-side;
  - realized large-arm draw persisted from frozen Phase-A rows;
  - mandatory CONDITIONAL_ON_REALISED_LARGE_ARM label persisted;
  - T19 guards conditioning records;
  - T17 now guards semantic drift under an unchanged rule identifier;
  - 7/7 mutation sweep detected.

Do not change these semantics.

## Remaining blocker S61 — committed test receipt is stale/inconsistent

At commit `7ad38eaf`, the actual committed file:

`results/v64/phase_b_design/V64_PHASE_B_MEASUREMENT_SUBSTRATE_TESTS_V1.json`

contains:

- `n_tests = 9`
- `n_real_tests = 7`
- `status = FAIL`

and specifically:

- T16 fails: `bound statistical contract digest is stale`
- T17 fails: `bound authority digest is stale`

This contradicts the reported final state of substrate 9/9 PASS.

The mutation sweep receipt says the mutated artifacts were restored byte-exact, so the likely explanation is:

> the test receipt was generated while V3 was temporarily mutated during the sweep and was not rerun/recommitted after restoration.

That is repairable, but repository authority must be self-consistent.

## Required closeout

1. Restore/verify the intended final artifacts:
   - statistical contract V3;
   - substrate contract;
   - R3 conditioning reference;
   - decision state;
   - test producer.

2. Rerun the substrate test suite ONCE against that restored final state.

3. Require:
   - 9/9 real tests;
   - T16 PASS;
   - T17 PASS;
   - T18 PASS;
   - T19 PASS;
   - overall `status = PASS`.

4. Commit the new final-state test receipt.

5. Record exact SHA-256s for:
   - statistical V3;
   - substrate contract;
   - R3 conditioning reference;
   - substrate test producer;
   - final substrate test receipt.

6. Add a final-state consistency guard that fails if:
   - any committed authoritative test receipt has `status != PASS`;
   - any bound authority digest differs from the live artifact;
   - a mutation-sweep restoration leaves a stale test receipt behind.

A simple closeout receipt is sufficient if it is generated from the final committed artifacts and checks those conditions.

## Do NOT change

- Phase-A V3 population 13,175;
- R1/R2/R3 definitions;
- conditioning records;
- weighting;
- donor/metacell thresholds;
- bootstrap seed/replicates;
- recoverability split scope;
- protected-column firewall;
- missingness rules;
- single-modality Phase-B boundary.

## Governance

Phase B = STOPPED.  
Stage 4 = NOT AUTHORIZED.  
TD60 = BLOCKED.  
Morabito = PROTECTED.  
TRAINING = OFF.  
Correspondence remains unopened.

After S61 is closed, STOP again for audit. Do not execute Phase B.
