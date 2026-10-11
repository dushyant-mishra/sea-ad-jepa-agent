# V79 Bayesian Geometry Controller Reconciliation — 2026-10-11

## Live state checked

Controller inspected the live Macha source branch:

`analysis/v79-bayesian-synthetic-geometry-20261009`

Current live head:

`c54019545c15e4b9932a79639e8de4659e0d822e`

Latest committed machine-readable state:

`docs/agent/V79_ACTIVE_STATE.json`

Committed terminal remains:

`SIMULATION_QUALIFICATION_INCOMPLETE`

The state records `real_data_inference_started=false` and no qualified posterior-generative authority.

## What is currently committed

- Gaussian recovery: S0 converged; S1 requires the A5 rerun; later seeds were still running/retrying at the last committed state.
- Bernoulli recovery: V1 evidence improved convergence, but full recovery was not yet frozen as passed.
- ZTNB: small qualification/recovery evidence is promising, but the complete S0-S5 recovery suite is not yet committed as terminal PASS.
- log-normal: small qualification/recovery evidence is promising, but the complete S0-S5 recovery suite is not yet committed as terminal PASS.
- benchmark: not frozen.
- corrected-TRAIN fitting: not started.
- held-out PPC/Q5: not started.
- biology geometry authority: absent.
- observation geometry authority: absent.

## Next unmet gate

The next gate is still simulation qualification.

Do not begin corrected-TRAIN fitting yet.

### Immediate instruction to Macha

1. Reconcile every externally running recovery job into committed GitHub evidence. For each family/seed, record PASS/FAIL, R-hat, ESS, divergences, and whether the result is under the currently frozen parameterization.
2. Finish the Bernoulli V1 S0/S1 A5 work first. If the preregistered recovery/convergence contract passes, freeze that Bernoulli parameterization prospectively.
3. Rerun/complete the full Bernoulli S0-S5 recovery suite under that exact frozen parameterization.
4. If Bernoulli still fails, stop and report the failure; do not push it into corrected TRAIN.
5. Do not change likelihood, hierarchy, priors, estimand, or conditioning without a prospective model-change amendment.
6. Keep `training_authorized=false`.

After Bernoulli is terminally reconciled, the next controller review should decide whether to move to Gaussian recovery, then log-normal/ZTNB recovery, then benchmark, following the canonical controller handoff.

## Integration policy unchanged

If and only if Macha later reaches terminal qualification, preserve the richest defensible posterior-generative geometry from corrected TRAIN. Biology-side qualified posterior structure may parameterize H1; observation-side qualified posterior structure may parameterize H2. Preserve posterior uncertainty where useful and randomize identities needed for planted causal truth.

Do not consume provisional sampler estimates into the synthetic generator.

## Firewalls unchanged

No TEST/Morabito, pathology, target-discovery ranks/panels, SCENIC+/ATAC target evidence, representation winners, Stage4/500K, V78 outcome-driven retuning, or JEPA training/checkpoint generation.