# Unified Task 2 TD execution manifest prelaunch plan — 2026-10-15

> **Status:** PREPARED ONLY. DO NOT IMPLEMENT OR EXECUTE TASK 2 UNTIL UNIFIED TASK 1 IS INDEPENDENTLY ACCEPTED AND FROZEN. Use the project iterative law: classify/reuse → RED → intended-failure confirmation → minimum implementation → GREEN → inherited regressions → hostile self-audit → repair/repeat → exact-head verification → independent review/freeze where required.

## Goal

Prepare the exact prospective implementation path for PR #380 Task 2: `TD_EXECUTION_MANIFEST_V1` plus the current-TD population/data-access law. Task 2 makes the scientific execution machine and its permitted data access explicit and machine-verifiable. It does **not** choose a target, open protected outcomes, establish human gate authority, or authorize training.

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Launch gate

Current Task 1 exact independent-review candidate is `86fa996f609bec3f39d0f6a12d7f040b2544af39` in PR #385. Task 2 may start only if fresh independent Macha review accepts that exact head, or a later repaired exact head that is separately reviewed and accepted. If Task 1 mutates, this launch plan must be rebound to the new accepted Task 1 head before any Task 2 RED is created.

Task 0 frozen base: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`.
Accepted architecture: PR #379 `3064ca545f0c94859ea989cd49a04fcbd5b9a303`.
Controlling implementation-plan lineage: PR #380 `5b6bf07e7d8b69b286ea430b09765a5ee4743325`.

## No-repeat / reuse classification

### Unified Task 2 itself

Classification: `OPEN__NEW_UNIFIED_INTERFACE`.

The new Task 2 is **not** the historical production-synthetic Task 2. Its job is manifest identity and population-access enforcement under architecture amendment A4.

### Historical production-synthetic Task 2

Classification: `ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE`.

Exact source head: `ff597faf2182522a320ec5322f8db9b67c9c6094`.

Historical code/test identities to retain:
- `scripts/production_synthetic/custody_v1.py` blob `8efb7622eb2773305f9159cafdb19ccae8946fef`;
- `tests/production_synthetic/custody_fixtures_v1.py` blob `23fb531077942223f4b4169853403de380af0b89`;
- `tests/production_synthetic/test_custody_v1.py` blob `3d27802f60ff026aef8b6d1a07bb879e55a3a39b`;
- `tests/production_synthetic/test_custody_v1_hostile.py` blob `8f22cd69e3332f4f6f4129b3099673472317520a`.

Reusable lessons include exact identity, freeze-before-use, actual exposure accounting, fail-closed custody, identity-keyed randomness, immutable lineage and anti-reroll/anti-retune discipline. The old code maps mainly to later sealed challenge/finalizer work. It **must not** be copied or relabeled as completion of unified Task 2.

## Files to create only after the launch gate opens

- `scripts/v5/td_unified/manifest_v1.py`
- `schemas/target_discovery/unified_v1/td_execution_manifest_v1.json`
- `schemas/target_discovery/unified_v1/population_access_policy_v1.json`
- `tests/v5/td_unified/test_manifest_v1.py`
- a Task-2-specific CI workflow or an extension of the unified workflow that triggers on the Task 2 implementation, schemas, tests and custody ledger.

Do not create these executable Task 2 files before the launch gate opens.

## Frozen interfaces

Task 2 consumes accepted Task 1 primitives:
- `canonical_sha256`
- `verify_scientific_receipt`
- `AuthorityRecord`

Task 2 produces:
- `PopulationAccessPolicy`
- `ProducerAccessReceipt`
- `TDExecutionManifest`
- `build_current_td_access_policy(...) -> PopulationAccessPolicy`
- `validate_manifest(payload, resolver) -> TDExecutionManifest`
- `validate_producer_access(manifest, receipt) -> None`

No second canonical serializer or authority taxonomy is permitted.

## Manifest identity law

`TD_EXECUTION_MANIFEST_V1` must bind authenticated exact identities, not branch tips, PR numbers or human-readable labels. At minimum it must bind:

- canonical registry identity;
- observation contract identity;
- support contract identity;
- controller code and controller policy identities;
- candidate, endpoint and source registry identities;
- qualification registry identity;
- population split registry identity;
- data access policy identity;
- `reader_fit` policy identity;
- `reader_validation` policy identity;
- `reader_oracle` policy identity;
- cross-fitting policy identity;
- protected-partition policy identity;
- required per-unit producer/code/policy/schema/metric/reference identities and authority records.

Every digest named by the manifest is a claim until the corresponding object is resolved and canonically re-hashed under the accepted Task 1 verifier.

## Current-TD access law to implement

### `reader_fit`

This is the only population surface on which current TD outcome-bearing estimation may be fit/evaluated. Held-out evaluation means deterministic cross-fitting **within `reader_fit`**. Stage-specific access classes must be explicit: values, metadata, support-only summaries and calibration-only statistics cannot be conflated.

### `reader_validation`

Protected. Its existence/partition identity may be bound from already frozen split-registry custody, but biological values, candidate-specific summaries and rescue statistics are unavailable to current Task 2 execution. No aggregate derived from protected validation values may flow upstream to rescue fit estimability.

### `reader_oracle`

Protected more strongly. Its existence/partition identity may be bound for custody, but no biological values, summaries or calibration statistics are available until an explicit later authority transition permits them.

### Actual-access receipts

Declared intent is insufficient. Every producer execution must emit a receipt enumerating the exact partitions and access classes actually touched. `validate_producer_access` must invalidate a receipt if observed access exceeds the manifest, even when the numeric scientific output is otherwise correct.

### Donor/fold law

A donor cannot appear on both train and held-out sides of the same cross-fit split. Cross-fit assignment must be deterministic from frozen identities and must not depend on candidate outcomes or later validation/oracle observations.

## Population custody to reuse, not recompute

Use authenticated historical population custody rather than rebuilding the support census merely for Task 2:

- controlling historical population/support lineage: PR #349 head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`;
- canonical population registry payload SHA-256: `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`;
- split SHA-256: `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`;
- calibration bundle SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`;
- metadata DB SHA-256: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`;
- 6,351,753 rows, 149 donors, 42 operators, 3 sources, 2,028 donor×operator strata;
- partitions: 104 `reader_fit`, 22 `reader_validation`, 23 `reader_oracle` donors.

These facts are custody inputs, not permission to open protected values.

## Prelaunch design item: exact cross-fit fold count

**Status: MUST BE FROZEN BEFORE FIRST OUTCOME-BEARING TASK 2 EXECUTION.**

The binding science fixes deterministic cross-fitting within `reader_fit`, but current controlling materials do not establish one exact fold count. Historical feasibility work discussed leave-one-donor-out in places; that does not automatically make LODO the unified manifest law, and choosing 5-fold merely for convenience would be equally unjustified.

Therefore Task 2 must expose an explicit `fold_count`/assignment-policy field and prospectively freeze the exact assignment law before execution. The choice must be made without inspecting candidate outcomes, `reader_validation`, or `reader_oracle`, and may not be changed after outcome-bearing execution begins except through a new manifest identity and requalification.

## RED-first test matrix

When the gate opens, the first Task 2 commit is tests only and must fail for the intended absence of `manifest_v1.py`.

Required controlling-plan RED tests:

```python
def test_current_td_policy_crossfits_only_within_reader_fit(): ...
def test_reader_validation_access_cannot_rescue_estimability(): ...
def test_reader_oracle_access_is_protected_until_later_authority_transition(): ...
def test_producer_receipt_must_enumerate_actual_partitions_and_access_classes(): ...
def test_numeric_success_with_forbidden_partition_access_is_invalid(): ...
def test_held_out_token_has_no_authority_without_bound_policy(): ...
def test_manifest_binds_exact_code_policy_schema_registry_and_population_identities(): ...
def test_branch_or_pr_number_cannot_serve_as_scientific_identity(): ...
def test_moved_decision_bearing_identity_requires_new_manifest_digest(): ...
```

Add hostile tests before GREEN for:
- forged access receipt with allowed declaration but forbidden observed access;
- validation-derived aggregate relabeled as fit-side summary;
- oracle-derived calibration token relabeled as metadata;
- donor leakage across cross-fit folds;
- duplicate/conflicting partition identity;
- manifest digest that resolves to mutated policy bytes;
- active-lineage identity that is superseded/revoked once Task 3 exists (forward compatibility test may remain deferred until Task 3);
- navigation metadata changes do not alter scientific identity, while decision-bearing policy changes do;
- protected access remains invalid even when result numerically equals the lawful result;
- unknown access class and unknown partition fail closed.

## Minimum implementation sequence after Task 1 acceptance

1. Cut a Task 2 branch from the exact independently accepted Task 1 head.
2. Record launch base and all reuse identities in a Task 2 execution ledger.
3. Freeze the exact cross-fit assignment law prospectively.
4. Add `test_manifest_v1.py` only; run and preserve intended RED.
5. Implement closed population-access schema and `PopulationAccessPolicy`.
6. Implement `ProducerAccessReceipt` with actual observed access.
7. Implement closed manifest schema and `TDExecutionManifest` validation using Task 1 recursive object verification.
8. Run focused Task 2 + Task 1 tests GREEN.
9. Run inherited unified synthetic integration and Task 0 custody regressions.
10. Hostile self-audit against protected-data leakage, false identity, stale authority and branch/PR identity shortcuts; repair RED-first until clean.
11. Freeze exact controller candidate and seek independent review before treating Task 2 as accepted foundation for Task 3.

## Forbidden during Task 2

- Do not read `reader_validation` or `reader_oracle` biological values.
- Do not use either protected partition to rescue estimability.
- Do not recompute real support/population assets merely because a new task began.
- Do not create candidate-specific biology, target winners or representation winners.
- Do not convert support absence, unresolved status or numerical failure into biological failure.
- Do not import historical synthetic Task 2 as completed unified authority.
- Do not let a branch, PR number, filename, free-text `held-out` label or hash string act as scientific authority.
- Do not choose fold count, thresholds or access policy after seeing outcomes.

## Launch-complete criterion

Preparation is complete when this plan, the machine prelaunch readiness ledger and the Task 2 review packet are present on the durable audit/handoff surfaces. **Task 2 itself remains unstarted** until independent Task 1 acceptance.