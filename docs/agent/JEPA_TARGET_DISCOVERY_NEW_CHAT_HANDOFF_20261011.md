# JEPA target-discovery takeover handoff — 2026-10-11

Status: `CURRENT_TAKEOVER_OVERLAY__NO_VALUE_AUTHORITY__NO_TARGET_AUTHORITY__NO_TRAINING_AUTHORITY`

Hard terminal:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the cold-start handoff for the **target-discovery lane only**. It supersedes older chat-level summaries where they disagree. Preserve historical failures; do not merge or rewrite them.

## Macha operator handoff

The new coordinator must also read:
- `docs/agent/JEPA_MACHA_OPERATOR_HANDOFF_20261011.md`
- `docs/agent/MACHA_NEXT_INSTRUCTION_PR267_20261011.md`
- `custody/takeover_20261011/MACHA_OPERATOR_STATE_20261011.json`

These define how to manage Macha as the canonical-machine execution worker, exactly what evidence to demand back, how to handle failure/PASS returns, and how to keep Macha's parallel Bayesian work authority-separated from target discovery.

The current Macha assignment is **qualify exact PR #267 head `16f05bd3845565bb2c24d70143d447d7ef2b8904`, then STOP**. Macha is not currently authorized to create a value-read authorization, run G6/G7, open corrected expression/count arrays, run corrected TD56/TD57B/TD57C/TD59/TD60, select a target, or train.

## 1. Current controlling surfaces

- Canonical handoff PR #247 branch `handoff/jepa-20261009-post-td-g4g5-crlf-bayes-complete`.
- Controlling audit/design PR #251 branch `review/td-g6g7-preauthorization-hardening-20261009`.
- Accepted corrected-substrate value-blind execution PR #259 head `80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947`.
- Current unqualified G6/G7 engineering candidate PR #267 head `16f05bd3845565bb2c24d70143d447d7ef2b8904`.

The self-contained takeover package is under `custody/takeover_20261011/` on both PR #247 and PR #251.

## 2. G4/G5 accepted PASS

PR #259 executed exact code `bf253a4dd62d943398f9ff59ed8b1e74777140a5` and established a value-blind corrected-substrate technical/data-integrity PASS only.

Exact physical evidence:
- driver receipt SHA-256 `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`
- mapping receipt SHA-256 `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`
- replay manifest SHA-256 `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Sample A is exactly `A_NATURAL_MIXTURE`: 25,000 cells, HVS 1,129 / NPH52 1,310 / SEA_AD 22,561.

Correct interpretation is **34/34 Sample-A mapping plus 35/35 corrected-substrate custody**. The non-Sample-A 35th HVS H5AD was byte-authenticated only.

No expression/count arrays were opened. G6/G7 were not run. No value-read authorization was created. No corrected biological replay occurred.

The PR259 driver/mapping JSON files retain platform CRLF bytes. Any later authority must bind their exact physical SHA values; never regenerate or normalize them.

## 3. Preserved failure history

- PR #245: `FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_BEFORE_G4_G5__MANIFEST_FILE_SHA_MISMATCH__WINDOWS_CRLF_SERIALIZATION`; no G4/G5/value read.
- PR #252: exact hardened code failed at G4/G5 mapping entry because literal `sample == "A"` conflicted with frozen `A_NATURAL_MIXTURE`, and Sample-A occupancy had been conflated with 35-file custody.
- PR #254: independent identical deterministic repeat.

Do not rerun/relabel these historical failures.

## 4. Current G6/G7 candidate

PR #267 branch `fix/td-g7-counterpart-auth-immutable-attempt-20261011`, exact head `16f05bd3845565bb2c24d70143d447d7ef2b8904`.

Status: `IMPLEMENTED__UNQUALIFIED__DO_NOT_EXECUTE_G6_G7`.

Relative to superseded PR #263 head `a509c59238bcdc60b88fa265e7e4473760a41025`, the bounded repair changes only:
- `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`
- `tests/v5/test_td_g7_counterpart_attempt_custody.py`

Repairs:
1. for overlap matrices, physical H5AD authenticates before S174 count-loader invocation;
2. immutable `STARTED_NOT_A_PASS` sidecar spends every G7 attempt after runtime authority + same-authority G6 PASS but before value-bearing work.

Existing immediate S174 reauthentication, duplicate ID/address rejection, exact G1b authority, zero-tolerance 9,216-address cross-check and non-success mismatch/NOT_ESTIMABLE rules remain.

No workflow has qualified the exact head. Do not claim tests passed.

Canonical qualification contract:
`docs/agent/TD_PR267_CANONICAL_QUALIFICATION_20261011.md`

Qualification must use exact PR259 receipts and the dedicated compatibility test must show `1 passed / 0 skipped / 0 failed`. A skip is not qualification.

After qualification, STOP for owner review. Qualification itself does not authorize G6/G7.

## 5. Owner-decision boundary

No owner-decision record exists. No runtime value-read authorization exists.

Even after PR #267 qualifies, future runtime value authority must bind an immutable explicit owner decision proving:
`AUTHORIZE_G6_G7_INTEGRITY_ONLY`

Controlling audit:
`docs/agent/TD_VALUE_AUTH_OWNER_DECISION_BINDING_AUDIT_20261010.md`

A future G6/G7 PASS would establish value integrity/corroboration only, not corrected biological recurrence.

## 6. Historical executor and fixture recovery

Authenticated Project-Library archive:
`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`
- Library id `file_00000000e9ec81f6a58dc73acf9d7807`
- bytes 92,478,083
- SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

Recovered exact executor SHAs:
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

Fresh historical-only local reruns reproduced archived output bytes exactly for TD56 HVS/NPH52/SEA_AD, TD57B Panel-0 HVS/NPH52, TD57B Panel-1 HVS/NPH52, and TD57C Panel-0 HVS including the historical FAIL and expected non-success exit.

Do not claim a new local TD57B SEA_AD replay: those two heavy cases were not completed in this coordinator container. The historical project self-audit separately records exact-fast SEA_AD replays as byte-identical.

NPH52 pass-through audit on the exact authenticated historical CSR found 0/1,310 NPH52 Sample-A rows and 0/25,000 Sample-A rows with duplicate CSR address indices.

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
- after corrected TD56/TD57B/TD57C/TD59 replay, STOP again before target selection, TD60 or training.

## 8. Corrected substrate / custody anchors

- corrected S174 rebuilt RAR SHA-256: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`
- calibration bundle SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- TD41-TD58 historical archive SHA-256: `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`
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
- discovery-expression split parts — 303,979,881 and 303,979,880 bytes — SHAs `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` and `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`.
- `checkpoints.zip` — 71,356,460 bytes — SHA `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`.
- `expression.zip` — 3,599,456 bytes — SHA `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`.
- `t1_checkpoint_u0200.zip` — 233,729,581 bytes — SHA `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`.
- `Status and Repair Plan.txt` and `WSL execution issue.txt` are preserved raw historical chat files on the handoff/audit custody surfaces.
- `Pasted markdown.md` — 36,211 bytes — SHA `9ad8789389fa020b7432ec3a43d2fd4640ebaf34f52432fa88322671e61771a5`; raw chat history only, no target-discovery authority.

## 11. Immediate next action for the new agent

Do **not** run G6/G7.

First read the Macha operator handoff and send Macha the frozen PR267 qualification instruction. Then independently audit Macha's evidence-only return.

For PR267 qualification itself:
1. fresh clean worktree at exact head;
2. run focused common/G6/G7 tests plus `test_td_g7_counterpart_attempt_custody.py`;
3. provide the exact PR259 driver and mapping receipt files, with exact physical SHAs `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae` and `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`;
4. run the exact-PR259 compatibility test and require 1 passed / 0 skipped / 0 failed;
5. record environment/logs and confirm no production code edit, no authorization object, no G6/G7 execution, and no expression/count read;
6. open/preserve an evidence-only draft qualification record;
7. STOP for owner review.

If qualification passes, it establishes only that the future value path's engineering/custody gate is qualified. It does not authorize value reading.

## 12. Hard interpretation rules

- G4/G5 PASS = corrected mapping/custody integrity, not biology.
- Future G6/G7 PASS = corrected value integrity/corroboration, not biology.
- Historical TD56/57B/59 = historical evidence requiring corrected replay.
- Historical TD57C FAIL stays failed historically.
- TD60 remains never qualifyingly executed, not failed.
- No target or representation winner exists.
- No real training or Stage 4 is authorized.
- Keep the Bayesian sidecar lane authority-separated; PR #249 remains terminal `SAMPLER_NOT_ESTIMABLE` and must not be tuned to historical outcomes.
