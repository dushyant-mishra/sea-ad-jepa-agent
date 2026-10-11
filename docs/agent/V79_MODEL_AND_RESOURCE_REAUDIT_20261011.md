# V79 model + resource re-audit — 2026-10-11

## Scope

Synthetic/V79 Bayesian geometry lane only. Target discovery is out of scope.

This audit re-examines the auxiliary model-development tournament and the current corrected-S174 loading/execution path, with special attention to scientific overclaim and local CPU/RAM/GPU pressure.

## Scientific ruling on Candidate V2

The current auxiliary evidence supports Candidate V2 as a **development candidate**, not a qualified model.

Supported directionally on the authenticated auxiliary 50K fit population:
- two-part detection + positive-magnitude architecture;
- broad class fixed structure;
- source fixed structure;
- operator structure;
- donor structure;
- nonlinear depth dependence;
- donor×class not earned as a default layer;
- modular per-gene fits preferred over the previous monolithic cross-gene hyper-sd hierarchy.

The compact evidence records strong held-out-donor gains for an explicit detection component and strong support for class/source/operator structure, plus donor/operator residual organization and weak donor×class increment.

### Remaining scientific audit gaps

1. **Population mismatch.** The tournament used the auxiliary 50K reader-fit population (10,379 balanced cells / 104 fit donors), not the exact corrected S174 TRAIN population (4,726 cells / 149 donors). Structural conclusions must be replayed on S174 before a confirmatory freeze.
2. **Executable provenance gap.** Compact result JSON/CSV and narrative candidate records are committed, but the exact executable tournament script that produced the auxiliary nested comparisons is not committed alongside them. Reproducibility is therefore incomplete.
3. **Count replay validation too narrow.** The record proves round-trip count reconstruction on 200 checked rows. Before using reconstructed counts as development authority, validate every cell×gene value used by the tournament panel, not a sample.
4. **Random-effect candidate not yet directly CV-qualified.** Donor/operator support is established by residual/permutation evidence, and naive fixed-effect recovery shows donor/operator leakage. The proposed constrained source-nested random-effect candidate is scientifically reasonable but has not yet been directly compared by held-out-donor predictive score against simpler nested alternatives on S174.
5. **Positive family remains unresolved.** Lognormal is the stable development default. ZTNB is not rejected; its local stress-test implementation was unstable and therefore cannot be used as family-ranking evidence.

Therefore the current terminal remains:

`DEVELOPMENT_CANDIDATE_V2__EXACT_S174_REPLAY_PENDING__NO_CONFIRMATORY_AUTHORITY__TRAINING_OFF`

## Current data-loading/resource defects

### Existing full loader

`scripts/v79/v79_data.py::load_counts()`:
- opens all 42 count shards;
- constructs one CSR matrix per shard;
- stores all shard matrices in a Python list;
- performs a global `sparse.vstack` into a 4,726 × 41,238 CSR matrix.

Each inference process repeats this load.

### Existing real inference

`run_v79_inference.py` loads the full matrix before selecting the small frozen gene panel. Phase A computes row sums, Phase B selects/densifies sampled genes, B0 computes detected-feature counts. Separate phase processes repeat the same full load.

`run_v79_phase_c.py` also reloads/vstacks the complete matrix independently, then densifies only the selected panel. Every fold process can therefore repeat the same full-shard reconstruction.

### Existing compact-cache builder is not actually streaming-safe

`build_v79_analysis_cache.py` is directionally correct but currently:
- appends every shard CSR into `blocks`;
- performs a global `sparse.vstack`;
- computes selected columns only after the global matrix exists;
- then calls `verify_against_loader()`, which reloads and vstacks the full matrix a second time.

So its real-data path performs two full-matrix constructions and defeats the stated bounded-memory purpose.

## Measured compute bottleneck

The first genuine single-fit resource receipt (`RESOURCES_gaussian_S1_alone.json`) measured:
- wall: 1,561.5 s (~26 min);
- peak RSS: 1.32 GB;
- mean process CPU: 10.28 logical CPUs;
- mean whole-machine CPU: 93.1%;
- minimum free RAM: 9.98 GB;
- disk read: only 21.9 MB during the monitored fit.

Interpretation: once a fit begins, **NUTS CPU saturation is the main pressure**, not matrix I/O or RAM. Data streaming is still valuable because it prevents repeated setup churn, but it will not by itself make the Bayesian sampler cheap.

## Required streaming redesign

### A. Two-pass bounded shard stream; never global-vstack

Pass 1, one shard at a time:
- authenticate count/meta bytes against S174 authority;
- reconstruct only that shard CSR;
- update global per-address detection counts;
- compute each cell's cached-address library size;
- compute each cell's detected-feature count;
- append compact design rows;
- release the shard before opening the next.

After pass 1:
- derive prevalence once;
- derive the frozen identity-blind gene panel once.

Pass 2, one shard at a time:
- authenticate/open shard;
- select only the frozen gene columns;
- write directly into a preallocated compact array or chunked on-disk store;
- release shard immediately.

No `blocks` list. No global CSR. No `sparse.vstack`.

### B. Compact authenticated analysis cache

The output should contain only what subsequent development/fitting needs:
- selected raw counts: shape `n_cells × n_selected_genes`;
- selected gene address indices;
- full-universe prevalence vector or its authenticated summary/hash;
- cached-address library size;
- source library;
- detected-feature count;
- broad-class/source/operator/donor integer codes;
- row/stable ordering identity;
- exact shard-authority hash, bridge hash, sampler seed, selected-panel hash, builder-code hash.

For Candidate V2, `donor×class` codes need not be carried into the default fit cache unless retained for sensitivity analysis.

### C. Memory map / chunk instead of compressed monolithic NPZ for repeated fitting

A compressed `.npz` is compact on disk but must inflate arrays when loaded. Prefer either:
- `.npy` arrays loaded with `mmap_mode='r'`, or
- Zarr/HDF5-like chunked arrays if the local environment already supports them.

For only ~4,726 cells × tens/hundreds of selected genes, memory-mapped `.npy` is sufficient and adds fewer dependencies.

Recommended layout:
- `counts_selected.npy` (`uint32` or smallest verified safe integer dtype);
- `library_cached.npy`;
- `source_library.npy`;
- `n_detected.npy`;
- design code arrays;
- one small JSON receipt.

### D. Prevalence computed once

The current historical path can compute prevalence more than once. The streaming builder should be the sole authority for prevalence during one development run. Gene sampling consumes the cached prevalence; no later fit scans 41K columns again.

### E. Phase/fold processes must consume only compact cache

After compact-cache creation:
- Phase A/B development reads only selected counts + design arrays;
- positive-count family comparison reads the same compact panel;
- folds index rows; they do not reload raw shards;
- PPC uses saved compact arrays/posterior summaries;
- raw corrected-S174 shards are not opened again unless the cache identity fails validation.

## CPU/GPU scheduling policy

### CPU

The measured NUTS fit consumes ~10 of 16 logical CPUs by itself. Therefore:
- **one NUTS fit at a time** on this laptop by default;
- no simultaneous heavy CPU geometry/bootstrap job while NUTS runs;
- cap BLAS/OpenMP/JAX CPU threads explicitly;
- benchmark 1-chain/2-chain development probes before 4-chain confirmation;
- use cheap MAP/GLM/mixed-model development comparisons before NUTS;
- exploit Candidate V2 modular per-gene structure: fit a bounded gene batch or one gene at a time, write result, free state, continue.

Two concurrent NUTS processes are not recommended from the observed CPU occupancy.

### GPU

Do not route NUTS to GPU by default. Prior V79 WSL/JAX-CUDA probes were slower/unstable for this step-bound sampler. Use GPU only for workloads that benchmark faster with exact-equivalence checks, e.g.:
- dense residual covariance/eigenspectrum;
- large bootstrap matrix algebra;
- vectorized deterministic development scoring across many genes;
- potentially batched likelihood evaluation after an explicit CPU-vs-GPU benchmark.

Keep posterior NUTS on CPU unless a new bounded benchmark demonstrates a real wall-time win and stable memory behavior.

## Candidate V2 execution strategy

Because the new candidate is modular per gene, the local machine no longer needs one giant cross-gene Bayesian state.

Development sequence:
1. build authenticated compact S174 cache with bounded two-pass streaming;
2. run nested held-out-donor deterministic/penalized models to recheck depth → class → source → operator → donor;
3. directly compare constrained donor/operator random-effect variants; keep donor×class sensitivity separate;
4. run positive-family development on the same compact panel;
5. only after structure stabilizes, run small per-gene Bayesian posterior fits;
6. estimate across-gene geometry as a second-stage meta-distribution from per-gene summaries/draws;
7. then freeze candidate and generate new untouched synthetic confirmation worlds.

This architecture reduces both scientific coupling and compute coupling: a difficult gene cannot force a 20- or 60-gene NUTS job to be rerun in full.

## Required audit before calling the model best-qualified

- commit the exact auxiliary tournament executable or reconstruct and independently reproduce its result;
- full-panel count round-trip validation, not 200-row sampling;
- implement/test bounded two-pass S174 cache builder with no global `vstack`;
- exact S174 nested structure replay;
- direct held-out-donor comparison of constrained operator/donor random effects;
- stable lognormal-vs-ZTNB development comparison if ZTNB remains a challenger;
- independent audit of the selected structure;
- only then freeze and run untouched synthetic confirmation.

No H0/H1/H2/H3 execution and no JEPA training is authorized by this audit.
