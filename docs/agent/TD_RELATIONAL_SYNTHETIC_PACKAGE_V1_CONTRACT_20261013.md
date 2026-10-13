# Synthetic → TD relational test-qualification package V1 — prospective contract

Date: 2026-10-13  
Lane: synthetic dataset only  
Status: `PREFROZEN_BEFORE_REPOSITORY_REALIZATION__TD_EXECUTION_OFF`

## Purpose

Produce one immutable external known-truth package for PR #316's read-only Target Discovery test-of-test interface. The package qualifies synthetic challenge construction only. It does not execute or adjudicate the TD gate.

## Lane firewall

This branch may create synthetic generator code, challenge truth, blinded fit views, hashes and synthetic qualification receipts.

It must not modify PR #316, PR #313, PR #314, TD estimands, TD thresholds, TD PASS/FAIL/NOT_ESTIMABLE logic, target selection, TD60, Stage4 or training authority.

No real TD57C/TD59/#314/#316 outcomes may be used to tune challenge amplitudes or geometry.

## Existing-asset audit

### Q00–Q11
Useful observation/nuisance falsifiers, but no explicit cell-level C2 relational truth object and no PR316 distance-interface realization. Not sufficient as the external C2 package.

### Historical Stage81A3 full-transcriptome fixture
Useful scientific basis for broad/fine/rare/donor latent programs and independent observations. It was not frozen as a PR316-compatible blinded C2 test-of-test package and does not provide the required explicit controller-separated relational truth at this interface.

### PR #311 rare-biology family
Useful scientific basis for donor-recurrent/restricted rarity, exact-zero donors, technical pseudo-rarity and source-dependent observability. Its V2/V3 qualification establishes challenge geometry, not the PR316 C2 relational test interface.

Therefore all nine PR316 capabilities are realized prospectively in this package, while reusing the above scientific mechanics. The capability ledger must say `SATISFIED_NEW_PROSPECTIVE_WORLD`; it may not overclaim a pre-existing frozen relational world.

## Frozen TD interface

Exactly nine distinct opaque challenge IDs will be bound to:

- `REL_BROAD_MESO_POSITIVE`
- `REL_FINE_RECURRENT_POSITIVE`
- `REL_RARE_LOCAL_ISLAND_POSITIVE`
- `REL_MULTI_ISLAND_POSITIVE`
- `REL_DONOR_RESTRICTED_POSITIVE`
- `REL_SOURCE_VISIBILITY_STRESS`
- `REL_TECHNICAL_TWIN_NEGATIVE`
- `REL_NULL_NEGATIVE`
- `REL_UNDERPOWERED_POSITIVE`

Fit-view JSON contains exactly the PR316 adapter fields:

`source, panel_id, z_distances, x_distances, y_distances, donor_ids, operator_ids, global_rows, focal_mask, neighbor_pool_mask, null_y_identity_maps, min_focal_anchors_per_donor`.

No capability name, semantic class, expected status, controller truth, `R`, pseudo-rare identity or technical/null designation is permitted in a fit-view file.

## Frozen population mechanics

Nominal challenges use 5 donors × 35 entities/donor. One operator is used per challenge so the test concerns biology rather than operator heterogeneity. Thirty-five entities provide 34 within-donor candidates; the frozen 1/8 scale therefore has `ceil(34/8)=5` selected neighbors, exactly meeting PR316's prospectively frozen minimum without inflating support.

Donor-restricted truth uses 6 donors × 35 entities: exactly 5 biologically active donors and at least 1 exact-zero donor.

Underpowered positive truth uses 4 donors × 35 entities. Biology is real and well observed, but recurrence is deliberately below PR316's frozen minimum of 5 donors.

All distance matrices are deterministic Euclidean distances expressed in fixed 1e-4 units as integers. This is a storage representation only and preserves the intended ordering.

Each fit view contains exactly 64 deterministic donor/operator-preserving Y-identity permutations.

## Frozen biological challenge mechanics

### Broad/mesoscale positive
X and Y share coarse biological organization but carry independent fine-scale jitter. The planted truth is explicitly mesoscale/coarse rather than a claim of universal fine-scale identity.

### Fine recurrent positive
Z, X and Y observe the same smooth within-donor latent biological trajectory with independent small observation noise.

### Rare local island positive
Each donor contains a compact rare biological island. The rare program's local latent geometry is shared by X and Y; common/background cells do not receive the same protected local geometry.

### Multi-island positive
The same rare biological class occurs in two disconnected local islands within every supported donor. Disconnectedness is controller truth, not an observation label.

### Donor-restricted positive
The rare relational program is present in exactly five donors and genuinely absent in the remaining donor(s). Zero prevalence is biological truth, not technical missingness.

### Source-visibility stress
This challenge reuses exactly the same latent coarse biological coordinates and seed as the broad/mesoscale positive challenge but degrades one observation view. Its controller record is explicitly linked by a shared latent-truth hash.

### Technical-twin negative
A frequency-matched focal/local structure is generated on the locality/observation side, while target biological relational truth is absent and X/Y biological geometry is independent.

### Null negative
No target biological relational relation is planted between X and Y.

### Underpowered positive
A genuine fine biological relation is planted, but only four recurring donors exist. Correct test semantics are controller-side `NOT_ESTIMABLE`; the fit view contains no expected verdict.

## Explicit controller relational truth

For every challenge the controller-only truth contains:

- latent biological coordinates;
- canonical Euclidean relation metric;
- SHA-256 of the latent biological distance matrix;
- biological-relation-present flag;
- rare-state truth when relevant;
- island identity when relevant;
- donor prevalence;
- exact-zero donor identity when relevant;
- technical/null designation;
- expected semantic status, controller-only.

The fit process receives none of these fields.

## Source-stress counterfactual identity

`REL_BROAD_MESO_POSITIVE` and `REL_SOURCE_VISIBILITY_STRESS` use the same fixed latent seed `10101`. Their latent-coordinate hash must be byte-identical. Their fit-view hashes must differ.

## Seed ledger

Challenge seeds are deterministic from this contract:
- broad mesoscale: `10101`
- source visibility: `10101`
- all remaining capabilities: `316100 + capability_index * 1009`

Null permutations use `challenge_seed + 9000`.

No seed may be changed after realization.

## Freeze / realization sequence

1. commit this contract and generator tests;
2. commit deterministic generator implementation;
3. run tests without TD executor;
4. realize package once from the exact generator head;
5. validate truth, controls, firewall, IDs, hashes and source-stress latent identity;
6. write immutable file ledger and synthetic qualification receipt;
7. deliver package identity/hashes to PR #316 as a comment only;
8. stop.

## Authority

All false:
- synthetic world regeneration;
- qualification model fitting;
- real TD execution;
- target selection;
- TD60;
- Stage4;
- JEPA training.

Terminal before realization:

`TD_RELATIONAL_SYNTHETIC_V1_PREFROZEN__NINE_CAPABILITIES_DEFINED__TD_EXECUTOR_NOT_RUN__REAL_TD_OFF__TRAINING_OFF`
