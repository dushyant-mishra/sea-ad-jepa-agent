# JEPA TD34/TD41 expression-axis custody checkpoint — 2026-10-07

Status: documentation-only audit checkpoint. No training, Stage-A execution, Stage 4, TEST, Morabito, target selection, representation selection, or production-estimand authority is granted.

## Why this checkpoint exists

Historical JEPA work contains proven row/value-binding failures and later feature/source-row authority repairs. Therefore recovery of old target-discovery scripts is not sufficient by itself: panel identity, row identity, and expression-column identity must each be proven separately before old RNA-derived biological results are reused.

## Newly recovered primary artifacts

### Original TD34 producer
Recovered from the uploaded light handoff package:

- `script/td_iteration34_state_geometry_globalrow.py`
- SHA-256: `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

This matches the historical frozen TD34 script digest.

TD34 uses the corrected global-row lineage and constructs four deterministic 512-address panels from the common-scalar molecular-address support space. Panel selection is based on support/address identity rather than RNA correlation or pathology outcome.

### Exact historical 50K x 41,238 expression archive
The two previously uploaded archive parts were verified against `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv` and reassembled.

Full archive:

- expected/verified bytes: `607959761`
- SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- matrix geometry: `50,000 x 41,238`
- storage: CSR sparse matrix

The archive contains the historical expression matrix but no embedded gene names, molecular-address list, or feature-axis sidecar.

## Important self-correction

Recovery of the original TD34 producer plus the exact expression archive does **not** yet prove that expression column `j` corresponds to Molecular Ledger address `j`.

The TD34 producer assumes this positional equivalence when sparse-matrix column indices are interpreted as molecular-address indices. The recovered expression archive itself does not carry an independent column->address binding that can prove that assumption.

Accordingly, the current status is:

`TD34_PANEL_SELECTION_GENEALOGY_RECOVERED__EXPRESSION_COLUMN_TO_ADDRESS_BINDING_NOT_YET_REQUALIFIED`

and downstream TD41/TD43 RNA-derived biological scores remain:

`SCIENTIFICALLY_INTERESTING__PANEL_SELECTION_CLEARED__EXPRESSION_ADDRESS_BINDING_REQUIRES_HISTORICAL_AUDIT`

This narrows, rather than removes, the historical blocker.

## Why the caution is necessary

The repository history already contains documented coordinate/value-binding failures:

1. Historical target discovery had a B-side row-addressing error where reset/local row indices could be confused with the frozen global row. TD23/TD33 later demonstrated that this could create a large false biological relationship and made `RESET_INDEX_FORBIDDEN` binding.
2. Later execution-authority audits found that metadata/payload authentication alone did not prove that values came from the intended physical source row. Repairs required explicit source-row equality, source cell/donor identity binding, block-local row verification, and physical payload coupling.

Therefore rerunning an old script against an old matrix can reproduce an old number without proving that the biological gene identity attached to each value was correct.

## What appears safe now

Panel *selection* itself is currently separable from the expression-axis concern because it is derived from the authenticated support/address state and deterministic address hashing, not from the RNA values used to score the panels.

The vulnerable step is the subsequent lookup of RNA values by matrix column index.

## Next required local artifact

Highest priority is any original artifact that proves the 41,238-column feature axis used when `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz` was created. Useful candidates include:

- feature-axis / molecular-address manifest;
- `features.*`, `molecular_address*`, `address_manifest*`, `gene_index*`, `gene_to_address*`, `address_to_gene*`, `vocabulary*`;
- `FOUNDATION_MOLECULAR_LEDGER*` artifact that is explicitly bound to the matrix producer;
- the producer/materializer script that created the 41,238-column discovery expression matrix from source matrices;
- any receipt hashing both the matrix payload and its ordered feature-axis bytes.

The decisive audit question is:

> For every historical discovery matrix column `j`, can we prove that the value came from the same molecular-address identity recorded at address `j` in the 41,238-address authority?

Until that is proven, do not use TD34/TD41/TD43 RNA-derived numerical outcomes as target or representation authority.
