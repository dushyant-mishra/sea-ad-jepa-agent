# Stage81A evidence, calibration, and mechanics readout

## Scope

This is the chronological scientific readout for Stage81A0 through the current
Stage81A3 work. It records the governing v4 design, data acquisition and
provenance, canonical data/vocabulary/split freeze, masking calibration,
synthetic mechanics, real-RNA forward-only validation, and initialization-
geometry forensics. Detailed stage-specific documents and machine-readable
artifacts remain authoritative; this file connects them into one navigable
record.

Nothing in this readout establishes real-data model training, learned biology,
pathology discrimination, causal regulation, therapeutic validity, or an
approved production checkpoint. Stage81B and Stage81C have not started.

Source artifacts:

- `results/v4/stage81a3_masking_calibration_summary.csv`
- `results/v4/stage81a3_masking_calibration_strata.csv`
- `results/v4/stage81a3_masking_calibration_report.json`
- `results/v4/stage81a3_remaining_mechanics_calibration.json`
- `results/v4/stage81a3_ema_variance_resolution.json`
- `results/v4/stage81a3_real_rna_forward_smoke.json`
- `results/v4/stage81a3_real_rna_forward_smoke_cells.csv`
- `results/v4/stage81a3_initialization_geometry_diagnostic.json`
- `results/v4/stage81a3_initialization_geometry_stages.csv`

## Stage81A chronology and provenance map

### Stage81A0: v4 design and failure-registry contract

Stage81A0 froze the design boundaries before new model work. It documented 56
historical issues, including 46 blocking or guardrail-tagged entries and ten
non-blocking entries. Twenty remained unresolved because many gates were
intentionally assigned to later stages. `stage81a0_pass=true` means the design
and failure registry were complete; it does not mean all later scientific
gates were solved.

The governing report is `results/v4/stage81a0_v4_stage_report.json`; the
human-readable contract is
`docs/v4/STAGE81A0_V4_FAILURE_REGISTRY_AND_DESIGN_CONTRACT.md`. The pathology-
blind foundation, later regulatory adapter, spatial branch, perturbation work,
and multi-agent council were kept as separate stage responsibilities.

### Stage81A1: local multimodal inventory

Stage81A1 inventoried local RNA, regulatory, spatial, perturbation, donor,
section, gene-identity, and graph evidence without training or constructing the
final v4 matrix. The audit passed. It confirmed the existing expression
normalization provenance and preserved the Stage75-79 TF/motif/chromatin graph
as a soft-prior lineage rather than a validated GRN. Spatial panels, ATAC peak
matrices, expression matrices, and historical interaction graphs retained
separate modality and claim boundaries.

The authoritative report is
`results/v4/stage81a1_multimodal_inventory_report.json`; the navigation guide
is `docs/v4/STAGE81A1_LOCAL_MULTIMODAL_INVENTORY.md`.

### Stage81A1B: official SEA-AD acquisition and regulatory preservation

Stage81A1B acquired and verified the approved June 2026 processed SEA-AD
portfolio, with no unfinished part files. It registered eleven official brain
regions, 144,023 RNA multiome cells, 138,118 ATAC multiome cells, and 133,084
exactly linked cells. It preserved 96 Stage75 integrated TF-target edges and
their source hashes, evidence tiers, motif, accessibility, coactivity,
peak-proximity, uncertainty, and claim-boundary fields.

The stage kept four graph lineages distinct: historical expression/module
graphs, STRING interaction controls, Stage75-79 candidate TF-target evidence,
and motif/enhancer/ATAC evidence features. None was promoted to causal or
validated regulation. See `results/v4/stage81a1b_acquisition_report.json` and
`docs/v4/STAGE81A1B_OFFICIAL_SEA_AD_ACQUISITION.md`.

### Stage81A1C-N/P: normal-reference and perturbation acquisition

Stage81A1C-N completed the approved normal-reference acquisition with ten
required assets, a four-donor/88-region clean normal holdout, and explicit
non-equivalence of differing microglia partitions. Stage81A1C-P registered 16
processed perturbation assets across eight studies and completed full-object
audits for two RDS objects. Unequal CRISPRa/CRISPRi feature universes and
unresolved archive-level identities remained explicit harmonization work, not
silently aligned matrices.

The authoritative reports are
`results/v4/stage81a1c_n_acquisition_report.json` and
`results/v4/stage81a1c_p_acquisition_report.json`, with corresponding documents
under `docs/v4/STAGE81A1C_N_NORMAL_REFERENCES.md` and
`docs/v4/STAGE81A1C_P_PERTURBATION.md`.

### Stage81A1D: living-human bridge

Stage81A1D verified 50 assets across the living-human bridge. HVS contains 24
partitions, 379,330 cells, and 78 exact source donors with no cross-partition
duplicate cells. NPH contains 957,659 source cells, 892,828 exact final-
annotation cells, and 52 exact donors. GSE226602 and GSE226267 share 45 exact
donors. The stage separated direct living-brain foundation candidates,
adapters, continuation candidates, and validation-only sources.

The report is
`results/v4/stage81a1d_living_human_acquisition_report.json`; see also
`docs/v4/STAGE81A1D_LIVING_HUMAN.md`.

### Stage81A2: canonical data, vocabulary, and split freeze

Stage81A2 froze the pathology-blind data contract at evidence commit
`808ce4f170055c5568cc5c1e0e3a56415b52f908`. It did not merge physical
matrices, create shards, upload data, or train a model.

- Foundation matrices: 36 across 13 datasets.
- Foundation donors: 149 train, 19 development, and 19 sealed.
- Cross-split leakage: zero.
- Vocabulary: exactly 4,096 unique canonical Ensembl genes.
- Vocabulary semantic hash:
  `f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb`.
- HVS: 24 partitions, 379,330 cells, 78 exact donors.
- NPH: 957,659 source cells; 892,828 retained exact-annotation cells; 64,831
  retained in source provenance but excluded from foundation eligibility as
  `missing_required_annotation`, not described as QC failures.
- GSE226602/GSE226267 exact donor overlap: 45.
- Pathology fields in the foundation manifest: zero.
- Readiness blockers: none; `stage81a2_pass=true` and
  `ready_for_stage81b=true` applied to the frozen data contract only.

The freeze report is `results/v4/stage81a2_freeze_report.json`; the detailed
contract is `docs/v4/STAGE81A2_CANONICAL_DATA_VOCABULARY_SPLIT_FREEZE.md`.

## Governing calibration contract

- Frozen vocabulary: 4,096 canonical genes.
- Vocabulary hash:
  `f2759db27218c7f9e716974bbdb7c6bcdfc2858a6b3e1acca4d7d97eea2abecb`.
- Expression transformation: raw counts, per-cell library-size normalization
  to 10,000, then `log1p`.
- Only genes measured in a source were eligible for masking.
- Measured zero expression remained distinct from an unmeasured feature.
- Population: foundation-training donors only.
- Development and sealed donors were excluded.
- Mask candidates: 15%, 25%, 40%, 50%, 60%, and 70%.
- Three deterministic random masks were evaluated per sampled cell and masking
  level.
- Masking calibration seed: 8102. This is not a production seed.
- Sampling rule: at most two cells per foundation-training donor, source
  object, and broad cell class, selected by stable SHA-256 cell hashes.
- Source and cell-class labels were used for stratified summaries only and did
  not change a cell's gene-masking probability.

## Calibration population

The calibration contained 6,896 unique cells and 124,128 cell-mask
evaluations.

| Source | Sampled cells | Evaluations across six levels and three replicates |
|---|---:|---:|
| HVS | 2,817 | 50,706 |
| NPH | 246 | 4,428 |
| SEA-AD | 3,833 | 68,994 |
| **Total** | **6,896** | **124,128** |

Sampled broad-cell-class counts were:

- HVS: 1,092 GABAergic neuronal, 1,096 glutamatergic neuronal, and 629
  non-neuronal/non-neural cells.
- NPH: 36 Astro, 38 Endo, 32 ExN, 32 InN, 36 MG, 36 OPC, and 36 Oligo cells.
- SEA-AD: 888 GABAergic neuronal, 888 glutamatergic neuronal, 888
  non-neuronal/non-neural, and bounded source-subclass samples including 74
  each for Astrocyte, Endothelial, Microglia-PVM, OPC, Oligodendrocyte, and most
  named neuronal subclasses.

## Overall exploratory masking results

| Masked genes | Evaluations | Median visible detected | P05 visible detected | Median signal retained | P05 signal retained | Below 100 | Below 250 | Below 500 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 15% | 20,688 | 2,112 | 737 | 85.0% | 83.9% | 0.01% | 0.13% | 1.44% |
| 25% | 20,688 | 1,864 | 652 | 75.0% | 73.6% | 0.01% | 0.19% | 2.24% |
| 40% | 20,688 | 1,492 | 520 | 60.0% | 58.4% | 0.01% | 0.53% | 4.44% |
| 50% | 20,688 | 1,244 | 435 | 50.0% | 48.4% | 0.02% | 0.90% | 7.55% |
| 60% | 20,688 | 995 | 348 | 40.0% | 38.4% | 0.04% | 1.77% | 13.00% |
| 70% | 20,688 | 746 | 260 | 30.0% | 28.5% | 0.18% | 4.42% | 24.06% |

The overall low-information tail expands gradually through 50%, accelerates at
60%, and is pronounced at 70%. This is a descriptive observation, not a policy
threshold.

## Source-level effective difficulty across all levels

The table reports the fifth percentile of visible detected genes. Median
retained signal remained close to the expected unmasked fraction in every
source, but the number of genes carrying that signal differed.

| Masked genes | HVS P05 | SEA-AD P05 | NPH P05 | Lowest-to-highest source range |
|---:|---:|---:|---:|---:|
| 15% | 818.5 | 696.9 | 550.0 | 550.0-818.5 |
| 25% | 717.0 | 616.0 | 480.9 | 480.9-717.0 |
| 40% | 574.0 | 490.9 | 384.9 | 384.9-574.0 |
| 50% | 480.5 | 409.0 | 316.9 | 316.9-480.5 |
| 60% | 384.0 | 325.9 | 251.9 | 251.9-384.0 |
| 70% | 286.0 | 245.0 | 190.0 | 190.0-286.0 |

At 70% masking, 24.1% of all evaluations had fewer than 500 visible detected
genes. The source and class summaries showed especially large tails in NPH
microglia and endothelial cells, SEA-AD Microglia-PVM, endothelial and VLMC
cells, and broad non-neuronal populations. Neuronal populations generally
retained larger visible contexts.

## Focused 40% versus 50% readout

Values below are shown as **40% masking -> 50% masking**. `Evaluations` is the
number of calibration evaluations at each masking level and includes three
deterministic masks per sampled cell.

## Source comparison

| Source | Evaluations | Median visible detected | P05 visible detected | Median signal retained | Below 500 | Below 250 |
|---|---:|---:|---:|---:|---:|---:|
| HVS | 8,451 | 1,547 -> 1,288 | 574 -> 480.5 | 60.0% -> 50.0% | 2.9% -> 5.9% | 0.0% -> 0.0% |
| NPH | 738 | 1,145.5 -> 956.5 | 384.9 -> 316.9 | 60.1% -> 50.1% | 9.5% -> 12.5% | 0.9% -> 2.4% |
| SEA-AD | 11,499 | 1,453 -> 1,212 | 490.9 -> 409 | 60.0% -> 50.0% | 5.3% -> 8.5% | 0.9% -> 1.5% |

NPH has the lowest source-level median and fifth-percentile visible-gene counts
at both masking levels.

## Priority cell populations

| Broad cell class | Source | Evaluations | Median visible detected | P05 visible detected | Median signal retained | Below 500 | Below 250 |
|---|---|---:|---:|---:|---:|---:|---:|
| MG | NPH | 108 | 696.5 -> 581.5 | 310.8 -> 259.5 | 60.2% -> 50.1% | 12.0% -> 25.9% | 0.0% -> 5.6% |
| Microglia-PVM | SEA-AD | 222 | 1,009.5 -> 839.5 | 421.1 -> 352.2 | 60.2% -> 50.1% | 11.3% -> 18.9% | 0.0% -> 0.0% |
| Endo | NPH | 114 | 805 -> 656.5 | 242.7 -> 206.3 | 60.2% -> 50.0% | 26.3% -> 26.3% | 6.1% -> 7.9% |
| Endothelial | SEA-AD | 222 | 1,350.5 -> 1,124 | 225 -> 180.1 | 60.1% -> 50.1% | 33.3% -> 33.8% | 10.4% -> 16.2% |
| VLMC | SEA-AD | 222 | 1,006.5 -> 838.5 | 200.2 -> 171.1 | 60.0% -> 50.0% | 34.2% -> 38.3% | 12.2% -> 14.9% |
| Astro | NPH | 108 | 1,306.5 -> 1,094 | 433 -> 354.4 | 60.1% -> 50.3% | 8.3% -> 8.3% | 0.0% -> 0.0% |
| Astrocyte | SEA-AD | 222 | 1,319.5 -> 1,091 | 614.1 -> 504.6 | 60.1% -> 50.0% | 1.4% -> 4.1% | 0.0% -> 0.0% |
| Oligo | NPH | 108 | 941.5 -> 788 | 335.4 -> 281.3 | 59.9% -> 49.9% | 13.9% -> 19.4% | 0.0% -> 2.8% |
| Oligodendrocyte | SEA-AD | 222 | 896 -> 747 | 401.1 -> 334.8 | 59.8% -> 49.9% | 10.4% -> 16.7% | 1.4% -> 1.4% |
| OPC | NPH | 108 | 1,248.5 -> 1,053 | 679.8 -> 567.1 | 60.0% -> 49.9% | 2.8% -> 2.8% | 0.0% -> 0.0% |
| OPC | SEA-AD | 222 | 1,344.5 -> 1,118 | 724.5 -> 600.4 | 59.9% -> 50.0% | 1.4% -> 1.4% | 0.0% -> 0.0% |
| ExN | NPH | 96 | 2,169 -> 1,811.5 | 659.8 -> 548 | 60.0% -> 50.1% | 0.0% -> 1.0% | 0.0% -> 0.0% |
| InN | NPH | 96 | 1,888.5 -> 1,586 | 846.5 -> 708.8 | 60.2% -> 50.2% | 0.0% -> 0.0% | 0.0% -> 0.0% |
| GABAergic | HVS and SEA-AD | 5,940 | 1,527 -> 1,271 | 676 -> 560 | 60.0% -> 50.0% | 1.8% -> 3.5% | 0.1% -> 0.3% |
| Glutamatergic | HVS and SEA-AD | 5,952 | 1,865 -> 1,553 | 1,048.6 -> 871 | 60.0% -> 50.0% | 0.2% -> 0.5% | 0.1% -> 0.1% |
| Non-neuronal and non-neural | HVS and SEA-AD | 4,551 | 888 -> 739 | 406.5 -> 337 | 60.0% -> 49.9% | 10.3% -> 19.4% | 0.9% -> 1.6% |

## Other adequate broad-cell-class strata

All rows below are SEA-AD source-by-class strata.

| Broad cell class | Evaluations | Median visible detected | P05 visible detected | Median signal retained | Below 500 | Below 250 |
|---|---:|---:|---:|---:|---:|---:|
| Ependymal | 201 | 1,273 -> 1,067 | 629 -> 529 | 60.1% -> 50.1% | 3.0% -> 5.0% | 0.5% -> 1.5% |
| LSX | 105 | 1,969 -> 1,639 | 1,225.8 -> 1,026.6 | 60.1% -> 50.1% | 0.0% -> 0.0% | 0.0% -> 0.0% |
| OB GABA | 93 | 1,295 -> 1,073 | 808 -> 669.6 | 60.0% -> 50.0% | 0.0% -> 0.0% | 0.0% -> 0.0% |
| Sst Chodl | 222 | 1,976 -> 1,649 | 431.5 -> 372.3 | 60.0% -> 50.0% | 11.7% -> 14.9% | 0.0% -> 0.0% |
| Vip | 222 | 1,662.5 -> 1,384 | 764.2 -> 637.4 | 60.1% -> 50.0% | 0.0% -> 1.4% | 0.0% -> 0.0% |
| STR D1 MSN | 222 | 1,944 -> 1,622 | 987.2 -> 813.2 | 60.0% -> 50.0% | 0.0% -> 2.3% | 0.0% -> 0.0% |
| STR D2 MSN | 222 | 1,969 -> 1,641.5 | 1,091.5 -> 903.7 | 60.1% -> 50.0% | 0.0% -> 0.0% | 0.0% -> 0.0% |
| STR Hybrid MSN | 222 | 1,857 -> 1,547 | 1,017.1 -> 847.3 | 60.0% -> 49.9% | 0.0% -> 0.0% | 0.0% -> 0.0% |
| STR RSPO2 GABA | 222 | 1,748 -> 1,452 | 586.2 -> 484 | 60.0% -> 50.0% | 1.8% -> 6.3% | 0.0% -> 0.0% |
| CN LAMP5-CXCL14 GABA | 222 | 1,648.5 -> 1,378.5 | 542.3 -> 447.2 | 60.1% -> 50.0% | 3.2% -> 9.0% | 0.0% -> 0.0% |
| CN ST18 GABA | 222 | 1,836.5 -> 1,531 | 512.9 -> 428.5 | 59.9% -> 49.9% | 5.4% -> 5.4% | 0.0% -> 0.0% |

## Shared broad classes by source

| Broad cell class | Source | Evaluations | Median visible detected | P05 visible detected | Median signal retained | Below 500 | Below 250 |
|---|---|---:|---:|---:|---:|---:|---:|
| GABAergic | HVS | 3,276 | 1,536 -> 1,280 | 821.8 -> 687.3 | 60.0% -> 50.0% | 0.7% -> 1.7% | 0.0% -> 0.0% |
| GABAergic | SEA-AD | 2,664 | 1,504.5 -> 1,253.5 | 575.5 -> 479.2 | 60.0% -> 50.0% | 3.2% -> 5.6% | 0.1% -> 0.7% |
| Glutamatergic | HVS | 3,288 | 1,834 -> 1,531 | 1,151 -> 955.4 | 60.0% -> 50.0% | 0.2% -> 0.3% | 0.0% -> 0.0% |
| Glutamatergic | SEA-AD | 2,664 | 1,915.5 -> 1,596 | 944.5 -> 790.5 | 60.0% -> 50.0% | 0.3% -> 0.8% | 0.1% -> 0.1% |
| Non-neuronal and non-neural | HVS | 1,887 | 821 -> 688 | 430.6 -> 357.3 | 60.0% -> 50.0% | 11.3% -> 22.7% | 0.0% -> 0.0% |
| Non-neuronal and non-neural | SEA-AD | 2,664 | 925.5 -> 774.5 | 377.3 -> 316 | 60.0% -> 49.9% | 9.6% -> 17.1% | 1.6% -> 2.7% |

## Integrity and runtime record

- NPH exact anti-join reproduced the frozen source disposition:
  957,659 source cells, 892,828 retained with exact final annotation, and
  64,831 classified as `missing_required_annotation`.
- The NPH calibration used only the 19 approved NPH Ctrl foundation-training
  donors and 246 bounded sampled cells.
- NPH source-specific measurement masks were retained across the seven QS
  source objects.
- The Stage81A3-local disposition and bounded-expression caches passed gzip
  integrity checks before calibration.
- The completed calibration runtime was 278.314 seconds.
- Runtime warnings: none.
- Focused Stage81A3 tests: 9 passed.
- Full v4 regression suite after calibration: 105 passed.
- Generated calibration outputs contain no machine-specific absolute paths.
- No frozen Stage81A2 evidence file was modified.
- No training shards, merged physical matrix, model initialization, or model
  training were performed.
- No development donor, sealed donor, pathology sidecar, pathology value, or
  disease label was accessed.

## Post-calibration synthetic mechanics validation

After the masking calibration, a separate synthetic-only mechanics task tested
the proposed gene visibility and token-construction semantics for Decisions 3
and 4. This work did not reopen calibration data, train on real data, implement
the full JEPA architecture, or freeze a masking percentage.

### Visibility semantics

Three concepts remain separate:

- `measurement_mask`: the gene was genuinely measured by the source.
- `context_mask`: a measured gene was intentionally hidden from the student.
- `expression`: the Stage81A2-normalized continuous expression value.

The implemented validity rules are:

```text
student_valid = measurement_mask AND NOT context_mask
target_valid  = measurement_mask
```

Operational behavior:

| Gene state | Student | Target |
|---|---|---|
| Measured, visible, nonzero | Active with expression value | Active with expression value |
| Measured, visible, zero | Active with numeric value `0.0` | Active with numeric value `0.0` |
| Measured, context-hidden | Excluded from attention | Active with true expression value |
| Unmeasured | Excluded from attention | Excluded from attention |

The dense implementation uses the inverse validity mask as PyTorch's
cross-attention `key_padding_mask`. Excluded genes therefore receive exactly
zero attention probability. There is no learned mask embedding, unmeasured
embedding, source-missingness embedding, or active placeholder token.

### Gene identity and expression fusion

The synthetic tokenizer implements:

```text
identity_component = Linear48to160(Embedding4096x48(gene_id))
value_component = Linear32to160(GELU(Linear1to32(expression)))
token = LayerNorm(identity_component + value_component)
```

The 4,096-by-48 gene identity embedding values are trainable. Vocabulary
identity, vocabulary order, and embedding dimension remain contract-bound. The
continuous value encoder is shared across all genes and sources; it is not
gene-specific or source-specific.

### Minimal set encoder

The initial Decision 3/4 bounded mechanics encoder contained:

- 24 learned latent slots;
- model width 160;
- four attention heads;
- one gene-token-to-latent cross-attention operation;
- no gene-array positional embedding;
- no predictor, EMA update, JEPA loss, collapse loss, or training loop at that
  checkpoint. Predictor and loss mechanics were evaluated later as a separate
  synthetic-only task described below.

### Synthetic observations

- Different genes remained distinguishable at identical zero expression and
  identical nonzero expression.
- One gene produced different tokens at expression values `0`, `0.5`, `1`,
  `2`, and `4`.
- Measured-zero genes remained active and retained gene identity.
- Token outputs for `2.000`, `2.001`, `2.010`, and `2.100` were finite and
  numerically continuous.
- Gene-order permutation invariance passed with predeclared
  `rtol=1e-6` and `atol=1e-6`.
- Student permutation maximum absolute difference was `7.15e-7`.
- Target permutation maximum absolute difference was `9.54e-7`.
- Changing an unmeasured gene from `0` to `1000` produced exactly zero student
  and target representation change.
- Unmeasured-gene attention probability was exactly zero.
- Changing a measured context-hidden gene from `0` to `100` produced exactly
  zero student representation change and zero student attention.
- The corresponding target representation changed by a maximum absolute value
  of `2.088`, confirming that the target received the measured hidden gene.
- A measured-zero gene participated in attention, while the same gene marked
  unmeasured did not.
- Synthetic backward propagation reached the trainable gene identity
  embeddings, identity projection, and both linear layers of the shared value
  encoder.
- Static API and import audits found no donor, study, dataset/source, library,
  specimen, sample, cell-type, diagnosis, pathology, trajectory, graph,
  regulatory, spatial, perturbation, dose, or drug inputs.

### Mechanics parameter counts

| Component | Trainable parameters |
|---|---:|
| Gene tokenizer | 210,112 |
| Minimal Perceiver cross-attention encoder | 107,200 |
| Combined synthetic mechanics | 317,312 |

### Mechanics validation

- New synthetic mechanics tests: 18 passed.
- Existing Stage81A3 masking-calibration tests: 9 passed.
- Complete v4 test suite after implementation: 123 passed.
- Historical JEPA, graph-JEPA, non-graph-v3, and MIL model files were unchanged.
- Frozen Stage81A2 evidence files were unchanged.
- No files were staged, committed, or pushed during this bounded task.

The synthetic results validate the mechanics of Decisions 3 and 4 only. They
do not validate the full architecture, establish model performance, or provide
a biological result.

## Synthetic learning-mechanics validation

A subsequent bounded synthetic-only task tested Decision 5 predictor mechanics
and Decision 6 loss, stop-gradient, and representation-health mechanics. It did
not open RNA matrices, access pathology, create training shards, or train on
real data.

### Full encoder skeleton used for mechanics tests

The encoder skeleton follows the already locked v4A structure:

```text
gene tokenizer
-> one gene-token-to-latent cross-attention
-> latent Transformer block 1
-> latent Transformer block 2
-> final LayerNorm
-> [B, 24, 160]
```

Each latent block uses PreNorm, four-head self-attention, a residual connection,
PreNorm, a `160 -> 320 -> 160` GELU feed-forward network, dropout `0.10`, and a
second residual connection. No repeated gene cross-attention was added.

### Decision 5 lightweight predictor

The predictor accepts only the online/context latent array with shape
`[B, 24, 160]` and returns the same shape:

```text
LayerNorm
-> four-head self-attention across 24 slots
-> residual
-> LayerNorm
-> Linear 160 -> 320
-> GELU
-> Linear 320 -> 160
-> residual
```

It has no gene-level input, cross-attention to genes, metadata input, or
biological head. A nonuniform synthetic change to one input slot changed other
output slots by a maximum absolute value of `0.0712`, confirming cross-slot
interaction through self-attention.

| Component | Trainable parameters |
|---|---:|
| Lightweight predictor | 206,560 |
| Full encoder skeleton | 730,752 |
| Predictor / encoder ratio | 0.282668 |

The ratio is reported descriptively; no production ratio threshold was
introduced.

### Decision 6 primary JEPA loss

The primary synthetic loss is direct corresponding-slot raw-latent mean squared
error:

```text
L_jepa = mean((predicted_target - target_latents.detach())^2)
```

There is no Hungarian matching, learned slot matching, L2 normalization,
cosine-only objective, gene reconstruction, expression reconstruction, or
cell-type supervision. Tests confirmed zero loss for identical tensors,
positive loss for perturbations, direct slot correspondence, and ordinary MSE
scaling geometry.

### Target gradient firewall

A gradient-frozen copy of the online encoder was used only to test synthetic
stop-gradient behavior. No EMA decay or update schedule was defined.

| Gradient observation | Result |
|---|---:|
| Online encoder parameter tensors with gradients | 42 / 42 |
| Predictor parameter tensors with gradients | 12 / 12 |
| Target encoder parameter tensors with gradients | 0 / 42 |
| Target encoder tensors requiring gradients | 0 |
| Initial online-target maximum parameter difference | 0.0 |

### Variance-floor safeguard API

The variance-floor function operates on raw `[B,24,160]` latents and computes
per-slot, per-dimension standard deviation across cells:

```text
cross_cell_std = std(latents, dimension=cells)
penalty = weight * mean(relu(gamma - cross_cell_std))
```

Both `gamma` and `weight` are required call-site parameters without defaults.
They are unresolved policy values and are not attached to a production training
loop. With diagnostic-only `gamma=0.5` and `weight=2.0`, the healthy penalty was
`0`, complete-cell-collapse penalty was `1`, and slot-only-collapse penalty was
`0`. This demonstrates that slot diversity cannot rescue cell collapse and that
slot collapse is a separate failure mode.

### Representation-health definitions

Cell representations are flattened and centered across cells. Entropy-based
effective rank is:

```text
p_i = s_i / sum(s)
effective_rank = exp(-sum(p_i * log(p_i)))
```

Top singular-value fraction is:

```text
s_1^2 / sum(s_i^2)
```

The zero-centered-energy convention is a top fraction of `1.0`. Telemetry also
reports cross-cell standard deviation, the singular-value spectrum, latent norm
statistics, bounded pairwise-distance quantiles, within-cell slot variance,
average pairwise slot cosine similarity, context-target agreement, and
online-target parameter distance.

### Synthetic collapse observations

| Case | Cross-cell std | Effective rank | Top singular fraction | Median pair distance | Norm std | Slot variance | Slot cosine |
|---|---:|---:|---:|---:|---:|---:|---:|
| Healthy | 0.982 | 46.92 | 0.026 | 87.44 | 0.702 | 0.954 | 0.0001 |
| Partial/low-rank | 1.340 | 1.97 | 0.674 | 112.04 | 39.485 | 2.296 | -0.0024 |
| Complete cell collapse | 0 | 1.00 | 1.000 | 0 | 0.000008 | 0.969 | 0.0071 |
| Slot collapse only | 0.990 | 45.02 | 0.050 | 87.74 | 3.274 | 0 | 1.000 |
| Constant norm, diverse direction | 0.159 | 46.92 | 0.026 | 14.14 | 0.000001 | 0.025 | -0.0011 |

The complete-collapse effective rank is numerically one because floating-point
centering leaves a rank-one residual; its cross-cell standard deviation and
pairwise distances are exactly zero. The partial-collapse case shows that large
pairwise distances do not imply high-dimensional variation. The constant-norm
case shows that norm stability alone does not establish representation health.

### Learning-mechanics validation

- Decision 5/6 focused synthetic tests: 16 passed.
- Decision 3/4 focused synthetic tests after the extension: 18 passed.
- Existing masking-calibration tests: 9 passed.
- Complete v4 test suite after the extension: 136 passed.
- Predictor output was finite for batch sizes 1, 2, and 5.
- Predictor and online encoder gradients were present; target gradients were
  absent.
- Static import and API firewalls found no generic metadata input or active
  historical graph, pathology, trajectory, spatial, perturbation, or drug
  dependency.
- Historical model files and frozen Stage81A2 evidence remained unchanged.
- No files were staged, committed, or pushed during the bounded task.

One initial cross-slot fixture added a constant to every feature of one latent
slot. PreNorm correctly removed that uniform shift, so the fixture was replaced
with a nonuniform feature-direction perturbation. The corrected test measured
the intended cross-slot interaction and passed.

These results validate Decisions 5 and 6 mechanically. They do not establish
real-data learning performance, representation biology, a production variance
threshold, a variance-loss weight, or an EMA policy.

## Corrected historical-mechanics interpretation

### R03/R04 collapse chronology

Low effective dimensionality and top-singular dominance were not unresolved
failures across the entire historical lineage. The supported chronology is:

1. Early models developed collapsed or narrow representation geometry.
2. Variance regularization was found to operate after L2 normalization at an
   inappropriate representation scale.
3. The variance safeguard was moved to raw latents.
4. Later v2.2 Stage A training achieved broad, noncollapsed geometry.
5. Conservative downstream adaptation could preserve that broad geometry.
6. Aggressive downstream objectives could damage the geometry again.
7. Full-dataset geometry gates were then used to reject unsafe runs.

The corrected distinction is:

- **Foundation collapse-control principles were historically demonstrated in
  later v2.2.**
- **Robust geometry under every downstream optimization was not guaranteed and
  historically failed under aggressive objectives.**

This chronology does not establish an isolated causal benefit for any one EMA,
masking, variance, or covariance setting. It supports raw-latent safeguards and
full-dataset geometry gates as foundation-model requirements.

### Decision 5 predictor status

Decision 5 predictor mechanics are validated at the synthetic-mechanics level.
The validated contract is input/output shape `[B, 24, 160]`, one four-head
latent self-attention block, an FFN of `160 -> 320 -> 160`, cross-slot
interaction, finite outputs, predictor gradients, and a metadata-free API.
The predictor has 206,560 parameters versus 730,752 encoder parameters, giving
a predictor/encoder ratio of approximately 0.282668.

This is mechanics validation, not empirical biological validation.

### Decision 6 primary-loss status

Decision 6 primary JEPA-loss mechanics are validated as:

```text
L_JEPA = mean((predicted_target - target_latents.detach())^2)
```

The loss compares corresponding 24 target slots in raw, non-L2-normalized
latent space. It uses no Hungarian matching and no reconstruction objective.
Online-encoder and predictor gradients are present, while target gradients are
absent. The unresolved components are variance-floor gamma, variance-loss
weight, whether covariance should enter optimization, and numerical collapse
and checkpoint thresholds.

### Singular-spectrum definitions and policy

The historical and current top-singular metrics use different formulas:

```text
historical top_sv_ratio = s_1 / sum_i(s_i)
current top_singular_energy_fraction = s_1^2 / sum_i(s_i^2)
```

Historical values such as 0.056, 0.141, 0.394, and 0.481 are therefore not
numerically interchangeable with the current squared-energy fraction.

The recommended policy is to report both metrics under explicit names:

- `top_singular_l1_fraction = s_1 / sum_i(s_i)` for historical continuity;
- `top_singular_energy_fraction = s_1^2 / sum_i(s_i^2)` for explained-energy
  concentration.

This dual report preserves lineage comparability while retaining the more
conventional energy-concentration diagnostic. Its cost is additional reporting
complexity and the risk of threshold confusion. Thresholds must therefore be
metric-specific, and historical thresholds must never be transferred to the
energy fraction. This remains a recommendation requiring human approval, not a
frozen Stage81A3 policy.

Historical and current effective rank do use the same definition after
centering representations across cells:

```text
p_i = s_i / sum_i(s_i)
effective_rank = exp(-sum_i(p_i * log(p_i)))
```

Effective-rank values are thus more directly comparable in definition. Their
numerical thresholds still cannot be transferred blindly across architectures,
latent dimensionalities, slot structures, datasets, or evaluation populations.

## Comprehensive remaining-mechanics calibration

A final bounded Stage81A3 synthetic task tested the remaining mechanics that
could responsibly be evaluated before real foundation-model training. It used
only deterministic synthetic tensors and the existing compact pathology-blind
masking summaries. It did not reopen large RNA matrices, access pathology,
create training shards, select production hyperparameters, or start Stage81B.

The calibration artifact was written to
`results/v4/stage81a3_remaining_mechanics_calibration.json`. Its SHA-256 after
the final run was
`6d2da3ac73b99a5676256006a3db9329b4fb3611836ced387643b6093331dcbf`.

### EMA schedule behavior

EMA momentum is now a pure function of the zero-based global optimizer-update
index, total optimizer updates, start momentum, end momentum, and schedule
type. Fixed, linear, and cosine mechanics were tested without creating a
production default. Scheduled checkpoint/resume reproduced the momentum
sequence, online encoder, target encoder, predictor, optimizer state, and
global optimizer step exactly.

Four comparison schedules were stress-tested over smooth, noisy, oscillatory,
abrupt-shift, very-small-update, and occasional-large-update trajectories:

| Test-only schedule | Smooth target movement | Smooth final normalized lag | Abrupt-shift final normalized lag |
|---|---:|---:|---:|
| Fixed 0.996 | 0.08191 | 0.9590 | 0.9569 |
| Historical 0.992 -> 0.9995 | 0.06148 | 0.9693 | 0.9731 |
| Reference 0.996 -> 1.0 | 0.02768 | 0.9862 | 0.9885 |
| Earlier proposal 0.996 -> 0.9999 | 0.02905 | 0.9855 | 0.9877 |

All four were extremely stale under the deliberately short 20-update fixture.
Lower momentum followed the online trajectory faster; higher momentum reduced
target movement but increased lag. This comparison does not identify a
biologically optimal schedule or endpoint.

When momentum reached exactly `1.0` only on the final update, the only effect
was the final teacher state. With a pre-update online-target gap of 5, momentum
`0.9999` moved the target by `0.0005`, while momentum `1.0` did not move it.
There were no later updates on which this difference could propagate.

### Variance-formulation registry

Four raw-latent formulations were compared on healthy geometry, cell collapse,
slot collapse, combined collapse, low-rank geometry, constant-norm directional
diversity, rescaled healthy geometry, dominant-singular geometry, and noisy
small batches.

| Formulation | Cell collapse | Slot collapse | Both collapsed | Main limitation |
|---|---|---|---|---|
| Pooled cell | Detected | Missed | Detected | Healthy false penalties from slot-averaging scale |
| Per-slot cross-cell | Detected | Missed | Detected | Small-microbatch sampling noise |
| Flattened cell x slot | Largely missed | Missed | Detected | Within-cell slot diversity hides cell collapse |
| Combined pooled + per-slot | Detected | Missed | Detected | Inherits pooled scale sensitivity |

The per-slot cross-cell formulation is the cleanest synthetic candidate for a
cell-collapse safety rail, but it is not a complete geometry safeguard. It did
not detect slot-only collapse, low effective rank reliably, or one dominant
singular direction. These require separate telemetry.

At test-only `gamma=0.5`, the per-slot healthy penalty at physical batch eight
had mean `0.00366` and was nonzero in four of five seeds. It was zero in these
fixtures at batch sizes 16 and 256. The cell-collapse penalty remained `0.5`.
This shows that a differentiable variance estimate at microbatch eight is
noisier than an effective accumulated batch and must not be treated as a
simultaneous 256-cell estimate.

Gamma values `0.05`, `0.10`, `0.25`, `0.50`, and `1.00` were tested only to map
scale sensitivity. Gamma `1.0` penalized healthy synthetic geometry, while the
lower values separated the healthy fixture from near-collapse more cleanly.
No production gamma was selected.

Using the per-slot formulation at test-only `gamma=0.5`, a variance weight of
`0.1` produced a variance-to-JEPA gradient ratio of about `0.0032` for the
healthy fixture and `0.0495` near collapse. A weight of `1.0` increased those
ratios to about `0.0319` and `0.495`. These are synthetic scale diagnostics,
not production-weight evidence.

### Slot-collapse susceptibility

The actual 206,560-parameter latent predictor was optimized for 100 synthetic
steps against an explicitly slot-collapsed target. Its objective fell from
`1.00161` to `0.0000755`, and predicted within-cell slot variance fell from
`0.98691` to `0.0000361`.

This demonstrates that the predictor can express slot collapse when directly
trained to do so. It does not show that the proposed JEPA objective causes slot
collapse on real data and does not mechanically justify adding a slot-repulsion
loss. Slot variance and slot cosine similarity remain required telemetry.

### Covariance stability

Pooled and per-slot covariance estimates were strongly batch-size dependent.
At batch eight, their mean penalties were `0.1416` and `0.1434`; at batch 256,
they were approximately `0.00390`. Flattening cells and slots reduced apparent
variability, but treats within-cell slots as if they were independent samples.
All formulations increased on a fixture with deliberately correlated
dimensions.

The synthetic evidence therefore supports covariance as detached interval or
full-checkpoint telemetry. It does not support adding a covariance training
penalty at physical microbatch eight without further evidence.

### Masking implementation comparison

The existing real-data calibration used exact-count masking: for each cell, it
hid `floor(mask_fraction * measured_genes)` after a deterministic seeded
permutation. It did not use independent Bernoulli masking. Hidden genes were
always a subset of measured genes; measured zeros remained eligible, and
unmeasured genes were never reclassified as context-hidden.

At 40% masking with 20 measured genes, exact-count masking always hid eight.
Bernoulli masking hid between two and 15, with standard deviation `0.1094` in
realized fraction and a `26.7%` probability of hiding at least half. With 200
measured genes, Bernoulli masking hid 61 to 103, with a `0.3%` probability of
hiding at least half. Both rules were deterministic under the same explicit
key, but exact-count preserves the information-dose semantics of the completed
calibration. Changing to Bernoulli production masks would require explicit
justification or a recalibration bridge.

A stateless SHA-256-derived RNG key was mechanically validated from explicit
production seed, frozen cell index, sample pass, and view index. The same key
reproduced the same mask; changed pass or view produced a new mask; resume did
not alter future masks. No numerical production seed, refresh policy, or view
count was selected.

### Multi-seed, CUDA, and accumulation mechanics

Five explicit test-only seeds produced consistent finite values, parameter
counts, gradient routing, fixture classifications, masking behavior, EMA
updates, checkpoint/resume behavior, and mixed-precision mechanics. This shows
cheap synthetic mechanics stability only; it does not establish biological
multi-seed reproducibility.

The actual v4 dimensions passed a synthetic CUDA smoke test on the RTX 3080
Laptop GPU at physical microbatch eight: 4,096 genes, width 160, 24 slots, two
blocks, four heads, online encoder, target encoder, predictor, and fp16
autocast. Peak allocated memory was 168,117,248 bytes and peak reserved memory
was 213,909,504 bytes. Losses and gradients were finite and no OOM occurred.

Two accumulated microbatches produced one optimizer update and exactly one EMA
update. No EMA update occurred between microbatches. Mixed-precision unscale,
gradient handling, optimizer stepping, and post-step EMA ordering passed. This
validates accumulation mechanics, not a production clipping threshold or final
effective-batch policy.

### Checkpoint-health and future audit policy

Future pathology-blind training requires three telemetry levels:

- Step level: JEPA loss, gradient norms, non-finite counts, visible measured
  genes, EMA update norm, and optimizer-step behavior.
- Interval level: raw cross-cell variance, effective rank, full singular
  spectrum, both explicitly named top-singular fractions, pairwise distance,
  slot variance, slot cosine similarity, target variance, and normalized
  online-target distance.
- Full checkpoint audit: train/development donor consistency, source/study
  strata, broad-cell-class diagnostics, vulnerable sparse-cell strata,
  corresponding-slot geometry, and canonical pooled 160-dimensional geometry.

Development donors may support pathology-blind checkpoint assessment. Sealed
donors and pathology cannot be used for checkpoint or hyperparameter selection.
No numerical health threshold or composite score was frozen. Lowest JEPA loss
alone is insufficient, and pathology separation is forbidden as a checkpoint
criterion.

### Final comprehensive test state

- Remaining-policy focused tests: 15 passed.
- Complete v4 regression suite: 162 passed in 32.89 seconds.
- Reported warnings: zero.
- Reported failures: zero.
- Static firewall and historical-import-isolation checks passed.
- Protected unrelated files and frozen Stage81A2 evidence remained unchanged.
- No real RNA training, pathology access, training shards, staging, commit, or
  push occurred.

## Focused EMA-timescale and variance resolution

A subsequent small read/test-only task addressed only the remaining EMA
timescale and variance-safeguard questions. It used the actual v4 encoder,
target encoder, predictor, and JEPA loss with synthetic expression-like inputs.
It did not repeat masking calibration, covariance calibration, CUDA memory
testing, checkpoint/resume testing, or firewall testing.

The evidence artifact is
`results/v4/stage81a3_ema_variance_resolution.json`, with SHA-256
`15ea332ebe78b19f8aa5596a743bfc7493e78780105d554de2df8f1620d345aa`.

### Exact variance-formula audit

The current model-facing implementation is
`sea_ad_jepa.v4.losses.variance_floor_penalty`. For raw latents with shape
`[B,24,160]`, it computes:

```text
cross_cell_std = torch.std(latents, dim=0, unbiased=False)
unweighted = mean(relu(gamma - cross_cell_std))
weighted = weight * unweighted
```

The reduced dimension is the batch/cell dimension only. The resulting
standard-deviation array has shape `[24,160]`, preserving corresponding latent
slots and dimensions. `unbiased=False` is population standard deviation with
correction zero. No epsilon is added. Gamma is applied elementwise to raw
standard deviation before the mean reduction; weight is applied afterward.
There is no L2 normalization and no direct variance target.

The focused mathematical fixture used two cells with every slot/dimension equal
to zero in one cell and four in the other. Population standard deviation was
exactly two. With gamma three and weight 0.5, the weighted standard-deviation
hinge was exactly 0.5. A direct variance hinge was zero because variance was
four. This locks the intended mathematical distinction.

### Production-step and EMA-timescale audit

An exact Stage81C optimizer-update count cannot yet be calculated. The compute
contract freezes initial microbatch eight, effective batch 256, 32 implied
initial accumulation microbatches, one EMA update per successful optimizer
update, and a 300-step startup window belonging to the production trajectory.
Stage81A2 freezes 149 foundation-training donors and hierarchical sampling
weights, but explicitly does not freeze a loader implementation.

Two required training-length quantities remain unfrozen:

- the number of sampled or weighted cell exposures constituting one pass;
- the total number of foundation passes or epochs.

EMA memory half-lives in optimizer steps are:

| Momentum | Half-life |
|---:|---:|
| 0.992 | 86.30 |
| 0.996 | 172.94 |
| 0.99925 | 923.85 |
| 0.9995 | 1,385.95 |
| 0.9999 | 6,931.13 |

Their fractions of plausible production run lengths are:

| Momentum | 1,000 | 5,000 | 10,000 | 50,000 | 100,000 |
|---:|---:|---:|---:|---:|---:|
| 0.992 | 8.63% | 1.73% | 0.86% | 0.17% | 0.09% |
| 0.996 | 17.29% | 3.46% | 1.73% | 0.35% | 0.17% |
| 0.99925 | 92.38% | 18.48% | 9.24% | 1.85% | 0.92% |
| 0.9995 | 138.59% | 27.72% | 13.86% | 2.77% | 1.39% |
| 0.9999 | 693.11% | 138.62% | 69.31% | 13.86% | 6.93% |

Long-horizon deterministic trajectories compared fixed 0.99925, linear
0.996-to-1.0, and historical linear 0.992-to-0.9995. The table reports final
target lag and optimizer updates required for the isolated mid-run shift to
reach half response:

| Run steps | Fixed 0.99925 | Linear 0.996 -> 1.0 | Historical 0.992 -> 0.9995 |
|---:|---|---|---|
| 1,000 | lag 1.390; no half response | lag 1.203; no half response | lag 0.699; 196 steps |
| 5,000 | lag 0.414; 923 steps | lag 0.362; 374 steps | lag 0.155; 167 steps |
| 10,000 | lag 0.158; 923 steps | lag 0.205; 359 steps | lag 0.097; 165 steps |
| 50,000 | lag 0.032; 923 steps | lag 0.089; 348 steps | lag 0.033; 163 steps |
| 100,000 | lag 0.022; 923 steps | lag 0.063; 347 steps | lag 0.024; 162 steps |

None tracked almost immediately under the fixture definition, and none was
effectively frozen by the end. Fixed 0.99925 was smoothest but responded most
slowly; the historical schedule responded fastest and moved most; linear
0.996-to-1.0 was intermediate but accumulated greater final lag at long
horizons as momentum approached one. Without a frozen production horizon,
these are tradeoffs rather than a supported production winner.

### Actual-architecture variance stress test

The short synthetic stress used:

- the actual 4,096-vocabulary-compatible v4 encoder architecture, with 128
  measured synthetic gene inputs per bounded fixture;
- the actual EMA target, predictor, and corresponding-slot JEPA loss;
- physical batch eight;
- refreshed 40% exact-count measured-gene masking, one view per pass;
- five explicit test-only seeds;
- healthy structured and collapse-prone low-rank expression-like fixtures;
- 20 optimizer updates per fixture and regime;
- test-only fixed EMA momentum 0.996;
- either JEPA alone or JEPA plus per-slot raw-standard-deviation floor with
  test-only gamma 0.10 and weight 0.10.

The weak safeguard raised final cross-cell standard deviation in all five seeds
for both fixture types. In collapse-prone fixtures, mean cross-cell standard
deviation changed from `0.01797` to `0.01860`. However, effective rank changed
from `6.6851` to `6.6810`, and top-singular energy fraction changed from
`0.28993` to `0.29121`; neither metric improved in any seed. The mean JEPA loss
changed only from `0.012268` to `0.012308`.

In healthy fixtures, the safeguard produced a larger cross-cell-standard-
deviation change, from `0.03109` to `0.03374`, while effective rank decreased
from `5.9132` to `5.8278` and top-singular energy concentration increased from
`0.58591` to `0.60545`. Thus the effect was not selective to the
collapse-prone trajectory.

All runs had finite losses and gradients, with zero nonfinite events. The
JEPA-only collapse-prone trajectories did not show gross progressive collapse
within the deliberately short test. Consequently, this experiment did not
demonstrate that the weak training safeguard protected a collapse-prone
trajectory while leaving healthy geometry broadly unchanged. Increasing the
penalty merely to force a positive result would be an unjustified synthetic
hyperparameter search.

The current recommendation is therefore to retain per-slot raw-standard-
deviation and broader geometry measures as telemetry, without adding the
tested variance term to the production loss. The formula itself is correct;
the evidence for using it as a training objective is insufficient.

### Focused resolution test state

- Exact variance-formula fixture: passed.
- Complete v4 regression suite: 163 passed in 33.33 seconds.
- Reported warnings: zero.
- Reported failures: zero.
- No frozen Stage81A2 evidence changed.
- No real RNA training, pathology access, Stage81B work, staging, commit, or
  push occurred.

## Stage81C exposure-budget audit

A subsequent terminal-only audit examined how many sampled-cell exposures and
optimizer updates could constitute a scientifically reasonable single
production trajectory. It read only frozen Stage81A2 manifests, the locked
compute contract, and historical project records. It did not construct a
loader, train a model, access pathology, create Stage81B shards, modify frozen
evidence, or freeze a training budget.

Repository provenance was verified before the audit. Branch `main`, local
HEAD, and `origin/main` all resolved to
`808ce4f170055c5568cc5c1e0e3a56415b52f908`. The pre-existing modified and
untracked working tree was preserved.

### Frozen exposure universe and availability boundary

Stage81A2 freezes 149 foundation-training donors:

| Source | Train donors | Frozen source-cell evidence | Exact train cells available in A2 |
|---|---:|---:|---:|
| HVS | 62 | 379,330 | 308,499 |
| NPH Ctrl | 19 | 957,659 source; 892,828 annotated across all NPH cohorts | Not available by train cohort |
| SEA-AD | 68 | 6,959,264 across 11 matrices | Not available by train donor |

The exact HVS training-cell composition is 79,585 GABAergic neuronal,
155,567 glutamatergic neuronal, and 73,347 non-neuronal/non-neural cells. HVS
train donors contain 1,625 to 12,509 cells, with median 4,572.5. The frozen HVS
resolution contains 1,424 train partition-by-donor-by-class rows, ranging from
1 to 2,819 cells with median 89.

NPH frozen annotated counts across all NPH cohorts are 73,487 Astro, 22,407
Endo, 222,449 ExN, 83,702 InN, 59,624 MG, 396,292 Oligo, and 34,867 OPC cells.
These counts are not partitioned into the 19 NPH Ctrl training donors in the
frozen A2 evidence. SEA-AD training-donor and broad-class cell counts are also
not frozen. Therefore the exact global number of eligible training cells is
not yet available.

### Frozen sampling semantics versus missing loader semantics

The frozen hierarchy is:

```text
tissue state -> study/source -> donor -> broad cell class -> cell
```

The source rule is inverse training-donor count renormalized across tissue
state and then study. Donors are uniform within source. Broad classes use
inverse available-class frequency with an exposure cap. Pathology and sealed
donors are forbidden.

Stage81A2 explicitly states that these are weighting rules rather than a loader
implementation. The following remain unspecified:

- normalized source-selection probabilities;
- numerical broad-class exposure caps;
- cell-selection mechanics;
- sampling with or without replacement;
- sampled exposures constituting one pass.

A conventional epoch therefore does not yet mean that every eligible cell is
visited exactly once. The transparent diagnostic definition is:

```text
exposure_equivalent_passes = total_sampled_cell_draws / total_eligible_train_cells
```

This quantity cannot yet be calculated because the global train-cell
denominator is absent. Even after it becomes calculable, it will not prove that
every cell was observed that many times. Conditional on source-selection
probability `p_s`, expected exposure per donor would be `draws * p_s / 62` for
HVS, `draws * p_s / 19` for NPH Ctrl, and `draws * p_s / 68` for SEA-AD.

### Candidate update budgets

One optimizer update is one actual student update after accumulating an
effective batch of 256. EMA updates exactly once per optimizer update.

| Optimizer updates | Sampled-cell draws | Global exposure-equivalent passes |
|---:|---:|---:|
| 4,000 | 1,024,000 | Unavailable until the train-cell denominator is frozen |
| 5,000 | 1,280,000 | Unavailable until the train-cell denominator is frozen |
| 6,000 | 1,536,000 | Unavailable until the train-cell denominator is frozen |
| 8,000 | 2,048,000 | Unavailable until the train-cell denominator is frozen |
| 10,000 | 2,560,000 | Unavailable until the train-cell denominator is frozen |

Expected source, donor, class, and source-by-class exposure distributions and
low-exposure risks cannot be calculated without normalized source
probabilities, a class cap, and replacement semantics. It is likewise unknown
when additional updates would mainly repeat already well-sampled strata.

### Historical v2.2 optimizer-update chronology

The historical `v2_2_topology_dropout_full_e50_fast` run was verified locally
as 40,000 cells, batch size 256, and 50 epochs. Its PyTorch DataLoader retained
the final partial batch, giving `ceil(40000 / 256) = 157` optimizer updates per
epoch.

| Epoch | Optimizer updates | Loss | Effective dimensions | Historical top-singular L1 fraction |
|---:|---:|---:|---:|---:|
| 5 | 785 | 0.005388 | 52.63 | 0.131 |
| 10 | 1,570 | 0.005284 | 59.76 | 0.076 |
| 20 | 3,140 | 0.005513 | 63.39 | 0.064 |
| 30 | 4,710 | 0.006109 | 65.67 | 0.056 |
| 35 | 5,495 | 0.006593 | 65.54 | 0.052 |
| 40 | 6,280 | 0.007242 | 64.98 | 0.064 |
| 45 | 7,065 | 0.008089 | 59.31 | 0.096 |
| 50 | 7,850 | 0.009155 | 52.52 | 0.151 |

Geometry matured around 4,700 to 5,500 updates. The best raw epoch under the
historical geometry ranking was epoch 32, or 5,024 updates; epoch 30 was the
best saved five-epoch checkpoint. Geometry plateaued through roughly 6,000
updates, began degrading around 6,280, and degraded clearly by 7,065 to 7,850.

The loss bottomed near epoch 8, approximately 1,256 updates, well before
geometry matured. This is direct historical evidence that lowest JEPA loss
alone is not an acceptable checkpoint criterion. The v2.2 timing is prior
evidence only and does not determine v4 duration because the architecture,
sources, sampling scheme, and exposure universe differ.

Historical foundation evidence also records that moving variance protection to
raw latents improved collapse control. Secondary downstream evidence showed
that aggressive objectives could damage previously broad geometry. A separate
20-step diagnostic reported effective dimensions 75.51 while full-data
evaluation found 40.62 with top-singular ratio 0.268, demonstrating that short
telemetry cannot approve a checkpoint. Downstream pathology performance was
not used to recommend a v4 duration.

### EMA memory across candidate budgets

| Momentum | Half-life, updates | 4k budget | 5k | 6k | 8k | 10k |
|---:|---:|---:|---:|---:|---:|---:|
| 0.996 | 172.94 | 4.3% | 3.5% | 2.9% | 2.2% | 1.7% |
| 0.99925 | 923.85 | 23.1% | 18.5% | 15.4% | 11.5% | 9.2% |
| 0.9995 | 1,385.95 | 34.6% | 27.7% | 23.1% | 17.3% | 13.9% |

Momentum 0.996 would follow comparatively quickly. Fixed 0.99925 and 0.9995
retain substantial memory while still receiving multiple half-lives over the
candidate horizons. The mechanically tested linear 0.996-to-1.0 schedule
becomes increasingly lagged near its endpoint. No EMA schedule was selected
because the production update budget and exposure contract remain unfrozen.

### Proposed pathology-blind audit cadence

- Every optimizer step: JEPA loss, gradients, nonfinite counts, visible-gene
  counts, optimizer behavior, and EMA update norm.
- Step 300: locked startup hard gate, atomic checkpoint, and bounded geometry
  check. This is part of the production trajectory, not a disposable pilot.
- Step 1,000: first full train/development pathology-blind geometry audit.
- Step 2,000: interval geometry evaluation and atomic checkpoint.
- Steps 4,000, 6,000, and 8,000: full train/development audits and atomic
  checkpoints.
- Step 10,000: only if explicitly selected in advance as the maximum budget.

Full audits must include effective rank, both named top-singular metrics,
cross-cell variance/std, cell distances, slot variance, slot cosine, EMA
online-target distance, target latent variance, source strata, broad-class
strata, sparse/vulnerable strata, and train-versus-development consistency.
Sealed donors cannot participate in checkpoint selection.

The stopping principle is to predeclare a maximum update budget, stop early
only for predefined hard failures such as nonfinite values or unmistakable
collapse, preserve intermediate checkpoints, and select using predeclared
pathology-blind geometry and stability rules. Lowest loss, pathology
separation, and post-hoc seed selection are forbidden.

### Provisional budget recommendation

The preferred main learning window is 4,000 to 6,000 optimizer updates, with a
proposed maximum of 8,000 updates. The reasoning is that historical geometry
matured near 5,000 updates and degraded after approximately 6,300 to 7,000,
while v4 is larger and more heterogeneous and therefore requires room for
later maturation and direct full-audit evidence.

Confidence is moderate-low. Human judgment remains required for the maximum
budget, normalized source probabilities, replacement semantics, class exposure
cap, definition of a pass, and EMA schedule. The recommendation is not frozen
and cannot become operational until the Stage81B loader makes exposure
accounting auditable.

**STAGE81A3 TRAINING-BUDGET DECISION NOT YET FROZEN**

## Real-RNA forward-only mechanics smoke

After the synthetic mechanics suite passed, Stage81A3 performed one bounded
real-RNA forward-only smoke. This was the first v4 architecture execution on
actual foundation RNA, but it contained no optimizer, backward call, EMA
update, checkpoint selection, pathology access, or learning.

Source artifacts:

- `scripts/v4/stage81a3_real_rna_forward_smoke.py`
- `results/v4/stage81a3_real_rna_forward_smoke.json`
- `results/v4/stage81a3_real_rna_forward_smoke_cells.csv`

### Exact pathology-blind sample

The deterministic pre-model selector produced 502 foundation-training cells:

| Source | Cells | Source-qualified train donors represented |
|---|---:|---:|
| HVS | 128 | 54 |
| NPH52 Ctrl | 246 | 19 |
| SEA-AD | 128 | 36 |
| **Total** | **502** | **109** |

The sample contained 165 sparse, 178 middle, and 159 dense cells. Detected
genes ranged from 323 to 3,999, with median 2,073. It included excitatory and
inhibitory neurons, oligodendrocytes, astrocytes, microglial/myeloid cells,
endothelial/vascular cells, OPCs, and other available non-neuronal classes.
Selection occurred before model initialization and did not use model outputs.

### Normalization and vocabulary verification

HVS values came from integer counts in `raw/X`; SEA-AD values came from integer
UMIs in `layers/UMIs`; NPH used the bounded compact cache reproduced from raw
counts. Every source followed per-cell library-size normalization to 10,000
followed by `log1p` exactly once. The NPH cache reproduced this transformation
to maximum absolute difference `5.33e-15`. All values were finite.

The exact 4,096-gene frozen order and semantic hash were reverified. All 4,096
selected vocabulary genes were measured in each represented source contract,
so this particular sample contained no actual unmeasured vocabulary position.
Measured zeros remained valid measured values.

### Mask and forward mechanics

Every cell used an exact-count 40% measured-gene context mask. Exactly 1,638 of
4,096 measured genes were hidden and 2,458 remained visible, giving realized
fraction `0.39990234375`. Visible detected genes ranged from 191 to 2,400, with
median 1,235.5.

The actual online encoder, exact-copy EMA target, and predictor ran in
evaluation mode under CUDA fp16 autocast with physical microbatch eight. All
online, target, predictor, and diagnostic-loss tensors were finite, with zero
NaNs and zero infinities. The detached initialization JEPA MSE had median
`0.219975` and range `0.213748-0.226420`. This is an initialization diagnostic,
not learned performance.

Two legal 40% masks on 32 cells produced median context-representation cosine
`0.999288` and median L2 distance `0.47518`. Perturbing intentionally hidden
measured values changed the student representation by exactly zero. An
in-memory synthetic unmeasured-placeholder extension also changed the
representation by zero. All four bounded measured-zero checks passed.

The online full-view and exact-copy target outputs matched with maximum absolute
difference zero. Online, target, and predictor parameter changes were all zero.
Peak CUDA allocation was 312,226,816 bytes and peak reservation was 513,802,240
bytes. No OOM occurred.

### Initialization geometry observed in the smoke

The untrained EMA-target arithmetic-mean embedding had:

- effective rank `3.2241`;
- top-singular L1 fraction `0.7682`;
- top-singular energy fraction `0.9823`;
- mean cross-cell standard deviation `0.06968`;
- median pairwise distance `0.9822`.

Final slots had mean within-cell slot variance `0.009336`, mean slot cosine
`0.990258`, and median corresponding-slot effective rank `3.5623`. These values
were unexpectedly narrow, but they occurred before learning and therefore were
not training collapse. They triggered the forensic audit below rather than an
architecture change.

The complete post-smoke v4 suite passed: 163 tests, zero failures, and zero
warnings. No Stage81A2 evidence changed.

## Real-RNA initialization-geometry forensic audit

The forensic task reused the exact same 502 cells, donor identities,
normalization, measurement masks, and 4,096-gene order. It instrumented the
actual evaluation-mode modules without changing their mathematical behavior.
The traced final output matched the ordinary encoder with maximum absolute
difference zero.

Source artifacts:

- `scripts/v4/stage81a3_diagnose_initialization_geometry.py`
- `results/v4/stage81a3_initialization_geometry_diagnostic.json`
- `results/v4/stage81a3_initialization_geometry_stages.csv`

### Input and random-projection baselines

The centered normalized 502 by 4,096 RNA matrix was broad:

| Metric | Normalized RNA input | Five random 4096-to-160 projections |
|---|---:|---:|
| Effective rank | 442.84 | 140.32-141.30 |
| Top-singular L1 fraction | 0.0187 | 0.0321-0.0369 |
| Top-singular energy fraction | 0.1250 | 0.1236-0.1590 |
| Median pairwise distance | 56.67 | 11.07-11.38 |

The input top 1, 5, and 10 singular values accounted for 12.50%, 25.63%, and
32.32% of energy. Neither the input RNA nor ordinary random compression explains
an effective rank near three.

### Actual stage trace

The real computation order is:

```text
identity_projection(gene_embedding) + shared_value_MLP(expression)
-> tokenizer LayerNorm
-> learned queries plus gene-token cross-attention
-> cross-attention output LayerNorm
-> latent block 1
-> latent block 2
-> final encoder LayerNorm
-> arithmetic mean over 24 slots
```

The primary cell-summary trace was:

| Stage | Effective rank | Top energy fraction | Cross-cell SD | Median pairwise distance |
|---|---:|---:|---:|---:|
| Normalized RNA input | 442.84 | 0.1250 | 0.59161 | 56.67 |
| Expression-value contribution mean | 1.85 | 0.9649 | 0.01686 | 0.2443 |
| Fused-token mean before tokenizer LayerNorm | 1.87 | 0.9649 | 0.01686 | 0.2443 |
| Token mean after tokenizer LayerNorm | 3.22 | 0.9788 | 0.02775 | 0.4020 |
| Cross-attention after output LayerNorm | 3.22 | 0.9816 | 0.07319 | 1.0322 |
| After latent block 1 | 3.25 | 0.9800 | 0.08026 | 1.1373 |
| After latent block 2, before final LayerNorm | 3.25 | 0.9814 | 0.08866 | 1.2421 |
| Final slots after LayerNorm, mean pooled | 3.22 | 0.9823 | 0.06968 | 0.9822 |

The arithmetic token mean is a diagnostic summary rather than learned pooling.
Its agreement with the nearly uniform cross-attention result localizes the
initialization tendency without proving that the full token tensor has lost all
information.

Tokenizer LayerNorm increased effective rank from `1.87` to `3.22`.
Cross-attention output LayerNorm increased it from `2.90` to `3.22`. The two
latent blocks changed it only from `3.22` to approximately `3.25`, and final
LayerNorm changed `3.25` to `3.22`. LayerNorm and latent blocks were therefore
not the primary source of narrowing.

### Identity, expression, and attention localization

Median identity-contribution norm was `7.33`; median expression-value norm was
`2.52`, giving ratio `2.91`. The identity contribution is invariant across
cells. Identity-only zero-expression cells produced zero pairwise distance.
Expression-only final geometry was itself narrower, with effective rank `1.91`
and top energy fraction `0.9887`. Identity has the larger absolute scale, but
its magnitude alone does not explain the low-dimensional cell-varying geometry.

Cross-attention initialized almost uniformly. Median normalized attention
entropy was `0.999995`; median between-slot attention-map cosine was `0.999980`;
mean cross-cell attention-map variance was `4.0e-14`. Thus cross-attention
propagates an average-like narrow token summary and initializes highly similar
slot attention profiles. No full attention tensor was persisted.

### Counterfactual and pooling controls

Per-gene across-cell permutation preserved gene marginal distributions while
destroying each cell's multigene pattern. It raised final effective rank to
`24.28` but reduced median pairwise distance from `0.982` to `0.089`. Genuine
cell-level covariance therefore drives the strong dominant real-data axis,
while architectural initialization constrains how that covariance is represented.

Flattened final slots had effective rank `4.71`; arithmetic mean pooling reduced
this to `3.22`. Top-energy fraction changed by only `0.000038`, and flattened-
versus-mean pairwise-distance correlation was `0.999999999`. Mean pooling adds
secondary rank narrowing but does not create the dominant axis.

### Multi-initialization and strata

Five explicit test-only initialization seeds were evaluated without selection:

- pooled effective rank: `3.22-4.40`;
- top-singular energy fraction: `0.947-0.982`;
- mean slot cosine: `0.981-0.990`;
- mean slot variance: `0.00934-0.01785`.

All five were narrow, supporting a structural initialization tendency rather
than one unlucky seed. The production seed remains unresolved.

Every source began broad and converged to narrow final geometry:

| Source | Input effective rank | Final effective rank | Final top energy fraction |
|---|---:|---:|---:|
| HVS | 118.80 | 3.31 | 0.984 |
| NPH52 | 218.77 | 3.02 | 0.985 |
| SEA-AD | 116.58 | 3.16 | 0.979 |

Dense, middle, and sparse final ranks were `4.98`, `4.94`, and `3.61`.
Sparsity contributes to severity but does not explain the global effect. Major
broad-class final ranks ranged from approximately `1.60` to `3.20`; no single
source or class was responsible.

### Forensic interpretation and boundary

Quantitatively supported classifications are:

- `TOKENIZER-FUSION NARROWNESS`, specifically the scalar value-path/token-
  summary geometry at random initialization;
- `CROSS-ATTENTION NARROWNESS`, with nearly uniform and nearly identical slot
  attention maps, while preserving rather than creating most pooled rank loss;
- `MEAN-POOLING NARROWNESS`, as a secondary effect;
- `STRUCTURAL MULTI-SEED INITIALIZATION NARROWNESS`;
- `NO SINGLE DOMINANT SOURCE IDENTIFIED`.

Input-dominated narrowness, latent-block narrowness, LayerNorm-associated
narrowness, and a single-seed accident are not supported as primary
explanations.

The mechanism is localized, but a forward-only audit cannot establish whether
trainable tokenizer and attention weights can escape it. The evidence does not
yet justify changing architecture. A separately approved bounded synthetic
learnability/geometry-escape diagnostic is required before Stage81A3 freeze.

Across the baseline, controls, and all five initialization seeds, online,
target, and predictor parameter differences were exactly zero. Optimizer steps,
EMA updates, and backward calls were zero. The final full v4 suite passed 163
tests in 37.82 seconds with zero warnings and zero failures.

**INITIALIZATION GEOMETRY REQUIRES FURTHER DIAGNOSTIC**

## Descriptive interpretation

Moving from 40% to 50% masking reduces median retained transformed-expression
signal by approximately ten percentage points across strata. The visible-gene
consequences are heterogeneous. Neuronal populations generally retain larger
visible contexts. Microglial, oligodendrocyte, vascular, and broad
non-neuronal populations show larger low-information tails. Endothelial and
VLMC populations already have low fifth-percentile visible-gene counts at 40%
masking.

These observations are descriptive calibration results. They do not establish
an approved masking fraction or architecture setting.

**STAGE81A0 DESIGN AND FAILURE REGISTRY = FROZEN**

**STAGE81A1 MULTIMODAL INVENTORY = COMPLETE**

**STAGE81A1B SEA-AD ACQUISITION AND REGULATORY PRESERVATION = COMPLETE**

**STAGE81A1C NORMAL-REFERENCE AND PERTURBATION ACQUISITION = COMPLETE**

**STAGE81A1D LIVING-HUMAN BRIDGE = COMPLETE**

**STAGE81A2 CANONICAL DATA/VOCABULARY/SPLIT CONTRACT = FROZEN**

**DECISION 3 VISIBILITY MECHANICS = VALIDATED**

**DECISION 4 TOKENIZATION MECHANICS = VALIDATED**

**DECISION 5 PREDICTOR MECHANICS = VALIDATED**

**DECISION 6 PRIMARY LOSS/COLLAPSE-METRIC MECHANICS = VALIDATED**

**FOUNDATION COLLAPSE CONTROL PRINCIPLES = HISTORICALLY SUPPORTED**

**EMA UPDATE/SCHEDULE/RESUME MECHANICS = VALIDATED**

**MASK RNG MECHANICS = VALIDATED**

**CUDA MICROBATCH 8 MECHANICS = VALIDATED**

**GRADIENT ACCUMULATION MECHANICS = VALIDATED**

**REAL-RNA FORWARD MECHANICS = VALIDATED**

**REAL-RNA INITIALIZATION GEOMETRY = NARROW AND EXPLAINED LOCALLY, BUT REQUIRES FURTHER DIAGNOSTIC**

**ARCHITECTURE CHANGE FROM CURRENT FORENSIC EVIDENCE = NOT JUSTIFIED**

**VARIANCE GAMMA = UNRESOLVED**

**VARIANCE LOSS WEIGHT = UNRESOLVED**

**VARIANCE TRAINING SAFEGUARD = TELEMETRY ONLY AT CURRENT EVIDENCE**

**COVARIANCE TRAINING PENALTY = TELEMETRY ONLY**

**TOP-SINGULAR METRIC POLICY = HUMAN DECISION REQUIRED**

**EMA SCHEDULE = UNRESOLVED**

**MASKING RECOMMENDATION = 40% EXACT-COUNT, REFRESHED, ONE VIEW PER PASS**

**PRODUCTION SEED POLICY = ONE PREDECLARED SEED, NO SEED RESELECTION**

**PRODUCTION SEED NUMERIC VALUE = UNRESOLVED**

**CHECKPOINT-HEALTH NUMERICAL THRESHOLDS = UNRESOLVED**

**STAGE81A3 ARCHITECTURE INCOMPLETE**

**STAGE81B NOT STARTED**

**PATHOLOGY NOT OPENED**

**NO REAL-DATA MODEL TRAINING PERFORMED**

## Stage81A3 synthetic geometry-escape / learnability diagnostic

### Why this diagnostic was run

The earlier pathology-blind real-RNA forward audit showed that broad normalized
RNA geometry (effective rank 442.84) and a broad random 4096-to-160 projection
(effective rank approximately 140-141) became a narrow untrained v4 pooled
representation (effective rank approximately 3.22-4.40, top singular energy
approximately 0.947-0.982). That result localized a strong initialization
tendency but did not establish whether the unchanged JEPA could learn its way
out of it.

This follow-up therefore used synthetic data only. No real RNA was reopened,
no pathology was accessed, and no production training was performed.

### Synthetic evidence design

- Two deterministic fixtures were generated, each with 8,192 cells, 4,096
  measured genes, and 32 evaluation-only latent factors.
- Each factor affected a distinct, partially overlapping 224-gene module with
  a stride of 128 genes.
- Counts were nonnegative and sparse, with heterogeneous simulated library
  sizes and measured zeros. They were normalized per cell to 10,000 and then
  transformed with `log1p`.
- `balanced_multifactor` used independent factors.
- `dominant_axis_multifactor` correlated the secondary factors with the first
  factor and multiplied the first loading amplitude by 2.25, while retaining
  genuine multifactor structure.
- The known factors were used only in a fixed held-out linear ridge readout.
  They were never supplied to the encoder or predictor and never entered the
  training objective.
- Five predeclared test-only initialization seeds were retained without
  selection: 8114001, 8114002, 8114003, 8114004, and 8114005.

The full synthetic fixtures were broad enough to test learnability:

| Fixture | Nonzero fraction | Input effective rank | Input top singular energy | Raw-expression factor R2 | Random-projection rank | Random-projection factor R2 |
|---|---:|---:|---:|---:|---:|---:|
| balanced_multifactor | 0.641 | 241.72 | 0.0252 | 0.856 | 139.04 | -0.290 |
| dominant_axis_multifactor | 0.624 | 240.12 | 0.0517 | 0.858 | 137.98 | -0.272 |

The random projection retained broad geometry but not held-out linear factor
recovery under this bounded readout. This is itself a useful warning that high
effective rank is not sufficient evidence of meaningful factor retention. The
raw normalized expression did retain the generating structure strongly.

### Exact test mechanics

- The model was unchanged: 4,096 genes, 48-dimensional gene identity, width
  160, 24 latent slots, two latent blocks, four heads, dropout 0.10, and the
  validated latent predictor.
- The only optimized loss was
  `mean((predicted_target - target_latents.detach()) ** 2)`.
- Variance, covariance, contrastive, reconstruction, supervised, and
  biological auxiliary loss weights were all zero.
- Every use applied deterministic 40% exact-count masking over measured genes.
- Physical microbatch was 8, effective batch was 256, and gradient
  accumulation was 32 microbatches.
- CUDA fp16 mixed precision was used.
- The single test-only optimizer setting was AdamW with learning rate 1e-4,
  weight decay 0.01, and no gradient clipping. It is not a production
  hyperparameter.
- Fixed test-only EMA momentum was 0.99925. Exactly one EMA update followed
  every successful optimizer update.
- Checkpoints were evaluated at optimizer steps 0, 20, 50, 100, 200, 300, and
  500. No run was extended to 1,000 because the five-seed result was not
  ambiguous.

### Mean trajectories across five seeds

Balanced multifactor:

| Step | JEPA diagnostic loss | Target effective rank | Target top singular energy | Target factor R2 | Online effective rank | Slot cosine | Slot variance |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.221219 | 4.676 | 0.988388 | -0.140 | 4.676 | 0.990869 | 0.008750 |
| 20 | 0.007405 | 4.677 | 0.988390 | -0.140 | 4.661 | 0.990892 | 0.008729 |
| 50 | 0.001818 | 4.671 | 0.988428 | -0.149 | 4.328 | 0.990995 | 0.008630 |
| 100 | 0.000953 | 4.648 | 0.988530 | -0.139 | 3.983 | 0.991133 | 0.008498 |
| 200 | 0.000578 | 4.589 | 0.988763 | -0.138 | 3.814 | 0.991255 | 0.008381 |
| 300 | 0.000434 | 4.519 | 0.989012 | -0.131 | 3.680 | 0.991298 | 0.008339 |
| 500 | 0.000304 | 4.361 | 0.989568 | -0.125 | 3.445 | 0.991309 | 0.008328 |

Dominant-axis multifactor:

| Step | JEPA diagnostic loss | Target effective rank | Target top singular energy | Target factor R2 | Online effective rank | Slot cosine | Slot variance |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.221171 | 4.855 | 0.987252 | -0.079 | 4.855 | 0.990747 | 0.008868 |
| 20 | 0.007369 | 4.854 | 0.987256 | -0.086 | 4.835 | 0.990769 | 0.008846 |
| 50 | 0.001794 | 4.849 | 0.987292 | -0.077 | 4.482 | 0.990874 | 0.008746 |
| 100 | 0.000929 | 4.826 | 0.987412 | -0.075 | 4.125 | 0.991012 | 0.008613 |
| 200 | 0.000573 | 4.761 | 0.987686 | -0.084 | 3.960 | 0.991135 | 0.008496 |
| 300 | 0.000432 | 4.688 | 0.987982 | -0.063 | 3.821 | 0.991178 | 0.008454 |
| 500 | 0.000302 | 4.528 | 0.988637 | -0.071 | 3.576 | 0.991188 | 0.008444 |

### Per-seed outcome at step 500

| Fixture | Seed | Target rank, step 0 | Target rank, step 500 | Online rank, step 500 | Target factor R2, step 500 | Nonfinite events |
|---|---:|---:|---:|---:|---:|---:|
| balanced | 8114001 | 4.767 | 4.423 | 3.499 | -0.119 | 0 |
| balanced | 8114002 | 4.823 | 4.410 | 3.362 | -0.135 | 0 |
| balanced | 8114003 | 6.500 | 6.121 | 4.753 | -0.250 | 0 |
| balanced | 8114004 | 3.054 | 2.887 | 2.447 | -0.074 | 0 |
| balanced | 8114005 | 4.238 | 3.962 | 3.166 | -0.047 | 0 |
| dominant axis | 8114001 | 4.926 | 4.565 | 3.602 | -0.061 | 0 |
| dominant axis | 8114002 | 5.021 | 4.595 | 3.507 | -0.061 | 0 |
| dominant axis | 8114003 | 6.676 | 6.288 | 4.889 | -0.170 | 0 |
| dominant axis | 8114004 | 3.176 | 3.004 | 2.537 | 0.007 | 0 |
| dominant axis | 8114005 | 4.478 | 4.191 | 3.343 | -0.071 | 0 |

Every target effective-rank trajectory ended below its own initialization, and
every target top-singular-energy fraction ended above its initialization. No
seed was discarded. The maximum final target mean factor R2 was only 0.0071,
whereas the two raw-expression references were approximately 0.856 and 0.858.

### Tokenizer, attention, and slot trajectory

The bounded stage trace remained narrow and became slightly narrower. Averaged
across seeds, balanced-fixture rank moved as follows from step 0 to 500:

- fused token summary: 1.396 to 1.396;
- token summary after LayerNorm: 2.962 to 2.956;
- cross-attention output: 3.767 to 3.663;
- after latent block 1: 3.775 to 3.622;
- after latent block 2: 3.673 to 3.494;
- final pooled slots: 3.688 to 3.475.

The dominant-axis fixture showed the same direction. Cross-attention remained
nearly uniform: mean median normalized entropy was approximately 0.999996 at
step 0 and 0.999995 at step 500; between-slot attention-map cosine changed
only from approximately 0.999981 to 0.999977. Cross-cell attention-map
variance remained around 1e-13. Slot cosine increased slightly while slot
variance and median per-slot effective rank decreased.

### Optimizer, gradient, and EMA health

The diagnostic completed 5,000 successful synthetic optimizer updates and
5,000 matched EMA updates. There were zero nonfinite events. Gradients were
finite throughout. Mean gradient norm declined with loss, from approximately
0.895 over steps 1-20 to approximately 0.0166 over steps 301-500. Mean EMA
target-update norm rose from approximately 3.06e-4 to 1.84e-3 while the
online-target distance increased to approximately 2.70. These observations
show that both optimizer and EMA mechanics were active; they do not explain
the result as a frozen teacher or a skipped-update failure.

### Scientific interpretation

The primary JEPA objective learned an increasingly easy prediction while the
cell geometry became narrower, slot similarity increased, attention remained
almost uniform, and held-out synthetic factor recovery remained absent. This
is the exact failure mode the diagnostic was designed to distinguish from
mere loss improvement.

The completed evidence is classified:

**C. GEOMETRY REMAINS TRAPPED**

**CURRENT ARCHITECTURE SHOWS SYNTHETIC GEOMETRY-ESCAPE FAILURE**

This is synthetic mechanics evidence, not a claim that JEPA as a general
method cannot work and not a biological validation result. It does mean the
current unchanged v4 tokenizer/cross-attention/pooling path and primary loss
should not proceed automatically to real-RNA optimization. Architecture
redesign remains a separate human decision and was not performed here.

Compact evidence files:

- `scripts/v4/stage81a3_synthetic_geometry_escape.py`
- `results/v4/stage81a3_synthetic_geometry_escape.json`
- `results/v4/stage81a3_synthetic_geometry_escape_trajectory.csv`

**SYNTHETIC GEOMETRY REMAINS TRAPPED**

**REAL-RNA OPTIMIZER STEPS PERFORMED: 0**

**REAL-RNA EMA UPDATES PERFORMED: 0**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**SYNTHETIC TRAINING ONLY: YES**

**PATHOLOGY OPENED: NO**

**STAGE81B STARTED: NO**

**STAGE81C STARTED: NO**

**STAGE81A3 NOT COMPLETE**

## SINGLE-TRAJECTORY FORENSIC LOCALIZATION OF GEOMETRY TRAPPING

### Scope and exact replay

One previously trapped `balanced_multifactor` trajectory was replayed with
diagnostic-only instrumentation: seed 8114001, 8,192 synthetic cells, 4,096
genes, 32 known generating factors, the unchanged v4 encoder and predictor,
raw JEPA MSE, AdamW at 1e-4 with weight decay 0.01, effective batch 256,
40% exact-count masking, fixed EMA 0.996, and exactly 500 optimizer and 500 EMA
updates. No architecture, tokenizer, target, loss, masking, or training policy
was changed.

The replay reproduced the original trajectory. Replay agreement uses explicit
diagnostic-specific numerical tolerances, not scientific effect thresholds:
1e-6 for JEPA loss, 0.005 for effective ranks, 1e-5 for singular fractions and
slot metrics, 1e-4 for online-target distance, and 0.025 for the separate
held-out ridge R2 diagnostic. The largest observed difference was 0.02109 in
online factor-readout R2 at step 100. In contrast, the maximum JEPA-loss
difference was 1.62e-7, effective-rank difference was 0.00225, singular-energy
difference was 1.43e-6, and online-target-distance difference was 3.00e-5.

### Common versus cell-specific JEPA loss

The diagnostic identity `total MSE = common MSE + centered residual MSE` held
to floating-point precision. The full-slot trajectory was:

| Step | Total MSE | Common MSE | Residual MSE | Residual explained fraction |
|---:|---:|---:|---:|---:|
| 0 | 0.255783 | 0.254318 | 0.001465 | 0.716869 |
| 20 | 0.007425 | 0.006400 | 0.001024 | 0.798827 |
| 50 | 0.001695 | 0.000969 | 0.000726 | 0.848538 |
| 100 | 0.000827 | 0.000363 | 0.000464 | 0.898427 |
| 200 | 0.000486 | 0.000146 | 0.000340 | 0.922720 |
| 300 | 0.000377 | 0.000087 | 0.000291 | 0.932698 |
| 500 | 0.000263 | 0.000045 | 0.000218 | 0.948858 |

The large raw-loss decline is therefore not merely a cell-common shortcut.
Centered residual MSE also fell by approximately 85%, and residual explained
fraction rose from 0.717 to 0.949. At step 500, all 24 slots agreed: the
slot-wise residual explained fraction ranged from 0.9468 to 0.9504, with a
median of 0.9489. Objective/common-component dominance is falsified as the
primary explanation for this trapped trajectory.

### Token information localizes the loss

The known factors are recoverable from the synthetic task and from the full
token tensor at step 500:

| Representation | Held-out mean factor R2 |
|---|---:|
| Full raw normalized expression | 0.8563 |
| Visible 60% raw expression | 0.5368 |
| Hidden 40% raw expression | 0.3520 |
| Full 4,096 x 160 tokenizer tensor, bounded linear kernel | 0.8345 |
| Token mean | -0.0341 |
| Cross-attention output mean | -0.0573 |
| Final target-slot mean | -0.1059 |

The full-token kernel remained stable from step 0 (0.8348) through step 500
(0.8345). The tokenizer therefore preserves nearly all linearly accessible
factor information present in full raw expression. Token averaging destroys
that accessibility, and cross-attention does not recover it. A tokenizer
information bottleneck is not supported.

### Q/K/V/O and functional routing

All Q/K/V/O parameter groups had finite, almost universally nonzero gradients.
By step 500, relative movement from initialization was 0.2083 for Q, 0.2046 for
K, 0.0324 for V, and 0.0441 for O. Q/K movement was therefore larger than V/O
movement, so a simple claim that only V/O learned would be incorrect.

However, functional routing remained ineffective. Mean gradient norms over
steps 301-500 were approximately 1.01e-4 for Q, 1.03e-5 for K, 7.86e-3 for V,
and 7.93e-3 for O. AdamW accumulated substantial Q/K movement despite much
smaller late gradients, but that movement did not create differentiated
attention maps.

Pre-softmax logits remained narrow: all-head standard deviation increased only
from 0.01005 at initialization to 0.01665 at step 500, with a final range of
-0.0887 to 0.0898. At step 500, median normalized attention entropy was
0.999990, median maximum weight was 0.000255, median top-10 mass was 0.002538,
median between-slot attention-map cosine was 0.999956, and mean cross-cell map
variance was 4.76e-13. With 4,096 genes, these values are effectively uniform.

Raw learned queries remained broad (effective rank 22.51 at step 500), and
W_Q-projected queries also remained broad (effective rank 21.92), although the
projected top singular energy fraction increased from 0.0874 to 0.1043. The
failure is therefore not query-vector collapse by itself. Keys also retained
nontrivial across-gene geometry: median per-cell effective rank changed from
45.71 to 44.92, median sampled gene-pair cosine from 0.266 to 0.286, and
cross-cell key standard deviation from 0.128 to 0.156. Identity and value key
contributions cannot be exactly separated because fusion and tokenizer
LayerNorm occur before the linear W_K projection; no artificial decomposition
was reported.

### Multi-mask sensitivity

The raw masked input and visible tokenizer tensor remained strongly sensitive
to which genes were hidden, while the latent pathway became increasingly
mask-invariant:

| Step | Raw visible | Token tensor | Context slots | Pooled context | Predictor |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.6484 | 0.9223 | 0.0600 | 0.0603 | 0.0646 |
| 100 | 0.6515 | 0.9223 | 0.0402 | 0.0403 | 0.0445 |
| 300 | 0.6511 | 0.9217 | 0.0298 | 0.0299 | 0.0350 |
| 500 | 0.6487 | 0.9224 | 0.0254 | 0.0255 | 0.0292 |

Each ratio is mean within-cell squared distance across eight deterministic
40% masks divided by mean between-cell squared distance within matching masks.
Full-versus-masked pooled-online cosine increased from 0.99971 to 0.99990 while
mean L2 distance fell from 0.2985 to 0.1727. Training therefore increases
mask invariance after cross-attention even though the token tensor still
strongly records the changed mask.

### Mechanistic conclusion

The evidence localizes the information loss between the information-rich full
token tensor and the almost-uniform cross-attention output. It falsifies a
tokenizer information bottleneck and does not support common-component loss
dominance as the primary mechanism. Q/K parameters move, but their logits do
not produce useful gene-, slot-, or cell-specific routing.

**PRIMARY FORENSIC CLASSIFICATION: ATTENTION ROUTING BOTTLENECK STRONGLY SUPPORTED**

The single recommended next causal experiment is a separately approved,
synthetic-only Q/K routing-bootstrap intervention that leaves tokenization and
target semantics unchanged. No such intervention was implemented here.

Compact evidence files:

- `scripts/v4/stage81a3_forensic_failed_trajectory_replay.py`
- `results/v4/stage81a3_forensic_failed_trajectory_replay.json`
- `results/v4/stage81a3_forensic_loss_decomposition.csv`
- `results/v4/stage81a3_forensic_attention_qkvo.csv`
- `results/v4/stage81a3_forensic_token_information.csv`
- `results/v4/stage81a3_forensic_mask_sensitivity.csv`

**STAGE81A3 COMPLETE: NO**

**READY FOR STAGE81B: NO**

**REAL-RNA OPTIMIZER STEPS PERFORMED: 0**

**REAL-RNA EMA UPDATES PERFORMED: 0**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**SYNTHETIC FORENSIC OPTIMIZER STEPS: 500**

**SYNTHETIC FORENSIC EMA UPDATES: 500**

**PATHOLOGY OPENED: NO**

**STAGE81B STARTED: NO**

**STAGE81C STARTED: NO**

**PRODUCTION SEED SELECTED: NO**

**ARCHITECTURE CHANGED: NO**

**TRAINING OBJECTIVE CHANGED: NO**

## FINAL INFORMATION-PRESERVATION AND ENGINEERING QUALIFICATION

### Decision purpose and governing state

This was the single final Stage81A3 synthetic qualification authorized from
frozen Stage81A2 evidence commit `808ce4f170055c5568cc5c1e0e3a56415b52f908`.
The scientific requirement was not merely student/teacher agreement. It was a
compact, pathology-blind representation that retained most controlled
molecular variation and inferred that state from incomplete observations.

The prior forensic evidence was verified before implementation. In particular,
the tokenizer remained rich, native gene-to-latent attention was nearly
uniform, a fixed forward-only scaling exposed useful Q/K ranking information,
the matched permuted-ranking control did not, and arithmetic mean pooling
destroyed information distributed across slots. Historical baselines were
reused from the geometry-escape, EMA-disambiguation, forensic replay, and
attention-logit diagnostic artifacts. They were not rerun as competitors.

### Exact candidate

Only two compression operations changed:

1. Gene-to-latent QK logits were normalized independently for each
   cell/head/slot over valid genes. In float32, the implementation computes
   `mu = mean(L_valid)`, `sd = sqrt(mean((L_valid - mu)^2))`, then
   `L_norm = (L - mu) / max(sd, 1e-6)`. Invalid genes are set to negative
   infinity before softmax. The same code is used by online and EMA target
   encoders. There is no learned or fixed temperature parameter.
2. The full final `[B,24,160]` slot pattern is the distributed state. The
   canonical 160-D summary is a deterministic, train-subset-fitted PCA-160 of
   flattened `[B,3840]` slots. PCA uses no factor labels or evaluation cells
   and is not trainable. Arithmetic mean is retained only as a historical
   comparison.

The tokenizer, 4,096-gene vocabulary, width 160, 24 slots, two latent blocks,
four heads, predictor, corresponding-slot raw JEPA MSE, exact 40% masking,
AdamW settings, microbatch 8, effective batch 256, fp16, and fixed diagnostic
EMA 0.996 were unchanged.

### Qualification execution

Both predeclared fixtures and all five fixed seeds completed exactly 500
optimizer updates and 500 EMA updates each. This produced 10 trajectories,
5,000 qualification optimizer updates, and 5,000 qualification EMA updates.
No seed, checkpoint, fixture, or result was selected or replaced. Step 500 was
the decision point; steps 0, 20, 50, 100, 200, and 300 were trajectory evidence.

The run took 90.62 summed trajectory minutes. Peak allocated GPU memory was
271,799,296 bytes (0.253 GiB). Microbatch 8 fit without fallback. There were
zero nonfinite losses, activations, or gradients; zero GradScaler skips; zero
target-gradient events; and zero CUDA OOM events.

### Information map at step 500

Values below are fixture medians across five fixed seeds.

| Representation or ratio | Balanced | Dominant-axis |
|---|---:|---:|
| Raw normalized expression R2 | 0.856 | 0.858 |
| Raw PCA-160 R2 | 0.838 | 0.839 |
| Visible 60% raw R2 | 0.539 | 0.573 |
| Hidden 40% raw R2 | 0.356 | 0.409 |
| Full tokenizer tensor R2 | 0.841 | 0.843 |
| Cross-attention flattened slots R2 | 0.551 | 0.568 |
| Post-block flattened slots R2 | 0.536 | 0.553 |
| Final flattened target slots R2 | 0.535 | 0.555 |
| Historical arithmetic mean R2 | -0.108 | -0.064 |
| Target PCA-160 R2 | 0.528 | 0.549 |
| Masked online flattened slots R2 | -0.163 | -0.075 |
| Masked online PCA-160 R2 | -0.507 | -0.407 |
| Predictor PCA-160 R2 | -0.495 | -0.412 |
| Token-to-slot retention | 0.640 | 0.655 |
| Slot-to-PCA160 retention | 0.982 | 1.006 |
| End-to-end token-to-PCA retention | 0.630 | 0.653 |
| Masked-to-full retention | -0.972 | -0.733 |

The raw PCA reference retained almost all raw-expression information, showing
that 160 dimensions were not intrinsically too small for these fixtures. The
candidate PCA also retained essentially all information that reached the
slots. Therefore PCA-160 was not the primary bottleneck. The decisive first
loss remained gene-to-latent compression: about 34-36% of tokenizer factor
information was lost before the final slots. The masked student was worse: its
held-out factor R2 was negative in every run and never equaled the visible-raw
reference.

### Checkpoint trajectory and JEPA loss

| Fixture | Step | Target flat R2 | Target PCA R2 | Masked PCA R2 | JEPA MSE |
|---|---:|---:|---:|---:|---:|
| balanced | 0 | 0.548 | 0.532 | -0.462 | 0.196760 |
| balanced | 20 | 0.548 | 0.531 | -0.489 | 0.009650 |
| balanced | 50 | 0.548 | 0.530 | -0.438 | 0.002721 |
| balanced | 100 | 0.547 | 0.528 | -0.450 | 0.001648 |
| balanced | 200 | 0.546 | 0.528 | -0.453 | 0.001117 |
| balanced | 300 | 0.543 | 0.529 | -0.516 | 0.000938 |
| balanced | 500 | 0.535 | 0.528 | -0.507 | 0.000720 |
| dominant-axis | 0 | 0.565 | 0.553 | -0.340 | 0.198144 |
| dominant-axis | 20 | 0.564 | 0.553 | -0.368 | 0.010233 |
| dominant-axis | 50 | 0.564 | 0.553 | -0.387 | 0.002968 |
| dominant-axis | 100 | 0.564 | 0.553 | -0.295 | 0.001765 |
| dominant-axis | 200 | 0.563 | 0.551 | -0.381 | 0.001173 |
| dominant-axis | 300 | 0.561 | 0.549 | -0.417 | 0.001012 |
| dominant-axis | 500 | 0.555 | 0.549 | -0.407 | 0.000758 |

JEPA loss fell by more than 99% while masked-state factor information remained
negative. This is direct evidence that low teacher/student MSE did not imply a
useful incomplete-cell representation. The candidate learned agreement without
recovering the controlled state available in visible expression.

### Per-factor retention

The evidence CSV retains every factor, seed, representation, and checkpoint.
At step 500, all 32 tokenizer factors were positive and informative. Across
balanced factors, median target/token retention by factor ranged from 0.523 to
0.712; masked PCA R2 ranged from -0.812 to -0.196. Across dominant-axis
factors, target/token retention ranged from 0.558 to 0.898; masked PCA R2 was
negative for 31 of 32 factors. Only the dominant shared factor remained
positive under masking (`R2=0.470`), which did not rescue the broad factor set.
Exact all-seed values are in
`results/v4/stage81a3_final_information_preservation_factors.csv`; the compact
step-500 median-by-factor audit is:

| Fixture | Factors | Token R2 range | Target PCA R2 range | Masked PCA R2 range | Target/token range |
|---|---|---:|---:|---:|---:|
| balanced | 0-31 | 0.808-0.871 | 0.425-0.612 | -0.812 to -0.196 | 0.523-0.712 |
| dominant-axis | 0-31 | 0.791-0.965 | 0.462-0.867 | -0.813 to 0.470 | 0.558-0.898 |

No fixture hid success in a minority of factors. S4 failed in both fixtures.

### Attention, slots, masks, and geometry

Variance normalization worked mechanically. Median raw QK logit SD was about
0.01030 and normalized SD was 1.00000. Median attention entropy was about
0.940, maximum weight about 0.0046, top-10 mass about 0.0315, and between-slot
attention-map cosine about 0.378. Median top-10 Jaccard between slots was zero;
same-slot overlap across cells was 0.429. Thus the new attention was genuinely
nonuniform and slot-differentiated, not the historical nearly uniform routing.
This improvement was insufficient to preserve the required information.

Target within-cell slot cosine remained about 0.90 and slot variance about
0.094. Median final PCA effective rank was 28.64 for balanced and 28.55 for
dominant-axis, but median top singular energy was 0.974 in both fixtures. Every
run exceeded the individual 0.90 top-energy ceiling, so geometry failed despite
moderate effective rank. This again demonstrates why rank alone is not enough.

Four deterministic masks were compared on the same cells. Same-cell cross-mask
cosine was high (median 0.979 balanced, 0.968 dominant-axis) and exceeded
between-cell cosine (0.608 and 0.679). This apparent mask stability is not a
success because S5 and S6 failed. It is stability through information erasure,
the exact failure prohibited by S7.

Q, K, V, and O all had finite nonzero gradients and measurable movement. For
the first recorded trajectory, mean gradient norms were 0.00270 (Q), 0.00275
(K), 0.0323 (V), and 0.0355 (O), with relative movements 0.0567, 0.0645,
0.0425, and 0.0693. The model was not frozen, and shrinking Q/K scale alone
cannot explain the failure because normalization enforced unit routing SD.

### Scientific and engineering gates

| Gate | Balanced | Dominant-axis |
|---|---|---|
| S1 tokenizer healthy | PASS | PASS |
| S2 token-to-slot retention | FAIL | FAIL |
| S3 final 160-D retention | FAIL | FAIL |
| S4 per-factor coverage | FAIL | FAIL |
| S5 masked student preserves state | FAIL | FAIL |
| S6 JEPA adds value over visible raw | FAIL (0/5) | FAIL (0/5) |
| S7 no erasure robustness | FAIL | FAIL |
| Geometry safety | FAIL | FAIL |

Every engineering gate passed: repository integrity, 16 focused candidate
tests, exact-count masking semantics, finite online and predictor gradients,
zero target gradients, EMA formula/count/order, fp16 numerical health,
checkpoint/resume, deterministic continuation, compute limits, pathology
firewall, protected-file hashes, and no unapproved training behavior.

The candidate checkpoint audit restored online, target, predictor, optimizer,
GradScaler, counters, mask generator, and RNG state. A one-update continuation
was bit-exact: model/loss maximum differences were zero, optimizer and scaler
states matched, and the task-created checkpoint was removed. The EMA formula
maximum float32 error was `2.384185791015625e-7`, within the declared `5e-7`
numerical tolerance. Post-qualification regression was `179 passed`, zero
failed, zero warnings.

Candidate checkpoint preflight and refresh executions outside the ten science
trajectories were recorded separately. The scientific qualification count is
exactly 5,000 optimizer and 5,000 EMA updates. No real RNA entered any update,
PCA fit, or model input. The pathology firewall found zero executable access
to diagnosis, amyloid/tau, Braak, CERAD, pathology group, trajectory, or
condition fields. Synthetic factors were used only for held-out evaluation.

### Final decision and hard stop

PCA-160 did not cause the primary failure. Variance-normalized routing improved
attention mechanics but did not make the Perceiver compression sufficiently
information-preserving. The masked online representation failed every
predeclared incomplete-state value test. Low JEPA loss was therefore not a
scientific success.

**DOES JEPA EARN ITS PLACE IN v4? NO FOR CURRENT FORMULATION.**

**PRIMARY CLASSIFICATION: CURRENT PERCEIVER COMPRESSION PATH FAILS INFORMATION-PRESERVATION GATES**

Under the task's hard-stop rule, do not test another temperature, Q/K
normalization, pooling method, EMA, longer run, favorable checkpoint, or seed.
The current Perceiver compression path is rejected for the v4 foundation
contract. A future redesign requires a new human-approved task; it is not a
continuation of this qualification.

Evidence files:

- `configs/v4/stage81a3_information_preserving_candidate.yaml`
- `scripts/v4/stage81a3_final_information_preservation_qualification.py`
- `results/v4/stage81a3_final_information_preservation_qualification.json`
- `results/v4/stage81a3_final_information_preservation_runs.csv`
- `results/v4/stage81a3_final_information_preservation_factors.csv`
- `results/v4/stage81a3_final_information_preservation_geometry.csv`
- `results/v4/stage81a3_final_information_preservation_engineering_gates.json`

**SCIENTIFIC QUALIFICATION: FAIL**

**ENGINEERING QUALIFICATION: PASS**

**JEPA EARNS ITS PLACE IN v4: NO FOR CURRENT FORMULATION**

**STAGE81A3 COMPLETE: NO**

**READY FOR STAGE81B: NO**

**REAL-RNA OPTIMIZER STEPS PERFORMED: 0**

**REAL-RNA EMA UPDATES PERFORMED: 0**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**SYNTHETIC QUALIFICATION TRAJECTORIES: 10**

**SYNTHETIC QUALIFICATION OPTIMIZER UPDATES: 5,000**

**SYNTHETIC QUALIFICATION EMA UPDATES: 5,000**

**PATHOLOGY OPENED: NO**

**STAGE81B STARTED: NO**

**STAGE81C STARTED: NO**

**PRODUCTION SEED SELECTED: NO**

**PRODUCTION EMA SELECTED: NO**

**TOKENIZER CHANGED: NO**

**TARGET SEMANTICS CHANGED: NO**

**GENE-TO-LATENT ROUTING CHANGED: YES, VARIANCE-NORMALIZED LOGITS**

**CANONICAL CELL SUMMARY CHANGED: YES, TRAIN-FITTED PCA-160 OF FLATTENED FINAL SLOTS**

**NO ADDITIONAL MODEL EXPERIMENT IS AUTHORIZED BY THIS TASK.**

**NOTHING STAGED, COMMITTED, OR PUSHED**

### Final A-AP qualification ledger

- **A. Repository state:** `main`; HEAD and `origin/main` both
  `808ce4f170055c5568cc5c1e0e3a56415b52f908`; index empty.
- **B. Prior evidence verified:** tokenizer richness, native attention-scale
  bottleneck, useful Q/K ranking, negative permuted control, and pooling loss.
- **C. Scientific north star:** preserve meaningful molecular state and infer
  it from incomplete observations, rather than merely minimize JEPA loss.
- **D. Exact candidate architecture:** 4,096 genes, width 160, 24 slots, two
  latent blocks, four heads, unchanged predictor, and EMA target.
- **E. Exact changes:** variance-normalized gene-to-latent logits and
  train-fitted PCA-160 in place of arithmetic mean as canonical summary.
- **F. Attention mechanics:** valid-gene population SD normalized to 1.0 in
  float32; invalid genes have zero probability; no temperature parameter.
- **G. PCA contract:** deterministic training-subset fit on flattened full-view
  target slots, without factors or evaluation cells.
- **H. Pre-test regression:** existing suite passed before qualification;
  candidate-focused tests passed 16/16.
- **I. Qualification contract:** two fixtures, five fixed seeds, 500 updates,
  exact 40% masking, fp16, and diagnostic EMA 0.996.
- **J. Completion:** all 10 runs, 5,000 trajectory optimizer updates, and 5,000
  trajectory EMA updates completed.
- **K. Raw expression:** median factor R2 was 0.856 balanced and 0.858
  dominant-axis.
- **L. Raw PCA-160:** median R2 was 0.838 and 0.839; 160 dimensions were not
  intrinsically inadequate.
- **M. Tokenizer:** healthy median R2 of 0.841 and 0.843.
- **N. Cross-attention:** flattened-slot R2 of 0.551 and 0.568.
- **O. Distributed final slots:** R2 of 0.535 and 0.555.
- **P. Final PCA-160:** R2 of 0.528 and 0.549; PCA retained essentially all
  information that reached the slots.
- **Q. Per-factor retention:** insufficient across the broad factor set; all
  82,240 factor/checkpoint records are retained in the compact factor CSV.
- **R. Masked online representation:** PCA R2 was negative in all 10 runs.
- **S. Full target:** remained moderately informative, so masked failure was
  not an averaging artifact.
- **T. Visible-raw reference:** median R2 was 0.539 and 0.573.
- **U. JEPA value:** zero of 10 runs matched visible-raw information.
- **V. Stage loss:** the main information loss occurred from tokenizer to
  latent slots, not from slots to PCA.
- **W. Retention:** token-to-slot medians were 0.640/0.655 and end-to-end
  medians were 0.630/0.653.
- **X. Geometry:** effective rank was about 28.6, but top singular energy was
  about 0.974 and failed every individual ceiling.
- **Y. Attention differentiation:** unit normalized SD, entropy about 0.940,
  and between-slot map cosine about 0.378 showed nonuniform routing.
- **Z. Slot differentiation:** slot cosine remained about 0.90; Q/K/V/O all
  moved and received finite gradients.
- **AA. JEPA telemetry:** MSE fell below 0.0008 while masked factor information
  stayed negative.
- **AB. Mask robustness:** high same-cell mask similarity accompanied poor
  information, so it was stability through erasure and S7 failed.
- **AC. Gradients:** online/predictor gates passed and target gradients stayed
  absent.
- **AD. EMA:** formula, ordering, count, and frozen-target checks passed.
- **AE. Resume:** model, optimizer, scaler, RNG, masks, and counters resumed
  bit-exactly; the temporary checkpoint was removed.
- **AF. Numerical health:** zero nonfinite events, scaler skips, or OOMs.
- **AG. Compute:** microbatch 8 fit without fallback; peak allocation was
  271,799,296 bytes.
- **AH. Firewall:** no real RNA or prohibited pathology field was accessed.
- **AI. Tests:** post-qualification suite passed 179 tests with zero failures
  and zero warnings.
- **AJ. Scientific gates:** S1 passed; S2-S7 and geometry failed in both
  fixtures.
- **AK. Engineering gates:** all passed.
- **AL. JEPA decision:** JEPA does not earn its place in v4 under the current
  formulation.
- **AM. Classification:** current Perceiver compression path fails the
  information-preservation gates.
- **AN. Hard stop:** no temperature, normalization, pooling, EMA, duration,
  checkpoint, or seed follow-up is authorized by this task.
- **AO. Evidence:** candidate config, implementation, runner, tests, JSON,
  run/factor/geometry CSVs, engineering report, and this readout.
- **AP. Git safety:** protected files unchanged, index empty, and nothing
  staged, committed, or pushed.

**FINAL PRIMARY CLASSIFICATION: CURRENT PERCEIVER COMPRESSION PATH FAILS INFORMATION-PRESERVATION GATES**

**SCIENTIFIC QUALIFICATION: FAIL**

**ENGINEERING QUALIFICATION: PASS**

**JEPA EARNS ITS PLACE IN v4: NO FOR CURRENT FORMULATION**

**STAGE81A3 COMPLETE: NO**

**READY FOR STAGE81B: NO**

**REAL-RNA OPTIMIZER STEPS PERFORMED: 0**

**REAL-RNA EMA UPDATES PERFORMED: 0**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**SYNTHETIC QUALIFICATION TRAJECTORIES: 10**

**SYNTHETIC QUALIFICATION OPTIMIZER UPDATES: 5,000**

**SYNTHETIC QUALIFICATION EMA UPDATES: 5,000**

**PATHOLOGY OPENED: NO**

**STAGE81B STARTED: NO**

**STAGE81C STARTED: NO**

**PRODUCTION SEED SELECTED: NO**

**PRODUCTION EMA SELECTED: NO**

**TOKENIZER CHANGED: NO**

**TARGET SEMANTICS CHANGED: NO**

**GENE-TO-LATENT ROUTING CHANGED: YES, VARIANCE-NORMALIZED LOGITS**

**CANONICAL CELL SUMMARY CHANGED: YES, TRAIN-FITTED PCA-160 OF FLATTENED FINAL SLOTS**

**NO ADDITIONAL MODEL EXPERIMENT IS AUTHORIZED BY THIS TASK.**

**NOTHING STAGED, COMMITTED, OR PUSHED**

## EMA 0.996 bootstrap disambiguation

### Why this test was performed

The preceding synthetic geometry-escape diagnostic used fixed EMA 0.99925 for
500 optimizer updates. Because that momentum has a memory half-life of
approximately 924 updates, the target had not traversed one half-life by the
final checkpoint. A clean one-variable comparison was therefore run to test
whether a more responsive teacher could bootstrap the unchanged architecture
out of its narrow initialization.

The only substantive change was:

`fixed EMA momentum: 0.99925 -> 0.996`

Everything else was reused exactly from the completed baseline: both
deterministic 8,192-cell fixtures, all five seeds, 4,096 genes, 32 generating
factors, train/evaluation partitions, factor readout, 40% exact-count masks,
model and predictor architecture, AdamW learning rate 1e-4, weight decay 0.01,
no gradient clipping, CUDA fp16, microbatch 8, effective batch 256,
accumulation 32, 500 updates, and the primary JEPA loss alone. Variance and
covariance remained telemetry-only with training weights zero.

### Matched geometry and loss comparison

The tables below show five-seed means. Every comparison is paired by fixture,
seed, and checkpoint.

Balanced multifactor:

| Step | Target rank, EMA .99925 | Target rank, EMA .996 | Target energy, EMA .99925 | Target energy, EMA .996 | Target factor R2, EMA .99925 | Target factor R2, EMA .996 | JEPA loss, EMA .99925 | JEPA loss, EMA .996 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4.676 | 4.676 | 0.988388 | 0.988388 | -0.140 | -0.140 | 0.221219 | 0.221219 |
| 20 | 4.677 | 4.679 | 0.988390 | 0.988412 | -0.140 | -0.135 | 0.007405 | 0.006972 |
| 50 | 4.671 | 4.655 | 0.988428 | 0.988612 | -0.149 | -0.146 | 0.001818 | 0.001645 |
| 100 | 4.648 | 4.557 | 0.988530 | 0.989057 | -0.139 | -0.149 | 0.000953 | 0.000836 |
| 200 | 4.589 | 4.340 | 0.988763 | 0.989885 | -0.138 | -0.139 | 0.000578 | 0.000522 |
| 300 | 4.519 | 4.137 | 0.989012 | 0.990626 | -0.131 | -0.119 | 0.000434 | 0.000396 |
| 500 | 4.361 | 3.782 | 0.989568 | 0.991881 | -0.125 | -0.109 | 0.000304 | 0.000277 |

Dominant-axis multifactor:

| Step | Target rank, EMA .99925 | Target rank, EMA .996 | Target energy, EMA .99925 | Target energy, EMA .996 | Target factor R2, EMA .99925 | Target factor R2, EMA .996 | JEPA loss, EMA .99925 | JEPA loss, EMA .996 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4.855 | 4.855 | 0.987252 | 0.987252 | -0.079 | -0.079 | 0.221171 | 0.221171 |
| 20 | 4.854 | 4.855 | 0.987256 | 0.987269 | -0.086 | -0.086 | 0.007369 | 0.006932 |
| 50 | 4.849 | 4.833 | 0.987292 | 0.987452 | -0.077 | -0.086 | 0.001794 | 0.001623 |
| 100 | 4.826 | 4.727 | 0.987412 | 0.987958 | -0.075 | -0.080 | 0.000929 | 0.000815 |
| 200 | 4.761 | 4.502 | 0.987686 | 0.988943 | -0.084 | -0.080 | 0.000573 | 0.000517 |
| 300 | 4.688 | 4.289 | 0.987982 | 0.989825 | -0.063 | -0.050 | 0.000432 | 0.000394 |
| 500 | 4.528 | 3.919 | 0.988637 | 0.991312 | -0.071 | -0.041 | 0.000302 | 0.000276 |

At step 500, faster EMA reduced target rank relative to the slower baseline by
0.579 in the balanced fixture and 0.609 in the dominant-axis fixture. Loss was
slightly lower, but singular concentration was higher. Online ranks were also
slightly lower under EMA 0.996: 3.399 versus 3.445 for balanced and 3.519 versus
3.576 for dominant-axis. Online factor readout did not improve.

### Per-seed matched outcomes

| Fixture | Seed | Initial target rank | Final rank, EMA .99925 | Final rank, EMA .996 | Final target factor R2, EMA .99925 | Final target factor R2, EMA .996 | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|
| balanced | 8114001 | 4.767 | 4.423 | 3.797 | -0.119 | -0.113 | remains trapped |
| balanced | 8114002 | 4.823 | 4.410 | 3.661 | -0.135 | -0.117 | remains trapped |
| balanced | 8114003 | 6.500 | 6.121 | 5.457 | -0.250 | -0.225 | remains trapped |
| balanced | 8114004 | 3.054 | 2.887 | 2.600 | -0.074 | -0.044 | remains trapped |
| balanced | 8114005 | 4.238 | 3.962 | 3.395 | -0.047 | -0.047 | remains trapped |
| dominant axis | 8114001 | 4.926 | 4.565 | 3.909 | -0.061 | -0.036 | remains trapped |
| dominant axis | 8114002 | 5.021 | 4.595 | 3.812 | -0.061 | -0.026 | remains trapped |
| dominant axis | 8114003 | 6.676 | 6.288 | 5.592 | -0.170 | -0.126 | remains trapped |
| dominant axis | 8114004 | 3.176 | 3.004 | 2.696 | 0.007 | 0.033 | remains trapped |
| dominant axis | 8114005 | 4.478 | 4.191 | 3.587 | -0.071 | -0.051 | remains trapped |

Small factor-readout increases in some runs were insufficient for escape
because geometry narrowed in every run. No absolute threshold was introduced:
clear escape required both directional geometry broadening from initialization
and improved factor recovery, as specified before the run.

### Module movement and gradient evidence

Mean step-500 module telemetry across all ten runs:

| Module group | Online relative movement | Target relative movement | Mean gradient norm, steps 301-500 | Nonzero finite gradient element fraction |
|---|---:|---:|---:|---:|
| gene embedding | 0.00133 | 0.00094 | 1.50e-5 | 0.99999 |
| identity projection | 0.07468 | 0.04141 | 1.48e-3 | 1.00000 |
| value encoder | 0.01513 | 0.01056 | 4.55e-3 | 1.00000 |
| tokenizer LayerNorm | 0.00318 | 0.00203 | 1.10e-3 | 1.00000 |
| gene-to-latent cross-attention | 0.13098 | 0.07813 | 1.17e-2 | 0.99999 |
| learned latent queries | 0.34273 | 0.20907 | 8.10e-4 | 1.00000 |
| latent block 1 | 0.04748 | 0.03130 | 3.94e-3 | 0.99999 |
| latent block 2 | 0.04474 | 0.03000 | 3.64e-3 | 0.99999 |
| final encoder LayerNorm | 0.00470 | 0.00324 | 6.74e-4 | 1.00000 |
| predictor | 0.03153 | N/A | 5.07e-3 | 0.99998 |

The predictor did learn, but its relative movement was smaller than the
identity projection, cross-attention, learned queries, and both latent blocks.
Almost every scalar parameter in every group received finite nonzero gradients.
This does not support a predictor-only shortcut. It supports the more specific
interpretation that encoder parameters learn substantially while their cell
geometry remains narrow or becomes narrower.

### Faster target following

Mean whole-encoder online-target distance at step 500 fell from 2.703 under EMA
0.99925 to 1.391 under EMA 0.996. Target module movements were substantial and
in the same groups as online movement. Faster teacher following therefore
worked mechanically; it followed the narrowing encoder more closely rather
than enabling a bootstrap into broader geometry.

### Attention and stage trace

Attention differentiated only microscopically. Mean median normalized entropy
changed from approximately 0.999996 at initialization to 0.999989 at step 500.
Between-slot attention-map cosine changed from approximately 0.999981 to
0.999954, and cross-cell attention-map variance rose only from approximately
6.6e-14 to 3.0e-13. Attention remained effectively uniform.

For the balanced fixture, bounded target-stage effective rank changed from
step 0 to 500 as follows:

- expression-value contribution summary: 1.393 to 1.392;
- fused-token summary: 1.396 to 1.395;
- token summary after LayerNorm: 2.962 to 2.947;
- cross-attention output: 3.767 to 3.429;
- after latent block 1: 3.775 to 3.292;
- after latent block 2: 3.673 to 3.151;
- final target slots: 3.688 to 3.062.

The dominant-axis fixture showed the same direction. No formerly narrow stage
broadened during learning.

### Interpretation

EMA 0.996 was demonstrably more responsive, but responsiveness did not resolve
the failure. It modestly lowered loss, increased target singular concentration,
and made the target track the narrowing online encoder more closely. All ten
paired runs remained trapped, with zero numerical failures.

**FASTER EMA DOES NOT RESOLVE GEOMETRY TRAPPING**

**CURRENT ARCHITECTURE / LEARNING DYNAMICS REQUIRE MECHANISTIC REVIEW BEFORE A3 FREEZE**

This is a synthetic mechanics conclusion only. It does not select production
EMA, alter the architecture, authorize real-RNA optimization, or establish a
biological result.

Compact evidence files:

- `scripts/v4/stage81a3_ema_bootstrap_disambiguation.py`
- `results/v4/stage81a3_ema_bootstrap_disambiguation.json`
- `results/v4/stage81a3_ema_bootstrap_disambiguation_trajectory.csv`
- `results/v4/stage81a3_ema_bootstrap_module_telemetry.csv`

**REAL-RNA OPTIMIZER STEPS PERFORMED: 0**

**REAL-RNA EMA UPDATES PERFORMED: 0**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**SYNTHETIC TRAINING ONLY: YES**

**PATHOLOGY OPENED: NO**

**STAGE81B STARTED: NO**

**STAGE81C STARTED: NO**

**PRODUCTION SEED SELECTED: NO**

**ARCHITECTURE CHANGED: NO**

**STAGE81A3 NOT COMPLETE**

## Recent Stage81A3 work ledger and current interpretation

This ledger records the order in which the latest Stage81A3 questions were
tested. It is an orientation index for the detailed sections above and does not
replace their methods, numerical tables, or claim boundaries.

### 1. Bounded real-RNA forward-only smoke

**What was tried:** The exact v4 encoder, exact-copy EMA target, and predictor
were run in evaluation mode on 502 pathology-blind foundation-training cells:
128 HVS, 246 NPH Ctrl, and 128 SEA-AD. Inputs used the frozen 4,096-gene order,
source-correct count layers, normalization to 10,000 followed by `log1p`, and
an exact-count 40% mask. There was no optimizer, backward call, or EMA update.

**What worked:** Source normalization, vocabulary order, masking semantics,
hidden-value invariance, unmeasured-placeholder invariance, online/target exact
copy, CUDA fp16 forward execution, and finite-output checks all passed. Peak
CUDA allocation was 312,226,816 bytes. The full v4 suite passed 163 tests.

**What was observed:** The untrained pooled target geometry was unexpectedly
narrow: effective rank 3.2241 and top singular energy fraction 0.9823. This was
an initialization observation, not training collapse.

### 2. Real-RNA initialization-geometry localization

**What was tried:** The same 502 cells were traced through each encoder stage,
with random-projection, expression-only, identity-only, permutation, flattened-
slot, five-initialization, source, sparsity, and broad-cell-class controls.

**What worked:** The traced output matched the ordinary forward pass exactly.
The normalized RNA input was broad (effective rank 442.84), as were random
160-dimensional projections (140.32-141.30), excluding narrow input geometry
or ordinary dimensional compression as sufficient explanations.

**What was observed:** Geometry narrowed in the expression-value/token-summary
path and was propagated by almost-uniform cross-attention. Initial attention
had normalized entropy 0.999995 and between-slot map cosine 0.999980. All five
test-only initializations and all three sources were narrow. Latent blocks and
LayerNorm were not the primary source, and mean pooling was secondary.

### 3. Synthetic geometry-escape diagnostic

**What was tried:** The actual v4 architecture was trained only on two known-
factor synthetic fixtures, five fixed test seeds each, for 500 updates using
the unchanged JEPA objective and test-only fixed EMA 0.99925.

**What worked:** Optimizer, gradient, accumulation, masking, EMA, telemetry,
and numerical-health mechanics operated correctly. There were 5,000 successful
synthetic optimizer updates and 5,000 matched EMA updates in total, with no
nonfinite events.

**What was observed:** All 10 of 10 trajectories remained geometrically
trapped. JEPA loss fell, but effective rank fell and singular concentration
rose; known-factor recovery remained absent. The architecture did not
demonstrate synthetic geometry escape under this contract.

### 4. EMA 0.996 bootstrap disambiguation

**What was tried:** The same ten synthetic runs were repeated with only one
change: fixed EMA momentum 0.99925 was replaced by 0.996. Architecture, data,
seeds, masking, optimizer, objective, and 500-step duration were unchanged.

**What worked:** Faster EMA tracked the online encoder more closely. Mean
whole-encoder online-target distance at step 500 fell from 2.703 to 1.391.
Encoder and predictor parameters received finite nonzero gradients and moved,
rejecting a frozen-encoder or predictor-only mechanical explanation.

**What was observed:** All 10 of 10 trajectories still remained trapped, and
target geometry became narrower. Faster target following therefore followed
the narrowing encoder rather than bootstrapping broader geometry. EMA
timescale was removed as the primary explanation.

### 5. Exact failed-trajectory forensic replay

**What was tried:** The `balanced_multifactor`, seed 8114001, EMA 0.996 run was
replayed for exactly 500 synthetic optimizer and 500 EMA updates with
diagnostic-only common/residual loss decomposition, Q/K/V/O telemetry, logits,
query/key geometry, bounded full-token kernel readout, and eight-mask
sensitivity. The architecture and training objective were unchanged.

**What worked:** The replay matched the prior training trajectory under named
metric-specific floating-point tolerances. JEPA-loss difference was at most
1.62e-7, effective-rank difference at most 0.00225, and no nonfinite event
occurred. The final full v4 regression suite passed 163 tests with zero failures
and zero warnings.

**What was observed:** Cell-specific residual learning was substantial:
residual explained fraction rose from 0.7169 to 0.9489. Full raw expression
factor R2 was 0.8563 and the complete tokenizer-tensor kernel retained R2
0.8345, but token mean, cross-attention mean, and final target mean were
-0.0341, -0.0573, and -0.1059. Final attention remained effectively uniform:
normalized entropy 0.999990 and between-slot map cosine 0.999956. Q/K moved,
but did not produce functionally differentiated routing. Latent mask
sensitivity also fell during training even though token-level sensitivity
remained high.

### Current evidence state

- Common-component/raw-target shortcut as the primary mechanism: not supported.
- Full-token tokenizer information loss: not supported.
- Faster EMA as the missing bootstrap mechanism: not supported.
- Q/K parameter immobility: not supported; Q/K moved substantially.
- Functionally ineffective cross-attention routing: strongly supported.
- Real-RNA biological performance: not tested.
- Production architecture change: not authorized.
- Production EMA, variance safeguard, and production seed: not frozen here.

**CURRENT PRIMARY FORENSIC CLASSIFICATION: ATTENTION ROUTING BOTTLENECK STRONGLY SUPPORTED**

**NEXT BOUNDED CAUSAL QUESTION: CAN A SYNTHETIC-ONLY Q/K ROUTING BOOTSTRAP RESTORE FACTOR ACCESSIBILITY WITHOUT CHANGING TOKENIZATION OR TARGET SEMANTICS?**

**STAGE81A3 COMPLETE: NO**

**READY FOR STAGE81B: NO**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**PATHOLOGY OPENED: NO**

## FORWARD-ONLY ATTENTION-LOGIT-SCALE CAUSAL DIAGNOSTIC

### Why this test was performed

The failed-trajectory forensic replay showed that the full tokenizer tensor
retained known synthetic-factor information while ordinary cross-attention was
almost uniform. The remaining causal question was whether learned Q/K rankings
were useful but too small in amplitude for softmax, or whether the rankings
themselves were uninformative. This diagnostic changed only forward-pass logit
amplitude. It did not train or mutate a modified model.

### Reference-state recovery and corrective rerun

The exact `balanced_multifactor`, seed 8114001, EMA 0.996 state was recovered
with the unchanged v4 architecture, raw JEPA MSE, AdamW contract, 40%
exact-count masking, and 500 optimizer plus 500 EMA updates. Recovery passed
the established metric-specific replay tolerances. Differences from the prior
forensic evidence were:

- JEPA loss: `4.60e-8`;
- target effective rank: `0.00118`;
- online effective rank: `0.00190`;
- target factor-readout mean R2: `0.00855`;
- logit standard deviation: `1.17e-8`;
- normalized-attention-entropy median: `0.0`.

The diagnostic was executed twice because the first successful run exposed
missing required slot-level and ordinary-forward-equivalence telemetry. The
scientific condition did not change. The final evidence-producing recovery
used 500 optimizer and 500 EMA updates; cumulative recovery work during this
task was therefore 1,000 optimizer and 1,000 EMA updates. Both were synthetic
state recovery, not competing training conditions or a seed sweep.

The explicit manual original-logit path agreed with the ordinary PyTorch
attention forward to maximum absolute difference `0.001990` at cross-attention
and `0.001599` at final slots, passing the predeclared `0.003` CUDA-fp16
implementation-equivalence tolerance. This is a numerical implementation
tolerance, not a scientific threshold.

### Deterministic forward-only intervention

The original aggregate step-500 logit standard deviation on the fixed 16-cell
diagnostic subset was measured before counterfactual factor readout:

```text
sigma_reference = 0.016647244
c = 1 / sigma_reference = 60.070004
```

Exactly one scale was evaluated. It was not tuned against factor R2, geometry,
entropy, mask sensitivity, or any output. No temperature sweep or production
attention scale was selected.

Online encoder, EMA target encoder, and predictor SHA-256 parameter hashes were
identical before and after all forwards. Maximum parameter change was exactly
zero for all three modules. The counterfactual performed zero optimizer steps,
zero EMA updates, and zero backward calls.

### Attention behavior

| Condition | Logit SD | Median normalized entropy | Median maximum weight | Median top-10 mass | Median between-slot map cosine | Cross-cell map variance |
|---|---:|---:|---:|---:|---:|---:|
| Original | 0.01665 | 0.999990 | 0.000255 | 0.002538 | 0.999840 | 1.55e-12 |
| Scaled learned ranking | 1.00000 | 0.964507 | 0.002630 | 0.018902 | 0.562748 | 1.35e-8 |
| Scaled permuted ranking | 1.00000 | 0.964507 | 0.002630 | 0.018902 | 0.534277 | 6.13e-8 |

Scaling made attention nonuniform and slot-specific. Lower entropy alone is
not treated as success: the permuted control had the same entropy and
concentration but did not recover factors.

Positive scaling preserved learned ordering by construction. Complete
`argsort` ranking was identical for 1,533 of 1,536 checked rows (`0.99805`);
the remaining three rows reflected numerical ties rather than a sign or order
changing intervention. Median top-20 Jaccard overlap between slots was zero
for both original and scaled learned rankings, as expected because scaling
does not change top genes. Median same-slot overlap across cells was `0.3793`
for learned rankings and zero after the fixed gene-permutation control.

### Factor-information recovery

The full tokenizer kernel remained strongly informative (mean held-out factor
R2 approximately `0.835`). Forward readouts were:

| Representation | Original R2 | Scaled learned ranking R2 | Scaled permuted ranking R2 |
|---|---:|---:|---:|
| Cross-attention flattened slots | 0.1943 | 0.4506 | -0.2759 |
| Cross-attention pooled | -0.0410 | -0.2250 | -1.0808 |
| Post-latent-block flattened slots | -0.0910 | 0.4211 | -0.3074 |
| Final flattened slots | -0.1150 | 0.4200 | -0.3091 |
| Final pooled representation | -0.1001 | -0.2505 | -1.0674 |

The learned ranking therefore carries substantial factor information that is
expressed when its amplitude is increased. Recovery survives both latent
blocks and final normalization in the distributed 24-slot pattern. It is not
generic concentration: the identically distributed permuted-ranking control
remained strongly negative. However, arithmetic pooling still destroys the
recovered pattern and becomes worse under scaling. The forward counterfactual
is consequently mechanistically informative but is not a healthy canonical
representation or candidate production model.

### Geometry and slot differentiation

Flattened cross-attention effective rank increased from `4.46` to `75.85`, and
final flattened-slot rank from `4.28` to `62.83`. Final flattened top singular
energy fraction fell from `0.9935` to `0.9610`. The permuted control was even
higher-rank (`146.08`) while having negative factor R2, demonstrating why rank
increase alone is not a rescue criterion.

Final within-cell slot cosine changed from `0.99354` to `0.93963`, slot
variance from `0.00619` to `0.05787`, and median per-slot effective rank from
`3.92` to `19.88`. At cross-attention, slot cosine changed from `0.98434` to
`0.86323`, slot variance from `0.01505` to `0.13148`, and median per-slot rank
from `4.21` to `21.61`. Scaling therefore did not merely sharpen all slots onto
one common attention map.

The final pooled representation remained narrow despite improvement:
effective rank changed from `3.78` to `10.69`, but top singular energy fraction
remained `0.9868` and factor R2 remained negative. Pooling/slot-readout semantics
remain unresolved even though Q/K ranking utility is established.

### Mask sensitivity and cell-specific routing

Mask-sensitivity ratios changed as follows:

| Stage | Original | Scaled learned ranking |
|---|---:|---:|
| Cross-attention slots | 0.04368 | 0.07006 |
| Final slots | 0.03432 | 0.05275 |
| Pooled representation | 0.03447 | 0.03424 |

Thus learned-ranking amplification restored some mask sensitivity in the
distributed slots but not after pooling. Median full-versus-masked pooled
cosine changed only from `0.999872` to `0.999844`, while median L2 distance rose
from `0.2017` to `0.2164`. Cross-cell attention-map variance increased by
approximately four orders of magnitude, but it remained small in absolute
terms and does not establish biological routing.

### Causal interpretation

The positive forward-only intervention, negative permuted-ranking control,
slot-level factor recovery, and increased mask/slot differentiation jointly
show that Q/K learned useful relative gene ordering. Ordinary softmax scale
suppresses expression of that ordering. This does not validate `c = 60.07`,
select a temperature, or prove that a scaled model would train stably. It also
does not resolve the failed pooled representation.

**PRIMARY CLASSIFICATION: Q/K RANKINGS CONTAIN USEFUL INFORMATION BUT LOGIT SCALE SUPPRESSES ROUTING**

The single recommended next experiment is one separately approved synthetic
training run with one evidence-backed Q/K routing-bootstrap mechanism. It must
retain the same tokenizer and target semantics, include the fixed permuted or
equivalent negative control, and evaluate both distributed slots and pooled
output. This diagnostic scale must not be frozen as the production mechanism.

Evidence files:

- `scripts/v4/stage81a3_attention_logit_scale_diagnostic.py`
- `results/v4/stage81a3_attention_logit_scale_diagnostic.json`
- `results/v4/stage81a3_attention_logit_scale_factor_readout.csv`
- `results/v4/stage81a3_attention_logit_scale_geometry.csv`
- `results/v4/stage81a3_attention_logit_scale_mask_sensitivity.csv`

**STAGE81A3 COMPLETE: NO**

**READY FOR STAGE81B: NO**

**REAL-RNA OPTIMIZER STEPS PERFORMED: 0**

**REAL-RNA EMA UPDATES PERFORMED: 0**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**SYNTHETIC REFERENCE-STATE RECOVERY OPTIMIZER STEPS: 1,000 CUMULATIVE; 500 FINAL EVIDENCE RUN**

**SYNTHETIC REFERENCE-STATE RECOVERY EMA UPDATES: 1,000 CUMULATIVE; 500 FINAL EVIDENCE RUN**

**FORWARD COUNTERFACTUAL OPTIMIZER STEPS: 0**

**FORWARD COUNTERFACTUAL EMA UPDATES: 0**

**FORWARD COUNTERFACTUAL BACKWARD CALLS: 0**

**PATHOLOGY OPENED: NO**

**STAGE81B STARTED: NO**

**STAGE81C STARTED: NO**

**PRODUCTION SEED SELECTED: NO**

**PRODUCTION ATTENTION SCALE SELECTED: NO**

**ARCHITECTURE CHANGED: NO**

**TRAINING OBJECTIVE CHANGED: NO**

## CURRENT TERMINAL STATUS

The chronologically latest Stage81A3 decision is the section
**FINAL INFORMATION-PRESERVATION AND ENGINEERING QUALIFICATION** and its
**Final A-AP qualification ledger** above. Those sections supersede earlier
diagnostic next-step suggestions but do not rewrite their historical evidence.

The final qualification completed all 10 fixed synthetic trajectories and
5,000 optimizer plus 5,000 EMA trajectory updates. Engineering qualification
passed, including 179 post-qualification tests. Scientific qualification
failed because token-to-slot retention, end-to-end retention, per-factor
coverage, masked-student information, JEPA value, no-erasure robustness, and
geometry failed in both fixtures. The tokenizer remained healthy and PCA-160
preserved nearly all information that reached the slots, localizing the main
failure to the current Perceiver compression and incomplete-state JEPA path.

**FINAL PRIMARY CLASSIFICATION: CURRENT PERCEIVER COMPRESSION PATH FAILS INFORMATION-PRESERVATION GATES**

**SCIENTIFIC QUALIFICATION: FAIL**

**ENGINEERING QUALIFICATION: PASS**

**JEPA EARNS ITS PLACE IN v4: NO FOR CURRENT FORMULATION**

**STAGE81A3 COMPLETE: NO**

**READY FOR STAGE81B: NO**

**REAL-RNA MODEL TRAINING PERFORMED: NO**

**PATHOLOGY OPENED: NO**

**NO ADDITIONAL MODEL EXPERIMENT IS AUTHORIZED BY THIS TASK.**

**NOTHING STAGED, COMMITTED, OR PUSHED**


## RLC-CD FAST FULL-VOCABULARY FEASIBILITY PROBE

The learned CELL-token IPB candidate was stopped after three completed trajectories because
the tokenizer and contextual gene tensor remained rich while the 160-dimensional learned
cell state and masked inference moved decisively away from the information-preservation
requirements. Its partial JSON remains frozen locally at SHA-256
`aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308` and is not treated as a completed qualification.

RLC-CD removed the CELL token, Perceiver slots, global teacher matching, and learned pooling.
It retained the frozen tokenizer and six-layer token-preserving linear-attention encoder,
while defining the cell state in a factual-TRAIN-fitted 160-dimensional whitened PCA system.
The visible molecular contribution entered exactly; the neural predictor estimated only four
missing block contributions. A TRAIN-only ridge completion baseline was evaluated on unseen
mask-bank views. The target decomposition passed=True with
maximum absolute error 3.5e-07.

Exactly three matched 100-update synthetic conditions were run: base residual completion,
paired counterfactual completion, and paired completion with a learned 12-node acyclic latent
mechanism auxiliary. The true generator DAG and factor labels were evaluation-only. No real
RNA, pathology, EMA, production weights, checkpoint selection, seed selection, or parameter
sweep was used.

The visible-only, linear, three neural, per-factor, per-gene, intervention-delta, learned-DAG,
token-retention, numerical, GPU-memory, and CPU-preparation results are recorded in
`results/v4/stage81a3_rlc_causal_fast_probe.json` and its compact CSV companions.
Final bounded classification: **LINEAR COMPLETION MATCHES OR BEATS NEURAL RLC**. The no-automatic-follow-up hard
stop remains active pending human review.


## Conditional Predictability and Irreducible Uncertainty Audit

This bounded synthetic audit separated true biological factors (`F`), noise-free expected
molecular state (`LAMBDA_NORM`), and two independent sequencing realizations (`X_A`, `X_B`).
A TRAIN-only PCA-160 biological reference was fitted to expected expression. Twelve exact
40% masks compared random missingness, four coherent coexpression blocks, and an oracle
generator-label coverage diagnostic that is forbidden for real-data use.

Fixed ridge estimators and exactly five fixed diagnostic MLP fits measured visible-only,
conditional completion, replicate reliability, hidden-gene predictability, per-factor reporter
coverage and identifiability, latent-coordinate ambiguity, and paired factual/counterfactual
response prediction. No foundation model, JEPA, causal DAG, real RNA, or pathology data was
trained or accessed.

The full expected-state PCA reference retained mean factor R2
`0.999792`. Projecting the two
independent count replicates into that same basis retained
`0.915638` and
`0.912125`. Their median
factor-prediction correlation was
`0.932715`;
gene-level correlation and R2 distributions are both retained because exact count realization
is substantially less reproducible than biological factor state.

Median empirical count-based recoverable-gap fractions were RANDOM_40
`-0.383634`, COEXPRESSION_BLOCK_40
`-0.055923`, and ORACLE_COVERAGE_40
`-0.389083`. Noise-free visible expected state was already
within 0.05 of the full reference in all views, so its recoverable-gap fraction is correctly null
rather than forced to one. Ridge count-to-latent completion was consistently stronger than the
fixed nonlinear diagnostic but did not improve mean factor information over the visible count
state. Hidden expected genes remained more predictable than either exact sequencing realization.

Reporter coverage and recoverability were positively associated most strongly under coherent
block masks; the oracle coverage diagnostic did not restore count-based gap recovery. Across 160
coordinates, `33` were high-predictability,
`61` intermediate, and
`66` low under RANDOM_40. The paired causal sidecar
had median delta R2 `0.359364`
and remained partial, not a causal-training result.

Primary classification: **TARGET LARGELY UNIDENTIFIABLE UNDER 60/40 OBSERVATION**. Measurement-noise dominance was
`False`; graph-block identifiability
failure was `False`;
nonlinear-over-linear advantage was
`False`; and
counterfactual hidden-response predictability was
`PARTIAL`. These results
support carrying ambiguity explicitly rather than authorizing another deterministic completion
architecture. Human review remains required.


## Reproducible Biological State Basis Audit

RepPCA-160 was fitted without factor labels from the symmetrized cross-covariance of two
independent TRAIN sequencing realizations of the same synthetic biological cells. It is intended
to emphasize reproducible cross-replicate molecular variation. It is not assumed to be biological
truth, is not a pathway basis, is not pathology-informed, and is not yet a production representation.

The shared eigenspectrum contained `2059` positive,
`0` near-zero, and
`2037` negative directions under the fixed threshold.
RepPCA mean factor R2 was `0.999717` for expected biology,
`0.904077` for X_A, and `0.905963` for X_B. Pair-mean PCA
controls were `0.906045` and `0.903273` for the two
count replicates. RepPCA median coordinate replicate correlation was
`0.087298`;
its within/between distance ratio was
`0.782410`.

All frozen CP-IU masks passed exact whitened visible-plus-hidden decomposition. TRAIN-only
residual priors and replicate measurement-noise floors were recorded per realistic mask and
coordinate. Direct coordinate alignment to the old CP-IU PCA table is not defined across bases
and was not invented. Final classification: **REPRODUCIBLE STATE BASIS QUALIFIED FOR BELIEF-JEPA**. Qualification does
not authorize Belief-JEPA training; human review remains required.


## RBB-JEPA Belief Geometry Audit

State preservation and conditional predictability are distinct. Using the exact qualified
RepPCA-160 basis, this no-neural-training audit estimated TRAIN-only prior, replicate-noise,
and fixed-ridge conditional residual covariance for eight realistic masks, then scored diagonal
and full Gaussian geometry on SEALED cells. No coordinate is interpreted as a pathway, and no
factor label, expected-state target, real RNA, or pathology data entered uncertainty fitting.

Median conditional off-diagonal energy was
`0.282965`; median full-over-diagonal
held-out NLL improvement was
`-3.289779` nats per latent
dimension; median severe marginal non-Gaussian fraction was
`0.000000`. Classification:
**CORRELATED GAUSSIAN BELIEF REQUIRED**. This selects only a mathematical family for human review.
The classification was triggered by off-diagonal residual energy, not by superior full-covariance
scoring. Under the fixed estimator, full covariance worsened SEALED NLL, so an unregularized full
covariance is not deployment-ready; any correlated parameterization requires separate
regularization and human review.
Both covariance forms also underestimated held-out residual scale: median coordinate-level
standardized-error variance was
`30.156800`, and median diagonal/full
Mahalanobis means were `4870.461653` and
`5978.401158` versus an ideal 160-dimensional Gaussian mean
of `160`. With zero severe marginal-shape flags, this
is recorded as conditional-reference scale miscalibration rather than evidence for an automatic
mixture model.
No RBB-JEPA was trained or authorized.


## RBB-JEPA OUT-OF-FOLD CONDITIONAL UNCERTAINTY AUDIT

The preceding geometry audit correctly detected correlated conditional residual structure, but
its covariance scale came from residuals of a ridge predictor evaluated on the same cells used
to fit it. This audit therefore assigned every TRAIN cell to exactly one of eight deterministic
held-out folds, fitted the fixed symmetric ridge on the other seven folds, and estimated
conditional covariance only from concatenated out-of-fold errors. Factor labels, expected-state
values, SEALED cells, real RNA, and pathology did not enter fitting or rank selection.

Median OOF-to-in-sample coordinate variance ratio was
`64.427846`. The shared architecture rank selected
from TRAIN-only positive correlated energy was `9`. On SEALED cells,
median standardized variance was `0.468566`; median diagonal
and LRD Mahalanobis means were `75.559729` and
`77.690334` for a 160-dimensional target. Median diagonal-minus-LRD
NLL was `0.024943` nats per dimension.

Primary classification: **GAUSSIAN BELIEF FAMILY NOT YET QUALIFIED**. This is uncertainty-family qualification
only. It does not train or authorize RBB-JEPA, identify pathways, open pathology, or complete
Stage81A3.


## RBB-JEPA VALIDATION-CALIBRATED BELIEF COVARIANCE AUDIT

In-sample covariance underestimated predictive uncertainty because the residuals came from the
same cells used to fit the ridge mean. Eight-fold OOF covariance then overestimated deployment
uncertainty because each mean predictor used 2,688 rather than all 3,072 TRAIN cells. This final
audit fit the unchanged mean predictor on all TRAIN cells, estimated covariance exclusively from
512 untouched VALIDATION residuals, and evaluated all fixed covariance families once on SEALED.

Rank nine was frozen before this audit. The correlated controls were rank-9 LRD and analytic OAS;
OAS is a statistical upper-bound/control, not a proposed neural output head. Median SEALED joint
scale ratios were diagonal `0.995034`, LRD
`1.035008`, and OAS
`0.991429`. Median diagonal-minus-LRD and
diagonal-minus-OAS NLL improvements were
`0.015098` and
`0.001510` nats per dimension.

Primary classification: **CORRELATED GAUSSIAN SUPPORTED, BUT RANK-9 LRD UNDEREXPRESSIVE**. This remains a bounded uncertainty
qualification result. It does not train or authorize RBB-JEPA, alter rank, open real RNA or
pathology, or complete Stage81A3.

## RBB-JEPA Adaptive Correlated Belief Feasibility

One synthetic model (seed `8114001`) received exactly `150` optimizer updates. The visible
molecular state was factual and hard-preserved; only the missing RepPCA contribution was inferred
probabilistically. Conditional and measurement uncertainty remained separate, and coordinated
uncertainty used context-adaptive rank-32 capacity. Random missingness was allowed to remain
approximately diagonal, while coherent missingness could activate shared uncertainty. The full
4,096 x 160 gene-token molecular evidence ledger remained available. Correlated directions are
not called pathways, exact missing expression was not a target, and no real RNA or pathology was
accessed.

Primary classification: **TOKEN-PRESERVING ENCODER REGRESSED**.

Token retention passed: `False`. No-harm passed for both mask
families: `True`. Proper-score comparison against prior-only passed:
`True`. Joint calibration passed: `True`.

This is one bounded synthetic feasibility result, not biological validation, not Stage81A3
completion, and not authorization for Stage81B or real-data training.

## RBB-JEPA Frozen-Encoder Gradient-Interference Probe

This single-variable forensic follow-up reconstructed the original seed-8114001 step-0 model and
matched the prior retention ratio exactly (`1.0020574895396623`). The tokenizer and all six
token-preserving encoder blocks were frozen and detached; training-mode dropout 0.10 was retained.
Only belief-side parameters received optimizer updates.

The run completed exactly 150 belief updates. Retention remained `1.0020574895396623` at steps
0, 25, 50, 100 and 150, compared with `0.8811191875486374` at step 150 when the molecular encoder
was trainable. In-process frozen-state hash checks passed at all five milestones, and frozen
gradient checks were exactly zero at steps 1, 25 and 150. These observations support the specific
hypothesis that the prior end-to-end belief objective damaged the molecular representation.

Final scientific classification could not be completed. After all eight SEALED mask evaluations,
the new counterfactual changed-direction uncertainty calculation failed because a float64 direction
vector was combined with a float32 compact covariance. Atomic final outputs had not yet been
written and no model checkpoint existed. The model was not rerun or continued.

Primary classification: **ENGINEERING / NUMERICAL FAILURE**.

The dtype defect was corrected and regression-tested after the stopped run, but no follow-up model
or evaluation was authorized. Proper-score, calibration, correlated-component, replicate and
counterfactual conclusions from this frozen-encoder run therefore remain unresolved.

## RBB-JEPA Frozen-Encoder Exact Recovery Probe

This exact seed-8114001 repeat preserved the frozen molecular ledger and added only durable
serialization plus corrected counterfactual dtype handling. The belief-side checkpoint was written
immediately after update 150, before SEALED evaluation. Retention stayed at
`1.002057` and all molecular hashes and gradient-firewall
checks passed.

Primary classification: **GRADIENT INTERFERENCE CONFIRMED; FROZEN MOLECULAR LEDGER SUPPORTS RBB BELIEF**.

Correlated component: **NOT EARNED**.
Point-state recovery: **NEGLIGIBLE**.
Counterfactual sidecar: **NOT SUPPORTED**.

This supports molecular evidence preservation and is still synthetic qualification evidence. It
does not establish pathology biology, disease vulnerability/resilience, spatial validity,
regulator causality, perturbational world dynamics, cross-platform transfer, or permanently
unmeasured-panel generalization. The structurally unmeasured gene contract remains open before
final Stage81A3 freeze qualification.

## Structurally Unmeasured Genes and Heterogeneous Panel Qualification

This forward-only synthetic audit introduced four explicit measurement states: observed measured,
measured zero, training masked, and structurally unmeasured. A measured zero remains factual
evidence; a training mask hides a measured value and remains target-eligible; structural panel
unmeasurement provides no value and is never target-eligible. Panel-unmeasured genes may be
inferred only when observation support exists elsewhere in foundation data. Globally never-observed
genes cannot receive learned cell-specific inference from nonexistent data.

The frozen molecular ledger and belief checkpoint received zero optimizer updates. Legacy parity
and the structural-value firewall were tested at `1e-6`. Four nested random and four TRAIN-graph
coherent panel views covered FULL, P80, P60, P40, and diagnostic P20 measurements. Four
complementary P60 pairs had exact 2,458/2,458 sizes, 820-gene intersections, and 4,096-gene unions.

Primary classification: **MEASUREMENT SEMANTICS QUALIFIED; BELIEF REQUIRES STRUCTURAL-PANEL TRAINING EXPOSURE**.

Correlated component under structural panels: **NOT EARNED**.
Cross-panel cell identity: **SUPPORTED**.
P20 stress result: **UNCERTAIN BUT CALIBRATION-DEGRADED**.

This is synthetic architecture qualification only. It does not establish real biological validity,
pathology biology, regulator causality, spatial validity, perturbational dynamics, or Stage81A3
completion.

## RBB Belief-Only Structural-Panel Exposure

One seed-8114001 synthetic model received exactly 150 belief-only updates. Every effective batch
contained eight fixed 32-example strata: ordinary random/block replay plus random/coherent P80,
P60, and P40 panel simulation. The molecular ledger remained detached and hash-stable with zero
optimizer overlap and zero molecular gradients. Panel-simulated values were removed from model
input while an independent paired full-support observation supplied only the existing latent-state
residual target. No gene reconstruction target was introduced.

A single positive global covariance temperature was fitted on VALIDATION only across both panel
families and P80/P60/P40, then compared on SEALED data against the unchanged pre-exposure belief
and the panel-exposed belief. Factor labels were evaluation-only and SEALED was never used for
panel construction, training, scalar fitting, or checkpoint selection.

Primary classification: **SCALAR RECALIBRATION IS SUFFICIENT; NEURAL PANEL EXPOSURE NOT EARNED**.

Correlated component: **NOT EARNED**.
Point-state recovery: **NEGLIGIBLE**.
Scalar recalibration: **SUFFICIENT**.
P20 stress: **UNCERTAIN BUT CALIBRATION-DEGRADED**.
Cross-panel identity: **SUPPORTED**.

This is one bounded synthetic belief-training probe. It does not establish real biological
validity, disease biology, causality, spatial validity, perturbation dynamics, or Stage81A3
completion. The prior trainable-encoder failure, frozen-encoder engineering failure,
frozen-recovery success, and forward-only structural-panel classification remain separate evidence.

## Stage81A3 Core Architecture Simplification

This zero-update audit returned to the frozen-recovery belief checkpoint and did not use the
rejected panel-exposure weights. The Perceiver and CELL-token designs remain rejected because
they lost molecular information; the six-block token-preserving ledger remains frozen. The hard
gradient firewall is architectural because prior end-to-end belief gradients damaged ledger
retention. Exact hidden-expression reconstruction is not the objective: the core reports an
accountable belief over RepPCA state while preserving factual visible evidence exactly.

Structural unmeasurement remains explicit because an assay that did not measure a gene is not
evidence of biological zero. Neural panel-exposure training was rejected after it failed to add
held-out value. The adaptive learned correlated evidence branch was removed because three
independent evaluations found no earned value. Fixed prior correlation was retained unchanged;
its statistical directions are not called pathways, programs, or mechanisms.

Calibration remains a post-inference observation-regime layer, not biological state. Raw
conditional uncertainty, separate measurement noise, raw total uncertainty, and calibrated total
uncertainty remain exposed. Population-scale calibration asks whether the belief is approximately
wide enough overall; cell-level localization asks whether the model knows which individual cells
are relatively more uncertain. A scalar can improve the former without improving the latter.

Primary classification: **CORE ARCHITECTURE SUCCESSFULLY SIMPLIFIED; SCALAR CALIBRATION IS NOT ARCHITECTURE-SAFE**.

Adaptive correlated evidence: **REMOVED - UNEARNED**.
Fixed prior correlation: **RETAINED**.
Point-state recovery: **NEGLIGIBLE**.
Structural population-scale calibration: **PARTIAL**.
Structural cell-level localization: **NOT SUPPORTED**.

Counterfactual capability remains unsupported. This synthetic audit does not establish pathology
biology, causal dynamics, real-data validity, or Stage81A3 completion.

## Uncertainty Localization Identifiability Audit

This audit was run before any further architecture change because the prior structural-panel
localization failure could reflect either a noisy evaluation target or a genuinely weak uncertainty
mapping. The frozen simplified core received zero updates. One stochastic target can rank cells
poorly when target sequencing noise is large, whereas 32-replicate average risk estimates the
conditional expected predictive difficulty for a fixed visible observation. Expected biological
risk and measurement-noise risk were therefore kept separate.

The implementation audit corrected an important premise: the historical structural localization
gate used expected `LAMBDA_NORM` biological-state error, not one stochastic sequencing target.
That historical failure remains unchanged. The new B01 single-realization gate is reported
separately and cannot retroactively relabel the prior result.

Repeated-measurement disagreement was tested as a reproducibility diagnostic: it asks whether the
inferred state is stable across two legitimate observations of the same synthetic cell. The
evidence jackknife measured inference fragility after deterministic removal of additional valid
evidence; it is not causal importance or gene essentiality. Two fixed-alpha ridge regressions were
used only as ceiling probes for recoverable visible-evidence information. They are not architecture
proposals and no fitted weights were persisted.

Primary classification: **ENGINEERING / NUMERICAL FAILURE**.

Replicate-averaged risk reliability: **True**.
Original single-realization localization gate: **FAIL**.
Replicate-averaged total-risk gate: **PASS**.
Expected-biological-risk gate: **FAIL**.
Replicate disagreement: **STRONG**.
Evidence jackknife: **STRONG**.
Visible-evidence diagnostic ceiling: **ABOVE 0.50**.

All earlier single-target localization failures remain historical facts. This synthetic forensic
audit does not establish real-RNA validity, pathology biology, causal mechanisms, spatial biology,
regulatory pathways, perturbation dynamics, or Stage81A3 completion.

## Foundation Heterogeneity Reality Bridge Audit

This audit bridged the synthetic mechanics work to the actual pathology-blind foundation TRAIN
corpus without starting foundation training. It verified the frozen Stage81A2 contract at commit
`808ce4f170055c5568cc5c1e0e3a56415b52f908`: 13 datasets, 36 canonical matrix entries,
149 TRAIN donors, 19 development donors, 19 sealed donors, and 4,096 ordered vocabulary genes.
Only TRAIN expression was read. Development and sealed expression were not opened. Donor and
specimen identifiers were used only for split and leakage accounting. Pathology-bearing source
schemas were enumerated, but prohibited field values were not read.

Foundation integration was implemented as a shared observation contract over separately streamed
matrices, not as a physical matrix merge. Expression, gene identity, and measurement mask are
separate from provenance. Dataset ID, matrix ID, and donor ID remain provenance-only by default.
Measured zero remains measured evidence; structural unmeasurement remains explicit. No cell-level
RNA was written to result artifacts.

Three bounded engineering failures were corrected before the accepted run. The first source pass
found that one SEA-AD release used the explicitly authorized `Subclass` field when `Class` was
absent. The second completed the scientific calculations but failed in the final forward-smoke
summary because scalar attention denominators were concatenated rather than stacked. The third
completed all calculations and CSV/NPZ writes but strict JSON serialization rejected a NumPy
boolean. These were repaired with a whitelisted schema fallback, scalar stacking, and explicit
NumPy-scalar conversion. A final governance review then tightened class, tissue, assay, and cell-ID
reads to selected TRAIN indices only. Full donor/specimen identifiers were retained solely for
split/leakage checks. The accepted deterministic rerun completed in about 130 seconds.

The central measurement result was unexpected but internally exact: the original source feature
universes differ, including seven explicit NPH source-object universes, but every registered
universe contains every gene in the frozen 4,096-gene vocabulary. Consequently all 36 canonical
matrix masks collapse to one complete real mask, measured fraction is exactly 1.0, all genes have
support from all 13 datasets, and both matrix and dataset overlap graphs form one component at
0.25, 0.50, 0.75, and 0.90. The 4,096 bridge genes are measurement-connectivity genes only, not
biological hubs or regulators. Real structural-state deficit is therefore zero within this frozen
vocabulary and cannot qualify future genuinely targeted or narrower panels. A deterministic
60%-measured synthetic control omitted median diagnostic-state energy of about 92.46; synthetic
60/40 masking is therefore retained as a mechanism test and classified as harsher than the
current real frozen-vocabulary masks.

A TRAIN-only, matrix-equal, non-production `REAL_DIAGNOSTIC_PCA160` used 17,839 bounded cells.
It captured 34.59% of matrix-equal variance in 32 coordinates, 37.97% in 64, and 42.47% in 160.
Per-matrix 160-D retention ranged from about 31.70% to 53.18%. This supports an accountable 160-D
state as plausible, but not as a frozen production basis. PCA160 retained strong observation-domain
information: matrix balanced accuracy was about 0.874 and technology balanced accuracy about
0.884 in fixed TRAIN-internal linear diagnostics. Median coordinate eta-squared was low, but some
coordinates reached about 0.399 for dataset/technology and 0.573 for donor. These are observed
domain imprints, not automatic batch effects; tissue and region remain potentially legitimate
biology and were not regressed out.

All 36 matrices were registered as raw-count capable, and bounded complementary count splitting
preserved nonnegative integer counts, gene identity, masks, and exact partition accounting. This
earns broad measurement-uncertainty mechanics coverage, not biological ground truth. The bounded
normalization audit reproduced `log1p(10000 * count / library_total)`. Median matrix-level depth
and detection differed descriptively across sources: HVS approximately 15,163 UMIs and 2,415
detected vocabulary genes, NPH approximately 8,969 and 1,902, and SEA-AD approximately 19,522 and
2,748. These are observed domain shifts; normalization remains plausible with quality context.

No vocabulary-level higher-evidence reference edge met the fixed requirement of at least 0.90
containment plus 256 additional genes because all frozen-vocabulary masks are identical. Direct
paired higher-evidence teachers are therefore not established here, and higher-evidence reference
availability is classified as sparse. Count splitting may supervise measurement uncertainty later,
but it cannot substitute for biological-state supervision. Biological-state uncertainty,
measurement/predictive uncertainty, and domain/transfer uncertainty remain three distinct design
objects. No new uncertainty head was implemented.

The 64-cell CUDA token-ledger smoke returned finite `[64,4096,160]` outputs, changed no parameters,
used about 269 MB peak allocated VRAM, and performed zero backward calls, optimizer updates, or EMA
updates. All twelve hard bridge gates passed, including pathology, donor, specimen, vocabulary,
measurement semantics, overlap connectivity, loader, forward mechanics, and no-optimization gates.

Primary classification: **B. CORE ARCHITECTURE REMAINS VALID; REAL OBSERVATION /
DOMAIN CONTRACT NEEDS SPECIFIC REVISION BEFORE A3 FREEZE**.

Accountable 160-D state: **PLAUSIBLE-BUT-DOMAIN-QUALIFICATION-NEEDED**.
Normalization: **PLAUSIBLE-WITH-QUALITY-CONTEXT**.
Real measurement-mask library: **READY**, with one complete current-vocabulary mask.
Foundation overlap: **STRONGLY CONNECTED**.
Higher-evidence references: **SPARSE**.
Count-split readiness: **BROAD**.
Domain support: **CHARACTERIZABLE**.
Synthetic 60/40 masking: **TOO-HARSH for current masks; MECHANISM-ONLY**.
Real-data forward mechanics: **PASS**.

Before Stage81A3 freeze, measurement-mask input semantics and provenance-only identity policies
must remain explicit. Before production training, humans must select a source-balanced sampler,
qualify assay/technology/quality context, fit any real accountable basis on pathology-blind TRAIN,
and define legitimate higher-evidence supervision without fabricating perfect teachers. Domain and
biological-uncertainty neural machinery remain downstream and unearned.

Stage81A3 remains incomplete and unfrozen. Stage81B and Stage81C were not started. No production
foundation model, real neural optimization, production basis, sampler, checkpoint, pathology
analysis, or counterfactual capability was created.

## Foundation Biological State, Observation Process, Uncertainty Decomposition And Domain Transfer Qualification

### Scope and governance

Stage81A3-FBSDQ used pathology-blind TRAIN RNA only. It did not open DEV or SEALED expression, did not read pathology, and performed zero neural optimizer, backward, or EMA updates. The candidate arrays are diagnostic and are explicitly **not production-frozen bases**.

### What was tested

- Built deterministic donor-balanced samples capped at 2,048 cells per canonical matrix and gave every matrix equal covariance weight.
- Compared a balanced pooled-variance PCA160 basis with a balanced reproducible cross-count REP160 basis built from complementary 50/50 count splits.
- Refit both bases across eight deterministic donor folds and audited subspace stability, individual-axis stability, and near-degenerate rotating blocks.
- Tested same-cell count-split repeatability and retrieval, conditional technology imprint, technology-direction removal as a diagnostic only, and donor/matrix/dataset/technology transfer.
- Tested whether process and quality descriptors predict repeat-measurement instability in held-out matrices.
- Separated controlled biological-evidence removal (20/40/60/80/100% nested gene evidence) from count-depth thinning (25/50/75/100%).
- Constructed separate measurement-domain familiarity and biological-state support axes, plus an audit-only four-quadrant summary.

### Biological interpretation

Technology is treated as an observation process because the same underlying biology can be recorded differently by chemistry, platform, cell-versus-nucleus preparation, and depth. A strong technology signature is therefore not automatically removable batch: it may be entangled with real cell, tissue, or sampling differences. Count splits approximate repeated measurement of one cell; cross-count covariance emphasizes directions reproducible across those repeated measurements. Donors and matrices were balanced so a large source could not define the state merely by volume. Within-matrix centering was used only to choose REP directions and was not applied as permanent batch correction to final coordinates.

Subspace and axis stability were audited separately because an overall state space can remain stable while individual axes rotate inside near-degenerate blocks. Such rotation limits coordinate-wise uncertainty claims. Biological-evidence removal differs from depth thinning: the former removes kinds of molecular evidence after normalization, whereas the latter remeasures the same 4,096-gene evidence at lower count depth. The full view is therefore a higher-evidence reference, not biological truth, and its own count-split noise floor remains explicit.

The 4,096 x 160 molecular ledger remains the high-resolution molecular evidence contract. The 160-D state is an accountable global summary and is not expected to reconstruct every molecular detail. Tissue and region remain legitimate evaluation/context variables, not automatic nuisance covariates. Domain support is two-axis: unfamiliar measurement and unusual biology are reported separately.

### Observed qualification result

- Primary classification: **B. CORE ARCHITECTURE VALID; SPECIFIC PRE-FREEZE CONTRACT REVISION REQUIRED**
- PCA160: **QUALIFIED**
- REP160: **PARTIAL**; extra complexity **NOT EARNED**
- State subspace: **STABLE**; axes: **ROTATING-WITHIN-STABLE-SUBSPACE**
- Count-split reproducibility: **STRONG**
- Technology/biology: **MIXED**
- QC measurement context: **PARTIAL**
- Biology/measurement separation: **SUPPORTED**
- Ready for human A3 freeze review: **FALSE**

These results qualify or constrain mechanics only. They do not establish pathology biology, causal regulation, counterfactual capability, or production readiness.

## Pre-Freeze Resolution, Rare-State Preservation, And Read-Only Context Architecture

PRRC repaired two evaluation defects without changing the underlying FBSDQ measurements. Matrix transfer is now reported as **STRONG where identifiable / PARTIAL coverage** (10/36 units), separating performance from whether source label vocabularies permit evaluation. Weak aggregate donor balanced accuracy can coexist with high local neighbor purity because balanced accuracy penalizes missed classes equally while local purity asks whether immediate neighbors agree; rare and unevenly donor-spread labels can therefore dominate the former. The donor audit classified the root cause as **RARE-STATE DOMINATED** (cell-count rho=0.847; donor-breadth rho=0.480).

The previous QC comparison used a Spearman difference even when PROCESS_BASE predictions were constant, making the baseline rank statistic undefined. Repaired held-out MAE, R-squared, quality-model Spearman, and descriptive calibration slope yield **EARNED** measurement-context evidence: median relative MAE improvement 0.720, favorable matrices 1.000, median quality-model Spearman 0.975, and worst technology median improvement 0.497. QC may enter only the measurement/observation stream; dataset, matrix, donor, sample, and specimen identifiers remain provenance-only. Normalization remains PLAUSIBLE-WITH-QUALITY-CONTEXT and log1p/10k was not changed.

Donor transfer is interpreted separately from raw class abundance because donor breadth asks whether a state recurs across people. Annotation rarity is fixed at at most 1% and at least 100 cells; donor-recurring rarity additionally requires at least three cells in each of at least five TRAIN donors. The full TRAIN metadata census found 13 donor-recurring rare labels. Rare-state diagnostics compare normalized RNA, the complete 4,096-token molecular ledger, PCA160, and REP160 on the same deterministic bounded cells. REP remains not production frozen and its global complexity decision is not reopened. No predeclared catastrophic PCA compression flag fired, but preservation is not fully identifiable for: CN LAMP5-CXCL14 GABASubclass, EpendymalSubclass, STR RSPO2 GABASubclass, VipSubclass. Consequently **E. RARE-STATE IDENTIFIABILITY INSUFFICIENT** and the overall result remains **B. CORE INTRINSIC ARCHITECTURE VALID; RARE-STATE ISSUE REQUIRES PRE-FREEZE REVISION**. Microglia-PVM was identifiable and preserved without a critical PCA loss; several neuronal rare labels and other families remain partial because their bounded sample contains fewer than k+1 cells.

The 160-dimensional state is treated as a stable subspace whose individual axes may rotate. Near-degenerate coordinates use the fixed 0.01 relative eigengap rule, and uncertainty is reported as variance trace within each block; blocks are not pathways and axes are not assigned immutable biological meanings. U_BIO, U_MEAS, and U_DOMAIN remain distinct, while U_CONTEXT is established as a separate conceptual contract for incomplete or unreliable local context.

Intrinsic cell state and context are separate objects. The ContextReader is one-way and read-only, performs no iterative message passing, retains eight explicit context exemplars so rare neighbors cannot disappear solely through pooling, and can query neighbor molecular ledgers without mutation. Directional context A<-B need not equal B<-A, but this is contextual association rather than causality. Physical context may come only from experimentally grounded coordinates or adjacency, never RNA similarity. Existing MTG MERFISH, HPF/MEC MERSCOPE, and Caudate Xenium assets provide legitimate coordinates, but their 180-464-gene panels lack a paired full 4,096-gene target reference and some lack donor IDs. They therefore fail the fixed real-probe target contract; real context optimization was not run. Pathology remains closed, no plaque or tau entity was instantiated, and nothing supports returning to message-passing Graph-JEPA.

## TARGETED DONOR-RECURRING RARE-STATE COVERAGE RESOLUTION

The original PRRC bounded matrix-balanced sample contained too few cells from four globally donor-recurring rare populations to make the fixed k=15 preservation metric identifiable. RSCR therefore used deterministic donor-balanced targeted sampling of pathology-blind TRAIN cells only, without changing the vocabulary, normalization, molecular ledger, PCA160, REP160, rarity rules, comparator contract, k, or critical-loss thresholds.

Production-basis result: **A. PCA160 RARE-STATE COVERAGE RESOLVED - PCA160 REMAINS PRODUCTION BASIS PROPOSAL**

- **CN LAMP5-CXCL14 GABASubclass:** ADEQUATELY PRESERVED (256 cells across 37 donors).
- **STR RSPO2 GABASubclass:** ADEQUATELY PRESERVED (256 cells across 37 donors).
- **VipSubclass:** ADEQUATELY PRESERVED (256 cells across 37 donors).
- **EpendymalSubclass:** ADEQUATELY PRESERVED (256 cells across 34 donors).

Rare-neuron conclusion: **ADEQUATE**. Other rare-state conclusion: **ADEQUATE**. REP160 advantage: **NONE**.

The audit remained pathology-blind and read-only with respect to model parameters: zero intrinsic optimizer updates, zero backward calls, zero EMA updates, and zero context optimizer updates. Context mechanics and their real-data limitation were carried forward unchanged. Stage81A3 was not frozen and Stage81B was not started.

## COMPLETE DONOR-RECURRING RARE-STATE COVERAGE AUDIT

The four-state RSCR run was completed before scope expansion and retained as valid intermediate evidence. The amendment then applied the same pathology-blind targeted contract to all 14 donor-recurring annotation-defined rare states from a complete TRAIN metadata census. Foundation/domain sampling policy was not changed.

Production-basis result: **A. PCA160 RARE-STATE PRESERVATION QUALIFIED ACROSS DONOR-RECURRING ANNOTATION-DEFINED RARE STATES**. Robustly identifiable: 14; identifiable but sparse: 0; not identifiable: 0; critical PCA flags: 0; borderline stability states: 0. Microglia/immune: **ADEQUATE**; rare neurons: **ADEQUATE**; other families: **ADEQUATE**.

PRRC under-sampling classification: **SYSTEMATIC** (counts {'lt16': 5, '16_to_31': 2, '32_plus': 7}). Every robust state used four predeclared donor-balanced resamples. REP160 remained diagnostic and was not promoted. Annotation-defined rare-state coverage is not equivalent to exhaustive discovery of all rare molecular states.

The molecular ledger parameter hash was unchanged. No pathology, DEV, or SEALED expression was opened; optimizer, backward, EMA, and context-update counts remained zero. Context mechanics and real-context NOT-TESTABLE status were carried forward unchanged. Stage81A3 was not frozen and Stage81B was not started.

## PATHOLOGY-BLIND RARE-BIOLOGY COMPLETENESS AUDIT

Channels B/C extended annotation-defined RSCR with a fixed family-wise bounded discovery audit: complete RNA and ledger local-isolation at k=30, top-1% candidate designation, deterministic overlap neighborhoods, technical-association firewall, rotation-stable continuous extremes, donor recurrence, and donor-fraction saturation. No clustering or hyperparameter shopping was performed. The family cap was set to 1,024 so a 75% donor subset can mathematically satisfy the unchanged five-donor recurrence rule; no rarity or evidence threshold was altered.

Classification: **D. RARE BIOLOGY DISCOVERY NOT SATURATED / DATA COVERAGE INCOMPLETE**. Candidate cells: 105; neighborhoods: 65; donor-private biological candidates: 41; donor-recurring neighborhoods: 3; RNA+ledger rare/PCA-not-rare recurring states: 1 (0 stable); RNA-rare/ledger-not-rare recurring review flags: 1 (0 supported architecture failures); high-technical-concern candidates: 10; saturation: **SATURATING**. All 3 donor-recurring data-defined neighborhoods failed the four-resample recurrence-stability check. The raw RNA-to-ledger review flag had mixed technical association and was unstable, so it does not support another intrinsic architecture run.

This concerns rare cellular states, not disease-related abundance. Annotation-defined coverage and bounded data-defined discovery do not prove exhaustive discovery of all rare molecular biology. The full molecular ledger remained parameter-identical; PCA160 and REP160 were not refit or promoted. **Ready for human A3 freeze review: NO.** Pathology, DEV, and SEALED expression remained closed; optimizer, backward, EMA, and context-update counts remained zero. Stage81A3 was not completed or frozen and Stage81B was not started.

## UNIFORM CONTEXT DATA QUALIFICATION AND HUMAN PROVENANCE ADJUDICATION

The frozen UCDQ contract was applied uniformly to 21 acquired context datasets and 234 sample records. The original automated result was **REAL CONTEXT QUALIFICATION NOT IDENTIFIABLE** because SCP2167's publication provenance had not yet been human-adjudicated. That run nevertheless established that SCP2167 passed every non-provenance broad same-entity gate: 36,601 source features, all 4,096 frozen genes, raw UMI counts, nucleus resolution, physical XY coordinates with unknown units, and 4,065 of 4,067 exact spatial matches with no duplicated identifiers. Its automated provenance remained `UNKNOWN`, so its original role was `QUARANTINED_PENDING_GOVERNANCE`.

The original governance history remains immutable. A generic `disease=normal` value was incidentally displayed in a terminal preview before the audited reader ran; it was not used in qualification, and the audited code blocked pathology-like fields. Therefore **ORIGINAL UCDQ GOVERNANCE-COMPLIANT COMPLETION: NO**, while **UCDQ QUALIFICATION COMPUTATION COMPLETE: YES**.

The human reviewer subsequently adjudicated SCP2167 using only Russell AJ et al., *Slide-tags enables single-nucleus barcoding for multimodal spatial genomics* (Nature 2024;625:101-109; DOI 10.1038/s41586-023-06837-4; PMID 38093010; PMCID PMC10764288). The publication identifies the human prefrontal-cortex donor as neurotypical and identifies SCP2167 as the human-brain deposition. This changed provenance from `UNKNOWN` to `NEUROTYPICAL_DECLARED` without changing the UCDQ contract, thresholds, or non-provenance evidence. The unchanged gate therefore assigns SCP2167 `CORE_SAME_ENTITY_BROAD_CONTEXT`.

Post-adjudication identifiability is **YES** for bounded real context value, **YES** for cross-donor context value, and **YES** for cross-technology context replication. The broad anchor is one-donor Slide-tags SCP2167; independent directly measured replication is supplied by five eligible Fang STG MERFISH experiments across two donors and 954 frozen genes. The five Fang MTG experiments remain quarantined for surgical-provenance review and were not used.

This result establishes that a real context-value experiment is identifiable, not that context benefit has been demonstrated. No physical-neighbor graph, context masking, experiment, model training, optimizer update, or architecture change was performed. Stage81A3 remains unfrozen and Stage81B was not started.

## CHECKPOINT GOVERNANCE AMENDMENT: ADDRESS SPACE AND REPRESENTATION RESOLUTION

The repository checkpoint review identified two linked but independent open
architectural blockers that postdate the completed audits above. This amendment
does not rerun, delete, or reinterpret the historical experiments.

First, the frozen 4,096-gene vocabulary was a configured top-K capacity after
eligibility and ranking, not a transcriptome-derived biological saturation
point. Stage81A2 remains immutable historical evidence, but a versioned
maximal-exact-transcriptome data-contract revision is required before
Stage81A3 Freeze 1.

Second, the number 160 has two distinct historical roles that must no longer be
implicitly tied together:

- `d_gene=160`: learned contextual width per Molecular Ledger gene token;
- `d_cell=160`: PCA160 global whole-cell coordinate resolution.

Expanding the biological address space `G` adds explicit gene tokens and does
not require compressing all genes into one 160-dimensional vector. The per-gene
contextual width is therefore a model-capacity parameter whose future
sufficiency remains unresolved. PCA160 is a genuine global compression and must
be treated as a derived summary rather than the complete molecular identity of
a cell. The canonical Molecular Ledger should continue to retain explicit gene
identity, observed expression, and measured/unmeasured state in addition to any
learned context vector.

Future qualification must decouple `G`, `d_gene`, and `d_cell`. Global state is
a resolution question; if no defensible saturation exists, multiple nested or
multiresolution summaries may be required instead of replacing 160 with another
arbitrary fixed number. No vocabulary change, width change, PCA change, sweep,
evidence regeneration, Stage81B work, or Stage81C work occurred in this
checkpoint.

**BIOLOGICAL GENE ADDRESS SPACE: OPEN BLOCKER**

**GENE-TOKEN CONTEXTUAL CAPACITY: OPEN BLOCKER**

**GLOBAL-STATE RESOLUTION: OPEN BLOCKER**

**STAGE81A3 COMPLETE: NO**

**FREEZE 1 DECLARED: NO**

**STAGE81B STARTED: NO**

**STAGE81C STARTED: NO**
