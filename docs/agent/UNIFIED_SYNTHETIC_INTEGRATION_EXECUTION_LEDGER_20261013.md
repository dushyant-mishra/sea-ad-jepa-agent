# Unified synthetic integration execution ledger — 2026-10-13

Authority: non-authorizing mechanics integration only.

Historical decision-ledger rule: no new JEPA architecture is being designed here. This work integrates already-decided synthetic components and existing downstream contracts. Any future new experiment must name the unresolved question, prior experiments touching it, why they did not answer it, and the exact authority for the new test.

Ruling 1: PR #315 base does not physically contain the PR #253 `v79_hierarchical_biology.py` and `v79_observation_operator.py` primitives even though the design binds them. The implementation will materialize those two files byte-for-byte from frozen PR #253 commit `1a0ab6e1108af924ca13e81caa3c70f3101d251c`; no mechanics changes are permitted in this integration.

Ruling 2: the green post-TD harness was produced after PR #315. Downstream compatibility will be established against its frozen callable/identity without modifying TD estimands or decision rules. If exact materialization is required for CI, it must be byte-identical to the audited source and recorded as imported custody, not a new architecture.

Ruling 3: the first slice is a deterministic mechanics fixture only. It asks no new biological question and performs no fitting, scoring, controller adjudication, target selection, or training.
