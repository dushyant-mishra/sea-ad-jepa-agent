# TD G7 S174 immediate-use custody successor requirements

Date: 2026-10-10

Status: `REPAIR_SPEC_ONLY__DO_NOT_EXECUTE_G6_G7__NO_VALUE_AUTHORITY`

Base code:
`c5d9c64cf42dc8c12d91672458689c0a0a67f472`

Upstream value-blind evidence:
- PR #259 execution record head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- driver receipt SHA `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping receipt SHA `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`

This successor exists only to close the remaining G7 custody defects found before qualification.

## Required code changes

1. Preserve the existing global G1b S174 shard hash pass.
2. For each shard with natural Sample-A overlap:
   - re-hash `meta.npz` immediately before reading `cell_id`;
   - require exact immutable G1b hash;
   - reject duplicate `cell_id` before building the row lookup.
3. After natural overlap is known and immediately before opening S174 count values:
   - re-hash `counts.npz` again;
   - require exact immutable G1b hash.
4. For every S174 CSR row used in comparison:
   - require valid CSR geometry;
   - reject duplicate address indices within that row;
   - do not sum, first-win, or last-win ambiguous duplicate entries.
5. Record immediate-use S174 meta/count hashes per evaluated matrix in the G7 receipt.
6. Preserve physical H5AD immediate SHA verification before physical count reads.
7. Preserve strict finite/nonnegative/exact-integer raw-count semantics.
8. Preserve same-authority G6 PASS requirement.
9. Preserve `NOT_ESTIMABLE` and mismatch as process non-success.
10. Do not alter G6 scientific behavior, G7 comparison tolerance, replay address set, Sample-A geometry, or G1b authority.

## Required tests

Add focused tests proving:
- changed S174 meta bytes after global custody but before metadata use fail;
- changed S174 counts bytes after global custody but before count use fail;
- duplicate S174 cell IDs fail;
- duplicate address indices in a compared S174 row fail;
- no-overlap shards never open S174 count values;
- immediate-use hashes are recorded for overlap matrices;
- physical H5AD immediate SHA recheck remains intact;
- G7 PASS alone returns process 0; mismatch and NOT_ESTIMABLE do not.

## Qualification after repair

After code/tests are committed, canonical qualification must:
1. pin exact successor head in a clean worktree;
2. run focused common/G6/G7 tests;
3. feed the exact PR #259 physical receipt bytes to `load_bound_preflight()` using the audited SHA values above;
4. create no runtime authorization object;
5. run neither G6 nor G7;
6. read no expression/count values;
7. preserve qualification logs and STOP for owner review.

## Authority boundary

This branch does not authorize value reads or corrected biological replay.

Future biological replay is already prefrozen on PR #251 but remains unauthorized.

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
