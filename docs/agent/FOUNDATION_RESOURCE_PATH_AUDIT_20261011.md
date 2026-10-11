# Foundation / JEPA Resource-Path Audit — 2026-10-11

## Scope

Prospective code/resource review while training remains unauthorized. This audit distinguishes current bounded paths from future physical benchmarking that cannot yet be run because the final production representation/training path is not frozen.

## Current code findings

### Historical PROD41K T1 teacher path

`scripts/v4/stage81a3_prod41k_teacher_t1.py` is bounded by design rather than materializing all cells × all addresses as one dense tensor:

- effective batch = 128;
- training microbatch = 8;
- evaluation batch = 8;
- evaluation biology surface uses a 4,096-feature vocabulary;
- representation evaluation buffers are bounded to the fixed evaluation cohort, not the full 4.55M-cell population;
- GPU tensors are created batchwise.

This does not make the historical path a current production resource authority, but it rules out an obvious all-population dense allocation in that implementation.

### Contextual target preflight

`scripts/v4/contextual_target_f1_preflight_core_v1.py` contains a `.getrow(...).toarray()` path over 41,238 addresses. The densification is one requested row at a time, so peak dense memory is bounded; however, repeated row extraction can be I/O/CPU-inefficient at scale. It should not be generalized into a full-population execution pattern.

### V79/Macha real-data path

Independent audit already found that Macha's later corrected-TRAIN phases reload and stack the full 41,238-column sparse TRAIN matrix separately in each process before selecting a much smaller gene panel. That is avoidable repeated I/O/memory pressure. The current representation V4 resource contract therefore requires a compact authenticated selected-feature cache for heavy real fits rather than repeated full-registry reconstruction.

### V79 factorial synthetic path

The separate V79 factorial lane has already been hardened prospectively: latent biology is blockwise, observation streams directly to sparse counts, scoring stays sparse until selected genes, and CI verifies old-vs-new endpoint equivalence.

### FULL104 dimension path

The FULL104 lane is intentionally physical/blockwise and now has prospective precision and returned-metric receipt contracts in PR #270. The >30 GB / 8,915-block physical expression store is not mounted in the current chat environment, so peak resource behavior of the eventual full-stream dimension execution cannot be truthfully measured here.

## Memory arithmetic guard

A single 4,000 × 41,238 float32 dense matrix is 659,808,000 bytes before rates, masks, gradients, optimizer state, copies or framework overhead. Registry-wide dense materialization is therefore not a lawful default.

The V4 compact-cache contract permits dense selected-feature material only after an explicit memory-budget check and requires source/hash binding.

## Current ruling

`CURRENT_KNOWN_PATHS_BOUNDED_OR_HARDENED__REPEATED_FULL_REGISTRY_RELOAD_IDENTIFIED_AND_FORBIDDEN_FOR_NEW_HEAVY_REAL_FITS__FINAL_PRODUCTION_RESOURCE_BENCHMARK_PENDING_FINAL_EXECUTION_PATH`

The remaining resource task is a measurement gate, not an architecture-design task:

- once the final representation/training executor is frozen, record peak RAM/VRAM, CPU utilization, disk read volume, wall time and cache hit/reuse behavior on the exact path;
- fail closed if the executor reconstructs full-registry data per worker/process when a compact authenticated cache can serve the same scientific input;
- do not treat historical Stage81A3 peak RSS (~6.39 GB) as a guarantee for the future executor.

`training_authorized=false`
