# Unified Task 2 execution ledger — 2026-10-15

## Authority and launch base

Task 0 frozen: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.

Unified Task 1 independently accepted and frozen at exact head:
`799d2e235901dfad9ce3b305c767a1c989e362f6`.

Macha acceptance branch head:
`5949f1c4116241f297690ad2ed248fe68b1614c2`.

Task 2 starts prospectively from the accepted Task 1 head. No later Task 1 mutation may silently become the Task 2 base.

Global authority remains exactly:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## Scope

Unified Task 2 implements `TD_EXECUTION_MANIFEST_V1` plus the current-TD population/data-access law. It does not select a target, inspect protected biological values, create representation authority, or authorize training.

Historical production-synthetic Task 2 remains `ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE` at `ff597faf2182522a320ec5322f8db9b67c9c6094`; it is reuse substrate only and does not complete this task.

## Accepted Task 1 carry-forward

- receipt verification must be memoized before Task 3 registry chains;
- Task 2 must verify raw-file SHA-256 against actual bytes;
- Task 3 must block active use of revoked records;
- the authority scope→stage table is now a documented lane invariant and must be preserved;
- NumPy is an explicit dependency of canonical identity because the accepted NumPy-scalar policy is part of Task 1 identity semantics.

## Population custody reused without recomputation

- population/support lineage: PR #349 head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`;
- canonical population registry SHA-256: `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`;
- split SHA-256: `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`;
- 104 `reader_fit`, 22 `reader_validation`, 23 `reader_oracle` donors.

These identities authorize custody only. Protected values remain unopened.

## Prospectively frozen cross-fit law

Before any outcome-bearing Task 2 execution, the lane freezes:

- `fold_count = 5`;
- folds are donor-grouped and exist only inside `reader_fit`;
- every fit donor appears in exactly one held-out fold;
- no donor appears on train and held-out sides of the same fold;
- assignment is deterministic from frozen donor identity plus non-outcome source metadata;
- assignment must not inspect candidate outcomes, `reader_validation`, or `reader_oracle`;
- the implementation must balance donor counts across folds and, where feasible without outcome information, source representation;
- tie-breaking is deterministic from canonical donor identity;
- any change to fold count or assignment law after this freeze creates a new manifest identity and requires requalification.

Rationale: 104 fit donors gives approximately 20–21 held-out donors/fold, avoiding very small held-out folds while keeping repeated calibration tractable. This is a prospective design choice, not a result-driven optimization.

## Access law

`reader_fit`: only current-TD outcome-bearing surface; held-out evaluation occurs through the frozen cross-fit law.

`reader_validation`: partition identity may be bound; biological values/candidate summaries/rescue statistics are forbidden upstream.

`reader_oracle`: partition identity may be bound; biological values/summaries/calibration statistics remain forbidden until later explicit authority.

Every producer must emit actual observed-access receipts. Declared intent cannot override observed access. Forbidden observed access invalidates authority even when numerical output equals a lawful output.

## Identity law

Task 2 must reuse accepted Task 1 `canonical_sha256`/receipt primitives. No second semantic serializer or authority taxonomy is allowed.

All manifest SHA strings remain claims until the underlying object is resolved and re-hashed. Raw-file identities require exact bytes and direct SHA-256 verification; a hash string alone is not authority.

## Iterative execution protocol

1. RED tests only.
2. Verify intended RED.
3. Minimum implementation to GREEN.
4. Run Task 1 + inherited integration + Task 0 custody regressions.
5. Hostile self-audit; any defect gets a fresh RED before repair.
6. Repeat until exact-head clean.
7. Independent Macha review before freeze.

No protected partitions or candidate outcomes may be opened for debugging or convenience.
