# Macha independent hostile review — Unified Task 2 (A4), PR #388

Date: 2026-10-15.

Role: independent hostile reviewer of controller work. Non-controlling.

The only real-data read was a **metadata-only** replay: the reader-split raw bytes (partition identity), plus the donor→source table from my own `ccc3a089` audit. No biological values, candidate outcomes or validation/oracle values were opened.

## Verdict

`REJECT_UNIFIED_TASK2`

`TASK2_REMAINS_OPEN__UNIFIED_TASK3_REMAINS_BLOCKED`

The access-time mechanics are sound:
- fold, phase and donor gating;
- protected partitions limited to identity-only access;
- reader-split raw bytes verified when the policy is built;
- controller code verified by git blob;
- one semantic identity per manifest role;
- closed schemas.

Four core authority claims, however, hold only by string or by trust. An arbitrary donor list and arbitrary folds can still pass as current-TD population authority. A fabricated ledger passes as observed access. The manifest validates contradictory protected-partition and cross-fit policies, and it omits required identities.

## Head

| item | value |
|---|---|
| head | `2c391137bf0564d31d39efa1ec0a61e198dbf027` (PR #388 → `freeze/unified-task1-accepted-799d2e23-20261015`) |
| ancestors | `799d2e23`, `e37a22b8` |
| delta | 10 added files; no Task 0/1 file modified |
| local tests | full `tests/v5/td_unified`: 95 passed (local, not CI) |

## Blocking findings

All probes are in `docs/agent/macha_task2_review_evidence_2c391137/task2_probe1.py` and its `.log`.

### T2-B1 — CRITICAL: current-TD population authority is string-based at consumption

- **Loci (`scripts/v5/td_unified/manifest_v1.py`):**
  - `require_current_td_population_authority` (~331–350);
  - `validate_population_access_policy_payload` (~374–470);
  - `validate_manifest_population_binding` (~353–371);
  - `validate_manifest` (~670–708).
- **Failing inputs.**
  - **P1.** A hand-built `PopulationAccessPolicy` with 104 donors named `FAKE_000…FAKE_103`, the frozen `efe43e63…` and `50b29d7e…` strings, and arbitrary folds passes `require_current_td_population_authority`. Its payload passes `validate_population_access_policy_payload`.
  - **P2.** The real 104 reader-fit donors with folds that are not the `DONOR_SHA256_ORDER_ROUND_ROBIN_V1` assignment also pass.
  - **P5.** The population registry `50b29d7e…` is never resolved or recomputed anywhere. It is a constant string compared with strings.
- **Why it matters.**
  - Only `build_current_td_access_policy_from_reader_split` touches the split bytes; every consumer trusts the strings it then copied.
  - This contradicts the plan's global constraint ("a digest string is never authority") and the packet's claim that an arbitrary donor list cannot masquerade as the current population.
  - The prospective cross-fit law is not enforced at any consumer.
- **Smallest repair.**
  - Every authority predicate (`require_current_td_population_authority`, payload validation for `AUTHENTICATED_READER_SPLIT`, `validate_manifest`) must resolve the reader-split raw bytes by raw SHA-256, recompute the 104 fit donors, and recompute the folds by the declared law. It then requires exact equality with the policy's `fit_donors` and `crossfit_folds`.
  - Either resolve and recompute the population registry `50b29d7e…` from its frozen bytes, under PR #349's own canonicalization or the raw receipt SHA-256, or remove it from the authority predicates and label it declared-but-unverified.

### T2-B2 — IMPORTANT: a fabricated observed-access ledger is indistinguishable from a session-generated one

- **Locus.** `validate_producer_access` (~588–631) and `PopulationAccessSession.finalize`.
- **Failing input.** **P3.** A ledger dict and receipt written by hand, with no session, recording one clean EVAL event, are accepted. Any producer can therefore submit a clean ledger that hides a forbidden read.
- **Why it matters.**
  - The module docstring, check 7 and the plan's protected-partition review focus all depend on "observed, not self-reported" access.
  - This gap is separate from the acknowledged limit that application-level instrumentation is not an OS sandbox: it is checkable in software and currently unchecked.
- **Smallest repair.**
  - Make the session harness-owned. A registry that the producer cannot write issues a `session_id` and stores the finalized ledger. The ledger binds `session_id`, plus a registry attestation such as an HMAC with a harness-held key.
  - `validate_producer_access` must resolve the ledger only from that registry and refuse any ledger the registry did not issue.
  - Add the P3 negative test.

### T2-B3 — IMPORTANT: redundant manifest sub-policies are unvalidated and can contradict the access policy

- **Loci.** `_MANIFEST_ROLE_BY_FIELD` and `validate_manifest`. These fields are checked only for role tag and digest:
  - `crossfit_policy_sha`;
  - `protected_partition_policy_sha`;
  - `reader_fit_policy_sha`, `reader_validation_policy_sha`, `reader_oracle_policy_sha`.
- **Failing input.** **P4.** The manifest validates with all of these:
  - `PROTECTED_PARTITION_POLICY` = `{"reader_validation":"BIOLOGICAL_VALUES_ALLOWED","reader_oracle":"BIOLOGICAL_VALUES_ALLOWED"}`;
  - `CROSSFIT_POLICY` = `{"folds":"LEAVE_SOURCE_OUT_CHOSEN_LATER"}`;
  - `READER_VALIDATION_POLICY` = `{"use":"RESCUE_ESTIMABILITY"}`.
- **Why it matters.** The same quantities (folds, protected partitions, per-partition use) have two authority surfaces with no precedence or consistency rule. A downstream consumer reading the manifest's protected-partition policy would read "values allowed".
- **Smallest repair.** Either remove the redundant fields, or require each to be a canonical sub-object derived from the access policy and checked for equality, with a closed schema per role. Examples: the cross-fit policy binds the assignment law plus the canonical SHA of the folds; the protected-partition policy binds exactly `PARTITION_IDENTITY`-only.

### T2-B4 — IMPORTANT: the manifest omits required identities from its own contract and the plan

- **Loci.**
  - `_MANIFEST_ROLE_BY_FIELD`, versus the plan's Task 2 Step 5 ("per-unit code/policy/artifact/metric/reference identities");
  - the controller's `UNIFIED_TASK2_MANIFEST_ACCESS_SCHEMA_CONTRACT_V1_20261014.md` §8 required identities.
- **Defect.** These identities are absent:
  - normalization/library contract;
  - TargetPortfolio code and policy;
  - per-unit producer and executor code/policy/schema;
  - metric definitions;
  - reference-producer identities;
  - falsifier/control identities.

  `qualification_registry_sha` cannot carry them transitively, because any role-tagged object is accepted there (P4 shows vacuous objects validate). The packet's check 1, "binds the full declared dependency surface", is therefore not met.
- **Smallest repair.** Add the missing identity fields, or one closed per-unit identity table with content checks. Alternatively, amend the contract and plan prospectively to defer them explicitly to the Task 3 registry, stating that the manifest binds the registry's verified content, not an opaque role-tagged object.

## Packet checks 1–10

| check | result |
|---|---|
| 1 manifest identity surface | **FAIL** (T2-B3, T2-B4). Controller code is git-blob-verified, semantic dependencies are canonically recomputed and role-checked, and cross-role reuse is refused. |
| 2 raw-file identity | reader-split bytes verified (SHA `efe43e63…` matches the bundle file); `verify_raw_file_sha256` recomputes. Population registry not verified (T2-B1). |
| 3 population custody | **FAIL** (T2-B1). Split semantics are correct when built from bytes (149 = 104/22/23; I replayed it). `FIXTURE_UNBOUND` is distinct. |
| 4 cross-fit law | law correct when built: every donor held out once, 21/21/21/21/20, no overlap. Not enforced at consumption (T2-B1/P2). |
| 5 protected partition | **PASS.** Identity-only, custody phase, donor-free; values, metadata, summaries and calibration fail closed. |
| 6 reader-fit access | **PASS.** Fold, phase and donor bound; TRAIN cannot read held-out donors and EVAL cannot read train donors; unknown values refused. |
| 7 observed access | **FAIL** (T2-B2). The OS-sandbox limitation is correctly disclosed. |
| 8 schema/code parity | closed (`additionalProperties: false`), required counts 17/11/5/5 match code. |
| 9 no second identity system | **PASS.** Reuses Task 1 `canonical_sha256`. `verify_git_blob_sha1` duplicates Task 1's private helper; minor. |
| 10 inherited state | **PASS.** No Task 0/1 change; no authority granted. |

## Prospective cross-fit replacement

The switch from source-stratified to `DONOR_SHA256_ORDER_ROUND_ROBIN_V1` was **lawful**: it was prospective, made before any outcome-bearing execution, and unstratified donor folds are valid for pooled donor-primary inference. It is not result-driven tuning.

The stated premise is incomplete, though. A custodied donor→source table did exist:
- PR #349's registry (the `50b29d7e…` this head binds by string) carries donor×operator strata with source;
- my `POPULATION_SUPPORT_AUDIT` `population/DONOR.csv` at `ccc3a089`, identity-bound in frozen Task 0 via receipt index `2af2acc3…`.

What was missing was a *verified binding in Task 2*, not the registry itself.

Metadata-only replay of the law's held-out composition per fold:

| fold | HVS | NPH52 | SEA_AD |
|---|---|---|---|
| 0 | 7 | 4 | 10 |
| 1 | 7 | 2 | 12 |
| 2 | 11 | 6 | 4 |
| 3 | 7 | 4 | 10 |
| 4 | 9 | 1 | 10 |

Fold 4 holds out a single NPH52 donor. This does not affect pooled donor-primary tests. It does rule out per-fold source-stratified metrics, and the folds' training composition varies. Non-blocking; record it.

## Non-blocking

- **N1.** Carry M1 forward: memoize recursive receipt verification before Task 3.
- **N2.** `ProducerAccessReceipt` is not yet bound into `SCIENTIFIC_RECEIPT_V1` (for example via `access_policy_sha` plus `access_ledger_sha` as INPUT/ACCESS_POLICY roles). Bind it when producers emit scientific receipts.
- **N3.** `reader_fit_values` for all fit donors are loaded into the producer process at session construction. This is acceptable under the disclosed application-level limit, but the harness should hold the values, not the producer.

## Freeze decision

Task 2 may not be frozen at `2c391137`. After T2-B1 to T2-B4 are repaired RED-first, a focused re-check of those four items suffices.

`TASK2_REMAINS_OPEN__UNIFIED_TASK3_REMAINS_BLOCKED`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
