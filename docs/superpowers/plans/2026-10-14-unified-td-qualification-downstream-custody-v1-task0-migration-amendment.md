# Unified TD Qualification and Downstream Custody V1 — Task 0 Migration Amendment

## 0. Status, precedence and preserved predecessor

This document is a binding amendment to:

`docs/superpowers/plans/2026-10-14-unified-td-qualification-downstream-custody-v1-implementation.md`

The predecessor plan is preserved exactly at commit:

`d79474e62d9151bb67e49873df8ddc1d5bdbc890`

This amendment does not rewrite that predecessor. The predecessor plan plus this amendment constitute the controlling implementation plan after focused review accepts the amended head.

Where this amendment changes sequencing, prerequisites, execution method or Task 0 scope, this amendment controls.

Accepted architecture remains PR #379 exact head:

`3064ca545f0c94859ea989cd49a04fcbd5b9a303`

Acceptance comment remains:

`6174861625`

No implementation task is authorized merely by committing this amendment. Task 1 remains blocked until Task 0 is implemented, independently reviewed, accepted, and frozen at an exact head.

Binding project authority remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

---

## 1. Revised dependency order

The implementation sequence is now:

```text
Task 0 — PRE-MERGER MIGRATION AND CUSTODY AUDIT
  ↓
TD_EXECUTION_MANIFEST_V1
  ↓
TD_QUALIFICATION_REGISTRY_V1
  ↓
KNOWN_TRUTH_CASEBUNDLE_V1 / TRUTH_BUNDLE_V1
  ↓
TARGET_QUALIFICATION_BUNDLE_V1
  ↓
DOWNSTREAM_CERTIFICATION_CONTRACT_V1
```

Tasks 1–12 in the predecessor plan retain their numbering and scientific content unless this amendment explicitly changes a prerequisite or execution rule.

Task 0 is a hard prerequisite. Do not begin Task 1 until:

1. Task 0 has been implemented RED-first;
2. its migration outputs pass the hostile validator;
3. a fresh independent implementation review accepts it;
4. the accepted Task 0 exact implementation head is frozen;
5. unresolved dependencies are explicitly carried forward.

---

## 2. Task 0: Pre-merger migration and custody audit

### Goal

Inventory, classify and preserve all meaningful pre-unification synthetic, TD and downstream work so that no valid work is silently abandoned, rebuilt unnecessarily, misclassified, duplicated under a new name, incorrectly promoted, or left with ambiguous scientific authority.

Task 0 is evidence/custody work. It must not open current human candidate outcomes, rerun candidate tournaments, or create new biological authority.

### Required audit scope

Audit all meaningful work that predates the unified architecture or was already underway when the lanes were merged, including at least:

- synthetic Tasks 1–12 history;
- current and unfinished synthetic branches/PRs;
- known-truth/simulator prototypes;
- TD gate branches and repaired gate surfaces;
- TD controller/tournament work;
- TargetPortfolio logic;
- support/estimability registries;
- authenticated real-data qualification/calibration artifacts;
- Macha audit outputs;
- downstream teacher/student code;
- downstream leakage/falsifier suites;
- JEPA handoff/certification work;
- historical sealed batteries;
- failed experiments and negative priors;
- generated fixtures;
- calibration/custody receipts;
- schema/provenance/RNG/canonicalization utilities;
- workflows and machine-readable state files.

Do not rely only on prose handoffs. Inspect Git history, open PRs, relevant historical branches, frozen exact heads, generated artifacts and receipts.

Do not open protected human candidate outcomes merely to classify infrastructure.

### Required migration classes

Every meaningful artifact receives exactly one top-level migration class:

```text
REUSABLE_SHARED_INFRASTRUCTURE
KNOWN_TRUTH_SUBSTRATE
KNOWN_TRUTH_CHALLENGE_ASSET
DEVELOPMENT_FIXTURE
HISTORICAL_NEGATIVE_CONTROL
PRODUCTION_INTERFACE_DEPENDENCY
SUPERSEDED_PARALLEL_IMPLEMENTATION
CLOSED_FAILED_EXPERIMENT
NEEDS_REVIEW_BEFORE_CLASSIFICATION
```

Definitions:

- `REUSABLE_SHARED_INFRASTRUCTURE`: canonical serialization, deterministic IDs, content hashing, parent binding, receipt lineage, commit/reveal, identity-keyed RNG, provenance, observation/support primitives, realism calibration infrastructure. Reuse unless a documented defect requires replacement.
- `KNOWN_TRUTH_SUBSTRATE`: donor/source/operator generators, count generation, support/evidence-right generation, observation processes, library-mass modeling and biological/nuisance latent worlds. Migrate into the CaseBundle path.
- `KNOWN_TRUTH_CHALLENGE_ASSET`: source-confounding, sparse-estimability, leakage, measurement-artifact, stable-subspace/unstable-axis, malformed-authority and related worlds. Migrate into the challenge-family registry.
- `DEVELOPMENT_FIXTURE`: useful RED/GREEN or mechanics fixture with no sealed final-qualification authority.
- `HISTORICAL_NEGATIVE_CONTROL`: historical construction that exposed a genuine failure mode and must remain a permanent regression challenge where applicable.
- `PRODUCTION_INTERFACE_DEPENDENCY`: useful work that cannot lawfully continue until the merged lane supplies an exact production schema/producer/executor/policy. Do not replace the missing interface with synthetic authority logic.
- `SUPERSEDED_PARALLEL_IMPLEMENTATION`: independent synthetic copies of TD gates, decision engines, TD controller, portfolio/winner selection, target qualification or downstream certification. Preserve evidence/tests/lessons but stop advancing authority.
- `CLOSED_FAILED_EXPERIMENT`: failed experiments remain failed unless separately and prospectively reopened for a documented scientific reason.
- `NEEDS_REVIEW_BEFORE_CLASSIFICATION`: provenance/scientific role cannot be established from exact evidence. Do not guess or manufacture replacement lineage.

If one historical module contains separable roles, decompose it into sub-artifacts so each sub-artifact receives one class. Do not give one artifact conflicting classes without an explicit decomposition record.

### Required audit record per artifact

For every significant artifact record:

```text
artifact_id
artifact_path
artifact_digest
source_branch
source_commit
original_role
scientific_role
migration_class
current_authority
qualification_stage_if_applicable
active_lineage_status_if_applicable
known_defects
tests_or_receipts
reusable_components
superseded_components
destination_in_unified_architecture
requires_requalification
requalification_reason
historical_evidence_retained
```

Branch names and PR numbers are navigation metadata only. Exact code/artifact identities must be recorded wherever available.

### Required audit of in-progress work

Every active or partially completed task additionally records:

```text
task_id
branch
exact_head_sha
current_status
original_goal
work_completed
work_remaining
files_created
tests_created
inputs_used
outputs_generated
scientific_assumptions
continue_stop_or_redirect
reason
unified_destination
blocking_dependency_if_any
```

Apply these rules:

**Continue** only work that directly contributes to retained Tasks 1–3, canonical identity/custody, CaseBundle, TruthBundle, challenge generation, observation simulation, support/evidence modeling, sealed-exam infrastructure, realism/calibration or external truth adjudication.

**Stop and freeze** duplicate production scientific authority: duplicate gates, reference-decision logic, TD controller, target/winner selection, target qualification or downstream certification. Preserve exact state before stopping; do not delete or destructively rewrite it.

**Redirect/split** mixed work. Keep reusable substrate/challenge components and separately classify duplicate verdict/authority components as superseded.

### Mandatory preservation of scientific lessons

Task 0 must extract already-established scientific laws from historical work and map each into the unified architecture as a schema invariant, producer contract, challenge-family requirement, regression test, registry rule, Target Qualification Bundle obligation, or downstream certification obligation.

At minimum preserve:

```text
measured zero != unsupported
unsupported != unresolved
unresolved != numerical failure
numerical failure != biological FAIL
support cannot be manufactured
source failures cannot be averaged away
counts and normalization library must thin together
evidence acquisition != measurement depth
synthetic known truth != human biological truth
stable subspace != stable individual axes
NO_WINNER / TARGET=NONE is lawful
false certainty and false abstention are both qualification failures
reader_fit held-out means deterministic reader_fit cross-fitting under current TD policy
reader_validation / reader_oracle remain protected
```

No important scientific lesson may remain only in historical prose.

### No unnecessary recomputation

Task 0 must reuse already authenticated/cached identities where they exist.

Do not:

- redownload real datasets;
- recompute transport hashes without a specific custody failure;
- rerun broad real-data support discovery;
- rerun candidate outcomes;
- regenerate historical reference artifacts merely to classify them;
- manufacture new canonical identities because lineage is inconvenient.

If lineage cannot be verified, classify `NEEDS_REVIEW_BEFORE_CLASSIFICATION` or record a custody defect.

---

## 3. Task 0 files and interfaces

**Files:**

- Create: `scripts/v5/td_unified/premerger_migration_v1.py`
- Create: `tests/v5/td_unified/test_premerger_migration_v1.py`
- Generate after validator GREEN: `results/target_discovery/unified_qualification_v1/PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json`
- Generate after validator GREEN: `results/target_discovery/unified_qualification_v1/PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json`
- Create human-readable audit: `docs/agent/PREMERGER_MIGRATION_AND_CUSTODY_AUDIT_V1_20261014.md`

**Interfaces:**

- Consumes: Git history/PR/branch/artifact/receipt metadata; exact authenticated identities already present in the project; historical handoffs as navigation evidence only.
- Produces: `MigrationClass`; `ArtifactMigrationRecord`; `InProgressWorkRecord`; `UnresolvedWorkRecord`; `validate_migration_matrix(...) -> None`; `validate_unresolved_work_ledger(...) -> None`; `audit_premerger_inventory(...) -> MigrationAuditReceipt`.
- Does **not** implement `TD_EXECUTION_MANIFEST_V1`, `TD_QUALIFICATION_REGISTRY_V1`, gate registration, Target Qualification Bundle or downstream certification logic. Those remain owned by the merged lane and later tasks.

---

## 4. Task 0 RED-first execution steps

- [ ] **Step 0.1: Freeze the audit input surface before inventory writes**

Record the controlling architecture head `3064ca545f0c94859ea989cd49a04fcbd5b9a303`, predecessor plan head `d79474e62d9151bb67e49873df8ddc1d5bdbc890`, current open synthetic/TD/downstream PR heads, and the Git history/search cut used for Task 0. This is navigation/custody metadata, not scientific authority.

- [ ] **Step 0.2: Write hostile RED tests for migration completeness and authority safety**

```python
def test_every_significant_artifact_has_exactly_one_migration_class(): ...
def test_available_exact_commit_or_digest_cannot_be_omitted(): ...
def test_parallel_implementation_cannot_remain_ambiguously_active(): ...
def test_reusable_work_cannot_be_marked_obsolete_without_rationale(): ...
def test_closed_failed_experiment_cannot_be_silently_promoted(): ...
def test_unresolved_work_cannot_disappear_from_ledger(): ...
def test_conflicting_classes_require_explicit_subartifact_decomposition(): ...
def test_branch_or_pr_name_cannot_create_authority(): ...
def test_candidate_outcomes_are_not_opened_to_classify_infrastructure(): ...
def test_global_project_authority_is_unchanged(): ...
```

- [ ] **Step 0.3: Write RED tests for preservation of in-progress work and scientific lessons**

```python
def test_active_or_partial_work_has_continue_stop_or_redirect_decision(): ...
def test_stopped_partial_work_retains_exact_head_files_tests_and_missing_work(): ...
def test_mixed_work_records_reusable_and_superseded_subcomponents(): ...
def test_required_scientific_lessons_have_explicit_unified_destinations(): ...
def test_authenticated_real_calibration_identity_is_reused_not_reinvented(): ...
```

- [ ] **Step 0.4: Run Task 0 tests and preserve RED**

Run:

`python -m pytest -q tests/v5/td_unified/test_premerger_migration_v1.py`

Expected: FAIL because Task 0 validator/inventory outputs are absent.

- [ ] **Step 0.5: Inventory exact historical work without opening protected outcomes**

Search relevant Git history, branches, open/closed PRs, scripts, tests, schemas, workflows, receipts, generated fixtures, calibration artifacts, negative-result ledgers and handoffs. Reuse exact authenticated identities rather than regenerating them.

- [ ] **Step 0.6: Implement the migration validator and machine-readable records**

Implement only inventory/classification/custody validation in `premerger_migration_v1.py`. It must fail closed on missing class, missing available identity, ambiguous authority, unresolved-item loss, conflicting classification without decomposition, or global-authority drift.

- [ ] **Step 0.7: Generate the migration matrix**

Write:

`results/target_discovery/unified_qualification_v1/PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json`

The matrix must contain the complete classified inventory and exact available identities, including historical evidence retention and requalification requirements.

- [ ] **Step 0.8: Generate the unresolved-work ledger**

Write:

`results/target_discovery/unified_qualification_v1/PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json`

Every unresolved item must contain:

```text
item_id
missing_dependency
why_missing
who_owns_resolution
can_known_truth_lane_finish_now
requires_merged_lane_interface
requires_real_data
blocks_same_code_path
blocks_known_truth_qualification
blocks_real_reference_ready
blocks_human_execution
```

Unfinished work must not be conflated with obsolete work.

- [ ] **Step 0.9: Write the human-readable migration/custody audit**

`docs/agent/PREMERGER_MIGRATION_AND_CUSTODY_AUDIT_V1_20261014.md` must explain what survives unchanged, what is reused, what migrates to known-truth infrastructure, what becomes a challenge/regression asset, what remains unfinished, what depends on merged-lane interfaces, what is superseded, what failed historically, what requires requalification, and the actual authority of each major artifact family.

- [ ] **Step 0.10: Run Task 0 tests GREEN**

Run:

`python -m pytest -q tests/v5/td_unified/test_premerger_migration_v1.py`

Expected: PASS against the exact generated matrix and unresolved-work ledger.

- [ ] **Step 0.11: Run hostile closure check for Task 0**

From the two machine-readable artifacts alone, verify the merged lane can answer unambiguously:

- what was built;
- what was validated;
- what failed;
- what remains reusable;
- what was superseded;
- what is unfinished;
- where every surviving artifact lives;
- what authority each artifact actually has;
- what requires requalification;
- what exact production interface blocks each unresolved item.

Any ambiguity blocks Task 0 completion.

- [ ] **Step 0.12: Commit Task 0 implementation as its own reviewable identity**

```bash
git add \
  scripts/v5/td_unified/premerger_migration_v1.py \
  tests/v5/td_unified/test_premerger_migration_v1.py \
  results/target_discovery/unified_qualification_v1/PREMERGER_ARTIFACT_MIGRATION_MATRIX_V1.json \
  results/target_discovery/unified_qualification_v1/PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json \
  docs/agent/PREMERGER_MIGRATION_AND_CUSTODY_AUDIT_V1_20261014.md
git commit -m "audit: migrate pre-unification TD and synthetic custody"
```

- [ ] **Step 0.13: Fresh independent Task 0 implementation review**

A fresh reviewer must challenge completeness, classification, exact identities, partial-work preservation, authority mapping, no-outcome-opening, no-recomputation, and unresolved dependency ownership. Review defects return to Task 0 and create a new exact implementation identity where behavior/records changed.

- [ ] **Step 0.14: Freeze accepted Task 0 head before Task 1**

Only after the independent review accepts Task 0 may the owner freeze its exact head and authorize proceeding to Task 1. Task 1 remains blocked before that point.

---

## 5. Task 0 completion gate

Task 0 is complete only when the migration artifacts alone answer:

> What happened to every significant piece of synthetic, TD and downstream work that existed before the merger?

The answer must identify exactly:

- what survives unchanged;
- what is reused;
- what moves into known-truth infrastructure;
- what becomes a challenge/regression asset;
- what remains unfinished;
- what depends on a new production interface;
- what is superseded;
- what failed historically;
- what must be requalified;
- what authority each artifact actually has.

If that cannot be answered unambiguously, Task 1 is blocked.

---

## 6. Revised execution method

After this amendment is focused-reviewed and accepted, implementation uses:

`SUBAGENT-DRIVEN EXECUTION`

Required pattern:

```text
Task 0
  → fresh implementation review
Task 1
  → fresh implementation review
Task 2
  → fresh implementation review
...
Task 12
  → fresh implementation review
whole-branch hostile audit
```

Do not batch multiple authority-critical tasks under one review merely to save time.

Tasks 1–5 are especially authority-sensitive: canonical identity, manifest/access law, registry, sealed challenge custody, and known-truth/human path equivalence.

A review defect returns work to the owning task and creates a new exact implementation identity when decision-bearing behavior changes.

The final whole-branch hostile audit does not replace per-task review.

---

## 7. Stop gates remain binding

The predecessor plan STOP gates remain unchanged:

```text
STOP U1 — before sealed final known-truth exposure
STOP U2 — before KNOWN_TRUTH_QUALIFIED promotion
STOP U3 — before REAL_REFERENCE_READY
STOP U4 — before human candidate execution
STOP U5 — before downstream training eligibility/authorization
```

Task execution below a stop gate never implies permission to cross it.

In particular:

- implementing sealed-exam machinery does not authorize exposing the final sealed exam;
- implementing registry promotion does not authorize promotion;
- implementing real-reference schemas does not create real-reference readiness;
- implementing the human path does not authorize human execution;
- implementing downstream certification does not authorize training.

Each stop gate requires its own prospective evidence and authorization.

---

## 8. Focused amendment review checklist

The focused reviewer should verify only the plan amendment and its interaction with the predecessor plan:

1. Task 0 is a hard prerequisite before Task 1.
2. The audit scope covers synthetic, TD and downstream pre-merger work rather than synthetic history alone.
3. Every meaningful artifact gets exactly one migration class, with explicit sub-artifact decomposition for mixed modules.
4. Exact available commit/digest identities are required and PR/branch names are non-authoritative.
5. Active/partial work is explicitly continued, stopped/frozen or redirected.
6. Existing authenticated calibration/support identities are reused unless a specific custody defect exists.
7. Scientific lessons are migrated into executable/shared obligations rather than left in prose.
8. The machine-readable migration matrix and unresolved-work ledger are mandatory Task 0 outputs.
9. Task 0 is RED-first and independently reviewed before Task 1.
10. The execution method is subagent-driven with per-task review.
11. STOP U1–U5 and the global project authority remain unchanged.
12. The amendment does not create competing manifest/registry/gate/downstream authority implementations.

Until this focused review passes, implementation remains off.