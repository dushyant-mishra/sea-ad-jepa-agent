# V62 — Corces Supplementary Data Set 2 donor-identity successor correction

**Date:** 2026-09-28  
**Status:** structural/provenance correction only; no molecular regulatory outcome opened.  
**Governance:** `TRAINING=OFF`; `TD60=BLOCKED`.

## Correction

The earlier V60 authentication collapsed `Donor_ID` values at the underscore and therefore reported six donor tokens. That collapse is not compatible with Supplementary Data Set 2's own data dictionary.

The workbook states verbatim:

> `Donor_ID - A numeric identifier unique to each individual donor.`

The full values in the QC sheet are therefore the individual-donor keys. Across the 70,631 scATAC cells there are **8 unique documented individual donors**:

- `03_39`
- `04_38`
- `06_0615`
- `09_1589`
- `09_35`
- `11_0393`
- `14_0586`
- `14_1018`

All eight contribute Cluster-24 microglia. Cluster-24 totals **4,655 cells**, distributed as:

| Donor_ID | Cluster-24 cells |
|---|---:|
| 03_39 | 651 |
| 04_38 | 380 |
| 06_0615 | 779 |
| 09_1589 | 1,050 |
| 09_35 | 225 |
| 11_0393 | 415 |
| 14_0586 | 879 |
| 14_1018 | 276 |

The total is 4,655 and all 8/8 documented donors are represented.

## Why the previous six-donor count was wrong

Truncating the key to its leading field merges `09_1589` with `09_35` and `14_0586` with `14_1018`. The workbook explicitly defines the **full** field as unique to each individual donor, so those merges are invalid.

This successor does not rewrite V60 history. It supersedes only the donor-count interpretation in `V60_CORCES_DS2_DS9_AUTHENTICATION_V1.json` and documents why.

## Consequence

- Corces scATAC substrate donor count: **8 documented individual donors**, not ~6.
- Cluster-24 microglia: **4,655 cells across all 8 donors**.
- This strengthens the accessibility-side provenance but does not prove donor robustness for the final regulatory object.
- It does not resolve the University of Washington / SEA-AD person-level overlap.
- It does not change the n=18 specificity benchmark status.

## Custody

User-supplied public workbook: `41588_2020_721_MOESM5_ESM.xlsx`  
SHA-256: `2d1aa847e0f075728e73b91e9d793450e278166edbb2f2a082e264f873c94707`

No controlled data were used. No target/program-gene overlap was computed.
