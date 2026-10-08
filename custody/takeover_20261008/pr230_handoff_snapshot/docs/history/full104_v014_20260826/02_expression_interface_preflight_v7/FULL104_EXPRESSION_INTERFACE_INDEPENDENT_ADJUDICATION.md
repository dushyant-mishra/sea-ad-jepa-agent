# FULL104 expression-interface independent adjudication

Terminal decision: `STOP_NPH_PROTECTED_EXPRESSION_REACHABLE`

Phase 2 authorized: `false`

## Dataset-Fidelity

`PASS` on the emitted 84-row payload, row identities, 42 asset pins, 41,238-address/state geometry, measured-zero handling, raw-count normalization, and deterministic replay.

## Red-Team

`STOP` on the data firewall. The NPH helper called `qread()` on each whole TRAIN derivative and only then selected requested columns. Those derivatives contain 17 reader-fit donors and two reader-oracle donors (`human_NPH_1025`, `human_NPH_878`). Therefore protected expression was reachable in memory and the report fields `reader_fit_only=true` and `protected_expression_read=false` are false.

Red-Team also found that final publication was not fail-atomic, its subsequently generated output manifest lacked an external anchor and omitted itself, and identity-sidecar exclusion was declarative rather than enforced by a frozen consumer.

## Adjudication

V7 is engineering/provenance evidence only. Its `PASS_FULL104_EXPRESSION_INTERFACE` report is superseded and cannot authorize D/shared/private derivation.

Required repair:

1. Use authenticated physical NPH derivatives containing reader-fit donors only, or a demonstrably bounded reader that cannot deserialize protected columns.
2. Publish completed artifacts atomically from staging and externally anchor the final manifest.
3. Separate audit identity from teacher inputs and freeze a consumer that accepts only `normalized_values` and `observation_states`.
4. Rerun in a fresh versioned directory and obtain independent Dataset-Fidelity and Red-Team PASS.
