# Stage75E SCENIC+ preparation and execution plan

## Purpose

Prepare the first true enhancer-supported execution stage without changing the
locked Stage27C benchmark or upgrading any causal, therapeutic, or validated-GRN
claim.

Approved interpretation:

> Model-based, enhancer-informed perturbation hypotheses requiring experimental validation.

## Locked scientific boundaries

- `prediction_benchmark_updated=False`
- `causal_validation_pass=False`
- `therapeutic_target_claim=False`
- `validated_grn_claim=False`
- Stage72B remains a candidate TF-target coactivity graph, not a validated
  TF-peak-gene GRN.
- Stage73R showed that context graph features can improve a compact model over
  no graph, but topology-specific utility was not established because a
  target-shuffled control was slightly better.
- Stage74 is hypothesis-organizing only.
- IRF8 and STAT1 are the only primary regulators that passed all Stage74 gates.
- ELF1, RELA, BACH1, NRF1, SPI1, CEBPA, STAT3, and MITF remain descriptive
  secondary hypotheses.
- Stage74's earlier bootstrap was not a true donor bootstrap and must not be
  reused as donor-level uncertainty.

## Preparation sequence

### E0 - Container runtime

Already completed:

- clean SCENIC+ v1.0a2 image;
- `pip check` passes;
- principal imports pass;
- external-tool smoke tests pass;
- mounted project write test passes.

### E1 - Input and schema freeze

Run while the large databases are downloading:

```bash
MODE=inputs bash scripts/stage75e_run_preflight_wsl.sh
```

This writes:

- `results/tables/stage75e_input_inventory_v1.csv`
- `results/reports/stage75e_input_inventory_v1.json`
- a mechanics-only TF/target/peak subset

No raw matrices are copied or committed.

### E2 - Small motif annotation

Run independently of the large downloads:

```bash
bash scripts/stage75e_download_motif_annotation_wsl.sh
```

The downloaded table remains under `data/` and must not be committed.

### E3 - cisTarget integrity gate

After both large feather files finish and the downloader's SHA1 checks pass:

```bash
MODE=all VERIFY_SHA1=0 bash scripts/stage75e_run_preflight_wsl.sh
```

Set `VERIFY_SHA1=1` only when an additional full streamed SHA1 pass is desired.
The downloader already performs the authoritative checksum validation.

### E4 - Minimal mechanics-only pycisTarget/SCENIC+ smoke test

Use the generated bounded BED/TF/gene files to verify mechanics without making
biological claims:

```bash
IMAGE=scenicplus:1.0a2-container.1 bash scripts/stage75e_run_pycistarget_smoke_wsl.sh
```

This checks SCENIC+/pycisTarget imports, bounded region/TF/gene inputs,
motif-to-TF annotation overlap, and non-memory-mapped Arrow schema access for
the cisTarget databases. It is a resource/API smoke test, not motif enrichment
inference and not biological validation.

### E5 - Full enhancer-supported eGRN construction

Only after E4 passes:

1. prepare GSE174367 microglia snRNA AnnData;
2. prepare GSE174367 microglia snATAC/pycisTopic object;
3. link the non-paired modalities using frozen sample/state annotations;
4. run motif enrichment with the official hg38 databases;
5. construct TF-to-region and region-to-gene evidence;
6. export enhancer-supported directed candidate eRegulons.

### E6 - State-specific signed response models

Fit donor-grouped regularized response models separately for:

- MTG rare-high;
- MTG background;
- DLPFC rare-high;
- DLPFC background.

Use the enhancer-supported graph as a predictor mask, not as proof of regulation.
Do not select edges by pathology outcome.

### E7 - Bounded perturbation propagation

Use fixed doses `0.25, 0.50, 0.75, 1.00`, at most three iterations, bounded
expression shifts, and the frozen JEPA readout.

Required controls include:

- no propagation;
- degree-preserved target shuffle;
- sign shuffle;
- TF-label shuffle;
- region-to-gene shuffle;
- state-label-shuffled coefficients;
- expression-matched random regulator;
- background coefficients applied to rare-high cells.

### E8 - True donor hierarchical uncertainty

Resample donors first, then cells within donor. Do not treat two datasets as
donor bootstrap units. Report donor counts, successful bootstrap iterations,
median effects, intervals, sign stability, and control deltas.

## Git discipline

Do not stage:

- raw H5/H5AD files;
- cisTarget feather databases;
- motif tables;
- download logs;
- generated caches;
- existing unrelated/protected working-tree files.

Review all generated result tables before staging.
