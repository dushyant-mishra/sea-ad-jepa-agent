# v4A Defective-Training Lineage Audit — 2026-09-06

Status: `PROVENANCE_INVENTORY_COMPLETE__NOT_AN_INVALIDATION`
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

## `DEPENDENCY_UNCLEAR__REVIEW_REQUIRED` (all resolved below)

Originally listed rather than guessed; every item is now classified in the
resolution section at the end of this document:

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

---

# Resolution of the three `DEPENDENCY_UNCLEAR__REVIEW_REQUIRED` items — 2026-09-06

All three are now classified. **Zero `DEPENDENCY_UNCLEAR` items remain.**

## The principle that decided them

**Forward-only execution is not exculpatory by itself.** A run that performs no
optimizer step still inherits the defect if it loads post-`u0` weights. What
matters is which weights a conclusion depends on, not whether the script trained.

Conversely, referencing a defective checkpoint does not by itself contaminate a
conclusion. A script may hash a checkpoint purely to authenticate provenance and
never load a tensor from it.

The discriminating question is therefore: **does the conclusion depend on the
values of post-`u0` weights?** Three outcomes follow.

## 1. Phase-2 capacity and materialisation audit — `UNAFFECTED_STATIC_OR_U0`

`scripts/v4/audit_full104_phase2_capacity_and_materialization.py` contains
**zero** occurrences of `torch.load` or `load_state_dict`. It never loads a
tensor. It reads `t1_checkpoint_u0205.pt` only to compare its SHA against
`checkpoint_manifest.json` and abort on mismatch.

Its actual method is source inspection: `ast.parse` over `ipb_jepa.py`,
`gene_tokenizer.py` and `full104_model_components_v2.py`, plus interface traces
asserting `width: int = 160`, `heads: int = 4`, `blocks: int = 6`,
`gene_states`, `cell_state`, and the parameterised head signatures. Every
recorded fact — the 41,238 addresses, the 160 token width, the 48-wide query
identity, the serialization limits, the
`candidate_rank_320_classification` — is a property of source code.

`PASS_CAPACITY_INTERFACES_AUTHENTICATED` therefore **survives unchanged**. The
u205 reference is authentication, not dependence.

## 2. Authenticated T1 feature export — `TRAINING_MECHANICS_DEFECT_INHERITED`

`scripts/v4/export_authenticated_t1_features_readonly.py:24` calls
`online.load_state_dict(state['online_encoder'])` and
`target.load_state_dict(state['target_encoder'])` from `t1_checkpoint_u0205.pt`,
then computes features.

Its own audit records `neural_updates: 0` and
`firewall: existing frozen T1 evaluation only`. Both are true and neither
helps: the forward pass is clean, the **weights** are not. This is the clearest
instance of the principle above.

- `u205_features` and `FOUNDATION_AUTHENTICATED_T1_FEATURE_EXPORT.json` →
  `TRAINING_MECHANICS_DEFECT_INHERITED`
- the `u0_features_sha256` recorded in the same file →
  `UNAFFECTED_STATIC_OR_U0`

## 3. Foundation calibration bundle — script unaffected, bundle needs a label

`scripts/v4/package_foundation_calibration_bundle.py` copies files and records
hashes. It loads no weights and draws no conclusion, so the packaging act is
`UNAFFECTED_STATIC_OR_U0`.

But lines 73–74 place **both** checkpoints inside the bundle:

```
checkpoints/t1_checkpoint_u0000.pt   authenticated u0 checkpoint
checkpoints/t1_checkpoint_u0205.pt   authenticated u205 checkpoint including EMA
```

So `exports/foundation_calibration_bundle_20260824/` ships a defect-inherited
artifact described only as "authenticated". Authenticated is accurate — the
bytes are what they claim to be — and is not the same as mechanically sound.

**Action required:** the bundle should carry a label marking
`t1_checkpoint_u0205.pt`, and any bundle content derived from it, as
`TRAINING_MECHANICS_DEFECT_INHERITED`. Not done here: the bundle is a historical
export and relabelling it is a governance decision, not an implementation one.

## The eleven referencing documents

| document | class |
|---|---|
| `t1_run/checkpoint_manifest.json` | `UNAFFECTED` — provenance record *about* checkpoints |
| `foundation_calibration_bundle_20260824/checkpoints/checkpoint_manifest.json` | `UNAFFECTED` — copy of the same record |
| `foundation_calibration_bundle_20260824/BUNDLE_SHA256_MANIFEST.csv` | `UNAFFECTED` — hash manifest |
| `FOUNDATION_AUTHENTICATED_T1_FEATURE_EXPORT.json` | **`INHERITED`** for the u205 half, unaffected for the u0 half |
| `prod41k_t1_contextual_recovery_v1/` — 7 files | **`SPLIT`**, see below |

A manifest that records the SHA of a defective checkpoint is not itself
defective. It is a true statement about bytes, and it is the mechanism by which
the defect can be traced at all.

### The T1 contextual recovery group splits, like the atlas

`prod41k_t1_recovery_query_self.py:92` runs `for u in (0, 205)`, and the outputs
carry an explicit `update` column — `T1_RECOVERY_ORIGINAL_REPRODUCTION.csv`
opens `update,artifact,rows,columns,max_abs_numeric_difference,…` with rows at
`0` and at `205`.

- rows and records at `update == 0` → `UNAFFECTED_STATIC_OR_U0`
- rows and records at `update == 205` → `TRAINING_MECHANICS_DEFECT_INHERITED`
- any u205-minus-u0 contrast → `TRAINING_MECHANICS_DEFECT_INHERITED`

This is the second artifact family found to split on an update column, after
`FOUNDATION_TEACHER_SHORTCUT_ATLAS`. Both were built to compare an untrained
baseline against a trained endpoint, which is exactly the shape that makes half
the file survive.

## Summary of the completed inventory

| class | scope |
|---|---|
| `UNAFFECTED_STATIC_OR_U0` | `u0000`; the entire current F1 lane; the phase-2 capacity audit; all checkpoint and bundle manifests; the packaging script; every `update == 0` row |
| `TRAINING_MECHANICS_DEFECT_INHERITED` | `u0010`–`u0205`; the u205 feature export; every `update == 205` row; every u205-minus-u0 delta, including the rare-endpoint degradation figures |
| `DEPENDENCY_UNCLEAR__REVIEW_REQUIRED` | **none remaining** |

Nothing was retrained, no result was discarded, and no forward-only, `u0` or
static conclusion was reclassified merely for proximity to a defective branch.

One governance item is left open deliberately: relabelling the historical
`foundation_calibration_bundle_20260824` export.
