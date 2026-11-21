# Macha GPU execution environment and runtime custody V1

Date: 2026-10-14
Status: `HISTORICAL_EXECUTION_CAPABILITY_RECOVERED__CURRENT_MERGED_RUNTIME_REQUALIFICATION_REQUIRED__NO_TRAINING_AUTHORITY`

## Purpose

Correct the merged-lane execution model using project history. The project does not lack a production-capable GPU execution environment. Macha is a Claude coding/execution agent operating on the project GPU laptop and is the natural executor for GPU-bound qualification and, if separately authorized later, production training. This document binds historical execution capability without promoting any current training authority.

## Historical hardware/runtime evidence

Project handoffs record a frozen historical GPU contract:

- NVIDIA GeForce RTX 3080 Laptop GPU
- 16 GB VRAM
- 115 W power limit
- Intel Core i9-11980HK
- 8 physical / 16 logical CPU cores
- ~32 GB RAM
- historical PyTorch 2.7.0+cu128

Later execution must re-detect the actual current runtime rather than assume the historical software stack remains unchanged.

Historical full 41,238-address mechanics had already run successfully at physical microbatch 16 with approximately 10.7 GiB allocated / 10.9 GiB reserved. Historical 4,096-gene synthetic runs used substantially less VRAM (~3 GB), so synthetic and production microbatch decisions were explicitly kept separate.

## Historical GPU execution evidence

The project contains prior real GPU-bound execution, not merely CPU reference code:

1. Frozen-cache predictor execution retained exact hidden queries, visible controls, full-view and self-masked targets, student CELL and complete visible student gene states. A frozen cache of 1,111 cells reached ~5.43 GiB, with the expected u0 SHA checked before and after.
2. Predictor fitting was launched under `conda run -n sea-ad-jepa`, with `nvidia-smi` used to verify GPU utilization and memory residency.
3. Execution-environment failures from conflicting Intel/OpenMP runtimes were encountered and provenance-recorded. Compatibility attempts included `MKL_THREADING_LAYER=GNU`, then `KMP_DUPLICATE_LIB_OK=TRUE` with single-thread CPU math while GPU optimization remained active. These are historical environment facts, not current approved runtime settings.
4. Project history defines GPU preflight requirements for scientific correctness, checkpoint recovery, true gradient accumulation, safe VRAM headroom and throughput measurement.
5. A remote FULL104 execution contract existed specifically because >30 GB physical FULL104 assets were expected to be executed on the GPU laptop/attached drive and return compact receipts.

## Historical optimizer/EMA execution law

The project explicitly recognized that changing physical microbatch without true accumulation changes the optimizer. The intended production form was:

- zero_grad once per effective update;
- forward/backward over physical microchunks;
- loss weighted by microchunk scientific mass / effective scientific mass;
- optimizer step exactly once;
- EMA update exactly once after the proved optimizer step.

Historical GPU optimization policy was to choose the smallest microbatch within 5% of fastest safe throughput, with reserved VRAM capped prospectively around 85% of runtime total and measurements for GPU utilization, transfer, forward/backward, optimizer and EMA time.

## Correct merged-lane role model

Macha has distinct roles that must not be conflated:

1. `GPU_EXECUTION_AGENT`
   - run exact frozen commands on the GPU laptop;
   - access physical FULL104/heavy assets available there;
   - perform GPU mechanics, equivalence, memory/throughput and later authorized training runs;
   - emit exact source/runtime/hardware/artifact receipts.

2. `AUTHOR_IMPLEMENTER`
   - Macha authored/implemented old synthetic Tasks 1–2 at exact head `ff597faf2182522a320ec5322f8db9b67c9c6094`;
   - for those bytes, Macha may provide author/provenance attestation and identify defects, but cannot independently qualify/adjudicate his own implementation.

3. `INDEPENDENT_HOSTILE_REVIEWER_OF_CONTROLLER_WORK`
   - Macha may independently review controller/merged-lane artifacts he did not author, including Task 0 custody/consolidation at `c80d7398b41f10208ec1622bc52599383b940be6`;
   - he may independently adjudicate the controller's migration/classification of historical artifacts.

Controlling independence law:

`SAME_AGENT_SEPARATE_PASS != INDEPENDENT_REVIEW`

An execution or implementation performed by Macha cannot self-promote merely because Macha can also perform a later review pass. Where Macha is the executor/author, a different reviewer/controller must adjudicate before promotion. Where the controller authored the artifact, Macha can serve as independent hostile reviewer.

See also:
`docs/agent/MACHA_ROLE_INDEPENDENCE_CORRECTION_V1_20261014.md`

## Consequence for downstream packages

Package N (`PACKING_RNG_HARDWARE_EQUIVALENCE`) must no longer be described as "build/obtain production GPU runtime." The GPU runtime/executor exists historically. Package N must:

- re-detect current hardware/software/runtime;
- bind exact source/config/TQB/runtime roots;
- qualify reference-vs-GPU semantics and gradient equivalence where required;
- qualify current physical microbatch/accumulation without changing scientific weights or optimizer definition;
- verify identity-keyed RNG/packing on GPU;
- freeze current hardware/kernel provenance.

Package J must run inherited optimizer/gradient/moment/EMA hostile tests on the exact joined current GPU configuration.

Package L must bind checkpoint/resume/source/runtime/environment provenance for the current GPU runtime and fail closed on unrecorded environment pivots.

Package R (`RUNTIME_ELIGIBILITY`) consumes the GPU qualification receipts; it does not wait for a hypothetical future GPU executor.

## What is still not qualified

Historical GPU capability does not establish current merged authority. Still required:

- current exact TQB-bound teacher/student/runtime source identity;
- current model/protected-registry geometry;
- current CUDA/PyTorch/driver/kernel environment receipt;
- current GPU reference/equivalence qualification;
- current true-accumulation and scientific-weight parity;
- current EMA timescale authority;
- current checkpoint/resume/runtime provenance;
- complete hostile leakage/falsifier battery on the joined configuration;
- downstream certification;
- runtime eligibility;
- independent training-eligibility review;
- explicit training authorization.

## Authority

This document changes execution/custody understanding only. It does not authorize optimizer execution on protected/current production data and does not authorize training.

Binding global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
