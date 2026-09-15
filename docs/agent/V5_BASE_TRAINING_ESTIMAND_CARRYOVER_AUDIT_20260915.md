# V5 base-training estimand carryover audit — 2026-09-15

Status: `BASE_TRAINING_ESTIMAND_OPEN__OLDER_DONOR_UNIFORM_WORDING_NOT_CURRENT_AUTHORITY`

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

## Classification

- estimand sensitivity across empirical/FULL104, source-uniform, and donor-oriented views: `ALREADY_AUDITED`
- production base-training estimand: `OPEN`
- planning-lane proposal algebra: supporting mechanics only; not current estimand authority

## Carryover finding

The divergent planning-lane `src/sea_ad_jepa/v5/proposal_policy_v1.py` describes its donor-uniform target mass as the **"frozen donor-uniform target"** and builds an exposure-constrained proposal `q` around it.

The current V5 dataset-target authority, however, explicitly says that the production base-training estimand remains open and that empirical/FULL104, source-uniform, and donor-primary/operator-balanced views answer different scientific questions. Therefore the planning-lane phrase cannot be widened into current V5 authority.

`OLDER_PROPOSAL_POLICY_FROZEN_DONOR_UNIFORM_WORDING != CURRENT_V5_BASE_TRAINING_ESTIMAND_AUTHORITY`

## Current rule

Current V5 code may reuse the algebraic distinction `p != q != packing`, importance-weighting mechanics, and exposure-constraint mechanics only after the scientific target mass `p` is supplied by a separately frozen `BaseTrainingEstimandAuthorityV1`.

No proposal helper, scheduler, sampler, or packing code may choose the scientific estimand implicitly.

The current estimand authority schema therefore binds:

- population authority root;
- support/eligibility authority root;
- explicit estimand identifier;
- exact scientific-weight artifact root;
- weight schema;
- normalization rule;
- scientific weight unit.

It deliberately contains no proposal, packing, dimension-selection, or candidate-estimand default.

## Not frozen here

This audit does **not** choose among:

- empirical/FULL104 cell mass;
- source-uniform mass;
- donor-primary mass;
- donor-primary/operator-balanced mass;
- any later environment/worst-environment estimand.

That choice must be justified prospectively from the scientific question, not selected because one representation or shortcut metric looks better under it.
