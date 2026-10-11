# Macha next execution contract — synthetic/V79 lane — 2026-10-11

This is the only authorized next Macha task for the synthetic/V79 Bayesian geometry lane.

## Start state

- source branch at last audit: `analysis/v79-bayesian-synthetic-geometry-20261009`
- source head: `b06bd819abd7da1be0426767c6909f4cdc7cc7bf`
- implementation authority: PR #279
- failed-closed physical execution record: PR #280
- controller repair decision: PR #280 comment `6112948943`
- G500 physical cache SHA-256: `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`

## Task

1. Work on the PR #279 implementation line. Do not modify PR #280's historical failed-closed record.
2. Add RED tests before implementation proving:
   - only operator-within-source columns get the new penalty;
   - source + operator-within-source remains full rank;
   - separated synthetic operator levels converge at primary lambda=1;
   - non-operator nested model outputs are unchanged;
   - the sensitivity set is exactly `{0.25, 1, 4}` and cannot be adapted after outcomes.
3. Implement explicit operator-within-source regularization in both cheap hurdle proxies:
   - primary lambda = `1`;
   - sensitivity lambda = `0.25` and `4`;
   - no stronger penalty on intercept/depth/class/source;
   - no new covariates or hierarchy.
4. Keep first repaired replay optimizer maxiter/convergence rules unchanged.
5. Obtain independent CI GREEN and record run/job/test counts.
6. On the physical execution machine, verify the existing G500 cache SHA/custody. If the SHA is valid, **reuse it**. Do not rebuild it.
7. Rerun the same exact-S174 cache-only replay:
   - 200 prevalence-balanced replay genes;
   - 50 support genes;
   - 3 donor-held-out folds;
   - 99 permutations;
   - seed `20261011`;
   - same metrics and panel rules.
8. Every primary lambda=1 fit must converge. If any primary fit still fails, fail closed and stop. No maxiter increase, no gene dropping, no operator pooling, no post-hoc penalty change.
9. Report lambda=0.25 and lambda=4 sensitivity results even if they disagree with the primary result. Sensitivity failures must be recorded.
10. Operator question D is `SUPPORTED` only if held-out-donor operator increment has the same direction and remains materially present across all three penalties. Otherwise report `PRIOR_SENSITIVE__UNRESOLVED`.
11. Operator residual support must use donor-centered residuals and within-donor permutation, at primary and both sensitivities.
12. Keep donor and donor×class adjudications separate from operator regularization.
13. Positive family H is development-only: lognormal may be judged stable/unstable, but ZTNB cannot be declared inferior by this replay.
14. Commit machine-readable results, per-gene deltas, convergence table, sensitivity results, exact environment/provenance, and updated active state.
15. Stop for controller review. Do not launch NUTS or any follow-on qualification automatically.

## Required A-H output

A. quadratic vs linear depth
B. broad class increment
C. source increment
D. penalty-robust operator-within-source increment
E. donor residual support
F. penalty-robust donor-controlled operator residual support
G. donor×class increment beyond donor
H. positive-lognormal stability

## Forbidden

- old 18-fit Gaussian/lognormal/ZTNB restart
- Bernoulli V2/V3 resurrection
- corrected-TRAIN Bayesian posterior authority fit
- H0/H1/H2/H3/C_OBS/C_BIO scientific execution
- TEST/Morabito/pathology
- target discovery under this instruction set
- V78 outcome retuning
- Stage4/500K
- JEPA training/checkpoints

Expected successful terminal:
`EXACT_S174_STRUCTURE_REPLAY_COMPLETE__PRIMARY_OPERATOR_LAMBDA_1__FROZEN_SENSITIVITY_0p25_1_4__DEVELOPMENT_ONLY__CONTROLLER_MODEL_FREEZE_REQUIRED__BAYESIAN_CONFIRMATION_OFF__TRAINING_OFF`

Expected terminal if primary repaired fit still fails:
`EXACT_S174_STRUCTURE_REPLAY_FAILED_CLOSED__REGULARIZED_OPERATOR_MODEL_NONCONVERGENCE__NO_POST_HOC_RESCUE__CONTROLLER_REVIEW_REQUIRED__TRAINING_OFF`
