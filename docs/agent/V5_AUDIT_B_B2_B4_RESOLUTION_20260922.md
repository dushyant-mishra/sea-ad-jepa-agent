# Audit-B B2 scientific resolution and B4 execution freeze

Date: 2026-09-22

Status:

`OUTCOME_BLIND_B2_RESOLVED__B4_MATERIALIZED__N1_NOT_EXECUTED__TRAINING_OFF`

## Immutable parents

- Audit-B V1 preexecution parent:
  `95db537de2df04e83c72d17ab788f985901ee4b644769d598243a9eed5eef398`
- RNG-V3 authority:
  `775aba506982a9a8dbecccb454d8d3d68709e524bb7f67e9397bbf819b72c2fb`
- RNG global seed:
  `1267387626254385975` — frozen, not spent.

No Audit-B burden result was inspected before this resolution.

## B2 decision

### Primary burden population

Primary:

`SOURCE_BALANCED__DONOR_UNIFORM_WITHIN_SOURCE__TARGET_UNIFORM_V1`

Reason: Audit-B is an information-channel / technical burden guard across HVS,
NPH52 and SEA_AD, rather than an estimate of the biological donor population
itself. Equal source mass prevents one acquisition/source environment from being
diluted by the others.

Mandatory robustness aggregate:

`DONOR_UNIFORM_ACROSS_ALL_DONORS__TARGET_UNIFORM_V1`

This preserves direct visibility into the project's donor-primary population
estimand. The robustness aggregate cannot replace or override the frozen primary
aggregate after N1.

All three sources must also remain reported separately.

### Precision scope

`ONE_PREDECLARED_PRIMARY_BURDEN_STATISTIC_V1`

The original prospective wording referred to the relative standard error of
"the primary burden statistic" in the singular. Requiring all 18 policy x rung
cells to control escalation would be a new and much stricter multiplicative
condition.

All 18 nonuniform policy x rung cells remain mandatory reports; 17 are
non-gating for sample escalation.

### Primary precision cell

Policy:

`RIDGE8_CONDITIONAL`

Rung:

`1/20 = 5%`

Reason:

- RIDGE is the currently frozen primary expression-proxy attacker family.
- 5% is the first rung in the prospectively frozen ascending burden ladder.
- This choice uses only already-frozen design roles; it is not selected from
  Audit-B burden outcomes.

### Precision rule

For the primary cell:

[
SE leq maxleft(rac{1}{860}, 0.05|arDelta|ight)
]

where (arDelta) is the target-level normalized B2 burden difference.

The primary 5% mask contains exactly:

[
1 + leftlfloorrac{(17186-1)}{20}ightfloor = 860
]

addresses, including the target.

Therefore (1/860) is frozen as a structural absolute-SE floor representing one
average masked-address share at the primary rung. It is derived solely from
pre-outcome mask geometry.

Consequences:

- meaningful nonzero effects retain the original 5% relative-SE requirement;
- a mean near zero no longer causes RSE to explode solely because of division by
  a near-zero number;
- an exactly zero mean can be judged precisely estimated if its absolute SE is
  small;
- a zero/near-zero mean with large absolute uncertainty still escalates.

The rule is:

`HYBRID_ABSOLUTE_OR_RELATIVE_TARGET_SAMPLE_SE_V2`

and zero means:

`ZERO_MEAN_USES_ABSOLUTE_SE_BRANCH_V1`

## Semantic receipts

B2 scientific resolution V3:

`766f467f4566cf0087ca4bc22f5263575a8ae50d7e5905666886190c3ad95889`

Precision-rule authority V2:

`0a712b3aeebc42732726667722c90b2b9d97a6110cba157c2d99aa642c0c97b4`

Executable B4 contract V2:

`2c91e661812ab5cbb22902ddffb7a098ed11300c42a8c465e76389153e0200aa`

## What B4 authorizes

B4 authorizes only Audit-B execution under the frozen prefix ladder:

- N1 = 256;
- N2 = 1,024 only if frozen primary precision at N1 is insufficient;
- N3 = 4,096 only if frozen primary precision at N2 remains insufficient.

The RNG seed, target prefixes, weighting, primary cell and precision thresholds
may not change after seeing N1.

Before N1, the B4 no-compute preflight must verify:

- the B4 contract canonical digest;
- the signed B2 resolution digest;
- the precision-rule authority digest;
- the RNG-V3 semantic digest and global seed;
- Phase-IV target-sample freeze and all seven bound inputs;
- heavy-statistics qualification;
- exact mask-plan generator;
- exact burden estimator;
- FULL104 manifest;
- canonical address registry.

## What B4 does not authorize

B4 does not authorize:

- terminal masking;
- P1/P2/P3/P4 terminal selection;
- target-panel selection;
- rare-tail molecular analysis;
- TD60;
- pathology;
- DEV/SEALED;
- D_shared;
- G5;
- teacher/student training.

Current firewall:

`N1_UNOPENED__MASKS_NONE__BURDEN_NOT_RUN__TERMINAL_MASKING_UNOPENED__RARE_TAIL_MOLECULAR_UNOPENED__TD60_UNEXECUTED__TRAINING_OFF`
