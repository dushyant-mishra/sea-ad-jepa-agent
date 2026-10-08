# F1 Evidence-Trend Numerical Repair — External Review

Date: 2026-09-03

Reviewed commit: `249bc3b37cb6368ad97fde6bfb2a4560e83ff5a4`

Reviewed package root SHA-256: `ce759e1397cba36d3d595603b14472ccbb756826144a4dbb3db31a964da0c607`

External-review terminal:

`PASS_F1_EVIDENCE_TREND_NUMERICAL_REPAIR_EXTERNAL_REVIEW`

## Scope

This review closes only the synthetic-only F1 evidence-trend numerical-repair gate. It does not authorize the real F1 biological sweep, protected outcome adjudication, training, optimizer/EMA updates, DEV/SEALED/pathology access, nuisance reselection, or reopening any closed scientific branch.

## Findings

1. The conclusion-bearing evidence-trend arithmetic is the frozen paired-difference identity
   `(A100-A20)+0.5*(A80-A40)` in float64; A60 has coefficient zero.
2. The production evidence-slope source remained unchanged across the external-review correction at SHA-256 `afa32c5608ed6749e7c61f6ec7183f186377f6bcd29280b330af6a5265be00ce`.
3. The independent slope reference uses a separate `math.fsum` implementation and does not import the production slope helper.
4. The corrected independent adjudicator reconstructs all 11 current gate Booleans from raw frozen synthetic donor endpoints. It records `FROM_RAW_FROZEN_ENDPOINTS` and `copied_production_gate_count=0`.
5. All 11 independently reconstructed gate Booleans and final `qualified` agree with the superseding production decision on the frozen baseline.
6. Ten deliberate flips of non-evidence production gates are all detected while the independently reconstructed vector remains unchanged, resolving the prior external-review independence defect.
7. Thirteen applicable frozen truth-table attacks are independently reconstructed. The historical free-form nuisance-column attack is correctly non-applicable because current 15C uses the frozen nuisance design rather than caller-supplied nuisance geometry.
8. The already accepted QR-HC3 authority is reused rather than re-litigated. The historical decision-v1, decision-v4, integration-v4, accepted 15C adapter and stable QR-HC3 Git-blob authorities remain unchanged.
9. Exact-flat, legacy-defect, sign, and prospective near-boundary evidence-trend evidence remain consistent with the original repair package.
10. The package firewall records no expression, real F1 outcomes, protected data, model/checkpoint access, training, optimizer or EMA activity during this synthetic-only repair.

## Test-runner note

The normal pytest session wrapper reportedly stalled in the nested Windows worktree. The repair test functions were executed directly through the same Python interpreter without assertion failures. There is no GitHub CI status attached to the reviewed commit. This review therefore relies on the conclusion-bearing source, frozen regression artifacts, hash-bound package, adversarial independence checks, and direct code inspection rather than treating a pytest-session summary as independent evidence.

This Windows-worktree runner behavior must not be carried forward as the production execution strategy. Heavy reader/forward benchmarking should reuse the authenticated WSL/CUDA execution lineage when it remains valid.

## Promotion

The evidence-trend numerical-repair gate is closed at its accepted synthetic-only scope.

The next authorized gate is:

`F1_REAL_READER_FORWARD_EXECUTOR_PREFLIGHT`

The preflight must be prospective, WSL-first for heavy GPU/I/O work, resource-adaptive only in mechanical execution geometry, and scientifically invariant. It must authenticate and hash-bind the real reader/forward path, evidence-mask authority, model/checkpoint/tokenizer/namespace/observation semantics, query/null identities, dtype and shard identity before the real F1 biological sweep can be authorized.

The preflight may benchmark a prospectively fixed, non-conclusion-bearing technical fixture to measure VRAM, RAM, CPU, I/O and forward throughput. It must not adjudicate biological F1 outcomes. Adaptive tuning may change batching, block size, worker count, prefetch, caching and equivalent scheduling only; it may not change query design, evidence masks, nulls, donor order, protected programs, statistics, thresholds, model architecture or scientific semantics.

Real F1 remains forbidden until that preflight is itself reviewed and explicitly promoted.
