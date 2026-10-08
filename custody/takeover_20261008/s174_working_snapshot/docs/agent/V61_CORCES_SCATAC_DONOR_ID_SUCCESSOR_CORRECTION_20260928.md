# V61 successor correction — Corces scATAC donor identity

**Date:** 2026-09-28  
**Status:** structural/provenance correction only. No molecular regulatory outcome opened.  
**TRAINING=OFF. TD60=BLOCKED.**

This successor corrects the V60 statement that the Corces scATAC atlas contains six donors.

## Source inspected

User-supplied public Corces et al. Supplementary Data Set 2:

`41588_2020_721_MOESM5_ESM.xlsx`

Sheet: `scATAC-seq QC Metadata`.

The workbook's own column dictionary states:

> `Donor_ID - A numeric identifier unique to each individual donor.`

The full `Donor_ID` field therefore has to be treated as the individual-donor key. Collapsing it to only the first numeric token is invalid.

## Correct donor count

Across the 70,631 scATAC cells there are **8 unique documented individual donor IDs**:

- 03_39
- 04_38
- 06_0615
- 09_1589
- 09_35
- 11_0393
- 14_0586
- 14_1018

The earlier six-token count arose by collapsing `09_1589` with `09_35`, and `14_1018` with `14_0586`. The workbook explicitly defines those full values as unique individual donors, so that collapse merged distinct individuals.

## Cluster 24

Cluster 24 contains **4,655 microglial cells** and includes cells from **all 8 documented individual donors**.

This supersedes the historical V60 wording:

- "6 donor tokens"
- "all six donors"
- any inference that the scATAC layer has ~6 independent donors.

The correct public-metadata statement is:

> Corces scATAC contains 70,631 cells from 8 documented individual donors; Cluster 24 contains 4,655 microglia represented in all 8 donors.

## Consequence for V61 Object E

This correction strengthens the public scATAC provenance description but does **not** prove that the HiChIP filename donor key is the same biological-person key across assays.

The V61 HiChIP parser uses the two-token `A_B` structure and is therefore structurally consistent with the documented scATAC `Donor_ID` convention. Cross-assay identity remains appropriately labelled `LIKELY_SAME_KEY__UNPROVEN` until a direct metadata bridge is found.

The unresolved University of Washington / SEA-AD person-level overlap is unchanged.

## Governance

This is a versioned successor correction. Historical V60 evidence is preserved rather than silently rewritten.

- no target/program-gene overlap inspected
- no Morabito outcome opened
- no training authorization changed
- `TRAINING=OFF`
- `TD60=BLOCKED`
