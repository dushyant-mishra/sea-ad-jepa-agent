# Stage75F out-of-core SCENIC+/pycisTarget execution plan

## Purpose

Stage75F moves from Stage75E resource smoke tests into a memory-safe execution
architecture. The goal is to prepare enhancer-supported candidate evidence in
bounded, resumable pieces without asking SCENIC+/pycisTarget to load every cell,
region, and cisTarget column at once.

Approved interpretation remains:

> Model-based, enhancer-informed perturbation hypotheses requiring experimental validation.

## Claim boundaries

Stage75F does not change the locked scientific conclusions:

- `prediction_benchmark_updated=False`
- `causal_validation_pass=False`
- `therapeutic_target_claim=False`
- `validated_grn_claim=False`
- Stage72B remains a candidate TF-target coactivity graph, not a validated GRN.
- Stage75F batches are not candidate selection by outcome.
- Motif support, once produced, is enhancer-informed evidence only, not proof of
  regulation.

## Why out-of-core

Adding Dask or Zarr alone does not make unmodified pycisTopic or pycisTarget
streaming. The pipeline uses a thin adapter layer around the domain-specific
formats:

- stream 10x HDF5 sparse arrays with `h5py`;
- write microglia-only sparse subsets to a disk-backed CSC store;
- use bounded Feather column reads for cisTarget databases;
- run motif-enrichment pilots in restartable regulator/region batches.

## F1/F2 - Stream microglia-only RNA and ATAC subsets

Run an audit first:

```bash
cd "/mnt/d/Jepa project"
MODE=audit IMAGE=scenicplus:1.0a2-container.1 bash scripts/stage75f_run_stream_microglia_10x_wsl.sh
```

If the audit reports matched microglia barcodes for snRNA and snATAC, run the
extractor:

```bash
cd "/mnt/d/Jepa project"
MODE=extract DOCKER_MEMORY=24g IMAGE=scenicplus:1.0a2-container.1 bash scripts/stage75f_run_stream_microglia_10x_wsl.sh
```

Outputs are local processed intermediates and must not be committed:

- `data/processed/stage75f/gse174367_mg_snrna.csc.h5`
- `data/processed/stage75f/gse174367_mg_snatac.csc.h5`
- `data/processed/stage75f/*metadata.parquet` or gzip CSV fallbacks
- `results/reports/stage75f_stream_microglia_10x_manifest_v1.json`

The default HDF5 matrix layout is a CSC sparse representation with `data`, `indices`,
`indptr`, and `shape` arrays. This preserves the 10x sparse-column structure and
avoids loading the full source matrix.

## F3 - Build bounded compatible objects

After F1/F2, materialize smaller microglia-only sparse matrices for the APIs that
require in-memory objects:

- AnnData for expression;
- pycisTopic-compatible accessibility object for bounded pilot regions.

The final pycisTopic object is still an in-memory boundary, so Stage75F should
only materialize microglia-only and then pilot-filtered matrices.

## F4 - Prepare region batch manifests

Create regulator/target/region batches without motif enrichment:

```bash
cd "/mnt/d/Jepa project"
IMAGE=scenicplus:1.0a2-container.1 bash scripts/stage75f_run_prepare_batches_wsl.sh
```

This writes small, restartable batch inputs:

- `results/tables/stage75f_candidate_tf_target_edges_v1.csv`
- `results/tables/stage75f_candidate_peak_gene_links_v1.csv`
- `results/tables/stage75f_batch_manifest_v1.csv`
- `results/stage75f_batches/*.regions.bed`
- `results/stage75f_batches/*.tf.txt`
- `results/stage75f_batches/*.genes.txt`

These are preparation artifacts, not motif-supported eRegulons.

## F5/F6 - Motif-enrichment pilots and expansion

Run IRF8 and STAT1 first. Expand to ELF1, RELA, BACH1, NRF1, SPI1, CEBPA,
STAT3, and MITF only after primary-regulator pilot batches complete.

Each batch should write:

- motif enrichment table;
- motif-to-TF annotation table;
- motif-hit regions;
- query-to-database region mapping statistics;
- runtime and memory report.

Completed batches should be skipped on restart. A failed batch must not require
rerunning completed batches.

## F7/F8 - Candidate evidence assembly and SCENIC+ integration

Only after batched motif support exists:

1. assemble candidate TF-region-gene evidence;
2. record which edges have motif support and region-gene proximity support;
3. run compatible SCENIC+ integration steps on bounded microglia-only objects;
4. export evidence tables with the claim language preserved.

## Git discipline

Do not stage:

- raw 10x HDF5 files;
- Stage75F extracted sparse matrices;
- cisTarget feather databases;
- motif tables;
- download logs;
- generated Docker logs;
- unrelated protected working-tree files.

Review any small generated summary table before deciding whether it belongs in
Git.
