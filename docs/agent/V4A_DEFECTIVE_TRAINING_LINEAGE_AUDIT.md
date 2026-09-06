# v4A Defective-Training Lineage Audit — 2026-09-06

Status: `PROVENANCE_INVENTORY__NOT_AN_INVALIDATION`
Implementing agent: `CLAUDE_CODE`. Not self-certified.

This is an inventory of which historical work executed through the C2 defect
condition. It does **not** invalidate results, and nothing was retrained.

The C2 causal condition is `.backward()` executed inside an enabled fp16
`torch.autocast` region, established for the historical 128/8 path.

## Method

Grep cannot answer this. A file can contain both an autocast block and a
backward call without the backward being inside it, and a backward inside a
nested `autocast(enabled=False)` is shielded. The scan walks the AST of every
Python file and reports, per backward call, the innermost governing autocast
state.

One correction was needed during the audit and is recorded because it changed
the answer completely. `run_update` writes `enabled=device.type == "cuda"`, a
runtime expression rather than a constant. The first scan classified that as
"dynamic" and grouped it with shielded, returning **zero** affected files. A
runtime-enabled flag that is true on every GPU run *is* the defect condition.
After reclassification the true count appeared.

## Scope of the defect

```
python files scanned                                    4729
backward inside an enabled/runtime-enabled autocast         7   across 7 paths
backward inside an explicitly disabled autocast             0
backward outside any autocast                             356
unparseable                                                 1
```

The 7 hits are **one implementation**: `run_update` in
`scripts/v4/stage81a3_prod41k_engineering_smoke.py`. The other six are worktree
copies and one export bundle of the same function:

```
scripts/v4/stage81a3_prod41k_engineering_smoke.py                              (canonical)
exports/foundation_calibration_bundle_20260824/code/...engineering_smoke.py    (bundle copy)
outputs/.worktrees/{f1_evidence_trend_repair, f1_real_production_executor,
                    f1_real_reader_forward_preflight, f1r,
                    github-review-mirror-sync-20260902}/scripts/v4/...          (worktree copies)
```

**No other training loop in the repository executes backward under autocast.**
The 356 backward calls outside any autocast include every probe, reader and
diagnostic trainer; none inherits the condition.

`results/stage75e_container/stage76_runtime_check.py` does not parse and was not
classified. It is not a training path, but it is recorded as unscanned rather
than silently assumed clean.

## Executions through the defective implementation

| caller | role |
|---|---|
| `stage81a3_prod41k_teacher_t1.py:789` | **T1 production training, 205 updates** |
| `stage81a3_prod41k_engineering_smoke.py` (4 sites) | its own smoke and branch-A/branch-B tests |
| `verify_prod41k_t1_u1_parity.py:62` | u1 parity verification |

`prod41k_t1_recovery_query_self.py` defines a *different* local `run_update` with
an unrelated signature. It is not the defective function and is out of scope.

## Checkpoint classification

`t1_checkpoint_u0000.pt` is captured at `global_update_step = 0`, before any
optimizer step. It is the model at initialisation.

| checkpoint | classification |
|---|---|
| `u0000` sha256 `19fb0c25…` | `UNAFFECTED_STATIC_OR_U0` |
| `u0010`, `u0025`, `u0050`, `u0100`, `u0200`, `u0205` | `TRAINING_MECHANICS_DEFECT_INHERITED` |

The inherited classification is not an inference. Every one of those six
checkpoints independently shows the signature directly: 123 optimizer states, of
which exactly 48 hold both Adam moments at zero, mapping exactly to 12 each of
`attention_norm`, `attention.query`, `attention.key` and `attention.value`, with
step counters advancing normally.

## Downstream consumers

Five scripts read post-`u0` checkpoints:

```
scripts/v4/adjudicate_prod41k_teacher_t1.py
scripts/v4/export_authenticated_t1_features_readonly.py
scripts/v4/foundation_teacher_shortcut_analysis.py
scripts/v4/package_foundation_calibration_bundle.py
scripts/v4/audit_full104_phase2_capacity_and_materialization.py
```

Eleven documents, results or exports reference trained checkpoints by name.

### `FOUNDATION_TEACHER_SHORTCUT_ATLAS` splits, and the split matters

`foundation_teacher_shortcut_analysis.py:41` iterates
`[('u0', u0), ('u205', u205)]` and then computes `u205_minus_u0` deltas. So the
atlas contains both classes of row in one file:

| rows | classification |
|---|---|
| `checkpoint == u0` | `UNAFFECTED_STATIC_OR_U0` |
| `checkpoint == u205` | `TRAINING_MECHANICS_DEFECT_INHERITED` |
| `u205_minus_u0` deltas | `TRAINING_MECHANICS_DEFECT_INHERITED` |

This resolves a specific open dispute. The Historian's objection to the SEA-AD
regional axis rested on **0.7551 operator balanced accuracy from `rich_H` at u0,
untrained**. That is a `u0` row. It is `UNAFFECTED_STATIC_OR_U0` and **survives
this audit unchanged.** The concern it raises about operator decodability does
not depend on defectively trained weights.

Conversely, any claim of the form "training changed X" that reads a
`u205_minus_u0` delta is measuring a defectively trained endpoint against a clean
one, and is `TRAINING_MECHANICS_DEFECT_INHERITED`. That includes the rare-endpoint
degradation figures.

## The current F1 lane

`UNAFFECTED_STATIC_OR_U0`.

The F1 successor is forward-only on frozen `u0`. Scripts in that lane
(`run_contextual_target_v1_f0.py`,
`audit_contextual_target_f1_reader_forward_freeze_v1.py`,
`benchmark_contextual_target_f1_repair_v1.py`,
`build_full104_parallel_reuse_delta.py`) bind `u0000` / `19fb0c25…` and do not
read post-`u0` weights. C2 trainability and F1-A target validity remain separate
claim layers, and no F1 authority currently depends on defectively trained
post-`u0` weights.

**Nothing here blocks the F1 contract freeze.** Had a dependency been found it
would have been flagged immediately; none was.

## `DEPENDENCY_UNCLEAR__REVIEW_REQUIRED`

Not yet resolved, and listed rather than guessed:

- `package_foundation_calibration_bundle.py` references both `u0000` and trained
  checkpoints. Which bundle conclusions rest on which has not been traced
  per-artifact.
- `audit_full104_phase2_capacity_and_materialization.py` and
  `export_authenticated_t1_features_readonly.py` read trained checkpoints, but
  whether their conclusions are about **weights** or about **interface/capacity
  structure** has not been established. A capacity or materialisation claim may
  be structural and therefore unaffected.
- The eleven referencing documents have not been read individually.

## What this audit does not do

It does not retrain anything, does not discard any result, and does not
reclassify a forward-only, `u0` or static conclusion merely for living near a
defective training branch. `adjudicate_prod41k_teacher_t1.py` produced the
historical finding that T1 did not qualify biology at u205; that outcome remains
historical fact and is unchanged by this inventory.
