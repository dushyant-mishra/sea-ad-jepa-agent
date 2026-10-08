# JEPA new-agent handoff — post V77 ZERO_UPDATE join + S174 repair/replay

Status: **COLD-START TAKEOVER GUIDE — NON-AUTHORIZING**  
Date: 2026-10-07  
Handoff branch: `handoff/jepa-20261007-post-v77-s174-takeover`  
Scientific/runtime base for this handoff: PR #228 head `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`  
This document records the state after the runtime/interface audit, V77 joined ZERO_UPDATE work, executed q-safety work, physical provenance hardening, and the S174 real-TRAIN cache repair/replay.

## 0. Executive state

There are now **three separate lanes** and they must not be collapsed:

1. **Canonical runtime/interface lane** — PR #224 + PR #226. This owns the current teacher/student/predictor/optimizer/EMA/checkpoint mechanics and proof semantics. Do not rebuild these components elsewhere.
2. **Joined V77 qualification lane** — PR #228. This joins the V77 synthetic adapter to `QualificationBatchV1`, executed q-safety, and the canonical V5 ZERO_UPDATE path. Latest verified head is `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`; GitHub Actions run `37680819156` is GREEN.
3. **Real-TRAIN S174 repair lane (Macha)** — `claude/s174-train-cache-rebuild-20261007`. Latest verified head at this handoff is `c9975b24f3332a5ba3001890a15f6959e903b5f4`. The scrambled Stage81A3R cache was rebuilt by fresh gene-ID join and the nine affected V77 real-data results were replayed. S149 is now corrected.

Nothing in this handoff authorizes production training, Stage A, TEST, Morabito, 500K, Stage 4, target freeze, representation freeze, uncertainty-model freeze, deciding thresholds, or production EMA half-life selection.

Standing hard state:

- `TRAINING=OFF`
- `STAGE_A_EXECUTION=OFF`
- `MULTIMODAL_TRAINING=OFF`
- `500K=NOT_AUTHORIZED`
- `STAGE4=NOT_AUTHORIZED`
- `TEST=SEALED`
- `MORABITO=PROTECTED`

The only possible next mutation authority, if remaining gates close, is the already-preregistered **tiny bounded synthetic rehearsal**. It is not yet production authority.

---

## 1. Read order for a new agent

Read these in this order before changing code:

### A. Full prior takeover/custody

1. `docs/agent/JEPA_NEW_AGENT_FULL_TAKEOVER_HANDOFF_20261007.md` on `handoff/jepa-20261007-runtime-interface-custody` / PR #227.
2. `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md` on the same branch.
3. `docs/agent/archive/chat_runtime_20261007/JEPA_RUNTIME_INTERFACE_CHAT_CUSTODY_MANIFEST_20261007.json`.

These contain the earlier full historical audit: runtime lineage, V47/V48/V63 science lineage, teacher/partial-student identifiability correction, historical row-binding failures, observation-operator regression, scientific-asset custody, and exact-hash local artifact inventory.

### B. Current V77/runtime wiring audit

4. `docs/agent/JEPA_V77_RUNTIME_WIRING_AUDIT_20261007.md` on `handoff/jepa-20261007-v77-wiring-audit`.
5. PR #228: `integrate/v77-qualified-zero-update-20261007`.
6. `.github/workflows/v77-qualified-zero-update-join.yml`.
7. `docs/superpowers/plans/2026-10-07-v77-qualified-zero-update-join.md`.

### C. Current S174 repair/replay

8. Branch `claude/s174-train-cache-rebuild-20261007`, head `c9975b24f3332a5ba3001890a15f6959e903b5f4`.
9. `docs/agent/S174_REPLAY_SUMMARY.md` on that branch.
10. `results/v77/s174_replay/S174_REPLAY_SIDE_BY_SIDE_V1.json` (SHA-256 recorded in the summary: `ffc2cd36d6463aede69e63f0dd1c068f21fc837ca1436831105bbc0fe263fbcc`).
11. The S174 register addenda, especially addendum 5 (value verification) and addendum 6 (repair/corrected replay state).

Do not use old S149 numbers after this point except as historical corrupted-input results.

---

## 2. Canonical runtime/interface authority

### PR #224 — canonical V5 runtime

Branch: `reconcile/canonical-v5-runtime-successor-20261006`  
Accepted runtime checkpoint: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`

Canonical low-level path:

`authenticated bounded input -> V5 keyed online/student encoder -> V4 predictor -> frozen teacher target -> mechanics-only loss -> backward -> unscale if AMP -> gradient validation -> guarded AdamW step -> physical completion assertion -> guarded presentation-normalized EMA -> completed update proof -> authority-bound checkpoint -> physical write -> SHA verification -> verified reload`

Important facts already audited:

- online/student is V5 `KeyedIPBEncoderV2Reference`;
- teacher is a parameter-identical deep copy of the authenticated student at initialization, frozen/eval, then advanced only by guarded EMA;
- predictor remains inherited V4 `BlockPredictor` mechanics;
- AdamW owns online encoder + predictor parameters only;
- teacher targets are computed under `torch.no_grad()`;
- optimizer completion must be proven before EMA;
- skipped/rejected/incomplete optimizer update cannot advance teacher;
- presentation-normalized EMA uses successful base-cell presentations as teacher age;
- historical fixed `.996` is **not** current production authority;
- candidate `16,249` presentations is **not selected/frozen** production half-life;
- checkpoint state binds online/predictor/teacher/optimizer/scaler/cursor and typed continuation/provenance;
- V1 runtime proof is diagnostic only; it cannot promote mutation proof.

Do not resurrect old `CurrentTrainingAuthorityV2` / `OptimizerGuardV4` historical copies or old generic rehearsal paths if they are not the canonical current implementation.

### PR #226 — shared qualification V2

Branch: `reconcile/shared-qualification-v2-on-canonical-runtime-20261007`  
Head: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`  
Base: runtime checkpoint `9d00684e...`

This is the clean successor to old PR #223 and deliberately does **not** transplant #223's older `src/sea_ad_jepa/v5/*` copies.

Key properties:

- oracle realization binding;
- challenge partition preservation;
- evaluation authorization enforcement;
- distinct retry identities;
- CI trigger coverage;
- preflight partition validation;
- real RNA cannot execute under synthetic authority;
- generic callbacks do not prove physical zero mutation;
- policy declarations do not prove executed transitive q-safety;
- V1 runtime proof cannot promote mutation proof;
- typed V2 physical continuation is the only runtime mutation-promotion route.

---

## 3. What was audited and repaired in PR #228

PR: #228 `Join V77 to qualified ZERO_UPDATE runtime`  
Branch: `integrate/v77-qualified-zero-update-20261007`  
Base: #226 head `e83bb8d90...`  
Latest verified head: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`  
GitHub Actions run: `37680819156` — **GREEN**.

### Files currently added/changed by the integration lane

- `.github/workflows/v77-qualified-zero-update-join.yml`
- `docs/superpowers/plans/2026-10-07-v77-qualified-zero-update-join.md`
- `scripts/v77/v77_synthetic_batch_adapter.py`
- `src/sea_ad_jepa/qualification/v77_join.py`
- `src/sea_ad_jepa/qualification/v77_zero_update.py`
- `src/sea_ad_jepa/qualification/v77_bound_zero_update.py`
- `src/sea_ad_jepa/qualification/v77_physical_binding.py`
- `tests/integration/test_v77_joined_zero_update.py`
- `tests/integration/test_v77_executed_q_safety.py`
- `tests/integration/test_v77_canonical_zero_update.py`

### A. Historical source/runtime spillover audit

Before implementation, the current branch was checked against #224/#226 history and older handoffs.

Result:

- PR #228 does **not** replace current V5 teacher/student/predictor/EMA sources;
- the V77 adapter itself contains no second optimizer/EMA/checkpoint loop;
- the canonical runtime still constructs student, frozen teacher copy, predictor and optimizer;
- integration work is confined to adapter/join/proof/ZERO_UPDATE surfaces.

A historical branch named `integrate/v77-qsafe-runtime-successor-20261007` exists. Treat it as forensic evidence only. Do not merge it blindly.

### B. Executed q-safety RED -> GREEN history

These exact transitions were recorded so future agents can distinguish actual execution proof from policy metadata:

- RED `0d393d296ea5168e739fc4c3a5768e22844852d7`: policy-only q-safety could not count as executed proof; no gate existed.
- GREEN `0618e639fb2f124790e5fa3bf206fca0c971ff3a`: fail-closed policy-only rejection added.
- RED `6d891e51eec5494441200c00940ad8f428edab7d`: bare `PROVEN_BY_BOUND_ADAPTER_RUNTIME` enum could spoof proof.
- GREEN `1a4f2e8ebca66ed0c63fa4b1b4f2bcf03dd86dcb`: typed `BoundAdapterQSafetyProofV1` required.
- RED `0ceac519e1bab1578a25e3f6d4ee800f41d978d0`: typed proof replayable across adapter/batch/runtime.
- GREEN `74f2b99d827e16134bf02c1820958442b78c37ee`: proof bound to exact adapter identity/digest, batch scientific identity digest and runtime source digest.

### C. V77 -> shared batch bridge

- RED `3fe29343bd415bd18a5d1c27f85ccd21eeed44a0`: actual V77 `SyntheticConversion` had no physical route to `QualificationBatchV1`.
- GREEN `8e631460f3c286f46e34139431c990ec687ecb52`: physical bridge added.

The bridge binds:

- explicit ordered feature identity;
- structural measurement support;
- query/evidence masks;
- source/operator rosters and mapping;
- donor grouping;
- adapter digest;
- observer manifest digest;
- split identity;
- target identity.

Visibility separation:

- learnable/model-visible: `gene_ids`, `student_expression`, `measurement_mask`, `hidden_target_mask`;
- lawful context may include reviewed physical summaries like `visible_library_size`, `n_measured`;
- `source_index` / `operator_index` remain provenance and are filtered out before learnable context;
- donor identity is split-only;
- `query_counts` and `full_library_size` are readout-only.

### D. Executed hidden-query perturbation

The executed q-safety test uses two physical V77 synthetic conversions that differ only at hidden query readout values.

Required invariants:

- hidden readout changes;
- model-visible digest remains identical;
- lawful operator-context digest remains identical;
- mask/support/global observation identity remain fixed;
- query values remain readout-only;
- hidden query values do not perturb student normalization or QC/depth descendants;
- no raw source/operator identity reaches learnable model context.

All required q-safety channels receive typed execution evidence. Proof remains `execution_authorized=False`, `training_authorized=False`, `production_promotable=False`.

### E. Canonical V5 ZERO_UPDATE bridge

`src/sea_ad_jepa/qualification/v77_zero_update.py` executes a canonical teacher/student/predictor forward path while forbidding mutation.

It uses the actual inherited runtime constructor from `sea_ad_jepa.v5.inactive_update_reference.build_reference_modules` and hashes the exact physical runtime source manifest.

Required receipt invariants:

- checkpoint digest before == after;
- optimizer step before == after == 0;
- teacher presentations before == after == 0;
- online parameters unchanged;
- teacher parameters unchanged;
- predictor parameters unchanged;
- optimizer state unchanged;
- no optimizer step;
- no EMA;
- no training authorization.

A physical V77 adapter source binding was added so a caller cannot substitute an arbitrary adapter digest while presenting the same logical batch.

### F. Sept-8 provenance hardening

Historical failures required stronger coupling than "metadata hash matches".

V1 already rejected:

- source/global-row mismatch;
- selected local/block-row mismatch;
- source/logical cell mismatch;
- consumed-value digest mismatch.

The current GREEN head adds a V2 physical binding surface that additionally binds:

- logical donor == source donor;
- matrix slot == authenticated matrix slot;
- feature-space digest == authenticated feature-space digest;
- payload location == authenticated payload location;
- authenticated payload digest;
- authenticated values == consumed values.

This is specifically intended to prevent:

- reset-index substitution;
- correct digest / wrong row;
- correct metadata / wrong expression values;
- correct logical row / wrong physical payload;
- correct cell / wrong donor;
- correct row / wrong matrix slot;
- correct row / wrong feature-space interpretation.

Latest GREEN integration checkpoint: `6282b59c...`.

---

## 4. Historical failure modes that MUST remain in the regression suite

### TD23/TD33 row addressing failure

Historical B-side `sample_row` was reset to local `0..24999`. Treating it as global expression row produced a false relationship near `0.3906061`; using the correct global row produced ~`0.0062546`.

Any old analysis without proven B-side global addressing is `ROW_BINDING_UNVERIFIED`.

### Sept-8 physical row/value failure

Authenticated file/payload metadata is insufficient if consumed expression values come from the wrong physical row.

Required chain:

`source row coordinate + block-local selection + logical cell/donor identity + matrix slot + feature-space identity + payload location/digest + physically consumed values`

must resolve to one inseparable proof chain.

### Smoke-scale observation-operator regression

Old calibration-closure lineage silently removed stress-twin's zero-quota rescue:

- 2K: stress-twin 42/42 operators min1; calibration-closure 36/42 min0;
- 10K: stress-twin 42/42 min1; calibration-closure 41/42 min0;
- 100K: both 42/42 min4;
- 500K: both 42/42 min20;
- FULL104-scale 4,553,407: both 42/42 min179.

Because 2K smoke is the gate to later rehearsal, **all 42 operators must be explicitly present at smoke scale** before any bounded synthetic mutation run.

---

## 5. S174 real-TRAIN cache defect and repair

This is a separate real-data lane, not part of PR #228.

### Defect

Old cache:

`data/cache/stage81a3r_corrected_real_train`

The word "corrected" referred to collision handling, not gene-axis correction.

The cache builder applied a frozen HVS/SEA-AD provenance table indexed in Ensembl-ID order to physical H5AD columns in genomic order. That scrambled HVS/SEA-AD gene identities.

NPH52 came through a separate path and did not share this defect.

### Value verification

S174 was first inferred from code/provenance, then value-verified with a prospectively preregistered TRAIN-only read-only probe.

Probe preregistration commit: `7b597a59f1df607a090e2f2f0621f739ed354bc6`.

Value-verification record: `976d2be6c8cfaf46e7dfd79bf900fb9fc4c0d4bd`.

36 cells, 12 each from one HVS and two SEA-AD matrices:

- HVS positional/scrambled agreement 1.0000; true-gene ID agreement 0.0298; decoder 1.0000;
- SEA-AD MTG positional/scrambled 1.0000; true-gene ID 0.0249; decoder 0.9990;
- SEA-AD DFC(A9) positional/scrambled 1.0000; true-gene ID 0.0240; decoder 0.9991.

Named markers made the defect obvious (e.g. real MBP/PLP1/SNAP25 values missing at their nominal cache addresses because those slots held unrelated genes).

### Rebuild

Repair branch: `claude/s174-train-cache-rebuild-20261007`.

Freeze commit before reading counts: `cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef`.

New cache:

`data/cache/s174_rebuilt_real_train_v1`

Policy:

- fresh physical H5AD gene-ID join;
- old positional mapping never used;
- genuine collisions remain excluded/unresolved, never guessed or summed;
- old cache untouched;
- NPH shards copied byte-identically;
- same TRAIN cells.

Original frozen G1 failed because the simple reread did not account for 897 frozen SEA-AD remappings. This was not retroactively changed to PASS.

A successor gate G1b was prospectively frozen and authorized at commit `4ab8e2101f2e595d9a97df05517d6e672768ecec` after demonstrating:

- HVS exact reread match;
- all non-remapped SEA-AD addresses exact;
- every remapped entry equals the physical source count specified by frozen authority;
- 100% of G1 discrepancies confined to the known remap set;
- zero unexplained discrepancies;
- rebuilt artifact hashes unchanged.

353 historical Ensembl-ID -> different-symbol mappings remain an identity-governance issue. The replay follows the frozen identity authority and does not tune them after outcomes.

### Corrected replay

Latest repair/replay head: `c9975b24f3332a5ba3001890a15f6959e903b5f4`.

Corrected files are under:

`results/v77/s174_replay/`

Old files in `results/v77/` remain untouched for history.

Key summary:

`docs/agent/S174_REPLAY_SUMMARY.md`

Side-by-side numeric artifact:

`results/v77/s174_replay/S174_REPLAY_SIDE_BY_SIDE_V1.json`

Key corrected S149 findings:

- pooled fraction |r| > 0.3: `0.6148 -> 0.1348`;
- coverage-only null: `0.5463 -> 0.0042`;
- share of strong-correlation fraction reproduced by coverage null: `0.8885 -> 0.0314` (~89% -> ~3%);
- pooled median |corr|: `0.377 -> 0.1946`;
- null median |corr|: `0.3273 -> 0.013`;
- HVS within-cohort strong-correlation fraction: `0.0768 -> 0.1083`;
- NPH52: `0.0312 -> 0.2078`;
- SEA-AD: `0.0602 -> 0.2319`;
- coverage-strata agreement remains 1.0.

Interpretation:

- the old headline "pooled dependence is mostly cohort-composition artifact" **does not survive**;
- the coverage-strata identity finding survives;
- the claim that within-study dependence is several times weaker reverses under corrected inputs;
- S149 status is **CORRECTED**, not simply "failed" or "withdrawn".

Other corrected geometry:

- expression-envelope median |corr| `0.3291 -> 0.0562`;
- expression pairs |r|>0.3 `0.5621 -> 0.0242`;
- top-10-PC variance `0.5089 -> 0.262`;
- topology T5 mean within-class median |corr| `0.3329 -> 0.0418`;
- evaluation universe `19,569 -> 14,417`, shared `11,230`, Jaccard `0.4935`.

This corrected expression geometry is close to the original synthetic generator's ~0.0675 median correlation and ~2.3% pairs above 0.3. Therefore the old V77 Step-3 background search, factor-family falsification and Observer-V2 decision — which were judged against the corrupted targets — must be re-scored prospectively without tuning to the corrected outcome.

---

## 6. Macha/V77 science lane — what remains valid

The synthetic S157 conclusion remains valid for its stated design question:

- exact same-assay RNA semantic twins remain `NON_IDENTIFIABLE_BY_DESIGN`;
- source/operator identity is only a shortcut positive control, not biology;
- q-safety / adapter conclusions are not invalidated by S174;
- the identity of the evaluation-universe addresses was contaminated historically, but S157's core conclusion does not depend on which particular addresses occupy that universe.

Do not tune away the S157 negative result.

The preregistered tiny bounded synthetic mutation experiment remains **unexecuted** unless a later Macha commit explicitly changes that state. Before execution, its runtime/interface fields must be filled from the reviewed current runtime/integration contract, not from old #223 or old #224 snapshots.

---

## 7. Scientific principles that remain binding

### Rich teacher / partial student identifiability

A richer teacher is desirable, but a partial-RNA student cannot be required to reproduce teacher-private realization-level information it never observes.

For deterministic squared error, the student can at best learn the conditional expectation of the target given its admitted evidence.

Therefore:

- full rich-teacher realization matching is not generally scientifically identifiable;
- score shared/predictable components, or use distributional/uncertainty/abstention semantics where required;
- the runtime deterministic teacher-block loss is a **mechanics fixture only**, not scientific target authority.

### Technology / observation operator

Technology should be modeled as an observation process, not a biological covariate.

Potential lawful descriptors include measurement support, chemistry/platform class, measured vocabulary, depth/detection summaries and acquisition noise characteristics.

Raw dataset/source/operator IDs and unrestricted donor/dataset embeddings must not become production model covariates without explicit future scientific authority.

### External evidence

Do not assume ATAC, SCENIC+, spatial, genetics or protein evidence is automatically independent. Audit construction, pairing and circularity explicitly.

SCENIC+ built partly from the same RNA cannot automatically count as independent confirmation.

---

## 8. Local scientific assets / custody references

Large scientific bytes are intentionally not duplicated into ordinary Git history. Use the custody manifests and hashes before trusting local copies.

Prior exact-hash custody commit:

`cb7a98d00359eecece8525b23c43fbc8578c69ef`

Expression-parts reassembly SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Project/chat environment files that may exist locally and are referenced by custody records:

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `checkpoints.zip`
- `expression.zip`
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
- `t1_checkpoint_u0200.zip`
- `WSL execution issue.txt`
- `Status and Repair Plan.txt`

Do not assume these bytes are current production authority. The old PROD41K/T1 checkpoint is forensic-only because the historical fp16 lineage had 48 gradient-dead mandatory tensors.

Historical local path mentioned in custody:

`D:/Jepa project/CONTEXTUAL_TEACHER_TARGET_V1_CODEX_PACKET_V2`

contains old teacher-target scripts such as `student_singleton_predictor_ema_direct.py` and q-context variants. These are forensic references only.

---

## 9. What NOT to resurrect

Do not reintroduce:

- historical fixed `.996` V5 EMA as production authority;
- `16,249` presentations as a selected half-life;
- old inactive runtime step guards;
- generic rehearsal paths that bypass canonical runtime proof;
- old #223 runtime copies;
- V1 runtime proof as mutation authority;
- caller-supplied arbitrary adapter/runtime hashes as proof;
- raw source/operator/dataset IDs as learnable covariates;
- old pooled S149 numbers as current evidence;
- S159 recentered thresholds as current authority;
- V63 nuisance success as exact-twin biological proof;
- automatic SCENIC+/ATAC independence;
- old PROD41K/T1 checkpoints as current training evidence;
- calibration-closure smoke lineage that erased operators at 2K/10K.

---

## 10. Immediate next tasks for the new agent

### Runtime/integration lane

Start from PR #228 head `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`.

Do **not** modify canonical teacher/student/EMA/checkpoint code unless a failing regression demonstrates a genuine defect.

Next steps:

1. **Final historical spillover scan** on the exact PR #228 head:
   - alternate/direct `optimizer.step()` paths;
   - direct teacher/EMA mutation outside guarded runtime;
   - old guards/authorities reachable from joined path;
   - V1 proof promotion;
   - unverified checkpoint/reload route;
   - hidden private implementation imports;
   - hard-coded `.996` defaults in reachable path;
   - raw source/operator IDs reaching encoder/predictor;
   - query/readout values or full-library descendants reaching learnable context.

2. **Inspect exact tensors/context entering encoder and predictor** in ZERO_UPDATE, not only declarations. Confirm only intended model-visible objects are consumed.

3. **Smoke-scale operator-support gate**: before any mutation rehearsal, prove all 42 observation operators have nonzero support at 2K using the stress-twin zero-quota rescue lineage.

4. **Freeze exact identities** only after the above are GREEN:
   - runtime source manifest/digest;
   - #226 shared-interface SHA;
   - PR #228 adapter/join/ZERO_UPDATE SHAs;
   - V77 synthetic world/realization manifest;
   - workflow/test SHA.

5. Only then hand those frozen fields to Macha's already-preregistered tiny bounded synthetic mutation experiment.

### S174 / real-data lane

Start from `claude/s174-train-cache-rebuild-20261007@c9975b24f3332a5ba3001890a15f6959e903b5f4`.

Next work is not another cache rebuild. The corrected cache/replay is done.

The next scientific job is to **re-score the downstream V77 decisions that depended materially on the old real-data calibration targets**, especially:

- Step-3 background-search rounds;
- factor-family falsification verdicts;
- Observer-V2 decision.

Rules:

- no tuning on corrected outcomes;
- preserve original outputs and corrected outputs side by side;
- state explicitly which old conclusions survive, reverse or become unqualified;
- keep 353 historical ID/symbol remappings flagged for a separate identity-governance lane.

### Science/design lane

Still unresolved and separate from runtime mechanics:

- select biological estimand;
- donor/source weighting;
- repair/validate any remaining S159/bootstrap inference authority;
- teacher shared/private/uncertainty target semantics;
- external validation independence/pairing for Nott/ATAC/SCENIC+/spatial/genetics/protein;
- numeric representation dimension authority (do not promote 160D merely because architecture can use it).

---

## 11. Gate before tiny bounded synthetic mutation

Minimum required GREEN state:

- V77 adapter -> `QualificationBatchV1` physically executed;
- executed q-safety typed proof bound to exact adapter/batch/runtime;
- canonical ZERO_UPDATE teacher/student/predictor forward path executes;
- no online/teacher/predictor/optimizer mutation;
- no optimizer step or EMA;
- physical provenance V2 attacks fail closed;
- V1 runtime proof cannot promote;
- no alternate optimizer/EMA/checkpoint path reachable;
- no raw source/operator leakage to learnable parameters;
- all 42 observation operators present at 2K smoke scale;
- exact SHAs frozen prospectively.

Only then may Macha run the preregistered small **synthetic** arms (BIO/planted biological signal, exact RNA semantic twin, operator-linked nuisance twin, query-leak negative, clean negative) under identical initialization/runtime/update budget/context/visibility/scoring.

Loss reduction alone is not success. The scientific question is whether learned representation behavior distinguishes biological structure from nuisance beyond what is possible from admitted observations.

---

## 12. Reporting vocabulary

Use exact labels where appropriate:

- `GREEN_MECHANICS`
- `POLICY_ONLY_NOT_EXECUTION_PROVEN`
- `PROVEN_BY_BOUND_RUNTIME`
- `DEVELOPMENT_CALIBRATION`
- `NEEDS_REPAIR`
- `NON_IDENTIFIABLE_BY_DESIGN`
- `ROBUST_TO_MODELED_NUISANCE`
- `SUPPORTIVE_BUT_NOT_IDENTIFYING`
- `UNQUALIFIED`
- `FORENSIC_ONLY`
- `SUPERSEDED`

Do not call local tests GitHub CI. Do not call a receipt execution unless an executor ran. Do not equate provenance authentication with biological validity. Do not call a candidate threshold/EMA timescale frozen just because a JSON file exists.

---

## 13. Workflow discipline for the next agent

For every bounded change:

1. write prospective RED contract/test;
2. commit it;
3. observe the isolated failure through the actual workflow that is supposed to cover it;
4. implement the minimal repair;
5. run focused tests;
6. run broader regression/governance CI;
7. adversarial self-audit;
8. historical spillover check;
9. record a durable checkpoint/receipt;
10. verify remote SHA and distinguish local evidence from GitHub CI.

Do not reconstruct large source files from truncated API responses. Use exact blobs/minimal patches. Earlier in this work, an incomplete fetched view temporarily caused a source reconstruction error; the exact prior blob had to be restored. Treat that as a standing operational warning.

---

## 14. Current canonical pointers at handoff

- PR #224 accepted runtime checkpoint: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
- PR #226 shared interface: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
- PR #228 GREEN joined ZERO_UPDATE head: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- PR #228 GitHub Actions run: `37680819156` — success
- Prior runtime/interface custody PR #227 head (historical reference): `2708c8870cd32bdf0cd607829c5572af0ee32d46`
- V77/S157 scientific custody lineage: `claude/v77-synthetic-premise-custody-20261005`
- S174 rebuild/replay branch: `claude/s174-train-cache-rebuild-20261007`
- S174 current replay head: `c9975b24f3332a5ba3001890a15f6959e903b5f4`
- S174 G1b authorization/freeze: `4ab8e2101f2e595d9a97df05517d6e672768ecec`
- S174 value verification: `976d2be6c8cfaf46e7dfd79bf900fb9fc4c0d4bd`
- S174 preregistration: `7b597a59f1df607a090e2f2f0621f739ed354bc6`
- prior exact-hash chat/runtime custody: `cb7a98d00359eecece8525b23c43fbc8578c69ef`

This handoff is documentation only. It does not itself authorize execution beyond the explicit gates described above.
