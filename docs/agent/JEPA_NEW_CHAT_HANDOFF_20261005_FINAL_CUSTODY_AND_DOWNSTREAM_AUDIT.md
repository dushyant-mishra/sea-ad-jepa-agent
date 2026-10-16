# JEPA new-chat handoff — final 2026-10-05 custody + downstream-pipeline audit

## Read this first

This handoff supersedes action routing contained in older October-5 chat artifacts. Historical documents remain valuable as evidence, but the live project frontier has moved.

The project is currently split into **three deliberately separate workstreams**:

1. **V77 synthetic-world qualification (Macha lane):** finish the repaired 41,238-address B/C/D/E rebuild and complete the frozen recoverability/oracle matrix. This is simulator qualification, not model training and not production-target selection.
2. **Downstream-pipeline audit (next agent / Sol lane):** identify and mechanically qualify the actual 41,238-address execution path from input registry through masking, encoder/predictor/EMA, gradients, checkpointing, resume and representation extraction. Repair implementation defects but do not authorize training.
3. **Real-RNA target qualification (separate future lane):** prospectively freeze and run the TRAIN-only, zero-encoder-update, zero-EMA-update discrimination gate for the real teacher-target candidates. Synthetic results cannot select the production target.

**TRAINING remains OFF. 500K remains NOT AUTHORIZED. Stage 4 remains NOT AUTHORIZED. TEST remains SEALED. Morabito remains PROTECTED. No production target or representation winner exists.**

---

## 1. Live main and authority freshness

Verified at handoff time:

`main = 874939b5e9dd34a4f195dcc163db90e9dd3eee11`

This is the authority-freshness merge:

> Merge authority freshness governance — Keep the canonical startup surface synchronized with the actual project frontier and guard against completed tasks remaining advertised as current.

The earlier terminal target-lineage reconstruction was merged at `3d70167800369fb4f6b335563712576a8cb6c1f3`.

### Standing governance rule

**Canonical authority/startup surfaces must move with the project frontier.** When a controlling task closes or the next authorized task changes, update the startup pointer/authority surfaces in the same change set or an immediate successor. Do not leave a completed task advertised as current.

---

## 2. Current hard scientific boundaries

V75 100K measurement architecture is qualified only within its declared scope.

Exact status:

`PASS__100K_MEASUREMENT_ARCHITECTURE_QUALIFIED__500K_PROMOTION_INDETERMINATE`

Therefore:

- 100K measurement architecture: qualified within scope;
- 500K: `NOT_AUTHORIZED`;
- learned-state scaling ladder: stopped;
- production teacher target winner: `NONE`;
- training: `OFF`;
- multimodal training: `OFF`;
- Stage 4: `NOT_AUTHORIZED`;
- recoverability TEST: `SEALED`;
- Morabito: `PROTECTED`.

Do not infer a training/model claim from the measurement-architecture result.

---

## 3. Representation and checkpoint authority

### `cell_state`

`cell_state` exists architecturally but is **not qualified as the designated global biological state**.

### `width=160`

`width=160` is model/token capacity, not evidence that biology is 160-dimensional.

### Gene/block state

Gene/block states can be architectural objective targets without thereby becoming the global biological state.

### Online versus EMA

Downstream scientific authority between online and EMA representations remains unresolved.

### Historical checkpoints

There is **no trained checkpoint for the current architecture**. Historical T1/PROD41K checkpoints are forensic artifacts only and must not be used as current biological authority or warm starts for prospective qualification.

The historical PROD41K/T1 lineage had a reproduced fp16 training-mechanics defect: the loss could fall while all 48 mandatory pre-attention tensors were gradient-dead. Any future downstream audit must explicitly guard against recurrence.

---

## 4. Terminal production-target conclusion

The terminal target-lineage reconstruction is complete and merged.

Governing conclusion:

**No production teacher target is qualified.**

PR #163 defined `T_A`, `T_B1`, `T_B2`, `T_C` plus residual modifier `T_D`, exposed query leakage and numerous shortcut seams, and selected no target.

PR #178 found the corrected synthetic T_A/T_B comparison `NOT_INFORMATIVE`; the synthetic fixture could not legitimately select the real biological target.

Historical results whose original deciding receipt could not be recovered must retain the qualification:

`RECONCILED_HISTORY__ORIGINAL_RECEIPT_NOT_RECOVERED`

Do not silently upgrade them to independently re-executed primary evidence.

---

## 5. Governing premise reset

The project must keep these distinctions explicit:

`observable RNA != recoverable RNA structure != biological state != transferable biological state != causal state`

The project has historically mixed three goals:

1. recover reproducible transcriptomic structure from incomplete RNA;
2. learn a transferable biological coordinate system across donors/studies/technologies;
3. learn mechanistic structure suitable for regulatory/counterfactual prediction.

Success at #1 does not prove #2. Success at #1 and #2 does not prove #3.

The appropriate initial claim is therefore closer to **recoverable/predictable transcriptomic or molecular state**, unless independent evidence later qualifies stronger biological, regulatory or causal language.

### Six premise gates

- **P1 Target meaning:** define what the target means independent of architecture.
- **P2 Recoverability:** measure what lawful partial observations can contain; nonrecoverable biology is not automatically model failure.
- **P3 Structured state:** compare global, query-local, program and structured-combined representation families without pre-selecting one.
- **P4 Technical identifiability:** separate biology from identity/source/operator/depth/support/missingness/normalization and biology×operator effects.
- **P5 Transport estimand:** specify donor/operator/study/technology transfer and the population/weighting the foundation representation is meant to serve.
- **P6 Claim boundary:** separate RNA representation, transferable biological state, regulatory support and causal prediction.

Claim levels remain:

1. `RNA_REPRESENTATION`
2. `TRANSFERABLE_BIOLOGICAL_STATE`
3. `REGULATORY_SUPPORT`
4. `CAUSAL_PERTURBATIONAL_PREDICTION`

No automatic promotion.

Representation families remain:

- `GLOBAL_CELL_STATE`
- `QUERY_LOCAL_STATE`
- `PROGRAM_STATE`
- `STRUCTURED_COMBINED_STATE`

No default winner.

---

## 6. Premise-contract implementation state

Approved design:

`docs/superpowers/specs/2026-10-05-premise-qualification-contract-design.md`

Original design commit:

`40e4543ff37c91de5b98b9fb5e26c511d6a80537`

Implementation plan:

`docs/superpowers/plans/2026-10-05-premise-qualification-contract.md`

plan commit:

`4fa973b53cd1280e23624045416d281c24090008`

Original branch:

`design/premise-qualification-contract-20261005`

was observed at `4de21f682afad8397a0cb63f81b569ecdb30c867` with the first RED Task-1 test. It descends from an older main lineage and **must be reconciled with current main before further use** rather than blindly resumed.

Important audit corrections that must survive any successor implementation:

- Stage-A contract is prefreeze-only until estimand/threshold/split decisions close; do not call the existence of a file execution authority.
- On real RNA distinguish `TARGET_OBJECT_RECOVERABILITY` from true `BIOLOGICAL_TRUTH_RECOVERABILITY`; the latter requires independent ground truth.
- Treat donor/operator/study/technology transfer as separate evidence axes where nesting/confounding does not justify a simple scalar ladder.
- Stage A can establish a lawful, nonshortcut RNA representation candidate; biological semantics need independent evidence.
- Any fitted diagnostic readout must be fit only on an inner TRAIN partition, frozen before held-out evaluation, and forbidden from changing target meaning after seeing results.
- Rare/novel signal on real RNA is initially rare/novel RNA structure or candidate biological novelty unless independent evidence supports stronger language.

The implementation plan still requires Tasks 1–7 sequentially and then a genuinely independent Task-8 whole-branch review before merge. Task 5 should **reuse** existing external-asset audits from PRs #188–#199 rather than repeat them. Task 6 must present estimand choices while leaving the selected estimand `UNSET_REQUIRES_APPROVAL`.

---

## 7. V77 synthetic-world status — important correction

Do not repeat the earlier mistake that B/C/D are merely 96-feature worlds.

World A remains locked at 96 features and should be classified only as a reduced measurement/metric control world.

However, **B/C/D/E had already been implemented at 41,238 addresses** at:

`9840cafe51309cade9a88889c66bdba666bf2eee`

The canonical-observer realism upgrade was then developed at:

`4e95aac41222fdf67faa29f86f4221021b566acc`

The v2 observer uses real registry identifiers in frozen tokenizer order, but planted synthetic modules are assigned without gene-symbol knowledge. A synthetic effect landing on `APOE`, `TSPAN6`, etc. creates no biological claim about that named gene.

### v2 realism improvements

The v1 observer was correctly criticized as potentially a small simulator wearing a 41K coat. Macha audited and improved it. Reported changes included:

- abundance max/median: 9.6× → 27,514×;
- top 1% of addresses carrying counts: 4.9% → 32.4%;
- address detect-rate SD: 0.044 → 0.218;
- never detected addresses: 0 → 11,972/41,238;
- pathway redundancy: none → chained overlapping families;
- 60 sparse background covariance programs across the full address space.

The registry itself supplies source-family measurement support. Reported structural coverage included HVS ~45.4%, NPH52 ~86.2%, SEA-AD ~86.8%, 17,569 addresses common to all three and 9,990 unique to one. This enables genuine structural unmeasurement rather than arbitrary dropout constants.

The reported abundance ratio exceeds the originally stated 100–10,000× band and was correctly recorded as an exceedance rather than post-hoc re-banded. Likewise measured family overlap ~0.32/0.37 remains below the declared 0.45 and should remain reported as measured.

### Identity-use caveat

Random planted biology on real identity slots may be acceptable for **training a synthetic model from scratch**, provided no semantic claims about the gene names are made.

It is **not automatically valid for evaluating a checkpoint trained on real biology**, because that checkpoint already carries learned gene-identity semantics. A separate prospective identity-use contract is required before such evaluation.

---

## 8. V77 sparse oracle and component-specific statistics

The old oracle was a dense 96-feature reader and was not suitable for 41,238-address v2 data. A naïve 41,238-feature OLS at ~2K cells would be p≫n and could manufacture interpolation ceilings.

A sparse successor was implemented and merged into Macha's lane. The qualified pattern is:

- reconstruct CSR counts;
- normalize by full cell library;
- CPM + `log1p`;
- project only onto prospectively planted module-address sets;
- never densify the 41,238-address matrix;
- densify only the small cells×modules product;
- fail closed on malformed indices, indptr, duplicate/out-of-range addresses, empty modules and zero-library cells.

Mechanical fix:

`(X @ membership).toarray()`

on the small cells×modules matrix only.

### Critical interpretation

Every such ceiling is:

`ORACLE_CEILING_UNDER_KNOWN_SUPPORT`

because module memberships are supplied from truth. It is an upper bound under perfect module discovery, **not a blind achievable ceiling** for a model that must discover those modules.

### Universal reader is not universal

Macha's audit found the module-score reader is appropriate by default for 8/13 components, but several components require component-specific sufficient statistics:

- B4 transient: score the symmetric transient band, not pseudotime itself;
- C1: full-versus-additive recoverability gap;
- C2: local multiplicative/ratio statistic;
- C3: biology×operator coupling via library/support statistics;
- D1 graph: graph/ranking recovery with explicit negatives, not a generic module R².

---

## 9. V77 defects S124 and S125

### S124 — inert C3 latent

C3 truth emitted `z_bioqc` while the v2 observer initially did not consume it. This reproduced the same class of inert-latent error previously caught elsewhere. It was repaired and must remain in the defect history.

Reported post-repair signal:

`|corr(z_bioqc, library)| ≈ 0.0988`

versus World A reference ~0.0086.

### S125 — vacuous off-twin

The first off-twin implementation removed the component from truth. Its statistic then did not run, and “did not run” was initially counted as rejection. That was a control that could pass without measuring anything.

Correct off-twin semantics:

- retain the truth latent;
- retain planted module allocation;
- use the same seed;
- keep module-address sets byte-identical;
- suppress only the component's observation contribution;
- run the same statistic on the same addresses;
- require the statistic to collapse toward its null band.

Do not revert to a `--components`-removed truth twin.

---

## 10. V77 current verified freeze/status commit

Verified commit:

`d028aef25a4d0d8ca87d638ec6f3eda0307656c4`

Message:

`V77: freeze component statistics, prove detect/reject, record C2 as a construction failure`

This commit states that statistics were frozen before the deciding rebuild and discloses previous smoke observations rather than pretending blindness.

Reported controlled results:

| Component | Statistic | Signal | Off-twin | Criterion | Detect | Reject |
|---|---|---:|---:|---|---|---|
| B4 | R²(band) | 0.3812 | -0.0202 | [0.25, 0.45] | PASS | PASS |
| C1 | full−additive gap | 0.0737 | -0.0237 | >0.05 | PASS | PASS |
| C2 | R²(ratio) | 0.1525 | -0.0033 | [0.40, 0.60] | FAIL | PASS |
| C3 | max |corr| | 0.0988 | 0.0151 | >0.05 | PASS | PASS |

Detect 3/4, reject 4/4.

C2 is currently a **construction failure**, not a model failure. Its band was not moved. A stopping rule now permits at most two further construction attempts; if it still fails, withdraw it from the battery rather than re-band it.

Current status from that commit:

`SPARSE_LOADER_QUALIFIED__COMPONENT_STATISTICS_FROZEN_AND_CONTROLLED__FULL_V2_REBUILD_PENDING`

Still pending/not claimed:

- full B/C/D/E rebuild at production cell counts;
- complete recoverability matrix;
- D1 graph recovery;
- model evaluation.

Model evaluation is not authorized yet.

---

## 11. Synthetic dataset does not currently need a JEPA teacher target

The user explicitly narrowed the current concern to the synthetic dataset itself.

Agreed position:

**The synthetic simulator does not currently need a JEPA teacher target in order to finish its qualification.**

First finish:

- planted ground truth;
- component semantics;
- designed recoverability classes;
- component-specific statistics;
- oracle ceilings;
- off/null controls;
- production-count rebuild.

Only if/when a synthetic JEPA training rehearsal is later authorized do teacher/student views and a teacher representation target become necessary.

If that later rehearsal happens, do not use planted truth as the optimization target. Prefer normal JEPA mechanics—teacher richer lawful observation, student partial observation, student predicts teacher representation—while planted synthetic truth remains the independent answer key used to judge whether the learned representation recovered the intended factors and rejected shortcuts.

Synthetic truth must never select the real production teacher target.

---

## 12. Real production-target work remains separate

The open production-target question is a separate real-RNA TRAIN-only gate with:

- encoder optimizer updates = 0;
- EMA updates = 0;
- TEST sealed;
- Morabito protected;
- target constructions prospectively frozen;
- absolute leakage controls;
- absolute shortcut controls;
- biological-unit uncertainty;
- representation-family neutrality.

Candidates remain `T_A`, `T_B1`, `T_B2`, `T_C`, with `T_D` only as its defined modifier.

Do not let synthetic V77 results rank or select these targets.

---

## 13. NEW PRIORITY: downstream-pipeline audit

This is the main next workstream requested from this environment while Macha completes V77.

Dedicated audit-start document:

`docs/agent/JEPA_DOWNSTREAM_PIPELINE_AUDIT_START_20261005.md`

### Preliminary signal

A default-branch code search did not expose an obvious single canonical entrypoint for `optimizer.step`, `torch.save`, `run_update`, or `teacher_student_runtime`. This is **not proof of absence**—the code may be historical, versioned, generated or unindexed—but it is enough to require a repository/history trace before any checkpoint rehearsal.

Previous inspection also suggested that at least one repaired successor update primitive hot-patches a historical update path rather than constituting a clean standalone current training pipeline. Do not assume the newest-looking versioned file is the canonical execution path.

### Downstream audit sequence

The successor should audit in this order:

1. 41,238-address registry identity, frozen order and tokenizer mapping.
2. Loader and normalization path: sparse/dense assumptions, count/log transforms, support/missingness, zero-library behavior.
3. Teacher/student masking and view construction, including query-value and normalization leakage.
4. Encoder path and exact tensor/representation outputs.
5. Predictor and teacher-target construction path.
6. EMA teacher initialization/update ordering/decay/dtype/device mechanics.
7. Optimizer parameter groups and actual gradient flow; explicitly prove required tensors receive valid gradients.
8. Mixed precision, attention numerics, scaler/autocast and the historical fp16 failure class.
9. Checkpoint serialization: online encoder, EMA teacher, predictor, optimizer/scaler where needed, RNG states, update count, registry/tokenizer/config/masking digests, split/data provenance.
10. Save/load and resume equivalence.
11. Representation extraction API: online vs EMA; global/cell; query-local/gene; program-level; no implicit `cell_state` authority.
12. Evaluation isolation: planted truth/module sets/oracle statistics remain answer-key-only and cannot leak into optimizer inputs/teacher target.
13. Synthetic checkpoint-ladder readiness, prospectively freezing initialization/early/mid/late/final rather than selecting checkpoints post hoc.
14. CI/workflow/entrypoint mapping and explicit marking of legacy/superseded execution paths.
15. Sweep for hard-coded 96-feature, 700-gene, old target-panel or other historical dimensional assumptions.
16. Update canonical authority surfaces whenever a discovered repair changes the actual project frontier.

Suggested per-component audit states:

- `CURRENT_AND_VERIFIED`
- `CURRENT_BUT_UNVERIFIED`
- `LEGACY_FORENSIC_ONLY`
- `SUPERSEDED`
- `DEFECT_CONFIRMED__REPAIR_REQUIRED`
- `MISSING_CANONICAL_SUCCESSOR`
- `INDETERMINATE__EVIDENCE_REQUIRED`

Do not treat “nothing obvious found” as a PASS.

### Condition before any synthetic checkpoint run

A synthetic pipeline/checkpoint rehearsal should not start until **both**:

1. V77 simulator/oracle qualification reaches a frozen admissible state; and
2. the downstream audit identifies and mechanically qualifies a coherent execution/checkpoint path.

If later approved, the synthetic checkpoint run is a known-truth rehearsal of training mechanics and representation recovery. It is not a production-target qualification and not real-biological validation.

---

## 14. Current-chat artifact custody audit

Twelve files were physically present in this chat runtime.

Ten are exact byte-for-byte matches to the prior October custody manifest by both byte count and SHA-256 and therefore are **not** duplicated:

- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `Status and Repair Plan.txt`
- `WSL execution issue.txt`
- `checkpoints.zip`
- `expression.zip`
- `t1_checkpoint_u0200.zip`

Prior custody reference:

`handoff/jepa-20261005-historical-audit-custody@8a84a8e7882a047de598a2f25243ef44011ff8fa`

manifest:

`docs/agent/archive/chat_runtime_20261005/CHAT_RUNTIME_CUSTODY_MANIFEST_20261005_V1.json`

The two files genuinely unique to this final chat runtime are:

- `Pasted text.txt` — 35,941 bytes — SHA-256 `152bb05c84d7ebcbcc8b1ee9094100a96cc9e10d64eedf4600e868a4ba3f27e0`
- `Pasted markdown.md` — 27,543 bytes — SHA-256 `53f85c2ca3d01f6957b25ca13285bac21eb7dd13b48f62ad398e6080b0e20a66`

The first is historical October-5 handoff/authority-reset context. The second is the deep premise audit that materially informed the current six-gate framework.

### Integrity qualification

A Git connector base64/text preservation attempt was independently checked against the local source bytes and **failed byte identity**. The non-identical tree entry was deleted. This handoff therefore does not make the false statement that Git contains an exact copy of those two source files.

Instead, their exact byte counts and SHA-256 values are bound in:

`docs/agent/archive/chat_runtime_20261005_final/CHAT_RUNTIME_CUSTODY_MANIFEST_20261005_FINAL.json`

The source bytes should be retained externally from this chat export/archive if exact byte recovery is required. The scientific content that matters for project continuation is incorporated into this handoff and the premise-governance documents.

Custody does not create scientific authority.

---

## 15. What not to do

Do not:

- start production JEPA training;
- start synthetic checkpoint training before V77 + downstream audit readiness;
- authorize 500K or Stage 4;
- unseal TEST or Morabito;
- warm-start current work from T1/PROD41K;
- call `cell_state` qualified biological state;
- call width 160 biological dimensionality;
- call oracle-under-known-support a blind achievable ceiling;
- let planted synthetic truth/module membership enter the optimization target;
- use synthetic V77 to choose the real production teacher target;
- interpret nonrecoverable biology as model failure;
- move numeric thresholds after deciding results;
- treat donor holdout as universal cross-technology state;
- treat ATAC/SCENIC+ association as causal proof;
- silently erase S124/S125 or C2's current construction failure;
- silently revive stale authority routing;
- accept a custody copy without verifying byte identity.

---

## 16. Immediate takeover sequence

**First:** read current `main` and verify it is still `874939b...` or identify any newer merge before acting.

**Second:** keep Macha's V77 lane independent. Check whether the full v2 production-count rebuild and ceiling matrix have landed after `d028aef2`; audit any new result against the frozen statistics and S124/S125 semantics before accepting it.

**Third:** resume the downstream-pipeline audit from `docs/agent/JEPA_DOWNSTREAM_PIPELINE_AUDIT_START_20261005.md`. Do not begin by writing a new trainer. First identify the real current/historical runtime lineage, entrypoints and interface contracts, then classify each component as current, legacy, defective, missing or indeterminate.

**Fourth:** repair only reproducible downstream defects using test-first / fail-closed changes. The first high-value checks are the 41K input/tokenizer contract, masking/leakage path, gradient-flow path, EMA ordering and checkpoint serialization/resume semantics.

**Fifth:** keep the real-RNA target gate separate. Resume the premise-contract governance work only after reconciling its branch with live `main`; do not treat its partially executed TDD branch as current authority simply because files exist there.

**Sixth:** if V77 and downstream mechanics both qualify, prospectively design the synthetic checkpoint-ladder rehearsal. Only then consider turning training on for that explicitly scoped synthetic experiment.

---

## One-sentence takeover instruction

**Preserve TRAINING OFF; audit any post-`d028aef2` V77 rebuild against the frozen synthetic rules, and in parallel perform a fail-closed downstream execution audit from the canonical 41,238-address input through masking, encoder/predictor/EMA, gradient mechanics, checkpoint save/load/resume and representation extraction, repairing reproducible defects and removing legacy ambiguity before any synthetic checkpoint rehearsal is authorized.**
