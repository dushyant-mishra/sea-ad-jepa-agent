# TD G7 S174 immediate reauthentication audit

Date: 2026-10-10

Status: `KNOWN_PREQUALIFICATION_DEFECT__NO_RESULT_AFFECTED__DO_NOT_QUALIFY_PR258_HEAD_C5D9`

Affected candidate head:
`c5d9c64cf42dc8c12d91672458689c0a0a67f472`

No G7 execution has occurred. No corrected expression value has been read under this candidate. No scientific result is affected.

## Finding 1 — S174 count-shard TOCTOU

The current G7 candidate performs a global S174 custody pass that hashes every `*.counts.npz` and `*.meta.npz` against the immutable G1b freeze. Later, for a matrix with natural Sample-A overlap, it opens the same `meta.npz` and `counts.npz` to obtain cell IDs and raw counts.

The later value-use path does not re-hash those files immediately before opening them.

Therefore a same-path replacement after the global hash pass but before the overlap value read could evade the intended immediate-use custody boundary.

This is the same class of time-of-check/time-of-use problem already fixed prospectively for physical H5AD reads.

## Required repair for immediate-use custody

A successor G7 must:

1. retain the global all-shard hash/custody pass;
2. for every shard with natural Sample-A overlap, re-hash `meta.npz` immediately before reading `cell_id`;
3. require that immediate meta hash to equal the immutable G1b freeze hash;
4. after overlap is established and immediately before opening count values, re-hash `counts.npz` again;
5. require that immediate counts hash to equal the immutable G1b freeze hash;
6. record the immediate-use hashes in the G7 receipt per evaluated matrix;
7. fail before any S174 value access on mismatch.

The immediate recheck is required even if the same shard passed the earlier global custody pass.

## Finding 2 — duplicate S174 cell IDs can collapse silently

Current code constructs:

`where_s174 = {cell: index for index, cell in enumerate(s174_cells)}`

If `cell_id` contains a duplicate within one S174 shard, dictionary construction silently keeps the final row.

A successor G7 must require:
- exact row count agreement between count and meta files;
- `cell_id` present;
- every `cell_id` finite/string-resolvable as historically expected;
- `cell_id` unique within each shard before any dictionary/index map is constructed.

Duplicate `cell_id` is a custody/identity failure and cannot be resolved by choosing first/last occurrence.

## Finding 3 — duplicate CSR addresses inside one S174 row can overwrite silently

Current `sparse_row_dict()` assigns one dictionary entry per sparse address. If an S174 CSR row contained the same address index more than once, later entries would overwrite earlier entries in the dictionary.

The immutable G1b bytes are trusted historical custody, but G7 is intended to be an independent exact corroboration gate. It should therefore fail closed on ambiguous CSR row representation rather than relying on implicit dictionary behavior.

For every S174 count shard whose values are actually opened for natural overlap, the successor must require:
- valid CSR indptr geometry;
- address indices in `[0, 41238)`;
- no duplicate address indices within any row used by the overlap comparison.

Sorted index order is not itself a biological requirement, so the gate need not reject merely unsorted-but-unique rows. It must reject duplicates instead of summing, choosing first, or choosing last.

## Required regression tests

Before successor qualification, focused tests must prove:

1. same-size changed S174 `meta.npz` after global custody but before overlap metadata read is rejected;
2. same-size changed S174 `counts.npz` after global custody but before count-array read is rejected;
3. duplicate S174 `cell_id` values fail closed;
4. duplicate address indices within an overlap S174 CSR row fail closed;
5. a no-overlap shard never opens its count-value arrays;
6. an overlap shard records both immediate meta and immediate counts hashes;
7. physical H5AD immediate SHA recheck remains intact;
8. G7 mismatch and NOT_ESTIMABLE remain non-success exits.

## Disposition

PR #258 remains useful audit history and contains the standalone V2 architecture, but exact head `c5d9c64cf42dc8c12d91672458689c0a0a67f472` is superseded before qualification.

Do not ask the canonical machine to qualify or execute that head.

A successor must be created from it (or an equivalent reconciled base), implement only the fail-closed custody fixes above plus tests, and remain `DO_NOT_EXECUTE_G6_G7` until separately qualified against the exact PR #259 receipt bytes.

No value authorization is created by this audit.

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
