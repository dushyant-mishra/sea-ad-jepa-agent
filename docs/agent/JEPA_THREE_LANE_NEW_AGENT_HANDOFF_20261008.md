# JEPA three-lane cold-start takeover — 2026-10-08

Status: **COLD-START HANDOFF / NON-AUTHORIZING / THREE LANES MUST REMAIN SEPARATE**

This is the successor handoff to PR #237. It is written so a new agent can continue without reconstructing prior chats. It does not authorize additional training, additional optimizer steps, real-data training, TEST access, Morabito access, 500K, Stage 4, target freeze, representation freeze or production EMA selection.

---

## 0. First rule: preserve the three-lane separation

Do **not** collapse these lanes into one branch and do **not** cherry-pick old runtime code across them.

### Lane A — canonical runtime / integration / guarded mutation mechanics

Purpose: own the actual student, predictor, teacher, optimizer, EMA, checkpoint/restart, qualification join, physical provenance and bounded synthetic mutation mechanics.

Current takeover surface:

- PR #237: `handoff/jepa-20261008-complete-runtime-s174-takeover`
- PR #237 head: `cae71f20d15ae7399fd38bc6bf15dbe16048797f`
- active executable source underneath: PR #236 branch `impl/v77-bounded-synthetic-mutation-20261007`
- PR #236 current source head: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`
- final execution-bearing audited commit: `8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

Authority: **mechanics-only, synthetic-only, non-production**.

Do not import runtime implementation from the S174 lane or from historical Macha branches.

### Lane B — S174 real-TRAIN cache repair and corrected real-data replay

Purpose: repair the scrambled Stage81A3R TRAIN cache, replay affected V77 real-data calibration/statistical analyses, preserve old-vs-corrected results, and keep identity issues explicit.

Current source:

- branch: `claude/s174-train-cache-rebuild-20261007`
- source head: `750cb83c8c0535cc67a70d58b62db5607bd7d01e`
- last CI-confirmed execution checkpoint: `46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`
- CI run: `37693603160`
- result: **146 passed, zero skipped**

Exact snapshot preserved inside PR #237:

`custody/takeover_20261008/s174_working_snapshot/`

Authority: **TRAIN-only real-data repair/replay and corrected descriptive science**. No training, no optimizer/EMA/runtime implementation.

Do not merge this branch's historical runtime lineage into Lane A.

### Lane C — Macha / V77 synthetic scientific-design lane

Purpose: synthetic-world design, identifiability analysis, context shortcut audits, observation-operator design, preregistration and scientific hypotheses.

Historical Macha branch:

- `claude/v77-synthetic-premise-custody-20261005`
- current head: `976d2be6c8cfaf46e7dfd79bf900fb9fc4c0d4bd`

Important: this branch contains valuable scientific history but its old runtime/interface pins are superseded. Lane C must **consume** the frozen Lane A runtime contract; it must not create another optimizer/EMA/checkpoint stack.

Authority: **scientific design and synthetic diagnostics only**, unless a later prospectively frozen contract explicitly grants more.

---

## 1. Canonical read order

A new agent should read in this order before editing code:

1. `custody/takeover_20261008/MANIFEST.json`
2. `docs/agent/JEPA_COMPLETE_TAKEOVER_20261008.md`
3. this file
4. `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md`
5. `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md`
6. `docs/agent/JEPA_NEW_AGENT_FULL_TAKEOVER_HANDOFF_20261007.md`
7. `custody/takeover_20261008/PR230_PRIOR_HANDOFF.md`
8. `custody/takeover_20261008/s174_working_snapshot/docs/agent/S174_REPLAY_SUMMARY.md`
9. `custody/takeover_20261008/s174_working_snapshot/docs/agent/S174_SYNTHETIC_REPLAY.md`
10. `custody/takeover_20261008/s174_working_snapshot/docs/agent/S174_DOWNSTREAM_RESCORE.md`

Do not use old handoff "next step" instructions without checking whether they were superseded. In particular, PR #228-era instructions to prove ZERO_UPDATE and then attempt one tiny synthetic update are **already complete**.

---

## 2. Canonical runtime lineage — do not replace it

Accepted chain:

1. PR #224 canonical runtime: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
2. PR #226 shared qualification V2: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
3. PR #228 joined V77 ZERO_UPDATE: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
4. PR #232 physical-provenance V2 repair: `d3430ce6c0e878272e92b61e01822334e088d8c8`
5. PR #233 CI coverage repair for the 2K 42/42 observation-operator gate
6. PR #234 pre-rehearsal freeze
7. PR #235 preregistered one-step bounded synthetic rehearsal contract
8. PR #236 implemented and audited one-step synthetic rehearsal
9. PR #237 consolidated takeover/custody

The canonical low-level model/runtime components are already selected for mechanics:

- online/student encoder: V5 `KeyedIPBEncoderV2Reference`;
- predictor: inherited V4 `BlockPredictor` mechanics;
- tokenizer: inherited V4 gene-tokenizer mechanics;
- teacher: parameter-identical deep copy of the authenticated student at initialization, frozen for gradient updates and advanced only by guarded EMA after successful optimizer completion;
- optimizer: canonical AdamW path over online encoder + predictor only;
- teacher target evaluation under `torch.no_grad()`;
- gradient validation occurs after unscale and before step;
- physical optimizer completion must be proven before EMA;
- EMA unit: `SUCCESSFUL_BASE_CELL_PRESENTATIONS`;
- EMA is presentation-normalized, not fixed-step `.996` authority;
- checkpoint/restart persists online encoder, predictor, EMA teacher, optimizer, scaler/cursor plus typed authority/provenance continuation.

Historical fixed `.996` is V3/test history only. Candidate 16,249 presentations is not a production half-life. The bounded rehearsal used a **test-only 1000-presentation half-life** and did not select production EMA.

---

## 3. What Lane A has actually proven

### 3.1 Joined q-safety and interface work

The historical audit found the initial PR #228 join was too shallow. It was repaired prospectively through RED->GREEN tests.

Decision-changing milestones included:

- policy-only q-safety cannot be promoted to executed proof;
- a bare `PROVEN_BY_BOUND_ADAPTER_RUNTIME` status cannot mint proof;
- typed `BoundAdapterQSafetyProofV1` is required;
- proof is bound to exact adapter identity/digest, batch scientific identity and runtime source digest;
- actual V77 `SyntheticConversion` is physically converted into `QualificationBatchV1`;
- raw `source_index` and `operator_index` are provenance/operator context and cannot reach learned model inputs;
- unreviewed dataset/operator identity proxies fail closed;
- executed hidden-query perturbation proves query values cannot alter model-visible state, lawful normalization/depth summaries, support/missingness, masks or query-dependent preprocessing.

Key files in current top-level lineage:

- `scripts/v77/v77_synthetic_batch_adapter.py`
- `src/sea_ad_jepa/qualification/v77_join.py`
- `src/sea_ad_jepa/qualification/v77_zero_update.py`
- `src/sea_ad_jepa/qualification/v77_bound_zero_update.py`
- `tests/integration/test_v77_joined_zero_update.py`
- `tests/integration/test_v77_executed_q_safety.py`
- `tests/integration/test_v77_canonical_zero_update.py`
- `.github/workflows/v77-qualified-zero-update-join.yml`

### 3.2 Historical physical-provenance failures that drove the repair

Never forget these attacks:

- TD23/TD33 reset-row/global-row alias: B-side local `sample_row` was once treated as a global expression row; false relationship ~0.3906 vs correct ~0.00625.
- Sept-8 finding: metadata and payload authentication are insufficient if the values consumed come from the wrong physical row.

Required proof chain:

`global expression row + block-local selected row + logical cell + source cell + donor + matrix slot + feature space + payload location + authenticated payload digest + authenticated value digest + consumed value digest`

must refer to one physical observation.

PR #232 made `PhysicalRowValueBindingV2` mandatory at ZERO_UPDATE execution and added authenticated payload digest checking.

PR #232 head:

`d3430ce6c0e878272e92b61e01822334e088d8c8`

Workflow run `37693805825`: **29 passed**.

### 3.3 2K operator-support regression

Historical failure:

- stress-twin 2K: 42/42 operators, minimum count 1;
- calibration-closure 2K: 36/42, minimum 0;
- 10K: 42/42 vs 41/42;
- at >=100K both appeared complete.

Root cause: calibration-closure removed the zero-quota rescue. Since 2K is the smoke gate, this can silently qualify the wrong observation process.

PR #233 added the existing 2K regression to V77 CI. Current accepted rule: **all 42 operators must be present, minimum support >=1 at 2K**.

Do not restore the calibration-closure sampler lineage that erased operators.

### 3.4 Bounded one-step synthetic mutation rehearsal

Contract: `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_CONTRACT_20261007.md`

Audit: `docs/agent/V77_BOUNDED_SYNTHETIC_MUTATION_REHEARSAL_AUDIT_20261008.md`

Implementation:

- `src/sea_ad_jepa/qualification/v77_bounded_mutation.py`
- `tests/integration/test_v77_bounded_synthetic_mutation.py`
- `.github/workflows/v77-qualified-zero-update-join.yml`

Audited execution commit:

`8dabe9ef9ed87b4beaf00acefda1a3073ed751de`

CI:

- joined workflow run `37712331165`: **51 passed**;
- independent successful-custody rerun: **1 passed**;
- shared qualification workflow `37712331253`: SUCCESS.

Observed successful state change:

- optimizer `0 -> 1`;
- teacher presentations `0 -> 2`;
- student/online parameters changed;
- predictor changed;
- teacher changed only after completion;
- optimizer state changed;
- typed continuation persisted;
- fresh modules restored to exact post-step digests.

Adversaries include missing/wrong physical proof, wrong adapter/runtime, q-proof replay, nonfinite/GradScaler skip, EMA-before-completion, same-run reuse, weak V1 runtime proof, EMA restart drift, and exact child reload.

This proves **one tiny synthetic update only**. It grants no second update and no production/real-data authority.

---

## 4. Runtime proof semantics — important historical distinction

Do not promote older compatibility proof classes.

- `BoundRuntimeMutationProofV1`: historical/diagnostic only.
- mutation promotion requires typed presentation-EMA V2 physical continuation from the actual persisted artifact.
- q-safety proof is separate from runtime-provenance proof.
- generic callbacks do not prove physical zero mutation.
- policy declarations do not prove executed transitive q-safety.

The deterministic V5 teacher-block loss used by runtime qualification is a **mechanics fixture**, not scientific target authority.

---

## 5. Teacher/student scientific identifiability rule

The project corrected a fundamental target mistake historically.

A richer teacher is desirable, but a partial-RNA student cannot generally reproduce teacher-private realization-level state that is absent from its observations. Under deterministic squared-error prediction, the student can only learn the conditional expectation of the target given admitted evidence.

Therefore:

- do not require full rich-teacher realization matching from partial RNA;
- score a shared/predictable component, or explicitly model uncertainty/distributions/abstention;
- exact same-assay RNA semantic twins can legitimately remain `NON_IDENTIFIABLE_BY_DESIGN`;
- runtime mechanics do not resolve target identifiability.

This remains a scientific-design problem for Lane C.

---

## 6. Lane B: S174 real-data defect and corrected evidence

### 6.1 Defect

Old cache:

`data/cache/stage81a3r_corrected_real_train`

Despite its name, "corrected" meant collision handling; the feature axis still applied a frozen HVS/SEA-AD provenance table to physical H5 columns. The 2026-09-27 decoder had already demonstrated that this positional feature mapping was wrong.

S174 value probe prospectively preregistered and then read 36 TRAIN cells across:

- one HVS matrix;
- SEA-AD MTG;
- SEA-AD DFC/A9.

Results:

- cache matched the scrambled builder map 100%;
- true gene-by-Ensembl match ~2.4-3.0%;
- decoder recovered ~99.9-100%.

Named-marker examples included MBP, PLP1, SNAP25 and GAD1 being zero at their nominal cache addresses while the source contained high counts because those addresses physically contained other genes.

Conclusion: **S174_VALUE_VERIFIED**.

### 6.2 Rebuild

Corrected cache:

`data/cache/s174_rebuilt_real_train_v1`

Built by fresh gene-ID join from the physical H5AD columns. Old cache left untouched. NPH shards copied byte-identically because NPH identity was already correct.

Key producing/verification scripts in the S174 snapshot:

- `scripts/v77/rebuild_s174_train_cache.py`
- `scripts/v77/compare_s174_rebuild.py`
- `scripts/v77/explain_s174_g1.py`
- `scripts/v77/gate_s174_g1b.py`
- `scripts/v77/rescore_s174_downstream.py`
- `scripts/v77/summarize_s174_synthetic_replay.py`

Frozen/verification records:

- `results/v77/S174_REBUILD_FREEZE_V1.json`
- `results/v77/S174_REBUILD_BUILD_RECEIPT_V1.json`
- `results/v77/S174_REBUILD_VERIFY_AND_COMPARISON_V1.json`
- `results/v77/S174_REBUILD_G1_EXPLANATION_V1.json`
- `results/v77/S174_REBUILD_G1B_FREEZE_V1.json`
- `results/v77/S174_REBUILD_G1B_RESULT_V1.json`
- `results/v77/S174_REBUILD_STATUS_V1.json`
- `results/v77/S174_REBUILD_RECOVERY_V1.json`

Frozen G1 genuinely failed and must remain recorded as failed. It failed because the independent re-read was too narrow for 897 pre-existing SEA-AD identity remappings. The explanatory audit localized **100%** of discrepancies to the frozen remap set; all other addresses matched exactly and each remapped entry equaled the physical source count. A prospectively frozen successor G1b was then used. Do not rewrite history and relabel G1 as pass.

The 353 historical Ensembl-ID -> different-symbol remappings remain a separate identity-governance issue. Do not change them opportunistically to improve a replay.

### 6.3 Corrected S149 and real calibration results

Primary summary:

`custody/takeover_20261008/s174_working_snapshot/docs/agent/S174_REPLAY_SUMMARY.md`

Machine-readable side-by-side:

`custody/takeover_20261008/s174_working_snapshot/results/v77/s174_replay/S174_REPLAY_SIDE_BY_SIDE_V1.json`

Decision-changing S149 correction:

- pooled detection fraction |r| > 0.3: `0.6148 -> 0.1348`;
- coverage-only null: `0.5463 -> 0.0042`;
- old coverage share ~88.85%; corrected ~3.14%;
- median |corr|: pooled `0.377 -> 0.1946`, null `0.3273 -> 0.013`;
- study/coverage stratum still identifiable.

Therefore the old headline "pooled real dependence is mostly cohort-composition artifact" does **not** survive the corrected cache.

The corrected evidence says cohort coverage is still a strong source/study identifier, but it does not explain most pooled correlation structure.

Other corrected point estimates include:

- expression median |corr| `0.3291 -> 0.0562`;
- expression pair fraction |r|>0.3 `0.5621 -> 0.0242`;
- expression top-10-PC variance `0.5089 -> 0.2620`;
- detection transitivity `0.8871 -> 0.6672`;
- detection mean degree `1843.8 -> 404.36`;
- corrected evaluation universe 14,417 addresses vs old 19,569; Jaccard 0.4935.

### 6.4 S159 remains unresolved

Do not turn donor-bootstrap intervals into pass/fail thresholds yet.

Some corrected real point estimates sit outside their own donor-bootstrap p05-p95 intervals, including expression median |corr| and detection transitivity. Therefore current intervals are **uncertainty diagnostics**, not qualification thresholds.

Do not recenter an interval to make the point fit.

---

## 7. Lane C: Macha/V77 science history that remains valid

Historical Macha branch contains valuable audits, but do not use its old runtime pins.

Important surviving scientific conclusions:

- S157 exact same-assay RNA twin: `NON_IDENTIFIABLE_BY_DESIGN`; do not tune it away.
- source/operator IDs can trivially distinguish worlds but are shortcut controls, not biological covariates.
- measurement/support context can itself become an identity proxy and must be audited.
- SCENIC+/ATAC are not automatically independent if derived from or selected using the same RNA; independence/pairing must be demonstrated.
- technology is an observation process/operator, not a free biological dataset embedding.
- biological OOD and measurement OOD must be distinguished.
- donor variation must not simply be residualized away to make technology effects disappear.

Useful V77 audit scripts in the S174 snapshot include:

- `scripts/v77/audit_v77_context_shortcuts.py`
- `scripts/v77/audit_v77_historical_spillover.py`
- `scripts/v77/build_v77_extended_truth.py`
- `scripts/v77/build_v77_extended_rna_observer.py`
- `scripts/v77/build_v77_fullscale_multiome_observer.py`
- calibration/envelope builders under `scripts/v77/`.

External regulatory evidence history worth knowing:

PR #164 is a separate reconnaissance lane for GSE174367 RNA/ATAC. Its key result is that direct microglial ATAC measurement is conditionally independent and unused, while Stage75F RNA-derived candidate edges are circular with respect to an RNA-based predictor. It also documents no cell-level RNA/ATAC pairing, 18 shared donors, and the need for structurally distinct negative controls. This is useful evidence history; it is not current authorization to run protected benchmark evaluation.

---

## 8. Corrected synthetic replay — current scientific gap

Primary document:

`custody/takeover_20261008/s174_working_snapshot/docs/agent/S174_SYNTHETIC_REPLAY.md`

Machine-readable:

- `.../results/v77/s174_replay/S174_SYNTHETIC_REPLAY_V1.json`
- `.../results/v77/s174_replay/S174_SYNTHETIC_REPLAY_SIDE_BY_SIDE_V1.json`

Every committed replay runner was first rerun on the old universe and reproduced its old receipt exactly, then rerun unchanged on the corrected universe. No seed, arm, preprocessing or scoring rule was tuned after seeing corrected real values.

No candidate is selected.

The most important current gap is **class separation**:

- corrected real `T5 within-class / pooled correlation ratio ~= 0.7435`;
- replayed synthetic arms are roughly `1.02-1.21`;
- current synthetic hidden substates were generated independently of broad annotated cell class.

Therefore the current synthetic family does not reproduce the real contribution of broad cell-class structure to pooled dependence.

The 12-fold dynamic-range arm comes close to some corrected detection density/degree values but still misses other topology, abundance and depth properties. It is an observation, not a winner.

---

## 9. The next scientific design — Lane C owns this

Do **not** add more optimizer steps now. Runtime should stop drifting unless a new failing regression exposes a genuine mechanics defect.

The next prospectively designed synthetic family should test:

`broad cell class -> class-shared biological programs -> within-class continuous/substate biology -> fixed observation operator -> counts`

Initial arms should include at least:

1. class-shared program only;
2. class-shared + within-class continuous state — leading initial hypothesis;
3. class-shared + current substate mechanism.

Hold observation/counting fixed initially so biological latent structure is isolated from measurement-process redesign.

Evaluate jointly, not only T5:

- expression correlation geometry;
- detection correlation/topology;
- class separation;
- abundance distribution;
- depth/detected features;
- transitivity/community structure;
- shortcut readouts/source/operator predictability.

Do not optimize only one pooled statistic.

Before implementation:

1. write a prospective scientific design document;
2. state what would falsify each arm;
3. freeze seeds/arm definitions/statistics before reading new outcomes;
4. explicitly label corrected real point estimates as descriptive references unless/until S159 provides valid threshold authority;
5. keep the exact-twin negative control;
6. keep nuisance/source/operator shortcut controls;
7. preserve the 42/42 operator 2K support rule if the observation operator is reused.

---

## 10. What the new agent must NOT resurrect

Do not restore or promote:

- historical fixed `.996` as current V5 EMA authority;
- 16,249 presentations as a selected production half-life;
- old `CurrentTrainingAuthorityV2` / `OptimizerGuardV4` implementations as a second runtime stack;
- removed inactive-runtime step guard;
- generic donor rehearsal path;
- legacy dict EMA persistence;
- PR #223 old V5 runtime copies;
- V1 runtime proof as mutation-promotion authority;
- old scrambled S149 numbers as corrected evidence;
- pooled S149 ~89% coverage share;
- S159 recentered thresholds;
- raw source/operator IDs as learned biological covariates;
- automatic SCENIC+/ATAC independence;
- seed-7302 worlds as independent confirmation;
- old PROD41K/T1 checkpoint as current training evidence;
- calibration-closure small-scale sampler that loses observation operators;
- a full rich-teacher realization target that the partial student cannot identify.

---

## 11. Important local / large artifacts and custody

Exact-hash custody manifest:

`docs/agent/archive/chat_runtime_20261007/JEPA_RUNTIME_INTERFACE_CHAT_CUSTODY_MANIFEST_20261007.json`

Prior exact-hash custody commit:

`cb7a98d00359eecece8525b23c43fbc8578c69ef`

Important chat/local artifacts recorded there include:

- `WSL execution issue.txt`;
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`;
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`;
- checksum CSV;
- `checkpoints.zip`;
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`;
- `expression.zip`;
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`;
- `t1_checkpoint_u0200.zip`;
- `Status and Repair Plan.txt`.

Reassembled 41K expression ZIP SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Large binary policy: do not insert multi-hundred-MB scientific bytes into normal Git history. Use exact hashes, manifests and recovery provenance. Hash identity is not scientific validity.

Historical local forensic package:

`D:/Jepa project/CONTEXTUAL_TEACHER_TARGET_V1_CODEX_PACKET_V2`

Classification: forensic reference only, not current teacher/EMA authority.

The old PROD41K/T1 checkpoint is forensic-only because the historical fp16 lineage contained 48 gradient-dead mandatory tensors.

---

## 12. Data/cache paths the next agent will need

Lane B local cache paths:

- old defective cache: `data/cache/stage81a3r_corrected_real_train`
- corrected cache: `data/cache/s174_rebuilt_real_train_v1`

Lane B source H5ADs are described and hash-frozen in `results/v77/S174_REBUILD_FREEZE_V1.json` inside the S174 snapshot. Do not substitute files by name alone; verify hashes.

Corrected replay result root:

`custody/takeover_20261008/s174_working_snapshot/results/v77/s174_replay/`

Spillover audit root:

`custody/takeover_20261008/s174_working_snapshot/results/v77/spillover/`

Runtime mutation implementation/tests remain top-level on the PR #237 lineage; do not execute runtime from inside the S174 snapshot.

---

## 13. Required working discipline

For any decision-changing change:

1. prospectively write RED requirement or preregistration;
2. commit it;
3. observe intended failure when the claim is mechanical/testable;
4. make the smallest repair;
5. run focused tests;
6. run broader regression/governance CI;
7. adversarially self-audit;
8. run historical spillover checks;
9. record exact workflow run and SHA;
10. update the takeover/handoff record.

Never call a local pytest run "GitHub CI". Never call a receipt executed unless an executor actually ran. Never equate authenticated provenance with biological validity.

---

## 14. Hard boundaries at takeover

Still active:

- `TRAINING=OFF` for real data;
- `STAGE_A_EXECUTION=OFF`;
- `MULTIMODAL_TRAINING=OFF`;
- `500K=NOT_AUTHORIZED`;
- `STAGE4=NOT_AUTHORIZED`;
- `TEST=SEALED`;
- `MORABITO=PROTECTED`;
- no production EMA half-life selection;
- no target freeze;
- no representation freeze;
- no additional mutation budget merely because the one-step rehearsal passed.

---

## 15. Immediate next-work checklist for the new agent

### Lane A — runtime

- Treat current runtime as frozen/maintenance-only.
- Verify PR #237 and PR #236 heads before any edit.
- Do not add a second optimizer step.
- Only reopen runtime mechanics if a new scientific design exposes a concrete failed mechanics regression.
- Keep teacher/student/EMA/checkpoint lineage unchanged unless a prospective RED test proves a defect.

### Lane B — S174

- Treat corrected replay as completed and use corrected results for current evidence.
- Keep old results immutable for history.
- Do not silently rename old corrupted results as corrected.
- Keep G1 failed; G1b is the successor justification.
- Preserve the 353 Ensembl/symbol remappings as an explicit unresolved identity-governance issue.
- S159 remains open; if Lane B continues statistically, design a valid donor/estimand uncertainty procedure prospectively rather than recentering current intervals.

### Lane C — Macha/science

- Start with a design-only successor branch; do not implement immediately.
- Read corrected S174 real points and synthetic replay first.
- Design class-shared biological programs + within-class heterogeneity while initially keeping the observation/count process fixed.
- Preserve exact-twin and nuisance/source/operator negative controls.
- Define multi-statistic falsification criteria prospectively.
- Only after design review/preregistration should a new synthetic generator/world be implemented.
- If later mutation is scientifically justified, consume Lane A's existing frozen guarded mutation contract/runtime; do not recreate it.

---

## 16. Takeover bottom line

The project is no longer blocked on "can the runtime physically perform one update?" That question is GREEN for exactly one tiny synthetic guarded update.

The project is no longer allowed to use the old Stage81A3R scrambled real-TRAIN calibration as biological evidence. Corrected S174 replays materially changed the scientific interpretation.

The main open problem is now **scientific**: construct a synthetic biological state model that represents broad cell-class programs and within-class heterogeneity without reintroducing observation-operator shortcuts, then test it against the corrected real-data geometry under prospectively frozen criteria.

Keep the three lanes separate while doing so.
