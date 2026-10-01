# Claude instructions — V64 Phase-B substrate B6 availability-schema repair

**Date:** 2026-09-30

Continue from:

`claude/v64-exact-sampler-successor-20260930`

Audited head:

`154935c5ff1fe1c8f9cc09ab8ddb208256930c7f`

Do NOT execute Stage 4.

## Accepted at this checkpoint

The following are accepted:

- Phase-A V3 retained population: 13,175.
- Phase-B shard build: completed over 282 donors / 3,231 metacells.
- Pairing permutation:
  - content hash bound;
  - file hash bound;
  - bijection/range verified;
  - inverse round trips verified;
  - independently re-derived from RNA/ATAC obs names.
- B1 T5 materialization: closed.
- B2 32,153 interval reconciliation: closed.
- B3 shard-byte custody rehash: closed.
- B4 donor-pair availability-state logic: accepted in substance.
- B5 T6→T7 referential integrity: closed.
- Modality firewall: held.
- Stage 4 correspondence remains unopened.

## Remaining blocker B6 — frozen T3/T4 availability columns are not materialized

The frozen measurement substrate contract requires:

### T3_RNA_VECTORS
fields:
- `rna_log1p_cp10k`
- `rna_available`

### T4_ATAC_VECTORS
fields:
- `atac_log1p_norm`
- `atac_available`
- `n_assigned_peaks`

and explicitly states:

> per-element availability columns in T3 and T4, and an availability_state in T5

The executed shards persist sparse T3/T4 values but no per-element availability representation.

The closeout instead added `rna_available` / `atac_available` to T5. That is not the same contracted schema.

## Important semantic distinction

A sparse missing entry in T3/T4 can be a **measured zero**.

Therefore:

`sparse absence != unavailable`

Do not derive availability by treating missing sparse entries as false.

The existing T5 state logic may remain:
- zero coverage across all donor metacells => donor-pair missing;
- zero variance => donor-pair missing;
- otherwise measured.

But T5 does not substitute for the T3/T4 per-element availability representation.

## Required repair

Do NOT:
- reread the RNA matrix;
- reread the ATAC matrix;
- rebuild Phase A;
- rerun the sampler;
- recompute metacells;
- alter T3/T4 biological values;
- alter pair/donor populations.

Use only the frozen substrate and its already-persisted depth/metadata.

### Materialize or exactly factorize T3 availability

For the conceptual T3 universe:

`donor x metacell x gene`

persist availability with the semantics:

- a zero-valued RNA measurement is still `available=true`;
- only genuinely unavailable measurement is false.

If every frozen gene is assayed whenever that metacell has lawful RNA depth, a factorized representation is acceptable only if it is explicitly proven equivalent to the per-element column required by the contract.

### Materialize or exactly factorize T4 availability

For:

`donor x metacell x distal_interval`

persist availability with the same principle:

- an interval with assigned peaks but zero observed counts is measured zero, `available=true`;
- unavailable measurement must remain distinct;
- `n_assigned_peaks` stays bound.

Again, factorization is acceptable only if it is an exact lossless representation of the frozen per-element availability column.

## Required validation

Add adversarial tests that prove:

1. measured zero remains available;
2. unavailable element is not encoded as zero;
3. T5 `availability_state` is exactly consistent with the reconstructed T3/T4 availability plus zero-coverage/zero-variance rules;
4. factorized availability, if used, expands exactly to the conceptual per-element columns;
5. no RNA×ATAC quantity is computed.

Bind hashes for the repaired availability artifact(s) and updated closeout receipt.

## One documentation correction

The commit message for `154935c5` mentions an aggregate binding beginning `2d7ae4...`, but the committed aggregate/closeout receipts agree on:

`2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52`

Treat the receipt value as authority and correct the prose in the next closeout note.

## Governance

Stage 4 = NOT AUTHORIZED.  
TRAINING = OFF.  
TD60 = BLOCKED.  
Morabito = PROTECTED.  
Correspondence remains unopened.

After B6 is closed, STOP again for audit.
