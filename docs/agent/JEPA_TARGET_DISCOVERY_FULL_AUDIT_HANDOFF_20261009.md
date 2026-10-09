# JEPA target-discovery full audit handoff — 2026-10-09

## Purpose

This is the canonical cold-start handoff for the **target-discovery / biological-objective authority lane** after the historical audit work completed across the October takeover sessions.

It is intentionally conservative about scientific authority and intentionally aggressive about **not carrying stale RED findings forward once a later repair exists**.

The required reasoning pattern for every historical defect is:

**defect / finding → repair or recovery → verification → supersession / current authority**

Do not treat an old audit document as permanent scientific truth. Conversely, do not call an issue fixed from prose alone; bind the repair to exact code, inputs, outputs, hashes, CI/replay evidence, and exposure state.

This document is documentation/custody only. It does not authorize training, target freeze, representation freeze, Stage 4 advancement, production EMA selection, protected-data access, or any scientific promotion.

---

# 1. Start here: current PR and read order

Primary takeover PR:

- PR #237
- branch: `handoff/jepa-20261008-complete-runtime-s174-takeover`
- base: `impl/v77-bounded-synthetic-mutation-20261007`
- base SHA: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

Always re-read PR #237 before trusting a recorded latest head.

Recommended read order:

1. `docs/agent/JEPA_TARGET_DISCOVERY_FULL_AUDIT_HANDOFF_20261009.md` — this file
2. `docs/agent/TARGET_DISCOVERY_PRIMARY_ARTIFACT_LOCATOR_20261008.md`
3. `docs/agent/TARGET_DISCOVERY_CUSTODY_UPDATE_20261008.md`
4. `docs/agent/TD34_PANEL_RECONSTRUCTION_CANDIDATE_20261008.md`
5. `docs/agent/JEPA_FINAL_AGENT_HANDOFF_20261008_1757EDT.md`
6. `custody/target_discovery_20260907_recovered/README.md`
7. `custody/target_discovery_20260907_recovered/RECOVERED_PACKAGE_SHA256_MANIFEST.csv`
8. `custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`
9. `docs/agent/JEPA_COMPLETE_TAKEOVER_20261008.md`
10. `custody/takeover_20261008/MANIFEST.json`
11. `custody/takeover_20261008/s174_working_snapshot/`

Do **not** search PR #237 alone. Several decision-bearing historical artifacts live only on historical branches.

---

# 2. Executive authority state

## Runtime / engineering lane

The bounded synthetic one-update rehearsal is GREEN and physically bound. This establishes runtime mechanics only, not biological target authority.

Key lineage:

- PR #224 runtime head: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`
- PR #226 shared qualification interface: `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`
- PR #228 joined V77 ZERO_UPDATE: `6282b59c7bd961c0dfb99d3cb24bdd55fe2526f7`
- PR #232 physical provenance: `d3430ce6c0e878272e92b61e01822334e088d8c8`
- PR #233 2K operator smoke: `c919d957de79a3866fdaeab3ae2ae5a0891d4859`
- PR #235 bounded mutation contract: `71a3d6d84a36e1812ffd776153d48948bd8b945c`
- implementation/test head: `8dabe9ef9ed87b4beaf00acefda1a3073ed751de`
- PR #236 audit-record head: `8495c9f0a753dbb25c90bc27e65f28c4ee2e471e`

Successful bounded rehearsal:

- workflow run `37712331165` — SUCCESS
- job `113100879103`
- 51 focused tests passed
- optimizer step `0 -> 1`
- teacher presentations `0 -> 2`
- online/student and predictor changed
- teacher changed only via permitted post-completion EMA
- exact restore in fresh modules verified
- `execution_authorized=false`
- `training_authorized=false`
- `production_promotable=false`

Historical RED→GREEN audit:

- pre-audit implementation: `c59db70046c5dcc7c6c8be6e30bebb745604cad5`
- RED tests: `f0de464fcf921c14a96ef75df806075cc5b69da2`
- expected-failure CI `37711581663`: 45 pass / 5 fail
- repair: `6f9f51704431825c4d95649944c7613a77c4dcf6`
- repaired CI `37712004919`: 50 pass
- final physical-proof adversary: `8dabe9ef9ed87b4beaf00acefda1a3073ed751de`: 51 pass

Do not infer biological authority from this lane.

## Current biological/target authority

At this handoff:

- no production biological target is qualified
- no representation is frozen
- no Stage 4 advancement is authorized
- no real-data training is authorized
- no production EMA is selected
- no corrected-S174 diagnostic interval is an authorization threshold

The important correction is that the **HVS/SEA-AD feature-axis defect itself is no longer an open blocker**. It was prospectively repaired and replayed. The remaining work is to map which historical target-discovery conclusions were replayed or superseded on corrected substrate.

---

# 3. Evidence-status vocabulary

Use these labels for custody/provenance:

- `PHYSICALLY VERIFIED`
- `HASH-REFERENCED`
- `PROSE-ONLY`
- `MISSING SOURCE`
- `MISSING ARTIFACT`
- `REPRODUCED`
- `CONTRADICTED`

For defect status use:

- `FIXED__VERIFIED`
- `FIXED__REPLAYED`
- `PARTIALLY_FIXED`
- `SUPERSEDED_BY_NEW_DESIGN`
- `STILL_OPEN`
- `NOT_DISCOVERABLE_YET`

Do not use `MISSING` merely because a hash search failed once. Prefer `not discoverable yet` unless the search is exhaustive.

The target evidence graph should be reconstructed as:

`TD stage → exact commit → producer code → immutable inputs → panel manifest → pair manifest → output artifact → hashes → analysis/exposure status → claimed conclusion → independently reproducible? → substrate/materializer validity → repair/replay state → superseding authority`

Keep scientific conclusion and custody conclusion separate.

---

# 4. Critical S174 correction: HVS/SEA-AD feature axis is repaired

Historical old cache defect:

- HVS/SEA-AD feature-axis mapping had been scrambled by using family `source_feature_index` semantics against physical matrix columns.
- NPH52 was not affected by the same defect.

Prospective repair freeze:

- branch: `claude/s174-train-cache-rebuild-20261007`
- freeze commit: `cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef`
- receipt: `results/v77/S174_REBUILD_FREEZE_V1.json`
- status: `FROZEN__NO_COUNT_READ`

Repair semantics:

- physical var identifier → family provenance `source_exact_ensembl_id` → `molecular_address_index`
- never use family `source_feature_index` as a physical-column selector
- collisions excluded, never summed; recorded as `MEASURED_COLLISION_UNRESOLVED`
- old cache never modified
- cells/order preserved exactly from old cache
- NPH carried over byte-identically
- physical H5AD sources hashed before count read

Observed mapping correction recorded at freeze:

- 24 HVS matrices: 18,736/18,736 columns map by gene ID; 18,735 mapped columns differ from old positional address
- 11 SEA-AD matrices: 35,076 columns map by gene ID; 1,525 excluded as frozen ledger collisions; 35,075 move
- 7 NPH shards carried over byte-identically

Corrected replay:

- commit `46d8eaa8fa23cd60762a8a90c55b84e8d86364b2`
- CI `37693603160` — 146 passed, zero skipped

Later S174 handoff:

- `docs/agent/JEPA_FINAL_V77_S174_NEW_AGENT_TAKEOVER_20261007.md`
- commit `15c21bdc298e3ff0b262bdbab6121d4298aa55f1`

Live successor branch later advanced to:

- `claude/s174-train-cache-rebuild-20261007@f88338713b173edb3acbc90662e607ce45b5878b`

Current classification:

`DEFECT_CONFIRMED → PROSPECTIVE_REBUILD_FROZEN → PHYSICAL_GENE_ID_REBUILD → CORRECTED_REPLAY_PERFORMED`

Do **not** classify this feature-axis defect as an unresolved current blocker.

Open question is narrower:

**Which TD34–TD60 historical experiments were explicitly replayed/rematerialized on corrected physical substrate, versus merely reproduced on their historical substrate?**

---

# 5. Recovered Sept. 7 primary target-discovery custody

Historical package:

`JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

Recovered in the takeover chat and authenticated:

- bytes: `1664383`
- SHA-256: `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- expected historical SHA-256: exact match
- extracted files: 97

Embedded handoff:

`JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.md`

SHA-256:

`5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`

Exact historical match.

Durable takeover copies / indexes:

- `custody/target_discovery_20260907_recovered/README.md`
- `custody/target_discovery_20260907_recovered/RECOVERED_PACKAGE_SHA256_MANIFEST.csv`
- `custody/target_discovery_20260907_recovered/td_iteration34_state_geometry_globalrow.py`

The GitHub connector used for takeover documentation is text-only, so the binary ZIP itself was not committed. Its exact identity and authority-critical extracted text bytes are preserved.

Important package contents include:

- `CORE_INPUT_HASHES.csv` — zero bytes / empty; do not mistake this for a populated upstream hash ledger
- `PACKAGE_MANIFEST.csv`
- `LOCAL_ARTIFACT_MANIFEST.csv`
- `context/FOUNDATION_TARGET_DISCOVERY_PROSPECTIVE_CONTRACT_V1.md`
- `context/PROJECT_HISTORY_TARGET_DISCOVERY_DECISIONS_20260907.md`
- TD23 through TD36 scripts
- TD13 through TD36 evidence outputs

Important producer scripts in package:

- `scripts/td_iteration23_row_alias_forensic.py`
- `scripts/td_iteration24_depth_attack_corrected.py`
- `scripts/td_iteration25_state_geometry_corrected.py`
- `scripts/td_iteration26_label_firewalled_state_discovery.py`
- `scripts/td_iteration29_pairunit_label_free.py`
- `scripts/td_iteration29a_pairunit_falsification.py`
- `scripts/td_iteration30_diffusion_signature.py`
- `scripts/td_iteration31_source_conditional_subspace.py`
- `scripts/td_iteration31a_source_conditional_falsification.py`
- `scripts/td_iteration31b_splitfit_preprocess.py`
- `scripts/td_iteration32_countsplit_measurement.py`
- `scripts/td_iteration33_global_row_binding_guard.py`
- `scripts/td_iteration34_state_geometry_globalrow.py`
- `scripts/td_iteration35_source_conditional_globalrow.py`
- `scripts/td_iteration36_class_conditioned_subspace.py`

---

# 6. TD34/S149 genealogy: materially superseded old audit

Historical Oct. 6 audit:

- branch: `audit/td34-genealogy-s149-20261006`
- head: `efa5c21db479f2feb78892356af3eef42c2886d2`
- document: `docs/agent/JEPA_TAKEOVER_PIPELINE_ARTEFACT_TD34_GENEALOGY_CHECKPOINT_20261006.md`

That audit correctly reported, **at that time**, that only the TD34 summary and producer hash were visible in historical Git and therefore classified all four panels:

`INDETERMINATE__PRIMARY_PROVENANCE_MISSING`

That classification is now partially superseded.

Recovered authentic producer:

`scripts/td_iteration34_state_geometry_globalrow.py`

SHA-256:

`1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`

This exactly matches the producer hash recorded by the Oct. 6 audit.

Authentic panel rule recovered from source:

```python
common=np.where((states==1).all(0))[0]
ordered=np.array(sorted(common,key=lambda x:hashlib.sha256(f'TD25|{int(x)}'.encode()).digest()),dtype=np.int32)
panels=[ordered[i*512:(i+1)*512] for i in range(4)]
```

Therefore the four panels were deterministic hash slices of the common scalar support space, not selected by pathology, labels, outcomes, expression magnitude, source-specific correlation, or post-hoc covariance.

Producer input relevant to panel membership:

`/mnt/data/td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

The upstream NPZ is **not inside the recovered ZIP**.

The recovered Sept. 7 handoff independently states the common scalar comparison space was 17,186 Molecular Ledger addresses scalar-measured in all 42 operators.

Current TD34 producer/genealogy classification:

`PRIMARY_PRODUCER_RECOVERED_AND_HASH_VERIFIED__SELECTION_RULE_RECOVERED__UPSTREAM_SUPPORT_ARRAY_BINDING_PENDING`

Historical TD34 closure starting point:

- commit `ff85f5bb18dc7d438113c3a5662856a360d2cd8f`
- `target_discovery/HANDOFF_CURRENT_20260907.md`
- `target_discovery/iterations/TD30_TD36_CLOSURE_LEDGER.md`
- `target_discovery/iterations/td34_state_geometry_globalrow/TD34_SUMMARY.csv`

TD34 itself remains validation/falsification scaffolding, not target authority.

Its own status was:

`FALSIFICATION_ONLY__LABELS_USED_FOR_VALIDATION__NOT_TARGET_AUTHORITY`

with `pathology_accessed=False` and `protected_expression_accessed=False`.

---

# 7. TD34 candidate exact-panel reconstruction lead

Authenticated recovered file:

`evidence/td_iteration21b_estimability_sweep/TD21B_GENE_MEASUREMENT_RELIABILITY.csv`

Package SHA-256:

`da8aaedf38045b47d85fb219ccca4fa8c9709d06e74dd76d108d746ea0e2222c`

Observed in takeover analysis:

- exactly 17,186 unique `gene_index` values in each broad-class block
- the two sorted address vectors are identical
- surrounding authenticated TD21B summary identifies the universe as `common_scalar: 17186`

Applying the authentic TD34 ordering rule to that candidate equivalent support vector gives candidate panel hashes:

- panel 0: `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976`
- panel 1: `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44`
- panel 2: `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56`
- panel 3: `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5`

Candidate 2,048-address manifest SHA-256 generated during takeover:

`c3d706e62b7de5eec67a2aa78f91e376df976038ce7dfc3b6b1106bf39aced2c`

This is **candidate reconstruction**, not final genealogy closure.

Durable note:

`docs/agent/TD34_PANEL_RECONSTRUCTION_CANDIDATE_20261008.md`

Required closure test:

1. recover/hash-bind original `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`, **or**
2. recover a historical TD41/TD43 panel or pair manifest whose panel membership independently matches these 2,048 addresses.

If either succeeds, promote from candidate reconstruction to closed panel genealogy with explicit hashes.

---

# 8. Package-manifest discrepancy that still deserves one forensic check

`PACKAGE_MANIFEST.csv` and `LOCAL_ARTIFACT_MANIFEST.csv` do not always record the same SHA for TD34 outputs.

Examples observed during takeover:

- TD34 geometry packaged hash: `59663057360e059fe56cc2844fede3ab689d8890e1535a42fee01247973ad0b2`
- corresponding local-artifact hash: `4bb128f53e4b7bbcf9f5c2548523e434eba8cd8a606d336ba74d137eb644a43e`

- TD34 summary CSV packaged hash: `201e7c04a447ff4b6dab37b6895a91590a54ca5c1b90cb1e05daa6c9d96e3abe`
- corresponding local-artifact hash: `315f3bbbb21cb82037d69248758602e5818886482719b12197634c690d380765`

- TD34 summary JSON packaged hash: `8a144fee23fac88d9698e65dac2fc3eff5aa3560268a0315daec482db6c19027`
- corresponding local-artifact hash: `8ff8f33d66ba03abf8b7c89913e7b28e3d20aaf88bc2fefd8f369b97775614d6`

`TD25_STATE_SELECTION.csv` remained identical across both manifests.

Do not assume tampering. First test newline normalization, packaging transformation, regenerated metadata fields, or serialization differences. Record exact byte diff if investigated.

---

# 9. TD41 / TD43 measurement forensic lane

Historical commits:

- `54f67f5cd5138c47311e95441b4895076ffb7bfc`
- `fa33944589b84d4dbf7d28dd19c743bf83843569`
- `77d546710d2c5c58dac3f5aea5555591763616fe`
- `780f2dfd16094e3b748dbb0e533de21f94bb93c2`
- tree `5907b7e949a50ae626950f8434b18fd8e08c35c4`

Historical closure characteristics:

- exact common-scalar support requirement
- complete-pair convergence requirement
- matched-null excess requirement
- 24/24 reconstructed cases
- 0 support violations
- no target authority

Two exact deciding-script SHA-256 values were preserved historically but source bytes were not recovered at the earlier audit checkpoint:

- `e14164f406a4f657e5921baff2396c9b108123eed7e30ac5e955dd2c0cd51e7d`
- `144123d2f4c4aa4cb3833ede1d121fb39be1042d551c4f86b074c3ccf8cf19a2`

Old classification:

`HASH-REFERENCED / SOURCE NOT YET PHYSICALLY VERIFIED`

Next-agent priority:

Search later archive/custody branches for these exact hashes and for panel/pair manifests. If TD41 panel identity matches the TD34 candidate reconstruction, that can close the missing TD34 membership binding without the original support NPZ.

Do not infer that 24/24 measurement reconstruction automatically makes TD41/43 target authority.

---

# 10. Sept. 8 relational reframe: important conceptual pivot

Historical handoff:

`target_discovery/HANDOFF_CURRENT_20260908.md`

The September target-discovery program explicitly pivoted from searching for another fixed target tensor into:

`TARGET_DISCOVERY -> RELATIONAL_OBJECTIVE_QUALIFICATION`

Key conceptual conclusions:

- do not restart fixed-coordinate target search
- do not start u1 training
- protected reader_validation / reader_oracle / DEV / SEALED / external holdout / pathology remain closed
- the historical 50k archive is falsification-only
- TD44–47 raw inversion-field targets failed
- TD48–55 query ordinal coordinate mappings failed
- TD54 was `NOT_ESTIMABLE` because of hash-bit ambiguity
- failures involved donor recurrence, source replication, correct-cell alignment, or measurability
- named universal coordinate search was abandoned

This matters when interpreting TD56–TD60. Those stages are relational-objective science, not a hidden return to a fixed target tensor.

---

# 11. TD56 historical scientific result

Key commits:

- freeze `d257fd3cf4957ecbb1ab3f03a06e54d043a1326f`
- result `f879af2e0bfc1981bb8a65b07f76e7998fda2774`
- reframe `9f87e3578ff871242ba14174aa8a71902da13b6b`

Object:

- disjoint 512-gene X/Y views
- 2,048 fixed hash-ranked pair-order coordinates per view
- within donor×operator cell-cell concordance distance
- matched Y-cell null preserving donor/operator/depth/detection

Primary historical values:

- HVS: `0.7975611` vs p95 `0.5541568`
- NPH52: `0.8007195` vs p95 `0.5990585`
- SEA_AD: `0.8782250` vs p95 `0.7526606`

All historical source-level tests passed. Independent numeric-pair hashing and a second nonoverlapping 2,048-pair block also passed.

Historical interpretation:

disjoint molecular views encode the same within-donor relational biology.

Current audit status:

**scientifically documented historically; corrected-substrate replay mapping not yet established.**

The next agent must determine whether TD56 was explicitly rerun/rematerialized after the HVS/SEA-AD physical feature-axis repair.

---

# 12. TD57A: quarantined exploratory lane

Commits:

- `94799072b62e9efe6156744ae2449b5ed6c2908f`
- `1ab86fc57ce2fd4f888dac0a285b3e85e6a1ed97`
- quarantine `0954e0a386de602047911ef6293ac423ce22f6d4`

Quarantine file:

`target_discovery/iterations/td57a_exploratory_quarantine/TD57A_EXPLORATORY_QUARANTINE.md`

Status:

`EXPLORATORY_OUTCOME_SEEN_BEFORE_FREEZE__NOT_DECISION_BEARING`

Local script hashes recorded historically:

- `run_td57_source.py` — `67c8fce216503ff5a21d36d77752cc946d5c4c07f9ac5e3e7685ef55b4536199`
- `run_td57a_source.py` — `cca6894b4635a8305eb461233218eb1cf59c8387f33710acb3696b02f1b22730`
- `run_td57a_nullspecific.py` — `c3989fd0e5524b51610a05480210ca96518d73480cb4a2138340e77eb93b3ef8`
- `run_td57a_nullspecific_last.py` — `19992c35da513a3ef31b771d95ad91b5c909e83dbedefe61e781a2d6c6fcaa0b`

Terminal:

`TD57A_EXPLORATORY_QUARANTINED__NEW_INDEPENDENT_FREEZE_REQUIRED`

Do not promote TD57A later because downstream ideas resemble it. Its exposure history remains disqualifying for decision authority.

---

# 13. TD57B: independent donor-recurrent scale-free relational order

Key commits:

- `ae18a2224cecb73daa3e4c748195dbde7c8f6b4f`
- freeze `dccf186868f5ff7070d7e6b32cbb0fef0a6d7cdb`
- executor bind `4de0920244309376415b37bcef9e2edd9898933c`
- fast SEA freeze `dfc08d570c29e76c5e3d58d593575a3ba8240f04`
- kernel bind `6fa084fe24757e2da443fc58e8073e843d1b77cd`
- Panel0 pass `a56398b2957ba2c263ec82f4715349ab77e79c86`
- 24-case table `584b3ae9fd767dbad4fa765e7847288a762943b1`
- close `e50f065bf46446460f900f6c12a94fc364fdfbf6`
- handoff `52f9e2210beeec76a90110c705a5da73c203600e`

Design:

- gene ranking positions 1024..3071, disjoint from TD56/TD57A
- Panel0 X 1024..1535, Y 1536..2047
- Panel1 X 2048..2559, Y 2560..3071
- 2,048 fixed hash-ranked unordered pairs/view
- scale-free ternary order: `q(i;j,k)=sign(d(i,j)-d(i,k))`
- two deterministic donor splits × two halves
- matched Y null within donor×operator depth/detection blocks
- 64 deterministic nonzero cyclic shifts
- null-specific support

Historical result:

- 24/24 PASS
- weakest `obs-null_p95` margin: `+0.0375178074843`
- weakest `obs-null_max` margin: `+0.0326836261591`

Terminal:

`TD57B_INDEPENDENT_DONOR_RECURRENT_SCALE_FREE_RELATIONAL_ORDER_SURVIVES__FREEZE_LOCAL_NEIGHBORHOOD_STABILITY_GATE_NEXT`

Current audit status:

historically strong and prospective, but **exact corrected-substrate replay status still must be bound**.

---

# 14. TD57C: preserve the failure

Commits:

- `1a38eccaeaf55ddd2a88f5d3b9a573d7de037286`
- `07775de9dc08c4540368bb782b4d3452e47ce099`
- `52f9e2210beeec76a90110c705a5da73c203600e`
- `d224dacd420d914f555987707102471ae82c8b3a`

Locality feasibility:

- nearest 1/4: 7 HVS donors
- nearest 1/3: 17 donors
- nearest 1/2: 29 donors
- prospective freeze selected nearest 1/3

HVS Panel0 results:

- split0/H0: FAIL `0.5370` vs `0.5556`
- split0/H1: PASS `0.5872` vs `0.5865`
- split1/H0: FAIL `0.5417` vs `0.5806`
- split1/H1: PASS `0.5872` vs `0.5833`

2/4 failed; sequential firewall stopped NPH52, SEA_AD and Panel1.

Replay was byte-identical; direct/vectorized max difference was 0.

Terminal:

`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`

Unrestricted diagnostic on the same panel passed 4/4, but that does not rescue the prospectively frozen nearest-third gate.

Preserve TD57C as a genuine prospective failure unless a later **distinct, prospectively frozen** experiment explicitly supersedes it.

---

# 15. TD58: useful but authority-contaminated by TD57A predecessor

Freeze:

`0ef3ce5e4ca5ce49137fc82042e8474af49f3287`

Result:

`9420a91401766110f730cd106c8fe19f6bf76886`

File:

`target_discovery/iterations/td58s_primary60_partial_evidence_triplet/TD58S_PROSPECTIVE_SCREEN.md`

Status:

`FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY`

Design explicitly reused TD57A views/pairs/sampler/strata/donor recurrence/null. It tested partial evidence:

- visible genes: 307/512 = 59.96%
- two fixed masks
- 2,048 visible pair coordinates
- fresh donor splits
- null-specific support
- HVS → NPH52 → SEA sequential stop

Result:

`TD58S_PRIMARY60_PARTIAL_EVIDENCE_RELATIONAL_TARGET_SURVIVES__NO_TARGET_AUTHORITY`

24/24 PASS.

Interpretation:

useful falsification / robustness evidence, but not a clean authority spine because its object lineage traces to quarantined TD57A.

---

# 16. TD59: mesoscale nearest-half survival + independent replay closure

Historical chronology includes:

- `ecb34b13291c8e208f960a1561dab6ae60d1c0ac`
- `f3eb86d26a306fe99ae2848dca89e9f2e9e25207`
- `864651fbe56b973f6645866624513e827c2c54da`
- `4a27575bb2bc37617624a266b888f8ec0d36080c`
- `fabdf334d44610489d31b7aaa637b6745e57716b`
- `91a782c92b5d0d02358e3481a08395819c77f905`
- `9cea9048f950864a5924021d7f4cfdee3191e8e2`

Replay/repair commits:

- `628af6ad125a975c174876af8184789f40a9b1f4`
- `49496a0b1a4f442533b6d3c349ff5dbbd7a52887`
- `963fe77f67f53de4434facf7e8346fa4f9eb7793`
- `17c22e780f759a0af1b28ad1c887f5401c1f37dc`
- `9caa1b19e5b34acd19d61a204e9944d492502603`
- `33d9e01185783cd379e3823c02f557e878573d64`

Historical design:

- two fresh Z/X/Y panels
- HVS, NPH52, SEA_AD
- two donor splits × two halves
- nearest-third failed previously; nearest-half tested as mesoscale boundary

Historical result:

- 24/24 under `obs > .5` and `obs > null p95`
- weakest `obs-null_p95`: `+0.0011566307718604563`
- 22/24 beat null max; two exceptions were Panel0 HVS

Terminal:

`TD59_NEAREST_HALF_MESOSCALE_RELATIONAL_RECURRENCE_SURVIVES__PILOT_FRONTIER_BRACKETED_BETWEEN_ONE_THIRD_AND_ONE_HALF__NO_TRAINING_AUTHORITY`

Independent reconstruction closure at `9caa1...`:

`PASS_TD59_REPLAY_CLOSURE_BY_INDEPENDENT_RECONSTRUCTION__ORIGINAL_EXECUTOR_BYTES_NOT_RECOVERED`

Recorded there:

- successor executor SHA-256: `870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`
- manifest root: `f379301555831bb32fe227ac578b33659e58adac8a71e88a17a3f06a9e332237`
- 24/24 exact rows reproduced
- observed / null_p95 / null_max reproduced
- six pair hashes reproduced
- original executor SHA: `3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0`
- `original_executor_bytes_recovered=false`
- `original_result_json_bytes_recovered=false`
- `scientific_terminal_changed=false`

Important distinction:

This establishes **scientific-statistic reproducibility** of the historical result. It does **not automatically establish corrected physical-substrate biological validity**.

Highest-priority TD59 question:

Was the independent replay reconstructing historical defective HVS/SEA values, or was there a later replay on the corrected gene-ID physical substrate? Search successor branches before deciding current biological authority.

---

# 17. TD60: frozen design, historical blocked state

Historical design commits:

- `79c893ab27f87c1c2c4e57241bfc3af8d855a250`
- `fbfb2e414216233acc4c757d5d53d507e93c03af`

Historical design:

- no new panel/locality search
- reuse TD57B global + TD59 mesoscale mechanics
- decision state: successor u40 EMA only
- u0 references only
- u10–u205 ineligible
- 160-D `cell_state`
- cosine distance
- anchored triplet order
- matched wrong-cell Y null
- full gate: 24/24 global + 24/24 mesoscale = 48/48

Historical blocker:

Claude V3 terminal mismatch with overlay validator. Teacher/student lane untouched; training unauthorized.

No qualifying TD60 PASS/FAIL execution was recovered in the historical audit.

Classification at takeover:

`PROSPECTIVELY_FROZEN / BLOCKED / RESULT_NOT_YET_RECOVERED`

Next-agent task:

Search later objective/representation branches to determine whether TD60 was actually executed later, explicitly superseded, or abandoned in favor of later V5/V64/V77 architecture/premise work. Do not silently convert “blocked” into “failed.”

---

# 18. G2 / PIPELINE_ARTEFACT_m

Primary historical audit location:

- `audit/td34-genealogy-s149-20261006@efa5c21db479f2feb78892356af3eef42c2886d2`
- `docs/agent/JEPA_TAKEOVER_PIPELINE_ARTEFACT_TD34_GENEALOGY_CHECKPOINT_20261006.md`

Related Macha audit:

- commit `785a45972fed3ea896d2209058e2860ef115fc2d`
- `docs/agent/V74_MACHA_FULL_AUDIT_FINAL_20261003.md`

Historical conclusion at that checkpoint:

- G2 successor contract remained `FROZEN__NOT_IN_FORCE__DECIDING_MARGIN_UNSET`
- `PIPELINE_ARTEFACT_m` CONTROL_A-vs-CONTROL_B positive-control discrimination experiment had been specified but no qualifying execution was recovered
- synthetic worlds did not plant A-vs-B asymmetry, so they tested false-alarm behavior but not detector sensitivity
- decision: `S102_G2_NOT_CLOSED__PIPELINE_ARTEFACT_M_DETECTION_HALF_UNQUALIFIED`
- Stage 4 not authorized
- real NIH-CARD correspondence unopened

Historical successor starting point:

`claude/v74-g2-continuous-successor-20261002@03c0c486...`

Do not treat the Oct. 6 RED state as permanent. Search all later G2 / Macha / `PIPELINE_ARTEFACT_m` / CONTROL_A / CONTROL_B / sensitivity / injected-asymmetry receipts and verify whether:

1. a deciding margin was frozen prospectively,
2. positive-control asymmetry was actually injected,
3. the experiment was executed,
4. receipts were hashed and preserved,
5. a later document explicitly superseded S102.

Current status at this handoff:

`NOT YET PROVEN CLOSED`

not “permanently failed.”

---

# 19. Nott / liftover / V64

Concrete historical starting points:

- successor branch: `chatgpt/v64-e2-single-source-successor-20260929`
- later head recorded: `23255baaf81381d5c22c655a605642db27f2a173`
- substrate-fit contract branch: `chatgpt/v64-nott-substrate-fit-contract-20260929@a6ecae6c31ba2083de72566fd336b187f7d59bfc`

The next agent should reconstruct an exact chain for:

- source dataset identity
- original genome build
- liftover tool/version/reference chain
- pre/post-liftover feature counts
- rejected/ambiguous coordinates
- promoter/gene mapping rules
- any deduplication/collision policy
- exact external evidence exposed before decisions
- output hashes
- whether later V64/V65 receipts supersede early substrate concerns

Do not summarize this lane as merely “Nott recovered.” Determine whether the **decision-bearing transformed substrate** is physically reproducible and whether it was exposed before freeze.

---

# 20. SCENIC+ / cisTarget external-network lane

Historical recovery / infrastructure branches:

- `agent-4/scenicplus-recovery-expansion-20260926@5e3d1197...`
- `claude/v69-scenicplus-external-network-20261001@d5b76230...`

Known infrastructure chronology includes:

- `7e72f7a652fe262d6df1ff0fbf3290920c0aa395` — Stage75A readiness
- `b4b21ae7a9d60c3a68b651def2738847e17b6c6d` — Stage75B acquisition scaffold
- `413c186d80dbed5ff906044d64e59d48fcf31110` — Stage75D WSL handoff
- `d26bea69c501f55717790f465472780e52f8db3e` — Stage75E SCENIC+ container scaffold
- additional infrastructure successors: `8265326d...`, `80597349...`, `e3b4c6e7...`, `c3d8c2d7...`, `64f634b6...`, `b46d1f2c...`, `4a3c44f7...`, `1981bb6c...`, `1d4f35cf...`, `59bc7372...`, `6395046e...`, `5d51e5ea...`, `cc580c7c...`, `15ab3ffe...`, `8196396a...`, `a30a4ce5...`, `d3447769...`

Important workflow names preserved in later takeover snapshot:

- `.github/workflows/v64-export-claude-nihcard-subset.yml`
- `.github/workflows/v64-fetch-fantom-hg38-cage-bed.yml`
- `.github/workflows/v64-import-claude-exact-supplement.yml`
- `.github/workflows/v64-import-claude-paired-subset.yml`
- `.github/workflows/v64-open-resource-fetch.yml`
- `.github/workflows/v65-build-promoter-dual-ledger.yml`
- `.github/workflows/v69-gse214979-scenicplus-acquisition.yml`

Example known receipt:

`results/v64/V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json`

Required reconstruction is not “does SCENIC+ infrastructure exist?” It does. The target question is:

**Which exact external network / cisTarget / SCENIC+ outputs became decision-bearing, with what source version, genome build, ranking database, motif annotations, feature universe, hashes, and exposure boundary?**

Also recover whether Nott, FANTOM, Morabito, NIH-CARD, or GSE214979 evidence was used only as substrate realism / falsification or ever entered a deciding target/objective gate.

---

# 21. NIH-CARD lane

Historical starting points:

- design branch: `claude/v64-nihcard-e2-design-20260929@6d08386f...`
- realism branch: `claude/v64-nihcard-realism-design-20260929`
- exact-control audit artifact: `results/v64/V64_NIH_CARD_EXACT_CONTROL_SAMPLER_INDEPENDENT_AUDIT_V1.json`

The takeover audit located design/control work but **did not yet independently locate the original later NIH-CARD Stage 3/4 execution package**.

Do not conflate:

- design
- control-sampler audit
- export/import scaffolding
- realism tests
- actual Stage 3/4 execution

The next agent must locate the deciding execution package if it exists, and bind:

- commit
- workflow/run/job
- input subset hashes
- sampler contract
- exact control construction
- output receipt(s)
- exposure state
- whether Stage 3/4 authority was ever actually granted or remained blocked

Current status:

`DESIGN_AND_CONTROL_AUDIT_FOUND__LATER_DECIDING_EXECUTION_NOT_YET_INDEPENDENTLY_LOCATED`

---

# 22. Historical terminal-target audit: use as history, not current authority

Historical branch:

`audit/terminal-target-lineage-20261005@0be861461f0c5b3f5e527d4fbb1e124032c801e8`

Document:

`docs/agent/JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V3_FINAL.md`

Important historical conclusions:

- no qualified production target at that time
- target discrimination precedes encoder training
- qualification gate must use zero encoder optimizer + zero EMA updates
- TD41–43 measurement reliability did not itself grant target authority
- PROD41K/T1 u205 mechanically defective
- F1-B synthetic bridge restored gradients but was not target authority
- FOUNDATION/FULL104 had source/measurement issues
- PR163 TA/TB1/TB2/TC selected nothing
- PR178 corrected synthetic TA/TB was NOT_INFORMATIVE
- V75 was architecture only
- V77 synthetic recovered-data work did not grant target-state authority

This branch is an ancestor of much later work. Use it to identify defects and candidate gates, then search successors. Do **not** simply restate its conclusion as if no later repairs occurred.

---

# 23. Historical contamination-boundary audit: key defect scope

Historical branch:

`audit/target-discovery-contamination-boundary-20261007@4b9834e3db14f43dc8ec663bbb437233757360d7`

Document:

`docs/agent/JEPA_TARGET_DISCOVERY_SUCCESSOR_OPERATING_CONTRACT_20261007.md`

Important decoder/feature-axis lineage cited there:

- `b2231e9e` — retract affected gene-level results
- `5a217f92` — counts intact, gene axis wrong
- `b642dce6` — root cause + verified closed-form FULL104 Level-4 decoder
- `9d30ef62` — NPH52 not affected
- `490d0ffd` — historical 50K HVS/SEA materializer shares defect
- `778706f1` — all six count-producing paths audited
- `91b9725e` — corrected myeloid panels in narrow scope

Historical warning:

HVS/SEA or mixed-source decision-bearing results tracing to defective 50K materialization required corrected interpretation/replay.

This warning was valid when written but is **partly superseded** by the S174 physical gene-ID rebuild. What remains unresolved is the exact stage-by-stage replay map for historical TD56/57B/59 and related target-discovery outputs.

---

# 24. Current defect → repair → verification → supersession table

| Item | Historical defect/finding | Repair/recovery | Verification | Current classification |
|---|---|---|---|---|
| Runtime bounded update | restore/failure/run-ID gaps | `6f9f517...` + `8dabe9e...` | 50 then 51 tests, successful workflows | `FIXED__VERIFIED` |
| Physical row binding | supplied proof could lack sufficient physical binding | PR232 `d3430ce...` | 29 pass | `FIXED__VERIFIED` for supplied proof enforcement |
| 2K operator smoke | 6 operators could disappear | PR233 `c919d95...` | 128 pass, 42/42 min>=1 | `FIXED__VERIFIED` |
| HVS/SEA feature axis | positional mapping wrong | S174 freeze `cf4d470...`, physical gene-ID rebuild | corrected replay `46d8eaa...`, 146 pass | `FIXED__REPLAYED` |
| TD34 producer missing | only hash known in Oct. 6 audit | Sept. 7 ZIP recovered; exact producer bytes recovered | SHA exact match `1e26f37...` | `FIXED__VERIFIED` for producer custody |
| TD34 exact panels | standalone manifests/support NPZ unavailable | candidate reconstruction from TD21B 17,186 universe | candidate hashes derived; downstream cross-check pending | `PARTIALLY_FIXED` |
| TD41/43 script custody | deciding script hashes known, bytes not recovered at checkpoint | successor/archive search required | not yet closed | `NOT_DISCOVERABLE_YET` |
| TD56 corrected substrate | historical result survives on old record | need explicit corrected replay mapping | pending | `NOT_DISCOVERABLE_YET` |
| TD57A authority | exploratory exposure before freeze | quarantined | explicit quarantine | `SUPERSEDED_BY_NEW_DESIGN` / never authority |
| TD57B corrected substrate | historical prospective success | need explicit corrected replay mapping | pending | `NOT_DISCOVERABLE_YET` |
| TD57C nearest-third | prospective 2/4 failure | none needed unless distinct later experiment | byte-identical replay | `STILL_FAILING_AS_FROZEN` |
| TD58 | prospective partial-evidence success but reuses TD57A object lineage | no clean authority repair known | 24/24 historical | `FALSIFICATION_ONLY` |
| TD59 statistic | original executor bytes absent | independent reconstruction | 24/24 rows + values + pair hashes reproduced | `REPRODUCED` scientifically; substrate correction still pending |
| TD60 | frozen design blocked by validator mismatch | search later successor | no qualifying recovered result yet | `NOT_DISCOVERABLE_YET` |
| G2 / PIPELINE_ARTEFACT_m | positive-control sensitivity half not qualified | search later G2 successor | pending | `NOT YET PROVEN CLOSED` |
| Nott/liftover | substrate/provenance chain requires exact reconstruction | historical successor branches found | pending complete bind | `PARTIALLY_RECOVERED` |
| SCENIC+/cisTarget | infrastructure present; deciding external-evidence chain unclear | recovery/external-network branches found | pending exact producer/input/output bind | `PARTIALLY_RECOVERED` |
| NIH-CARD Stage3/4 | design/control found; deciding execution not independently located | search historical execution package | pending | `NOT_DISCOVERABLE_YET` |

---

# 25. Exact next-agent work order

Do these in order. Do not jump directly to model training or new target design.

## A. Close TD34/S149 exact panel genealogy

Search for:

- `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`
- exact producer SHA `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`
- TD41/TD43 panel manifests
- TD41 pair manifests
- any `panel0`, `panel1`, `panel2`, `panel3` address lists tied to TD34/TD25
- any exact 17,186-address common-support ledger

Compare recovered/historical membership against candidate hashes:

- P0 `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976`
- P1 `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44`
- P2 `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56`
- P3 `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5`

If exact match is independently verified, record a closure receipt and supersede the Oct. 6 `INDETERMINATE__PRIMARY_PROVENANCE_MISSING` panel finding.

## B. Resolve G2 / PIPELINE_ARTEFACT_m successor state

Search:

- `PIPELINE_ARTEFACT_m`
- `CONTROL_A`
- `CONTROL_B`
- `G2`
- `S102`
- `detection sensitivity`
- `positive control`
- `injected asymmetry`
- `deciding margin`
- `continuous successor`

Start from:

`claude/v74-g2-continuous-successor-20261002@03c0c486...`

Goal: determine whether the RED Oct. 6 audit was later closed with a prospectively fixed margin and executed positive-control discrimination experiment.

## C. Build exact corrected-substrate replay map for TD56 / TD57B / TD59

Search later S174/decoder/replay branches for:

- `TD56 replay`
- `TD57B replay`
- `TD59 corrected`
- `target discovery replay`
- `HVS_SEAAD_REPLAY`
- `50K corrected`
- `old vs corrected`
- exact historical output hashes

For each stage classify separately:

- historical statistical reproduction
- physical-substrate correction
- scientific terminal changed or unchanged

Do not assume the S174 V77 cache rebuild automatically repaired historical 50K target-discovery outputs.

## D. Reconstruct Nott/liftover V64

Start:

- `chatgpt/v64-e2-single-source-successor-20260929@23255baaf81381d5c22c655a605642db27f2a173`
- `chatgpt/v64-nott-substrate-fit-contract-20260929@a6ecae6c31ba2083de72566fd336b187f7d59bfc`

Bind raw source → liftover → mapping → collision/rejection policy → output → downstream decision use.

## E. Reconstruct SCENIC+/cisTarget external provenance

Start:

- `agent-4/scenicplus-recovery-expansion-20260926@5e3d1197...`
- `claude/v69-scenicplus-external-network-20261001@d5b76230...`
- `.github/workflows/v69-gse214979-scenicplus-acquisition.yml`
- `results/v64/V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json`

Recover exact database versions, motif/ranking resources, gene universe, genome build, hashes and exposure boundary.

## F. Recover NIH-CARD Stage 3/4 deciding execution

Start:

- `claude/v64-nihcard-e2-design-20260929@6d08386f...`
- `claude/v64-nihcard-realism-design-20260929`
- `results/v64/V64_NIH_CARD_EXACT_CONTROL_SAMPLER_INDEPENDENT_AUDIT_V1.json`
- relevant V64 export/import workflows

Goal: find actual execution receipts or prove they are not discoverable from Git/history available.

## G. Re-adjudicate TD41→TD60 only after A–F

Produce one final authority table with columns:

`stage | original conclusion | provenance status | substrate validity | later repair/replay | superseding conclusion | current decision authority`

Do not compress failures into successes. Specifically preserve TD57C nearest-third failure unless a later prospectively distinct test supersedes it.

---

# 26. Data and local assets the next agent may need

The takeover environment had:

`/mnt/data/JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`

Authenticated identity:

- bytes `1664383`
- SHA-256 `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`

If that file is not physically available in the next runtime, use the durable extracted custody under:

`custody/target_discovery_20260907_recovered/`

and search older external custody for an exact ZIP matching the hash above.

Preserved reconstructed expression archive identity from prior custody:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Do not substitute an unverified similarly named archive.

TD34 producer expected support path in its original runtime:

`/mnt/data/td_support_extract/FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`

Expression sparse arrays used by TD34 producer:

`/mnt/data/td_matrix_npz/arrays/data.npy`

`/mnt/data/td_matrix_npz/arrays/indices.npy`

`/mnt/data/td_matrix_npz/arrays/indptr.npy`

`/mnt/data/td_matrix_npz/arrays/shape.npy`

Metadata:

`/mnt/data/td_expr_meta/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`

Operator metadata pattern:

`/mnt/data/td_expr_meta/operator/**/op*.meta.csv`

These paths document historical producer dependencies; they are not evidence those files exist in a future runtime.

---

# 27. Hard authorization boundaries

Remain in force unless a later explicit authority document with primary evidence says otherwise:

- no real-data training
- no target freeze
- no representation freeze
- no Stage 4 advancement
- no production EMA selection
- no TEST/protected data exposure
- no reader_validation / reader_oracle / DEV / SEALED opening for target qualification
- no 500K protected expansion
- no threshold selection from corrected S174 outcome envelopes
- no promotion of TD34 validation geometry into target authority
- no promotion of quarantined TD57A
- no post-hoc rescue of TD57C nearest-third failure
- no assumption that engineering GREEN means biological GREEN

---

# 28. Final current posture

The project is no longer in the state described by the earliest October RED audits.

Several major defects were genuinely repaired:

- runtime guarded update custody
- physical row binding enforcement
- 2K operator coverage regression
- HVS/SEA-AD physical feature-axis reconstruction
- TD34 original producer custody

Several scientific results remain historically strong:

- TD41/43 measurement reconstruction
- TD56 global disjoint-view relational geometry
- TD57B independent donor-recurrent scale-free relation
- TD59 nearest-half mesoscale survival and independent numerical reconstruction

But the **current authority question remains unresolved** until historical target-discovery results are explicitly mapped onto corrected physical substrate and external-evidence provenance is fully bound.

The correct next move is not more exploratory target search and not training. It is to finish the authority graph.

Target completion criterion for the next audit agent:

1. TD34 exact panel genealogy closed or clearly bounded as irrecoverable with all available custody exhausted.
2. G2 successor state resolved.
3. TD56/57B/59 corrected-substrate replay status resolved independently for each stage.
4. Nott/liftover provenance chain closed.
5. SCENIC+/cisTarget decision-bearing provenance and exposure boundary closed.
6. NIH-CARD deciding Stage 3/4 execution package either recovered or explicitly classified not discoverable after exhaustive historical search.
7. TD41→TD60 final authority table written and committed.
8. Main handoff and PR #237 description updated to point to the final table.

Until those are complete, scientific authority remains fail-closed while runtime engineering may remain GREEN.
