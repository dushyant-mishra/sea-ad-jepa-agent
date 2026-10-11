# V79 Bayesian Geometry Controller Reconciliation R2 — 2026-10-11

## Live source checked

Source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`

Live head at reconciliation: `ea0102132eb25b3d282988181c95387bf4f57ff6`

Previous controller reconciliation source head: `c54019545c15e4b9932a79639e8de4659e0d822e`

The source branch advanced by two commits. The new commits add a machine-wide scheduler, timeout/rerun evidence, snapshot provenance, and snapshot-equivalence checks.

## What changed materially

The previous recovery launch oversubscribed the 16-core machine. Several Gaussian, Bernoulli, log-normal and ZTNB fits reached the old 4-hour timeout and were killed. This is a scheduling/runtime failure, not evidence that the corresponding statistical recovery worlds failed.

The lane now uses a machine-wide scheduler with lower concurrent fit count and longer per-fit timeout. ZTNB is also being evaluated on the GPU after the GPU was re-tested without severe CPU contention.

`results/v79/recovery/PROVENANCE.json` records computational equivalence between earlier frozen snapshots and the scheduler snapshot for Gaussian, Bernoulli and log-normal. This supports retaining already-completed fits when their model/world computation is unchanged.

## Bernoulli recovery audit

The provenance record claims the following Bernoulli parts are completed:
- S0 class absent
- S1 present
- S5 labels removed

It records S4 as still running from the earlier Bernoulli snapshot. S2 and S3 were killed by the earlier oversubscribed/4-hour execution and are scheduled for rerun.

Important evidence gap: the completed Bernoulli S0/S1/S5 result JSON payloads are not committed at the expected `results/v79/recovery/part_bernoulli_*.json` paths on live head `ea010213...`. The branch currently commits the provenance map, scheduler plan, and timeout evidence, but not the completed Bernoulli payloads needed to independently inspect final R-hat, ESS, divergences, effect recovery, and any A5 chain extension.

Therefore Bernoulli must NOT yet be called frozen or recovery-qualified.

## Current ruling

Terminal state remains:

`SIMULATION_QUALIFICATION_INCOMPLETE`

Bernoulli status:

`PARTIAL_RECOVERY_EVIDENCE__COMPLETED_PAYLOADS_NOT_COMMITTED__S2_S3_S4_INCOMPLETE__NOT_FREEZE_READY`

No corrected-TRAIN fitting is authorized yet.

## Next instruction to Macha

Do only the following for the Bernoulli gate before moving on:

1. Commit the completed Bernoulli S0, S1 and S5 recovery JSON records, including full diagnostics and the code snapshot recorded by each fit.
2. Make the A5 status explicit for S0/S1: whether an extension was needed, and if so commit the post-extension result rather than relying on the earlier marginal diagnostic.
3. Finish Bernoulli S2, S3 and S4 using the current bounded scheduler / equivalent frozen snapshot.
4. Commit all six S0-S5 records plus one combined Bernoulli recovery receipt that evaluates the preregistered recovery criteria: planted-effect recovery, absent-effect behavior, shuffled/permuted controls, R-hat, ESS, divergences and parameterization identity.
5. If all Bernoulli recovery criteria pass, freeze the Bernoulli parameterization prospectively and advance to the next recovery family. If any required criterion fails, keep Bernoulli nonterminal and repair only prospectively.
6. Do not start corrected TRAIN, do not export a downstream observation authority, and do not send any provisional Bernoulli posterior values to the factorial lane before independent audit.

## Firewalls unchanged

- no TEST/Morabito
- no pathology
- no target-discovery ranks/panels
- no SCENIC+/ATAC target evidence
- no V78 outcome-driven retuning
- no JEPA training/checkpoint generation
- no synthetic-arm outcome rescue
- `training_authorized=false`
