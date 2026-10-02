# JEPA chat-exclusive custody and handoff — 2026-10-01

## Purpose

This document preserves information and files that were physically available in the current ChatGPT chat runtime but were not already carried on Sol's implementation branch at custody time. It is a custody/handoff artifact only. It does **not** merge Macha's execution branches, authorize Stage 4, open protected outcomes, or promote synthetic results to biology.

## Git heads at custody time

- Sol implementation branch: `chatgpt/v64-privileged-information-recoverability-20260930`
  - head: `4fd4305395c4da0c025f336006be7c9dbbe6dd70`
- Macha Stage-4 branch: `claude/v64-exact-sampler-successor-20260930`
  - head observed during custody pass: `653ab20b68c0473a24a37384066a250acd471105`
- Macha SCENIC+ branch: `claude/v69-scenicplus-external-network-20261001`
  - head observed during custody pass: `0a1c5733e1c932f2a919c38e8647aded27221ee8`

The raw pasted handbacks archived beside this file include intermediate branch heads and process-state observations. Those are historical observations, not substitutes for re-querying GitHub when current state matters.

## Governance that remains unchanged

- Stage 4: **NOT AUTHORIZED**.
- Real RNA×ATAC correspondence: **UNOPENED**.
- Training: **OFF**.
- Morabito: **PROTECTED**.
- TD60: **BLOCKED**.
- Real recoverability TEST: **SEALED**.
- No broad SCENIC+ eRegulon network is yet qualified as biology.

## Stage-4 corrections carried from this chat

### S99: the first synthetic control construction was not the frozen control construction

The original synthetic worlds used controls that were effectively random rather than the frozen `PROMOTER_FIXED_DISTAL_MATCHED_CONTROL` construction. Consequently, the earlier technical false-positive rates (0.875 at 60 donors and 1.000 at 282 donors), hidden-confound behavior, and control-vs-control behavior characterize that fixture, not the frozen Stage-4 design. They are retained as history but are superseded for design inference.

The repaired fixture binds controls to the same promoter, matches distance within the frozen tolerance, enforces symmetric accessibility/measurement support, trims when no admissible control exists, and fails closed on matching violations.

### Complete five-gate executor

The Stage-4 executor was extended to compute the frozen PASS gates that had previously been absent:

1. primary one-sided LCB95 of Delta > 0;
2. clean control-vs-control null;
3. worst absolute SMD across the 14 frozen matching features <= 0.25;
4. top 1% of donors contribute <= 10% of primary-statistic weight, with Kish ESS reported;
5. attrition/funnel reconciliation.

A separate limitation survives independently: because the primary estimand is donor-averaged, gate 4 is close to structurally vacuous under equal donor weighting. It was implemented as frozen rather than silently redefined.

### V2 prospective calibration

A new prospectively frozen calibration was launched only after repairing the control construction. The design is 4 worlds × 2 donor counts × 40 draws = 320 runs:

- `BIOLOGY_POSITIVE`
- `TRUE_NULL`
- `MEASURED_TECHNICAL`
- `HIDDEN_CONFOUND`
- donor counts 60 and 282

Primary outcome: rate at which `FIVE_GATE_DECISION.ALL_FIVE_PASS` is true in each cell. Per-gate rates are also recorded. Any world build that fails the matching audit halts the sweep as a fixture defect rather than being excluded.

The decisive interpretation was frozen prospectively: if genuine biology and the hidden cross-modal confound pass at similarly high rates, the five-gate design cannot distinguish those two worlds. Do not reinterpret that as two independent successes.

## SCENIC+ / GSE214979 corrections and current state carried from this chat

### Route-B fragment QC is complete

The initial handback incorrectly said Route-B fragment QC was still in flight because the receipt was looked for under `routeB/`. The receipt is under `receipts/` and records a complete full-file scan:

- status: `PASS__ROUTEB_FRAGMENT_QC_COMPLETE`
- records scanned: 5,831,261,753
- cohort-barcode records kept: 23,522,438
- records counted/discarded outside the cohort: 5,807,739,315
- 12/12 development-population donors have at least one passing cell

The 63.6 GB fragments file was independently re-hashed in this chat:

- bytes: 63,641,120,882
- SHA-256: `b7c5aa2d39fb1a3c6e5c9cf06dc83cdcf2c5bb3239151c4276a73f675cb71e8f`

### Donor identity must never be inferred from barcode suffix

Three barcode suffixes map to more than one donor. Suffix-derived donor inference is therefore a demonstrated defect on this dataset, not a hypothetical risk. Every producer touching barcodes must join through the frozen barcode→donor authority and fail closed on suffix-derived mappings.

### Route-B work order

The current intended sequence is:

1. donor-aware pseudobulk extraction from the authenticated fragments;
2. MACS/pycisTopic donor-aware peak calling and consensus region universe;
3. custom cisTarget database machinery;
4. Route-B network and controls;
5. Route-A network with the matched machinery;
6. donor stability, route comparison, frozen program-level receipts and adapters.

No eRegulon biological claim is authorized merely because the substrate or database exists.

### SCENIC+ speed-cycle findings

#### S23: rankings were not reproducible until the random tie-break seed was pinned

The cisTarget tool chose a fresh random seed per run for ranking ties. Score files were identical while rankings differed. The rankings seed is now explicitly pinned as an engineering convention, not a biological choice.

#### S20: BLAS oversubscription was real; pinning is output-safe

The image exposed OpenBLAS with 16 threads. At 16 outer workers that could imply severe oversubscription on an 8-physical-core machine. BLAS threads were pinned to 1. Measured score outputs were bitwise identical between pinned and unpinned BLAS, so the pinning is an execution/scheduling fix rather than a scientific change.

#### Union score reuse is demonstrated; rankings may not be shared

A prospective equivalence test showed that motif-region **scores** can be computed once over a union region set and subset back to route-specific regions without changing values. A deliberately reversed union order was used so a position-dependent implementation could not pass by accident.

The corresponding rankings counter-control changed substantially, proving the comparison can detect differences. Therefore:

- one shared motif-scoring pass over `RouteA ∪ RouteB` is allowed if the full implementation preserves the demonstrated semantics;
- route-specific rankings must still be built separately.

This is the main legitimate compute reduction found so far.

#### C: SSD bind mount did not speed the benchmark

With pinned seed and threads, the same 16-motif × 150,561-region workload produced byte-identical outputs on D: and C: Docker bind mounts.

Indicative timings under the same Stage-4 contention:

- D: external bind mount: 532 s wall, ~203.1 s cbust
- C: internal SSD bind mount: 535 s wall, ~206.6 s cbust

Difference: ~0.6%, inside noise. Therefore do not spend the scratch budget moving cisTarget bind-mounted data from D: to C: on the assumption that the SSD is faster. The caveat is important: this compares Docker Desktop bind mounts, not native container-local storage.

#### Worker-scaling remains the missing speed decision

The worker-scaling table (1/2/4/8/16 workers) was intentionally deferred while the Stage-4 V2 sweep was using CPU. Worker count, shard size, and safe route/build concurrency remain **NOT DETERMINED** until an idle-machine scaling table is measured.

### Long-run engineering guards now treated as hard requirements

- execute long scripts from immutable snapshots; never edit a mounted script while it is executing;
- pin the rankings seed;
- pin BLAS/OpenMP thread counts;
- shard completion receipt is written only after output is closed and re-read from disk;
- merge validation must prove no missing/duplicate/reordered motifs and exact motif-axis identity;
- compare benchmark outputs by artifact kind, not run-specific filename;
- do not delete a C: scratch copy until the D: archival copy has been re-hashed on D: and matches;
- voiding/quarantining a run must also stand down its watchers/monitors.

### Open Route-B design item: ENCODE blacklist

The frozen Section 2 text does not name a blacklist, while the pycisTopic protocol normally excludes blacklist regions. Macha correctly did not choose silently. This requires an explicit prospective amendment before the Route-B region universe is frozen; otherwise either adding or omitting a blacklist would be an unrecorded design choice.

### MACS parameter erratum

The frozen text described pycisTopic protocol defaults but omitted `--nolambda` from the written flag string. pycisTopic supplies it by default. This is recorded as an under-specified frozen string rather than a silent executor deviation. No threshold was tuned in response.

## Synthetic full-project twin requirement added permanently

The synthetic twin must reproduce **selection and matching mechanisms**, not only marginal distributions, geometry, dimensions and confounders. S99 demonstrated why: a fixture can look statistically realistic while measuring a design the project never uses.

For Stage 4 specifically, the twin must reproduce promoter-fixed control selection, distance matching, accessibility/measurement qualification, trimming, matching audits and missingness semantics.

The twin remains staged:

- continue ETL, truth-firewall, failure-injection and checkpoint framework now;
- do not freeze Stage-4 calibration behavior until the repaired V2 sweep lands and is audited;
- do not freeze SCENIC+ network realism until real Route-A/Route-B network characteristics exist.

## Chat-runtime files preserved beside this handoff

All five user-uploaded chat handbacks are preserved verbatim as separate files under `docs/agent/archive/chat_runtime_20261001/`:

- `CHAT_UPLOAD_01_PASTED_TEXT.txt`
- `CHAT_UPLOAD_02_PASTED_TEXT.txt`
- `CHAT_UPLOAD_03_PASTED_TEXT.txt`
- `CHAT_UPLOAD_04_PASTED_MARKDOWN.md`
- `CHAT_UPLOAD_05_PASTED_MARKDOWN.md`

Large scientific files visible in the runtime are Project-backed rather than chat-exclusive. They are **not duplicated into Git history**. Their exact runtime byte sizes and SHA-256 values are preserved in `CHAT_RUNTIME_BINARY_CUSTODY_MANIFEST_20261001.json` where available.

This follows the project custody rule: preserve identity and recovery information for large scientific assets without injecting hundreds of megabytes/gigabytes into ordinary Git history.
