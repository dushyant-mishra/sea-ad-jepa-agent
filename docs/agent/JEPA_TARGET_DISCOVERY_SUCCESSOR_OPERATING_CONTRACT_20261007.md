# JEPA Target Discovery Successor Operating Contract — 2026-10-07

Status: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__TRAINING_OFF__REAL_RNA_STAGE_A_NOT_AUTHORIZED__STAGE4_NOT_AUTHORIZED`

## Purpose

This is the operating contract for the next agent taking over target discovery and feature-axis recovery. It supplements the detailed handoff and exists to prevent three failure modes: redoing already-qualified Macha/V77 repairs, mistaking historical decoder work for a full 41K rebuild, and crossing the real-RNA authorization boundary while trying to close the remaining feature-axis gap.

## Mandatory start order

Read first:

1. `docs/agent/JEPA_TARGET_DISCOVERY_PHYSICAL_FEATURE_AXIS_NEW_CHAT_HANDOFF_20261007.md`
2. `docs/agent/JEPA_TARGET_DISCOVERY_RICH_TEACHER_TAKEOVER_HANDOFF_20261007.md`
3. `docs/agent/JEPA_HVS_SEAAD_REPLAY_PLAN_MACHA_SCOPE_CORRECTION_20261007.md`
4. target-recovery custody roots and archive maps under `docs/agent/archive/chat_runtime_20261007*`
5. historical decoder lineage around commits `b2231e9e`, `5a217f92`, `b642dce6`, `9d30ef62`, `490d0ffd`, `778706f1`, and `91b9725e`

Do not infer absence of historical decoder/rematerialization work from the current branch tree or filenames alone. The decoder lineage lives on older audit/Claude branches and may not be present in the current handoff tree.

## Controlling feature-axis facts

- `b2231e9e`: retracted affected gene-level results.
- `5a217f92`: established that counts were intact and the gene axis was wrong.
- `b642dce6`: identified the root cause and supplied a verified closed-form FULL104 Level-4 decoder.
- Root cause: `source_feature_index` in `HVS_COMMON` / `SEA_AD_COMMON` followed harmonized Ensembl-ID order while the H5AD physical `var` axis followed genomic order; the former was incorrectly applied as if it were the latter.
- `b642dce6` verified two HVS objects and three SEA-AD objects cell-by-cell against source, with SEA-AD ambiguous columns dropped rather than guessed.
- `9d30ef62`: NPH52 does not share this defect.
- `490d0ffd`: the historical 50K discovery HVS/SEA-AD materializer does share this defect.
- `778706f1`: all six count-producing paths were audited; the affected paths are the HVS/SEA-AD `_COMMON` consumers, while the four NPH52 paths were separately verified for this defect.
- `91b9725e`: corrected myeloid panels were produced in the verified narrow scope.

The key distinction is mandatory:

**verified decoder/root-cause repair != validated general 41,238-address expression reader/rematerialization**.

The corrected historical artifact covers only the verified narrow scope described by the decoder lineage. No full 41K physical-column rebuild has yet been established in the controlling handoff.

## Macha/V77 boundary

Do not redo Macha's repaired synthetic support/observer work. In particular, preserve:

- S146 source-order repair;
- S147 structural-attrition repair;
- old-world refusal;
- name-mapped source/operator handling;
- adapter and q-safety repairs;
- spillover and ZERO_UPDATE work.

Those fixes authenticate/repair synthetic-world and observation-pipeline semantics. They do not themselves prove real H5AD physical feature-column identity.

## Historical archaeology procedure

Before proposing any implementation:

1. Search commit history and inherited branches, not only the current tree, for any post-`b642dce6` generalization of the decoder or any full corrected 50K HVS/SEA-AD materialization.
2. Search by content as well as filenames. Useful terms include `source_feature_index`, `var`, `_index`, `gene_ids`, `feature_name`, `feature_order_sha256`, `feature_universe`, `physical column`, `genomic order`, `Ensembl order`, `FULL104_LEVEL4_COLUMN_DECODER`, and `rematerial`.
3. Inspect exact receipts/manifests and code. A branch or commit message saying "fixed" is not sufficient.
4. For any claimed general reader, prove the chain:
   authenticated source bytes -> exact matrix object -> exact physical ordered feature vector -> identity at physical column -> canonical molecular address -> reader output.
5. Check width, duplicate semantics, unresolved identifiers, collisions, and ambiguity handling. Rank equality or a feature-order checksum alone is insufficient.
6. Treat HVS and SEA-AD independently. Do not import a SEA-AD feature-order authority into HVS or vice versa.
7. Treat NPH52 as a separate lineage. `not affected by this defect` must not be silently promoted to universal qualification for every other property.

## Stop/go rule

If a complete, matrix-specific, authenticated full 50K physical-column decoder/rematerialization already exists in history, stop and reconcile it into the handoff. Do not reimplement it.

If no such artifact exists, the next permissible deliverable under the current mandate is a design/qualification plan only. Do not read or rematerialize real RNA without explicit authorization from the real-data lane.

## Target-discovery scientific contract

The project objective is a cellular molecular world-state predictor, not hidden-gene imputation.

Rich teacher evidence remains desirable. But a deterministic partial-RNA student cannot generally reproduce teacher-private realized evidence it does not observe. Under squared error the student can, in general, learn the conditional expectation of the teacher representation given permitted student context, not the realized teacher-private component.

Therefore:

- deterministic student loss should apply only to demonstrated recoverable/shared components;
- teacher-private information requires uncertainty/probabilistic treatment, abstention, separate objectives, or exclusion from deterministic point loss;
- biological-evidence uncertainty and sequencing/measurement uncertainty must remain distinct;
- historical `D_shared` / `D_private` semantics must not be silently redefined as RNA-predictable / teacher-private without new evidence.

## Historical target-discovery status

- `TARGET_WINNER = NONE`.
- `REPRESENTATION_WINNER = NONE`.
- TD55: do not promote.
- TD56-TD58: evidence for relational/shared predictable structure only; not a target winner.
- TD57C primary failure remains a failure; later diagnostics cannot post-hoc rescue it.
- Any HVS/SEA-AD or mixed-source decision-bearing result tracing to the defective historical 50K materialization requires corrected interpretation/replay before it can support a cross-source biological conclusion.
- NPH-only results may remain informative but cannot independently restore a cross-source conclusion.
- Corrected replay must preserve the original hypothesis, thresholds, and decision rule. Outcomes are to be classified prospectively as: survives unchanged; quantitative change but same decision; fails; cannot replay.

## Replay discipline

Do not rerun the whole TD34-TD58 program indiscriminately.

After a corrected substrate is qualified, first compute old-vs-corrected deltas:

- changed addresses;
- changed nonzero entries;
- per-gene and per-cell disagreement;
- affected source/operator distributions;
- whether each historical panel/derived state intersected changed values.

Replay only analyses whose decision-bearing inputs intersect the corrected values. Preserve original artifacts unchanged under their historical hashes.

## Authorization boundaries

Unless a newer explicit authority supersedes this contract:

- training: OFF;
- real-RNA Stage A execution: NOT AUTHORIZED;
- Stage 4: NOT AUTHORIZED;
- 500K execution: NOT AUTHORIZED;
- TEST/Morabito/pathology: sealed/protected;
- no new target winner;
- no new representation winner.

A real-RNA 41K rebuild requires explicit authorization from the real-data lane. Repository archaeology, source-code audit, receipt audit, and design work remain permissible.

## Evidence language

Use `supports`, `promising lead`, `not yet qualified`, `replay-required`, `not presently gene-value-qualified`, or `not invalidated by this defect` unless exact qualification evidence exists.

Do not use `verified` or `qualified` for a matrix-wide claim unless physical-column identity has been proven end-to-end for the exact matrix and scope claimed.

## Immediate next action for successor

Continue historical archaeology from the decoder lineage, including older `audit/v29-*`, later V48-V59, and inherited `claude/*` branches. Determine whether any artifact generalized the verified `b642dce6` decoder from its narrow FULL104/myeloid scope into a complete corrected 50K HVS/SEA-AD expression reader. Record positive or negative evidence with exact commit/file/receipt references. Only after that determination should any repair design be drafted.
