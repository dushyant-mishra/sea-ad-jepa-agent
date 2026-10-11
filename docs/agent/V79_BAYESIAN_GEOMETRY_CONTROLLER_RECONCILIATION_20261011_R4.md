# V79 Bayesian Geometry Controller Reconciliation R4 — 2026-10-11

## Scope

Synthetic/V79 Bayesian dataset-geometry lane only. Target discovery is a separate lane and is not part of this controller action.

## Live source checked

Source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`

Live head: `d9d8cac6fa65463529374c50a9c309e7eb7e5405`

The source branch has not advanced beyond this head during the present audit.

## Code-path qualification

`results/v79/recovery/CODE_PATH_QUALIFICATION_0bc45513.json` records successful local end-to-end qualification of the recovery code path for Gaussian, Bernoulli, log-normal and ZTNB, plus scheduler outcome classes. It verifies frozen sampler-config identity, A5-v2 retry semantics, commit-bound code snapshots, attempt/divergence-location records and combined-receipt mechanics.

This qualifies the execution path. It does **not** itself qualify any scientific recovery family.

Earlier Gaussian/log-normal/ZTNB fit material was moved under `results/v79/recovery/evidence_pre_code_path_qualification_20261011/`. It remains useful historical/development evidence but must not be promoted to terminal recovery authority after the code-path qualification boundary.

## Detection/Bernoulli terminal ruling

V1 already failed S4 because of divergences at target_accept 0.9 and 0.95, with the 0.99 attempt operationally infeasible.

V2 was prospectively declared the final allowed detection parameterization: all random components non-centred.

Current post-code-path-qualified S4 result:
- code snapshot: `0bc455131cf80ce0ef563b6ccbf6301b1ee09f58`;
- sampler config: `DETECTION_V2_NC_ALL`;
- frozen ESS minimum: `400`;
- worst R-hat: `1.0050606796610788`;
- worst ESS: `361.8761303230284`;
- divergences: `0` across the final chains.

The ESS criterion fails. Under the frozen recovery contract, this is terminal.

Detection ruling:

`DETECTION_V2_FAILED_S4_ESS__DETECTION_FAMILY_NOT_QUALIFIED__NO_V3__NO_THRESHOLD_CHANGE__NO_POST_FAILURE_TUNING`

S0/S1 completion, if already available or in-flight, may be preserved for audit completeness but cannot rescue or reverse the S4 family failure.

## Remaining scientific recovery gate

The only still-eligible simulation-recovery families are:
- Gaussian;
- log-normal;
- ZTNB.

No terminal post-code-path-qualified S0-S5 scientific recovery receipt is currently committed for any of those three families. The older files under `evidence_pre_code_path_qualification_20261011/` cannot substitute for a current full-suite receipt.

Therefore the next gate is:

`POST_CODE_PATH_QUALIFICATION_FULL_S0_S5_RECOVERY_FOR_GAUSSIAN_LOGNORMAL_ZTNB`

For each remaining family, use the already frozen model/sampler configuration and corrected A5 rule. Every required S0-S5 world must reach a terminal result and a combined family receipt. If a required world fails after its prospectively allowed retry/extension path, mark that family `NOT_QUALIFIED` and stop it. Do not invent a new parameterization or relax thresholds after seeing results.

## Real-data boundary

Corrected-TRAIN fitting remains blocked.

Do not benchmark or fit a family to corrected TRAIN until its simulation recovery is terminally qualified and independently audited. Detection/Bernoulli is no longer eligible for corrected-TRAIN fitting as a qualified family.

After the remaining family rulings are terminal, the lawful sequence remains:
1. benchmark each qualified family alone under the frozen benchmark rule;
2. corrected-TRAIN fit only for qualified families;
3. held-out PPC and Q5 donor×class adjudication;
4. positive-count family ruling;
5. biology geometry authority;
6. observation geometry authority, explicitly marking detection as unqualified;
7. self-audit and independent downstream audit.

## Required source-state repair

`docs/agent/V79_ACTIVE_STATE.json` is stale (`updated_utc` 2026-10-11T08:05Z; head_at_write `6082624...`). It still describes obsolete Bernoulli V1/V2 scheduling and outdated queues.

The root recovery provenance was intentionally displaced by the code-path-qualification cleanup; the remaining historical `PROVENANCE.json` lives under the pre-qualification evidence archive and must not be presented as current authority.

Macha must publish fresh machine-readable state/provenance for the post-code-path-qualified recovery phase, recording:
- live code snapshot;
- detection terminal NOT_QUALIFIED;
- no V3 allowed;
- Gaussian/log-normal/ZTNB current S0-S5 status;
- `real_data_inference_started=false`;
- corrected-TRAIN blocked;
- exact current scheduler/job identities.

## Controller terminal

`SIMULATION_QUALIFICATION_INCOMPLETE__DETECTION_TERMINAL_NOT_QUALIFIED__GAUSSIAN_LOGNORMAL_ZTNB_POST_CODE_PATH_RECOVERY_PENDING__CORRECTED_TRAIN_BLOCKED__TRAINING_OFF`

`training_authorized=false`
