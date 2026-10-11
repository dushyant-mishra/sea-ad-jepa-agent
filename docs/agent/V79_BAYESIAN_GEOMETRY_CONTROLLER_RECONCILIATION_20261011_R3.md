# V79 Bayesian Geometry Controller Reconciliation R3 — 2026-10-11

## Live source checked

Source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`

Live head at reconciliation: `3798ac05dcfe9f2d226694200281872702253db7`

Current terminal remains:

`SIMULATION_QUALIFICATION_INCOMPLETE`

No corrected-TRAIN inference or synthetic-consumable authority is authorized.

## Material changes since R2

Macha advanced the lane substantially beyond `ea010213...`.

1. The A5 sampler-extension implementation was corrected so that a divergence appearing during the extension escalates target_accept under the pre-existing retry rule rather than terminating as NOT_DIAGNOSED. This is a code/contract consistency repair, not a new convergence threshold.
2. Log-normal S3 exposed that A5 bug: first pass R-hat 1.0325 / ESS 171 / 0 divergences; extension R-hat 1.0109 / ESS 395 with 1 divergence. The fit is being rerun under the corrected rule and is not qualified yet.
3. Detection/Bernoulli V1 failed recovery world S4 (operator-only): divergences at target_accept 0.9 and 0.95; the 0.99 retry was computationally infeasible at the observed rate and was stopped.
4. Before seeing any V2 result, Macha precommitted V2 = every random component non-centred as the final permitted detection sampler parameterization. If V2 fails any of S4, S0 or S1, detection must be reported NOT QUALIFIED with no further parameterization search.
5. Launch files now run V2 S4 on CPU and V2 S0/S1 on GPU from snapshot `61df6088`.

## Detection/Bernoulli ruling

V1 is no longer freezeable: it failed S4.

V2 is a scientifically acceptable prospective last-chance attempt because its stopping rule was committed before any V2 outcome. However, at live head `3798ac05...` the repository contains only the V2 launch script/job definitions; there are no committed V2 S0/S1/S4 result JSON payloads yet.

Therefore detection/Bernoulli status is:

`V1_FAILED_S4__V2_PRECOMMITTED_FINAL_ATTEMPT_RUNNING_OR_UNCOMMITTED__NOT_QUALIFIED`

If V2 passes S0, S1 and S4, the exact same V2 parameterization must then be run/committed for the complete S0-S5 suite before the family can be called recovery-qualified. Earlier V1 S2/S3/S5 results cannot substitute for a complete V2 suite.

## Other families

Gaussian remains incomplete: S0 previously converged; S1 requires the A5-compliant rerun; S2-S4 remain in the corrected-rule queue and no terminal combined PASS is committed.

Log-normal remains incomplete: Q10 was promising, but S3 exposed the A5 implementation bug and must be rerun under the corrected rule; the full S0-S5 recovery suite is not terminally committed.

ZTNB remains incomplete: Q9 was promising and S0-S5 recovery jobs are/were scheduled across CPU/GPU snapshots, but no complete independently auditable terminal recovery receipt is committed.

## Provenance / evidence quality

The existing `PROVENANCE.json` is stale relative to the current head: it was written at 06:50Z and still describes the earlier V1 Bernoulli and old scheduler state. It should not be used as the current authority after the V1 S4 failure and V2 precommit.

The machine-readable `V79_ACTIVE_STATE.json` is also stale relative to current head: it was last updated at 08:05Z and still describes V1 Bernoulli as the frozen detection setting. The current self-audit and commits supersede that description.

## Required next actions for Macha

1. Commit V2 S0, S1 and S4 result JSONs with R-hat, ESS, divergences, A5/retry history, recovery values and code snapshot.
2. If any of V2 S0/S1/S4 fails the preregistered contract, stop detection and label it NOT QUALIFIED. Do not search V3.
3. If all three pass, run and commit the complete V2 S0-S5 suite under the exact same parameterization and produce one combined receipt.
4. Refresh `V79_ACTIVE_STATE.json` and `PROVENANCE.json` so machine-readable state matches the live scientific state.
5. Finish Gaussian, log-normal and ZTNB recovery under the corrected A5 implementation and commit terminal combined receipts.
6. Only after all required recovery families pass may the benchmark gate run. Corrected TRAIN remains blocked until then.

## Firewalls unchanged

- no TEST/Morabito
- no pathology
- no target-discovery evidence
- no SCENIC+/ATAC target evidence
- no V78 outcome-driven retuning
- no provisional Bayesian values sent to H1/H2
- no JEPA training/checkpoint generation
- `training_authorized=false`
