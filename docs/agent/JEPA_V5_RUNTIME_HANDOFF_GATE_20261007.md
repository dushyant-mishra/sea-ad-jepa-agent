# V5 canonical runtime handoff gate — 2026-10-07

Status: **PR #224 MECHANICS GREEN; SHARED-INTERFACE RESTACK / JOINED ZERO-UPDATE AUDIT STILL REQUIRED**

Accepted runtime head at this checkpoint:

`1354ff6e1ef04cf81f478bb8b2ab3a0f562231b8`

GitHub Actions at that exact head:

- `v5-inactive-runtime-step-guard`: PASS
- `v64-runtime-core-reconciliation`: PASS
- `Current authority surface guard`: PASS

This is a non-authorizing mechanics checkpoint. It does not authorize training, Stage A, real-RNA execution, TEST, Morabito, 500K, Stage 4, a target, a representation, an estimand, a weighting rule, a deciding threshold, an uncertainty model, or a production EMA timescale.

## Architecture lineage accepted

The keyed V5 student encoder remains byte-identical through the later V47/V48/V63 scientific lanes audited here. V4 IPB/predictor mechanics and the gene tokenizer likewise survive unchanged through V63. Later V43+ work changes teacher-target science/identifiability questions, not these low-level mechanics.

The teacher structural mechanism is therefore accepted only as `deepcopy(student encoder) + guarded EMA`. This says nothing about the scientific meaning of the teacher target.

## Rich-teacher / partial-student boundary

The target-discovery lineage at `6c576cec1aa4a8fdab863fae64eacced7945b65b` restores the project invariant:

`RICH_TEACHER_DESIRABLE__FULL_RICH_STATE_NOT_GENERALLY_IDENTIFIABLE_FROM_PARTIAL_RNA`

The deterministic teacher-block loss inside `inactive_update_reference.py` is therefore classified only as:

`MECHANICS_FIXTURE_ONLY__NOT_TARGET_AUTHORITY`

The runtime explicitly does **not** authorize full realized rich-teacher state matching from partial RNA. Scientific qualification owns the decomposition among shared/RNA-predictable state, teacher-private evidence, biological uncertainty/distributional prediction, and abstention semantics. `runtime_target_semantics_boundary_v1.py` fail-closes target/uncertainty/Stage-A/training authority.

## EMA mechanics and authority

Historical fixed `.996` is V3/test history only. It is not current V5 authority. A recovered candidate 16,249-successful-presentation half-life is also not frozen authority.

Current authenticated mechanics are presentation-normalized:

- presentation unit: `SUCCESSFUL_BASE_CELL_PRESENTATIONS`;
- scalar momentum is derived per completed update from `presentations_this_update` and an explicitly supplied rehearsal half-life;
- no production half-life is selected;
- completed EMA proof binds parent checkpoint, EMA configuration identity, guard receipt, presentations in the update, and parent/child teacher-age arithmetic;
- canonical persisted continuation is `ema_persisted_continuation_v2.py`;
- restart rejects EMA configuration drift.

The older dictionary-style EMA persistence route is retired from the canonical public surface. Noninitial direct issuance is refused; continuation must use V2.

## Wrapper/private implementation self-audit

A safe-edit wrapper refactor was introduced after an earlier partial-file replacement accidentally truncated a checkpoint implementation. The audited implementation blobs are retained under private module names, while small public wrappers define the canonical API.

This refactor was itself attacked before acceptance:

1. the private implementation blobs are included in `CANONICAL_RUNTIME_SOURCE_FILES`;
2. the public wrappers themselves are included in runtime provenance;
3. `v5/__init__.py`, which enforces the private-import gate, is included in runtime provenance;
4. all three are watched by focused CI;
5. fresh-process direct imports of both private implementations are refused;
6. the canonical wrappers open a one-import permit only while loading their implementation and revoke it immediately;
7. the public EMA surface does not expose the retired dictionary persistence function;
8. no duplicate runtime-source entries are allowed.

The import gate changes no model numerics and carries no execution/training authority.

Process note: one orphan no-op Git commit object (`e09d9f28f0a4a9c70da036ba9aa49655c05c0462`) was accidentally created during low-level Git staging, but the branch ref was never moved to it. A separate attempted write to a nonexistent branch also failed before changing repository state. Both are recorded here rather than hidden.

## Source-row / value provenance invariant

Two historical defects remain mandatory adversarial constraints.

### TD23 reset-row alias

B-side `sample_row` reset to local 0–24,999 while the physical discovery matrix used preserved global rows. The aliased path reproduced an apparent dependency near 0.39; correct global-row addressing gave about 0.0063. Older B-side analyses without proven row binding are `ROW_BINDING_UNVERIFIED`.

### September-8 source-row/value authority repair

Authentic identifiers and payload digests were not enough. The repaired contract requires source-row identity, logical cell/donor identity, physical source asset/slot, block-local row, and the exact consumed values to be coupled. Authenticating one payload while validating an independently supplied vector is not authority.

Standing invariant:

**coordinates, logical identity, authenticated payload bytes, and consumed expression values are one inseparable proof chain.**

The joined V77/#223/runtime audit must attack global/local row swaps, reset-index substitution, correct digest/wrong row, correct metadata/wrong values, and correct logical row/wrong physical location.

## Accepted mechanical properties at this checkpoint

- one canonical guarded V5 mutation path;
- actual AdamW mechanics;
- AMP unscale before gradient validation;
- physical GradScaler skip detection;
- optimizer completion before EMA;
- teacher cannot advance after a rejected/incomplete optimizer step;
- presentation-normalized EMA;
- completed EMA configuration/teacher-age proof;
- online/predictor/teacher/optimizer/GradScaler/cursor checkpoint state;
- deterministic bounded AMP interruption/reload;
- physical checkpoint write + SHA-256 verification before deserialization + reload/revalidation;
- transitive runtime provenance including wrappers/private implementations, geometry, keyed RNG/dropout, JEPA mechanics, tokenizer and EMA mechanics;
- runtime target-semantics neutrality;
- historical competing optimizer guard and generic donor rehearsal path retired.

## Remaining handoff gates

PR #224 mechanics are GREEN, but Macha does not yet receive mutation authority. The remaining sequence is:

1. restack PR #223 onto this exact accepted #224 runtime lineage without overwriting newer runtime files;
2. rerun the shared-interface/governance and V5 integration suites;
3. require only the strongest V2 physical runtime proof for mutation-proof promotion; historical V1 remains diagnostic only;
4. execute the actual V77 adapter + shared interface + canonical runtime path in `ZERO_UPDATE` mode to prove q-safety physically rather than from policy metadata;
5. run the coordinate/value-coupling attacks at that join;
6. run a final bypass/historical-spillover audit;
7. only then hand Macha an exact reviewed SHA for a bounded **synthetic** mutation rehearsal.

Hard boundaries remain:

`TRAINING=OFF`, `STAGE_A_EXECUTION=OFF`, `MULTIMODAL_TRAINING=OFF`, `500K=NOT_AUTHORIZED`, `STAGE4=NOT_AUTHORIZED`, `TEST=SEALED`, `MORABITO=PROTECTED`.
