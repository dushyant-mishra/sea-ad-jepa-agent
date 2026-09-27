# JEPA R6 — target fidelity and V5 architecture/pipeline compatibility audit

**Scope:** non-authorizing local research and GitHub source-contract inspection, 2026-09-26. No merge, no production current-V5 training, no protected outcome inspection. This is an *interface audit plus isolated red-team prototype*, **not** a successful end-to-end execution of the live combined V5 runner. Historical data here have been repeatedly used in R1–R5; further results are development diagnostics, not independent confirmation.

## Source authority and actual branch topology

The exact inspected source was GitHub draft PR #165, head `25447126e3cf269b8416b52b1bbb98deebaa5d64` (V36 live issuer/guard). Its V5 `src/sea_ad_jepa/v5/` tree is materially larger than current `main` or the V43 branch; V43 #176 at `e7555ed0cc4dea07a2425da4185924a2d5728359` is based on `main` (`c49b13bd75c2d23716c777336db8fbfc78c09cd0`), **not** on PR #165, #169 or #163. The Phase-IV masking repair #169 (`e14c4003daf1248502ee83161fda8eb52376bb84`) is a separate stack. No individual branch is a ready-to-run integrated V43 production implementation. All refs must be refreshed before any changes.

Inspected exact Git blob SHAs on #165:

| V5 source | Git blob SHA-1 | Finding |
|---|---|---|
| `target_construction_authority_v1.py` | `aa2a498fc214b5df2342b443b98272147d90186d` | **Incompatible** with rich q-visible teacher: enum mandates `QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1`. Versioned scientific V2 successor required; keep V1 unchanged. |
| `teacher_target_semantics_authority_v2.py` | `0f0cf18db5e1217d292ef1c8d82db846e790c74e` | Generic q-local non-scalar semantics compatible in spirit, but does not type independent core/fine/rare targets, their coordinates, direct q teacher policy, abstention or individual provenance. Extend by versioned schema. |
| `production_protected_registry_authority_v1.py` | `2c94593f49321613867ac2710cf4adf5db9b3a59` | Derives `model_depth × 4 protected roles × 2 parameters` for **one** encoder-depth index. Does not identify independent teacher/student branches and their separate depths. New branch-aware successor needed. |
| `current_teacher_target_receipt_v2.py` | `4965241f53b660d12201132927fed9b39aa10af2` | Hash-bound package and 33-root lineage reusable; does not expose per-head target support, individual original source lineage or teacher/student input-policy distinction. Bind these inside a reviewed new target-package root and receipt successor. |
| `current_trainer_preexecution_contract_v2.py` | `bc5615e402ff74fd4b675cb7397d553eee2a4f8f` | Existing exact V2 root graph reusable at outer boundary; must bind the versioned target/geometry/registry successors and assert the actual model topology. |
| `qualified_optimizer_guard_v3.py` | `cca2461880f6bbe78cad2c6df1238cb9664cb8b8` | Live issuer check at guard install, arm and step is reusable *once* upstream typed proof is valid; do not treat token validation as evidence all online modules have real gradients or every EMA teacher updated. |
| `current_atomic_checkpoint_guard_v2.py` | `bcc8f1835ebceadd23091520a287f9182e691290` | Generic exact-root + telemetry mapping is useful. Per-head/branch optimizer, EMA, scheduler, RNG, donor exposure, support decisions and abstentions require typed telemetry and replay validation. |
| `masking_rng_replay_authority_v3.py` | `8f00708ae0ee61b428ea176570ba5a2929e14254` | Reuses stable pre-panel masking roots and preserves mask families when target panel changes. Production has **four** authenticated folds; the local R1–R6 **five** historical diagnostic folds cannot be substituted. Teacher and student have distinct observation policies; only student requires q-free input lineage. |
| `ema_presentation_v1.py` | `6f4442e25a6f891b9548b11403154233f616d842` | `exp(log(.5)*presentations/half_life)` can be reused for each explicitly mapped EMA branch, after actual successful optimizer step. Half-life remains a separately authorized scientific choice; no historical `.996` default. |

The existing V5 32 upstream-root + preexecution receipt vocabulary need not gain arbitrary top-level roots solely because teachers become multi-head; **head-specific evidence must be cryptographically bound through the existing typed root roles, or a formally reviewed root-schema successor**. Reusing the same digest strings while changing the target's meaning is forbidden.

## Historical developmental target stress (already-existing local R6 outputs, inspected in this audit)

R6 used the same reused 1,561-cell historical donor population (361 microglia/PVM; five disjoint 10-donor test folds), 40 dependent q–fold tasks and per-fold training-only neighborhood selection. It used original input data, not protected FULL104 outcomes. Split-half count thinning of the original non-q context is only a *repeatability proxy*, with shared technical effects still capable of inflating it:

| Context N(q) size | All-cell repeatability proxy | Microglia repeatability proxy |
|---|---:|---:|
| 8 | 0.4839 | 0.4479 |
| 16 | 0.5040 | 0.4652 |
| 32 | 0.5098 | 0.4770 |

Teacher-only measured disjoint held-out H(q) RNA panel, all-cell mean R²: N8 only `0.30308`, N8+q `0.31061`, N8+visible technical `0.34356`, N8+visible technical+q `0.34601`, visible technical only `0.32679`, q only `0.12102`. Microglia: N8 `0.22175`, N8+q `0.23008`, N8+technical `0.26681`, N8+technical+q `0.26948`, technical only `0.26043`.

**Interpretation:** the observed queried value adds only about `0.00245` all-cell / `0.00267` microglia R² *after* the technical baseline in this particular same-assay predictive test. The raw R5 +0.00753 q increment was not wrong, but it was not technical-adjusted. Do not declare that the richer teacher has gained *biological* information, choose N8 over N16/N32 from these reused data, or call split-half RNA repeatability biology. This is an important reason to prioritize independent teacher-only biological falsifiers over multi-teacher engineering.

## Portable non-authorizing architecture bridge implemented here

`JEPA_R6_ARCHITECTURE_BRIDGE_RESEARCH_20260926.py` + `JEPA_R6_ARCHITECTURE_BRIDGE_REDTEAM_20260926.py` specify/test a *proposed* logical target and topology boundary for the candidate rich, shared-head or separate-team architectures. This local program **does not import, override or authorize** the protected V5 modules and does not authenticate original source bytes by a syntactically valid SHA alone.

The bridge enforces canonical same-cell/same-query teacher heads; q-value-visible teacher option versus strictly q-free student input, normalization and QC ancestry; no direct q scalar or teacher-target panel values in student inputs; explicit unsupported-head abstention; duplicate-head rejection and copied-specialist diagnostic without consensus suppression. Its topology enforces every declared online encoder/predictor in the optimizer, no EMA teacher directly optimized, complete branch-qualified protected attention tensors across each declared encoder depth and exact online-to-EMA pairing. The bridge validates **logical payloads and manifest inventories only**; it is not a cryptographic proof of measured assays or physical step evidence.

`python JEPA_R6_ARCHITECTURE_BRIDGE_REDTEAM_20260926.py` completed **25/25 isolated local tests**. Cases include direct, denominator and QC q leakage, mismatched same-cell identity, fake-zero abstention, missing target-input ancestry, duplicate heads, copied specialist detection, teacher in optimizer, unguarded online predictor, missing branch protected tensor and missing EMA pair.

## Pipeline compatibility decision and next integration sequence

1. **Keep current substrate, donor support and anti-spillover rules.** Their measured/unmeasured distinction, population and source SHA, donor-uniform sampling, exact row identity and existing historical provenance remain relevant. A teacher may see q; the student still must not receive q, even through normalization/QC/global descendants.
2. **Decide biological target before changing authorizing enums.** Compare q-visible versus q-excluded teacher on a fixed, untouched development biological measurement, with technical adjustment, query-specific falsifiers and support thresholds predeclared. The measured N8 target is a developmental *anchor*, not yet the complete latent teacher world state. Do not freeze clinical/pathology or independently reserved ATAC outcomes based on R1–R6.
3. **Add versioned teacher-target construction semantics**, per-head support/abstention, ordered target genes, coordinate basis, input derivation lineage and teacher q policy. Preserve existing V1/previous receipt bytes; rebind the exact live target constructor. Reject a schema that merely changes enums without exact original-input authentication.
4. **Run both single-rich and multi-head/multi-teacher topology through branch-aware dynamic registry**, topology manifest, full per-module gradient/Adam and optimizer step/cursor protection, and one distinct EMA update per mapped online–teacher pair *after* the verified optimizer step. Check rare-head inactive updates and do not age an EMA teacher on a skipped step.
5. **Retain separate student mask family and teacher information policy**. Revalidate #169 source successor against the chosen target and #163 scientific teacher options. Production four-fold replay and any chosen q-neighborhood-specific co-masks need their own frozen policy; five-fold historical tournament seeds are not production seeds.
6. **Expand target/optimizer/checkpoint receipts and real critical-suite evidence to cover the new implementation source and topology**. Original 33-root V5 closure is still `0/33` complete; synthetic V40/V41 evidence is not a production suite proof. Run tests against exact combined branch source after an independent dependency reconciliation; never infer one green PR means the other stacks were exercised.
7. **Only after target-only biology passes**, train capacity/compute-matched developmental neural A single-rich, B shared-head and C complementary-team contenders. Same donor partitions, assay availability and approved target semantics; scored on independent biology and q-specific student predictability separately. If specialist biology adds no residual information beyond rich teacher after controlling for technical effects, pivot to single-rich and preserve specialists as diagnostics rather than ship extra machinery.

**Hard boundaries:** TRAINING OFF; protected FULL104 outcomes, D_shared G5 and Audit-B N1 unopened; historical exploratory subset not qualification data; no live GitHub repository edits made by this local artifact. All 25 new tests are isolated research-contract tests, not tests of integrated live V5 code.
