# JEPA full-lane audited takeover V8 — 2026-10-17

Status: HISTORICAL_AUDIT_AND_SYNTHETIC_LINEAGE_RESTORED__TASK4_INDEPENDENT_RECHECK_PENDING__NO_BIOLOGICAL_OR_TRAINING_AUTHORITY

## Read-first order (mandatory)

1. This V8 handoff (also mirrored on PR #322 and #323).
2. PR #322: `docs/agent/JEPA_LANE_AUDIT_SNAPSHOT_V7_20261017.md` and `results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V7_20261017.json` for latest Task4 state.
3. PR #323: `docs/agent/JEPA_SUCCESSOR_HANDOFF_V7_20261017.md`.
4. Synthetic lane PR #325: `docs/agent/SYNTHETIC_DATASET_LANE_HISTORICAL_AUDIT_COMPENDIUM_20261013.md`, `SYNTHETIC_DATASET_LANE_NO_REPEAT_LEDGER_20261013.md`, `SYNTHETIC_DATASET_LANE_NO_REPEAT_ADDENDUM_V80_20261013.md`, `SYNTHETIC_DATASET_LANE_V80_AUDIT_DELTA_20261013.md`, `SYNTHETIC_DATASET_LANE_AUDIT_STATE_V2_20261013.json`.
5. Synthetic operations PR #324: `SYNTHETIC_DATASET_LANE_SUCCESSOR_HANDOFF_V4_20261013.md`, `SYNTHETIC_DATASET_LANE_SCRIPT_RESULT_INDEX_20261013.csv`, `SYNTHETIC_DATASET_LANE_PROJECT_ARTIFACT_CUSTODY_20261013.csv`.
6. Unified synthetic population PR #328, external audit PR #339, production design PR #344, production implementation plan PR #356.
7. V79/V80 qualification: PR #348 and frozen V79 artifacts; V80 receipt `results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json`.
8. Real population/source audit PR #349; TD repair PRs #351/#358/#360/#362/#364-#369, and Macha real-data audit branch.
9. Task4 design PR #402, initial RED PR #403, implementation PR #404, hostile review history #405-#427.
10. Local binary hashes in PR #322 `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_V4_20261017.json`.

**No-repeat rule:** do not re-audit settled historical material indiscriminately. Only reopen for changed bytes, changed scientific question, new contradiction, known unresolved blocker, changed runtime or changed authority boundary. No green aggregate erases a source-level failure.

## 1. Exact current gates — as of the inspected 2026-10-17 V7 snapshots

Frozen accepted Task0 `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`; Task1 `799d2e235901dfad9ce3b305c767a1c989e362f6`; Task2 `c7dfff1cee608e4a101855d42cf0af08491c2aaf`; Task3 `117dd51dea827e734b299982da93991b934bdc8f`. Task3 acceptance independent Macha head `c33f2bd2`, PR #401. Freeze branch `freeze/unified-task3-accepted-117dd51d-20261016`. Do not alter frozen Task0-3 production code to make downstream tests pass.

**Task4 is NOT independently accepted.** Macha rejected predecessor `36e3b46f1ca44465864a11872b459b5d108d6a67` for T4-B1–B5 at review head `d4d9ef94`. Successor-6 `211375de57cc1f70d46c6eb3a4860d61a1aba0a6` repaired remint/double-spend but did not close inherited B1/B2/B4/B5. Current immutable recheck PR #427 is pinned to `64535753acfab0993165b5666797808f20cd8743`; repair PR #426 is separate. Eight GitHub checks pass at the pinned head, but **real Windows custody recheck and independent Macha A1-A5 acceptance are absent**. A simulated Windows fsync test is not equivalent to a real Windows test. Genuine external trust remains unwired; FINAL and training fail closed.

Global authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## 2. Synthetic dataset lane — essential missing history

This lane is not synonymous with Task4's synthetic *tests*. It comprises historical synthetic biological worlds, realistic observation operators, support/estimability contracts, withheld controller truth, frozen benchmark worlds, and a planned production-scale merged biological dataset.

### 2A. Biological and statistical ancestors (do not repeat)
- **Stage81A3:** earlier mechanistic biological synthetic substrate with latent factors, expected molecular state, paired observations and interventions. Incomplete ancestor, **not** a frozen production simulator; A3R support/address semantics may be reused but the historical global-state pilot was not frozen.
- **Stage70/71, V78:** negative-prior experiments, not authority.
- **V72–V75:** scoped ancestry for population/measurement mechanics.
- **V77:** qualitative broad-class generation lesson, not a calibrated human-rare-phenotype model.
- **V79:** fixed Q00–Q11 statistical/observation benchmark. Frozen `NOT_QUALIFIED`: **291/292 gates passed; Q08 sparse-positive convergence failed with 3 NOT_DIAGNOSED fits**. Do not relabel this PASS, rerun/rescue retrospectively, change thresholds, or hide Q08 inside aggregate performance.
- **V80:** *new prospective* sparse-positive benchmark, not a V79 patch. PR #348 qualified benchmark/custody/adjudication mechanics at executable source `b840067e4c9439e4cb4aa9e8c649ef2f6064a142`, workflow `38504094639`. V80 frozen receipt SHA-256 `346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32`. Eight worlds / 192 per-gene fits. Six estimable worlds; SP05/SP06 deliberately non-estimable by construction. `COMPLETE`, `NOT_ESTIMABLE`, `NUMERICAL_FAILURE` are distinct; numerical failure, false abstention and false certainty remain hard fails. Fit never sees held-out controller outcomes; recovery metrics are controller-computed. **No successor estimator has been qualified.** A future frozen estimator must pass both V80 and immutable V79 291 protected passes; V79 historical failure remains failure.

PR #325 is the durable full historical synthetic audit compendium and error ledger. PR #324 is operational handoff, scripts/results and artifact custody. Use these first, not a blank-slate repository scan.

### 2B. Unified/merged synthetic population actually implemented — PR #328

PR #315 V2 corrected the initial flawed design that omitted Stage81A3 and directly planted candidate-shaped latents. Synthetic biology must be candidate-agnostic; C1/C2/C3/C6/C4/C5 truth must be derived controller-side, not used as model inputs. The synthetic controller oracle is not the teacher. Teacher constructs a target from permitted richer *measured* evidence; student predicts from lawful reduced evidence. PR #311 contributed donor-calibrated rare/multimodal/context/perturbation design, not license to plant human frequencies.

**PR #328** at `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec` implemented and qualified a *single unified candidate-agnostic mechanics/interface fixture*:
- common and rare programs within one donor/cell population, not a separate rare dataset;
- frozen V79 hierarchy/observation primitives and weak/central/strong/extreme synthetic stress presets (not empirical prevalence);
- context-dependent rare activity, CONTROL / ACTIVE_RARE_PROGRAM_PERTURBATION / MATCHED_PERTURB_NULL;
- same-nucleus and separate-nucleus RNA+ATAC;
- true measured zero distinct from structural unmeasurement;
- observation-artifact pseudo-rarity;
- donor-disjoint reader partitions;
- controller-only C1–C6 truth derived after generation, excluded from fit-view serialization;
- interface compatibility with audited post-TD rehearsal.

External audit PR #339 verdict `PASS_WITH_LIMITATIONS` found four scope/provenance/runtime/perturbation issues. All four were repaired: fixture-only claim, transitive executable/blob SHA binding, pinned Python/scientific runtime, explicit perturbation arm semantics. RED `38485411283` at `43ee596e...`; GREEN `38485929906` at `8213bcb...`. Frozen receipt SHA-256 `0cc1bc599dd0e77ec46f603d8a7edbb7da58762020a68d703b403dc7bf0a4dad`. World `dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66`; fit view `fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a`; controller `120c4e47bb7d667360c0786bb6004f02166d0f189c4a2b33b478545c7296c05f`; manifest `9b74681f57601225aa26037fa1eac439be067143bfb900cdcd5f73af0dbc8d3b`; package `9f2f3b7a53d5862a2a08bbd23c1d42f990f0f055616fbce7a1491493cda3fb41`. CI artifact 11859436393, archive digest `825dd42c8467418045b7a3406cff190697a8abc0104c6203c8a425089bb4d1ef`.

**Limitations:** not full Stage81A3 causal network; not complete interactions; not full 41,238-address production realization; not physically separated blinded domains; not calibrated human rarity/effect; not full downstream production rehearsal; not real biological validation; no selection/training authority. STAT1/50K calibration is `QUARANTINED_NOT_HARD_AUTHORITY`.

### 2C. Production lineage-composite simulator (DESIGN/PLAN, NOT IMPLEMENTED)

PR #344 accepted V3.1 design + controlling V3.1.1 E1–E7 erratum. Exact head `847fe734b15e52f204f18903a124e1cfd3bf111d`. Read:
`docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-consolidated-corrective-amendment.md`;
`docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-1-erratum.md`.
V3.1 review at `dcd0754d...`; amended plan later accepted at `2507b967...`.

E1: post-exposure difficulty/regime reduction not a clean qualification; E2: withheld-family spec controller-secret and commit/reveal bound; E3: G7 SAME_CODE_PATH requires real content validator; E4: numeric quantities classified authenticated empirical / pinned math / prospective convention; E5: calibrated NOT_ESTIMABLE distinct from numerical failure; E6: R1 must use exact real executor metric/scaling/aggregation law; E7: docs/agent notes non-controlling until promoted into spec.

**PR #356** plan `2c2723a1a731e7a848196aef3f7c4ab965e9ff6a`: read production V3.1.1 implementation plan, F1/N3–N6 binding notes, post-Macha real-lane dependency delta, and Tasks1–3 execution handoff under `docs/superpowers/plans/`. Tasks1–3 prospectively executable with fresh implementer/reviewer; Task4 of *synthetic production plan* waits for three reviews and checkpoint. STOP_A first production realization, STOP_B sealed qualification, STOP_C finalizer all binding. **This Task4 numbering is different from Unified TD custody Task4**; do not conflate them.

External unresolved production constraints include G6 nondegenerate margin/human decision contract; G8 299 vs 599 decision-law conflict; R1 real executor/source parameterization; TargetPortfolio; G7 real same-code-path content validator; V79/V80 successor-selection conflict; PR #355 repair. Do not start production worlds merely because fixture PR #328 is GREEN.

### 2D. Real support geometry that synthetic must stress

PR #349 at `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7` outcome-blind population registry: 6,351,753 rows; 149 donors; 42 observation operators; 3 sources; 2,028 donor×operator strata; **104 reader-fit / 22 reader-validation / 23 reader-oracle donors**. Population registry SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`. Calibration bundle `07748d5b...`; metadata DB `a771f08b...`; split `efe43e63...`. Support is `SUPPORTED | UNSUPPORTED_STRUCTURAL | BLOCKED_EVIDENCE_CONTRACT`, not a single boolean. C1–C4/C6 unresolved evidence contracts; C5 structurally unsupported in RNA-only population pending regulatory registry. Foundation technology is snRNA-seq only; this population cannot prove technology transfer.

Macha real-data audit, branch `audit/td-real-data-qualification-macha-20261014` @ `ccc3a089...`, reports **289/41,238** addresses scalar measured by zero operators, **17,186/41,238** by all 42, HVS-only 730, NPH52-only 4,894, SEA_AD-only 4,710; NPH52-only 4,894 absent from reader-validation scalar support. These constrain observation/support stress, **not** latent biological prevalence. Balanced worlds are controls, not sufficient qualification substrates. Preserve measured-zero vs missing/not-assayed semantics.

## 3. Real Target Discovery and scientific audit — do not restart

TD implementation/repair lineage: G8 #364; G6 #365; G9/S1/S2 #366; R1 #367; G2 #368; G7 #362; R4/C6/C4 #358; C4→C6 #351; G12 #360; system battery #369. PRs #375–#378 superseded duplicates. Human TD gates are not inferred from qualified fixture mechanics.

Scientific channels must remain explicit:
1. RNA counts/expression/observed programs;
2. ATAC peak accessibility and differential accessibility;
3. chromVAR donor-pseudobulk motif-associated accessibility (motif family, not direct binding);
4. footprinting;
5. SCENIC+ inferred enhancer/regulon links;
6. expression target/query programs;
7. perturbational controls and effects;
8. orthogonal cohorts/external replication;
9. ETL/provenance/technology observation-operator histories.
Shared ATAC source means DA/chromVAR/footprinting/SCENIC+ analyses are correlated evidence, **not four independent replications**. Donor, not cell, is replicate for donor-level claims. Contradictory/missing/unsupported evidence remains explicit; no favorable-zero-fill or source-failure averaging. Prior Morabito viewing is an exposure question determined by exact ETL lineage, not blanket invalidation. Pre-repair NPH/gene-semantic evidence remains non-authorizing.

ChromVAR/limma non-authorizing design: `docs/agent/TD_MOTIF_PROGRAM_EVIDENCE_LAYER_CHROMVAR_LIMMA_V1_20261015.md`. RNA/ATAC/SCENIC+ multimodal integration must preserve these claim boundaries.

Teacher target design error already identified: fitting a rich predictor to one RNA panel to predict a disjoint held-out panel is not a teacher constructing a biologically enriched measured target. Require genuine measured teacher target, protected query identity, donor disjointness, and identity-only/shared/fixed/stop-grad/shuffle plus leakage controls. Historical PR #163/#178, PR #199/#312 and subsequent controls are prior evidence.

Mechanics already audited: optimizer/teacher no-grad/EMA update order, invalid-step blocking, Adam/checkpoint/restart, RNG/packing, FULL104 support, donor-primary target, normalization, visibility and masking, p/q separation, and anti-carryover. Mechanics audit does not prove target biology or grant training authority.

## 4. Unified Task3 → Task4 historical audit lineage

Task3 rejects `851544e8...`, `68df3158...`, `d9e58a18...`; accepted `117dd51d...`. C1–C9 carry-forward includes stable revoked identity, full prerequisite closure, persistent cross-process R4, legacy-import firewall, diagnostic-only readiness, credentialed actors R7, frozen actor policy on revocation, closed requirement classes, construction-time Task1 law, and in-process tampering protection; pooled-donor scope R5 persists.

Task4 PR #402 design; #403 RED (run `38938697657`, 14 intentional failures); #404 core implementation. Rejections: `b31371d...` self-minted trust; `c537db4...` post-seal substitution; `b5ed724...` fabricated campaign state; `d41720b...` reveal-before-terminal-freeze; `06888082...` copied rows falsely proving regeneration. Recheck PRs #417/#419 RED; repair #418/#420. Macha rejected successor5 `36e3b46f...` at `d4d9ef94` for B1-B5; successor6 `211375de...` superseded. Current #427 `64535753...` mechanically CI-green but independently unaccepted. Additional exact-head Windows verification missing. Never equate a passing CI fixture with actor/process external custody or biological authority.

Current next action for Unified Task4: read PR #427 packet, independently run Macha A1–A5 and sibling routes plus genuine Windows local custody and POSIX durability tests; issue explicit exact-SHA ACCEPT/REJECT; if rejected preserve RED first and repair on separate branch. No final real protected challenge material or training.

## 5. Local user-uploaded artifacts and storage truth

Read PR #322 `LOCAL_ARTIFACT_CUSTODY_MANIFEST_V4_20261017.json`; **binary files are not mirrored into Git** and cannot be inferred to exist on a future agent's machine. Verify SHA-256 before use.
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip`: reassemble part001 + part002, 607,959,761 bytes; SHA256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`.
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`: 410,278,055 bytes; `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- `expression.zip`: 3,599,456 bytes; `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`.
- `checkpoints.zip`: 71,356,460 bytes; `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`.
- `t1_checkpoint_u0200.zip`: 233,729,581 bytes; `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`.
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`: 1,531,109 bytes; `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`; semantic provenance remains to be recovered.
- Text imports in Git: `docs/agent/historical_imports/STATUS_AND_REPAIR_PLAN_20260912.txt` and `WSL_EXECUTION_ISSUE_AND_FOUNDATION_DESIGN_NOTES_20260824.txt`.
Artifacts are evidence/custody, not permission to infer truth, reuse secrets or train.

## 6. Working instructions for successor agent

Treat this as **two independent but connected operational lanes**: (A) Unified TD custody Task4 exact-SHA hostile qualification and (B) synthetic biological dataset/production-world implementation per PR #356. Neither may grant the other's authority. Current audit branches #322/#323 are navigation/custody, not merged-code authority; GitHub PR labels such as merged/unified must not substitute for merge status.

For any request, first identify the unit, its exact SHA, assay/cohort, source-dependency family, claim type, prior decision, and gate. Read existing result/receipt before rerunning. Classify as `ALREADY_AUDITED`, `NEGATIVE_PRIOR`, `SUPERSEDED`, `OPEN`, `CHANGED_INPUT_REQUALIFICATION`. Do not re-spend failed V79 worlds; do not reinterpret a fixture as the complete 41,238-address production simulator. Future agent should audit its *new* delta, not restart every historical audit.

On a major milestone update BOTH PR #322 audit snapshot and PR #323 successor pointer, with current exact SHA, independent verdict, CI run IDs, source hashes, unresolved blockers, and whether authority changes. Keep machine-readable state synchronized. Do not overwrite prior RED or historical artifacts. Preserve controller/fit/protected-data separation, external actor attestation, and sealed challenge holdouts. Final status always `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED` until a separately authorized gate changes it.

## Boundary of this handoff

This document is an evidence-based navigation/assimilation index. It **does not assert** that every historic branch's scripts/results are merged into a single default branch or that local binaries are accessible to future chats. Audit/handoff PRs are currently OPEN, not merged. Deep contents remain on their cited branches, and PR #325 / #324 are first-party synthetic-lane custody sources. Directly compare source SHA if encountering contradictory newer work.
