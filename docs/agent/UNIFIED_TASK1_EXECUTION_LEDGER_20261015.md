# Unified Task 1 execution ledger — 2026-10-15

Base/freeze: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.
Controlling plan: PR #380 head `5b6bf07e7d8b69b286ea430b09765a5ee4743325` plus frozen Task 0 custody.
Authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## Carry-forward blockers

Unified Task 1 begins prospectively only after Task 0 acceptance. Old Tasks 1–2 are ADAPT_AND_WRAP substrate only, never completed unified work. Carry forward `U_TASK1_3_FOUNDATION`, O1–O8, D1 exception-wrapping, E2 precommitment erratum, post-reveal fresh-family design, and reader-fit calibration-status questions as blocking dependencies for any same-code-path or later qualification use.

## Reuse evidence

Old Task 1 implementation: `ff597faf2182522a320ec5322f8db9b67c9c6094:scripts/production_synthetic/canonical_v1.py`, blob `b8a34d8d47f618e7dcde1b3e5c53584701294561`.
Old Task 1 tests: `ff597faf2182522a320ec5322f8db9b67c9c6094:tests/production_synthetic/test_canonical_v1.py`, blob `0bce5cbdde37112f316ffc1386342b34c0ed4d41`.
These establish tested canonical byte behavior and known-answer compatibility; they do not establish the new recursive scientific-receipt or unified-authority semantics.

## Rulings

Ruling: preserve the old Task 1 canonical byte rules rather than invent a second serializer — this preserves semantic distinctions such as measured zero vs missing and avoids needless fingerprint churn. New unified receipt identities get their own explicit V1 domain and schema, so old synthetic identity prefixes are not silently reinterpreted as new authority.

Ruling: Task 1 does not consume any candidate outcomes or protected partitions. All tests use synthetic dictionaries and dummy identities only.

## Iterative protocol

Each Task 1 change follows RED -> intended failure confirmation -> minimal GREEN -> inherited old-Task-1 compatibility tests -> hostile self-audit -> fix/repeat -> exact-head CI -> independent review before freeze.
