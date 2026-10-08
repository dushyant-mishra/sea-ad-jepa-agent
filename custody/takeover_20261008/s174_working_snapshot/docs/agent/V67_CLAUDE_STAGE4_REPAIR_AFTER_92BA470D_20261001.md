# V67 Claude Stage-4 repair after 92ba470d

Read:
`results/v64/V67_CLAUDE_STAGE4_92BA470D_INDEPENDENT_AUDIT_V1.json`

## Hard boundary

Repair authority/preflight only. Do **not** implement or run the Stage-4 executor. Do not compute correspondence, Delta, residualised correspondence, bootstrap inference, p-values or confidence bounds.

## S77 — protect the blocker registry itself

Current execution mode derives grantability from:

`unsatisfied_prerequisites`

but no gate requires that block or exact G16/G17 entries to exist.

Add a fail-closed prerequisite-registry gate.

While the executor is absent, require exactly:

- `G16_EXECUTOR_BOUND`
- `G17_EXECUTOR_OPENS_NO_MATRIX`

and require default execution mode to remain nonzero.

Negative tests:

- delete the entire prerequisite block;
- set the list to empty;
- delete G16;
- delete G17;
- replace either with unrelated text.

All must remain non-grantable.

A later successor must satisfy G16/G17 with explicit bound evidence; it must not become grantable merely by deleting blockers.

## S78 — bind Phase-B consumer semantics

Without computing correspondence, verify the accepted substrate interpretation:

- aggregate binding `2a5404842ec64028789ef2b9cdc13604d80e4aee39298faa8faba70071894f52`
- donors 282
- metacells 3231
- microglia 84129
- genes 4372
- intervals 32153
- pair keys 37419
- T5 rows 10552158
- T3 nnz 6624289
- T4 nnz 55467544
- minimum-donor pairs 36794
- exact five-state availability vocabulary/order
- T3 donor×metacell×gene
- T4 donor×metacell×interval
- T5 donor×pair_key
- pair_gene resolves to gene axis
- pair_interval resolves to interval axis
- metacell ids exactly 0..3230

Mutation-test each semantic family. Use frozen Phase-B artifacts only.

## S79 — producer post-commit custody

Bind the committed Git blob of:

`scripts/v64/build_stage4_execution_authority_v1.py`

in a post-commit patch/receipt and verify it fail-closed. Preserve the build-time SHA; do not pretend the producer knew its final blob before commit.

## S80 — resolve permutation contradiction

The pairing permutation currently says:

`required_for_stage4_execution=false`

while REQUIRED_BINDINGS + G15 make it execution-blocking.

Choose one prospective meaning and make wording/gate behavior consistent.

## Stop

After S77-S80 repair and mutation tests, STOP FOR INDEPENDENT AUDIT.

G16/G17 remain unsatisfied. Stage 4 remains NOT AUTHORIZED. Correspondence unopened. Training OFF. Morabito protected. TD60 blocked.
