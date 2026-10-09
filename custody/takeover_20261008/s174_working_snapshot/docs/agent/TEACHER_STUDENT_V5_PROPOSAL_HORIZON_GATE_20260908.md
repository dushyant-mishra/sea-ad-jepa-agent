# Teacher/Student V5 proposal/horizon continuation gate — 2026-09-08

Status: `BASE_PROPOSAL_AND_ONE_POPULATION_EQUIVALENT_HORIZON_FROZEN__TRAINING_UNAUTHORIZED`

This continuation is deliberately layered **above** the immutable 66-pass V5 data-first snapshot rooted at `9684f4c2b7eff1da863ae50124c6aad49d25f137a84898e05e98d2ae1f0c67ad`. No file in that frozen 53-row prototype manifest is changed by this gate.

## Prospectively frozen constraints

Before selecting base proposal `q`, this gate freezes:

- total presentation horizon: exactly **4,553,407 cell presentations**, one full reader-fit-population equivalent;
- no automatic second epoch or horizon extension;
- maximum expected repeated exposure of any individual cell: **32**;
- minimum expected presentations for every one of the 1,400 reader-fit donor×operator groups: **16**;
- importance-sampling ESS fraction: **>= 0.50**;
- max/min per-cell importance-weight ratio: **<= 64x**.

The group-coverage floor has an explicit probability interpretation. With independent proposal draws and expected group count at least 16, `P(group gets zero draws) <= exp(-16)`. A union bound over all 1,400 groups is `< 1.58e-4`.

These are presentation-space constraints. They do not freeze update size, token budget, GPU packing, EMA half-life, or any execution schedule.

## Frozen base proposal

Scientific target remains unchanged:

`DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`.

Base proposal is now frozen as the unique continuation rule that maximizes the direct target component in the declared convex family while satisfying the frozen exposure and group-coverage constraints; the resulting proposal also passes the independently frozen ESS and importance-conditioning limits.

For each reader-fit cell:

- `p_target = 1 / (D * donor_cells)`;
- `q_source = 1 / (S * source_cells)`;
- `q_group = 1 / (D * donor_operator_groups_for_donor * group_cells)`;
- `q = alpha*p_target + beta*q_group + gamma*q_source`.

Exact coefficients:

- `alpha_target = 50747095471185150 / 1173046947290933909 = 0.04326092454217784`;
- `beta_operator_coverage = 5436880721882508 / 1173046947290933909 = 0.004634836426997731`;
- `gamma_source_uniform = 253256277841 / 265996376719 = 0.9521042390308244`.

Exact `p/q` importance correction is mandatory. Proposal mass does not redefine scientific mass.

Derived reader-fit diagnostics:

- proposal mass = 1.0;
- ESS fraction = `0.5993992196029957`;
- max/min importance-weight ratio = `57.8322200737568x`;
- max expected per-cell exposure = `32.0`;
- min expected donor×operator group presentations = `16.0`.

The repeat ceiling is attained by the 81-cell NPH52 donor `human_NPH_906`; the group-coverage floor is attained by a 1-cell HVS donor×operator group for donor `H19.03.319`. These are geometry facts only; no outcomes or protected populations were used.

Relational proposal remains unchanged from V2: `DIRECT_DONOR_ANCHOR_CELL_TRIPLET_TARGET_PROPOSAL_V2`; finite triplet budget remains unfrozen.

## Still unauthorized / unfrozen

- training and neural execution;
- successor-u0 materialization;
- TD60;
- protected-population/pathology/oracle access;
- GPU Philox production kernel;
- bounded V5 mechanical-qualification runtime;
- token/memory/update geometry;
- evidence/view/block numerical schedule;
- finite relational triplet budget;
- EMA half-life.

Next lawful gate: optimized GPU Philox keyed-dropout implementation and exact agreement to the frozen CPU V2 reference/test vectors, followed by bounded mechanical qualification. No training starts here.
