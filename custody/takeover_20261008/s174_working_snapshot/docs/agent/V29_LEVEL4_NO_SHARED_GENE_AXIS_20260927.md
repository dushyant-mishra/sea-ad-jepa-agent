# The Level-4 blocks have no shared gene axis — and the data is intact

Date 2026-09-27. Producer `scripts/v5/full104_level4_permutation_recovery_v1.py`,
receipts `results/v29/FULL104_LEVEL4_PERMUTATION_RECOVERY_HVS_V1.json` and
`…_SEAAD_V1.json`. Follows
`V29_LEVEL4_GENE_IDENTITY_DEFECT_AND_RETRACTIONS_20260927.md`.

## Three findings, and the first two are good news

**1. Nothing was lost.** Matching Level-4 columns to source columns by the exact
pattern of which nuclei are nonzero and at what value:

| matrix | nuclei | matched uniquely | too sparse to match | **no matching source column** |
|---|---|---|---|---|
| `HVS::c5e9db26-…` | 512 | 15,149 | 2,272 | **0** |
| `sea_ad_mtg_rna_final_2026` | 512 | 21,265 | 5,361 | **0** |

Zero unmatched in both. Every Level-4 column is exactly some source column. The
counts are complete and correct; only their position is wrong. The "too sparse"
group is genes detected in one or two nuclei at a count of one, whose pattern is
not distinctive enough to match from a single block — more blocks resolve them.

**2. It is recoverable.** Because the map is exact and injective, a per-matrix
decoder can be built by fingerprint matching against the authenticated source,
without rebuilding the substrate.

**3. But there is no shared gene axis, and that is the serious part.** Of the
13,386 genes recovered in *both* matrices, the number that sit at the same
Level-4 column in both is **zero**:

| gene | address the namespace assigns | actual HVS column | actual SEA-AD column |
|---|---|---|---|
| APOE | 6,186 | 22,730 | 36,012 |
| CSF1R | 14,980 | 6,276 | 10,864 |
| CD74 | 392 | 6,283 | 10,871 |
| P2RY12 | 12,469 | 4,436 | 7,401 |
| TREM2 | 2,044 | 6,949 | not recovered |
| C1QA | 13,365 | 286 | not recovered |

Column *j* denotes a different gene in every matrix. The 41,238-wide
"common molecular address space" that the Level-4 blocks appear to implement is
not what their columns actually are.

## What the ordering looks like

Within a matrix the ordering is internally consistent and looks genomic. CD74
and CSF1R are neighbours on chromosome 5, and they sit 7 columns apart in HVS
(6,276 and 6,283) and 7 apart in SEA-AD (10,864 and 10,871). The HVS map is
monotone in that source's own `var` order; the SEA-AD map is not, so the two
matrices were not written by the same rule. Neither matches the address
namespace ordered by index, by symbol, or by address ID as a string — all three
were tested and all three scored 0.0%.

`successor_gene_index` in `matrix_measurement_support.csv.gz` is not the decoder
either: it reproduces the namespace order (0 = TSPAN6, 1 = TNMD) and agrees with
the recovered map on 0 of 15,149 HVS columns.

## What this invalidates

Any computation that treats Level-4 column *j* as the same gene across matrices.
That is the entire premise of a 104-donor, 42-operator, three-source corpus, so
it reaches every cross-source gene-level result derived from these blocks.

It does **not** reach:

- the authenticated metadata (`foundation_metadata_rows.sqlite`), which carries
  no expression;
- the eligibility census built from it;
- row identity in the blocks, which is correct — `canonical_cell_id` matches the
  source object's own index at `expression_row`, `source_library` matches that
  row's total, and identity closure held across 8,076 blocks and 187,909 of
  187,909 nuclei;
- per-cell library totals, which are order-independent and correct;
- Level-1, Level-2 or Level-3 blocks, which were not examined and must not be
  assumed to share the defect or to be free of it.

## The honest limit on the diagnosis

A per-matrix decoder may exist somewhere in the project that I have not found,
in which case the blocks are correct and only my reading of them was naive. What
is established is narrower and sufficient to act on: **no decoder is present in
the Level-4 artifacts themselves**, the naive assumption that column equals
`molecular_address_index` is wrong for every matrix tested, and no two matrices
agree on any gene's position.

The materialization contract records `selection_sha256`,
`selection_manifest_sha256`, `freeze_manifest_sha256` and `code_sha256`, and
references none of the registry semantic hash `5fc4c03e…` that the loader
manifest and `address_namespace.csv` share. That is consistent with the blocks
having been written against a different address authority, and it is where the
search for an existing decoder should start.

## Next

1. Search the project for an existing per-matrix column decoder before building
   one. If the materialization code (`code_sha256`
   `575d02a4e7f7c5c6f3187eeed691a2eac7d3f1df9510621bc497b283806c270b`) can be
   located, it names the rule directly.
2. If none exists, build decoders by fingerprint matching across several blocks
   per matrix, which resolves the sparse remainder, and verify each against the
   authenticated source before use.
3. Check whether Levels 1–3 share the defect.
4. Verify NPH52, whose R `.qs` source still has no reader.
5. Re-run the ladder only after a decoder passes verification.
