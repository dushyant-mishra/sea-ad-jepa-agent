All five blockers closed. **Branch @ `154935c5`. Stopping for audit — Stage 4 sealed.**

Phase A, the sampler and the substrate build were all left alone; the executed v1 shard bytes and receipts were read only.

## B3 — the custody gap, which had teeth

The validator took each shard's SHA-256 from the receipt that shard wrote itself. A shard altered afterwards would have been read structurally while the binding pointed at old bytes. Every `.npz` is now re-hashed from disk and required to equal its receipt before anything proceeds — all 8 match, and the aggregate binding is recomputed over the **recomputed** hashes (`2a540484…`, which matches the earlier value, confirming nothing drifted).

## B2 — the 21 was a red herring, as you suspected

```
32,117 Phase-A row intervals + 57 enumeration keys
  − 18  enum intervals coinciding with an existing Phase-A interval
  −  3  duplicate hg38 coords within the enum set (two edges admitting the same hg19 start)
= 32,153

```

Two distinct causes, and only **11 of the 20** edges involved are R3 edges. The match to 21 is coincidence.

## B1 — T5 materialised

**10,552,158 rows** = 282 donors × 37,419 pairs, 101.7 MB, derived from T1–T4 only with no matrix re-read. Carries both activity fields, both depth sensitivities, `n_metacells_contributing`, `n_assigned_peaks`, availability state and flags. Factorised internally (activity depends only on donor×gene, accessibility on donor×interval) but **stored keyed donor × pair_key** as the contract requires.

## B4 — availability, and the distinction that matters

| state                           | count     |
| ------------------------------- | --------- |
| MEASURED                        | 8,598,011 |
| NOT_MEASURED_RNA_ZERO_COVERAGE  | 1,471,461 |
| NOT_MEASURED_ATAC_ZERO_COVERAGE | 482,686   |
| NOT_MEASURED_\*_ZERO_VARIANCE | 0         |

**A sparse absence is a MEASURED ZERO, not a missing value** — the gene was assayed and had zero counts; log1p(0) is exactly 0.

I didn't report those two zeros bare. On a real donor, 2,776 genes have nonzero coverage and none has zero variance; on a synthetic constant column the same predicate fires. **The branch is live — the data just doesn't exercise it.**

Phase B deliberately does *not* split MEASURED_AND_SUPPORTS from MEASURED_AND_DOES_NOT_SUPPORT — that needs the correspondence, which is Stage 4. 36,794 of 37,419 pairs reach the 30-donor minimum; the 625 below are **labelled, not dropped**.

## B5 — T6→T7 integrity

All 17 R3 enumeration rows resolve, every record's edge matches its row's edge, no non-R3 row carries a reference. **11 T7 records are unreferenced, which is lawful** — an R3 pair whose small-arm alternatives were all already selected as CONTROL_A or CONTROL_B needs no enumeration row.

Modality firewall held: both depth-sensitivity terms are single-modality slopes on that modality's own depth.

I audited 154935c5ff1fe1c8f9cc09ab8ddb208256930c7f. Most of the Phase-B substrate closeout is now solid. What I accept: - B1 T5 materialized: 10,552,158 donor×pair rows = 282 × 37,419. - B2 interval reconciliation: 32,117 + 57 − 18 − 3 = 32,153. - B3 custody: all 8 shard NPZ files were re-hashed from disk and matched their receipts. - B4 donor-pair availability logic: measured zero is correctly distinguished from donor-pair zero coverage / zero variance. - B5 T6→T7 integrity: the R3 references resolve correctly. - Pairing hardening is excellent: content SHA, .npy file SHA, range, uniqueness, inverse round-trip, independent re-derivation from RNA/ATAC obs names, all pass. - The modality firewall held. No RNA×ATAC correspondence was opened. The authoritative aggregate binding is: 2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52. There is a minor prose typo in the commit message mentioning 2d7ae4...; the committed aggregate and closeout receipts both agree on 2a540484..., so the receipt value should be treated as authority. However, I found one new contract-compliance blocker: B6. The frozen substrate contract explicitly requires T3 RNA vectors to contain rna_available, T4 ATAC vectors to contain atac_available, and says availability should be represented as per-element availability columns in T3 and T4, with the donor-pair availability_state in T5. The executed shard producer does not materialize T3/T4 availability arrays. The closeout instead added rna_available and atac_available to T5. That does not satisfy the frozen artifact schema. This matters because sparse absence is not the same as unavailable. A missing sparse entry may mean a perfectly valid measured zero. So Stage 4 must not infer availability from sparsity after outcomes exist. The repair is narrow and does not require rerunning the biological substrate: no RNA reread; no ATAC reread; no Phase-A rerun; no metacell rebuild; no value changes. Claude should materialize—or losslessly factorize—the already-implied T3/T4 availability information from the frozen substrate and depth metadata, and prove: 1. measured zero → available=true; 2. genuinely unavailable → false, not encoded as zero; 3. T5 availability states reconcile exactly with T3/T4 availability plus the frozen zero-coverage/variance rules; 4. any factorized representation expands exactly to the contracted conceptual per-element availability columns. So my current status is: Phase A V3 accepted, 13,175; Phase B execution completed; B1–B5 closed; pairing/custody closed; B6 open/blocking; Stage 4 still sealed; Training off; Morabito protected.

B6 is correct, and the distinction is the important one: Stage 4 must not infer availability from sparsity. The local exploration reported:

- metacells: 3,231
- total RNA == 0: 0; minimum total RNA 629
- total ATAC == 0: 0; minimum total ATAC 255
- intervals: 32,153
- intervals with 0 assigned peaks: 0; minimum assigned peaks 1

The proposed factorisation was:

`rna_available[m,g] = total_rna[m] > 0`

`atac_available[m,i] = (total_atac[m] > 0) AND (n_assigned_peaks[i] > 0)`

Conceptual per-element sizes:

- T3: 3,231 × 4,372 = 14,125,932
- T4: 3,231 × 32,153 = 103,886,343

The local B6 script `close_phase_b_b6_availability_v1.py` then proposed bit-packed full columns plus the factorisation, a synthetic unavailable witness, a T5 reconciliation narrative, and factorisation round-trip. The local run reported:

- T3 elements 14,125,932, all_available=True, packed ~1.8 MB
- T4 elements 103,886,343, all_available=True, packed ~13.0 MB
- T3 sparse absences on available elements 7,501,643; unavailable 0
- synthetic unavailable fixture PASS
- claimed T5 derivation PASS
- factorisation expansion PASS
- local receipt SHA-256 `1ecc6b60d39c2b5b25b08c5193ac68c49ccce79e1558f80ac8a05ffc48f7cee3`

This local PASS was subsequently audited and NOT accepted as final because the T5 proof set `holds=True` rather than independently reconstructing all T5 states; the sparse-zero proof covered T3 but not T4; global metacell indexing/axis identity were not proven; and the new B6 artifact lacked full input/output custody binding. See the current GitHub B6 precommit audit for the authoritative acceptance target.
