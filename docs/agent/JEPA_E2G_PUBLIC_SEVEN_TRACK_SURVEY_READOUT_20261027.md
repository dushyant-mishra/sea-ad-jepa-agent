# Seven-source public E2G contextual survey — executed readout (2026-10-27)

**Current result:** `SEVEN_TRACKS_READ__PROVISIONAL_GENE_SYMBOL_OVERLAP__NO_TF_EDGE_VALIDATION__NO_TARGET_AUTHORITY`

The execution followed the prospective contract at
`docs/agent/JEPA_E2G_PUBLIC_TRACK_PROSPECTIVE_COMPARISON_20261027.md`.
The contract was committed **before** the full seven reference tracks were
downloaded and before target-gene results were inspected. Inputs were seven
publicly accessible portal IGV browser tracks; no requester-pays billing
project, SEA-AD raw matrices, controlled fragment data, or protected
pathology data were accessed.

Full one-shot result: GitHub Actions run
https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40516374655
(job `122231225045`), **success**, 10 hostile unit tests passed.
The full 54,322-byte JSON receipt is in the Actions artifact
`e2g-public-seven-track-provisional-symbol-survey`,
with SHA-256 `140bcd212cff9d05d8458ff52d81b65573fb6d48fedfa7c940db92ceaf889c2e`.
The artifact has 14-day retention. The durable small mirrors in this PR
preserve all 27 target-gene counts, all 27 target-gene distal counts,
seven exact source-byte SHA-256 hashes and execution/custody information.

An earlier RED test run `40516264862` identified an implementation defect
in the Git-blob NUL delimiter used to authenticate Stage75. That defect
was fixed before the successful run, not waved away. In particular the
successful test matched Stage75 blob
`87117c485c25f9c7295a6ac4ba5ca48b45c844aa`.
This did not reopen Stage75 graph hypotheses.

## Source-level result

| Public browser track | Total track E2G rows | Rows for 27 frozen Stage75 target symbols | Target symbols with any row | Panel rows >=20kb from TSS | Panel target symbols with a >=20kb row |
| --- | ---: | ---: | ---: | ---: | ---: |
| rE2G inflammatory macrophage (treatment unspecified) | 84,593 | 190 | 27 | 59 | 17 |
| rE2G inflammatory macrophage, LPS 1h | 85,719 | 194 | 27 | 60 | 19 |
| rE2G inflammatory macrophage, LPS 4h | 84,048 | 199 | 27 | 65 | 18 |
| scE2G Macrophages 3 | 52,580 | 197 | 26 | 60 | 17 |
| scE2G Macrophages 1 | 57,159 | 225 | 27 | 77 | 20 |
| rE2G broad brain sample | 62,378 | 62 | 17 | 23 | 7 |
| scE2G coronary-artery myeloid | 70,980 | 273 | 26 | 106 | 21 |

**These are not observed gene regulation or validation metrics.**
The thresholded browser BEDPE names contain target **symbols** (with
model-specific element-class suffixes), not canonical Ensembl IDs.
We matched the exact 27 historical symbol tokens, with only explicitly
predeclared `_promoter/_genic/_intergenic` suffix removal.
No external same-cell measurement or TF-bound enhancer source was
used. All positive gene matches are **provisional annotations only**.

Every gene in the panel has a prediction in each of the three macrophage
rE2G contexts. This alone is **not a discriminative or independently
validated biological result**. Many predicted links are promoter proximal:
only 59/190, 60/194 and 65/199 panel links, respectively, are >=20kb
from the target TSS by the predeclared geometry-only definition. This
is not a regulatory-element or experimentally validated distal enhancer
designation.

For illustration, without ranking or selecting targets:

- `IRF8`: 24/18/23 prediction rows in the three inflammatory-macrophage
  contexts, including 10/8/10 >=20kb geometrically distal rows.
- `TREM2`: 5/7/10 rows (distal 1/1/3) in those three contexts, with
  zero rows in the selected broad brain and scE2G Macrophages-3 files.
  These zero rows are **not** proof that regulation is biologically absent.
- `APOE`: 6/6/10 rows (distal 1/2/3) in those contexts; the single broad
  brain track had 4 rows, none >=20kb. No causal link is inferred.
- `CD74`: 3/4/3 rows (distal 0/0/0) in those contexts. A proximal-only
  annotation does not establish that no distal enhancer exists.

The three Gschwind-labeled ENCODE biosample accessions are different
source IDs. They are **not an authenticated paired time course**,
replicate series, age trajectory or Alzheimer's-specific biological
experiment. Counts are thresholded by the publication workflows;
scE2G vs rE2G outputs, and even different assay contexts within a family,
can be affected by thresholds, chromatin input and target-gene measurement.
We did not conduct formal significance testing, normalization across files,
effect-size inference or perturbation validation.

The full source files are hash-pinned in
`results/regulatory/e2g_public_7track_provisional_result_receipt_v1_20261027.json`.
Compact gene-by-source tables:
`results/regulatory/e2g_public_7track_27gene_prediction_counts_v1_20261027.csv`;
`results/regulatory/e2g_public_7track_27gene_distal_counts_v1_20261027.csv`.

## Scientific interpretation and next evidence gate

The published atlas has useful **gene-level regulatory-context coverage**
for our historical targets, without additional cloud billing or new raw
sequencing. There is currently **no direct human adult microglia-labelled
track**, no donor-resolved disease comparison, no authenticated external
Ensembl identity reconciliation, and no TF→enhancer→gene chain allowing
Stage75 `TF→target` edge validation.

Any future decisive use requires all of:

1. Resolve target gene symbols to frozen **source-authenticated,
   unversioned Ensembl gene IDs** and verify external E2G gene identifiers
   with a real independent mapping rather than symbol guesses.
2. Recover enhancer coordinates with build and interval convention,
   authenticate motif/TF-to-element occupancy on the relevant peaks, and
   preserve score/model/assay provenance.
3. Separate broad brain, macrophage, culture, vascular and microglia
   contexts; treat proxy transfer as a hypothesis, not direct microglial
   evidence.
4. Run distance-only/ABC-only and matched randomized element→gene
   controls on a prospective target and split contract, with donor/source
   units where genuine biological replicates exist.
5. Obtain direct perturbational evidence for any causal language.
   Reopening the previous **failed randomized graph auxiliary** requires
   its own new scientific estimand and authority.

No JEPA target, representation, Stage4 or real training is authorized.
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
