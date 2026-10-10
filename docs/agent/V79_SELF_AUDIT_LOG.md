# V79 Bayesian synthetic-geometry lane: self-audit log

Updated at every checkpoint. Each entry records what went wrong, what it cost, the fix, and the rule
adopted so it does not recur. Failures stay recorded; nothing is rewritten after the fact.

## 2026-10-09: setup and model qualification

| # | what happened | cost | fix | rule adopted |
|---|---|---|---|---|
| 1 | Chose Pyro (already installed) and launched multi-minute NUTS runs without a short timing probe | about 40 min; no 10-gene run finished within about 27 min | Ported to NumPyro/JAX in a new separate env `v79-bayes` | Smoke test at tiny size, then a timing probe of 2 minutes or less at target size, then extrapolate and set a budget before any long run |
| 2 | Ran the Pyro and NumPyro benchmarks at the same time | both slowed; timings unusable | Stopped the abandoned Pyro process (by verified command line) | One heavy job at a time; check running processes before launching |
| 3 | Defaulted to non-centred random effects without checking per-group information | deep NUTS trees; NumPyro run did not finish in about 30 min | Centred effects; centring is a sampler setting chosen on simulations only | Before choosing a parameterization, check cells per level against effect and residual variance |
| 4 | Assumed `LocScaleReparam(centered=None)` learns centring under NUTS (it is a `numpyro.param`, learned only by SVI); the config also matched its own `_decentered` helper sites and recursed | one failed run | Explicit centring; config skips `_decentered` sites | Verify library behaviour in isolation before relying on it |
| 5 | Residual hyperparameters sampled inside the cell-level plate | caught by the smoke test | Moved outside | Keep smoke tests before benchmarks |
| 6 | Extrapolated a 1,000-iteration run from a 150-iteration probe; NumPyro's later warm-up windows shrink the step size and deepen trees, so the extrapolation was off by more than 10x | two overrunning probes | Warm-up traces now record steps and step size per iteration; every run has a hard `timeout` | Probe with the same warm-up schedule shape or trace adaptation live; never extrapolate from a different schedule |
| 7 | Gathered effects by index (`a[idx]`); on CPU the gradient is a single-threaded scatter-add | gradient 3.98 ms vs potential 0.43 ms (9x) | One-hot / projection matrix products | Time potential and gradient separately before any NUTS run |
| 8 | Sampled class/source as K free values minus their mean, leaving a direction only the prior informs; then tried centring random effects by subtracting group means, which creates the same kind of direction | saturated trees (about 1,000 steps) | K-1 orthonormal contrasts for class and source; random effects on block-orthonormal within-parent bases (operator and donor within source, donor-class within class) | Never constrain a parameter by subtracting its own mean; parameterize on an orthonormal basis of the constrained space |
| 10 | Made per-gene log sds non-centred on the reasoning that few genes inform the population; each gene's sd is pinned by its own data (149 donors, 426 donor-classes, 42 operators), so the non-centred form built a funnel. The same lesson as #3, not applied one level up | most of the remaining slowness | Centred per-gene log sds: after adaptation, step size 0.09-0.10 and 55-65 steps per iteration (from 0.02 and about 300) | Judge centring by how much data informs each parameter, at every level of the hierarchy |
| 11 | Expected the GPU to rescue a step-bound sampler; a 4-gene, 2-chain, 100-iteration GPU run took 580 s; the smoke test also lacked progress output | about 25 min | GPU kept for large gene counts, where each step carries real work | Fix step counts first; a faster device does not fix geometry; stream progress in every smoke test |
| 12 | JAX timing measured before the asynchronous work finished (reported 17 s for a run of about 40 min); post-processing expanded every draw to every cell (about 1.5 GB per component) | wrong timing; long post-processing | `block_until_ready` before every clock read; realized variances from level counts | Block before timing; never materialize draws x cells x genes |
| 13 | Simulation truth scored on the planted parameterization, not the model's (operator and donor source-means belong to source under the model) | spurious under-coverage (source 0.4) | Truth re-expressed on the model's decomposition, with a test that the predictor is unchanged | Score recovery on exactly the estimand the model reports |
| 14 | Edited the model code while a delegated agent was benchmarking it; the agent caught it and labelled which code each timing used | some timings on superseded code | Benchmark agents get a frozen copy or a commit to measure, never a live worktree | Freeze what an agent measures before delegating; no edits under a running agent |
| 15 | GPU route (WSL JAX-CUDA): intermittent hangs with the default allocator (3/3 runs); stable only with synchronous allocation, which is slower than CPU (potential + gradient about 11-15 ms vs 4.1 ms) | about 2 h of agent time | CPU chosen for this design size; GPU recorded as not usable as configured | Ask "is the device the bottleneck?" before building an environment for it |
| 9 | User asked for parallel work; lanes had been run one after another | slow progress | TD G4/G5 execution, the Bayesian-bootstrap geometry module and the GPU environment were delegated to background agents, each in its own worktree or with new files only | Independent work goes to parallel agents with disjoint files; the coordinator keeps the critical path |

Probe evidence after the fixes (simulated data on the real design, 10 genes, 4 chains x 150 iterations):
Gaussian, centred: 19 s, 0 divergences, 511 mean steps. Bernoulli: centred 159 steps against 415
non-centred, about 12 s each, 0 divergences.

## Carried over from earlier lanes (same session)

- A background launch put variable assignments inside a `&&` chain that was itself backgrounded, so later
  commands saw empty paths. Rule: define variables at top level and validate a launch command on one job first.
- Full-drive file scans timed out repeatedly. Rule: search by exact name or size predicate first; widen only
  if that finds nothing.
- Hard-coded readings in a re-score claimed facts the numbers did not support. Rule: derive every reading
  from computed values.

Warm-up trace after fixes 7-8 (simulated data, 10 genes, 1 chain, 150 warm-up iterations, 251 s on a shared
CPU): step size grew from 0.003 to 0.02 and steps per iteration fell from about 590 to about 300 as the mass
matrix adapted; adaptation was not complete. Extrapolated cost on CPU: about 20-30 min per 10-gene fit, hours at
60 genes. A JAX-CUDA environment in WSL is being built and benchmarked in parallel.

## 2026-10-10: geometry module (D1) and observations

- The Bayesian-bootstrap geometry module (written by a delegated agent, re-run and verified by the coordinator
  before commit) reproduces every corrected reference statistic with uniform weights: graph statistics bit-exact,
  continuous statistics within 4e-15 relative, abundance within 2.1e-14 (required 1e-9). 17 tests pass in both
  environments locally; the real-data test skips in CI because the cache bytes are local-only.
- Two library definitions are in use and both are kept, labelled: the reference builders' CP10K denominator is
  the sum over the 41,238 cached addresses; the model depth covariate uses `source_library` (at least the cached
  sum; ratio minimum 0.961; log correlation 1.0000).
- One of the 3,000 HVGs is detected in every TRAIN cell, so the reference detection layer gives it zero
  correlations by the builder's convention; kept as is for comparability.
- One draw takes about 24 s on a contended CPU (dense trace(A^3) five times per draw, full eigendecompositions);
  to be optimized with exactness preserved before 1,000 draws.
- `timeout` from Git Bash on a native Windows process: verify it fires (check process start time) rather than
  assuming.

## 2026-10-10: detection qualification, Phase C and validation code

| # | what happened | cost | fix | rule adopted |
|---|---|---|---|---|
| 16 | Detection qualification at contract settings failed on the donor-class hyperparameters (m_dk R-hat 1.08, ESS 31; s_dk R-hat 1.19, ESS 15; 1,465 s, 0 divergences, 80 steps): a donor-class level has about 11 binary cells, too few to pin a centred logit effect | one 25-minute fit | Donor-class effects non-centred for detection only (`CENTRING`), chosen on simulation. Requalification: worst R-hat 1.0049, worst ESS 438, 39 steps, 853 s, but 3 divergences in one chain, so the contract's retry rule applies; requalified at target_accept 0.95 | Choose centring per component and likelihood from the information per level; requalify at contract settings after every sampler change |
| 17 | The recovery runner did not apply the contract's retry rule, so one divergence would have failed a fit the rule retries | found before the suite ran | Retry rule in the recovery, held-out PPC and Phase C runners | Every fitting runner applies the same diagnostics and retry rule |
| 18 | The contract text still said per-gene log sds are non-centred, while the code centred them since entry 10 | found by rereading the contract against the code before real inference | Amendment A1, before any real data; previous contract hash recorded | Reread the contract against the code at every gate |
| 19 | Phase C's frozen family rule compares a density on log count with a probability on count; the raw log densities are on different measures | found while implementing | Both families scored on the count scale (amendment A2); a test checks the rule picks the generating family in both directions | Before applying a model-comparison rule, check the scores are on the same measure |
| 20 | The delegated PPC agent stopped on the session rate limit mid-task | none; its 428-line module and 9 tests were complete and passing | Coordinator reviewed and extended it (positive-count families, signed dependence, eigenspectrum, quantiles, held-out lpd, per-fold runs) | Check a stopped agent's partial output before redoing it |
| 21 | `grep -c $''` in this Git Bash counted every line, a false CRLF alarm | a few minutes | Bytes checked with Python; the contract test already does this | Check line endings on bytes, not with shell escapes |

Simulation choices for the zero-truncated NB (sampler and recovery only, never tuned on real data): log mean
count at average depth N(-0.5, 1.5) (about 0.03 to 12 counts, detection about 3% to 90%), log dispersion
N(log 2, 0.3). Gaussian and Bernoulli simulated worlds were checked byte-identical before and after the change.
