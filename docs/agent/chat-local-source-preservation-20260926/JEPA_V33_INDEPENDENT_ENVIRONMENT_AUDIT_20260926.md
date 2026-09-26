# JEPA V33 independent environment audit — September 26, 2026

**Status:** non-authorizing, read-only repo review plus newly executed local historical-asset audit. **TRAINING OFF**, protected outcomes unopened, 0/33 full closure roots. This document is a *scoped* independent audit, **not** an exhaustive review of every historical commit, all 263 branch tips, absent GPU storage or all >30GB FULL104 expression bytes. The previous 263-tip discovery was performed on PR155; repeat only for changed tips or a changed research question.

## 1. Controlling chronology and immutable scopes

- `main` currently identified as `c49b13bd75c2d23716c777336db8fbfc78c09cd0` (September 24 V25 governance). `START_HERE.md` and `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json` point to V25. New V32 PR159 is **draft/unmerged** and does not supersede governance.
- Draft [PR159](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/159) head `80fa4b90760d07df55adaaa09ce5dc394f204d4f` is **2 ahead, 0 behind main**, exactly three added documents/receipt files, zero code/data changes. No associated pull-request-triggered GitHub Actions run returned for this head. Its V4 15/15 result is reported from a separate local chat, **not reproduced in this mounted environment**.
- Supporting branches are independently stacked. Do not conflate PR146 original physical FULL104 metadata, PR149 independent replay, PR150 V28 documentation, PR151 typed V3/V1 mismatch, PR152 nonauthorizing prospective teacher draft, PR153 mechanical negative controls, PR154-155 branch-tip searches, PR156 issuer red team, PR157 V31 cross-lane audit, PR158 GSE289721 exploratory reconnaissance, and PR159 V32 documentation. No implied merge or approval.
- Historical T1/C2/EMA, Stage81A3 TRAIN-cache, T0, QID matched-null-vs-wrong-query, invalid `x4_within` results, V0/V1, Layer2 and prior LODO were already audited. **Do not rerun historical work merely because a new chat began.** The September 25 S9 claim of defective `sea-ad-jepa` was fully retracted: original environment requires its `Library/bin` on PATH *at interpreter launch*.

## 2. Local physical evidence newly verified here

The following files are physically mounted. The non-authorizing script `jepa_v33_local_audit.py` was **executed** and emitted `jepa_v33_local_result.json`. It streams SHA-256 instead of extracting huge archives or loading legacy pickle-backed artifacts.

| Artifact | Physically verified SHA-256 | Independent observation |
|---|---|---|
| `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` | Matches V32 manifest; 60 ZIP members, ZIP integrity test succeeded |
| Historical expression `part001` | `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e` | Matches uploaded part manifest |
| Historical expression `part002` | `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875` | Matches uploaded part manifest |
| `part001 || part002` concatenated *stream* | `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7` | Matches uploaded combined archive SHA; no extra copy written |
| `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` | `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` | **QUARANTINED** historical provenance mismatch, do not load/promote |
| Historical `checkpoints.zip` | `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c` | Archive integrity passes; **no current-V5 authority** |
| Historical `expression.zip` | `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4` | Archive integrity passes; **not FULL104** |
| `t1_checkpoint_u0200.zip` | `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c` | Archive integrity passes; **not current-V5 checkpoint** |

**NOT PRESENT:** `JEPA_TEACHER_TARGET_V4_NONAUTHORIZING_RESEARCH_PACKAGE_20260926.zip`, `STAGE75_PILOT_COVERAGE_AUDIT_20260926.zip`, final V32 transfer bundle, complete 30GB+ FULL104 source expression and original Morabito H5 files. Do not equate a GitHub SHA manifest with physically possessing the payload. The larger mounted historical files are not a substitute for absent V32 or FULL104 sources.

## 3. Stage75 historical regulatory candidate audit

Fetched actual GitHub `results/tables/stage75_integrated_tf_target_summary_v1.csv` at Git blob `fd0f8e12c1161629f53f568f30cbc0bf8e3ff1a1`. Its 96 candidate rows contain **27 unique target symbols and seven regulator symbols**. The table explicitly marks `validated_regulation=False`, `validated_grn_claim=False`, `causal_validation_pass=False` for all rows, and `edge_atac_peak_support_status=not_gene_mappable_from_processed_peak_matrix`; its `advance_supported` is a *candidate eligibility flag*, **not validated causal regulation**.

Separately read all **41,238 rows** of the physically authenticated **historical** `address_namespace.csv` inside the calibration archive and checked the 27 exact symbol names. Result: **25 unique historical matches, two ambiguous, zero missing**; seven regulator symbols uniquely matched. Two ambiguous cases:

| Symbol | Historical current-exact address | Historical legacy-exact address | Provenance split |
|---|---|---|---|
| HLA-DPA1 | ENSG00000231389 | ENSG00000168384 | HVS/SEA-AD versus NPH52 |
| HLA-DPB1 | ENSG00000223865 | ENSG00000215048 | SEA-AD versus NPH52 |

**Fail closed:** Do not pick the `current_exact` entry automatically for all source datasets or merge the legacy signal by symbol. Resolve with source-native Ensembl, authenticated annotation releases and exact current V5 registry mapping. Historical symbol coverage **does not demonstrate** full Morabito RNA overlap, ATAC mappability, donor/sample pairing, actual eRegulons or FULL104-compatible current gene coverage. RNA and ATAC are not automatically cell-paired.

## 4. Training authority / engineering blockers

**P0 — issuer provenance gap independently source-confirmed.** Exact PR149 `src/sea_ad_jepa/v5/current_training_authority_v1.py` accepts a caller-provided closure mapping, delegates its internal digest check to `preexecution.bind_closure_v2`, validates the receipt's relationship to the same supplied roots and only calls `validate()`/`canonical_digest()` dynamically on caller-supplied `critical_test` and `runtime_source`. It does **not** run `validate_current_v5_authority_closure_v2` against all actual typed parent objects or authenticate actual parent bytes. At PR156 head `a5af773adfd66d0e727113610f5e62d7353b13b8`, hosted CI run [36223680982](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36223680982) confirmed the self-consistent invented-closure positive adversary and two corrupted-digest rejection controls (**3 passed, no skips**). CI success means **the vulnerability was demonstrated**, not repaired. The formal B1 contract is also OFF. Safe repair: require the issuer to consume a validated, authenticated, full typed graph and independently verify provenance of the validator's executed result; re-run three original adversaries plus genuine/altered-parent positive controls. Merely adding another caller-provided hash or string flag does not fix provenance.

**P0 — masking CI failure.** PR144 exact head `21efb1047c73cfe7b88047f0aeee1978b035971f`, [run 36208393701](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/36208393701): **826 passed, 5 failed**, all traced to frozen Phase-IV `planner_source` SHA mismatch, expected `143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d`, observed `de2f019e28675e3258cfeede65f77557210f5fcd083f94ae09f97b1c8629f9f8`. The failure is correct fail-closed behavior, but dependent tests that stop early at preflight have **not** validated their advertised downstream rejection paths. Inspect the changed planner's semantics; if legitimate, issue a **versioned new freeze** and rerun exact-head CI. Never edit old signed digest just to make tests green.

**P0 — V3/V1 class mismatch.** PR151 documents that PR149's syntactically valid RNG and parameter artifacts use V3 classes while the V27 current closure expects exact V1 classes. No class auto-upcast or fake 6/33 closure.

**P1 — real training mechanics vs evidence.** PR147 Phase1A reports 104/104 development preflight and legitimate CPU synthetic mechanics, but no authorized real-data run. PR153 has 17 mechanical failure injections, not physical CUDA/FULL104 proof. The previous 40/40 affirmative count is withdrawn as vacuous; preserve the real negative gradient injection and valid CPU demonstrations. Protect the strict optimizer-unscale→gradient→actual step/Adam→EMA→cursor→atomic checkpoint order.

**P1 — teacher target.** PR152 prospective definition and V32 exploratory V4 raw-count view-isolation have complementary but unmerged roles. Query ID may be lawful; student query *realization*, its normalization and QC descendants may not enter student features. V32 15 local unit tests cannot establish current V5 live end-to-end leakage safety. On independent reavailability of the V4 ZIP, challenge q-scalar edits, opposite-view depth changes, count-dependent mask selection, cache-key leakage and identity-only/global-only shortcuts; record the required comparator as *not run* if global context is disabled. Then run q-aware versus q-agnostic development-only tests on frozen held-out donors; no protected result access.

**P1 — masking and support.** Historical September 16 nine-cell masking grid had no qualified policy. PR144 frozen-source mismatch is independent of whether its scientific attacker will succeed once rerun. Do not treat `UNIFORM` as approved by default.

**P1 — uncompleted full RAW evidence.** PR146/149 physically reproduced FULL104 *metadata*, not the completed original all-8,915-block source raw-count independent reaggregation. The original full read in PR120/124 ended at a session limit with **NO RESULT**. This environment lacks the complete source; specific read must occur on the GPU laptop with exact source hashes and compact signed receipt after prior authorization checks.

## 5. External benchmarking and biological interpretation

PR158 GSE289721 is a source-authenticated *feasible candidate*, **not** qualified benchmark truth. Its two independent differentiations in one genetic background cannot support donor-population generalization. The deposit has 24 unique protospacers (6 targets × 3 plus 6 controls), 72 capture rows due to 3 capture patterns/guide, ~13% published guide-assignment yield, unresolved cell-line identity and no published knockdown efficiency. Its prespecified within-library engagement and control-vs-control gates must pass before any effect comparison. INPP5D overlaps GSE178317's development target and must be excluded from independent pooled concordance unless exposure is explicitly handled. The existing CRISPRbrain GSE178317 pair is **same-experiment** comparison, not independent biological replication. Historical Stage75 and Morabito do not automatically prove external perturbation causality.

## 6. What was and was not exercised; self-audit

**New local execution:** independently hashed the calibration ZIP, both expression parts, combined stream, three historical ZIPs and quarantined NPZ; archive-level CRC test for four complete ZIPs; read full historical address namespace; ran `jepa_v33_local_audit.py --audit` with fail-closed exact census. Six **new** synthetic red-team tests in `jepa_v33_local_audit.py --test` all passed: valid hash, changed-byte hash, part reorder, duplicate-gene ambiguity, missing-symbol treatment and no collision auto-promotion. Unit tests validate **our audit code**, not V4 current teacher or V5 training. **Self-audit correction:** the initial local unittest launcher used `exit=False` and could return status 0 despite failures. Replaced it with a fail-closed test runner and then deliberately injected a failing test; the runner returned `False` as required, without rewriting any scientific result. JSON machine receipt: `jepa_v33_local_result.json`; self-test log: `jepa_v33_selftest.log`.

**Independent self-audit corrections and limits:** (i) Do **not** call 25/27 historical symbol mapping current-V5 coverage; (ii) do **not** re-label all 96 candidate regulatory edges as validated; (iii) do **not** call 15/15 hosted tests or reexecuted here; (iv) a SHA of the concatenated historical archive proves exact byte identity only against the pinned external manifest, not that it is the live FULL104 stream; (v) the known `001375ec...` NPZ is quarantined; (vi) passing diagnostic PR156 CI is evidence of an *open defect*; (vii) other PR branch heads and CI can change after this dated audit; re-fetch before changes.

## 7. Ordered safe execution

1. **Immediate source repair on independent branch:** fix PR156's issuer provenance gap and add fail-closed tests for invented typed roots, forged closure, modified parent bytes and missing B1. Do not change current PR149 historical receipts or enable training.
2. **Unblock frozen masking CI** through exact old/new planner source diff and semantic review, versioned successor freeze if justified, rerun all 831 focused tests and verify complete non-skip census. Preserve old failing run for traceability.
3. **Recover the actual V32 transfer ZIP** (absent here) and rerun the 15 V4 tests with source hashes; independently red-team all view/norm/QC/channel leak paths. Keep PR152 as the separate prospective scientific decision authority.
4. **Current gene identity:** rehash original Morabito assets and authenticate current source-native Ensembl; resolve HLA collisions without guessing; measure entire 41,238-address FULL104 overlap and ATAC genomic-coordinate coverage; no full SCENIC+ expansion until coverage and cost are justified.
5. **Physical-GPU-only work:** authenticate source/ABI invocation and 8,915-block raw-count scope; return exact compact receipts and aggregate counters, no 30GB copy into Git; only later seek independently reviewed B1/B2 authority.

**Forbidden shortcuts:** no experimental training, protected result inspection, therapeutic ranking, D_shared/G5 outcome opening, V3→V1 type coercion, silent previous-run parameter carryover, manual HLA symbol resolution, or treating technical wells as independent biological replicates.
