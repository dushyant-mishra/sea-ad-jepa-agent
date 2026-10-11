# TD G6/G7 standalone V2 — G7 sequencing and narrow-read addendum

Date: 2026-10-10

Status: `DESIGN_ADDENDUM__NO_EXECUTION_AUTHORITY__NO_VALUE_READ`

This addendum supplements the standalone V2 design and the V3-preflight amendment.

## 1. Mechanical G6 -> G7 sequence gate

G7 must require a genuine `JEPA_TD_RELATIONAL_G6_RECEIPT_V2` with terminal `PASS_TD_G6_SOURCE_LIBRARY_EXACT` before any S174 count value or physical H5AD value is opened.

The G6 receipt must be bound to the same:
- V3 preflight receipt SHA;
- V3 mapping receipt SHA;
- runtime V2 authorization SHA;
- G6 V2 script SHA;
- G7 V2 script SHA;
- V2 authorization schema/token.

The receipt must keep `biological_replay_authorized=false`, `target_selection_authorized=false`, `td60_authorized=false`, and `training_authorized=false`.

This is a sequencing gate only. G7 remains scientifically independent: it does not use G6 values or G6's comparison result as its S174 reference.

## 2. Narrow S174 value-read scope

Global G1b/S174 custody checks may:
- hash every frozen counts/meta shard byte-for-byte;
- read shard `shape` metadata;
- read cell-ID/meta geometry needed to establish natural overlap.

They must not open every shard's count `data` array merely to prove global custody.

S174 count arrays may be opened only for a shard containing a genuine natural Sample-A HVS/SEA overlap that G7 will compare. Physical H5AD value arrays are likewise opened only after the corresponding physical source SHA is independently re-authenticated immediately before the reread.

The G7 receipt must record whether S174 count values and physical H5AD values were opened per matrix, including explicit false values for zero-overlap matrices.

## 3. Namespace and status semantics

A zero-overlap result remains `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` and process non-success. A mismatch remains process non-success. Only `PASS_TD_G7_S174_EXACT_OVERLAP` is process success.

Nothing in this addendum authorizes creation of a runtime authorization, G6/G7 execution, corrected biological replay, target selection, TD60, or training.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
