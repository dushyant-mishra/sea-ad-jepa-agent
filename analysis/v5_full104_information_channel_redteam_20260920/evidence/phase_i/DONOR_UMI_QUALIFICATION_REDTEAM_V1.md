# Red-team of the `donor_umi` independent qualification

Date: 2026-09-22
Branch: `gpu/v5-full104-n1-physical-burden-preflight-20260922-claude`
Parent: `601cccf4fff98a471fa0cf2595374efa9ef9be59` (PR #58 head)

All controls used disposable copies. The authenticated Level-4 store, the heavy
NPZ and the pass1 artifact were never written to.

## Exercised against physical mutation — all fail closed

| control | rejection |
|---|---|
| altered manifest byte | `FULL104 block manifest hash mismatch` |
| wrong heavy artifact | `heavy artifact sha mismatch: b7463358…` |
| changed strict-core address order | `pass1 core differs from artifact core` |
| changed donor identity/order | `pass1 duniq differs from artifact duniq` |
| truncated `cell_donor` (missing cell) | `pass1 cell_donor length mismatch` |

## Guard present in code, NOT exercised against physical mutation

I am listing these separately rather than counting them as passes. Exercising
them needs a disposable copy of the Level-4 **count** store, which is >30 GB;
copying it to mutate one byte is not a reasonable use of the machine, and
mutating the authenticated original is not permissible. So the guard is stated,
its line is cited, and the fact that it was not physically exercised is recorded.

| control | guard in `qualify_donor_umi_independent_v1_20260922.py` |
|---|---|
| duplicate block key | `len({r["block_key"] for r in rows}) != EXPECTED_BLOCKS` |
| missing block | manifest row count check + `sha256_file(counts_path)` open |
| altered count-block byte | `sha256_file(counts_path) != row["counts_sha256"]` |
| altered metadata byte | `sha256_file(meta_path) != row["meta_sha256"]` |
| one duplicated cell | `if np.any(seen[sel])` → `selection_row consumed twice` |
| negative raw count | `if np.any(data < 0)` |
| floating / non-integer raw count | `np.all(np.equal(np.mod(data, 1), 0))` |
| donor identity per row | `np.array_equal(dcodes, cell_donor[sel])` |
| block geometry | `matrix.shape != (len(recs), N_LEDGER)` |
| exactly-once accounting | `cells_consumed != EXPECTED_CELLS or not seen.all()` |
| partial output as complete | the receipt is written only **after** the exactly-once check passes |

`changed split receipt` and `changed source vector` are not inputs to this
script — it authenticates `donor_nnz`/`donor_umi` against raw blocks and does not
consume the split. They belong to the N1 runtime's binding surface (see B2 in the
design note), not here.

`resumed run consuming a block twice` does not apply: this qualifier is a single
uninterrupted pass with no resume path. If a resumable variant is ever written,
that control becomes live and must be exercised.

## A bug I introduced and fixed

The first run crashed:

```
IndexError: index 40567 is out of bounds for axis 0 with size 40476
```

I had sized the strict-core lookup by `core.max() + 1` (40,476). The strict core
is a subset of the **41,238-column ledger**, so a block's column indices routinely
exceed `core.max()` and must map to `-1` rather than index out of bounds. Fixed by
sizing the lookup to `N_LEDGER`, and a block-geometry assertion
`matrix.shape != (len(recs), N_LEDGER)` was added so a block of the wrong width
fails closed instead of silently mis-indexing.

Worth stating plainly: this was a crash, not a silent wrong answer — the array
bound caught it. Had I sized the lookup *larger* than the ledger instead of
smaller, the same mistake would have produced quietly wrong sums.

```
N1 TARGET SELECTED = NONE
MASKS GENERATED    = NONE
BURDEN CALCULATED  = NO
OUTCOME OPENED     = NONE
TRAINING           = OFF
```
