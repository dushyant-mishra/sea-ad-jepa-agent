# V79 corrected-S174 streaming structure replay — execution contract

Date: 2026-10-11

Status: `IMPLEMENTED_AND_SYNTHETICALLY_VERIFIED__REAL_S174_EXECUTION_PENDING`

Lane: synthetic/V79 Bayesian dataset geometry only. This is model-development evidence, not target discovery, not confirmatory Bayesian qualification, not H0-H3 execution, and not training authority.

## Why this path exists

The historical V79 real-data runners repeatedly rebuilt the full 4,726 × 41,238 sparse matrix and then selected a small gene panel. That is unnecessary. The authenticated corrected S174 cache itself is only about 49 MB, and the expensive historical recovery fit was CPU-bound rather than data-I/O-bound.

The replacement path has two stages:

1. exactly one bounded two-pass scan of the 42 authenticated count shards plus one authenticated metadata read per shard;
2. all repeated model-development comparisons consume only the compact selected-gene cache.

No global CSR matrix is assembled. At most one count-shard CSR is resident at once. Metadata design arrays are parsed from the exact bytes already authenticated against the S174 authority, rather than reopening the files after verification.

## Frozen implementation

Implementation PR: #279

Key scripts:
- `scripts/v79/build_v79_analysis_cache.py`
- `scripts/v79/run_v79_s174_structure_replay.py`
- `scripts/v79/run_v79_scheduler.py`

Focused CI at code head `2d5de281a171f0510d22a7408780fb069625ea02`:
- workflow run `38166126568`
- job `114548954034`
- `15 passed in 1.27 s`

The tests establish:
- no `scipy.sparse.vstack` in cache construction;
- no use of the historical full-matrix loader during cache verification;
- exactly two count-shard streaming passes;
- maximum one count shard resident;
- selected counts, libraries, detected-feature counts and frozen gene sample equal the historical loader on synthetic shards;
- design arrays from authenticated metadata bytes equal the historical firewall loader;
- tampered shard rejection;
- hash-bound compact-cache replay;
- donor-held-out folds never split a donor;
- prevalence-balanced replay panels;
- full-rank source + operator-within-source fixed proxy;
- residual permutation support diagnostics;
- operator support is tested after donor centering;
- scheduler defaults to one machine-wide heavy fit and a 120-second settle window.

## Exact physical input

Use the already authenticated repaired S174 cache; do not reconstruct S174 rows from the larger 50K corpus.

Cache root:
`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Bridge:
`results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`

Shard authority:
`results/v79/V79_S174_SHARD_AUTHORITY_V1.json`

The repair lineage preserves exactly the historical S174 cells by cell ID and order, while replacing their expression values with corrected physical-source values. A larger-corpus reconstruction is therefore not an equivalent authority.

## Step 1 — build one compact development cache

Run from the PR #279 code snapshot/worktree:

```powershell
python scripts/v79/build_v79_analysis_cache.py `
  "D:\Jepa project\data\cache\s174_rebuilt_real_train_v1" `
  "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json" `
  "results/v79/V79_S174_SHARD_AUTHORITY_V1.json" `
  500 `
  "results/v79/development/s174_structure_replay"
```

Expected outputs:
- `V79_ANALYSIS_CACHE_G500.npz`
- `V79_ANALYSIS_CACHE_G500_RECEIPT.json`

Required receipt facts:
- schema `V79_ANALYSIS_CACHE_RECEIPT_V2`;
- `streaming_passes = 2`;
- `max_count_shards_resident = 1`;
- `global_sparse_assembly = false`;
- `metadata_from_authenticated_bytes = true`;
- all 84 shard files match the committed S174 authority;
- cache NPZ hash recorded.

If any authority, row-count, firewall, or shard-shape check fails, stop. Do not repair in place.

## Step 2 — cheap exact-S174 structure replay

```powershell
python scripts/v79/run_v79_s174_structure_replay.py `
  "results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500.npz" `
  "results/v79/development/s174_structure_replay/V79_ANALYSIS_CACHE_G500_RECEIPT.json" `
  "results/v79/development/s174_structure_replay/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V2.json" `
  --genes 200 `
  --support-genes 50 `
  --permutations 99 `
  --folds 3 `
  --seed 20261011
```

This stage reads no 41K shards. It uses only the hash-bound compact cache and SciPy/NumPy; no JAX and no NUTS.

Nested held-out-donor comparisons:
- depth linear;
- quadratic depth;
- + broad class;
- + source;
- + operator-within-source.

Random-effect support diagnostics on a prevalence-balanced 50-gene subpanel:
- donor after the full fixed structure;
- operator beyond donor, using donor-centered residuals and permutations within donor;
- donor×class increment beyond donor, using donor-centered residuals and permutations within donor.

Positive magnitude uses a stable lognormal development proxy. It does not adjudicate ZTNB; ZTNB remains a challenger for a separately stable implementation.

## Resource policy

This replay is intentionally not a Bayesian fit. It should finish before any NUTS campaign is reopened.

For subsequent heavy Bayesian work:
- one heavy fit at a time by default;
- no simultaneous bootstrap/eigenspectrum job;
- per-gene modular fits rather than one monolithic cross-gene NUTS model;
- GPU is not the default NUTS device without a fresh measured advantage;
- every long fit gets a resource receipt.

Historical measured Gaussian recovery resource evidence:
- peak RSS about 1.32 GB;
- mean process use about 10.3 of 16 logical CPUs;
- whole-machine CPU about 93%;
- wall time about 26 minutes.

Thus the primary heavy-fit bottleneck is sampler CPU, not the S174 expression bytes.

## Controller interpretation

The replay output remains `DEVELOPMENT_ONLY`.

If exact S174 preserves the auxiliary ordering—two-part model, class/source/operator/donor earned, donor×class not broadly earned—then Candidate V2 may be frozen for a **new untouched synthetic confirmatory qualification**.

If S174 contradicts that ordering, return to model development. Do not reinterpret the old V1/V2 synthetic tests as confirmation.

No posterior parameters may be exported to the factorial generator from this replay.
