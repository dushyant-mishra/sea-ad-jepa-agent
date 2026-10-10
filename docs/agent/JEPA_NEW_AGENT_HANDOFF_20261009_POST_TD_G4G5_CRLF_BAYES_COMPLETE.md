# JEPA new-agent cold-start handoff — 2026-10-09

## 0. Start here and do not reconstruct the project from old chats

This document is the current cold-start takeover surface for the JEPA project as of 2026-10-09 after:

- canonical V5 runtime convergence and bounded synthetic mutation rehearsal;
- S174 real-data feature-axis defect discovery, repair, corrected replay and downstream re-scoring;
- synthetic E0-E3 and V78 follow-on falsification work;
- target-discovery custody recovery through TD34 and TD41-TD60 lineage;
- recovery of the corrected TD relational replay implementation through G7;
- a fresh exact 17,186-core / 9,216-address historical replay-manifest reconstruction;
- independent S174 RAR transfer authentication;
- the first canonical-machine G4/G5 attempt, which stopped before G4/G5 due a Windows CRLF serialization defect;
- preregistration of a historical-only Bayesian replication-method spike.

Do not begin by searching old branches or chats. Read this file, then the machine state and artifact locator in the same handoff branch.

### Handoff branch

`handoff/jepa-20261009-post-td-g4g5-crlf-bayes-complete`

Base at creation:

`impl/td-relational-corrected-preflight-20261009@6716f044fcbefeb39bddf505c09a82378ce602e8`

This handoff branch is documentation/custody only. It grants no scientific or execution authority and must not be merged into `main` without explicit owner instruction.

## 1. Global hard terminal

The project remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Also preserve:

- TEST sealed;
- Morabito protected;
- DEV/SEALED/pathology-dependent surfaces unopened unless separately authorized;
- no target freeze;
- no representation freeze;
- no production EMA selection;
- no production multimodal training;
- no TD60 execution authority;
- no corrected TD value read until the exact gate sequence below is satisfied.

Engineering/test GREEN results never override scientific authority.

## 2. Current GitHub control surfaces

### PR #237 — custody/scientific-history base

Branch:
`handoff/jepa-20261008-complete-runtime-s174-takeover`

Head:
`813ead17570dbb4b6a5a58ebe6dc84fed8aa0438`

Role: immutable-style custody and scientific-history base. It should not be advanced for current target-discovery implementation. Its residual instruction to continue searching for a corrected TD replay bridge is superseded.

### PR #243 — current target-discovery implementation successor

Branch:
`impl/td-relational-corrected-preflight-20261009`

Head at handoff creation:
`6716f044fcbefeb39bddf505c09a82378ce602e8`

Role: current corrected-relational G1-G7 implementation surface plus the non-authorizing Bayesian spike preregistration.

Read first on that branch:

- `docs/agent/JEPA_TARGET_DISCOVERY_IMPLEMENTATION_HANDOFF_20261009.md`
- `custody/target_discovery_20261009/TD_IMPLEMENTATION_STATE_20261009.json`
- `docs/agent/JEPA_TARGET_DISCOVERY_BAYESIAN_SPIKE_PREREG_20261009.md`
- `docs/agent/JEPA_TD_RELATIONAL_CORRECTED_25K_REPLAY_CONTRACT_20261007.md`
- `docs/agent/JEPA_TD_RELATIONAL_G6_G7_PREFREEZE_20261007.md`

### PR #244 — S174 transfer custody evidence

Branch:
`custody/s174-cache-transfer-verification-20261009`

Head:
`eb3f92045e95ee4e5a85a864d1ec5922fe8f3d16`

Terminal:
`PASS_S174_RAR_EXACTLY_MATCHES_G1B_AUTHORIZED_CORRECTED_CACHE`

This is custody-only. Do not interpret it as new S174 science.

### PR #245 — preserved failed TD G4/G5 execution record

Branch:
`exec/td-relational-g4g5-local-20261009`

Head:
`bf6ddda4e1b020fdb959812036b957c40166fede`

Terminal:
`FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_BEFORE_G4_G5__MANIFEST_FILE_SHA_MISMATCH__WINDOWS_CRLF_SERIALIZATION`

G4/G5 were not executed. Do not merge this PR into #243 as if it were a PASS.

### Synthetic/runtime lanes that remain relevant historical context

- PR #236 `impl/v77-bounded-synthetic-mutation-20261007@8495c9f0...`: one guarded synthetic optimizer update rehearsal completed; synthetic-only/non-production.
- PR #240 `impl/v77-class-propagation-20261008@f3a5d142...`: E0-E3 tournament complete; broad-class mechanism directionally supported by E2 but no arm adequate/promoted.
- PR #241 `handoff/synthetic-dataset-post-e0e3-20261008@1ffc8174...`: synthetic-lane custody.
- PR #242 `impl/v78-signed-detection-marginals-20261009@e959d9a7...`: F0-F3 follow-on synthetic falsification; no arm promoted; current branch still had repository closure work at last audit.
- PR #224 `reconcile/canonical-v5-runtime-successor-20261006@9d00684e...`: canonical runtime mechanics lineage.
- PR #226 `reconcile/shared-qualification-v2-on-canonical-runtime-20261007@e83bb8d...`: shared qualification interface lineage.

Do not restack or merge these into the current TD lane unless a future reviewed design explicitly requires it.

## 3. Runtime / model mechanics — what is already closed

The canonical V5 runtime lineage established:

`authenticated q-safe input -> encoder -> predictor -> EMA teacher -> loss -> backward -> CurrentTrainingAuthorityV2 -> OptimizerGuardV4 -> guarded optimizer step -> completion assertion -> EMA -> authority-bound checkpoint -> deterministic reload`

Key invariants already proven in synthetic/runtime work:

- optimizer authority binds the actual optimizer/configuration;
- gradient validation occurs after unscale and before stepping;
- nonfinite/GradScaler skip cannot be misrepresented as a successful update;
- EMA can advance only after successful optimizer completion;
- presentation-normalized EMA proof binds parent/child teacher age and EMA configuration;
- checkpoint/restart carries online model, predictor, EMA teacher, optimizer, scaler, cursor and physical proof;
- physical row, logical identity, source/global/local coordinates, authenticated payload digest and consumed values must remain coupled;
- q-safety execution proof is distinct from runtime mutation proof.

PR #236 then executed exactly one bounded synthetic guarded update and reload. This is mechanical evidence only. Real training remains OFF.

Do not reopen generic runtime archaeology unless a new defect is observed.

## 4. S174 defect, repair and downstream scientific correction

### Defect

The historical TRAIN cache used by V77 real-data analyses had scrambled HVS and SEA-AD gene labels/physical-column identity.

### Corrected cache

Canonical local root:

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Geometry:

- 84 files;
- 42 `counts.npz` + 42 `meta.npz` pairs;
- 35 HVS/SEA-AD shards rebuilt from correct physical gene IDs;
- 7 NPH shards carried through unchanged qualified path.

G1 failed historically and remains preserved. Owner-authorized G1b was then defined and passed.

### Corrected downstream science

Important corrected findings from Macha's S174 lane:

- pooled cohort coverage explains about **3%** of pooled correlation structure, not the earlier ~89% interpretation;
- median absolute real gene-gene correlation is about **0.056**, not ~0.33;
- cell-class separation contributes about **26%** of pooled correlation;
- the earlier Step-3 interpretation that latent mechanism was effectively solved / observation was the bottleneck is superseded;
- earlier factor-family falsification and substate / Observer-V2 support conclusions are superseded;
- no candidate was ever accepted;
- detection continues to carry more dependence than expression.

Corrected synthetic replays reproduced their old historical outputs first and then showed that no existing arm simultaneously reproduces real class separation, depth, abundance and detection correlation. The 12-fold arm lands near real detection density/degree but is an observation, not a winner.

S159 uncertainty bands are diagnostics only, not pass/fail gates, until their statistical meaning is separately resolved.

### Transfer custody now independently closed

RAR:

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1.rar`

Bytes:
`47,964,366`

SHA-256:
`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

PR #244 proved 84/84 extracted files match the committed G1b-authorized authorities exactly.

Exact artifacts on #244:

- `docs/agent/S174_LOCAL_CACHE_TRANSFER_HANDOFF_20261009.md`
- `results/v77/s174_replay/S174_LOCAL_CACHE_TRANSFER_VERIFICATION_20261009.json`
- `scripts/v77/verify_s174_cache_transfer.py`
- `tests/v77/test_v77_s174_cache_transfer_receipt.py`

Known nomenclature defect only: corrected 14,417-address universe still carries historical label `TRAIN_PREVALENCE05_19569`. Do not rename casually; a rename would require builder review and rerun.

## 5. Synthetic scientific lane after S174

### E0-E3 broad-class propagation — PR #240

Key result:

- E1 = E0 exactly: isolation PASS.
- Corrected real T5 reference ~0.7435.
- E0/E1 T5 ~1.05047.
- E2 T5 ~0.91418: correct direction; broad class contributes missing pooled-vs-within covariance.
- E3 T5 ~1.19432: wrong direction.
- E2 is not an adequate repair because detection topology, abundance, depth and multiple expression metrics deteriorate.
- E3 rejected.
- signed detection topology remains very wrong in all arms.
- no arm promoted.

### V78 F0-F3 follow-on — PR #242

At last audited PR body:

- repaired S174 RAR, not the older Stage81A3R ZIP, is current execution substrate;
- repaired marginal authority built from all 42 corrected shard pairs;
- F0 exactly reproduces E2 baseline;
- F1 improves signed ratio toward real but collapses degree/transitivity and distorts abundance/depth;
- F2 preregistered signed-field hypothesis is falsified;
- F3 marginals improve one abundance magnitude but worsen signed topology / other metrics;
- no arm is adequate or promoted;
- no post-outcome retuning authorized.

This lane is informative for later mechanistic modeling, including future Bayesian evidence integration, but it has no target authority.

## 6. Target-discovery historical authority — controlling classifications

Do not use Sept-7/early-Sept documents as the current scientific conclusion without the Oct-8/Oct-9 supersession layer.

### TD34

Primary producer:

`custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

Content SHA-256:
`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

Upstream support NPZ archive SHA-256:
`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Support member SHA-256:
`852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

Predicate `(states == 1).all(0)` yields exactly 17,186 addresses.

Current classification:

`TD34_EXACT_PANEL_MEMBERSHIP_REPRODUCED__CANONICAL_UPSTREAM_SUPPORT_BOUND__SELECTION_RULE_HASH_BOUND__NO_TARGET_AUTHORITY`

TD34 genealogy is closed. Do not redo it.

### TD56

`HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57B

Historical prospective success:

- 2 independent panels;
- HVS/NPH52/SEA_AD;
- 2 donor splits x 2 halves;
- 24/24 PASS;
- weakest historical margin +0.0375178074843.

Current classification:

`HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

Historical commit:
`e50f065bf46446460f900f6c12a94fc364fdfbf6`

### TD57C

Historical frozen terminal:

`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`

This failure must never be retroactively rescued by later unrestricted diagnostics or an exploratory Bayesian posterior. A corrected-substrate replay is a separate evidence object and must obey the original sequential stop rule.

### TD58

`FALSIFICATION_ONLY__NO_TARGET_AUTHORITY`

### TD59

Historical nearest-half evidence:

- 24/24 historical cases passed;
- weakest margin +0.0011566307718604563;
- 22/24 beat historical null maximum.

Current classification:

`TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

Pre-outcome binding commit:
`f3eb86d26a306fe99ae2848dca89e9f2e9e25207`

Historical result commit:
`91a782c92b5d0d02358e3481a08395819c77f905`

Original first-run executor/result bytes remain unrecovered; successor replay must not be represented as original bytes.

### TD60

`PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`

Never call TD60 failed. Never promote it without a new explicit authority chain.

## 7. Historical TD41-TD58 physical bridge and exact assets

Historical frozen 50K sparse expression SHA-256:

`4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

Historical TD50 metadata roots:

- HVS `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb`
- NPH52 `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe`
- SEA_AD `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4`

Historical sparse components:

- data.npy `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`
- indices.npy `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`
- indptr.npy `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`
- shape.npy `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`

Authenticated historical TD41-TD58 archive:

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

Bytes:
`92,478,083`

SHA-256:
`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

Complete recovered 155-file TD manifest root:

`fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`

Exact 78-file recovered source bundle root:

`e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`

Do not claim every historical result/data byte is an ordinary Git blob. Large scientific bytes are represented by custody hashes/manifests where appropriate.

## 8. Corrected relational replay contract and exact geometry

Prepared corrected replay rematerializes the exact historical Sample-A subset and frozen genes while replacing the invalid HVS/SEA-AD physical feature-column mapping with matrix-native stable-ID resolution.

### Frozen 9,216 address allocation

- 0..1023: TD56/TD57A/TD58, two 512-gene views.
- 1024..3071: TD57B, two independent 1024-gene panels.
- 3072..6143: TD57C, two independent three-view panels; historical sequential stop must be honored.
- 6144..9215: TD59, two independent three-view nearest-half panels.

Exact replay manifest SHA-256:

`4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Exact Sample-A freeze:

- HVS 1,129
- NPH52 1,310
- SEA_AD 22,561
- total 25,000

`FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`

SHA-256:
`79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`

Corrected value chain:

`matrix-native stable feature ID -> native physical column -> canonical molecular address -> raw count -> historical normalization`

Normalization:

`log1p(raw_count * 10000 / full_source_library)`

where `full_source_library` is the whole-cell raw library size, not the 9,216-address subset.

No replacement gene is allowed. An unresolved frozen address is `NOT_ESTIMABLE` / STOP.

## 9. Fresh exact replay-manifest reconstruction on Oct 9

PR #243 carries active implementation and receipt:

`results/audit/TD_RELATIONAL_REPLAY_9216_REEXECUTION_20261009.json`

Fresh result:

`PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST`

Reexecution used:

- Aug-24 calibration bundle SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`;
- TD41-TD58 archive SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`;
- frozen builder Git blob `03dc4949e7e04040db5f85e331da72c5dcab86e6`.

It reproduced:

- common core 17,186;
- exact replay addresses 9,216;
- exact manifest SHA `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
- all frozen TD57B/TD57C/TD59 panel/pair validations.

No expression values were read.

## 10. Active corrected-replay implementation on PR #243

Active scripts:

- `scripts/v5/build_td_relational_replay_manifest.py`
- `scripts/v5/audit_td_relational_replay_mapping_preflight.py`
- `scripts/v5/run_td_relational_replay_preflight.py`
- `scripts/v5/materialize_td_relational_corrected_sampleA.py`
- `scripts/v5/audit_td_relational_g7_s174_overlap.py`

Active tests:

- `tests/v5/test_build_td_relational_replay_manifest.py`
- `tests/v5/test_audit_td_relational_replay_mapping_preflight.py`
- `tests/v5/test_run_td_relational_replay_preflight.py`
- `tests/v5/test_materialize_td_relational_corrected_sampleA.py`
- `tests/v5/test_audit_td_relational_g7_s174_overlap.py`

Key frozen docs/receipts:

- `docs/agent/JEPA_TD_RELATIONAL_CORRECTED_25K_REPLAY_CONTRACT_20261007.md`
- `docs/agent/JEPA_TD_RELATIONAL_G6_G7_PREFREEZE_20261007.md`
- `docs/agent/JEPA_TD_RELATIONAL_IMMUTABLE_NAMESPACE_FREEZE_20261007.json`
- `docs/agent/JEPA_TD_RELATIONAL_IMPLEMENTATION_READINESS_20261009.md`
- `docs/agent/JEPA_TD_RELATIONAL_PREFLIGHT_RUNBOOK_20261007.md`
- `docs/agent/JEPA_TD_RELATIONAL_REPLAY_9216_RECEIPT_20261007.json`
- `docs/agent/JEPA_TD_RELATIONAL_REPLAY_PREFLIGHT_STATUS_20261007.json`
- `docs/agent/JEPA_TD_RELATIONAL_VALUE_CODE_FREEZE_20261007.json`
- `docs/agent/JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_TEMPLATE_20261007.json`
- `docs/agent/JEPA_TD_SAMPLE_A_ROW_IDENTITY_RECEIPT_20261007.json`

The value-read authorization template is explicitly **not authority**.

## 11. Canonical-machine G4/G5 attempt and exact defect

PR #245 preserved the first canonical Windows run.

Code used:

PR #243 historical implementation head at execution time:
`a6c57e4e92b23756f5c49183eaa15d55f39cc325`

Command:

`python scripts/v5/run_td_relational_replay_preflight.py`

Environment:

- Windows 10 build 26200;
- Python 3.9.7;
- numpy 1.24.2;
- pandas 1.5.3;
- h5py 3.2.1.

All required authorities were present and verified:

- Sample-A freeze: 14,700,106 bytes / SHA `79eb005c...`.
- Stage81A2R provenance: 5,764,358 bytes / SHA `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`.
- Stage81A3R collision ledger: 1,101,503 bytes / SHA `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`.
- calibration bundle: exact authority `07748d5b...`.
- TD archive: exact authority `c84849f5...`.
- 35 HVS/SEA-AD H5ADs: all exact against S174 freeze, total 323,643,986,614 bytes.

The run stopped before G4/G5 because:

- builder content was correct;
- in-memory SHA was exact `4bde5f80...`;
- `Path.write_text` converted LF to CRLF on Windows;
- physical manifest SHA became `923475ae...`;
- driver correctly re-hashed the physical file and failed closed.

Terminal:

`FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_BEFORE_G4_G5__MANIFEST_FILE_SHA_MISMATCH__WINDOWS_CRLF_SERIALIZATION`

G4/G5 status:

`NOT_EXECUTED`

No expression arrays opened.

Preserved PR #245 artifacts:

- `docs/agent/TD_RELATIONAL_G4G5_LOCAL_EXECUTION_20261009.md`
- `docs/agent/TD_RELATIONAL_G4G5_LOCAL_EXECUTION_20261009.json`
- `results/target_discovery/td_relational_corrected_replay_20261007/preflight_v1/JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST.csv` — CRLF bytes exactly as failed run wrote them;
- `.../JEPA_TD_RELATIONAL_REPLAY_9216_RECEIPT.json`;
- `.../S174_REBUILD_FREEZE_V1.json`.

There is no `PREFLIGHT_RESULT.json`.

### Next exact implementation task

Repair platform-stable manifest serialization under TDD.

Preferred design:

1. Add RED regression proving the builder emits the exact same physical manifest bytes/hash on Windows-newline semantics and LF-native semantics.
2. Change the producer to write explicit LF bytes (`write_bytes` or `open(..., newline="\n")`).
3. Add a RED regression for the freshness guard so a partial failed-run namespace cannot be silently overwritten merely because `PREFLIGHT_RESULT.json` is absent.
4. Repair the freshness guard to fail closed when any frozen output namespace content already exists unless an explicitly new/superseding namespace is selected.
5. Run focused tests.
6. Rerun value-blind preflight into a fresh/superseding namespace on the canonical machine.
7. Required terminals:
   - `PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`
   - `PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`
8. Stop. Do not run G6/G7 automatically.

Do not edit the failed CRLF manifest in place. Do not reinterpret the failure as a scientific failure.

## 12. G6/G7 boundary after any future G4/G5 PASS

G6 materializer and G7 overlap auditor are recovered and fail-closed.

After G4/G5 PASS, still stop until the owner explicitly authorizes the exact frozen value-read scope.

Required owner token from the frozen contract:

`AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_ONLY`

The existing template has `real_value_read_authorized=false` and cannot be renamed/reused as if it were authority.

Only after valid authorization may the lane:

- materialize corrected 25,000 x 9,216 selected values;
- perform G6 whole-cell source-library sentinels;
- run G7 natural S174 overlap checks;
- execute the frozen corrected TD56 -> TD57A -> TD58 -> TD57B -> TD57C sequential -> TD59 replay order.

No target, representation, TD60 or training authority follows automatically from those results.

## 13. Bayesian target-evidence spike — current exact state

Preregistration:

`docs/agent/JEPA_TARGET_DISCOVERY_BAYESIAN_SPIKE_PREREG_20261009.md`

Status:

`SPIKE_PREREGISTERED__HISTORICAL_ONLY__NON_AUTHORIZING__NO_CORRECTED_REPLAY_INGESTED__NOT_YET_EXECUTED`

The exact TD41-TD58 archive has been materialized read-only for the spike. There are **no Bayesian posterior results yet**. Do not claim otherwise.

Frozen question:

Can a skeptical dependency-aware hierarchical model summarize historical TD57B/TD57C/TD59 case-level margins and posterior-predictive replication without:

- using historical PASS/FAIL labels during fitting;
- inventing pseudo-replicates;
- treating shared donors/sources/panels/substrate as independent evidence;
- ingesting the corrected replay before synthetic calibration/model definition closes?

Planned outputs are stage-level only:

- posterior stage margin;
- `P(margin > 0)`;
- source/panel heterogeneity where estimable;
- posterior predictive probability of positive margin in a new case;
- prior sensitivity.

No target-level posterior or ranking is allowed in this spike.

Mandatory synthetic falsification:

- null margins;
- one-source-only positive signal;
- duplicate/dependency resistance;
- sign-flipping source heterogeneity;
- shared positive recovery;
- at least three reasonable prior scales.

TD57C historical failure can never be relabeled by this spike.

### Bayesian next task

After the TD serialization repair is safely separated, continue the spike by reading only historical TD57B/TD57C/TD59 authenticated result surfaces, constructing the dependency ledger, and running the synthetic calibration before fitting historical evidence. Corrected replay results remain excluded until the historical method spike is frozen/closed.

## 14. Important physical/local assets

### S174 repaired cache

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Transfer RAR SHA:
`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

### Sample-A freeze

`D:\Jepa project\exports\foundation_corpus_discovery_v1\FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`

SHA:
`79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`

### Stage81A2R provenance

`D:\Jepa project\results\v4\stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`

SHA:
`df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`

### Stage81A3R collision ledger

`D:\Jepa project-stage81a3r-20260814\results\v4\stage81a3r_expression_materialization_collision_ledger.csv.gz`

SHA:
`f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`

### Calibration bundle authority

`FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`

Bytes:
`410,278,055`

SHA:
`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Warning: a different same-named 1,093,202,356-byte file exists under an exports path and is **not** the authority bundle.

### TD archive

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

Bytes:
`92,478,083`

SHA:
`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

## 15. 353 historical gene-ID remapping issue

There are 353 historical Ensembl/address mappings whose current symbol differs.

This belongs to the identity lane. Do not silently substitute current symbols into historical panels or use symbol remapping to rescue a frozen address. Before future biological interpretation, intersect exact frozen 9,216 identities with the 353-flag set and report identity uncertainty explicitly.

## 16. Things that are superseded and must not be resurrected

Do not resurrect:

- the claim that S174 cohort coverage explains ~89% of pooled correlation;
- the old strong median |r| ~0.33 as corrected real reference;
- Step-3 “latent mechanism solved / observation bottleneck” conclusion;
- factor-family falsification based on corrupted S174 substrate;
- substate / Observer-V2 support decisions from that corrupted substrate;
- Stage81A3R ZIP as byte-equivalent to the later Macha S174 repair;
- broad search for a missing corrected TD replay implementation;
- old TD60 “blocked/failed” wording; it was never qualifyingly executed;
- historical unrestricted TD57C post-failure diagnostics as a rescue of the frozen prospective failure;
- a generic 24/24 count as 24 independent Bayesian observations;
- S159 diagnostic uncertainty bands as hard pass/fail gates;
- any claim that a GREEN unit test or runtime rehearsal grants target/training authority.

## 17. Exact next-action order for the successor

1. **Do not search.** Verify this handoff branch head and read the machine manifest + artifact locator.
2. Fetch current PR #243 head and ensure it is still a descendant of `6716f044fcbefeb39bddf505c09a82378ce602e8`; if it moved, inspect only the delta.
3. Implement the CRLF/platform-stable manifest repair under TDD on a successor branch from #243.
4. Repair partial-namespace freshness semantics under TDD.
5. Run focused tests and record exact commit/workflow results; do not call CI PASS if no status exists.
6. Have the canonical Windows machine rerun value-blind G4/G5 into a fresh/superseding namespace.
7. If G4/G5 fails scientifically or on identity, preserve receipt and stop.
8. If G4/G5 passes, return to owner for the separate G6/G7 value-read authorization decision.
9. In parallel but isolated from corrected replay, continue the preregistered Bayesian historical-only spike: dependency ledger -> synthetic calibration -> label-blind historical fit -> posterior predictive checks -> only then compare with historical dispositions.
10. Do not let Bayesian exploration alter historical stage labels or target authority.
11. Keep runtime/synthetic lanes separate unless a new reviewed cross-lane design is explicitly authorized.

## 18. Merge policy

Do not merge PR #237, #243, #244, #245, this handoff branch, or the active synthetic/runtime drafts into `main` without explicit owner authorization.

PR #245 is an execution record, not a candidate scientific integration commit.

PR #244 is custody evidence, not a scientific change.

This handoff branch is takeover documentation/custody only.
