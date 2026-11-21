# JEPA historical chronology — additional source recovery, rounds 17–20 (2026-11-02)

**Status:** `APPEND_ONLY_HISTORICAL_EXPERIMENT_AND_SOURCE_EVIDENCE__NON_AUTHORIZING`. This is a successor to [`JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_20261102.md`](JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_20261102.md), not a replacement for the original historical decision ledger or any frozen earlier result. It adds original-source context recovered in a further four passes after the Graph-JEPA/Stage76–79 reconciliation. All original files below were read-only. No biological rerun or issuer rights were created.

**Authority remains:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## Round 17 — V2 Graph-JEPA matched topology comparison and evolving baselines

The original V2 real-graph/identity/strict-shuffle comparison was **physically evaluated**, using previously trained separate checkpoints and donor-heldout ridge readouts. It did not perform new training in the evaluation stage.

| V2 comparator | Mean donor OOF Spearman on the reported five pathology targets |
|---|---:|
| Real-graph JEPA latents | **0.2892** |
| Identity / no-graph JEPA latents | **0.2514** |
| Degree-preserving zero-overlap strict-shuffled graph JEPA latents | **0.2470** |
| Raw-expression regularized | **0.2867** |
| Module-mean non-neural | **0.2999** |

Real-minus-no-graph **+0.0378**; real-minus-strict-shuffled **+0.0422**. V2 therefore established **graph-specific improvement over tested neural graph controls**. It did *not* establish superiority to the simple non-neural module baseline, external biological truth, perturbational causality or transferable graph-topology gain. NeuN in that comparison favored no-graph. Do not rewrite the earlier V2 positive as wholly negative, nor project it onto V3's later decision rules.

Exact report sources:
- `results/reports/no_graph_ablation_predictive_representation_comparison_v1.md` blob `9a0b1b265257215a98bdb72689360821d742864d`
- `results/reports/strict_shuffled_graph_ablation_predictive_representation_comparison_v1.md` blob `85baa626edb9e3c9d699f8c3150c25ca8322120b`

V3 then actually ran **nine non-neural baselines on the locked Stage24 five-fold / 84-donor protocol**, producing an *intermediate* Stage25 module-mean high-water mark **0.3325**. Later the governing baseline and Stage27C reference were updated under their respective scorecards (module-mean **0.3128**, Stage27C **0.32670244**). These values are historical study-specific results, **not scores to rank in one pooled table** unless cohort, target, transform, split and comparison scopes are harmonized. Stage31's residual graph audit tested an optional graph residual/anti-oversmoothing strategy, best **0.32637036**, just below Stage27C; full-pass false though one target-specific partial gate passed.

Additional original sources:
- `results/reports/v3_primary_baseline_benchmark_suite_v1.md` blob `eb33a437917de0ceadeefa506066b77f853aed1b`
- `results/reports/stage31_residual_graph_controls_report_v1.md` blob `bd18428fec0a61795f30033a6c0ce141dfcefe68`

**No-repeat and interpretation:** Both V2's narrow positive and V3's stricter nonpromotion are valid in their own experiments. There is no blanket rule that every graph experiment failed. A future graph claim must identify the specific assay, cohort, frozen comparator, controls, scientific estimand and architectural generation.

## Round 18 — Stage81A3: executed synthetic information-preservation failure, not absent testing

The massive original source `docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md` (blob `5fbd0689333b1c774908878fe2cf930dbcac4d10`, 3,334 lines) contains distinct chronological experiments, including:

- Real-RNA **forward-only** forensic work: normalized RNA effective rank ~442.84; an untrained pooled Perceiver state fell to effective rank ~3.22–4.40. This is source-geometry diagnosis, not an authorized production training.
- A 2-fixture × 5-seed **500-update** baseline JEPA geometry test: 8,192 synthetic cells / 4,096 measured genes per fixture, 32 held-out generating factors, **5,000 optimizer and 5,000 matching EMA updates**. Loss fell sharply but factor recovery stayed poor, cross-attention almost uniform and representations narrowed; no seed selected or discarded.
- A *different* predeclared final Stage81A3 information-preservation candidate that variance-normalized gene-to-latent Q/K attention logits and replaced pooled arithmetic mean with a TRAIN-only **PCA160 over flattened 24×160 slots**. Exactly **10 × 500 synthetic updates** were run, without real RNA/pathology. Engineering checks, optimizer/EMA, deterministic resume and checkpoint health passed; postqualification regression **179 tests passed**.
- **Biological information gates failed:** median final unmasked target-PCA factor R² **0.528 / 0.549** (balanced / dominant-axis), masked student factor R² **−0.507 / −0.407** despite normalized raw-visible R² **0.539 / 0.573**. All seven S1–S7 scientific gates except S1 failed; geometry safety failed; JEPA loss nevertheless fell >99%. The explicit final decision was **`CURRENT PERCEIVER COMPRESSION PATH FAILS INFORMATION-PRESERVATION GATES`** and **`DOES JEPA EARN ITS PLACE IN V4? NO FOR CURRENT FORMULATION`**.

The baseline test and the final candidate each recorded a 5,000-update campaign; **do not conflate them as one single run or claim the later target/scientific result was rescued by loss decline**. The final candidate itself is not a universal proof against JEPA architectures; it is a scientific no-repeat result for the precise fixed architecture, masking, simulator and gates. The report explicitly forbade post hoc temperature, EMA, checkpoint, seed or pooling retries under that closed qualification.

## Round 19 — Stage81A3's *later separate* synthetic belief, real-data observation and rare-state investigations

The same original report continues with numerous distinct, actually executed and audited experiments that do **not** retroactively pass the failed Perceiver JEPA candidate:

- **RLC-CD and conditional recoverability:** token-preserving residual completion and a three-condition 100-update synthetic neural comparison were executed; linear completion matched or beat the neural alternative. A controlled conditional-predictability audit classified the 60/40 target **largely unidentifiable**, with ridge count-to-latent completion not adding information beyond visible counts.
- **Belief/uncertainty lineage:** RepPCA-160 qualified as a synthetic reproducible state basis; conditional covariance first proved scale-miscalibrated (median OOF/in-sample variance ratio **64.43**), then validation-only covariance fitting supported bounded correlated Gaussian structure but showed rank-nine LRD underexpressive. A 150-update trainable-encoder belief run regressed molecular token retention. Frozen-encoder reconstruction recovered retention at ~**1.002057** versus ~**0.881119** after trainable belief updates, confirming gradient interference for that specific model. Learned correlated belief, causal sidecar, point-state recovery and structural-panel neural retraining did not earn production adoption; scalar recalibration was enough for the tested panel setting but did **not** resolve cell-specific uncertainty localization.
- **Pathology-blind real-TRAIN bridge:** historical Stage81A2 had **13 datasets, 36 canonical matrix entries, 149 TRAIN donors, 19 development, 19 sealed, top-4096 features**. On that *restricted frozen vocabulary*, all 36 source masks were fully covered. This does **not** generalize to the later **42-operator/41,238-address** Stage81A2R universe. A real TRAIN-only **17,839-cell** equal-matrix PCA160 captured **42.47%** variance, with strong matrix/technology imprint and no new real optimization. The 60/40 synthetic mask was explicitly *harsher* than the real complete top4096 masks; count-split measurement noise is not an automatically richer biological teacher.
- **FBSDQ / pre-freeze resolution:** donor-balanced, count-split, equal-matrix PCA160 vs RepPCA160 and domain/measurement evidence audits supported **PCA160 as a bounded diagnostic basis**, rejected extra REP complexity, and found a stable global subspace but rotating individual axes. Quality descriptors were allowed only as **measurement context**, not identity covariates. This did *not* freeze a production basis or settle all dimension-resolution questions.
- **Rare-state completeness was iteratively tested:** an initial bounded sample could not identify four rare labels, so a deterministic targeted read-only audit recovered adequate preservation for four listed states. A subsequent all-**14 donor-recurring annotation-defined rare-state** audit reported 14 robustly identifiable, zero critical PCA flags, and no REP160 advantage; **annotation-defined coverage is not exhaustive rare-biology discovery**. A separate data-defined audit had 105 candidate cells, 65 neighborhoods, three donor-recurring neighborhoods but **none stable across the four fixed resamples**. Its decision was **rare-biology discovery not saturated / data coverage incomplete**, not a demonstrated intrinsic architecture failure. The prior 13-label census and later all-14 census are different dated counts.
- **Real spatial-context eligibility:** Uniform Context Data Qualification (UCDQ) audited **21 acquired datasets and 234 sample records**. Slide-tags SCP2167 met nonprovenance same-entity gates (4,065/4,067 exact coordinate-linked matches, 36,601 source features), but the first automated run was quarantined due to unresolved human provenance and had an explicitly documented incidental governance leak in a pre-reader terminal preview. Later *human publication-only* adjudication upgraded the source's provenance to `NEUROTYPICAL_DECLARED` and bounded role to `CORE_SAME_ENTITY_BROAD_CONTEXT`; five Fang STG MERFISH experiments (two donors) supported separate context replication, while Fang MTG was quarantined. **Identifiability of a real context-value test was earned; execution of a context-benefit experiment was not.**
- **Final governance correction:** the frozen 4,096-gene vocabulary was top-K engineering capacity rather than transcriptome saturation. Later Stage81A2R addressed the universal molecular address count; **gene-token contextual width `d_gene=160` and global state resolution `d_cell=160` must not be conflated**. The original report explicitly closed at `STAGE81A3 COMPLETE: NO`, `FREEZE 1 DECLARED: NO`, `STAGE81B STARTED: NO`, `STAGE81C STARTED: NO` (the separate Stage81C exposure-budget *audit* was not Stage81C production training).

This is a real multi-stage scientific program with strong positive mechanics and bounded negative scientific outcomes. **Do not simply say “PCA160 failed” or “rare cells were not preserved.”** The failed Perceiver, qualified-but-unfrozen PCA diagnostic, 14-state annotation coverage, unstable de-novo rare discoveries and eligible-but-unexecuted spatial context are distinct.

## Round 20 — scientific/architecture linkage back into current unified JEPA target research

The historical sequence explains much of the subsequent architecture and governance:

1. V2's controlled graph contribution, V3's stronger no-graph baseline and Stage31/35C/71 mixed results created an evidence-based **graph-is-conditional** policy, not a blanket graph prohibition.
2. Stage81A3's valid optimizer and declining loss still failed information preservation: this supports the later demand for a **measured teacher target**, complementary observation advantage, visible-raw comparisons, candidate-neutral truth, and anti-shortcut gating.
3. Stage81A3's synthetic/real 60:40 mismatch and full top4096 mask highlight why later **source-native 41,238-address matrix/operator rights, missingness semantics and no-queried-molecule proofs** are necessary. Never infer physical source validation from synthetic mask gates or frozen top-K coverage.
4. The recovered Stage81A3 stable-subspace/rotating-axis outcome and unresolved intrinsic representation dimensions underlie later full-population width/dimension independence requirements. Earlier `d_cell=160` was never a warranted permanent production representation selection.
5. Donor-balanced rare-label success did not prove saturation of novel rare states. Later whole-population and synthetic rare/technical pseudo-rarity work therefore inherits **both** the successes and the unresolved rarity-support issue.
6. SCP2167/Fang source-role work gives an already adjudicated lawful context candidate. It does **not** establish benefit from a physical context learner, and separate spatial assays have distinct pairing/donor limits.

## No-repeat, authority, and archival constraints

- These four rounds are **historical source reconciliation**, not new scientific reruns or independent approval. They supplement [the original October architecture decision ledger](JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md), [the recovered pre-September chronology](JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_20261102.md) and [the continuous audit/handoff protocol](JEPA_CONTINUOUS_CHRONOLOGY_AND_IMPLEMENTATION_CUSTODY_20261102.md).
- Source codes, frozen documents, original datasets and checkpoints are unchanged. Do not repin October 28 freeze digests.
- No old pathology/SEALED outcomes are granted newly independent validation status. The original Stage81A3 pathology-blind TRAIN versus DEV/SEALED rules and protected NPH52 expression restrictions are preserved.
- Any prospective new design or real run must first specify the *changed scientific question/inputs*, reuse earlier experiments where valid, and pass newly applicable issuer/evidence/masking/source-rights and independent-review contracts.

**Terminal:** `HISTORICAL_EXPERIMENT_GAPS_17_20_RECOVERED__NO_REEXECUTION__NO_SCIENCE_PROMOTION`.

---

## November 2 follow-on chronology correction (rounds 21–24)

**The phrase `Stage81A3 remained unfrozen` in this early recovery applies to the *then-current* Stage81A3 microqualification and failed Perceiver candidate, not the complete subsequent Stage81A3R historical lineage.** The later, source-preserved Stage81A3R Freeze1 contract **DID DECLARE `STAGE81A3_FREEZE1_DECLARED` with `d_global=224`**, under a 149-TRAIN-donor / 42-operator / 4,726-cell bounded protocol. It remained **historical-only** after the September 7 import and supplies **no current FULL104 production dimension, biological target, Stage4 or training authority**. Read [`JEPA_HISTORICAL_CHRONOLOGY_RECOVERY_ROUNDS_21_24_20261102.md`](JEPA_HISTORICAL_CHRONOLOGY_RECOVERY_ROUNDS_21_24_20261102.md) before reusing or paraphrasing this early statement. That later audit also records TD19's depth-only pseudostate negative control, Stage73R's non-winning graph result, and the discarded V5 x4 estimator.
