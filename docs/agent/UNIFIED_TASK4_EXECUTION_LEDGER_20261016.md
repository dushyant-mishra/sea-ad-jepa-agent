# Unified Task 4 execution ledger

Plan: `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`  
Binding amendment: `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`  
Frozen Task 3 base: `117dd51dea827e734b299982da93991b934bdc8f`  
Implementation PR: #404, `work/unified-task4-impl-20261016`  
RED PR: #403, `work/unified-task4-red-20261016`  
Mode: native execution, RED-first.

## Authority boundary

Task 4 remains custody/mechanics only. It grants no biological PASS/FAIL, target winner, representation winner, Stage 4 authority, protected-value authority, or training authority. Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No final hidden challenge values, production nonces, protected biological values, or final challenge worlds were generated in this implementation lane.

## Preserved RED

The first valid Task 4 RED is GitHub Actions run `38938697657`, job `117100597615`, on PR #403. The token had `Contents: read`; the focused suite produced 14 intentional failures at not-yet-existing Task 4 interfaces. An earlier collection/glob defect was corrected before accepting this RED.

Subsequent RED-first repairs preserved the following concrete failures:

- terminal-accounting gap: run `38943608912`, job `117117078319`, `1 failed, 67 passed`;
- campaign schema drift (`issued_exposures` absent from schema): run `38944319232`, job `117119472176`, `1 failed, 83 passed, 1 skipped`;
- incomplete/aliasable C1-C9 barrier vocabulary: run `38944836349`, job `117121219990`, `12 failed, 80 passed, 1 skipped`;
- trusted signer object accepted without actor-action attestation: run `38945592644`, job `117123776998`, `1 failed, 94 passed, 1 skipped`;
- caller self-asserted actor/process context could make the barrier GREEN: run `38946266116`, job `117126036930`, `1 failed, 95 passed, 1 skipped`.

Each repair was limited to prospective Task 4 code/tests/schemas/workflow. Frozen Task 0-3 production modules were not modified.

## Implemented custody laws

The implementation now provides:

- current-`registry_v1` Task 4 adapter and direct legacy-registry import firewall;
- canonical defect-bearing revocation identities that ignore cosmetic stage/status/restriction changes;
- persistent append-only cross-process custody with signed events, external expected-head checking, trusted external head anchors, stale-head refusal, truncation/rechain refusal, and replay mutation tests;
- externally verified actor-action attestations for privileged custody append, bound to the exact canonical event subject and exact next sequence;
- closed requirement-class and issuer law;
- closed exact C1-C9/R5 preauthority check vocabulary;
- deliberate refusal of caller-supplied mappings as proof of C5-C9 actor credentials, policy currency, construction law, or process isolation;
- finite sealed challenge lifecycle with exposure spend at issuance, canonical method identity, immutable output freeze, reveal-after-freeze only, regeneration verification, and explicit terminal accounting for every realization;
- strict schemas for campaign, custody, exposure, output-freeze, reveal, and evidence objects;
- NO-ECHO publication/secret scanning across repository bytes, logs, artifacts, receipts, paths, and raw binary tokens;
- read-only Task 4 CI with focused tests, full unified regression, 10k replay equivalence, and dedicated 100k replay benchmark.

## Latest verified code/test state before candidate-packet-only edits

Exact code/test head `cfa3b7c4f92a1569639b6733a6956c516d7f4cf4` has Task 4 run `38946411134`, job `117126540739`, fully GREEN:

- focused Task 4 custody suites: PASS;
- dedicated projected 100k custody replay benchmark: PASS;
- full `tests/v5/td_unified` regression: PASS.

Same-head regressions:

- Task 1 A1-A9: run `38946411299` PASS;
- Task 2 manifest/access: run `38946411331` PASS;
- Task 3 registry: run `38946411463` PASS;
- unified synthetic integration: run `38946411400` PASS.

Three inherited workflows remain red because they install pytest but not NumPy before importing `canonical_v1.py`; their logs fail at `ModuleNotFoundError: No module named 'numpy'` before exercising the intended assertions:

- Task 0 migration audit: `38946411227`;
- Task 0 B1-B5 verification: `38946411361`;
- Task 3 B6 workflow policy: `38946411617`.

These are classified as pre-existing workflow-environment defects, not Task 4 authority failures. Task 4 does not modify those frozen workflows.

## Current readiness classification

The implementation is mechanically candidate-ready for independent hostile review once the final candidate head receives a fresh Task 4 GREEN run. It is **not accepted authority**. FINAL campaign authority remains deliberately fail-closed because no genuine external C5-C9 context evidence has been wired; in-process or caller-created status/context mappings cannot unlock it.

Independent review must pin the exact candidate SHA and explicitly test sibling authority routes, restart/replay/rechain behavior, legacy aliases, actor credential substitution, self-asserted status/context objects, exposure/reveal/output mutation, terminal missingness, NO-ECHO leakage, and Task 0-3 byte preservation. Independent acceptance is required before any later-stage authority change.
