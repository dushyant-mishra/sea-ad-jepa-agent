# Level-4 gene identity is scrambled; results built on it are retracted

Date 2026-09-27. Verifier `scripts/v5/full104_level4_gene_identity_verifier_v1.py`,
receipt `results/v29/FULL104_LEVEL4_GENE_IDENTITY_VERIFIER_V1.json`.

## The finding

In the FULL104 Level-4 expression blocks, each nucleus's counts are complete and
belong to the right nucleus, but they are assigned to the **wrong molecular
addresses**. Verified against the authenticated source assets named in
`ASSET_AUTHENTICATION.csv`:

| matrix | row identity | column agreement | value multiset identical |
|---|---|---|---|
| `HVS::c5e9db26-…` | 8/8 | 5.8% | 8/8 |
| `HVS::19cd530b-…` | 8/8 | 8.0% | 8/8 |
| `sea_ad_mtg_rna_final_2026` | 8/8 | 4.2% | 0/8 |
| `sea_ad_pfc_a9_rna_final_2026` | 8/8 | 4.4% | 0/8 |
| `NPH52::matrix::MG_…qs` | NOT VERIFIED — R `.qs` source needs its own reader |

Row identity means the block's `canonical_cell_id` equals the source object's
own index at `expression_row` AND `source_library` equals that source row's
total. Column agreement means the Level-4 value at address A equals the source
value for the gene the address namespace says A is. For the two HVS matrices the
value multiset is identical cell for cell, so nothing was lost or invented: it
is a pure reordering.

Around 4–5% agreement is what chance produces at these count distributions,
where many entries are 1 or 2 and can land on an address that happens to be
nonzero anyway.

## How it surfaced

Extracting R8's gene panels gave biologically impossible numbers. C1QA was
detected in 0.0% and CSF1R in 0.2% of 512 SEA-AD middle-temporal-gyrus nuclei;
APOE and CSF1R in 0.0% of an HVS myeloid block while TREM2 showed 79.3%. The
HVS source object carries APOE at 66.5%, CSF1R at 55.0% and TREM2 at 14.5%.

## What was ruled out first

- All 29 panel addresses hold exactly the intended symbol, all `current_exact`.
- None appears in the collision ledger.
- The support ledger declares every one measured in every matrix checked.
- Every CSR row is index-sorted, and a dense readback that assumes nothing about
  ordering reproduces the extraction exactly.

So the extraction code is correct and the fault is upstream of it.

## Two identifier traps that produced false readings on the way

Both are recorded because either one alone would have looked like the defect.

1. The HVS CELLxGENE object indexes `var` by Ensembl ID; the SEA-AD object
   indexes by SYMBOL and keeps Ensembl IDs in `var['gene_ids']`. Joining an
   Ensembl-keyed namespace to a symbol-keyed index returns exactly 0.0%
   agreement for reasons that have nothing to do with the data.
2. Raw counts are in `raw/X` for the CELLxGENE objects and in `layers['UMIs']`
   for the SEA-AD objects; `X` is normalized in both. Comparing against `X`
   gives a mismatch that is an artifact of the layer choice.

The verifier now locates an Ensembl column explicitly, refuses to run without
one, picks a raw-count layer explicitly, checks that the layer is integral, and
records both choices in the receipt.

## Retracted

Every gene-level result computed from the Level-4 blocks in this cycle:

- `results/v29/FULL104_RESOLUTION_LADDER_V1.json` — all rungs, all cohorts,
  all three programs. The genes are not the genes.
- The per-gene detection rates by source reported in the same cycle.
- Any reading of which R8 program is measurable in which source.

## Not retracted

- The microglial eligibility census. Metadata only: 187,909 candidate myeloid
  nuclei, the per-source breakdown, and the SEA-AD supertype resolution at
  coverage 1.0000 with 138,242 of 138,242 donor IDs agreeing. No expression is
  involved in any of it.
- The extraction machinery. Row identity, per-block SHA-256 verification and
  identity closure all held — 187,909 of 187,909 nuclei recovered exactly once,
  zero duplicate `selection_row`, zero donor mismatches across 8,076 blocks.
  That machinery is what made the defect visible.
- `results/v29/R8_DEPTH_VS_PROGRAM_DISPERSION_V3.json`, which used R8's recorded
  summary statistics rather than the Level-4 blocks. It is not falsified by this
  defect, but R8's own 361-cell development cache was built from the same
  address space, so R8's inputs are now suspect and its numbers should not be
  treated as established until that cache is verified the same way.

## NPH52 is unverified, which is not the same as correct

The NPH52 microglia matrix looked biologically coherent — P2RY12 95.4%,
CD74 93.2%, CSF1R 90.0%, CX3CR1 88.8% — which is a textbook microglial profile
and unlikely to arise from a scrambled mapping. That is suggestive and it is not
evidence. Its source is an R `.qs` object that this verifier cannot read, so its
gene identity is **NOT VERIFIED**. No NPH52 result should be reported as
established until a `.qs` reader is added and the same check passes.

## What has to happen next

1. Find the permutation. The HVS case is a pure reordering, so the correct
   mapping is recoverable by matching Level-4 columns to source columns across
   many cells rather than rebuilding the substrate from scratch.
2. Determine whether the defect is in the materialization or in the address
   ordering the blocks were written against. The materialization contract
   records `selection_sha256`, `selection_manifest_sha256`, `freeze_manifest_sha256`
   and `code_sha256`, none of which reference the registry semantic hash
   `5fc4c03e…` that the loader manifest and `address_namespace.csv` share. The
   two may simply be different address spaces.
3. Add a `.qs` reader and verify NPH52.
4. Re-run the ladder only after column identity passes.
