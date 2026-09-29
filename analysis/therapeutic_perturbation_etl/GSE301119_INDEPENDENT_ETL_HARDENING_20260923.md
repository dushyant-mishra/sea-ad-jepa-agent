# Independent GSE301119 ETL hardening review — 2026-09-23

Status: `TARGET_ENGAGEMENT_RECEIPTS_SUPPORTED__TRANSCRIPTOME_BENCHMARK_SUBSTRATE_NEEDS_COUNT_PARITY_RERUN`

Reviewed producer: PR #77 @ `8c568947629b5df93305d0360bccdcb22bdd69b8`.

## What independently checks out

- The historical Stage81A1C-P object audit was **not** the same attribute-only reader. Commit `acc4e1f642769c1e564ba579b0735486d0d918b8` required R 4.4.3 + SeuratObject 5.4.0 and recorded the two object dimensions, metadata fields, guide counts, target counts, donors, CRISPR modes and non-targeting controls without materializing expression.
- The new committed feature lists are internally clean: CRISPRa has 19,162 unique IDs, CRISPRi 36,601 unique IDs, zero duplicate IDs in either list; CRISPRa is an exact subset and CRISPRi has 17,439 additional measured features.
- The committed guide×donor metadata has 2,098 CRISPRa and 2,137 CRISPRi rows, 1,090 / 1,114 unique guide identities, exactly D1/D2, exactly NT/Perturbed, and no observed guide identity maps to conflicting target/role annotations across the committed rows.
- The physical acquisition atlas reports all 16 historical assets present with matching size/SHA. This review does not independently reopen those 4.2 GB source bytes.

## Finding P1 — count-value reader parity remains unproved

PR #77 correctly discovered that the local Seurat 4 runtime silently mishandles Assay5 and therefore used direct serialized attributes. Structural counts match the independent SeuratObject-5 audit, but that earlier audit explicitly did **not** materialize the expression matrix. Therefore the exact `counts` sparse payload consumed by the new attribute-only reader has not yet been independently compared **by value and ordering** with SeuratObject 5's public `LayerData(..., layer="counts")` accessor.

This successor adds `crosscheck_seurat5_counts_v1.R`, which must be run in a SeuratObject >=5 environment on both authenticated GSE301119 objects. It fails unless dimensions, feature names, cell names, CSC `i/p/x` slots, row sums and column sums are exactly identical.

**Until that physical parity run passes, retain PR #77 target engagement as strong producer-side measured evidence, but do not promote the full count-derived substrate as independently qualified benchmark authority.**

## Finding P2 — preserve raw guide×donor counts

PR #77 persisted the guide×donor `log2(CPM+1)` matrix but not the raw guide×donor pseudobulk count matrix. For later differential-response modeling, alternative normalization, count-aware uncertainty and reproducible benchmark construction, normalization must not be the only retained molecular substrate.

The extraction script now writes a separate `*_guide_donor_raw_counts.rds` containing exact features, guide×donor metadata, raw pseudobulk counts and library sizes, while retaining the existing logCPM derivative. The new raw artifact is heavyweight and **has not been physically generated or hashed by this review environment**.

## Finding P3 — first-row metadata lookup is now guarded

The producer assigned guide target/CRISPR role by taking the first matching cell for each guide identity. The committed metadata happens to be consistent, but the code previously did not prove that before using the first row. The successor now fails if a guide identity maps to more than one target gene or CRISPR role, and the committed-receipt tests independently assert the same property.

## Claim correction

The existing PR #77 report says a "full transcriptome-wide effect matrix" exists on disk. The persisted object is more precisely a **guide×donor normalized-expression substrate**. Transcriptome-wide control-relative intervention effects have not yet been estimated/frozen. Target-gene engagement effects are the currently derived intervention effects.

## Next physical rerun on the perturbation machine

1. Use the exact authenticated PR #77 source RDS files.
2. Run the new SeuratObject-5 count parity checker for CRISPRa and CRISPRi and commit lightweight parity receipts + SHA manifest.
3. Rerun the hardened extraction to generate raw pseudobulk + logCPM derivatives.
4. SHA-256 and size-bind both heavy raw-count and logCPM artifacts; commit only their lightweight manifest/receipts.
5. Rerun the Python receipt tests with zero skips.
6. Only then freeze the GSE301119 transcriptome-wide benchmark substrate. No JEPA training or therapeutic ranking is implied.

`JEPA_TRAINING=OFF | THERAPEUTIC_RANKING=OFF | PROTECTED_FULL104_OUTCOMES=UNOPENED`
