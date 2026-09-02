# FULL104 capacity audit adjudication

Date: 2026-08-26

Status: **STOP_PROVENANCE_SCOPE_MISMATCH**

The raw reference audit completed without opening expression, but it audited the wrong population scope and must not be used for adaptive calibration.

## Mismatch

- Raw audit result: 104 donors, 42 operators, **3,292** unique cells.
- Authoritative fit-104 metadata inventory: 104 donors, 42 operators, **4,553,407** lawful cells.
- Difference: **4,550,115** cells.
- The raw audit covered only `0.0007229751` of the lawful inventory (about 0.0723%).

The resolved `production_train_loader.py` is authoritative for the historical T1 accepted cache, not for enumeration of the full lawful production corpus. Its 3,292-cell result is the known distorted T1 cache that the controlling contract explicitly forbids using to derive full-dataset quantities.

## Authority proving the mismatch

- `exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_DONOR_X_OPERATOR.csv`
  - SHA-256: `2ac07c2ba5f0fdde7c4845785f8f18fbaf633ff1f76c9fffbfcd0cb6ce47e037`
  - 1,400 donor × matrix rows; 104 donors; 42 matrices; 4,553,407 cells.
- `exports/prod41k_teacher_t1_20260823/T1_INVENTORY_EXPANSION_FEASIBILITY.json`
  - SHA-256: `8000954a0db16ae1bf5f7535dfd1c01ac054136f6ac0c09efd1708f7d46da1d3`
  - Independently records 4,553,407 lawful fit cells and 3,292 cached fit cells, metadata-only.

## Firewall and execution state

- Expression read: no.
- Reader-validation expression read: no.
- Reader-oracle expression read: no.
- DEV/SEALED expression read: no.
- Pathology read: no.
- Dataset-dependent values promoted: none.
- CUDA/calibration/training started: no.

The raw files in this directory are retained as evidence of the rejected scope and are marked **DO NOT USE FOR CALIBRATION**.

## Required repair before resumption

The capacity adapter must enumerate the full lawful production shard metadata for the exact 104 reader-fit donors, reconcile to the 4,553,407-cell donor × operator authority, and fail closed if donor, operator, source, or observation-state lineage differs. No expression should be opened during that repair.
