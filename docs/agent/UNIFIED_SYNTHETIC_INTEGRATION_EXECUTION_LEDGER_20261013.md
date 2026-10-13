# Unified synthetic integration execution ledger — 2026-10-13

Authority: non-authorizing mechanics integration only.

Historical decision-ledger rule: no new JEPA architecture is being designed here. This work integrates already-decided synthetic components and existing downstream contracts. Any future new experiment must name the unresolved question, prior experiments touching it, why they did not answer it, and the exact authority for the new test.

Ruling 1: PR #315 base does not physically contain the PR #253 `v79_hierarchical_biology.py` and `v79_observation_operator.py` primitives even though the design binds them. The implementation will materialize those two files byte-for-byte from frozen PR #253 commit `1a0ab6e1108af924ca13e81caa3c70f3101d251c`; no mechanics changes are permitted in this integration.

Ruling 2: the green post-TD harness was produced after PR #315. Downstream compatibility will be established against its frozen callable/identity without modifying TD estimands or decision rules. If exact materialization is required for CI, it must be byte-identical to the audited source and recorded as imported custody, not a new architecture.

Ruling 3: the first slice is a deterministic mechanics fixture only. It asks no new biological question and performs no fitting, scoring, controller adjudication, target selection, or training.

Dependency update — Macha/V79: the full frozen Q00-Q11 campaign execution is complete: 1,056/1,056 fits accounted for, 1,053 COMPLETE and 3 preserved `NOT_DIAGNOSED`, with no scoring, no truth access and no training. Controller scoring is now separately authorized against exact campaign receipt `a0065925789c58409a85ccbf72d24f5c7b1be142a4d17eddc434babdf0d0e340` and scorer head `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`; authorization bytes SHA-256 `6beedf515328fe6c96cbd6e36df25ce0ad368c6fa46798d6819e68165349db5f`. Final Layer-A scientific qualification remains pending the scored/adjudicated result and audit.

Audit correction: an earlier chat update incorrectly stated that 40 integration tests had passed. Durable CI proves the opposite at RED head `37a980e0d1f091d91df34f92f75a7b3351c020d1`: workflow run `38456612038` failed during collection because all four planned production modules were still absent. That failure is valid TDD evidence and is preserved. No integration mechanics are considered green until a later workflow run on the implemented modules passes. The controller must use CI evidence, not chat assertions, for qualification claims.

Implementation continuation: production modules were subsequently added under the frozen RED tests only; no test semantics, biological estimand, downstream gate, or authority rule was changed to obtain GREEN. Await CI on the implemented head before any mechanics-qualification claim.
