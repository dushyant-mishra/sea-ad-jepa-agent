# V79 Bayesian Geometry Takeover — 2026-10-10

Canonical handoff for Macha's Bayesian dataset-geometry lane.

## Start here

- Source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`
- Source head frozen for this handoff: `ba61ed4cfca6747e32c21aeabbeed6453e5ea31e`
- Audit branch: `audit/v79-bayesian-geometry-snapshot-20261010`
- Audit head inherited by this handoff: `2fa0b3ec705cd616123172c1a78b17be32ccab6a`
- Handoff branch: `handoff/v79-bayesian-geometry-takeover-20261010`

Read first:
1. `docs/agent/V79_BAYESIAN_GEOMETRY_AUDIT_SNAPSHOT_20261010.md`
2. `docs/agent/V79_BAYESIAN_GEOMETRY_AUDIT_STATE_20261010.json`
3. `docs/agent/V79_SELF_AUDIT_LOG.md`
4. current `scripts/v79/` and `tests/v79/`
5. `results/v79/recovery/` including stopped/superseded logs.

## What this lane is

This is a TRAIN-only Bayesian geometry/recovery lane for estimating identity-scrubbed dataset structure that may later inform synthetic-world design. It is not target discovery and it is not the PR #253 factorial synthetic-world generator lane.

PR #249 is a different, historical target-discovery Bayesian spike and must not be used as this lane's authority.

## Exact terminal state at handoff

`SIMULATION_QUALIFICATION_INCOMPLETE`.

Do not describe this lane as qualified, final, or ready for real-data inference.

Committed evidence at source head:
- held-out NumPyro PPC end-to-end test passed locally;
- detection S1 recovery converged (worst R-hat 1.0087; ESS 539; 0 divergences);
- detection S0 recovery failed contract convergence (worst R-hat 1.0194; ESS 205; 0 divergences);
- Phase C log-normal remained marginally non-converged on donor spread in the last reported qualification;
- the first full ZTNB qualification timed out; the branch contains the subsequent progress-streaming and stable-softplus likelihood fix plus tests;
- old detection S2/S3 jobs under the superseded centring setting were stopped and their logs preserved;
- no real expression-value Bayesian fit had begun at the last audited snapshot.

## External jobs that were running after the audited source head

The user-provided machine snapshot reported these jobs launched outside GitHub:

1. Detection candidate V1 on S0 and S1, using donor + donor×class non-centring.
2. Gaussian recovery rerun after donor×class non-centring correction.
3. Phase C log-normal donor reparameterization experiment.
4. ZTNB Q9 qualification from snapshot `5972ec10` with progress streaming.

These are NOT terminal GitHub results. Before doing anything else, inspect their output files on the execution machine and bind each result to its exact snapshot commit and command. If output is missing or partial, preserve the failure/timeout rather than reconstructing success.

## Required continuation order

1. Reconcile all four externally running jobs with their exact snapshot hashes.
2. Freeze the per-likelihood sampler parameterization only after the recorded simulation experiments justify it.
3. Rerun the complete detection, Gaussian, log-normal and ZTNB recovery suites under the selected settings.
4. Require every preregistered convergence/recovery criterion to pass. A local success on one planted world is insufficient.
5. Run the compute benchmark and freeze gene count/fold count.
6. Only after recovery + benchmark pass may real corrected-TRAIN phases B0/A/B/D1/C run.
7. Run held-out PPC / Q5 and bootstrap under the frozen settings.
8. Build the scrubbed artifact and report only after those gates pass.
9. Audit identity leakage/custody before allowing the synthetic-world lane to consume the artifact prospectively.

## Scientific interpretation boundary

The Bayesian lane may estimate distributions/variance allocations and uncertainty across broad class, donor, source/operator, donor×class and residual geometry. It must not export named real gene programs, donor-by-gene signatures, pathology, target ranks, SCENIC+/ATAC target evidence, or TEST/Morabito content into synthetic truth.

If its final qualified result conflicts with deterministic corrected-TRAIN localization from PR #250, freeze the disagreement and design a resolving experiment. Do not average the two or retune a completed V79 tournament post hoc.

## Parallel lane boundaries

- Target discovery: separate; current preflight described by PR #259, not owned here.
- Factorial synthetic world: PR #253 implementation, #256 audit, #257 takeover; do not modify from this branch.
- V78: frozen.
- JEPA training/checkpoints: unauthorized.

## Stop conditions

Stop rather than continue if:
- recovery criteria fail after the prospectively selected parameterization;
- exact snapshot provenance for a result cannot be established;
- real-data runners no longer refuse before qualification;
- identity-scrubbed output contains forbidden named biology or clinical/pathology information;
- any step would require post-outcome sampler/model tuning not covered by a new prospective amendment.

This handoff preserves current work; it does not authorize the next scientific gate.