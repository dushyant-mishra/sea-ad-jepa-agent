# Canonical Target-Discovery Takeover — 2026-10-11

Status: **ACTIVE REAL TARGET-DISCOVERY LANE**

Hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the canonical new-agent handoff for the real target-discovery program. Read this before touching PR #275, PR #277, PR #282, corrected expression values, TD56/57/59, TD60, representation selection, Stage4 or training.

## 1. Lane separation

Three parallel lanes exist and must not contaminate one another.

1. **Real target-discovery lane — this handoff.** Historical target evidence, physical mapping repair, G4/G5/G6/G7 custody, corrected biological replay, and eventual target adjudication.
2. **Synthetic/V79 lane.** Separate Bayesian/synthetic-world program. Current execution record is PR #280. Its results are not target-discovery biology.
3. **Foundation representation lane.** Separate representation-qualification program (PRs #269/#271/#272/#276 and FULL104 work). Representation qualification does not select the target.

Macha may work both target-discovery and V79 in parallel, but commands, evidence, authority, output namespaces and claims must remain separate.

## 2. Scientific architecture already established

Do not reopen these principles casually:

- Technology/acquisition is an observation operator, not biology.
- Donor is the biological replication unit; source→donor→cell hierarchy is mandatory.
- Biological evidence uncertainty and measurement/depth uncertainty are distinct.
- Unsupported targets abstain; measured zero is a valid observation.
- No forced modality imputation.
- No named latent coordinate receives authority merely because it is stable.
- Low neural loss/noncollapse does not qualify biology.
- Protected outcomes/pathology do not define the target.

The current incumbent *hypothesis*, not winner, is:

`T(c,q) = { Z_shared(c), R_broad/meso(c), Z_query(c,q), Support(c,q), U_bio(c,q), U_meas(c,q), optional Specialist(c,q) }`

where:

- `Z_shared`: learned shared biology without named-coordinate authority;
- `R_broad/meso`: donor-local relational order at broad/mesoscale;
- `Z_query`: measured q-conditioned non-q same-cell context; q-excluded normalization; student receives q address only;
- support/missingness is explicit;
- biological and measurement uncertainty remain separate;
- chromatin/regulatory component is optional specialist evidence only if independently qualified.

## 3. Historical row-binding rule — mandatory

The authenticated 50K discovery freeze is stacked:

- Sample A: global freeze rows `0..24999`
- Sample B: global freeze rows `25000..49999`
- B `sample_row` resets to `0..24999`

Historical authority requires:

`global_row = np.arange(len(freeze_csv))`

assigned **before any filtering or merge**. CSR access must use this explicit global freeze-file row, never a post-merge DataFrame index and never generic `sample_row`.

Durable historical guard:

`PASS_GLOBAL_ROW_BINDING__RESET_INDEX_FORBIDDEN`

Primary references:

- `target_discovery/HANDOFF_CURRENT_20260907.md`
- `target_discovery/iterations/td33_global_row_binding_guard/TD33_SUMMARY.json`
- `target_discovery/iterations/TD30_TD36_CLOSURE_LEDGER.md`

This rule became operationally critical again during first real G6 execution; see §10.

## 4. Why target discovery changed direction

The original T1 target optimized numerically but did not recover the intended biology. Historical mechanistic work showed:

- authenticated `u0` already contained substantial correct-cell query-local context;
- T1/u205 could reduce that context at informative evidence levels;
- source/address/operator shortcuts could dominate low-loss latent targets.

Historical shortcut/calibration evidence includes:

- rich_H u0 address+operator explained variance ~`0.99938`, residual ~`0.0006165`;
- u205 residual ~`0.000142`;
- mechanistic stress could produce low JEPA loss while source accuracy remained `1.0`, support R² ~`.995+`, and biology-factor R² negative.

R5 developmental query-target evidence used measured non-q same-cell context. Historical developmental heldout R²:

- q-specific: `0.4300`
- technical+q: `0.3496`
- q-agnostic: `0.2760`
- q-count-only: `0.1610`

These are developmental evidence only, not target authority.

## 5. Historical relational target-discovery evidence

### TD56 / TD56S

Historical positive: disjoint molecular views recovered common within-donor relational geometry across HVS, NPH52 and SEA-AD.

Reference:
`target_discovery/iterations/td56s_disjoint_gene_relational_geometry/`

Interpretation: evidence for a shared relational biological invariant, not a named coordinate and not a target winner.

### TD57B

Historical prospective success: `24/24` cases passed.

Weakest observed-null-p95 margin:
`+0.0375178074843`

All 24 historical cases beat null max.

Needs corrected replay on repaired physical substrate before current authority.

### TD57C

Historical immutable FAIL:

`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`

Nearest-third fine-local Panel-0 HVS failed `2/4` and sequentially stopped. Never rescue, relabel or average this away. If a corrected replay later passes, classify as historical/corrected divergence and require a fresh prospective locality experiment.

Reference:
`target_discovery/iterations/td57c_three_view_local_geometry/`

### TD59

Historical positive: `24/24` cases passed.

Weakest p95 margin:
`+0.0011566307718604563`

`22/24` exceeded null max.

Nearest-half was a historical frontier/bracket, **not** a production constant. Original historical executor bytes remain unrecovered; the project uses an independently validated replay-closure successor and must never call it the original executor.

### TD60

Current status:

`PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`

Never call TD60 failed. It was intended to test whether a lawful learned EMA teacher preserves already-observed relational geometry. It remains downstream of corrected historical replay and target-adjudication gates.

## 6. Corrected-replay interpretation prefreeze

Controlling document:

`docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`

Frozen interpretation:

- TD56 PASS + TD57B PASS + TD57C FAIL + TD59 PASS → broad/meso relational program consistent with historical scale bracket; may advance, not winner.
- TD56/B PASS + TD57C FAIL + TD59 FAIL → broad/global only.
- TD56 PASS + TD57B FAIL → no stronger donor-recurrent scale-free order; TD59 cannot rescue.
- TD56 FAIL → stop relational promotion.
- corrected TD57C PASS → historical/corrected divergence; fresh prospective locality experiment required.
- source disagreement → no universal source replication; do not average/rescue with free source embedding.
- not estimable → `NOT_ESTIMABLE__NO_BIOLOGICAL_PASS`.

Even the strongest pattern does not authorize target selection, TD60, Stage4 or training.

## 7. Physical-mapping defect and historical recovery

The historical TRAIN substrate used for TD56/57/59 was later shown to have corrupted HVS/SEA physical feature mapping. This does **not** erase the historical evidence, but it prevents historical results from authorizing the current target.

Corrected S174 substrate SHA-256:

`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

Historical recovery established:

- exact historical 50K CSR package recovered;
- important TD56/57B/57C historical executors recovered;
- historical-only replays reproduce archived outputs;
- TD57C historical FAIL reproduced;
- NPH52 established as unambiguous historical pass-through;
- TD59 original executor remains genuinely unrecovered, with independently validated successor replay closure.

## 8. Historical 50K CSR authority

Project-upload split parts:

- part001 SHA-256: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002 SHA-256: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- combined outer ZIP SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Historical CSR member hashes:

- `data.npy`: `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`
- `indices.npy`: `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`
- `indptr.npy`: `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`
- `shape.npy`: `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`

These are custody authority, not biological conclusions.

## 9. G4/G5 accepted value-blind state — PR #259

PR #259 remains the narrow technical/data-integrity PASS for corrected Sample-A mapping.

Important pins:

- execution head: `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`
- executed code: `bf253a4dd62d943398f9ff59ed8b1e74777140a5`
- driver receipt SHA-256: `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping receipt SHA-256: `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA-256: `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Accepted facts:

- all 35 HVS/SEA H5AD byte sources authenticated;
- 34 Sample-A matrices;
- 9,216 replay addresses resolve 1:1 on all 34 matrices;
- G4/G5 remained value-blind.

No corrected biological recurrence or target authority is created by PR #259.

## 10. G6/G7 custody lineage and first real execution

### Qualified predecessor

PR #277 qualified implementation:

`fafd4309cc086c95076cefdc94064e8b66e58ae4`

Historical qualification at that implementation:

- focused suite: `217 passed / 0 failed / 0 skipped`
- physical PR259 compatibility: `1 passed / 0 skipped / 0 failed`

Code identities:

- common: `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6: `614af59cf6f4f0a8910235fcdef8b8b3ec1aae47ecf98c30bfaa3eaa1b3a07ad`
- G7: `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

Owner decision SHA-256:

`36599b7ade189e051b6e156d53ea1acd4caf42794f26b152d7eada0513a1a273`

Runtime authorization SHA-256:

`7cc66f601d6fc294ef9255f4e9ac4b1e1f16db56d1ddf52cf1fb839646fc91fa`

Scope was **G6/G7 integrity only**.

### First real G6 execution — schema qualification failure

The first real execution at `fafd4309` ran on the canonical machine. All preconditions and runtime authority checks passed, then the immutable start marker was created. Approximately nine seconds later G6 crashed before opening any H5AD value array:

`AttributeError: 'DataFrame' object has no attribute 'global_row'`

The real authenticated Sample-A freeze does not persist `global_row`; the code and synthetic fixture had assumed it did.

Important classification:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

The old output namespace must remain immutable evidence. It contained only `G6_EXECUTION_START.json`.

Start-marker SHA-256:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

No receipt was produced. No corrected H5AD expression value was read. No biological result exists.

The project owner ruled that this six-second schema failure does **not** consume the meaningful biological/value-read opportunity. A replacement execution is allowed only after a prospectively repaired and freshly qualified successor receives new authority.

## 11. Current G6 successor — PR #282

PR #282 title:
`TD G6 successor: restore historical global-row binding before spend`

Executable branch:
`fix/td-g6-global-row-binding-successor-20261011`

Exact executable-successor head pending qualification:

`7e482cf50f73a5cecda16482777129dd3ca725a6`

Repair lineage:

- RED regression: `e437f29646f61ac45b74df45e227999a5d603de1`
- production repair: `bf815958dc6cd601922dbb176e05cce7eb1a543b`
- regression fixture correction: `4786925f6807cf9b96bc266fe708f21807a2086b`
- qualification-runner hardening / current head: `7e482cf50f73a5cecda16482777129dd3ca725a6`

Repair behavior:

- derives historical `global_row` from exact freeze-file position when source CSV lacks it;
- binds row identity before filtering/merging;
- validates all required metadata columns explicitly;
- validates exact TD50 sentinel/global-row coverage and historical CSR bounds;
- performs metadata-only compatibility checks before `G6_EXECUTION_START.json`;
- does not open H5AD count/value arrays during those pre-spend checks.

**PR #282 is not yet qualified.** There was no CI attached to the exact current head at handoff creation. Do not create owner/runtime authority or run replacement G6 until canonical qualification is accepted.

Required qualification must include:

1. full focused G6/G7 suite including `tests/v5/test_td_g6_global_row_binding.py`;
2. exact authenticated production Sample-A freeze compatibility:
   - SHA-256 `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`;
   - no physical `global_row` column;
   - all required columns present;
   - derived Sample-A global rows exactly `0..24999`;
   - terminal `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`;
3. exact PR259 physical compatibility, no skip;
4. exact clean-head/code-identity record.

Only after qualification may a new owner decision + runtime authorization be created, bound to the qualified successor SHA and a fresh output namespace.

## 12. G7 remains blocked

G7 is not authorized until a replacement G6 completes and an external owner/auditor accepts its complete five-file namespace, receipt semantics, source accounting and hashes.

G7 must continue to compare authenticated physical H5AD values against authenticated S174 values. G6 cache is prerequisite custody evidence only, not a substitute counterpart.

## 13. Corrected biological replay remains downstream

After accepted G6 and G7, issue a **separate** owner decision for corrected TD56/TD57B/TD57C/TD59 replay under the prefrozen interpretation contract.

Do not jump directly from G6/G7 to TD60, target selection or training.

Expected sequence:

`G6 replacement PASS -> external audit -> G7 -> external audit -> separate corrected-replay authority -> corrected TD56/57B/57C/59 -> interpret with frozen rules -> target tournament/adjudication -> later TD60 as appropriate -> representation/Stage4/training gates`

## 14. V2 target-tournament governance — PR #275

PR #275 is a parallel synthetic/metadata-only governance lane, not the current critical path.

Current live head at this handoff:

`512da1f0fb9e5af130f11f2b1073451da61158d0`

V1 executable was scientifically superseded prospectively because its candidate identities/gates/inheritance drifted from the science prefreeze.

Terminal:

`V1_SCAFFOLD_SCIENTIFICALLY_SUPERSEDED_FOR_FUTURE_REAL_TOURNAMENT__PRESERVE_HISTORY__BUILD_V2_PROSPECTIVELY__NO_REAL_TOURNAMENT_AUTHORITY`

V2 spec:

`docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze-v2.md`

V2 candidates:

- C1 `C1_SHARED_EMERGENT`
- C2 `C2_RELATIONAL_SHARED`
- C3 `C3_QUERY_MEASURED`
- C4 `C4_STRUCTURED_COMPOSITE`
- C5 `C5_REGULATORY_SPECIALIST`

C4 cannot rescue failed/untested C2/C3 applicable gates. C5 is specialist-only and never changes the foundation terminal.

PASS / FAIL / NOT_ESTIMABLE remain distinct.

Current V2 adjudicator test was added at commit:

`512da1f0fb9e5af130f11f2b1073451da61158d0`

Production V2 adjudicator was not yet implemented/qualified at the time the G6 lane became the critical path. Do not spend real-value attention there until G6/G7/corrected replay are closed unless specifically redirected.

## 15. Mandatory falsifiers/baselines for eventual real target adjudication

At minimum preserve:

- constant;
- technical/operator-only;
- address/support/operator shortcut;
- matched wrong-cell;
- fine-neighborhood wrong-cell relational;
- q-count-only;
- q-address-only;
- q-agnostic;
- wrong-q;
- technical+q;
- q-excluded teacher;
- identity+support-only.

The donor is the biological N; repeated cells/queries do not create independent biological N.

## 16. SCENIC+/ATAC/regulatory evidence

Regulatory/chromatin evidence is specialist/soft-prior/falsifier material, not universal target authority.

Historical Stage75 integrated regulatory summary:

- 7 TFs
- 27 targets
- 96 edges
- Tier A: STAT1, ELF1, SPI1
- Tier B: IRF8, BACH1, CEBPA, RELA

Morabito:

- RNA: 4,126 cells
- ATAC: 12,232 cells

Exposure caveat: regulatory hypotheses and aggregate ATAC evidence have already been used historically, so Morabito is not a pristine untouched validation benchmark. It may still support properly frozen cross-modality/external-donor checks, but never call it fully unseen.

## 17. Foundation calibration and supporting project artifacts

Important project-upload artifacts/hashes used for historical calibration or recovery:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
  - SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
  - contains calibration, shortcut atlas, contracts, metadata, code and sampler artifacts.
- `expression.zip`
  - SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
  - contains discovery sample freeze/audit and per-operator metadata.
- `checkpoints.zip`
  - SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
  - includes `t1_checkpoint_u0000.pt` and `t1_checkpoint_u0205.pt` plus manifest.
- `t1_checkpoint_u0200.zip`
  - SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
  - historical intermediate T1 checkpoints.
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
  - SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
  - SHA-256 `fd003bc8f2f34ac856791dfcf6b0e3b7d81eddfffb8b256d23c3e4a5d40f3356`

Large binary artifacts should remain on controlled storage/project uploads; commit hashes/manifests and reproducible paths rather than duplicating them into Git.

## 18. Separate V79 state — for Macha coordination only

PR #280 terminal:

`EXACT_S174_STRUCTURE_REPLAY_FAILED_CLOSED__OPERATOR_MODEL_LOGISTIC_NONCONVERGENCE__NO_METRICS_COMPUTED__CONTROLLER_REPAIR_DECISION_REQUIRED__BAYESIAN_CONFIRMATION_OFF__TRAINING_OFF`

Important: this is **not** a target-discovery result. Macha may work it in parallel, but must not feed its counts/models/decisions into the real TD evidence chain unless a prospective cross-lane contract explicitly permits it.

## 19. Current decisions / prohibitions

At handoff creation:

- replacement G6: **blocked pending exact-head successor qualification**;
- G7: blocked;
- corrected TD56/57B/57C/59: blocked;
- TD60: never qualifyingly executed, blocked;
- target selection: blocked;
- representation selection: separate lane, no winner;
- Stage4/training: off;
- no merge of PR #275/#277/#282 without explicit owner review.

Never:

- call TD60 failed;
- relabel historical TD57C FAIL;
- call historical TD59 successor the original executor;
- turn technical custody PASS into biological PASS;
- let synthetic fixtures count as biology;
- use cell/query count as biological N;
- delete or rewrite the failed `fafd4309` G6 namespace;
- reuse the old owner decision/runtime authorization for a successor implementation;
- invent unobserved source independence by averaging;
- declare Morabito pristine independent validation.

## 20. Immediate new-agent actions

1. Read this handoff and `TARGET_DISCOVERY_CANONICAL_STATE_20261011.json`.
2. Read PR #282 exact current head and qualification runner.
3. Have Macha qualify PR #282 on the canonical machine; no G6 execution during qualification.
4. Audit the qualification outputs independently.
5. If and only if accepted, issue new owner decision/runtime authorization bound to the exact qualified successor SHA.
6. Run replacement G6 once in a fresh namespace; preserve every outcome.
7. External audit before any G7.
8. After G7 audit, separately authorize corrected TD56/57B/57C/59 replay under the existing interpretation prefreeze.
9. Keep PR #275 V2 tournament engineering secondary until the real corrected substrate/replay state is known.
10. Maintain strict lane separation with V79 and foundation representation work.

The project is designed to permit scientific reopening and pivoting. Preserve historical failures and contradictions; do not optimize the narrative toward a winner.