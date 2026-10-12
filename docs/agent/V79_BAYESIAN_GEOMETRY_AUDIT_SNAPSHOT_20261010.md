# V79 Bayesian Geometry Audit Snapshot — 2026-10-10

This branch is an audit-only snapshot of Macha's independent Bayesian dataset-geometry lane.

## Exact live lineage

- Source branch: `analysis/v79-bayesian-synthetic-geometry-20261009`
- Audited source head: `ba61ed4cfca6747e32c21aeabbeed6453e5ea31e`
- Audit branch: `audit/v79-bayesian-geometry-snapshot-20261010`
- This lane is NOT PR #249. PR #249 is the older target-discovery Bayesian spike.
- This lane is NOT PR #253/#256/#257. Those belong to the separate factorial synthetic-world lane.

## Scope

This lane estimates TRAIN-only dataset geometry for later identity-scrubbed synthetic-world design. It separates broad class, source/operator, donor, donor×class and residual geometry, with distinct detection and positive-count/expression models. It is observational and non-promoting.

## Committed implementation already present on source branch

The source branch contains the V79 Bayesian code, tests, reports, recovery tooling, held-out PPC tooling, benchmark/custody runners, queue builders and the self-audit log under the existing `scripts/v79`, `tests/v79`, `docs/agent`, and `results/v79` paths. This audit branch inherits every committed byte from `ba61ed4c` before adding this snapshot.

Notable committed surfaces include:

- `scripts/v79/build_v79_synthetic_artifact.py`
- `scripts/v79/launch_v79_recovery.sh`
- `scripts/v79/make_v79_real_queue.py`
- `scripts/v79/report_v79.py`
- `scripts/v79/run_v79_bayesboot.py`
- `scripts/v79/run_v79_benchmark.py`
- `scripts/v79/run_v79_custody.py`
- `scripts/v79/run_v79_inference.py`
- `scripts/v79/run_v79_phase_c.py`
- `scripts/v79/run_v79_ppc_heldout.py`
- `scripts/v79/run_v79_qualification.py`
- `scripts/v79/run_v79_recovery.py`
- `scripts/v79/snapshot_v79.sh`
- `scripts/v79/v79_models.py`
- `scripts/v79/v79_phase_c.py`
- `docs/agent/V79_SELF_AUDIT_LOG.md`

## Verified/committed technical milestones at audited head

1. Held-out PPC end-to-end test passed in the Bayesian environment. It showed high posterior-predictive coverage when correctly specified and loss of donor-spread coverage when donor effects were deliberately omitted. This is local execution evidence; base CI skips NumPyro-dependent execution.
2. Detection-model non-centring of donor×class repaired a severe convergence failure from R-hat ~1.19 / ESS ~15 to acceptable convergence in qualification, but simulation recovery still exposed a marginal S0 failure under the then-current setting.
3. Detection recovery at the last committed state:
   - S1 present: PASS convergence, worst R-hat 1.0087, worst ESS 539, zero divergences; planted-component coverage 17–19/20.
   - S0 class absent: FAIL convergence, worst R-hat 1.0194, worst ESS 205, zero divergences.
   - Old S2/S3 jobs using the superseded setting were stopped; logs were preserved under `results/v79/recovery/stopped_ncdk_only_20261010/`.
4. Gaussian recovery had previously exposed donor×class spread non-convergence and was rerunning with that component non-centred.
5. Phase C log-normal qualification narrowly failed donor-spread convergence (reported R-hat 1.013 vs 1.01 contract limit), motivating a donor non-centring experiment.
6. The zero-truncated NB count-model qualification hit its 2.5-hour cap without final output. The branch then added progress streaming and a cheaper mathematically equivalent likelihood omitting only the data-only `-lgamma(y+1)` constant.
7. A new density test found an extreme-value float32 overflow in both the textbook/reference form and the initial optimized form. The committed implementation rewrites the NB terms with softplus and passes the equivalence/finite-value test.
8. Commit history relevant to this freeze:
   - `5972ec10d1f60851c4310624d817e0626e5619e7`: stable softplus truncated-NB likelihood, progress streaming, self-audit 31–33.
   - `8e63acc24a7a2bcbb5cf905bc40ec7a33ffad522`: recovery runner accepts recorded centring override for sampler experiments.
   - `ba61ed4cfca6747e32c21aeabbeed6453e5ea31e`: self-audit entry 34; detection centring remains borderline and V1 experiment launched.

## Last reported external-running state — NOT a committed terminal result

The user-supplied execution snapshot reported, after source head `ba61ed4c` was pushed:

- count-model qualification Q9 relaunched from snapshot `5972ec10` with progress streaming and donor + donor×class non-centring;
- detection candidate V1 launched on S0 and S1 from snapshot `8e63acc2`;
- Gaussian recovery fits still running;
- Phase C log-normal donor reparameterization experiment still pending/running.

These jobs execute on a separate Windows worktree/CPU environment. Their current completion state is NOT observable from GitHub and therefore is not promoted into this audit as a result. Any successor must inspect the remote run outputs before adopting them.

## Real-data gate state at audited head

No real expression-value inference had started in the supplied snapshot. Real-data phases A/B/B0/C/D1, held-out real-data PPC, bootstrap, and scrubbed Output B remained gated on successful simulation recovery plus the compute benchmark.

The lane may eventually emit a qualified identity-scrubbed geometry artifact for prospective synthetic-world design. Intermediate sampler experiments, failed recovery outputs, and provisional parameterizations are not generator authority.

## Firewalls / non-authorities

- TEST/Morabito: not accessed by this lane.
- Pathology: prohibited.
- Target-discovery rankings/panels/SCENIC+/ATAC evidence: not consumed.
- PR #259 target-discovery preflight is a separate lane.
- PR #253/#256/#257 factorial synthetic-world implementation is a separate lane.
- V78 remains frozen.
- No JEPA training/checkpoint generation is authorized.
- No intermediate Macha output may retroactively retune an already-executed synthetic arm.

## Next lawful sequence

1. Inspect the externally running V1 detection, Gaussian, log-normal and ZTNB jobs and preserve their exact snapshot/code hashes.
2. Select per-likelihood sampler parameterization only from the prospectively recorded simulation experiments.
3. Rerun complete detection / Gaussian / Phase C recovery suites under the selected settings.
4. Require every contract convergence/recovery criterion to pass; otherwise remain blocked and redesign prospectively.
5. Run the benchmark to freeze gene count/folds.
6. Only then permit real corrected-TRAIN Bayesian fits.
7. Audit the final identity-scrubbed artifact before any synthetic generator may consume it.

This snapshot is custody/history only. It does not claim the Bayesian lane is qualified or complete.