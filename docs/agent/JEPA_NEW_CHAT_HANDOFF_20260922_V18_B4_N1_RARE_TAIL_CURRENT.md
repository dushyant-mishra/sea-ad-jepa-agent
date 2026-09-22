# JEPA V5/FULL104 — September 22, 2026 new-chat handoff V18

**LATEST SUCCESSOR UPDATE:** PR #52 at `213552a46903cd92b8a0338df185f0fce9655832` is a three-test-only successor of original red PR #51; target-semantics Actions `35739933731` and explicit no-skip gate are **GREEN**. The original PR #51 remains historically RED; its failures below are an audit record, not the latest execution-readiness state. **Read `docs/agent/JEPA_V18_PR52_GREEN_SUCCESSOR_ADDENDUM_20260922.md` before using any target-lane status or commands below.** Molecular outcomes remain UNOPENED; next action is independent review then read-only runtime preflight.


Status: `B4_RUNTIME_PREFLIGHT_PASS__N1_AUTHORITY_CODE_GREEN_NOT_RUN__RARE_TAIL_STRUCTURAL_POSSIBLE__MOLECULAR_PR51_CI_FAILED__TRAINING_OFF`

**This is a docs-only cross-lane handoff.** It is based on the exact green Audit-B PR #50 head `e4b7e9f46842d66cd7db71b1df9de60fc037f971`. The target molecular work exists on **parallel** PR #51 `f8718b66f1c8bf39787408582fbbc85d5ada97d5` and **is not in the Audit-B branch**. Do not treat this handoff's Git ancestry as containing both lanes. Re-fetch all live heads and Actions status before acting.

Read: `START_HERE.md` -> `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json` -> this handoff -> V18 state -> V18 manifest -> V18 commands -> `docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md` -> September-21 ETL/target-history handoff.

## 1. Scientific purpose and hard rules

The aim is donor-generalizable **biological/cellular latent-state inference from partial RNA**, not reconstruction of an individual hidden gene. Current molecular representation is `VALUE_ONLY_256`; QC and visibility are observational, not target channels. The immutable full-data reader-fit substrate has **4,553,407 cells, 104 donors, 42 operators, 41,238 addresses, 17,186 all-operator common-core addresses, and 8,915 Level-4 blocks**. HVS/NPH52/SEA_AD have **41/17/46 donors**. Four source-stratified outer folds contain **28/26/25/25 donors**. Operator semantics are source-specific, not a universal nuisance axis.

Never silently promote Stage81A3 TRAIN, old 50K TD59, placeholder matrices, cached partial data, synthetic fixtures, exploratory RIDGE8, withdrawn Phase-IV results, or an old handoff to current FULL104 authority. Historical findings stay in perspective; do not rerun already-closed FULL104 lineage, ETL atlas, T0/T1/C2, QID/F1, Stage81, TD13–TD55 gene/module searches, TD56/57B/58/59 historical discovery, Stage-A structural qualification or streaming parity absent a changed input. All current scientific conclusions must bind exact receipt/manifest/source SHA and scope.

Never inspect or execute protected terminal P1–P4 masking outcomes, pathology, DEV/SEALED, D_shared/G5 or TD60 to tune unfinished work. **Training remains OFF.**

## 2. GitHub branch topology at this handoff

All listed PRs were still **open** and mergeable when checked on 2026-09-22; mergeability does NOT mean scientific authority or CI PASS.

| PR | Exact head | Role / CI |
|---|---|---|
| #38 | `3bf6b659de9bdd2711face82b50b47ec567ea449` | scientific integration / original FULL104 safe lane |
| #40 | `034be1949c389c93a26d8476ceedbcd402c55505` | previous docs-only ETL/target handoff (parallel) |
| #41 | `ebae1f9667a6e483ec35a6918234c40b99ae9ea2` | structural/preexecution hardening |
| #42 | `87de6cfd91e4a1f23e02467ca24e9cacf8a32582` | authenticated 105,553-cell sample + V3/V2 producer authorities |
| #43 | `18b9476625d14ecf90b0b6b1efd12d5a7495b548` | repaired RNG V3 `parameter_authority_sha256` consumer; green |
| #44 | `e48c15975b440160e48e29ace74196314d5fa9a6` | metadata-only rare-tail structural runner + validator; green |
| #45 | `5e7612c909c3ed677a91c6dec42e298dc02a6f24` | prospective B2 options memo (supporting docs, not executor) |
| #46 | `ed65f1ba97b95bf135aaa15209bc8cc6ca5c670b` | real B3 RNG receipt + permanently nonexecuting Audit-B V1 |
| #47 | `0180158f61f50ea4e5ad403fb11eb9d525b004c6` | signed B2 decision + hybrid precision + N1-only B4 V2; four green |
| #48 | `979cacbc924c45e55ad57e239a2ed4b0429e88ef` | read-only GPU B4 runtime preflight PASS, masking CI green |
| #49 | `5503cd8c99506d172616b1e2edd8090eeaa41a05` | GPU metadata-only rare-tail structural result; no Actions triggered (evidence paths only); local validator PASS |
| #50 | `e4b7e9f46842d66cd7db71b1df9de60fc037f971` | **current green Audit-B implementation head:** prospective N1 execution authority, crossfold/cached planner, result/precision/N2 receipt contracts; **all four hosted workflows green, masking no-skip PASS**. No N1 outcome. |
| #51 | `f8718b66f1c8bf39787408582fbbc85d5ada97d5` | **parallel rare-tail molecular proposal, NOT GREEN:** target-semantics Actions `35690220963` = 420 passed/3 failed; other two workflows green; fail-on-skip step skipped after failure. No molecular run. |

Masking ancestry: #38 -> #41 -> #42 -> #43 -> #46 -> #47 -> #48 -> #50. Target branch: #43 -> #44 -> #49 -> #51. PR #40/#45 are parallel documentation branches, not automatically merged. An earlier Phase-IV stop branch #39 remains historical/withdrawn; do not execute it.

## 3. Data, exact roots and materialization

Immutable data/provenance roots:
- FULL104 Level-4 manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`, 2,372,002 bytes; **8,915** metadata/count blocks under GPU machine's authenticated Level-4 root (`C:/jepa_full104_ssd/expression_level4` in prior provenance; resolve and hash rather than assuming path).
- Canonical 41,238-address registry SHA `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`, 24,946,770 bytes.
- FULL104 4-fold split **canonical** digest `5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4` (receipt file SHA `56f045d7dc80fde7e30c97632c1d109286e4b8f9f033b77476521c2822980585`).
- Phase-I V2 qualified `CORE_SUFFICIENT_STATISTICS_V1` NPZ SHA `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae`, **242,087,519 bytes**. Qualification receipt file SHA `21fd10f07187c8e59457cf8860a67359ab179878c194833ee119e0323a7c8d53`: all **4,553,407 rows**, all **104** donor library totals and entire per-cell source vector agree by the frozen three routes. **Do not rebuild** from small data.
- Authenticated population metadata SQLite SHA `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913` in external calibration bundle SHA `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- Phase-IV sample freeze **canonical** digest `c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac`, frozen artifact file SHA `d0ce8abbff0076071009997113f1b73ebb8bab9b0ada5d6ce9367eb786733c06`.
- Real target-qualification sample **105,553** cells, **103 donors x 1,024 plus one donor x 81**, 104 donors and all 42 operators; canonical sample receipt SHA `7220654284fe07c1abcf97a77d818700b46e3fe577fca4fd5bc4b99df6a4d6f6`. All **seven** selection/donor/rank/source/fold vectors independently replay-validated against the full source; disposable adversarial tamper tests failed closed. Sample is `FULL104_TARGET_QUALIFICATION_ONLY__NOT_MASKING__NOT_TRAINING_V1` and is NOT interchangeable with Audit-B N1 targets.
- Real sample files, receipts and hashes live under `analysis/v5_full104_target_qualification_20260921/evidence/real_sample/`, introduced on #42. NPY files: `selection_rows_i64.npy`, `donor_code_i64.npy`, `row_rank_i64.npy` (844,552 bytes each); `retained_count_by_donor_i64.npy`, `full_donor_n_i64.npy`, `fold_by_donor_i64.npy`, `donor_source_code_i64.npy` (960 bytes each). Exact file SHAs reside in `EXECUTION_PROVENANCE.json` and `SHA256SUMS.txt`. Operator aggregate `OPERATOR_SUPPORT_CANDIDATE_V1.json` is **supporting-only metadata**, not scientific target qualification.
- Level-4 counts/expression and full GPU artifacts are not part of the small Git handoff and must never be substituted with discovery ZIP, Stage81A3, or historical 50K.

## 4. Audit-B: closed preexecution decisions, results and formulas

B3 RNG-V3 authority source #46:
- canonical RNG digest `775aba506982a9a8dbecccb454d8d3d68709e524bb7f67e9397bbf819b72c2fb`;
- RNG JSON **file SHA** `ee95306997c33d76066579e77db88c53ff0bc6c0fcb964003b75da5717e3d396` (1,163 bytes);
- **global_seed = 1267387626254385975**. Treat as integer from JSON/Python, NEVER round through JavaScript floating point.
- parameter V3 canonical `e942c1253ea71e08f50196fbfe28b7eadc1c5757971094673bce75fe6b1436c1`; ladder V2 canonical `85148fdf9be2bdd655ec601c4d26870f47f6885ce83d93b6e5c7ff8046d32685`.
- target-panel dependency `NONE`; terminal outcome not inspected, seed **frozen, not spent**.

Audit-B V1 **permanently nonexecutable** contract canonical `95db537de2df04e83c72d17ab788f985901ee4b644769d598243a9eed5eef398`, file SHA `b00926494025b54480f3fb1ecd837a672c6498b87e3f2e633a7b62ade0d89040` (3,559 bytes). `precision_scope_id=UNRESOLVED__EXECUTION_FORBIDDEN`, `execution_authorized=false`. Any historical source-balanced fields inside V1 are **NOT** by themselves the B2 scientific decision.

Prospective B2 resolution V3 canonical `766f467f4566cf0087ca4bc22f5263575a8ae50d7e5905666886190c3ad95889`:
- primary target aggregation = **SOURCE_BALANCED__DONOR_UNIFORM_WITHIN_SOURCE__TARGET_UNIFORM_V1**;
- mandatory **non-gating** robustness aggregation = **DONOR_UNIFORM_ACROSS_ALL_DONORS__TARGET_UNIFORM_V1**;
- all 18 nonuniform policy x 6 rung cells reported by source; only **RIDGE8_CONDITIONAL at 5%** controls precision escalation;
- primary metric B2 = held-out detected-token burden; raw-UMI B3 descriptive only.
- frozen hybrid precision: `SE <= max(1/860, 0.05 * abs(mean_normalized_delta_B2))`; `860 = 1 + floor((17186-1)*0.05)` including target. A zero mean uses the absolute branch. No adaptive weighting/threshold/rung choice after N1.
- precision-rule authority V2 canonical `0a712b3aeebc42732726667722c90b2b9d97a6110cba157c2d99aa642c0c97b4`.
- original conceptual normalized burden: `(B2(policy-added addresses) - B2(uniform-dropped addresses)) / B2(uniform full mask with target)`; actual frozen source is `src/sea_ad_jepa/v5/audit_b_production_burden_v1.py`, file SHA `7f589f548bf94fd0bd207717f1b0289e2718958915e08d3a6d716b22164d441a`.

**Final** B4 executable successor V2 canonical `c68231e53ee08990949688013261c957fc205f9599bbc446780a12ba4d276927`. Earlier generic-execution draft digest `2c91e661...` was **withdrawn/superseded** before outcomes. B4 directly authorizes **N1=256 only**; `direct_n2_n3_execution_authorized=false`. N2=1,024 and N3=4,096 require separate precision-derived receipts. Never infer broader authority from generic `execution_authorized=true`.

GPU **read-only** B4 runtime preflight #48 receipt: `analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/B4_FULL_RUNTIME_PREFLIGHT_RECEIPT.json`. Terminal `READY_FOR_AUDIT_B_N1_EXECUTION`, all seven frozen Phase-IV physical inputs SHA-verified, full heavy geometry checked. B4 contract, B2 resolution, precision, RNG revalidated and direct N2/N3 guard exercised: both rejected `STOP_AUDIT_B_ESCALATION_RECEIPT_REQUIRED`. No mask drawn or burden computed. Physical mask-plan generator SHA `fdc0cec140132b71fd0c01af5ec97c323bac091055191754dfcf81111ee6441e`, **6,437 bytes**.

**Newest #50 code, GREEN but unexecuted:** `analysis/.../phase_iv/AUDIT_B_N1_EXECUTION_AUTHORITY_V1.json`, canonical authority SHA `eb3293720c54ae10023a90b73c1bf35b46b6cacfda70632522014d988ebb0096`. Exact 256-target authority from #48 read-only receipt, integer molecular-address target RNG identity, only RIDGE8@5% decision-driving; precision PASS forbids N2, precision FAIL may create **only** N1->N2 escalation receipt. Source files:
`src/sea_ad_jepa/v5/audit_b_n1_execution_authority_v1.py`,
`audit_b_n1_result_contract_v1.py`,
`audit_b_n1_crossfold_planner_v1.py`,
`audit_b_n1_cached_planner_v1.py`,
`audit_b_n1_runtime_rng_bridge_v1.py`;
builder `scripts/agent/build_full104_audit_b_n1_execution_authority_v1_20260922.py`.
All four CI workflows green at #50 exact head, masking workflow `35690520168` succeeded including fail-on-skips. **This is a qualification of code/receipt contracts, not evidence that N1 has run or that end-to-end heavy GPU production is already closed.**

## 5. Rare-tail target lane: structural PASS only; molecular code NOT GREEN

Historical target search synthesis: surviving TD56/TD57B/TD58/TD59 relational evidence; no historical gene/module coordinate promotion. Future TD60 = learned-teacher relational continuity, **not executed**. Historical TD59 numerical outcomes remain historical and must not be treated as current FULL104 molecular evidence.

Real metadata-only #49 structural preflight receipt `analysis/v5_full104_target_qualification_20260921/evidence/real_sample/RARE_TAIL_STRUCTURAL_PREFLIGHT_V1.json`: canonical SHA `f0d71c9b2f25d31a0b277b9a55f2a31f44d9084b924c3c14c67ef0c4c4a4bc89`, file SHA `7b9ff5938e3940fca8640e98217b1c9cf075597305d80bbc04c6df15d1eae801`, **498,827 bytes**. Validated 105,553 cells, 104 donors, all 42 operators and 1,347 donor×operator strata. All 12 source×fold cases structurally possible:
- HVS 11/10/10/10;
- NPH52 5/4/4/4;
- SEA_AD 12/12/11/11.
Minimum four eligible donors/case. **NPH52 folds 1–3 have zero slack: exactly 4/4; loss of a single donor fails its case.** This is a prospective fragility; do not rescue it by relaxing thresholds or changing sample/panels after seeing the result. 64 sampled-triplet cap; 881 strata exactly at cap; no RNA/count matrix or molecular distance opened. Terminal **`STRUCTURALLY_POSSIBLE__MOLECULAR_ESTIMABILITY_UNPROVEN`** is NOT a molecular PASS.

#51 parallel proposal freezes rare-tail molecular authority canonical `0b5629ca5e7087b1535e006021ec35d24a981986d5096eb4c99f001294c4c000` and execution contract canonical `e834285f652d35fe335d16c0e58eadf7ee2b0ffc11fb11035c4ba17a94b80c02`. Intended current FULL104 methods: exactly **two** fresh 512-gene Z/X/Y panels and frozen gene/pair hashes; 2,048 hashed pair coordinates/view, >=256 informative; q95 finite Z nearest-half isolation; >=5 tail anchors/donor; <=64 sampled triplets/donor×operator; >=20 resolved X/Y triplets/donor; 64 matched wrong-cell **Y-only** nulls with frozen donor/operator/depth/detection matching; null p95 sorted index 60; >=4 measurable donors/case; exactly 2 panels x 3 sources x 4 folds = **24 cases**, strict **24/24** pass requiring observed median donor agreement >0.5 and >null p95. The authority says teacher-tail evaluation=false, TD60=false, training=false.

**PR #51 is BLOCKED by hosted CI** at head `f8718b66f1c8bf39787408582fbbc85d5ada97d5`, target workflow run `35690220963`: **420 passed, 3 failed**:
1. `tests/test_v5_full104_rare_tail_molecular_primitives_v1.py::test_real_current_strict_core_reproduces_all_frozen_td59_view_hashes` raises `NameError: ROOT is not defined`.
2. `tests/test_v5_full104_rare_tail_molecular_runner_v1.py::test_materialize_panel_binds_selection_donor_source_operator_and_log1p10k` synthetic fixture does not represent all 42 operators and reaches correct production `ValueError`; fix fixture coverage, **not** production gate.
3. `tests/test_v5_full104_rare_tail_molecular_execution_contract_v1.py::test_zero_slack_nph52_cases_are_explicitly_bound_not_relaxed`: JSON nested lists compare unequal to tuple-of-tuples; normalize/test consistently without changing the actual frozen three zero-slack cases.
The failing regression prevented the no-skip step from running. Runtime closure and spillover workflows passed. A detailed defect comment was added to PR #51. **Do not run molecular data while CI fails.** After repairs, rerun all normal and fail-on-skip suites on the new exact SHA; independently confirm the authority JSON and contract digests and source hashes are updated if code semantics change.

## 6. What to do next (parallel, with strict stop points)

**Masking / CPU code review:** from #50 exact green head, audit N1 crossfold planner and cached-planner numerical parity against the frozen source; verify fold TRAIN-only statistics, zero held-out leakage, RNG V3 target identity and single-use side effects, receipt coverage (256 targets x 3 nonuniform policies x 6 rungs x 104 donors, fold/source report), exact B4 primary/robustness aggregation, precision decision only RIDGE8@5%, fail-closed malformed inputs, resumability/partial-run prevention. The existence of #50 modules **does not prove a complete heavy N1 CLI or executed outcome**. No N1 GPU computation until end-to-end executor qualification and explicit review of the one-time N1 execution plan. Once authorized and run exactly once, N1 outputs/receipt must freeze before inspecting precision; no adaptive retuning.

**Target / CPU repair:** fix PR #51's three precise regression failures **without changing molecular science**, then independent red-team all 24-case, matched-null, hash/source identity and zero-slack enforcement in production runner. Recompute authority/contract source hashes if source bytes change. Only when full exact-head no-skip CI is green may the next authorized action be a read-only molecular runtime preflight before biological expression access. Do not execute TD60 or any teacher training as a shortcut to this target qualification.

**Git governance:** PRs are a long unmerged chain. Do NOT auto-merge #50 and #51 (parallel descendants) or rebase blindly. First refresh live heads, verify ancestry and path overlaps, and agree a reviewed integration order preserving both SHA-bound receipts. Keep original closed scientific authorities immutable, avoid replacing archived handoff content, and make any future updated handoff point to this V18 package or a newer reviewed successor.

## 7. Required outcome firewall at handoff

`AUDIT_B_N1=UNOPENED; MASKS_EXECUTED=NONE; BURDEN_CALCULATION=NOT_RUN; TERMINAL_MASKING=UNOPENED; P1_P2_P3_P4=UNSELECTED; RARE_TAIL_MOLECULAR=UNOPENED; TD60=UNEXECUTED; PATHOLOGY_DEV_SEALED=UNOPENED; D_SHARED_G5=UNOPENED; TRAINING=OFF`.

Source and branch identity do not supersede validated scientific authority. Never represent green source/mechanics CI as full scientific execution.
