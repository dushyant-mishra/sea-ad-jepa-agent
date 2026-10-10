# JEPA synthetic-dataset lane — final V78 takeover handoff

Date: 2026-10-09

Claim class: **NON-TRAINING SYNTHETIC-LANE TAKEOVER / V78 SCIENTIFIC FALSIFICATION COMPLETE / NO ARM PROMOTED**

This file is the canonical cold-start handoff for the synthetic-dataset lane. A new agent should be able to continue without reconstructing chat history or repeating broad repository archaeology.

## 1. Exact takeover point

Implementation PR: **#242 — `V78 signed detection + marginal repair implementation`**

Implementation branch:
`impl/v78-signed-detection-marginals-20261009`

Audited implementation head:
`e959d9a732698ae9a41e8cb1f6c10052d7390326`

This handoff branch is created directly from that exact head:
`handoff/jepa-synthetic-v78-final-takeover-20261009`

At the audited implementation head, both required GitHub Actions workflows pass:

- V78 signed detection marginals: run `37998229856` — **SUCCESS**
- inherited V77 synthetic class propagation: run `37998229898` — **SUCCESS**

PR #242 remains draft and non-training-authorizing.

## 2. Lane boundary

This handoff owns only:

`corrected S174 TRAIN geometry -> synthetic generator -> frozen synthetic mechanism experiments -> synthetic-world adequacy`

Do not take over target-discovery work from this lane. In particular do not modify TD56/TD57/TD58/TD59 replay, target panels, ATAC/SCENIC+/NIH-CARD target evidence, 353 historical ID repair, or Bayesian target ranking.

Macha is separately authorized to work on a **TRAIN-only Bayesian dataset-geometry sublane** using the full corrected dataset locally. That work is observational/non-promoting and must return only identity-scrubbed geometry to the synthetic lane. It must not alter V78 retrospectively.

## 3. Historical defect that reset this lane

The old V77 real-data calibration cache used for HVS and SEA-AD had a gene-axis/label defect. Macha/Claude proved this physically, rebuilt the S174 TRAIN cache by real gene ID, preserved the failed preregistered G1 check, and then executed the authorized G1b repair.

Corrected scientific consequences included:

- S149 pooled `|r| > 0.3`: approximately `0.6148 -> 0.1348`;
- coverage-only null: approximately `0.5463 -> 0.0042`;
- coverage share of pooled correlation: approximately `89% -> 3%`;
- corrected real median absolute gene-gene correlation: approximately `0.056` rather than approximately `0.33`;
- broad cell class contributes materially to pooled-vs-within geometry;
- corrected real T5 descriptive reference: `0.7434589733649325`.

Therefore the earlier V77 interpretation that cohort/coverage explained most real correlation structure was superseded.

The following prior decisions were also superseded by the corrected replay: the Step-3 claim that latent mechanism was solved and observation was the bottleneck; the factor-family falsification conclusion; and the previous substate/Observer-V2 promotion language.

Still valid: no synthetic candidate had been accepted, and detection contains more dependence than positive expression.

## 4. ETL -> generator reconciliation and V77 class propagation

PR #239 merged the synthetic ETL-to-generator reconciliation onto the corrected-S174 lineage.

Primary defect found: real calibration described broad cell class, but V73/V77 synthetic truth did not physically instantiate broad cell class as a generative variable or condition biological covariance on it. Thus T5 was being used as a guard for structure the generator did not actually contain.

PR #240 then executed the prospective E0-E3 class-propagation tournament.

Important results:

- E1 = E0 exactly on the full matched score object: isolation PASS.
- corrected real T5: `0.7435` descriptive only.
- E0/E1 T5: about `1.05047`.
- E2 T5: about `0.91418`, moving in the biologically expected direction.
- E3 T5: about `1.19432`, wrong direction.
- E2 proved that broad class supplies a missing covariance component, but E2 was not adequate because detection topology, abundance and depth remained wrong or worsened.
- E3 was rejected.
- no E0-E3 arm was promoted.

This established the V78 premise: preserve E2 as the biological baseline and separately interrogate signed detection topology plus abundance/depth marginals.

## 5. V78 frozen design

V78 arms were prospectively fixed as:

- **F0**: exact committed E2 reference, BackgroundV1;
- **F1**: E2 with existing unmodified BackgroundV2 only;
- **F2**: F0 plus an isolated preregistered signed detection-selection field;
- **F3**: F2 plus pathology-blind rank-scrubbed abundance and operator->source->global depth marginals.

Frozen first-tournament settings:

- cells: `2500`;
- generator seed: `7302`;
- measurement seed: `7302`;
- E2 class program scale: `0.55`;
- corrected evaluation universe: 14,417 addresses;
- evaluation universe SHA-256: `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`;
- 41,238-address registry SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`;
- class authority SHA-256: `a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014`.

No post-outcome scale/seed/threshold retuning is allowed for V78.

## 6. Critical S174 custody correction

Two corrected-looking cache lineages exist and must not be conflated.

### Historical Stage81A3R archive

Library path:
`/Jepa project/stage81a3r_corrected_real_train.zip`

SHA-256:
`3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`

It contains 42 counts + 42 meta shards and is valid historical custody, but it is **not byte-equivalent to the later repaired S174 cache used by current V78**. The V78 substrate-distinction audit found only 7/42 count shards and 7/42 paired meta shards matching the later repaired lineage; 35/42 pairs differ.

### Current V78 repaired S174 substrate

Library path:
`/Jepa project/s174_rebuilt_real_train_v1.rar`

Size:
`47,964,366` bytes

SHA-256:
`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

The RAR contains 85 archive members: one directory plus exactly 42 `*.counts.npz` and 42 paired `*.meta.npz` files.

Current repaired calibration SHA-256:
`f6ba2c725a5437cc8455fff418027d36efe9ea9430fbd0a5765df62dedca6068`

Paired-meta semantic SHA-256:
`b876e13526f51d5a4199ca750ad09065c5ab8a20aeca39dff3d8c385f2241f46`

The current V78 gate and authority are bound to this repaired lineage, not the older Stage81A3R ZIP.

Canonical custody records:

- `results/v78/V78_S174_SUBSTRATE_DISTINCTION_V1.json`
- `results/v78/V78_S174_SHARD_META_DIGEST_V1.json`
- `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`
- `results/v78/V78_S174_CACHE_RECOVERY_CUSTODY_V1.json` — historical recovery record; read together with the substrate-distinction supersession.

Important semantic ruling: S174 `source_library` is a **per-cell library total**, not operator identity. Operator identity comes from the authenticated shard->matrix->operator bridge.

## 7. Canonical repaired F3 marginal authority

The current authority was built directly from the repaired S174 substrate and is preserved in Library custody as:

`/Jepa project/V78_MARGINAL_AUTHORITY_REPAIRED_V1.json`

SHA-256:
`997280132e981b4c23fab97c479eab782a7d7b162944364062ca21e18c9324c1`

Authority provenance:

- shards: 42;
- cells: 4,726;
- registry addresses: 41,238;
- corrected calibration SHA matches the repaired lineage;
- paired meta manifest verified;
- operator bridge verified;
- `canonical_corrected_train = true`;
- `training_authorized = false`.

Rank-scrubbed abundance geometry:

- positive addresses: `32,807`;
- zero addresses: `8,431`;
- identity scrubbed: true;
- rank scrubbed: true.

The synthetic generator may consume compact identity-scrubbed geometry only; it may not open corrected real cache paths at generation time.

## 8. V78 pre-execution gate

Canonical committed receipt:
`results/v78/V78_PREEXECUTION_GATE_READY_V1.json`

Status: **READY**

Blockers: `[]`

The gate authenticates:

- committed E2 reference;
- class authority;
- corrected evaluation universe;
- 42-operator bridge;
- repaired marginal authority;
- 42 count + 42 paired meta physical shards;
- 2K structural support with all 42 operators and minimum support >= 1.

The gate does **not** authorize JEPA training, E4, post-outcome retuning or protected data.

## 9. Frozen F0-F3 tournament — complete

Canonical committed result:
`results/v78/V78_SIGNED_DETECTION_MARGINAL_TOURNAMENT_V1.json`

Raw full local execution custody:
`/Jepa project/V78_FROZEN_LOCAL_TOURNAMENT_20261009.json`

Raw artifact SHA-256:
`981ea94af5fdfec258f7e620fa1fd2d4cb883b8330846f02c6aa258a45daacd3`

F0 exactly reproduces the committed E2 legacy score object.

Corrected real descriptive references used for interpretation, not binary pass/fail:

- detection median |r|: `0.19456419986728707`;
- strong-edge fraction `|r|>0.3`: `0.1348331666110926`;
- detection mean degree: `404.36466666666666`;
- detection transitivity: `0.6672406627478484`;
- positive/negative strong-edge ratio: `59.018503859093606`;
- T5 within/pooled: `0.7434589733649325`;
- abundance max/median nonzero: `2273.2075`;
- top-1% count share: `0.2741`;
- median detected/cell: `4495.5`.

### F0 — E2 baseline

- pos/neg ratio: `1800.3074`;
- mean degree: `293.0127`;
- transitivity: `0.40938`;
- T5: `0.914176`;
- abundance max/median: `501.138`;
- top-1% share: `0.23462`;
- median detected/cell: `3276`.

### F1 — BackgroundV2 only

- pos/neg ratio: `67.7444`, directionally close to real `59.0185`;
- mean degree collapses to `73.3273`;
- transitivity falls to `0.29112`;
- T5 reverts to `1.05845`;
- abundance max/median collapses to `78.3812`;
- top-1% share falls to `0.11856`;
- median detected/cell `2939.5`.

Ruling: **directional signed-ratio success, adequacy rejected**. A single near-match does not compensate for collapsed unsigned topology, lost E2 T5 direction and badly distorted marginals.

### F2 — preregistered signed detection field

- pos/neg ratio worsens to `8154.0909`;
- negative strong-edge fraction falls to approximately `2.45e-6`;
- mean degree `59.804`;
- transitivity `0.24990`;
- T5 `1.05749`;
- abundance max/median `641.684`;
- top-1% share `0.27180`;
- median detected/cell `2935`.

Ruling: **the frozen signed-detection mechanism/scale is falsified**. Do not generalize this to every possible signed-detection model.

### F3 — F2 plus repaired abundance/depth marginals

- pos/neg ratio worsens further to `54704`;
- mean degree `36.47`;
- transitivity `0.23319`;
- T5 `1.09347`;
- abundance max/median moves toward real to `1385.252`;
- top-1% share `0.22524`, away from real `0.2741`;
- median detected/cell `2433`, away from real `4495.5`.

Ruling: **count/depth marginal repair is inadequate and does not retain signed topology**.

## 10. Canonical scientific ruling

File:
`results/v78/V78_SIGNED_DETECTION_MARGINAL_SCIENTIFIC_RULING_V1.json`

Terminal interpretation:

- F0: exact E2 reproduction; baseline only.
- F1: BackgroundV2 contains structure capable of producing substantially more negative detection dependence, but not with adequate joint topology/marginal realism.
- F2: independent signed selection field is not an adequate explanation at the frozen geometry and magnitude.
- F3: marginal replacement alone cannot rescue topology; dependence and marginal mechanisms interact.
- promoted arm: **none**.
- training authorized: **false**.
- E4 authorized: **false**.
- target-discovery changes: **false**.
- next mechanism family: **unselected; do not retune V78**.

## 11. Exact current executable/code surface

Primary V78 implementation files:

- `scripts/v77/run_v78_signed_detection_marginal_tournament.py`
- `scripts/v77/run_v78_frozen_execution.py`
- `scripts/v77/build_v78_fullscale_rna_observer.py`
- `scripts/v77/build_v78_marginal_authority.py`
- `scripts/v77/build_v78_repaired_s174_marginal_authority.py`
- `scripts/v77/v78_signed_detection.py`
- `scripts/v77/v78_signed_scoring.py`

Primary tests:

- `tests/test_v78_signed_detection_marginals_v1.py`
- `tests/test_v78_marginal_authority_v1.py`
- `tests/test_v78_canonical_marginal_authority_build_v1.py`
- `tests/test_v78_signed_scoring_v1.py`
- `tests/test_v78_f3_depth_runtime_v1.py`
- `tests/test_v78_preexecution_gate_v1.py`
- `tests/test_v78_frozen_execution_driver_v1.py`

Primary V78 receipts:

- `results/v78/V78_S174_SUBSTRATE_DISTINCTION_V1.json`
- `results/v78/V78_S174_SHARD_META_DIGEST_V1.json`
- `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`
- `results/v78/V78_MARGINAL_AUTHORITY_CUSTODY_V1.json`
- `results/v78/V78_PREEXECUTION_GATE_READY_V1.json`
- `results/v78/V78_FROZEN_LOCAL_TOURNAMENT_CUSTODY_V1.json`
- `results/v78/V78_FROZEN_LOCAL_SCIENTIFIC_RULING_V1.json`
- `results/v78/V78_SIGNED_DETECTION_MARGINAL_TOURNAMENT_V1.json`
- `results/v78/V78_SIGNED_DETECTION_MARGINAL_SCIENTIFIC_RULING_V1.json`

Frozen design/plan:

- `docs/superpowers/specs/2026-10-08-v78-signed-detection-marginals-design.md`
- `docs/superpowers/plans/2026-10-09-v78-signed-detection-marginals.md`

## 12. CI state

At implementation head `e959d9a732698ae9a41e8cb1f6c10052d7390326`:

- V78 workflow `37998229856`: SUCCESS.
- V77 class-propagation spillover workflow `37998229898`: SUCCESS.

Do not claim a later head is green without fresh verification.

## 13. Parallel Bayesian dataset-geometry work (Macha)

Macha has local full corrected TRAIN access and has been assigned a separate Bayesian synthetic-geometry sublane.

Purpose: estimate TRAIN-only posterior uncertainty and variance decomposition for broad class, donor, source, operator, donor×class and within-class biology; model detection separately from positive expression/count magnitude; produce posterior-predictive distributions for synthetic adequacy.

Required firewall:

- no TD panel membership;
- no target ranks/posteriors;
- no SCENIC+/ATAC target evidence;
- no pathology labels;
- no TEST/Morabito;
- synthetic-consumable outputs must be identity scrubbed.

V78 is the pre-Bayesian baseline and must not be retroactively retuned from Bayesian results.

When Macha returns, use the posterior geometry only to motivate a **new prospective V79 design**.

## 14. What the next agent should do

Do **not** rerun repository-wide archaeology before beginning. Start from the exact audited V78 head above and verify only whether the PR head moved.

Immediate next work is prospective V79 design, not V78 tuning.

Recommended sequence:

1. Re-fetch PR #242 and compare its head to `e959d9a732698ae9a41e8cb1f6c10052d7390326`.
2. If unchanged, accept the V78 gate/tournament/ruling as the current frozen baseline.
3. If moved, inspect only commits after `e959d9a7...` and require fresh V78 + V77 workflows before trusting the newer head.
4. Consume Macha Bayesian synthetic-geometry results only after their custody, diagnostics, leakage tests and identity-scrubbing are verified.
5. Design V79 prospectively around the actual falsification:
   - BackgroundV2 can move signed ratio dramatically but destroys other geometry;
   - independent F2 signed selection fails;
   - F3 marginal replacement cannot rescue dependence;
   - therefore the next mechanism should address coupled detection/dependence/marginal structure rather than retuning F2/F3 scales.
6. Freeze V79 mechanisms, seeds, endpoints and falsification rules before any new outcome read.
7. Keep S159 descriptive; do not convert the old 20-resample intervals into binary gates.
8. Keep corrected pooled references descriptive until the Bayesian uncertainty work justifies a stronger population-level interpretation.

## 15. Hard boundaries

Remain fail-closed on:

- JEPA real-data training;
- production optimizer/EMA/runtime changes;
- E4 donor×class implementation unless separately authorized;
- TEST/Morabito;
- 500K/Stage4;
- target-discovery replay/ranking;
- 353 historical ID remediation;
- production target freeze;
- production representation freeze;
- post-outcome V78 retuning;
- planting real named biological programs into synthetic truth.

## 16. Historical branch map

Useful history only; do not use as modern implementation bases:

- `claude/v74-macha-reconciliation-20261003` @ `733829c69e14b094537481fbfaceafe08bf179d1` — older infrastructure/reconciliation lineage.
- `claude/v77-synthetic-premise-custody-20261005` — proved the S174 axis defect before corrected rebuild.
- `claude/s174-train-cache-rebuild-20261007` @ `f88338713b173edb3acbc90662e607ce45b5878b` — corrected S174 ancestor and PR #239 merge point.
- `impl/v77-class-propagation-20261008` / PR #240 — E0-E3 class-propagation experiment.
- `impl/v78-signed-detection-marginals-20261009` / PR #242 — current implementation/scientific baseline.

## 17. Terminal state

`V78 = COMPLETE SCIENTIFIC FALSIFICATION BASELINE`

`PREEXECUTION_GATE = READY`

`F0_EXACT_E2 = PASS`

`F1 = DIRECTIONAL SIGNED-RATIO SUCCESS, ADEQUACY REJECTED`

`F2 = FROZEN SIGNED-DETECTION HYPOTHESIS FALSIFIED`

`F3 = MARGINAL REPAIR INADEQUATE`

`PROMOTED_ARM = NONE`

`TRAINING_AUTHORIZED = FALSE`

`NEXT = PROSPECTIVE V79 DESIGN + INDEPENDENT BAYESIAN DATASET-GEOMETRY EVIDENCE`
