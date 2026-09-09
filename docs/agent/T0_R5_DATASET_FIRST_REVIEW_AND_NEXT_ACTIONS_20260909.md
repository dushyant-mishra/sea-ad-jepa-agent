# T0 R5 dataset-first review and next actions — 2026-09-09

Review target: `0f0076235b96691a04f56bc213f0280c68200e0c`

Parent R4 candidate: `b08d02f721636eeba43c8612f934e816deec5f05`

This document records the current external-review position after the R5 handoff and the user's instruction to build the best possible framework around the actual dataset, not around synthetic fixtures.

## Current disposition

`STOP_T0_R5_REAL_POPULATION_AUTHORITY_NOT_MATERIALIZED`

R5 is a substantial structural improvement over R4, but it is not a completed production authority. The decisive missing evidence is still the real 20,804-row population closure.

## What R5 improved

R5 correctly withdraws the R4 claim that the unsafe fabricated-vector `source_library` API had been structurally eliminated. The old caller-vector route is now a raising path, not a permissive proof path.

R5 also moves the design in the correct dataset-first direction:

1. `source_library` is no longer supposed to be proven from caller-supplied values.
2. A population-level raw-source authority is introduced.
3. Technical completeness requires population raw-source proof before using Q_DEPTH.
4. 35,076 projection positions are mandatory by default; small projections are fixture-only.
5. Closure-bound `rows` and `nnz` are meant to be reconciled on the production path.
6. A physical read plan is required rather than silently replaced with the logical root.
7. Estimability preflight root binds more than rank labels.
8. Downstream gates remain shut.

These are the right framework moves.

## What is still not done

The production B2 authority has not been materialized over the real population.

The pasted production attempt shows:

- membership digest authenticated;
- complete Phase2 manifest digest authenticated;
- 1,247 op31 metadata digests authenticated;
- 638,150 op31 metadata rows counted;
- source asset path present with byte count `32,978,570,763`;
- production execution then blocked by Claude Code permissions.

That is a PASS for input preflight, not a PASS for population authority closure.

## Dataset-first rule from here

Synthetic H5AD fixtures and three-row real-asset spot checks are allowed only for software attack and edge-case regression testing.

They do not count as framework progress unless they expose or fix a concrete bug.

Framework progress now means producing and replaying real artifacts from the frozen dataset:

```
real frozen source H5AD
+ real frozen B2 logical rows
+ real frozen Phase2 manifests and block payloads
+ real frozen B1 projection
=> immutable raw-source population authority
=> immutable technical-completeness authority
=> replay verification
```

## Master-list next actions

### A. Production B2 raw-source population authority

Goal: materialize the real 20,804-row raw-source population authority.

Required evidence:

- exactly `20,804` accepted logical rows processed;
- source SHA equals `e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79`;
- source byte count recorded as `32,978,570,763`;
- every logical index proven exactly once;
- no skipped logical index;
- no duplicate logical index;
- every proof binds `logical_index`, `expression_row`, `canonical_cell_id`, `donor_id`, `source_library`, `stored_values_in_row`;
- every source H5 row identity matches the logical row;
- every source-library value is computed from the authenticated `layers/UMIs` row;
- no pathology field is read, parsed, retained or emitted;
- final population raw-source root recorded.

### B. Production runner must be committed before execution

The next production run must not depend on a scratchpad-only script.

Commit a reproducible runner and verifier under `scripts/v4/`, for example:

- `scripts/v4/run_t0_b2_raw_source_population_authority_v1.py`
- `scripts/v4/verify_t0_b2_raw_source_population_authority_v1.py`

The runner should produce artifacts under `outputs/`, not under a temp Claude scratchpad.

### C. Permission-denied run is not closure

Claude's production execution was blocked by the Claude Code auto-mode classifier. This is not a data failure and not an authority failure, but it leaves the authority unmaterialized.

The next step is to run through an allowed execution path, after the runner is committed and reviewed.

### D. Replay before acceptance

After the raw-source population authority is produced, run an independent replay from disk.

Replay must verify:

- stored population root == recomputed population root == externally recorded expected root;
- row count == 20,804;
- all proof rows match the logical authority;
- source digest and byte count match recorded values;
- package root matches the file bytes;
- no pathology columns appear in emitted artifacts;
- `real_execution_ready` remains false.

### E. Technical completeness production authority

Only after A-D are complete, materialize technical completeness using:

- authenticated B2 closure;
- verified physical read plan;
- real B1 35,076 projection;
- real counts payloads;
- real population raw-source authority.

Required evidence:

- every consumed counts payload digest matches the logical row's `counts_sha256`;
- every consumed block `rows` and `nnz` matches closure-bound geometry;
- Q_DEPTH uses proven raw-source library values, not stored logical metadata;
- Q_DETECT uses the 35,076 B1 projection, not 28,061 scoring features and not 41,238 address-space width;
- donor summaries replay from disk;
- parent contract root replays;
- all 46 candidate donors accounted for or a STOP explains the mismatch.

### F. Do not start eligible-donor construction yet

Eligible-donor construction remains blocked until raw-source population authority and technical completeness authority both materialize and replay cleanly.

Keep in force:

```
DONOR_ROLE_GATE_SHUT
NUMERIC_CONFIRMATION_AT8_NOT_ACCESSED
real_execution_ready=False
NO_ELIGIBLE_DONOR_CONSTRUCTION
```

## Review attacks still open

Before accepting any R5/R6 candidate, attack these specifically:

1. Can any production caller still reach `_build_rows_from_values` or `_build_authority_from_values` with detached values?
2. Can a caller-built `AuthenticatedSource` or handle-like object still enter a public proof path?
3. Can a population authority with correct cardinality but wrong rows pass?
4. Does the physical plan root actually determine which counts files are read, or is it only recorded beside a separate caller-supplied payload map?
5. Does replay recompute roots from artifact bytes, or trust an in-memory object produced by the same run?
6. Are all large outputs named by exact path, size, and SHA-256?

## Acceptance criterion for this phase

This phase is complete only when a real production artifact exists and replay passes:

```
20,804 real rows proven
stored roots == recomputed roots == externally expected roots
package bytes hashed and immutable
no pathology numeric access
no eligible donor construction
```

Until then, the framework is structurally improved but not yet dataset-proven.
