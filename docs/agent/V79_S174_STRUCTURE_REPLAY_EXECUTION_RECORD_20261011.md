# V79 exact-S174 structure replay: execution record (failed closed)

Date: 2026-10-11

Terminal: `EXACT_S174_STRUCTURE_REPLAY_FAILED_CLOSED__OPERATOR_MODEL_LOGISTIC_NONCONVERGENCE__NO_METRICS_COMPUTED__CONTROLLER_REPAIR_DECISION_REQUIRED__BAYESIAN_CONFIRMATION_OFF__TRAINING_OFF`

Lane: synthetic/V79 Bayesian dataset geometry. This is development evidence only. No target discovery, no TEST/Morabito, no pathology, no NUTS, no training.

## Outcome in one paragraph

Step 1 (the authenticated streaming G500 compact cache) succeeded, with every receipt invariant satisfied. Step 2 (the cache-only structure replay) stopped on its first non-converged logistic fit, as the frozen runner is written to do. It wrote no replay JSON and printed no metric. A convergence-only diagnosis, which computes no predictive metric, located every failure in the operator-within-source model: 155 of 600 operator-model fits. The cause is quasi-separation. In many training folds, an operator has zero or all detections for a gene, so its fixed-effect coefficient diverges and only the 1e-4 ridge holds it. Questions A–H are therefore unanswered. The qualified PR #279 code was not changed and the replay was not rerun. A repair choice is needed from the controller before any metric is computed.

## Provenance

| item | value |
|---|---|
| execution commit | `615b55eb03b95630484b18d47de0ef7340368d37` (PR #279 head; code identical to CI-verified `2d5de281…`, 15 passed) |
| executed from | `git archive` snapshot `/d/v79_runs/615b55eb` (`SNAPSHOT_COMMIT.txt` = execution commit) |
| Python / NumPy / SciPy | 3.9.7 / 1.24.2 / 1.10.1 (no JAX, no NUTS) |
| cache root | `D:\Jepa project\data\cache\s174_rebuilt_real_train_v1` (repaired corrected S174; not regenerated) |
| shard authority | `results/v79/V79_S174_SHARD_AUTHORITY_V1.json`, SHA-256 `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288` |
| bridge | `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`, SHA-256 `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92` |
| shard inventory | 84 authority files; 84 present; 0 missing; 0 extra; bridge files = authority files |

## Step 1: G500 compact cache (PASS)

| receipt fact | value |
|---|---|
| schema | `V79_ANALYSIS_CACHE_RECEIPT_V2` |
| `streaming_passes` / `max_count_shards_resident` / `global_sparse_assembly` | 2 / 1 / false |
| `metadata_from_authenticated_bytes` | true |
| shard files verified against the authority | 84 |
| cache | `V79_ANALYSIS_CACHE_G500.npz`, 1,071,307 bytes, SHA-256 `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62` (real counts; kept on the execution machine, not committed) |
| cells / donors | 4,726 (exactly the corrected S174 population) / 149 |
| sources | HVS 3,072 cells from 62 donors; NPH52 246 cells from 19 donors; SEA_AD 1,408 cells from 68 donors |
| design levels | 3 broad classes, 3 sources, 42 operators, 149 donors, 426 donor-class groups |
| gene panel | 500 identity-blind, prevalence-stratified genes from the 14,417-gene universe (prevalence ≥ 5%) |
| panel prevalence | min 0.050, median 0.242, max 0.949; bins [.05,.1) 96, [.1,.2) 113, [.2,.3) 83, [.3,.5) 103, [.5,.7) 63, [.7,.9) 31, [.9,1] 11 |

The build took 3 seconds. No gene symbols, Ensembl IDs or molecular addresses appear in any committed result. Replay outputs refer to genes only by their position in the cache.

## Step 2: cache-only replay (FAILED CLOSED)

Command: the exact recipe command (`--genes 200 --support-genes 50 --permutations 99 --folds 3 --seed 20261011`).

Result: `RuntimeError: logistic fit did not converge: STOP: TOTAL NO. of ITERATIONS REACHED LIMIT` on the first failing detection fit. There is no replay JSON and stdout is empty, so no metric was produced or seen.

### Convergence-only diagnosis (no predictive metric computed)

The diagnosis repeats the frozen `_logistic_fit` call (same design, folds, ridge and L-BFGS-B settings) for every replay gene, model and fold, recording the optimizer status instead of raising. It never computes held-out log loss or LPD.

| model | non-converged fits (of 600) |
|---|---|
| depth linear | 0 |
| quadratic depth | 0 |
| + broad class | 0 |
| + source | 0 |
| + operator-within-source | **155** |

The 155 failures fall on 84 of the 200 genes. In 351 of the 600 operator-model fits, at least one operator level is constant (all detected or none detected) in the training fold for that gene. Failing fits stop at 300 iterations with gradient inf-norm about 0.003–0.016 and maximum |coefficient| about 6–14 on the logit scale. Even the operator fits that converge are, wherever such a level exists, determined by the 1e-4 ridge rather than by the data.

The random-effect support diagnostics also fit the full operator logistic model, so they would hit the same failure.

### What this means

- **A–C (depth, class, source):** these models converge in every fit, but no metric exists, because the runner aborted before writing anything.
- **D (operator):** the operator-within-source fixed proxy is ill-posed for many genes under donor-held-out folds with 42 operators. A held-out comparison of it would mostly measure the ridge strength.
- **E–H:** not reached.

## Repair options, for a controller decision before any metric is computed

1. **Raise the iteration limit only.** *Not recommended.* The fits would converge to the ridge-bounded near-separated solution. Held-out predictions for operators that are constant in training would become extreme, so the operator comparison would reflect the 1e-4 ridge, not the data.
2. **A stronger penalty on the within-source operator contrasts only, fixed now.** *Recommended.* This approximates the constrained hierarchical operator effect the candidate intends for its Bayesian form. For example: a Gaussian prior with SD 1 on the logit scale, which is ridge λ = 1 on those columns, with the same rule applied in the positive-count model. Depth, class and source columns stay as frozen. Convergence is recorded for every fit, and any remaining non-convergence fails closed again. The penalty value is a convention and must be labelled as one.
3. **Record non-convergence and drop failing genes.** *Not recommended.* It removes exactly the genes where operators separate most (mostly low-prevalence genes) and biases the comparison.
4. **Pool rare operators.** *Not recommended.* It changes the model after seeing the failure.

Whichever option is chosen should be implemented on the PR #279 implementation line, test-first, and re-verified before the replay is run again.

## Committed artifacts

`results/v79/development/s174_structure_replay/`:
- `V79_S174_REPLAY_EXECUTION_PROVENANCE.json`: commits, versions, authority and bridge hashes, shard inventory
- `V79_ANALYSIS_CACHE_G500_RECEIPT.json`: cache receipt
- `V79_G500_PANEL_PREVALENCE_COVERAGE.json`: panel prevalence coverage (no identities)
- `build_cache.stdout.txt`, `build_cache.stderr.txt`
- `replay.stdout.txt` (empty), `replay.stderr.txt` (the failure traceback)
- `diagnose_replay_convergence.py`, `V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS.json`: per-fit optimizer status; no predictive metric

## Unchanged

- Detection V2 remains `NOT_QUALIFIED`.
- Gaussian, log-normal and ZTNB remain `UNADJUDICATED__METHODOLOGICAL_HOLD`.
- No NUTS was run; corrected-TRAIN posterior inference is off.
- No parameters were exported.
- `training_authorized=false`.
