# Foundation Successor Representation Acceptance Audit — 2026-10-11

PR #276 now freezes a prospective acceptance contract for representation candidates evaluated **after** 2026-10-11. It explicitly does not re-adjudicate u0000 or u0205.

Verified code head: `7548a42c3a9bc05780abd60899f5cf70e1fafea2`.
GREEN run `38153629474`, job `114512001140`: **23 passed in 0.58 s**.
Current PR #276 evidence head additionally carries the frozen contract and RAM/I/O/wall-time receipts.

Contract artifact:
`results/v4/FOUNDATION_SUCCESSOR_REPRESENTATION_ACCEPTANCE_CONTRACT_V1.json`

## Donor transfer
For a future unopened candidate on held-out TRAIN donors:
- biology score must exceed its prospectively generated permutation q95 envelope;
- residual source, operator and support prediction must each remain at or below their own permutation q95 envelopes;
- all conditions are verdict-bearing.

## Matrix transfer
For leave-one-matrix-out evaluation:
- all cells/labels not identifiable from non-held-out matrices are counted and excluded from biology performance rather than silently imputed;
- each evaluable matrix must show biology above its permutation q95;
- residual matrix identity must remain within its permutation q95;
- every evaluable matrix must pass; pooled scoring without the identifiability ledger is forbidden.

## Conditional technology invariance
On held-out donors or held-out matrices:
- biology must exceed its permutation q95;
- compute the increment in source predictability when learned state is added to biological controls;
- that increment must remain within the prospectively generated permutation envelope.

Multiple verdict-bearing targets/strata require family-level permutation correction under the evaluation contract.

## Audit boundary
These rules were frozen after u205 outcomes were already known. Therefore u205 may **not** be retrospectively promoted or failed under this new contract. Its current ruling remains: evidence available, technology invariance not qualified, representation freeze blocked.

No representation winner, target winner, Stage4, target-discovery corrected-value authority, TEST/Morabito/pathology access or JEPA training authority is created.
