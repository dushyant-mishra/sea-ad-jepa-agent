# JEPA teacher target — V4 source audit, counterfactual red-team, and historical held-out-donor pilot

**Date:** 2026-09-26. **Classification:** NON-AUTHORIZING RESEARCH. **No GitHub files changed.** The 33-root readiness state remains **fully_closed = 0**, **TRAINING = OFF**; protected pathology, sealed masking/confirmation outcomes and real current FULL104 training remain unopened. This report supersedes the V2 **preferred normalization candidate**, not the historical V2 evidence or any current canonical authority.

## 1. Source audit: the live Level-4 path enables a simpler candidate

GitHub source was inspected on `dushyant-mishra/sea-ad-jepa-agent` main `c49b13bd75c2d23716c777336db8fbfc78c09cd0` and PR149 parent `938fe5d3a7288826fef86b2650fb3a9a21fd3794` (verify fresh heads before implementing):

- `scripts/v4/materialize_full104_phase2_expression.py`, lines 178–242: rejects collided/noninjective address mappings, reads **raw integer source counts**, sets `source_library` to the sum of **all raw source feature counts before mapping**, and writes integer CSR plus integer metadata. The originally committed `MATERIALIZATION_CONTRACT.json` states normalization is **deferred**. Its audit names the **8,915 Level-4 blocks**, 4,553,407 cells, 42 operators and original Level-4 manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`.
- `src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py`, lines 343–366 on the audited PR149 parent: current `iter_blocks(columns=...)` selects requested **raw** columns but scales them by the **unmodified full source library** and applies `log1p` before yielding normalized blocks. Merely omitting q from `columns` is not a strict q-blind route.
- The original V2 inverse transformation is appropriate as a research diagnostic where only pre-normalized historical arrays exist. **Do not make this the default FULL104 production change:** authentic current Level-4 blocks are raw, permitting an exact pre-normalization firewall. Do not edit producer bytes, the original block manifest or legacy masking outputs.

Source-code inspection and original audit are *not* a rehash of all local GPU Level-4 block files from this chat. The current GPU laptop must revalidate physical bytes and the exact current production reader source separately.

## 2. Newly discovered leakage: disjoint views can communicate through their shared denominator

For raw source library `L`, queried count `x_q`, student-visible gene set `C`, and teacher-only gene set `T`, prior V3 strict q exclusion used `log1p(10000 * x_C / (L - x_q))`. This is invariant to **q-only** count changes but is **not** invariant to `T`-only changes: `L` contains the teacher-only counts. Similarly, the teacher's ostensibly independent `T` view acquires aggregate `C` counts through `L - x_q`. This is an avoidable compositional channel, not evidence of biological predictive learning.

**V4 proposed first diagnostic** (requires owner approval): for measured, disjoint, predeclared `C` and `T`, compute directly on authenticated raw counts:

```
student_C = log1p(10_000 * raw_C / sum(raw_C))
teacher_T = log1p(10_000 * raw_T / sum(raw_T))
```

No part of the original `L`, q count, opposite view or forbidden QC is used as a normalization denominator. The original `L` is used **only within the trusted boundary** to validate that mapped counts do not exceed the original source library. The protected q scalar does not need to be read even transiently by this version. The output object contains only query identity, predeclared view addresses, view-normalized values and structural-support masks. Each view requires positive observed counts, otherwise the unit is **nonestimable**, not imputed. The feasibility population and donor/operator exclusion rate must be declared prospectively.

V4 has a scientific tradeoff: within-view normalization loses absolute amount and may erase relevant total-mRNA differences; it can accentuate sparse-view noise and differs from the frozen original FULL104 measurement route. An independently defined exogenous size factor is another possible future choice, but one inferred from the full q/T RNA cannot be called leakage-free. If the scientist instead chooses a non-disjoint teacher permitted to see all remaining RNA, the opposite-view nonoverlap contract is different; do not claim the V4 disjoint-view result in that setting. Any new preprocessing is a **versioned successor authority**, not a silent modification of the established representation.

## 3. Local tests performed and code status

- `teacher_target_raw_adapter_v3.py` retains the q-only normalization for explicit historical comparison and red-team positive controls; it is **not** the preferred disjoint-view production solution.
- `teacher_target_visible_only_adapter_v4.py` implements independent raw-CSR visible-only normalization with exact signed-integer source-library checks, canonical CSR checks, injective non-overlapping address lists, structural measurement verification, positive visible-view depth requirements, and model-facing output with no q count or L. It does not call V3's q-dependent normalization, and it has **not** been wired into the live V5 reader/trainer.
- `test_teacher_target_raw_adapter_v3.py` and `test_teacher_target_visible_only_adapter_v4.py`: **15/15 tests PASS**, no expected fails or skipped cases, including 512 randomized triples of q/opposite-view changes, planted original full-L and q-only-route leakage, bad metadata and nonestimable zero-view failures. Py_compile checks pass.
- `teacher_target_view_leak_redteam_v4.py`: **300 historical archived RNA rows**, each with 1,024 student and 1,024 teacher genes selected from authenticated historical structural support without reading q expression. Five q/teacher counterfactual regimes; all 300 had nonzero visible context. Original full-L normalized non-query coordinates changed by as much as **0.69643** log units; recomputed V4 visible-only representation changed by at most **8.88e-16** in float64. If the historical normalized inputs are *independently re-encoded*, max discrepancy is **2.92e-7** at float32 and **1.07e-5** at six-decimal storage. The counterfactuals are mathematically derived, not physically observed alternate cells. This emphasizes why original **raw** production counts are preferred and why actual storage precision must be measured.

**Non-authorizing physical historical source:** user-provided 50,000 × 41,238 normalized expression NPZ (SHA256 `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`), discovery sample metadata CSV (SHA256 `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`), and August 24 address-support archive member (SHA256 `ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa`) were authenticated before the pilot. This **historical** archive explicitly excludes old T1 and protected expression/pathology; these data are **not** a valid current FULL104 authorization sample. No current V5 model or GPU training was executed.

## 4. Held-out-donor historical feasibility — and a specificity warning

Exploratory, non-JEPA SVD teacher / ridge student **only**, using the first 4,000 natural-mixture historical sample-A cells (3,610 SEA-AD, 215 NPH52, 175 HVS). Donor identities, q, common-measured gene support, deterministic partition and archived expression were obtained from the historical manifests. Shared structurally measured addresses in the sampled operators: **17,405**. The 1,200-gene exploratory panel was chosen using **training-donor expression only**, then split deterministically into two nonoverlapping q-specific complementary views. The fixed donor hash produces **82 train donors (3,158 cells)** and **20 held-out donors (842 cells)**. Target embedding and student SVD fit on train donors only; no current/full run.

| Held-out-donor exploratory pooled R² | APOE q=6186 | P2RY12 q=12469 |
|---|---:|---:|
| Visible-only context → complementary-view SVD teacher | **0.8313** | **0.8319** |
| Historical coarse class + operator only | 0.3834 | 0.3970 |
| Historical native/fine class + operator only | 0.5939 | 0.5809 |
| Visible student-view technical summaries only | 0.1228 | 0.1324 |
| Training teacher shuffled within donor + coarse class | 0.5341 | 0.5399 |
| Context plus native class and operator | 0.8557 | 0.8535 |

Across the **19** held-out donors with at least three sampled cells, equal-donor-mean context RMSE was ~**0.4183** (APOE) and ~**0.4151** (P2RY12), compared with native-class-plus-operator RMSE ~**0.7357** and **0.7388**. Donor grouping, not number of cells, is the uncertainty unit; these were exploratory single-split, exploratory-panel results and thresholds were **not** prospectively frozen. Native class labels may themselves be inferred from RNA. Higher cross-view R² may reflect broad molecular cell state, cell subtype, biological cell programs, and residual technical composition; it is NOT a query-local JEPA prediction result.

**Critical limitation:** the two historical visible-only SVD target embeddings can be linearly predicted from each other at **R² 0.8498 (APOE → P2RY12)** and **0.8423 (reverse)** on the held-out cells. Distinct partitions produce overlapping global cell-state information. This observation does **not** prove the absence of query-specific information, but there is presently **no direct evidence that conditioning on q is biologically necessary** rather than merely adding an address embedding to a generic state representation. Do not claim scientific target approval from the strong cross-view scores.

APOE and P2RY12 were **structurally measurable in every sampled historical operator**, but had nonzero observed counts in only **21.4%** and **11.975%** of these 4,000 cells respectively. This is a demonstration of why eligibility must follow structural support, not `raw_q > 0`.

## 5. Proposed next decision and exact experiments for Claude

**Candidate research direction, not a final scientific approval:** query-blind, view-isolated student/teacher preprocessing; a common shared RNA latent component; and a *separately measured query × cell interaction* to test whether the address changes the biological state prediction beyond the shared component. Do not assume the q-specific component exists just because q embeddings can be learned. The teacher may use shared q-conditioned attention over permitted T; online student predicts that stop-gradient EMA teacher target from independently normalized C.

Require all of the following on a prospective authorized *development-only* donor split **before** target qualification:

1. **Actual-source replay:** use the live authenticated Level-4 raw blocks, exact metadata source-library integers, support authority, exact canonical address registry and production consumer. Test the original `iter_blocks` as a planted leaky control, but create an explicitly new authenticated `iter_raw_blocks`/trusted q+view boundary instead of silently altering historical scorer semantics. Rehash original block manifest and every physically used original raw block. Test mixed operators in separately authenticated groups and structural zeros vs unmeasured q.
2. **Two adversarial invariance gates:** (a) q-only raw mutation with all other counts fixed; (b) **opposite-view-only mutation** with own-view counts fixed. In both cases each branch's *every exposed tensor*, view membership, metadata, learned input embeddings and teacher target must be invariant as appropriate. Positive leaky controls MUST fail. Structural q selection and view splitting cannot use q count or observed expression prevalence. Do not pass source L, unfiltered raw/full-L-normalized values or original global QC to the encoders.
3. **Feasibility by donor/operator/cell type:** declare exact nonestimable conditions for empty/low-depth C or T; quantify how often view-only normalization fails and how much biological coverage is lost. Predefine replacement options or stop conditions before outcomes are inspected. Compare view-only with an independently justified q-safe fixed external size factor only if available and authenticated.
4. **Anti-collapse and q-specificity:** teacher component variance and effective rank, student/teacher matched-versus-within-donor/native-class shuffled controls, query-identity-only, fine-class+operator, available technical-only, **q-agnostic shared-state** controls, and query-swapped paired prediction. Fit any generic shared-state projector and q-specific decomposition using only train donors. For held-out donors test whether `q × cell` adds reproducible held-out value beyond the shared-cell-state-plus-query-main-effect baseline. Check independent gene-program specificity for a predeclared q panel; do not optimize those programs on the same heldout outcome.
5. **Authority and evaluation:** obtaining an implementation test pass does not close the teacher-target semantics root, its representation/remaining-RNA comparator dependencies, the source/runtime/preexecution chain, the masking grid, or the total 33-root closure. Original V5 remaining-RNA V1 requires a lawful global-only comparator; with global context OFF, prepare a coherent successor contract or independently prove query-/view-safe global context. Keep FULL104 training OFF until separately approved B1 scientific and actually complete B2 authorization. External GSE174367 ATAC and GSE289721 feasibility work remain parallel, non-authorizing lanes.

**Do not** promote the exploratory 0.83 scores, q addresses, 1,200-gene panel, 82/20 donor split, visible-depth minimum, ridge alpha, embedding dimensions or random seeds into frozen production hyperparameters. Their only role here is identifying computational feasibility and likely shortcut risks in an explicitly historical archival sample.

## 6. Reproduce locally

```
python -m unittest -v test_teacher_target_raw_adapter_v3 test_teacher_target_visible_only_adapter_v4
# Historical input /tmp/foundation_discovery_50k.npz must be extracted from the two user-provided parts
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python teacher_target_historical_crossview_v3.py --rows 4000 --query 6186 --normalization visible-only --out teacher_target_historical_crossview_v4_visible_q6186_results.json
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python teacher_target_historical_crossview_v3.py --rows 4000 --query 12469 --normalization visible-only --out teacher_target_historical_crossview_v4_visible_q12469_results.json
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python teacher_target_view_leak_redteam_v4.py
```

Historical inputs are **not** included in the compact V4 package; this avoids duplicating the 600-MB original ZIP and ~392-MB calibration archive. Verify all original checksums before using them. The source revision being reviewed is separate from any subsequent live GitHub changes.