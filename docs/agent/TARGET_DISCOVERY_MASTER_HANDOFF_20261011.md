# Target Discovery — Master New-Agent Handoff — 2026-10-11

Status: **ACTIVE REAL TARGET-DISCOVERY LANE**

Hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the primary takeover document for the target-discovery program. It is intentionally broader than the immediate G6 runbook: it carries the scientific objective, foundation/data role architecture, historical target-discovery evidence, audit corrections, exact code/data identities, current custody authority, PR #275 governance state, Macha operating instructions, and the downstream decision tree.

Read this file before touching PR #282, PR #275, PR #277, corrected expression values, TD56/57/59, TD60, target selection, Stage4, or training.

---

## 1. What this project is actually trying to build

The long-term objective is a JEPA-style biological representation learned from partial RNA evidence while preserving a high-resolution **Molecular Ledger**. The system is not supposed to collapse into hidden-gene regression, a generic cell classifier, a dataset/source predictor, or a single CELL embedding that erases useful molecular state.

The durable architecture is:

- **Molecular Ledger:** fine molecular evidence/state.
- **Biological state:** reproducible/shared biological structure without erasing legitimate donor biology.
- **Technology / acquisition:** an observation operator, not a biological covariate or a free dataset embedding.
- **Uncertainty:** biological-evidence uncertainty and measurement/depth uncertainty remain separate.
- **OOD:** biological novelty/support and measurement-domain OOD remain separate.
- **Transfer ladder:** donor -> matrix -> dataset/study -> technology.
- **Sampling:** donor-primary / source->donor->cell hierarchy; large SEA-AD cell count must not define the biological target.
- **Stable subspace over named axes:** exact latent coordinates do not receive scientific authority merely because they are reproducible.

The current target idea is an **incumbent hypothesis, not a winner**:

`T(c,q) = { Z_shared(c), R_broad/meso(c), Z_query(c,q), Support(c,q), U_bio(c,q), U_meas(c,q), optional Specialist(c,q) }`

where:

- `Z_shared(c)` is emergent shared biology with no named-coordinate authority;
- `R_broad/meso(c)` is donor-local broad/mesoscale relational order;
- `Z_query(c,q)` is measured q-conditioned non-q same-cell context with q-excluded normalization and q address only on the student side;
- support/missingness is explicit; unsupported targets abstain and measured zero remains valid;
- `U_bio` and `U_meas` remain separate;
- chromatin/regulatory information is optional specialist evidence only if independently qualified.

No modality is forced to impute another modality merely to fit a universal target.

---

## 2. Foundation dataset and role architecture

The source families are public research datasets: HVS, NPH52, and SEA-AD. Dataset-role restrictions in this project are **scientific exposure firewalls**, not claims that the data are confidential/private.

Frozen foundation split:

- 149 TRAIN
- 19 DEV
- 19 SEALED

Nested reader roles inside TRAIN:

- 104 fit
- 22 validation
- 23 oracle

Historical inventory:

- lawful full-149 inventory: 6,351,753 cells
- broader physical inventory: 6,374,468 rows
- 22,715-row NPH difference quarantined historically

Donor is the biological replicate unit. Do not convert repeated cells, queries, or case rows into biological N.

DEV/SEALED/pathology restrictions remain exposure rules for scientific validity. Protected pathology/outcome information does not define the target during discovery.

---

## 3. Original T1 result and why target discovery reopened

T1 optimized its training objective extremely well but failed the intended biological mechanism.

Historical T1 endpoint:

- u205 loss approximately `0.006142`

Mechanistic 2,464-query work showed that authenticated **u0 already contained correct-cell query-local context** and T1/u205 could erode it at higher evidence levels.

Mean correct-vs-wrong relative improvements for u0 at 20/40/60/80% evidence:

- `0.290496`
- `0.316317`
- `0.518179`
- `0.655603`

At 60/80%, all 8/8 continuous programs beat wrong-cell; against the query-specific null, 8/8 passed at 60/80%.

u205-u0 deltas at 20/40/60/80%:

- `-0.020588`
- `-0.001314`
- `-0.073158`
- `-0.119406`

At 60%, 6/8 were worse; at 80%, 8/8 were worse and none improved.

Lesson: the next target should preserve/expose lawful query-local biological context that already exists in the observation, not invent a generic low-loss latent.

Historical shortcut/calibration work also showed that source/address/operator information could explain nearly all variance in some learned representations. Low JEPA loss and noncollapse are therefore never sufficient biological evidence.

---

## 4. Query-conditioned measured target history (R5)

A more defensible developmental teacher-target was created for a cell `c` and query gene `q` using **other measured genes in the same cell**.

Teacher target:

`a_T(c,q)[j] = log1p(10000 * k_c,N(q)[j] / sum(k_c,N(q)))`

with an eight-gene `N(q)` panel, excluding the queried scalar `q` from values and normalization.

Rules:

- unsupported / empty panel -> abstain;
- measured zeros remain valid;
- student sees complementary RNA plus q address, not q scalar;
- q scalar cannot leak through values, normalization, QC descendants, or copied embeddings;
- q-excluded teacher is a mandatory ablation.

Historical developmental held-out R²:

- q-specific: `0.4300`
- technical+q: `0.3496`
- q-agnostic: `0.2760`
- q-count-only: `0.1610`

This is useful developmental evidence, not current target authority.

Mandatory falsifiers/baselines remain: constant, technical/operator, address/support shortcut, matched wrong-cell, fine-neighborhood wrong-cell, q-count-only, q-address-only, q-agnostic, wrong-q, technical+q, q-excluded teacher, identity+support.

---

## 5. Target-discovery progression before the relational program

TD13-TD36 explored gene loadings, dependency structures, global and class-conditioned subspaces, and generic clustering. These families did not produce robust recurrent biological targets. Some apparent positives were later invalidated by reset-row aliasing.

TD37-TD55 established that exact coordinates and proxies were fragile, while relational order/concordance was substantially more stable. Unresolved ties were treated as uncertainty rather than biological equality.

Do not reopen dead coordinate/loading/subspace target families without a materially new hypothesis.

---

## 6. Historical relational target-discovery evidence

### TD41 / TD43

Pair order/concordance showed strong relational signal and reliable measurement. This helped motivate relational rather than coordinate-level targets.

### TD56

Two disjoint gene views recovered the same within-donor cell-cell relational geometry across HVS/NPH52/SEA-AD.

Historical examples of observed versus null p95:

- HVS `0.7975611` vs `0.5541568`
- NPH52 `0.8007195` vs `0.5990585`
- SEA-AD `0.8782250` vs `0.7526606`

Historical interpretation: evidence for a shared relational invariant, not a target winner.

### TD57B

Historical prospective result: **24/24 PASS**.

Weakest observed-minus-null-p95:

`+0.0375178074843`

Weakest observed-minus-null-max:

`+0.0326836261591`

### TD57C

Historical immutable terminal:

`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`

HVS Panel-0 nearest-third fine-local test failed 2/4. The same X/Y unrestricted geometry passed 4/4, so this is a locality-specific failure.

Never rescue, average away, or relabel this historical failure. A future corrected PASS would mean historical/corrected divergence and requires a fresh prospective locality experiment.

### TD58

Historical result: 60% partial evidence reproduced the relational target in 24/24 cases.

### TD59

Prospectively froze a nearest-half mesoscale test; historical result **24/24 PASS**.

Weakest p95 margin:

`+0.0011566307718604563`

22/24 historical cases exceeded null max.

Nearest-half is a historical frontier/bracket, not a production constant.

The original TD59 executor SHA `326848...` remains unrecovered. The validated replay-closure successor is:

`870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`

Never describe that successor as the original executor.

### TD60

Current status:

`PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`

TD60 was intended as a learned-teacher continuity bridge. It has never qualifyingly executed and must never be called failed.

---

## 7. Critical historical row-binding rule

The 50K discovery freeze is stacked A then B:

- Sample A global rows `0..24999`
- Sample B global rows `25000..49999`
- Sample B `sample_row` resets to `0..24999`

The required historical rule is:

`global_row = np.arange(len(freeze_csv))`

assigned **before filtering or merging**.

CSR access must use this explicit global freeze-file row, never a post-merge DataFrame index and never generic sample-local `sample_row`.

TD23 demonstrated reset-row aliasing. TD31A/31B/32 apparent positives were invalidated by this family of errors. TD33 became the durable guard:

`PASS_GLOBAL_ROW_BINDING__RESET_INDEX_FORBIDDEN`

Primary references:

- `target_discovery/HANDOFF_CURRENT_20260907.md`
- `target_discovery/iterations/TD30_TD36_CLOSURE_LEDGER.md`
- `target_discovery/iterations/td33_global_row_binding_guard/TD33_SUMMARY.json`

---

## 8. Physical feature-mapping defect and why corrected replay is mandatory

The historical TRAIN substrate used for TD56/57B/57C/59 was later shown to have corrupted HVS/SEA-AD physical feature mapping.

This does **not** erase historical evidence. It does mean those results cannot by themselves authorize the current target.

Corrected S174 substrate SHA-256:

`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

Historical recovery established:

- exact historical 50K CSR recovered;
- important historical executors recovered;
- historical-only local replays reproduce archived outputs for TD56 HVS/NPH52/SEA, TD57B P0/P1 HVS/NPH52, and TD57C P0 HVS;
- TD57C historical FAIL reproduced;
- NPH52 remains an authenticated historical pass-through, not rematerialized;
- zero duplicate CSR indices were found in 1,310 NPH Sample-A rows and in all 25,000 Sample-A rows;
- TD59 original executor remains genuinely unrecovered and uses the validated replay-closure successor above.

Recovered executor SHA-256 identities:

- TD56 HVS: `a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43`
- TD56 NPH52: `090134f0cc129559286f06d80a31a880c07c9841a7ef3f446b914a78c8cd7162`
- TD56 SEA exact-fast: `c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866`
- TD57B executor: `1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`
- TD57B exact-fast wrapper: `808fb293a87d0020adc0f332742f3fa9b99c9c8ec5a88e50504a719ad4183a70`
- TD57C executor: `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`

Do not claim the coordinator newly reran every heavy SEA TD57B historical case; historical self-audit records exact-fast replay closure.

---

## 9. Historical and uploaded data custody identities

### Historical expression split / CSR

- part001 SHA-256: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002 SHA-256: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- assembled ZIP SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- inner historical NPZ SHA-256: `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

CSR member SHA-256:

- `data.npy`: `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`
- `indices.npy`: `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`
- `indptr.npy`: `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`
- `shape.npy`: `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`

### Important recovered/support bundles

- corrected S174 substrate: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`
- foundation calibration bundle: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- TD41-TD58 archive: `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`
- Sample-A freeze: `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
- provenance: `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`
- collision ledger: `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`
- Macha/S174 rebuild freeze: `240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`: `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356`
- `expression.zip`: `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- `checkpoints.zip`: `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- `t1_checkpoint_u0200.zip`: `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`: `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`

Do not commit large binary copies merely for convenience. Preserve canonical files and exact hash manifests.

---

## 10. Corrected-replay interpretation is already frozen

Controlling document:

`docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`

Interpretation rules:

- TD56 PASS + TD57B PASS + TD57C FAIL + TD59 PASS -> broad/meso relational program consistent with the historical scale bracket; may advance, **not a winner**.
- TD56/B PASS + TD57C FAIL + TD59 FAIL -> broad/global only.
- TD56 PASS + TD57B FAIL -> no stronger donor-recurrent scale-free order; TD59 cannot rescue.
- TD56 FAIL -> stop relational promotion.
- corrected TD57C PASS -> historical/corrected divergence; run a fresh prospective locality experiment.
- source disagreement -> no universal source replication; no averaging/free source embedding rescue.
- not estimable -> `NOT_ESTIMABLE__NO_BIOLOGICAL_PASS`.

Even the strongest corrected replay does not authorize TD60, target selection, Stage4, or training.

---

## 11. PR #259: accepted G4/G5 value-blind mapping state

PR #259 is an accepted narrow technical/data-integrity PASS.

Important pins:

- execution head: `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- executed code: `bf253a4dd62d943398f9ff59ed8b1e74777140a5`
- driver/preflight receipt SHA-256: `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping receipt SHA-256: `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA-256: `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Accepted scope:

- 35 frozen HVS/SEA H5AD byte sources authenticated;
- 34 Sample-A matrices;
- Sample A = 25,000 cells: HVS 1,129 / NPH52 1,310 / SEA-AD 22,561;
- 9,216 replay addresses resolve one-to-one on all 34 Sample-A matrices;
- expression arrays were not opened.

PR #259 does not establish corrected biological recurrence.

---

## 12. G6/G7 custody lineage

### Historical qualified predecessor: PR #277

Qualified implementation:

`fafd4309cc086c95076cefdc94064e8b66e58ae4`

Historical qualification:

- focused suite: 217 passed / 0 failed / 0 skipped
- PR259 physical compatibility: 1 passed / 0 skipped / 0 failed

Code identities at `fafd4309`:

- common: `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6: `614af59cf6f4f0a8910235fcdef8b8b3ec1aae47ecf98c30bfaa3eaa1b3a07ad`
- G7: `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

Historical owner decision SHA-256:

`36599b7ade189e051b6e156d53ea1acd4caf42794f26b152d7eada0513a1a273`

Historical runtime authorization SHA-256:

`7cc66f601d6fc294ef9255f4e9ac4b1e1f16db56d1ddf52cf1fb839646fc91fa`

### First real G6 attempt at `fafd4309`

All preconditions passed and a start marker was created. G6 then failed before opening any H5AD value array because the authenticated Sample-A freeze does not physically store `global_row`:

`AttributeError: 'DataFrame' object has no attribute 'global_row'`

Canonical classification:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

Start-marker SHA-256:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

No receipt. No corrected H5AD value read. No biological result.

Historical namespace:

`D:\jepa_td_real_g6_20261011\G6_OUT_fafd4309`

Preserve it indefinitely and never reuse/repair in place.

Audit lesson: synthetic fixtures had copied the consumer's desired schema instead of the external producer schema, so they hid a real interface defect. Metadata/schema/global-row checks must occur before the attempt-spending marker wherever possible.

---

## 13. PR #282: current qualified executable G6 successor

Branch:

`fix/td-g6-global-row-binding-successor-20261011`

Exact qualified implementation:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Repair behavior:

- derives historical `global_row` from exact freeze-file position when not physically stored;
- binds row identity before filtering/merging;
- validates required production metadata columns;
- validates TD50 sentinel/global-row coverage and historical CSR bounds;
- performs metadata/schema/global-row/TD50/CSR checks before `G6_EXECUTION_START.json`;
- does not open H5AD count/value arrays during those pre-spend checks.

### Failed predecessor qualification preserved

Head:

`7e482cf50f73a5cecda16482777129dd3ca725a6`

Qualification result:

- focused suite: 4 failed / 215 passed
- authenticated real Sample-A gate: PASS
- PR259 compatibility: PASS

All four failures were stale synthetic fixtures missing newly required real G6 schema fields. This was not a real-data failure.

Evidence is immutable at:

`qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

Owner/auditor ruled: preserve the stronger production schema contract and repair only the stale fixtures.

### Fresh qualification at `ff4a21f9`

The fixture repair changed only:

- `tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py`
- `tests/v5/test_td_v2_sample_a_row_order.py`

Production common/G6/G7 scripts were unchanged from the repaired successor lineage.

Fresh evidence:

- qualification branch: `qual/td-g6-global-row-successor-ff4a21f9-20261011`
- evidence commit: `8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`
- focused suite: **219 passed / 0 failed**
- authenticated Sample-A: `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`
- real Sample-A: 25,000 rows; SEA-AD 22,561 / NPH52 1,310 / HVS 1,129
- no physical `global_row`; derived rows exactly `0..24999`
- exact PR259 compatibility: **1 passed / 0 skipped / 0 failed**
- worktree clean before and after
- no H5AD value read and no G6/G7 execution during qualification

Qualified code identities:

- common: `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6: `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`
- G7: `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

Qualification terminal:

`QUALIFIED_FOR_REPLACEMENT_G6_INTEGRITY_EXECUTION__NO_BIOLOGICAL_AUTHORITY`

---

## 14. Current owner/runtime authority: replacement G6 only

Audit branch:

`audit/target-discovery-takeover-20261011`

Owner decision:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json`

Physical SHA-256:

`3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`

Runtime authorization:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Operational authorization:

`EXECUTE_REPLACEMENT_G6_ONCE_AT_ff4a21f9__FRESH_NAMESPACE__STOP_FOR_EXTERNAL_AUDIT`

**Current operational truth at this handoff:** replacement G6 is authorized but has not yet produced a new accepted execution namespace. G7 is not operationally authorized.

---

## 15. Macha's immediate task

Macha should execute replacement G6 exactly once from a fresh clean detached worktree at exact:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

under the fresh owner/runtime files above, into a new never-used output namespace.

### Before creating the output namespace / marker

Verify:

- exact HEAD and clean worktree;
- common/G6/G7 code SHA identities above;
- owner decision physical SHA;
- runtime authorization physical SHA;
- PR259 driver/preflight `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`;
- PR259 mapping `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`;
- replay manifest `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
- Sample-A freeze `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`;
- provenance `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`;
- collision ledger `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`;
- S174/Macha freeze `240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c`;
- TD artifacts ZIP `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`;
- historical CSR member hashes from §9;
- all frozen H5AD byte sources required by PR259;
- destination namespace has never existed.

Do not weaken production checks merely to satisfy fixtures or convenience.

### One-shot custody rule

Once `G6_EXECUTION_START.json` exists, preserve every outcome. Any exception, mismatch, STOP, NOT_ESTIMABLE-equivalent custody terminal, or non-PASS after marker creation spends that namespace. Do not repair/delete/rerun it in place.

Expected successful terminal:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Expected exact success file set:

1. `G6_EXECUTION_START.json`
2. `G6_RECEIPT.json`
3. `MANIFEST.json`
4. `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz`
5. `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz`

Expected accounting:

- HVS + SEA-AD physical reread: 23,690
- NPH52 authenticated historical pass-through: 1,310
- total Sample A: 25,000

On PASS, hash all five artifacts and report:

- exact branch/head;
- exact command;
- environment;
- output namespace;
- terminal;
- all five SHA-256 values;
- source-authentication accounting;
- physical-value-read accounting;
- warnings;
- whether any precondition or source identity differed from freeze.

**STOP AFTER G6. DO NOT RUN G7.**

Macha must not run corrected TD56/57B/57C/59, TD60, target selection, representation selection, Stage4, or training.

---

## 16. What the next agent must do after Macha returns G6

The next agent's first job is **external audit of the actual G6 namespace**, not immediate G7 execution.

Audit:

1. exact five-file set and no unexpected replacement files;
2. all SHA-256 values;
3. start-marker semantics and one-shot custody;
4. receipt/manfiest schema and authority flags;
5. source authentication and H5AD physical-read accounting;
6. 9,216 value/meta output dimensions and semantic consistency;
7. NPH52 pass-through accounting;
8. code/head/authority binding;
9. warnings or partial reads;
10. confirm no downstream action occurred.

Only if the external audit accepts G6 should a fresh operational G7 authorization be issued.

G7 must compare authenticated physical H5AD values against authenticated S174 values. The G6 cache is prerequisite custody evidence only; it is not the physical counterpart.

After G7 PASS and external acceptance, issue a **separate owner decision** for corrected TD56/TD57B/TD57C/TD59 biological replay under the already frozen interpretation contract.

---

## 17. PR #275: current target-tournament governance state

PR #275 is a separate **synthetic/metadata-only governance lane**. It is not the current real-data critical path.

Exact current qualified head:

`0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`

GitHub Actions qualification:

- run `38183565983`
- job `114601031751`
- artifact id `11718374988`
- artifact digest `sha256:585f7799e0aba4935b37b28319570025de67ecf73d9aa7523a5bf6abeb74de61`
- **197 passed / 0 failed / 0 errors**
- clean checkout before and tracked worktree clean after

Terminal:

`PASS_FULL_SYNTHETIC_METADATA_ONLY_V2_AUTHENTICATED_REGISTRY_TO_ADJUDICATION_CHAIN_197_OF_197`

The qualified prospective V2 chain is:

`V2 contract + execution context + authenticated candidate×gate governance registry -> externally pinned V2 prefreeze -> exact gate-case coverage -> gate evidence artifact -> full candidate evidence manifest -> candidate receipt -> tournament adjudication`

The execution context freezes SHA identities for:

- executor code;
- gate-executor registry;
- gate-estimand registry;
- gate-decision-rule registry;
- population;
- donors;
- sources;
- operators;
- support;
- teacher/student evidence rights;
- splits;
- observation descriptor;
- corrected-replay evidence.

The authenticated registry covers every candidate×gate role and binds one executor, one estimand, and one decision rule per role. Candidate-manifest construction authenticates the registry against the frozen execution context, derives those identities internally, requires the full frozen gate set, and no longer accepts free posthoc expected maps.

Important preserved RED->GREEN lineage:

- V2 adjudicator: initial 10/10 green, edge RED 2 failed/10 passed, hardened 12/12 green;
- V2 prefreeze: missing-module RED -> 174/174 green;
- V2 coverage bridge: missing-module RED -> 180/180 green;
- gate-evidence binder: missing-module RED -> 187/187 green;
- executor/estimand/decision-rule anti-posthoc hardening: RED 22 failed/167 passed -> 189/189 green;
- authenticated gate registry: missing-module RED -> 195/195 green;
- free-map bypass: RED 3 failed/193 passed -> production fix -> 197/197 green;
- state-only current head reran the same harness -> 197/197 green.

V2 candidate family remains C1-C5:

- C1 shared emergent
- C2 relational shared
- C3 query measured
- C4 structured composite
- C5 regulatory specialist

Governance rules include PASS/FAIL/NOT_ESTIMABLE distinction, no C4 compensation for failed/not-estimable constituents, optional C5 specialist cannot change the foundation terminal, exact external pins, and donor-primary inference.

**PR #275 has no real-value, corrected-replay, real-tournament, target-selection, TD60, Stage4, representation-selection, or training authority.**

Do not let tournament engineering distract from the real critical path.

---

## 18. SCENIC+ / ATAC / Morabito: how to use it correctly

Regulatory/ATAC evidence is a specialist, prior, falsifier, or external observational check—not a universal target by default.

Historical Stage75 integrated regulatory summary:

- 7 TFs
- 27 targets
- 96 edges
- Tier A: STAT1, ELF1, SPI1
- Tier B: IRF8, BACH1, CEBPA, RELA

Morabito GSE174367 microglial scale:

- snRNA: 4,126 microglia / 18 samples
- snATAC: 12,232 microglia / 20 samples
- 18 shared microglial donors between modalities, separate nuclei
- no FULL104 donor overlap

Stage75F 10-regulator/96-row material was derived from Morabito RNA, so it cannot be an independent answer key for an RNA predictor.

Aggregate/gene-specific ATAC accessibility was later exposed in PR175. Therefore the dataset is not wholly pristine. However, project history does **not** establish adaptive use of those observed ATAC values to choose architecture/train the teacher/tune donor-level validation: target design and donor-level evaluation preceded that aggregate coverage analysis.

Correct future framing: Morabito remains a candidate external-donor, independent-modality observational validation if choices are demonstrably independent of exposed aggregate accessibility. Disclose the exposure and prohibit ATAC-derived selection/thresholds. Do not claim same-cell RNA-ATAC validation.

---

## 19. Foundation representation / FULL104 is a separate lane

Do not use representation work to skip target qualification.

Current representation state remains `SUBSPACE_ONLY`; no representation winner.

Historical held-out TRAIN rich_H results included strong source/operator/support predictability. The technology-invariance question remains unqualified because source/acquisition can be partially biologically aliased.

FULL104 exact reader-fit scope:

- 4,553,407 cells
- 104 donors
- 42 operators
- 1,400 donor×operator groups
- 41,238 addresses

The full physical store required for final streaming qualification is not present in this environment. No D_shared/D_private/D_obs values are currently authoritative. Historical dimensions are not production authorities.

---

## 20. V79 synthetic lane is separate and on hold

Synthetic evidence never becomes target-discovery biology.

Historical V77/V78 did not promote a synthetic arm. Old V79 Bernoulli/detection V2 final attempt was not qualified because limiting ESS was approximately 361.876/362 < 400. The monolithic Gaussian/lognormal/ZTNB campaign is methodological hold/unadjudicated, not a biological failure.

Resource-safe exact-S174 replay implementation PR #279 was qualified at code head `2d5de281a171f0510d22a7408780fb069625ea02` with Actions run `38166126568`, job `114548954034`, 15 passed. Latest docs-only head was `615b55eb...`.

V79 is on hold unless explicitly resumed. Do not let V79 caches, conclusions, or authority contaminate real TD.

---

## 21. Audit and claim-boundary lessons that must survive takeover

Never equate:

- physical bytes authenticated with biological validation;
- one-to-one address mapping with corrected biological recurrence;
- successful cache/materialization with a target pass;
- low loss/noncollapse with biology;
- donor-membership disjointness with case-level statistical independence;
- cells/queries with biological N;
- historical evidence with current authority;
- synthetic green tests with real-data authority;
- safety-tool PII labels with a scientific finding that these public research datasets are private.

For any one-shot execution, audit every physical column/key/path dereferenced from the real authenticated input before spending the attempt marker. Synthetic fixtures should reproduce the producer schema, not consumer assumptions.

Preserve failed runs, failed qualifications, superseded code, historical positive results, historical negative results, and all exact hashes. Do not "clean up" contradictions by deleting them.

---

## 22. Canonical current dependency graph

`public-data foundation + scientific exposure firewalls`

`-> Molecular Ledger / observation-operator architecture`

`-> T1 mechanism failure localization`

`-> query-local/contextual target development`

`-> relational TD56-TD59 historical evidence`

`-> physical HVS/SEA mapping defect`

`-> historical recovery + corrected S174 substrate`

`-> PR259 G4/G5 value-blind integrity PASS`

`-> PR282 replacement G6 integrity execution (CURRENT ACTIVE OPERATION)`

`-> external G6 audit`

`-> G7 physical corrected-value corroboration under fresh operational authority`

`-> external G7 audit`

`-> separate owner authority for corrected TD56/57B/57C/59`

`-> interpret under frozen corrected-replay rules without rewriting history`

`-> real target-protocol adjudication using the already-qualified V2 governance machinery`

`-> representation qualification / tournament`

`-> TD60 learned-teacher continuity only if still scientifically appropriate`

`-> Stage4 / real training only under separate authority`

---

## 23. Files and PRs a new agent should read first

1. `docs/agent/TARGET_DISCOVERY_MASTER_HANDOFF_20261011.md` — this file.
2. `docs/agent/TARGET_DISCOVERY_CURRENT_HANDOFF_20261011.md`
3. `docs/agent/TD_G6_REPLACEMENT_AUTHORIZATION_ff4a21f9_20261011.md`
4. `docs/agent/TARGET_DISCOVERY_CANONICAL_STATE_20261011.json`
5. `docs/agent/MACHA_TARGET_DISCOVERY_AND_PARALLEL_LANE_RUNBOOK_20261011.md`
6. `docs/agent/TARGET_DISCOVERY_EVIDENCE_CODE_DATA_INDEX_20261011.md`
7. `docs/agent/TARGET_DISCOVERY_HISTORY_AND_AUDIT_LESSONS_20261011.md`
8. `docs/agent/TD_G6_ATTEMPT0_EXECUTION_RECORD_20261011.md`
9. `docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`
10. `target_discovery/HANDOFF_CURRENT_20260907.md`
11. `target_discovery/iterations/td33_global_row_binding_guard/TD33_SUMMARY.json`
12. PR #282 exact executable code and qualification evidence.
13. PR #259 G4/G5 evidence.
14. PR #277 historical G6/G7 predecessor evidence.
15. PR #275 only after the real critical path and historical science are understood.

---

## 24. Current exact status for takeover

### Real TD

- PR #282 qualified implementation: `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`
- qualification: 219/219 focused green; real Sample-A PASS; PR259 compatibility PASS
- fresh owner/runtime authority exists
- replacement G6: **authorized exactly once, pending execution/result**
- G7: **blocked pending external G6 audit**
- corrected TD56/57B/57C/59: **blocked pending accepted G6+G7 and separate authority**
- TD60: **not authorized; never qualifyingly executed**
- target winner: none
- representation winner: none
- Stage4/training: off

### Tournament governance

- PR #275 exact current qualified head: `0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`
- 197/197 synthetic/metadata-only governance green
- no real tournament authority

### V79

- separate/on hold

### Next event that changes the lane

A Macha replacement-G6 report. Audit it before any G7 authorization.

---

## 25. Controlling terminal

Until the exact downstream gates above are passed and separately authorized, the terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
