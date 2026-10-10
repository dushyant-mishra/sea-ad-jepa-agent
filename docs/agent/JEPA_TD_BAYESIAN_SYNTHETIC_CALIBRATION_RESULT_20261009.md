# JEPA TD Bayesian spike — synthetic calibration result

Date: 2026-10-09

Terminal: `SAMPLER_NOT_ESTIMABLE`

Method-spike disposition:

`STOP_THIS_BAYESIAN_FORMULATION__DO_NOT_TUNE_TO_HISTORICAL_OUTCOMES`

Parent freezes:
- `docs/agent/JEPA_TARGET_DISCOVERY_BAYESIAN_SPIKE_PREREG_20261009.md`
- `docs/agent/JEPA_TARGET_DISCOVERY_BAYESIAN_LEDGER_DESIGN_20261009.md`
- `docs/agent/JEPA_TD_BAYESIAN_SYNTHETIC_CALIBRATION_FREEZE_20261009.md`

No historical TD57B/TD57C/TD59 value or PASS/FAIL label was used to tune this calibration. No corrected replay was ingested. No historical Bayesian fit was run.

Hard project authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Execution

The prospectively frozen seven-block synthetic geometry, Student-t hierarchy, three prior regimes, four fixed chain seeds, chain lengths, burn-in, thinning, acceptance thresholds, Rhat threshold, ESS threshold and scientific acceptance criteria were executed without post-outcome tuning.

Focused deterministic function assertions passed for:
- frozen scenario arrays;
- exact zero-sum source-effect parameterization;
- null sign symmetry of the log posterior;
- seeded sampler determinism;
- diagnostics on independent synthetic chains;
- frozen scientific-criteria logic.

The repository has no registered GitHub Actions workflow, so this is an execution receipt from the current agent environment, not a GitHub-CI claim.

## 2. Sampler-quality result

The frozen quality floor required:
- every chain acceptance in `[0.10, 0.70]`;
- maximum split-Rhat <= `1.10`;
- minimum stage-effect ESS >= `200`.

Those requirements were not met.

| Prior | Scenario | chain acceptance range | max split-Rhat | min stage-effect ESS |
|---|---|---:|---:|---:|
| skeptical | S0 null | 0.2575–0.5129 | 1.7640 | 109.6 |
| skeptical | S1 one-source | 0.1574–0.5598 | 1.2864 | 175.9 |
| skeptical | S3 sign-flip | 0.2783–0.5496 | 1.2410 | 165.2 |
| skeptical | S4 shared-positive | 0.1660–0.5294 | 2.1121 | 66.3 |
| reference | S0 null | 0.4439–0.7149 | 1.5516 | 82.1 |
| reference | S1 one-source | 0.4728–0.7150 | 1.1996 | 146.7 |
| reference | S3 sign-flip | 0.3888–0.6035 | 1.4768 | 114.2 |
| reference | S4 shared-positive | 0.5215–0.6298 | 2.6249 | 56.1 |
| diffuse | S0 null | 0.3229–0.6543 | 1.6413 | 84.4 |
| diffuse | S1 one-source | 0.4081–0.4874 | 1.2414 | 112.5 |
| diffuse | S3 sign-flip | 0.3214–0.5749 | 1.1108 | 191.7 |
| diffuse | S4 shared-positive | 0.3901–0.6140 | 1.8873 | 97.5 |

Because the preregistered sampler-quality floor fails, the controlling calibration terminal is:

`SAMPLER_NOT_ESTIMABLE`

No scientific posterior from these runs is authoritative.

## 3. Scientific criteria — diagnostic only because sampler quality failed

For transparency, the frozen criteria evaluated on the sampled draws were:

| Criterion | skeptical | reference | diffuse |
|---|---:|---:|---:|
| C0 null calibration | PASS | PASS | PASS |
| C1 one-source-only resistance | FAIL | FAIL | FAIL |
| C2 duplicate resistance | PASS | PASS | PASS |
| C3 sign-flip heterogeneity | FAIL | FAIL | FAIL |
| C4 shared-positive recovery | FAIL | PASS | PASS |

Thus the method has problems beyond chain convergence:

1. **One-source-only resistance fails under every prior.** The latent stage mean becomes strongly positive when only HVS carries the large signal. Under the reference prior, for example, `P(mu_A>0)=0.9923` and `P(mu_C>0)=0.9975`, violating the frozen `<0.90` requirement, even though new-source predictive probabilities are more cautious (~0.709 and ~0.694).
2. **Sign-flip heterogeneity fails under every prior.** In the reference run, `P(mu_A>0)=0.9980` and `P(mu_C>0)=0.9983`; their 90% intervals exclude zero, despite new-source predictive probabilities around 0.64 and 0.62. The model's stage-mean estimand and the preregistered notion of source-general replication are therefore not aligned.
3. **Shared-positive recovery is prior-sensitive.** Skeptical-prior new-source predictive probabilities for A/C were ~0.763/~0.798, below the frozen `>0.85` criterion, while reference/diffuse passed. If sampler quality had not already failed, this disagreement would independently invoke `PRIOR_SENSITIVE`.
4. **Duplicate resistance passes at the ledger layer.** Exact duplicate case identities are rejected before fitting, as required.

These observations are diagnostic descriptions of a failed calibration, not scientific claims about the historical TD stages.

## 4. Interpretation

The initial hierarchical formulation is unsuitable for the preregistered replication question in its current form.

The key conceptual mismatch exposed by the synthetic controls is that a zero-sum source-effect model can give a strongly positive latent stage mean when only one source is strongly positive or when source signs conflict. A positive average source effect is not the same object as robust recurrence across sources. The posterior predictive distribution for a genuinely new source behaves more skeptically, but the preregistered spike required both latent-stage and predictive behavior to distinguish source-specific/heterogeneous evidence from recurrent evidence.

This result is exactly what the synthetic calibration firewall was intended to detect before the historical labels or corrected replay could influence model design.

## 5. Required stop

Per the original preregistration:

- do **not** lengthen chains, change proposal scales, change priors, alter thresholds, change the latent estimand, or revise the synthetic scenarios to obtain a PASS inside this spike;
- do **not** run a historical TD57B/TD57C/TD59 Bayesian fit with this formulation;
- do **not** use historical verdicts to redesign it;
- do **not** ingest corrected G4–G7 replay into it;
- do **not** create a target ranking or rescue/relabel TD57C.

The exact historical TD57C extractor and dependency ledger remain useful custody/method artifacts, but they do not authorize continuation of this failed Bayesian formulation.

A future Bayesian or replication method would require a **new prospective question and new preregistration**, clearly separated from this failed spike. It must define source-general recurrence in a way that is identifiable with the sparse TD57C HVS-only geometry and must be calibrated before historical fitting.
