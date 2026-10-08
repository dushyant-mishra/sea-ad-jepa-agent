# Stage81A1 Local Multimodal Inventory

## Scope

Stage81A1 is a read-only, decision-grade inventory governed by the frozen
Stage81A0 contract. It identifies local inputs for v4A expression learning and
later v4B regulatory, v4C spatial, and v4E perturbation work. It does not build
a training matrix, assign donor splits, train a model, download data, inspect
pathology values, or establish biological performance.

Run from the Git repository root with the project Python environment:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/stage81a1_audit_local_multimodal_assets.py --project-dir .
conda run -n sea-ad-jepa-v3 pytest -q tests/v4/test_stage81a1_multimodal_inventory.py
```

## Expression Decision

The immediate v4A-compatible candidate is
`data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad`.
It contains 40,000 Microglia/PVM nuclei from 89 donors, uses `X`, has unique
cell and gene identifiers, and exactly recovers the frozen v3 2,957-feature
order. Its `X` values are library-size normalized to 10,000 counts per cell and
then transformed with `log1p`. This conclusion is based on the builder code,
the independently reviewed Stage76 preprocessing provenance, and bounded
numeric checks; it is not inferred from value ranges alone.

The full source
`data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad` is retained as
the Stage81A2 vocabulary source. Its `uns/X_normalization` states
`ln(UP10K+1)`, while integer counts remain in `layers/UMIs`. Its 36,601 unique
gene symbols include all ten audited regulators and all 27 Stage75 targets.
Stage81A2 must explicitly choose whether v4A retains the exact 2,957-feature
v3 vocabulary or rebuilds a versioned vocabulary from this full source.

The canonical donor field is `Donor ID`; the canonical nucleus identifier is
`obs_names`. Final donor split assignment remains outside this stage.

## Gene And Regulatory Findings

The selected 2,957-feature matrix contains STAT1, ELF1, SPI1, IRF8, BACH1,
MITF, NRF1, and STAT3. CEBPA and RELA are absent. It contains 25 of 27 unique
Stage75 target genes. The full source contains all ten regulators and all 27
targets, so these are vocabulary exclusions rather than unresolved aliases.
No aliases were silently converted and no duplicate genes were collapsed.

Four graph/evidence lineages are frozen separately:

1. Stage27C/35C predictive or module graph.
2. Stage51 local STRING protein-association graph.
3. Stage75-79 directed TF-target perturbation candidate graph.
4. Motif, enhancer, ATAC, cisTarget, and coactivity evidence not promoted to a
   predictive graph.

The Stage75-79 source may be considered later as a soft v4B prior only with
the controls required by Stage81A0. Motif support is not causal regulation;
coactivity sign is a predicted response sign, not proven activation or
repression; and no source is labeled a validated GRN.

## Spatial And Perturbation Findings

No qualifying local SEA-AD spatial expression asset was found with a measured
panel, coordinates, documented coordinate units, tissue-section identity, and
donor linkage. Spatial panel, coordinate, section, and donor-linkage readiness
therefore remain independently false. SEA-AD MTG MERFISH, A9 expression, and a
multiregion release are recorded as absent; no download was attempted.

Two experimental perturbation families are local:

- Replogle-Weissman K562 genome-wide Perturb-seq is suitable only for generic
  controller or metric development because its biological domain gap is high.
- GSE178317 iTF Microglia expression and sgRNA assets are a promising future
  microglia calibration candidate, but perturbation assignments, controls,
  replicate units, normalization, and role separation remain unresolved.

Neither asset validates adult human AD microglial biology. A perturbation used
for calibration cannot later be called clean held-out validation.

## Pathology Firewall

The audit records pathology-related field names and file headers only. It does
not read pathology values, calculate distributions or associations, choose
features or splits from pathology, or use pathology for readiness decisions.
The v4 foundation remains self-supervised and pathology-label-free.

## Readiness Meaning

`stage81a1_pass=true` means that the local audit executed honestly,
deterministically, and without altering source data. `expression_v4_ready=true`
means the selected matrix has a resolved slot, transform, donor field, cell
identity, gene identity, feature order, and source hash. It does not freeze the
final v4 vocabulary or authorize training. `tf_prior_ready=true` means the
candidate evidence and its distinct lineages are identified with deterministic
gene reconciliation and bounded future roles; it does not validate the prior.

Stage81A2 should freeze the expression vocabulary, ordered gene-identity map,
and target/regulator coverage before any v4A matrix is built.
