# JEPA shared qualification implementation takeover — 2026-10-06

Status: `PLAN_READY__IMPLEMENTATION_NOT_STARTED__TRAINING_OFF`

## Exact current planning checkpoint

Handoff branch: `handoff/jepa-20261005-final-chat-custody-downstream-audit`

Implementation plan commit:

`49214e20a7971d90a8259d1ddee49ac94b519360`

Plan:

`docs/superpowers/plans/2026-10-06-shared-qualification-interface-implementation-plan.md`

Binding design records already present on this handoff branch include:

- `docs/agent/JEPA_SHARED_QUALIFICATION_PIPELINE_DESIGN_20261006.md`
- `docs/agent/JEPA_SHARED_QUALIFICATION_PIPELINE_FINAL_SAFEGUARDS_20261006.md`
- the subsequent lifecycle correction separating zero-update and mutation-enabled state paths;
- `docs/agent/JEPA_REAL_DATA_LANE_INDEPENDENT_RED_TEAM_20261006.md`;
- `docs/agent/JEPA_RUNTIME_CONVERGENCE_AUDIT_ADDENDUM_20261006.md`;
- `docs/agent/JEPA_PR221_PR222_RUNTIME_CONVERGENCE_CONTRACT_20261006.md`.

## Why implementation is sequenced this way

The shared scientific interface must be frozen and machine-tested before final #221/#222 runtime convergence, because the runtime must execute scientific contracts rather than invent or preselect them.

The first implementation slice therefore builds only:

- exact-governance-bound `QualificationProtocolV1`;
- visibility/firewall declarations;
- feature-identity receipt;
- immutable batch scientific identity separate from compute packing;
- three independent authorities;
- mode-aware run lifecycle and monotonic run identity;
- machine-readable transitive q-safety policy;
- required synthetic negative-control roster;
- one-way synthetic oracle unblinding;
- end-to-end provenance receipt;
- a zero-update qualification skeleton.

It explicitly does **not** implement:

- optimizer/EMA mutation;
- PR #221/#222 convergence;
- real PyTorch/GradScaler qualification;
- V77 CSR adapter;
- real-RNA adapter;
- Stage-A execution;
- target/representation/estimand/threshold selection.

## Downstream plan order

After the shared-interface plan is reviewed and implemented with RED→GREEN evidence:

1. write/execute the #221/#222 runtime convergence plan against the frozen interface;
2. physically qualify actual AdamW, GradScaler skipped-step behavior, optimizer/EMA reachability, persisted checkpoint completeness and deterministic resume;
3. emit the terminal runtime reconciliation receipt and supersede/close both donor PRs once independently reviewed;
4. write/execute the V77/S127 adapter/challenge plan using the same `QualificationBatchV1`/`QualificationProtocolV1` interface;
5. run zero-update synthetic pipeline-validity qualification first;
6. only under separate mutation authority, run any bounded synthetic mutation rehearsal;
7. future real-data Stage-A work uses the same middle pipeline through a separately authenticated real adapter and separately approved scientific/execution authority.

## Audit rule

Every substantive milestone must receive an iterative self-audit before progression:

- exact SHA and test evidence;
- historical-spillover scan;
- scientific/runtime lane-separation check;
- protected-data/training-state check;
- negative finding preservation;
- handoff update.

Do not inherit earlier GREEN evidence from superseded designs as current qualification.

## Hard boundaries

`TRAINING=OFF`

`STAGE_A_EXECUTION=OFF`

`MULTIMODAL_TRAINING=OFF`

`500K=NOT_AUTHORIZED`

`STAGE4=NOT_AUTHORIZED`

`TEST=SEALED`

`MORABITO=PROTECTED`

No production target winner, representation winner, estimand, biological-dimensionality claim, or deciding real-data numeric threshold is selected.

## Immediate takeover action

Review `docs/superpowers/plans/2026-10-06-shared-qualification-interface-implementation-plan.md` against the binding design and final safeguards. After explicit plan approval, execute the plan RED-first on an isolated successor branch/worktree. Do not start by editing #221 or #222 runtime code.
