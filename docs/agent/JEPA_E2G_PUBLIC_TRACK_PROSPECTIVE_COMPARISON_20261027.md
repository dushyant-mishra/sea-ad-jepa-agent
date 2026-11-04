# Prospective, non-deciding comparison: seven public E2G browser tracks (2026-10-27)

**Written before fetching full track bodies or inspecting target-gene overlaps.**
Status: `PROSPECTIVE_DESCRIPTIVE_CONTRACT__NO_BIOLOGICAL_TARGET_SELECTION`

## Fixed inputs

Historical project source: `results/v4/stage81a1b_existing_regulatory_evidence_integration.csv`,
Git blob `87117c485c25f9c7295a6ac4ba5ca48b45c844aa`, 96 unique
TF→target candidate rows and 27 unique target-gene symbols.
Preserve the seven-TF and 27-target counts, do not modify candidate rows,
and do not re-read sealed data.

Public E2G portal `getDataTracks` source IDs, preselected by biological
context and file accessibility, **not by any target-gene scores**:

1. `inflammatory_macrophage_ENCSR593WXK`: inflammatory macrophage, treatment unspecified, ENCODE-rE2G.
2. `inflammatory_macrophage_ENCSR643ZGR`: LPS 1 hour, ENCODE-rE2G.
3. `inflammatory_macrophage_ENCSR226JLK`: LPS 4 hour, ENCODE-rE2G.
4. `Macrophage`: Macrophages 3, Ma/Conley scE2G.
5. `Immune_monocyte_1`: Macrophages 1, Ma/Conley scE2G.
6. `brain_ENCSR344FLH`: broad brain source, ENCODE-rE2G.
7. `Stitziel_hCA_Myeloid`: coronary-artery myeloid, Amrute scE2G.

All seven advertised files were **HEAD 200**, with content-length
**1.6–7.8 MB**, on `storage.googleapis.com`. Public track URLs were
authenticated by `getDataTracks` via E2G GraphQL. Never use GCS
`gs://e2g` requester-pays bucket or create charges.

## Parsing, metrics and ceiling

- Require exact ID and uniqueness, HTTPS allowed hostname, no signed query;
  check HEAD length <= 9 MB; cap total at 50 MB, each uncompressed file
  <= 100 MB; record SHA-256 of exact bytes; stop if exceeded.
- Source files are browser BEDPE-like, with 10 tab columns in sampled rows:
  enhancer chrom,start,end; target chrom,TSSstart,TSSend; name; score; two
  additional annotation columns. No header in sampled range.
- Gene symbol is the portion before `|` in the BEDPE name field; scE2G
  suffixes `_promoter`, `_genic`, `_intergenic` may be stripped
  **only** when they leave an **exact** match to one of the 27 historical
  symbols. Do not silently fuzzy map, collapse paralogs or assume Ensembl ID.
- Accept score only when finite in [0,1], validated chrom/start/end,
  same enhancer and target chromosome. Preserve all records with valid
  parsing; fail closed on structural drift.
- Per source and target-gene symbol: count predictions, distinct enhancer
  intervals, promoter-proximal (<20kb center-to-TSS), distal (>=20kb),
  maximum score. Produce total file row/target counts to contextualize.
- Source comparison is **descriptive** only. Scores/thresholds across
  scE2G and rE2G are not calibrated to one another; absolute count
  comparison may reflect assay/pipeline depth and censoring.
- Temporal labels **LPS 1/4 hours do not establish a longitudinal
  trajectory or matched donor time course**. They are per-source contexts.
- A same-symbol prediction does **not** validate a specific TF→gene
  edge or enhancer/TF physical link. Until each external source has
  authenticated Ensembl identity, call it `PROVISIONAL_SYMBOL_OVERLAP`.
- Target absence in a thresholded browser file is **NOT_ESTIMABLE**
  for regulatory absence, not a biological negative.
- No statistical p values, fold changes, causal claims, target
  re-ranking, score-cutoff optimization, or JEPA architecture change.

If the public files cannot be read safely, preserve only access failures
and do not fake comparison outputs.

## Retained scientific controls for future authorized confirmation

The source-specific E2G evidence must later be joined by authenticated
enhancer coordinates, canonical gene IDs, context and provenance; compare
with distance-only, ABC-only when legitimate, and matched randomized
interval→gene controls. Only independent biological replicates can support
donor-level uncertainty. Previously failed randomized graph auxiliary
remains failed; no automatic reinstatement.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
