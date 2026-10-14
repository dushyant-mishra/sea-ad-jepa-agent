# Production Synthetic V3.1.1 — Tasks 1–3 execution handoff

Date: 2026-10-14

Status:
`TASKS_1_3_EXECUTABLE__SUBAGENT_DRIVEN_ONLY__TASK4_AFTER_THREE_CLEAN_TASK_REVIEWS__NO_PRODUCTION_REALIZATION`

Authority:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Exact execution starting point

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Planning PR: #356
Branch: `plan/production-synthetic-v3-1-1-20261014`

At handoff creation the branch includes:
- accepted primary implementation plan;
- F1/N3–N6 binding notes;
- post-Macha real-lane dependency delta through PR #363;
- this execution handoff.

Accepted design base remains exactly:
`847fe734b15e52f204f18903a124e1cfd3bf111d`

Controlling in-repo specs:

V3.1:
- path: `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-consolidated-corrective-amendment.md`
- Git blob SHA: `48e71346c74378729e39a4de6b80699d3cb43d15`
- SHA-256: `234af6dffa6f5d8bef03802a2eee4d8f65714ecd77718fa99c9b66e1d958b65c`

V3.1.1:
- path: `docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-1-erratum.md`
- Git blob SHA: `977faa75e37c31610122e7ad45d2fc26dac536a3`
- SHA-256: `ab1ae1bb67765cc025f580205d7c082ee4af470dd39ef23c4f000414e8e9363f`

Execution-support documents are non-controlling where they conflict with those specs:
- `docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-implementation.md`
- `docs/superpowers/plans/2026-10-14-production-synthetic-v3-1-1-binding-notes-f1-n3-n6.md`
- `docs/superpowers/plans/2026-10-14-production-synthetic-post-macha-real-lane-dependency-delta.md`

## 2. Execution protocol

Use `superpowers:subagent-driven-development`.

Strict sequence:
1. Task 1 implementer in fresh context.
2. Task 1 fresh-context spec/hostile reviewer.
3. Resolve any Critical/Important findings before Task 2.
4. Task 2 implementer in a new fresh context.
5. Task 2 fresh-context reviewer.
6. Resolve findings before Task 3.
7. Task 3 implementer in a new fresh context.
8. Task 3 fresh-context reviewer.
9. Only after all three task reviews are clean or formally adjudicated under the SDD protocol may Task 4 begin.

Do not parallelize Tasks 1–3. They define types/interfaces consumed downstream.

No subagent may touch real-lane PRs. No task in this handoff crosses a production realization/sealed/finalization gate.

## 3. Controller-only custody boundary

The controller—not an implementer or reviewer subagent—owns the real withheld family.

For Tasks 1–3:
- no real withheld-family specification exists in any subagent prompt;
- no real nonce is given to subagents;
- use dummy secrets only;
- generic mechanism code may be public only if ordinary development/fixture worlds also exercise that code path;
- any code path uniquely identifying the withheld family must remain off-repo;
- the production withheld spec/parameterization/applicability/scoring data stay off-repo;
- later commitment is `H(withheld_spec || controller_nonce || generator_semantic_hash || class_tag)`;
- repository-tree absence scanning is tested with dummy secrets only during Task 2.

No controller secret should be synthesized, guessed, logged, or committed during Tasks 1–3.

## 4. Task 1 brief — canonical identity and serialization

Create:
- `scripts/production_synthetic/canonical_v1.py`
- `tests/production_synthetic/test_canonical_v1.py`

Required interfaces:
- `canonical_json_bytes(obj) -> bytes`
- `raw_sha256(data) -> str`
- `semantic_sha256(obj) -> str`
- `ordered_registry_digest(rows, identity_keys) -> str`

Required RED→GREEN properties:
- JSON-key permutation does not change semantic identity;
- explicit row/shard reorder with stable scientific identity keys does not change semantic identity;
- line endings are normalized under semantic serialization;
- distinct raw bytes retain distinct raw-byte hashes;
- missing/numeric/order representation is canonical and documented;
- the 41,238 registry is bound by ordered content, not unordered set membership;
- no candidate, gate, target, representation or biological verdict enters identity logic.

Task 1 reviewer must verify:
- canonicalization is deterministic across supported Python object orderings;
- scientific identity rather than storage order controls registry semantics;
- raw hash and semantic hash are not conflated;
- non-finite/numeric/missing normalization cannot create silent collisions;
- tests actually permute serialization/ordering rather than merely restating the same object;
- no authority-bearing PASS receipt is emitted.

Required completion evidence:
- implementation commit(s);
- exact pytest command and output;
- reviewer verdict for spec compliance and code quality;
- no open Critical/Important finding.

## 5. Task 2 brief — custody, commit/reveal and identity-keyed RNG

Create:
- `scripts/production_synthetic/custody_v1.py`
- `tests/production_synthetic/test_custody_v1.py`
- `tests/production_synthetic/test_custody_v1_hostile.py`

Required interfaces:
- `freeze_generator_version`
- `commit_secret`
- `derive_stream`
- `record_exposure`
- `validate_successor_version`
- `attest_realization_set`
- `scan_secret_absence`

Required RED→GREEN properties:
- nonce floor ≥256 bits;
- commitment mismatch fails closed;
- domain-separated randomness is keyed to scientific identity, never row/storage position;
- scientific-unit streams are invariant to row ordering;
- integer-offset seed namespaces are rejected;
- seed replacement/discard/seed shopping is rejected;
- exact realization budgets are attested;
- after exposure, easier successors are forbidden except documented generator-defect repair;
- such a defect repair becomes `POST_EXPOSURE_VERSION` and inherits no qualification;
- `record_exposure` is explicit and immutable enough to support E1/E4 ordering;
- dummy-secret repository scan fails if dummy preimage appears in tracked content;
- published scan result contains only boolean/tree attestation, not secret bytes/preimage.

Task 2 reviewer must verify:
- no RNG path depends on array index/storage traversal;
- domain names cannot collide by concatenation ambiguity;
- frozen-version identity binds the semantic generator specification;
- exposure cannot be erased/replayed to reopen realism iteration;
- production withheld data are not required by tests;
- no withheld-only public path is introduced;
- tree scanning does not leak the secret while proving absence;
- no controller nonce/spec is committed.

Required completion evidence: same contract as Task 1.

## 6. Task 3 brief — calibration firewall, number provenance and realism stopping

Create:
- `scripts/production_synthetic/calibration_v1.py`
- `tests/production_synthetic/test_calibration_v1.py`

Required types/interfaces:
- `CalibrationArtifact`
- `NumericProvenance`
- `RealismContract`
- `validate_calibration_firewall`
- `validate_address_universe_agnostic`
- `derive_budget_from_precision`
- `advance_realism_iteration`

Required RED→GREEN properties:
- calibration donor overlap with development/validation/oracle/reserved holdouts is rejected;
- pathology/proxy stratification is rejected unless separately proven observation-only;
- every decision-bearing number declares exactly one provenance class:
  - `AUTHENTICATED_EMPIRICAL_CALIBRATION`
  - `PINNED_EXECUTOR_MATHEMATICS`
  - `PROSPECTIVE_CONVENTION`
- realism metric list, bands, adjustable observation parameters and maximum budget freeze before iteration 1;
- first jointly passing realization/version stops the realism search;
- exhausted budget returns `REALISM_NOT_QUALIFIED`;
- selecting a best-looking failed version is impossible;
- donor/world/null budgets derive from frozen precision targets, never downstream performance;
- no hidden biological parameter is lawful realism-tuning input;
- V73–V75 detected-feature envelopes are ineligible unless address-universe independence is demonstrated across the historical 96-feature versus canonical 41,238-address setting;
- authenticated real support-hole inputs may be registered only after artifact/hash validation and remain observation-side.

Authenticated real support geometry that may later become calibration inputs after exact artifact binding includes:
- 289 addresses scalar-measured by zero operators;
- 17,186 scalar-measured by all 42 operators;
- HVS-only 730 addresses;
- NPH52-only 4,894 addresses;
- SEA_AD-only 4,710 addresses;
- 4,894 NPH52-only addresses absent from reader-validation scalar support;
- reader-validation/oracle source/donor scarcity as recorded by the Macha audit.

Task 3 reviewer must verify:
- calibration provenance cannot silently become biological truth;
- empirical-envelope parameters and stress-world parameters are distinguishable;
- frozen stopping rule cannot be reset after a failure;
- precision budgeting cannot inspect downstream results;
- address-universe validation is substantive rather than a label/boolean supplied by caller;
- calibration artifacts carry exact identity/hash/source scope;
- no candidate outcome/proxy enters calibration.

Required completion evidence: same contract as Task 1.

## 7. Binding notes that later tasks must inherit

F1:
Task 12 must verify the full 64-character SHA-256 values for both controlling specs; shortened forms are invalid.

N3:
No uniquely withheld-only mechanism code path may be committed. Public generic code must also be exercised by non-withheld development/fixture worlds.

N4:
Synthetic measurement thinning must thin both `MEASURED_SCALAR` stored counts and the matching normalization-library quantity. A thinned-to-zero scalar remains `MEASURED_SCALAR`.

N5:
Do not reuse PR #343 thinning implementation as production authority. Its arithmetic law may inform the contract, but Macha found storage-order RNG, lack of observation-state awareness and failure to thin the library.

N6:
Task 8 must include its own library-size-only adversarial R1 negative control. PR #353 is semantics-fixture evidence, not hostile-control authority.

Post-Macha downstream delta:
- #357 G2 mechanics-qualified, human blocked;
- #358 common R4/C6/C4 increment mechanics-qualified, human blocked;
- #359 G8 contract/mechanics successor; human unauthorized and production thinning remains independent;
- #360 G12 runtime claim-envelope guard mechanics-qualified, human blocked;
- #361 historical sealed battery superseded for G7 by #363;
- #362 G7 source-aware V3 mechanics-qualified but E3 content enforcement still governs SAME_CODE_PATH;
- #363 current sealed cross-gate test-of-test, synthetic mechanics only;
- #355 remains unrepaired at `6e5182e2...` and cannot be promoted.

## 8. STOP gates

These remain mandatory and are not exercised in Tasks 1–3:
- `STOP_A_FIRST_PRODUCTION_REALIZATION`
- `STOP_B_SEALED_QUALIFICATION`
- `STOP_C_FINALIZER`

Implementation authorization covers code and fixture tests only.

## 9. Post-Task-3 checkpoint required before Task 4

Return one checkpoint containing:

1. exact implementation branch and head;
2. Task 1 commit range, pytest command/output, fresh reviewer verdict;
3. Task 2 commit range, pytest command/output, fresh reviewer verdict;
4. Task 3 commit range, pytest command/output, fresh reviewer verdict;
5. every deferred minor/parked ruling from the SDD ledger;
6. explicit statement that no Critical/Important finding remains open;
7. explicit statement that no production realization was created;
8. explicit statement that no real withheld spec/nonce was shared or committed;
9. explicit statement that none of STOP_A/B/C was crossed;
10. exact current heads of all moving real-lane dependencies when Task 4 is about to begin, with movement classification.

Only after this checkpoint is audited may Task 4 start.

## 10. Terminal state

`TASKS_1_3_HANDOFF_FROZEN__POST_MACHA_DEPENDENCIES_RECONCILED__CONTROLLER_SECRET_BOUNDARY_EXPLICIT__TASK4_AFTER_THREE_CLEAN_REVIEWS__STOP_A_B_C_ACTIVE__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
