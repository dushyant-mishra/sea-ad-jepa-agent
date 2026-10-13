# Target Discovery test-of-test qualification interface — 2026-10-12

Status: `TD_ONLY_PREFREEZE__SYNTHETIC_LANE_READ_ONLY__NO_REAL_OUTCOME_EXECUTION`

## Purpose

Define how Target Discovery (TD) will qualify its own biological tests against known synthetic truth **without modifying or taking ownership of the synthetic-dataset lane**.

This document belongs to Target Discovery. It creates no synthetic-world generation authority, no target authority, no corrected-replay authority, no TD60 authority, no Stage4 authority and no training authority.

## Hard lane boundary

Target Discovery owns:

- TD estimands;
- TD decision rules;
- PASS / FAIL / NOT_ESTIMABLE semantics;
- donor/source replication requirements;
- failure-scope semantics;
- gate qualification records;
- whether a qualified TD gate may later run on real data.

The synthetic-dataset lane owns:

- generator code;
- synthetic-world definitions;
- realization authority;
- controller truth;
- world/challenge hashes;
- synthetic-lane calibration and qualification.

TD must never:

- regenerate or mutate synthetic worlds;
- retune a synthetic challenge after seeing a TD result;
- import synthetic-lane execution authority;
- write to synthetic-lane branches, result namespaces or controller records;
- reinterpret synthetic stress amplitudes as measured human effect sizes.

TD may only consume a frozen external challenge package by exact immutable identity.

## External challenge package contract

A synthetic package is admissible to TD only if the synthetic lane supplies, read-only:

1. an immutable challenge/package identifier;
2. exact package/directory SHA-256;
3. exact fit-view hashes;
4. a separate controller-truth manifest/hash;
5. challenge capabilities/semantics;
6. donor/source/entity identifiers needed by the TD estimand;
7. explicit declaration of what truth is planted and what is not;
8. proof that fit-side observations do not expose controller truth;
9. authority statement showing world generation is complete/frozen for that package.

TD does **not** require access to generator internals during gate execution.

## Fit-side / controller separation

For every TD test qualification:

### Fit-side TD executor may see

- frozen synthetic observations needed by the test;
- donor/source/operator/support identifiers when lawful for that test;
- the candidate/gate configuration already frozen by TD;
- no truth labels or expected verdict.

### TD qualification controller may see after execution

- controller truth;
- expected challenge semantics;
- TD executor output;
- PASS / FAIL / NOT_ESTIMABLE result;
- raw sufficient statistics;
- evidence hashes.

### Fit-side TD executor must never see

- controller rare-state labels;
- technical-twin identity;
- planted relational/query truth labels;
- expected PASS / FAIL / NOT_ESTIMABLE;
- qualification outcome.

## Required qualification record per TD gate

Every gate that can later reject biological evidence must have a frozen qualification record containing:

- `candidate_id`;
- `gate_id`;
- `qualified_gate_executor_sha256`;
- `estimand_sha256`;
- `decision_rule_sha256`;
- external synthetic package identity and SHA-256;
- exact challenge IDs used;
- truth capability required for each challenge;
- expected semantic result per challenge;
- observed result per challenge;
- raw sufficient-statistics hash;
- sensitivity-control result;
- null / technical-specificity result;
- NOT_ESTIMABLE control result;
- donor/source scope tested;
- exact failure scope of the gate;
- authority flags all false.

A runnable real-data gate without this record is not biologically qualified.

## Qualification semantics

The synthetic qualification asks whether **the test behaves correctly when truth is known**. It does not ask whether the synthetic world is realistic enough to prove human biology.

Three classes are mandatory:

### Positive truth

When the biological property targeted by the TD gate is planted and sufficiently supported, the gate must recover the property at its declared scope.

### Negative / technical truth

When the biological property is absent, or when a matched technical pseudo-state is planted instead, the gate must not manufacture biological support.

### Underidentified truth

When the property exists but the frozen observations/support are insufficient for the gate, the gate must return `NOT_ESTIMABLE` rather than `FAIL`.

A gate cannot be qualified using only positive controls.

## Failure-scope firewall

Synthetic qualification failure means **the TD test is not qualified for that regime**. It does not mean the candidate biology is false.

Real-data gate failure, once the gate is qualified, may reject only the exact frozen claim named in the gate contract.

Examples:

- fine-local failure cannot erase broad/mesoscale relational evidence;
- rare-state failure cannot erase common-state evidence;
- one source-specific failure cannot establish universal biological absence unless universality is the explicit hypothesis;
- insufficient rare support must be `NOT_ESTIMABLE`;
- donor-restricted truth must not be called technical merely because many donors have exact-zero prevalence.

## TD57C-successor qualification requirements

The current PR #316 real-data successor remains on execution hold until its exact TD-side logic passes known-truth qualification.

The required external challenge capabilities are:

1. `REL_BROAD_MESO_POSITIVE` — broad/mesoscale relational biology present;
2. `REL_FINE_RECURRENT_POSITIVE` — reproducible fine relational biology present;
3. `REL_RARE_LOCAL_ISLAND_POSITIVE` — donor-recurrent rare local biology present;
4. `REL_MULTI_ISLAND_POSITIVE` — multiple disconnected rare/local islands present;
5. `REL_DONOR_RESTRICTED_POSITIVE` — legitimate biology present only in a subset of donors;
6. `REL_SOURCE_VISIBILITY_STRESS` — same latent biology with source-dependent observability;
7. `REL_TECHNICAL_TWIN_NEGATIVE` — matched technical pseudo-rarity with biological relational truth absent;
8. `REL_NULL_NEGATIVE` — no target relational biology;
9. `REL_UNDERPOWERED_POSITIVE` — biology present but frozen support deliberately below estimability requirements.

These capability names are TD requirements only. They do not authorize TD to create the worlds. A synthetic-lane owner may satisfy them using existing or future frozen packages.

## Expected behavior of the TD57C successor

The successor is qualified only if, under frozen TD logic:

- mesoscale positive truth is recovered at mesoscale without requiring fine-scale PASS;
- fine recurrent truth is recovered when supported;
- rare local islands are detectable through the rare-conditioned arm when supported;
- disconnected rare islands are not forced into one global connected neighborhood;
- donor-restricted true biology is preserved without requiring all donors to contain the program;
- source visibility changes do not create latent source biology;
- technical twins and null worlds do not produce a biological PASS;
- underpowered true biology routes to `NOT_ESTIMABLE`;
- no single fine-scale failure propagates into rejection of unrelated scales/programs.

## Relationship to PR #313

PR #313 remains a separate executor-engineering lane and is not modified by this document.

Its existing authenticated gate-output bridge is appropriate: it binds executor, estimand and decision-rule identities and preserves raw sufficient statistics while refusing to invent thresholds.

Before any candidate×gate role in #313 becomes real-execution-ready, TD must additionally bind a successful synthetic test-of-test qualification record for that exact executor/estimand/decision-rule identity.

If synthetic qualification shows that a currently frozen R1-R4 gate definition is biologically mismatched, TD must create an explicit prospective supersession. It must not silently change #313 semantics.

## Current known synthetic coverage

Read-only audit state:

- Q00-Q11 provide strong nuisance/observation falsifiers but do not currently provide planted C2 relational truth or C3 query-conditioned truth;
- the historical full-transcriptome fixture provides broad/fine/rare/donor hidden factors and can serve as a deterministic unit/sensitivity substrate if consumed read-only at a pinned identity;
- PR #311 rare-world V2/V3 provides donor-structured rare truth, technical twins, source-dependent observability, evidence/depth ladders, multimodal/context/perturbation challenge geometry;
- no existing evidence yet demonstrates that the actual TD56/57B/57C/59 or #316/#313 gate logic has been run blind against these known truths.

## Current blocker

`TD_TEST_OF_TEST_INTERFACE_FROZEN__NO_SYNTHETIC_LANE_WRITES__C2_RELATIONAL_TD_QUALIFICATION_PACKAGE_OR_ADAPTER_STILL_REQUIRED__PR316_REAL_EXECUTION_HOLD__PR313_REAL_GATE_EXECUTION_HOLD`
