# V79 Bayesian geometry controller handoff — empirical model development + resource-safe S174 replay

Date: 2026-10-11

This handoff controls only the synthetic/V79 Bayesian dataset-geometry lane. Target discovery is separate.

## Current ruling

The old plan to immediately complete Gaussian/log-normal/ZTNB S0-S5 confirmation is superseded by the methodological hold.

- Bernoulli/detection V2 remains terminally `NOT_QUALIFIED` under its frozen confirmatory contract (S4 worst ESS 361.876 < 400; R-hat 1.00506; 0 final divergences).
- This failure applies to that specific hierarchical Bernoulli parameterization. Empirical development subsequently showed that a separate detection process itself is useful.
- Gaussian/log-normal/ZTNB under the old monolithic hierarchy remain `UNADJUDICATED__METHODOLOGICAL_HOLD`.
- The old 18-fit campaign stays stopped.
- No Bayesian posterior inference is currently authorized.

Macha source branch is still held at `b06bd819abd7da1be0426767c6909f4cdc7cc7bf`.

## Auxiliary empirical development result

The authenticated auxiliary fit population supported a simpler two-part model:

Detection:
`detected ~ Bernoulli(logit^-1(intercept + quadratic(log_library) + broad_class + source + operator + donor))`

Positive magnitude development default:
`log(count) | count>0 ~ Normal(intercept + quadratic(log_library) + broad_class + source + operator + donor, sigma)`

Development principles:
- broad class + source are retained;
- operator-within-source is retained as a candidate measurement component;
- donor-within-source is retained as a biological population component;
- donor×class is **not** a default layer;
- genes are fit modularly rather than through the previous monolithic cross-gene hyper-SD hierarchy;
- across-gene geometry is estimated second-stage;
- lognormal is the stable positive-count development default;
- ZTNB is a challenger, not rejected.

Canonical auxiliary records:
- `docs/agent/V79_BAYESIAN_MODEL_DEVELOPMENT_V2_CANDIDATE_20261011.md`
- `results/v79/development/V79_BAYESIAN_MODEL_DEVELOPMENT_V2_EVIDENCE_COMPACT.json`

### Important self-audit correction

The earlier auxiliary residual-support count for operator used a weaker source-stratified permutation and could still carry donor composition. It is therefore **provisional**.

The exact S174 replay now tests operator beyond donor correctly: residuals are centered within donor and the null permutes within donor. This correction was frozen before viewing S174 results.

Held-out-donor predictive gains for operator in the auxiliary tournament remain valid development evidence, but the random-effect support claim must be adjudicated by the corrected S174 replay.

## Resource audit and repair

The historical real-data path repeatedly rebuilt the full 4,726 × 41,238 CSR matrix even though each model used a small gene panel. PR #279 replaces that path for model development.

Implementation PR: **#279**, branch `fix/v79-streaming-analysis-cache-20261011`.

Code head independently tested: `2d5de281a171f0510d22a7408780fb069625ea02`.

Focused GitHub Actions:
- run `38166126568`
- job `114548954034`
- **15 passed in 1.27 s**

The latest PR #279 head adds only execution documentation after that green code head.

The compact-cache builder now:
1. authenticates one count + metadata shard pair at a time;
2. derives metadata design from the exact authenticated bytes already in memory;
3. pass 1 computes prevalence, cached library and detected-feature count;
4. selects the frozen identity-blind gene panel;
5. pass 2 reopens one count shard at a time and copies only selected columns;
6. never globally `vstack`s the 41K matrix.

Receipt invariants:
- `streaming_passes=2`;
- `max_count_shards_resident=1`;
- `global_sparse_assembly=false`;
- `metadata_from_authenticated_bytes=true`.

The replay then consumes only that hash-bound compact cache. It uses NumPy/SciPy, not JAX/NUTS.

The operator predictive proxy is reference-coded within source so source + operator is full rank. The support diagnostics use:
- donor after full fixed structure;
- operator beyond donor: donor-centered residuals, permutation within donor;
- donor×class beyond donor: donor-centered residuals, permutation within donor.

## Why this matters for the laptop

The authenticated S174 cache is only about 49 MB. The large expression matrix is not the real heavy-fit bottleneck.

A measured historical Gaussian recovery fit used:
- peak RSS ~1.32 GB;
- ~10.3 of 16 logical CPUs on average;
- ~93% whole-machine CPU;
- ~26 minutes wall time.

Therefore:
- streaming removes unnecessary disk/RAM churn;
- the heavy Bayesian bottleneck is sampler CPU;
- scheduler default is now one machine-wide heavy fit with a 120-second settle window;
- future Bayesian qualification should use modular per-gene fits rather than monolithic cross-gene NUTS where scientifically possible;
- GPU is not assumed better for NUTS without a fresh benchmark.

## Sole next gate: physical exact-S174 structure replay

Do **not** reconstruct S174 from the larger 50K archive. The S174 repair deliberately preserves exactly the historical 4,726 cell IDs in their historical order and replaces only their expression values from corrected physical sources.

Physical input on the local machine:
- cache root: `D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`
- bridge: `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`
- authority: `results/v79/V79_S174_SHARD_AUTHORITY_V1.json`

Using PR #279 code, build one 500-gene compact cache, then run:
- 200 identity-blind prevalence-balanced replay genes;
- 3 held-out-donor folds;
- 50 identity-blind support genes;
- 99 frozen permutations.

Full command contract is on PR #279 at:
`docs/agent/V79_S174_STREAMING_STRUCTURE_REPLAY_EXECUTION_20261011.md`.

This is **development-only** evidence. No posterior parameter export is allowed.

## Post-replay decision

If exact S174 preserves the structural conclusions—two-part observation model; broad class/source; operator and donor supported; donor×class not broadly earned—then freeze Candidate V2 and generate **new untouched synthetic qualification worlds**.

If exact S174 contradicts the auxiliary development result, return to model development. Do not force the candidate through and do not reuse the old synthetic campaign as confirmatory authority.

Current terminal:
`DEVELOPMENT_CANDIDATE_V2__RESOURCE_SAFE_EXACT_S174_STRUCTURE_REPLAY_READY__PHYSICAL_S174_REPLAY_PENDING__OLD_CONFIRMATORY_CAMPAIGN_ON_HOLD__TRAINING_OFF`

Hard firewalls remain: no H0-H3 factorial outcomes, no TEST/Morabito/pathology, no target-discovery work in this lane, no V78 outcome-driven retuning, no Stage4 and no JEPA training.
