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
