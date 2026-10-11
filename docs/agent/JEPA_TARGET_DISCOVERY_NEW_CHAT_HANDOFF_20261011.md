# JEPA target-discovery takeover handoff — 2026-10-11

Status: `CURRENT_TAKEOVER_OVERLAY__NO_VALUE_AUTHORITY__NO_TARGET_AUTHORITY__NO_TRAINING_AUTHORITY`

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the cold-start handoff for the **target-discovery lane only**. It supersedes older chat-level summaries where they disagree. Preserve historical failures; do not merge or rewrite them.

## 1. Canonical control surfaces

- Handoff / cold-start PR: **#247**, branch `handoff/jepa-20261009-post-td-g4g5-crlf-bayes-complete`.
- Audit / preauthorization PR: **#251**, branch `review/td-g6g7-preauthorization-hardening-20261009`.
- Accepted value-blind G4/G5 execution record: **PR #259**, head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`.
- Current G6/G7 engineering candidate: **PR #267**, head `16f05bd3845565bb2c24d70143d447d7ef2b8904`.
- PR #267 is **IMPLEMENTED BUT UNQUALIFIED / DO NOT EXECUTE G6/G7**.
- PR #263 head `a509c59238bcdc60b88fa265e7e4473760a41025` is superseded-before-qualification and must not be run.
- PR #249 Bayesian formulation is terminated: `STOP_THIS_BAYESIAN_FORMULATION__DO_NOT_TUNE_TO_HISTORICAL_OUTCOMES`.

## 2. Scientific authority state

Target discovery remains open. There is no selected target and no representation winner.

Historical relational evidence:
- TD56: historical evidence that disjoint molecular views recover shared within-donor relational geometry.
- TD57B: historical prospective success, 24/24 cases PASS; weakest historical observed-null-p95 margin `+0.0375178074843`.
- TD57C: immutable historical prospective FAIL: `NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`. Never rescue or relabel retroactively.
- TD59: historical nearest-half mesoscale positive evidence, 24/24 cases; weakest p95 margin `+0.0011566307718604563`; 22/24 beat historical null max.
- TD60: `PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`. Never call TD60 failed.

The old TRAIN expression substrate used by historical TD56/57B/59 was later found corrupted for HVS/SEA_AD physical feature mapping. Therefore those stages are historical evidence requiring corrected-data replay, not current target authority.

## 3. Accepted corrected-substrate preflight — PR #259

PR #259 executed exact code `bf253a4dd62d943398f9ff59ed8b1e74777140a5` and passed the value-blind G4/G5 contract.

Exact evidence:
- driver schema: `JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3`
- driver terminal: `PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`
- driver physical SHA-256: `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping schema: `JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3`
- mapping terminal: `PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`
- mapping physical SHA-256: `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA-256: `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Sample-A contract:
- label `A_NATURAL_MIXTURE`
- 25,000 cells
- HVS 1,129
- NPH52 1,310
- SEA_AD 22,561
- 34 HVS/SEA H5AD matrices contain Sample-A cells and pass exact mapping
- all 35 frozen HVS/SEA H5AD byte sources pass custody authentication
- the 35th HVS H5AD contains no Sample-A rows and was hash-authenticated only

Critical interpretation: PR #259 proves that the historical replay can be mapped to the authenticated corrected substrate **without reading expression values**. It does not prove historical biological recurrence.

PR #259 did not run G6 or G7, did not create a value-read authorization, and did not run corrected TD56/57B/57C/59/60 or training.

The exact PR259 driver and mapping Git blobs preserve their Windows CRLF bytes. Any future authorization must bind the exact audited physical SHA pair above; do not regenerate or reformat those JSON files.

## 4. Current future value path — PR #267

PR #267 exact head: `16f05bd3845565bb2c24d70143d447d7ef2b8904`.

It is a bounded successor to superseded PR #263. Relative to #263, the repair changed only:
- `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`
- `tests/v5/test_td_g7_counterpart_attempt_custody.py`

No G6/common/scientific-statistic code changed in the bounded repair.

The full current standalone V2 code surface is snapshotted in this takeover bundle:
- common fail-closed custody gate
- standalone G6 V2 materializer
- standalone G7 V2 S174 overlap audit
- common/G6/G7 unit tests
- exact-PR259 real-receipt compatibility test
- G7 counterpart/attempt custody regression test

PR #267 repairs two prequalification G7 custody defects:
1. For a natural-overlap matrix, physical H5AD exact authentication occurs before the S174 count loader can be invoked; S174 counts still re-authenticate immediately before count opening. Thus both counterpart count sources authenticate before either side's count values are used.
2. G7 spends an immutable `STARTED_NOT_A_PASS` sidecar after runtime authority + same-authority G6 PASS and before value-bearing work. A failed attempt permanently spends the logical attempt path; existing marker or final receipt blocks reuse.

PR #267 has **no GitHub workflow result and no canonical pytest PASS**. Do not call it qualified.

Controlling qualification contract:
`docs/agent/TD_PR267_CANONICAL_QUALIFICATION_20261011.md`

Qualification must pin exact head `16f05bd...`, run the focused common/G6/G7 suites plus the new custody tests, and run `test_td_relational_pr259_real_receipt_compat.py` against the exact physical PR259 receipt bytes. That real-receipt test must report **1 passed / 0 skipped / 0 failed**. A skipped compatibility test is not qualification.

Qualification itself must create no runtime authorization, run neither G6 nor G7, and read no corrected expression/count values. After qualification: STOP for owner review.

## 5. Owner-decision boundary

No runtime value-read authorization exists.

Even after PR #267 qualifies, a valid `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2` is not sufficient unless it cryptographically binds an immutable explicit owner-decision record proving exactly:
`AUTHORIZE_G6_G7_INTEGRITY_ONLY`

Controlling audit:
`docs/agent/TD_VALUE_AUTH_OWNER_DECISION_BINDING_AUDIT_20261010.md`

Never infer authorization from a PASS, a PR mergeability state, or possession of the data.

If the owner later authorizes G6/G7 integrity execution:
- create the owner-decision record first;
- create the runtime authorization bound to exact PR259 receipt bytes and exact qualified common/G6/G7 implementation identity;
- G6 must PASS before G7 may run;
- G7 mismatch or `NOT_ESTIMABLE` is process non-success;
- after G7, STOP for review. G6/G7 integrity PASS does not authorize biological replay.

## 6. Historical executor / fixture recovery

Authenticated historical archive recovered from Project Library:
`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`
- Library file id `file_00000000e9ec81f6a58dc73acf9d7807`
- bytes 92,478,083
- SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

Exact recovered executor SHAs:
- TD56 HVS `a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43`
- TD56 NPH52 `090134f0cc129559286f06d80a31a880c07c9841a7ef3f446b914a78c8cd7162`
- TD56 SEA_AD exact-fast `c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866`
- TD57B executor `1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`
- TD57B fast wrapper `808fb293a87d0020adc0f332742f3fa9b99c9c8ec5a88e50504a719ad4183a70`
- TD57C executor `530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`

Historical discovery-expression package was reconstructed exactly from uploaded split parts:
- part001 SHA `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002 SHA `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- assembled ZIP SHA `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- inner historical expression NPZ SHA `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`

Fresh historical-only local reruns reproduced archived output bytes exactly for:
- TD56 HVS
- TD56 NPH52
- TD56 SEA_AD
- TD57B Panel-0 HVS
- TD57B Panel-0 NPH52
- TD57B Panel-1 HVS
- TD57B Panel-1 NPH52
- TD57C Panel-0 HVS, including the historical FAIL and expected non-success exit

Do not claim a new local TD57B SEA_AD replay: those two heavy cases were not completed in this coordinator container. The historical project self-audit separately records exact-fast SEA_AD replays as byte-identical.

NPH52 pass-through audit on the exact authenticated historical CSR found:
- 0/1,310 NPH52 Sample-A rows with duplicate CSR address indices
- 0/25,000 Sample-A rows with duplicate CSR address indices

TD59 is the documented exception. Original executor bytes with SHA `3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0` remain unrecovered. The independently validated replay-closure successor SHA `870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085` is the only admissible executable statistic reference. Never relabel it as original TD59 bytes.

## 7. Corrected biological replay is prefrozen, not authorized

Controlling prefreeze covers TD56, TD57B, TD57C and TD59.

Rules:
- no corrected biological replay before reviewed G6/G7 integrity evidence and a second explicit owner authorization;
- replay all four already-opened historical objects; do not stop the audit of one historical object merely because another corrected replay diverges;
- preserve each stage's historical panels, source families, donor splits, nulls, thresholds, address universe and locality definitions;
- TD57C historical FAIL is immutable. A corrected-data PASS would be reported as a divergence, not a retroactive rescue;
- TD59 locality-fraction tuning is forbidden; no new fraction search is allowed;
- the replay adapter must first reproduce authenticated historical fixtures/semantic rows before it may consume corrected G6 output;
- after corrected TD56/57B/57C/59 replay, STOP again before target selection, TD60 or training.

## 8. Corrected substrate / custody anchors

- corrected S174 rebuilt RAR SHA-256: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`
- calibration bundle SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- TD41-TD58 historical archive SHA-256: `c84849f5568f526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` is NOT the archive hash; do not confuse it with the expression split part. The real TD41-TD58 archive hash is `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`.
- Sample-A freeze SHA-256: `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
- source provenance SHA-256: `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`
- collision ledger SHA-256: `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`

## 9. Preserved failed/superseded history

Never erase or reinterpret these:
- PR #245: pre-G4/G5 failure from Windows CRLF manifest serialization; no H5/value read.
- PR #252: hardened code failed at mapping entry because code used literal `sample == "A"` and conflated Sample-A occupancy with 35-file custody.
- PR #254: independent repeat of the same deterministic failure.
- PR #258: earlier standalone G6/G7 candidate; superseded before qualification.
- PR #263: successor with S174 immediate-use hardening; superseded before qualification after two further custody defects were found.
- PR #267: current successor; implemented but unqualified.

The correct Sample-A/custody contract is not "34 instead of 35". It is **34/34 Sample-A mapping plus 35/35 corrected-substrate custody**.

## 10. Chat/project-local asset custody

Large local binaries are not duplicated into Git. They are bound by exact filename, bytes, SHA-256 and archive/member manifests. Current inventory includes:
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` — 1,531,109 bytes — SHA `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` — provenance mismatch, DO NOT USE as authority.
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` — 410,278,055 bytes — SHA `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- discovery-expression split parts — 303,979,881 and 303,979,880 bytes — SHAs `b8163f...72b2e` and `5bc2ec...6875`.
- `checkpoints.zip` — 71,356,460 bytes — SHA `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`.
- `expression.zip` — 3,599,456 bytes — SHA `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`.
- `t1_checkpoint_u0200.zip` — 233,729,581 bytes — SHA `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`.
- `Status and Repair Plan.txt` and `WSL execution issue.txt` are preserved raw historical chat files on the handoff/audit custody surfaces.
- new chat-local `Pasted markdown.md` — 36,211 bytes — SHA `9ad8789389fa020b7432ec3a43d2fd4640ebaf34f52432fa88322671e61771a5`; it contains Macha's PR259 report plus parallel V79/Bayesian log material. It is preserved as history only and grants no target-discovery authority.

## 11. Immediate next action for the new agent

Do **not** run G6/G7.

First inspect the current PR #267 head and the qualification contract. Have the canonical machine qualify exactly `16f05bd3845565bb2c24d70143d447d7ef2b8904`:
1. fresh clean worktree at exact head;
2. run focused common/G6/G7 tests plus `test_td_g7_counterpart_attempt_custody.py`;
3. provide the exact PR259 driver and mapping receipt files, with exact physical SHAs `62f2...8bae` and `6a97...8e0`;
4. run the exact-PR259 compatibility test and require 1 passed / 0 skipped / 0 failed;
5. record environment/logs and confirm no production code edit, no authorization object, no G6/G7 execution, and no expression/count read;
6. open/preserve an evidence-only draft qualification record;
7. STOP for owner review.

If qualification fails: preserve the failure, do not patch in the execution worktree, do not silently rerun, and do not weaken the contract.

If qualification passes: it means only that the future value-reading machinery correctly recognizes the accepted G4/G5 evidence and satisfies the frozen custody tests. It still does not authorize a value read.

## 12. Absolute prohibitions

Without new explicit owner authority, do not:
- create a runtime G6/G7 value-read authorization;
- execute G6 or G7;
- execute corrected TD56/57B/57C/59/60;
- select a target or representation winner;
- merge the handoff/audit/execution-record PRs;
- authorize real training or Stage 4;
- tune to historical outcomes;
- rescue TD57C;
- call TD60 failed.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
