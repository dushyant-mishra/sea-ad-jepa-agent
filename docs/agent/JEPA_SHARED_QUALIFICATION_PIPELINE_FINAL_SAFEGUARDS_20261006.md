# JEPA shared qualification pipeline — final safeguards addendum

Date: 2026-10-06
Status: `BINDING_DESIGN_ADDENDUM__NO_EXECUTION_AUTHORITY__TRAINING_OFF`

This addendum supplements `JEPA_SHARED_QUALIFICATION_PIPELINE_DESIGN_20261006.md`. It does not weaken PR #220 governance, the runtime-convergence audit, or any protected-data boundary.

## 1. Failure-containment state machine

Every qualification/mutation run must expose an explicit monotonic lifecycle. At minimum:

- `NOT_STARTED`
- `PREPARED`
- `MUTATED`
- `EMA_APPLIED`
- `CHECKPOINTED`
- `VERIFIED`
- terminal failure states carrying the last proven completed stage and failure reason

There must be no ambiguous success state. Later stages may not be inferred from earlier intent.

Required examples:

- preprocessing succeeds but guard fails -> remain below `MUTATED`;
- optimizer succeeds but EMA fails -> `MUTATED`, never `EMA_APPLIED`;
- EMA succeeds but checkpoint persistence fails -> `EMA_APPLIED`, never `CHECKPOINTED`;
- checkpoint persists but receipt/verification fails -> `CHECKPOINTED`, never `VERIFIED`;
- restart verification failure after mutation must be recorded as failed verification, not silently promoted to a complete deterministic trajectory.

Failure handling must be fail-closed and idempotent where retried. A restart/retry path must prove whether a prior mutation occurred before any additional mutation is allowed.

## 2. Single monotonic experiment/run identity

Every run gets one immutable `experiment_run_id` created before preparation. The same identity must transitively bind:

- scientific governance digest;
- QualificationProtocol digest/version;
- adapter identity;
- feature-identity receipt;
- QualificationBatch scientific identity;
- runtime authority, if mutation-enabled;
- optimizer event;
- EMA event;
- checkpoint lineage;
- qualification/readout artifacts;
- synthetic oracle unblinding event, when applicable.

No stage may mint a replacement run identity for the same experiment. Child/retry runs must explicitly identify their parent and reason.

## 3. Immutable scientific identity vs physical packing

`QualificationBatch` must distinguish immutable scientific content from compute representation.

Scientific identity includes, as applicable:

- biological observations/cells/nuclei included;
- canonical feature/address identities;
- query/hidden-target definitions;
- evidence and measurement masks;
- lawful operator context;
- scientific/evaluation weights;
- target/evidence specification references;
- unit-of-inference and grouping metadata;
- split membership.

Compute transformations such as microbatching, sharding, sparse/dense conversion, device placement, tensor contiguity, token packing, worker ordering, or memory-layout changes must not alter the scientific identity.

A `batch_scientific_identity_digest` must remain invariant across lawful repacking. If repacking changes the experiment semantics, a new batch/run identity is required.

## 4. Derived-feature visibility is transitive

Visibility classes apply to descendants, not only raw fields.

A field classified as `SPLIT_ONLY`, `READOUT_ONLY`, `PROVENANCE_ONLY`, or `ORACLE_ONLY` cannot be transformed into a model/preprocessing feature by renaming, aggregation, encoding, hashing, embedding, normalization, summary statistics, or other derivation.

Every derived field must declare its parents and inherit the strictest applicable visibility restriction unless a prospectively approved contract explicitly authorizes a lawful declassification.

Diagnostics must never silently become training/model features.

## 5. Synthetic oracle unblinding event

Synthetic oracle truth remains sealed until ordinary qualification outputs are frozen for the run.

Required sequence:

1. protocol, thresholds, diagnostics, failure logic, and representation request frozen;
2. normal pipeline executes;
3. ordinary outputs/readouts and provenance receipt frozen;
4. explicit `ORACLE_UNBLINDED` event recorded under the same run identity;
5. oracle evaluator consumes frozen outputs plus oracle truth;
6. oracle findings are appended as downstream evaluation artifacts only.

Any change to thresholds, diagnostics, representation fitting, preprocessing, target construction, or model behavior after unblinding invalidates that synthetic challenge as prospective deciding evidence and reclassifies it as development/calibration evidence.

## 6. Negative controls are first-class required arms

Every serious synthetic qualification run must prospectively include, where scientifically applicable:

- clean negative control;
- technical/operator shortcut control;
- planted recoverable biological control;
- planted inaccessible/private-state control;
- query-leak control.

Additional controls may be required by the QualificationProtocol. Missing required controls make the run incomplete rather than PASS.

The purpose is to verify that the qualification machinery distinguishes recoverable signal, technical shortcut, impossible private state, and leakage—not merely that optimization/loss behaves.

## 7. Three independent authorities

The architecture formally separates three authorities:

### A. Scientific experiment authority

Defines what question/configuration may be evaluated, including protocol, representation candidate, target/evidence construction, visibility/firewall rules, split/resampling structure, estimand status, thresholds status, and claim ceiling.

### B. Mutation authority

Defines whether parameter/EMA mutation is permitted for this run and under which guarded runtime/checkpoint mechanics.

Default remains `MUTATION_NOT_AUTHORIZED` / zero-update.

### C. Claim authority

Defines what conclusions may be reported from the resulting evidence under the claim ladder.

Passing scientific experiment validation does not grant mutation authority. Passing mutation mechanics does not grant a stronger scientific claim. Passing a synthetic challenge does not grant real biological claim authority.

Each authority has an independent version/digest and explicit status in the end-to-end receipt.

## 8. Terminal reconciliation receipt for PR #221/#222 convergence

The runtime successor may not be declared canonical until it emits a terminal reconciliation receipt containing at minimum:

- donor PR #221 exact head;
- donor PR #222 exact head;
- successor branch and exact head;
- retained files/components/invariants from each donor;
- rejected/superseded components from each donor;
- historical mechanisms deliberately not imported;
- RED tests introduced during convergence and observed failing evidence;
- corresponding minimal repairs and observed GREEN evidence;
- real AdamW qualification result;
- AMP/GradScaler skipped-step qualification result;
- checkpoint completeness inventory;
- interrupt/resume equivalence result and equality/tolerance standard;
- historical-spillover audit result;
- independent-review result;
- exact CI/workflow runs;
- unresolved qualifications and limitations;
- explicit statement that #221 and #222 are no longer canonical after supersession;
- explicit confirmation `TRAINING=OFF`, `STAGE_A_EXECUTION=OFF`, `TEST=SEALED`, `MORABITO=PROTECTED`, `500K=NOT_AUTHORIZED`, `STAGE4=NOT_AUTHORIZED`.

After receipt acceptance, donor PRs must be marked/closed as superseded rather than left as competing almost-canonical paths.

## 9. Additional RED requirements introduced by this addendum

Before implementation may claim these safeguards, write RED tests for at least:

1. illegal lifecycle jump (e.g. `PREPARED -> EMA_APPLIED` without proven mutation);
2. optimizer success followed by checkpoint failure does not yield `VERIFIED`;
3. restart verification failure cannot mint a successful terminal receipt;
4. event from another `experiment_run_id` cannot attach to the current run;
5. lawful repacking preserves `batch_scientific_identity_digest`;
6. semantic mutation during packing changes/rejects the scientific identity;
7. derived `SPLIT_ONLY`/`ORACLE_ONLY` information cannot become model-visible;
8. oracle cannot unblind before ordinary outputs are frozen;
9. post-unblinding retuning reclassifies challenge evidence as development/calibration;
10. missing required negative-control arm fails the protocol;
11. mutation authority OFF blocks optimizer/EMA even when scientific experiment authority is valid;
12. successful mutation mechanics cannot elevate claim authority;
13. missing terminal reconciliation fields prevent runtime-successor canonicalization.

## 10. Closure principle

The architectural north star is:

> Freeze interfaces before implementations, keep oracle/evaluation information physically downstream of model-visible data, and require every future change to declare whether it changes science, mechanics, or both.

Addendum interpretation:

- interfaces include lifecycle state, identity, visibility, authority, and provenance;
- mechanics must fail closed under partial failure;
- synthetic truth may test the qualification assay but cannot feed back into the same prospective challenge;
- all conclusions remain bounded by explicit claim authority;
- TRAINING remains OFF until a separate prospective execution authority is explicitly approved.
