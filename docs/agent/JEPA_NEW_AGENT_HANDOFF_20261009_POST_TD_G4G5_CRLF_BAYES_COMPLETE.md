# JEPA new-agent cold-start handoff — 2026-10-09 — V2

Status: `CURRENT_COLD_START__POST_G4G5_CRLF_REPAIR__BAYES_METHOD_TERMINATED__G6_G7_PREAUTH_HARDENED`

This is the current long-form cold-start surface for the JEPA project. Do **not** reconstruct the project from old chats or broad branch archaeology. Read this file, then:

- `custody/handoff_20261009/JEPA_CURRENT_TAKEOVER_STATE_20261009.json`
- `custody/handoff_20261009/JEPA_CURRENT_ARTIFACT_LOCATOR_20261009.csv`

The machine-state JSON is the most compact controlling state if this prose and an older document ever conflict.

## 1. Hard authority terminal

The project remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Also preserve:

- TEST sealed;
- DEV/SEALED/pathology surfaces unopened unless separately authorized;
- Morabito protected;
- no target winner;
- no representation winner;
- no production EMA/model choice;
- no TD60 execution authority;
- no G6/G7 value-read authority;
- no corrected TD56/TD57B/TD59 biological replay authority;
- no real training.

A code/test PASS never creates scientific authority by itself.

## 2. Current GitHub control surfaces

### PR #237 — custody/scientific-history base

Branch:
`handoff/jepa-20261008-complete-runtime-s174-takeover`

Head:
`813ead17570dbb4b6a5a58ebe6dc84fed8aa0438`

Role: custody and scientific history only. Do not resurrect its old search for a missing corrected-replay bridge; that work is closed.

### PR #243 — target-discovery implementation base

Branch:
`impl/td-relational-corrected-preflight-20261009`

Head at handoff base:
`6716f044fcbefeb39bddf505c09a82378ce602e8`

Role: recovered/frozen G1-G7 implementation lineage plus historical preregistration documents. It is no longer the complete live execution frontier by itself; see #248 and #251.

### PR #244 — S174 transfer custody PASS

Branch:
`custody/s174-cache-transfer-verification-20261009`

Head:
`eb3f92045e95ee4e5a85a864d1ec5922fe8f3d16`

Terminal:
`PASS_S174_RAR_EXACTLY_MATCHES_G1B_AUTHORIZED_CORRECTED_CACHE`

The transferred RAR is 47,964,366 bytes with SHA-256:

`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

84/84 files match the G1b-authorized corrected cache exactly. This is custody evidence, not new biological science.

### PR #245 — preserved first canonical G4/G5 execution failure

Branch:
`exec/td-relational-g4g5-local-20261009`

Head:
`bf6ddda4e1b020fdb959812036b957c40166fede`

Terminal:

`FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_BEFORE_G4_G5__MANIFEST_FILE_SHA_MISMATCH__WINDOWS_CRLF_SERIALIZATION`

Important interpretation:

- G4/G5 did **not** execute;
- mapping audit never started;
- no expression arrays were opened;
- all required authorities and all 35 HVS/SEA-AD H5ADs were authenticated;
- builder passed its internal checks and generated the correct frozen manifest content in memory;
- Windows CRLF physical serialization changed the file SHA and the driver failed closed;
- the preserved failed namespace must never be edited or reused.

### PR #248 — live G4/G5 repair and canonical rerun surface

Branch:
`fix/td-preflight-platform-stable-serialization-20261009`

Current recorded head:
`1ecb3a5eebbeccfec7a6cce95a75ae4cfe498049`

Repair-code freeze:
`1dbf37d5c9a4684e4bac73b9a86fb3875782e23e`

Repairs:

1. manifest physical bytes are written explicitly as UTF-8 LF bytes;
2. preflight freshness rejects any non-empty immutable namespace, not only a final result file.

Canonical rerun namespace:

`results/target_discovery/td_relational_corrected_replay_20261009/preflight_v2_post_crlf_repair`

Required success evidence:

- physical manifest SHA-256 exactly `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
- zero CRLF byte pairs;
- mapping terminal `PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`;
- driver terminal `PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`.

Any failure is preserved and stops. Even both PASS terminals only permit an owner decision about G6/G7; they do not authorize values.

### PR #249 — Bayesian method spike TERMINATED

Branch:
`analysis/td-bayesian-historical-ledger-20261009`

Controlling terminal:
`SAMPLER_NOT_ESTIMABLE`

Disposition:
`STOP_THIS_BAYESIAN_FORMULATION__DO_NOT_TUNE_TO_HISTORICAL_OUTCOMES`

What was learned safely:

- the 52 historical TD57B/TD57C/TD59 case rows are not 52 independent experiments;
- they collapse to at most seven stage×source blocks under the dependency-safe ledger;
- TD57C has only HVS prospective evidence because its sequential firewall stopped before other sources;
- historical PASS/FAIL labels were excluded from the modeling ledger;
- duplicate/missing/extra pseudo-cases fail closed.

The synthetic calibration was run **before any historical Bayesian fit**. It failed both sampler-quality and source-general-replication expectations. One-source-only and sign-flip scenarios remained too strongly positive; shared-positive recovery was prior-sensitive.

Therefore:

- no historical Bayesian fit was run;
- no posterior result exists for TD57B/TD57C/TD59;
- no corrected replay was ingested;
- do not lengthen chains/change priors/thresholds/estimands to force this formulation to pass;
- do not revive it with corrected replay;
- any future Bayesian/replication method requires a new prospective scientific question and preregistration.

### PR #251 — G6/G7 preauthorization hardening

Branch:
`review/td-g6g7-preauthorization-hardening-20261009`

Current recorded review head:
`9f06d31875938d73028fccfb6774cf0fb33c70fb`

Role: preauthorization-only review. No corrected expression values were read and no authority was created.

Two dormant defects were found before execution:

1. historical G6 V1 used `int(round(float(v)))` on physical H5AD values. G4/G5 is value-blind, so this could silently round a fractional/transformed value instead of proving raw counts;
2. G7 correctly labeled zero natural S174 overlap as `NOT_ESTIMABLE`, but returned process exit code 0.

Prospective hardening:

- future G6 candidate entrypoint is `scripts/v5/materialize_td_relational_corrected_sampleA_v2.py`;
- V2 reuses frozen V1 mechanics but requires every physical HVS/SEA value to be finite, nonnegative, and exactly integer before normalization;
- direct historical V1 materializer invocation is outside any future authorization;
- G7 loads V2, rejects fractional S174 reference values, and returns process success only for `PASS_TD_G7_S174_EXACT_OVERLAP`;
- `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` is a non-pass/non-success state;
- the revised value-read authorization file remains a template only.

Even future G6+G7 PASS would stop before the actual corrected TD56/TD57B/TD59 biological replay.

## 3. S174 corrected-data context

Historical TRAIN cache had scrambled HVS and SEA-AD physical feature labels/columns. G1b rebuilt the affected shards through stable physical identifiers; NPH52 followed the unaffected qualified path.

Canonical corrected cache:

`D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`

Key corrected downstream findings:

- pooled cohort coverage explains about 3% of pooled correlation structure, not the earlier ~89% interpretation;
- median absolute real gene-gene correlation is about 0.056, not ~0.33;
- cell-class separation contributes about 26% of pooled correlation;
- earlier claims that latent mechanism was effectively solved / observation was the bottleneck are superseded;
- earlier factor-family falsification and substate/Observer-V2 support on the corrupted substrate are superseded;
- no candidate was accepted;
- detection continues to carry more dependence than expression.

S159 uncertainty bands remain diagnostic, not hard pass/fail gates.

## 4. Target-discovery historical scientific state

### TD34

Gene-universe genealogy is closed.

Current classification:

`TD34_EXACT_PANEL_MEMBERSHIP_REPRODUCED__CANONICAL_UPSTREAM_SUPPORT_BOUND__SELECTION_RULE_HASH_BOUND__NO_TARGET_AUTHORITY`

The exact all-42-operator common-scalar intersection is 17,186 molecular addresses.

### TD56

Historical result: two disjoint molecular views recover the same within-donor relational geometry.

Current classification:

`HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57B

Historical prospective result:

- two independent panels;
- HVS/NPH52/SEA-AD;
- two donor splits × two halves;
- 24/24 historical cases PASS;
- weakest historical margin +0.0375178074843.

Current classification:

`HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57C

Historical frozen terminal:

`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`

This remains a real historical failure of the nearest-one-third three-view local proposal. Post-failure unrestricted diagnostics cannot rescue or relabel it. A corrected-substrate replay is a distinct evidence object and must obey the original sequential firewall.

### TD58

`FALSIFICATION_ONLY__NO_TARGET_AUTHORITY`

### TD59

Historical nearest-half mesoscale evidence:

- 24/24 historical cases passed;
- weakest historical p95 margin +0.0011566307718604563;
- 22/24 beat the historical null maximum.

Current classification:

`TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

### TD60

`PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`

Never call TD60 failed. It was never qualifyingly executed.

## 5. Corrected relational replay contract

The corrected replay preserves the exact historical biological question while replacing the invalid HVS/SEA physical feature-column mapping with stable identifier resolution.

Historical Sample-A:

- HVS 1,129 cells;
- NPH52 1,310 cells;
- SEA-AD 22,561 cells;
- total 25,000 cells.

Sample-A freeze SHA-256:

`79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`

Exact replay allocation: 9,216 molecular addresses.

Manifest SHA-256:

`4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`

Allocation:

- positions 0..1023: TD56/TD57A/TD58;
- 1024..3071: TD57B;
- 3072..6143: TD57C;
- 6144..9215: TD59.

Corrected HVS/SEA value chain:

`matrix-native stable feature ID -> physical column -> canonical molecular address -> raw count -> historical normalization`

Normalization remains:

`log1p(raw_count * 10000 / whole-cell source_library)`

No replacement gene is allowed. Unresolved frozen identity is STOP / NOT_ESTIMABLE.

NPH52 remains the authenticated unaffected historical pass-through path.

## 6. Critical custody assets

Historical TD41-TD58 archive:

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

Bytes: 92,478,083

SHA-256:

`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

Calibration bundle authority:

`FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`

Bytes: 410,278,055

SHA-256:

`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Warning: a different same-named ~1.09-GB file exists under an exports path and is not the authority.

Stage81A2R provenance SHA-256:

`df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`

Stage81A3R collision ledger SHA-256:

`f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`

S174 transfer RAR SHA-256:

`88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`

## 7. 353 identity-warning mappings

The S174 identity lane records 353 historical Ensembl/address mappings whose current symbol differs.

Stable historical molecular identity remains binding. Do not substitute a preferred current symbol into a frozen panel. Before biological interpretation of a corrected TD replay, intersect the 9,216 replay addresses with this identity-warning set and report any overlap explicitly.

This is a semantic warning layer, not permission to alter mappings.

## 8. Synthetic/runtime lanes

Runtime mechanics are already substantially qualified under PRs #224/#226/#236 and are not the current blocker. Real training remains OFF.

Synthetic mechanism work on PRs #240/#242 did not promote an arm. Broad-class propagation had directional support but no adequate mechanism; later signed-detection/marginal repairs also remained inadequate.

Do not reopen those lanes unless a new reviewed cross-lane scientific design requires them.

## 9. Exact next-action order

1. Start from this #247 handoff plus the V2 machine-state JSON and artifact locator.
2. Do not redo broad project archaeology.
3. Macha qualifies the focused #248 G1-G5 tests in the canonical repository context.
4. Macha reruns value-blind G4/G5 on canonical Windows into:
   `results/target_discovery/td_relational_corrected_replay_20261009/preflight_v2_post_crlf_repair`
5. Any G4/G5 failure is preserved and stops the lane.
6. If G4/G5 passes, **stop** and return the evidence to the owner.
7. Before any owner G6/G7 authorization is acted on, qualify the #251 regression tests and bind the hardened V2 G6 + hardened G7 entrypoints.
8. Only after explicit owner authorization may G6/G7 read corrected values, and only within the exact historical Sample-A 25,000-cell / 9,216-address scope.
9. G6 mismatch stops.
10. G7 mismatch stops.
11. G7 `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` stops for owner adjudication and is not a PASS; do not manufacture overlap.
12. Even G6+G7 PASS stops before corrected TD56/TD57B/TD59 biological replay.
13. The actual corrected biological replay requires another explicit owner decision after G6/G7 receipt review.
14. Bayesian PR #249 remains terminated. Do not feed corrected replay into it.
15. Do not let any side experiment relabel TD57C, promote TD60, select a target, or authorize training.

## 10. What the next biologically meaningful result will be

The current work is still target discovery.

The next decisive biological question is **not** whether a new target idea can be invented. It is whether the historical relational structure that survived in TD56/TD57B/TD59 also survives when replayed on the corrected substrate.

We are not yet at that replay. The ordered safeguards are:

`G4/G5 identity/mapping -> owner decision -> G6/G7 corrected-value integrity -> owner decision -> corrected historical biological replay`

Only the final step can tell us whether the earlier relational biological findings survive corrected data.

## 11. Anti-resurrection rules

Do not resurrect:

- pre-S174 ~89% cohort-coverage interpretation;
- old median |r| ~0.33 corrected-real reference;
- latent-mechanism-solved / observation-bottleneck conclusion from corrupted S174;
- factor-family falsification or substate/Observer-V2 support derived from corrupted S174;
- search for a missing corrected TD replay implementation;
- TD60-failed wording;
- unrestricted TD57C post-failure diagnostics as rescue of the frozen failure;
- 24/24 related cases as 24 independent Bayesian replicates;
- PR #249 Bayesian formulation;
- S159 diagnostic bands as hard gates;
- direct future use of the historical G6 V1 materializer;
- G7 `NOT_ESTIMABLE` as PASS;
- any inference that passing engineering tests grants target/training authority.

## 12. Merge policy

All listed PRs remain draft/open custody, implementation, execution-record, or method-review surfaces unless separately changed by the owner.

Do not merge #237, #243, #244, #245, #247, #248, #249, or #251 into `main` without explicit owner authorization.

PR #244 is custody evidence.

PR #245 is a failed execution record.

PR #247 is the takeover surface.

PR #248 is the current G4/G5 engineering/rerun surface.

PR #249 is a terminated method spike.

PR #251 is preauthorization hardening only.
