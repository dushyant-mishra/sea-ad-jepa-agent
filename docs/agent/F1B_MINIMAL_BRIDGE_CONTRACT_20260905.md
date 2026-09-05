# F1-B Minimal Mechanism Bridge — Prospective Contract

Date: 2026-09-05
Status: `FROZEN_PRE_RESULT_IMPLEMENTATION_CONTRACT`

This contract governs implementation and synthetic validation of the F1-B minimal
mechanism bridge. It does **not** authorize a real-data run. Real mode must fail closed
with `STOP_F1B_REAL_RUN_NOT_EXTERNALLY_AUTHORIZED` until a separately reviewed launch
authority is supplied. This implementation task must not create such an authority.

## 1. Question

F1 is forward-only on frozen `u0` weights and is therefore **invariant to every property
of the training path**. It cannot distinguish a working optimizer from a severed one. F1-B
is the missing bridge:

> Can the planned production mechanism actually learn a query-local contextual target
> without routing collapse and without destroying rare/innovation biology?

F1-B is a **mechanism qualification**, not a biological benchmark and not a target
selection sweep. It cannot qualify a target, cannot promote a candidate, and cannot
substitute for F1-A.

## 2. Scope: the minimal bridge

Qualified components, and nothing else:

| Component | Source | Authority |
|---|---|---|
| Encoder | `IPBEncoder` | `src/sea_ad_jepa/v4/ipb_jepa.py` |
| Tokenizer | `GeneExpressionTokenizer` | `src/sea_ad_jepa/v4/gene_tokenizer.py` |
| Query head | `SingletonQueryPredictor` | recovered `full104_model_components_v2.py` |
| Objective | `directional_pair_context_loss` | recovered `full104_model_components_v2.py` |
| Initialization | `online_encoder` at `u0` | `t1_checkpoint_u0000.pt` |

`DirectResidualStateHead` is **excluded** from this generation for two recorded reasons:
`DIRECT_INIT_MANIFEST.json` does not exist, so `from_freeze()` cannot run; and
`Full104HeadConfig.validate()` raises on `shared_dim <= 0` while the closed FULL104
terminal is `D_shared = null`. Both must be resolved before the full planned path is
qualifiable.

`BlockPredictor` and the graph block-mean target are **excluded**. They are the historical
T1 path, and closed finding #6 records that an arithmetic block-mean target can destroy
rare/local information.

## 3. Frozen semantics

Per cell, a fixed query set `Q` is drawn. Let `M` be `MEASURED_SCALAR` addresses.

- **Teacher evidence:** `M \ Q` — richest lawful context with *every* query ablated.
- **Student evidence:** `partial(M) \ Q` — a lawful subset at the frozen evidence level,
  with every query ablated.
- **Teacher target at `q`:** `LayerNorm(h_q - mean(h over teacher-visible))`, stop-gradient.
- **Student prediction at `q`:** `SingletonQueryPredictor(identity, q, student.gene_states,
  student.cell_state, student_visible)`.

Ablating the whole query set from **both** roles is a deliberate deviation from F1's
per-query masking. It is strictly stronger against query-self leakage and reduces teacher
forwards from `|Q|` to one per cell. It is declared here, prospectively, and is not a
result-driven choice.

The teacher is an EMA of the online encoder. Gradient never reaches it.

## 4. Loss

`directional_pair_context_loss(predicted, target, pairs)`, exact recovered bytes.

It centres each cell's query set (`x - x.mean(dim=1)`), which removes the cell-global
component **by construction**, then matches the direction of between-cell differences.
It is structurally unable to be solved through the CELL token or a global mean — the
pathway that produced the historical rare-biology destruction while T1's loss fell 382x.

## 5. Mechanics gates — the only STOP conditions

All predeclared. No post-result tuning. Evaluated at the first successful update and at
every telemetry checkpoint.

| Gate | Condition | Rationale |
|---|---|---|
| `G1_gradient_coverage` | all **48** tensors in `{attention_norm, query, key, value} x 6 blocks` have gradient norm `> 0` | T1 had 48/48 exactly zero |
| `G2_optimizer_moments` | the same 48 tensors have nonzero Adam `exp_avg` and `exp_avg_sq` after the step | T1 had exactly-zero moments at every checkpoint |
| `G3_movement_beyond_decay` | relative movement of Q/K/V exceeds `(1 - lr*wd)^steps` by the frozen margin | T1 sat at `1.017x` pure decoupled decay for 205 updates |
| `G4_routing_diversity` | attention weights differ across query addresses within a cell | uniform routing is indistinguishable across queries |

Gradient and moment checks are **per tensor**, never pooled. The historical
`component_gradient_report` pooled all block parameters into one `IPB_shared` L2 norm and
therefore reported `2.431694` at update 1 while 48 tensors were dead. Pooled reporting is
forbidden here. `missing` must mean `norm == 0`, not `grad is None`.

## 6. Routing outcome — reported, not gated

`N_eff/N`, max-weight-over-uniform, and top-k mass are recorded per block and head. The
terminal must name one of three outcomes explicitly:

- `ROUTING_SHARPENED` — `N_eff/N` falls materially below the frozen initial value;
- `ROUTING_DIFFUSE_WITH_HEALTHY_GRADIENTS` — G1–G3 pass and routing does not sharpen;
- `ROUTING_UNRESOLVED` — insufficient updates to distinguish.

`ROUTING_DIFFUSE_WITH_HEALTHY_GRADIENTS` is **not a failure**. It is the first honest test
of whether the ELU+1 kernel can sharpen when an objective actually asks it to, and it is
the only evidence that would justify reopening the attention architecture.

## 7. Biology telemetry — logged, with one safety abort

Biology is recorded, never used to select. Exactly one biology-derived STOP exists:

`G5_rare_non_degradation` — if a frozen rare/innovation endpoint degrades beyond the
predeclared margin, the run aborts.

This is a safety rail, not a selection rule: it can only stop the run, never choose among
candidates or promote anything.

It is checked **every telemetry checkpoint, not at the end**. In T1, `recurrent_1pct`
held flat through `u100` and then lost 23% of its average precision between `u100` and
`u200`, while the loss fell a further 32%. End-of-run evaluation would have missed it.

Endpoints must be checked for **dynamic range** before being trusted. T1's headline R²
endpoints sat at `0.9999` — saturated at ceiling and structurally incapable of registering
damage. Any endpoint whose baseline spread is below the frozen floor is reported as
`SATURATED_NOT_DECISION_BEARING`.

## 8. Modes and launch guard

Three mutually exclusive modes:

- `synthetic` — self-contained, no expression, open. The only mode this contract authorizes.
- `technical-fixture` — bounded authenticated real cells, requires launch authority.
- `real` — requires launch authority.

`technical-fixture` and `real` require an external JSON launch authority binding executor
and contract byte hashes, Git commit, frozen authority roots, output root, and an exact
boolean. Missing, malformed, stale, mismatched or self-created authority stops before any
expression access.

Real mode additionally requires:

- its **own** authorization — the current gate forbids optimizer steps, EMA updates and
  checkpoint writes by name, and F1-B may not ride on F1's authorization;
- **population disjointness** from F1-A's 2,781 evaluation recipients, asserted and
  recorded, so F1-A is not contaminated by an encoder that has seen its own evaluation cells;
- TRAIN-only, reader-fit only. DEV, SEALED, pathology and reader-validation/oracle forbidden.

## 9. Firewall

No DEV/SEALED/pathology. No F1 candidate outcome is read or computed. No protected-program
selection. No target family is promoted. No F1-A gate, weight, assignment, null map or
population is modified.

## 10. Promotion

Successful completion of this implementation phase ends at
`PASS_F1B_MINIMAL_BRIDGE_IMPLEMENTATION_AWAITING_INDEPENDENT_VERIFICATION`.

The implementer may not issue `PASS_IMPLEMENTATION_VERIFIER`. One fresh independent
verifier must reconstruct the conclusion-bearing mechanics from this contract text alone —
never from implementer notes — and defeat deliberate mutations, per
`MANDATORY_IMPLEMENTATION_VERIFIER_V1`.
