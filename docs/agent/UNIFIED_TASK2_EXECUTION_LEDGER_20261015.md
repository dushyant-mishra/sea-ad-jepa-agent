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
- the authority scope→stage table is a documented lane invariant and must be preserved;
- NumPy is an explicit dependency of canonical identity because the accepted NumPy-scalar policy is part of Task 1 identity semantics.

## Population custody reused without recomputation

- population/support lineage: PR #349 head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`;
- canonical population registry SHA-256: `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`;
- frozen reader split raw SHA-256: `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`;
- 104 `reader_fit`, 22 `reader_validation`, 23 `reader_oracle` donors.

The historical metadata-only population validator is reusable evidence and does not open expression data. Local custody verification against the calibration bundle independently reproduced the frozen reader-split SHA, 149 rows and 104/22/23 partition counts. Protected biological values were not opened.

## Prospectively frozen cross-fit law

`fold_count = 5` remains fixed prospectively. Folds are donor-grouped and exist only inside `reader_fit`; every fit donor appears in exactly one held-out fold and never on train and held-out sides of the same fold.

### Pre-execution amendment to assignment law

The original prelaunch draft proposed deterministic source-stratified assignment from donor identity plus non-outcome source metadata. Before any outcome-bearing Task 2 execution, hostile self-audit found that no exact donor→source registry with equivalent custody had been bound. Inferring source from donor-name prefixes or accepting an arbitrary caller mapping would manufacture authority.

Because **no outcome-bearing Task 2 execution had occurred**, the prospective law was amended before exposure:

- current-TD authoritative assignment law is now `DONOR_SHA256_ORDER_ROUND_ROBIN_V1`;
- the 104 fit donors are derived only from the exact frozen reader-split raw bytes;
- donor ordering is deterministic by SHA-256 of donor identity;
- source labels do not enter current-TD fold assignment unless a future new manifest explicitly binds an independently qualified source registry;
- generic caller-supplied donor/source construction is retained only as `FIXTURE_UNBOUND` mechanics and cannot satisfy current-TD manifest population authority;
- any later change to fold count or assignment law creates a new manifest identity and requires requalification.

This amendment is prospective, outcome-blind, and identity-changing. It is not a silent reinterpretation of the earlier draft.

Rationale for five folds remains: 104 fit donors yields approximately 20–21 held-out donors per fold, avoiding very small held-out folds while keeping repeated calibration tractable.

## Access law

`reader_fit`: only current-TD outcome-bearing surface; held-out evaluation occurs through the frozen cross-fit law.

`reader_validation`: only partition identity may be bound; biological values, generic metadata, candidate summaries, support/rescue statistics and calibration statistics are forbidden upstream.

`reader_oracle`: only partition identity may be bound; biological values, summaries, metadata and calibration statistics remain forbidden until a later explicit authority transition.

Actual access is not self-reported authority. Producer reads must pass through an instrumented population-access session that emits an `OBSERVED_ACCESS_LEDGER_V1`. The producer receipt binds the exact ledger SHA. Validation resolves and re-hashes the ledger, requires exact event equality, and checks donor/fold/phase rights. A forbidden read invalidates the session before data are returned.

## Identity law

Task 2 reuses accepted Task 1 `canonical_sha256` primitives. No second semantic serializer or authority taxonomy is allowed.

All manifest SHA strings are claims until underlying objects are resolved and re-hashed. Controller code is verified from actual bytes under Git-blob identity. Raw-file identities require exact bytes and direct SHA-256 verification.

Current-TD population authority additionally requires:

- access policy `population_authority = AUTHENTICATED_READER_SPLIT`;
- exact reader split raw SHA `efe43e63...`;
- exact population registry SHA `50b29d7e...`;
- assignment basis containing exactly 104 fit donors derived from the frozen split;
- manifest population-split registry and access policy agreeing on both frozen identities.

## Iterative audit history

### Initial RED — PR #387

Head `bca25a15ce24cc0aed2cca119712a56b423dc79c`.
Run `38674182634`, job `116223898766`: expected RED, 10 failures, all because `manifest_v1.py` did not yet exist.

### First GREEN

Head `3cb85ea2e498218729aa029f0de100fd90154f85`.
Run `38674344347`, job `116224402875`: 10 Task 2 tests passed; 27 accepted Task 1 tests passed.

### Self-audit cycle 1

RED head `3f421afc12f887418ed7c3d0dae18777ea22780c`: 4 new intended failures / 10 prior passes. Gaps: receipt did not bind exact policy identity; assignment inputs were not identity-bound; manifest dependency surface was incomplete; fold schema was loose.

GREEN head `852571312a5c17523bf45939de71d263d772596f`: 14 Task 2 tests + 27 Task 1 tests passed.

### Self-audit cycle 2

RED head `e4fb8c7111b835d95177ce9263da53433e780a69`: 5 new intended failures / 14 prior passes. Gaps: no donor/fold/phase access events; protected generic metadata too broad; assignment-basis SHA was trusted without inline basis; role tag alone could pass; producer receipt lacked a closed schema.

GREEN head `94477424c3dbe29f3e0ff89c97517cada0f4ad50`: run `38675071725`, job `116226705062`, 19 Task 2 tests + 27 Task 1 tests passed.

### Self-audit cycle 3

RED head `222535934bcafc6bbfabd13fb1be879637ddd345`: run `38675193800`, job `116227081359`, 6 new intended failures / 19 prior passes. Gap: producer-authored receipt was still a claim rather than actual observed access.

GREEN head `5521196253746f2c0f7b80bd2548815557756985`: run `38675463619`, job `116227927376`, 25 Task 2 tests + 27 Task 1 tests passed. Added instrumented access session, immutable access ledger binding, forbidden-read invalidation, and protected-identity-only gateway.

### Self-audit cycle 4 — population custody

RED head `785b1b0270a60f4db77b9da10db06ef05eab77d3`: run `38675823098`, job `116229066485`, 6 new intended failures / 25 prior passes. Gap: a lawful-looking policy could still be constructed over arbitrary caller-supplied donors rather than the frozen reader split.

GREEN4 is in progress at the time of this ledger update. It separates `FIXTURE_UNBOUND` mechanics from `AUTHENTICATED_READER_SPLIT` authority and makes current-TD authority consume actual reader-split raw bytes matching the frozen SHA.

## Runtime boundary note

`PopulationAccessSession` is an application-level instrumentation/access contract, not an OS sandbox. Arbitrary malicious Python running in the same process could introspect private attributes. Therefore real protected partitions must remain absent from the producer process entirely; Task 2 does not claim cryptographic/OS isolation. Later runtime qualification must enforce process/storage boundaries where needed.

## Iterative execution protocol

1. RED tests only.
2. Verify intended RED.
3. Minimum implementation to GREEN.
4. Run Task 1 + inherited integration + Task 0 custody regressions.
5. Hostile self-audit; any defect gets a fresh RED before repair.
6. Repeat until exact-head clean.
7. Independent Macha review before freeze.

No protected partitions or candidate outcomes may be opened for debugging or convenience.
