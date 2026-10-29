# Reacquired foundation source/ETL audit — October 28, 2026

**Scope:** authorized local bytes supplied to the successor environment. Pathology-blind. No held-out/dev/sealed expression was opened.  
**Parent contract decision:** PR #491 — D1 accepted as the released-depth semantic; D2 rejected from the current contract.  
**Authority:** source audit only. No current real calibration, target, Stage4, or training authority.

## 1. Custody is stronger than the freeze's hash-only state

The previously hash-indexed August package bytes are present in this environment. Exact SHA verification gives:

- calibration ZIP: `07748d5b…`
- expression metadata ZIP: `1098fd4c…`
- checkpoint ZIP: `ab2885f9…`
- split 41K expression outer archive: parts `b8163f53…`, `5bc2ec30…`; concatenated SHA `63239898…`
- inner 50k × 41,238 NPZ: `4c50f1de…`

The August bundle manifest `da7c3daf…` verifies **97/97** members across the multi-archive packaging. This proves byte custody only; it does not make the historical calibration current.

## 2. Real 50k residual decomposition

The frozen 50k sample contains 50,000 reader-fit cells, 41,238 addresses and 246,702,069 nonzero values. Its documented normalization is:

`log1p(raw_count * 10000 / full_source_library)`

Using the per-cell physical `source_library` from the separately hashed operator metadata, every nonzero value was inverted to its nearest raw integer count. Across all 246,702,069 values, the largest distance to an integer was only `2.18e-11`; zero values exceeded `1e-6`.

The resulting pooled residual mass is:

| source | cells | physical total | mapped 41K total | residual | pooled residual |
|---|---:|---:|---:|---:|---:|
| HVS | 10,958 | 201,375,438 | 201,375,438 | 0 | 0.0000% |
| NPH52 | 5,221 | 73,441,713 | 72,345,943 | 1,095,770 | 1.4920% |
| SEA-AD | 33,821 | 930,739,228 | 893,449,394 | 37,289,834 | 4.0065% |

This independently corroborates the earlier source-dependent residual finding without claiming FULL104 closure. The sample maximum residual fractions are 2.98% for NPH52 and 7.74% for SEA-AD; they do **not** replace the larger full-corpus maxima reported in prior audits.

## 3. Frozen expression audit has an incomplete per-shard ledger

`FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json` reports the correct global 50,000 cells / 246,702,069 nnz, but its `shards` list stops at operator 34.

The final NPZ, sample freeze and operator metadata contain operators 35–41 (all NPH52): 5,221 cells and 20,448,144 nnz. For operators 0–34, row-nnz totals computed from the final NPZ exactly match the listed audit shards.

Therefore the controlling interpretation is:

`AUDIT_LEDGER_INCOMPLETE_FOR_NPH52__FINAL_PAYLOAD_AND_METADATA_CONTAIN_35_41`

Do not rewrite the historical audit file; preserve this as an append-only correction.

## 4. Metadata grouping facts

The authenticated metadata SQLite contains 6,351,753 rows / 149 donors / 42 matrices/operators:

- reader_fit: 4,553,407 cells / 104 donors / 42 operators
- reader_validation: 947,031 / 22 donors / 35 operators
- reader_oracle: 851,315 / 23 donors / 42 operators

No donor occurs in more than one reader partition or more than one source; no matrix maps to multiple operator indices or multiple sources.

For reader-fit: HVS = 41 donors / 198,718 cells / 24 matrices; NPH52 = 17 / 236,476 / 7; SEA-AD = 46 / 4,118,213 / 11.

This is useful mechanical grouping evidence, but the SQLite has **no specimen/tissue-block field and no acquisition-key field**. It therefore cannot by itself close external donor/specimen identity.

## 5. Address and QC/alias implications

The 41,238-address namespace contains **275 duplicated nonempty symbols across distinct molecular address IDs**. Rights, query identity and alias review must therefore be keyed by `molecular_address_id`, never symbol alone.

Direct prefix census finds 30 `MT-*` addresses and 130 `RPS/RPL*` addresses (126 under a narrower numeric/RPLP pattern), plus `MALAT1` and `NEAT1`. These are not automatically invalid queries, but they emphasize that D1's arithmetic noninterference does not remove depositor-QC selection conditioning.

## 6. What remains blocked

The reacquired package does **not** include the off-ledger source-feature var metadata needed to determine whether excluded source features are aliases of a query address. Therefore the per-query/per-operator off-ledger alias audit cannot be executed here.

Depositor QC rules remain unrecorded. Specimen/tissue-block and acquisition keys are absent from the metadata SQLite. The FULL104 expression store itself is not present; the 50k sample is not a substitute.

Consequences:

- D1 remains the accepted released-depth contract but is not yet a qualified real issuer.
- D2 remains rejected from this contract version.
- the 50k residual readout is source-audit evidence, not calibration or biological target evidence.
- no real training or Stage4 authority changes.

Standing stop:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
