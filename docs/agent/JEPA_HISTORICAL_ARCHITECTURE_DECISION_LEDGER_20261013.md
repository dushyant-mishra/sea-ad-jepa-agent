# JEPA historical architecture / target / teacher / student / EMA decision ledger

**Date:** 2026-10-13  
**Status:** non-authorizing historical reconciliation and supersession map  
**Purpose:** prevent future agents from re-running closed experiments, reviving superseded interpretations, or using pre-repair gene-semantic evidence as current architecture authority.

## Read this with

- `docs/agent/memory-os/DECISION_REGISTRY.csv`
- `docs/agent/JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V3_FINAL.md`
- `docs/agent/JEPA_HISTORICAL_HANDOFF_TARGET_AUTHORITY_AUDIT_20261005.md`
- `docs/agent/JEPA_REPOSITORY_AUTHORITY_CLEANUP_AUDIT_20261005.md`
- `docs/agent/CURRENT_SUPERSESSION_MAP.md`
- `docs/agent/CURRENT_AUTHORITY_INDEX_20261005_SUPERSESSION_NOTICE.md`
- `docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md`
- machine mirror: `results/target_discovery/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.json`

The existing repository inventories remain the exhaustive file/script/config navigation layer:

- `results/tables/project_file_inventory_v1.csv`
- `results/tables/project_script_dependency_inventory_v1.csv`
- `results/tables/project_doc_config_index_v1.csv`
- `results/tables/v3_scorecard_status_v1.csv`

This document does **not** duplicate every historical byte. It records which conclusions survive, which are closed, which are only controls, and which evidence must be replayed because its molecular identity provenance is insufficient.

---

## Evidence identity classes

Every historical biological architecture result must be assigned one of these before reuse:

1. **`SOURCE_NATIVE_SAFE`** — source-native experiment whose relevant feature identity was not in the later NPH identifier-poor class. Historical SEA-AD MTG/DLPFC rare-head/graph work belongs here; keep its original scope and limitations.
2. **`FROZEN_4K_IDENTITY_AUDITED`** — experiment bound to the frozen 4,096 canonical Ensembl vocabulary later revisited by the Stage81A2R protected-identity audit.
3. **`REPAIRED_41K_ADDRESS_BOUND`** — experiment uses the repaired 41,238 molecular-address namespace and explicit `source_feature_index -> molecular_address_index` materialization.
4. **`SEMANTICS_FREE_MECHANICS`** — optimizer, AMP, EMA, checkpoint, numerical or custody evidence whose conclusion does not depend on gene biological identity.
5. **`GENE_IDENTITY_PROVENANCE_UNRESOLVED`** — pre-repair NPH/cross-source gene-semantic evidence without sufficient address binding. It is **not** active architecture authority. Replay is required if the question remains material.
6. **`NOT_GENE_SEMANTIC`** — governance/design/custody result rather than biological gene-semantic evidence.

The later gene-identity repair is **not** a blanket reason to invalidate old science. It is a reason to classify it correctly.

---

# Closed results — do not repeat or rename

## Hidden-gene / CELL anchor

**Historical conclusion:** rejected. `JEPA_ONLY > CURRENT >> ANCHOR_ONLY` in the matched causal history.  
**Current status:** `CLOSED_DO_NOT_REPEAT`.  
**Identity:** `FROZEN_4K_IDENTITY_AUDITED`.  
**Rule:** do not reintroduce the hidden-gene anchor absent genuinely new causal evidence.

Source authority: `docs/agent/memory-os/DECISION_REGISTRY.csv` (`DEC-001`).

## Query/address exposure as V6 bottleneck

**Historical conclusion:** rejected; exposure-dose slope was near zero.  
**Current status:** `CLOSED_DO_NOT_REPEAT`.  
**Rule:** do not spend new experiments debugging address exposure as a target rescue.

Source: `DEC-002`.

## Core-only evidence

**Historical conclusion:** insufficient for difficult/rare biology; distributed halo evidence helped rare-state inference.  
**Current status:** closed principle, retained.  
**Rule:** preserve lawful complementary evidence. Do not create artificial difficulty by starving the student of broad context.

Sources: `DEC-004`, `DEC-005`.

## Tier hiding / evidence-starvation cascade

**Historical conclusion:** rejected. Apparent low-dimensional gains did not survive stronger teachers; balanced tier hiding hurt biology.  
**Current status:** `CLOSED_DO_NOT_REPEAT`.  
**Rule:** if a cascade is later justified, cascade targets/queries, not evidence starvation.

Source: `DEC-006`.

## T0 / T1 / TCTX production-target lineage

**Historical conclusion:** no production winner. In the real forward-only gate, T1/TCTX row prediction was reported as almost entirely explained by address identity. TCTX fixed a self-information problem but did not become a causal target winner.  
**Current status:** `CLOSED_DO_NOT_RENAME_AND_REPEAT`.  
**Identity:** `FROZEN_4K_IDENTITY_AUDITED`.

Sources:
- `docs/agent/JEPA_TERMINAL_TARGET_LINEAGE_RECONSTRUCTION_20261005_V3_FINAL.md`
- `docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md`

## Static/context decomposition

**Historical conclusion:** contextual signal existed but the historical gate did not establish enough increment beyond identity to authorize the target.  
**Current status:** context-exists is closed as a sufficient target argument.

## V6R5B donor-cross-fitted residual target

**Historical terminal:** `RESIDUAL_TARGET_DOES_NOT_RESCUE`. Numerical residual-H prediction improved, but gains were overwhelmingly cell-global and molecular recovery remained poor.  
**Current status:** `CLOSED_DO_NOT_REPEAT`.  
**Rule:** do not rerun the residual address-selective predictor-capacity diagnostic absent genuinely new reauthorization.

Sources: terminal target lineage + `DEC-012`.

## Historical PROD41K T1 training

**Historical result:** did not qualify biology. Later mechanics audit superseded the old claim that the 205-update run had valid optimization mechanics: 48 attention-related optimizer moment tensors were exactly zero while their step counters advanced. The historical fp16-autocast backward condition was causally implicated; disabling autocast around backward restored the tensors under the frozen repair test.  
**Current status:** `CLOSED_DEFECTIVE_TRAINING_EVIDENCE`.  
**Rule:** do not rehabilitate, extend, resume or retrain the historical T1 path. Preserve the repaired gradient/optimizer gate in successors.

Source: `DEC-015`.

---

# Rare/specialist student history

## Stage69 / Stage70 rare auxiliary head

Stage69 showed an internal rare-auxiliary signal. Stage70 performed the stronger robustness/lock audit and **did not** earn a new benchmark lock.  
**Current status:** `NEGATIVE_PRIOR_CONTROL_ONLY`; not a co-equal production student topology.  
**Identity:** `SOURCE_NATIVE_SAFE` because this lineage used SEA-AD source-native MTG/DLPFC material rather than the later NPH identifier-poor feature universe.

Key sources:
- `scripts/run_stage70_rare_microglia_auxiliary_head_robustness_lock_audit_v1.py`
- `results/reports/stage70_rare_microglia_auxiliary_head_robustness_lock_audit_report_v1.md`

**Carry forward:** a specialist rare student should reappear only if the new qualified rare target demonstrates measurable negative transfer/interference in the shared student.

## Stage71 graph auxiliary

Historical graph benchmark did not establish graph-specific biological value; randomized graph control outperformed the real graph auxiliary in the internal benchmark and neither rare-cell representation nor donor-prediction lock was earned.  
**Current status:** `NEGATIVE_PRIOR_CONTROL_ONLY`.  
**Identity:** `SOURCE_NATIVE_SAFE`.

Sources:
- `scripts/run_stage71_full_rare_microglia_graph_jepa_hierarchical_benchmark_v1.py`
- `configs/agent/stage71_full_rare_microglia_graph_jepa_hierarchical_benchmark_v1.yaml`

**Carry forward:** regulatory/graph information may be reconsidered as privileged critics/corroboration, but graph-JEPA auxiliary training is not a default foundation arm.

---

# Teacher topology history

## V43 complementary teacher/student design — PR #176

Research-only prospective design comparing:

- A: single rich teacher;
- B: shared teacher trunk with typed/multiple heads;
- C: complementary/independent teacher team;
- controls for rare heads, support, q leakage and compute.

**Result:** design provenance only; no architecture selected.  
**Current status:** `DESIGN_REFERENCE`.

## V44 original-RNA tiny proxy — PR #177

This is the most useful historical topology prior that survives the identity re-audit.

The experiment used the historical 50k x 41,238 discovery expression substrate tied to the August calibration bundle and all-42-operator common support. It is therefore classified `REPAIRED_41K_ADDRESS_BOUND`.

Descriptive held-donor proxy result:

- rich R (unfair C+T teacher evidence): ~0.41588;
- A single T-only teacher: ~0.40267;
- B shared multi-head/projection: ~0.40782;
- C independent team: ~0.40186;
- D rare-tail specialist: ~0.40042.

**Interpretation that survives:** shared multi-head deserves a positive prior; independent teacher teams and rare-tail specialists did not earn extra complexity.  
**What does not survive as authority:** no neural IPB/EMA architecture winner, no q-specificity, unmatched compute/parameters, same-cell RNA Y readout.

Source: `analysis/v44_tiny_teacher_team_tournament_20260926/README.md` on PR #177.

---

# Teacher target-construction history

Historical target-construction policies included a q-value-visible rich teacher, q-value-blind rich complementary teacher, same-evidence value-blind control, block-blind teacher, and residual diagnostic. The corrected synthetic T_A/T_B comparison was explicitly **not informative** about real biology because the simulator's signal allocation could decide the result by construction.

**Current status:** unresolved only at the level of **zero-update target construction on real repaired TRAIN evidence after TD target semantics are known**. Do not treat the old synthetic comparison as winner selection.

---

# Student prediction semantics that remain active

The rich-teacher / partial-RNA-student audit established a durable principle: teacher-private information cannot generally be forced into a deterministic realization-level point target for an RNA-only student.

The downstream implementation must support typed recoverability:

- point-identifiable / conditional mean;
- distributional or state + biological uncertainty;
- teacher-private/auxiliary-critic-only;
- abstention / `NOT_ESTIMABLE`.

This is a scientific contract, not an optional architecture flourish.

---

# EMA and optimization history

## What is closed

Historical fixed/scheduled EMA sweeps explored values including `.992`, `.996`, `.99925`, `.9995`, `.9999` and schedules such as `.996 -> 1.0`. They established responsiveness/lag behavior but **did not select a production EMA**.

These conclusions are `SEMANTICS_FREE_MECHANICS` and survive the gene-ID issue.

Do not inherit `.996` or any other historical beta as authority.

## What remains active

The later V5 runtime made **EMA half-life in successful base-cell presentations** the native timescale. That is the preferred mechanics abstraction because it remains meaningful when batch size or accumulation changes.

**Production half-life is still unselected.** A compact short/intermediate/long presentation-half-life comparison belongs after target semantics and the downstream architecture are sufficiently fixed.

## Anti-collapse variance objective

A weak per-slot std/variance safeguard was studied but did not earn production-objective status. Keep effective rank, per-slot variance, singular-value concentration, geometry and redundancy telemetry. Do not add a variance penalty unless an actual collapse mechanism is demonstrated.

---

# Historical results downgraded by the gene-identity repair

The important rule is **not** "old NPH data were bad, so all old science is invalid." The correct rule is:

> pre-repair gene-semantic evidence involving NPH/cross-source feature identity is not active architecture authority unless it can be bound to the repaired molecular-address registry.

The clearest current example is the old 2/4/8 teacher-view preference. The decision registry already left it provisional. Its exact old numeric preference should **not** be inherited; replay on repaired/bound FOUNDATION TRAIN is required only if teacher view count remains scientifically material.

Status: `GENE_IDENTITY_PROVENANCE_UNRESOLVED -> REPLAY_REQUIRED`.

---

# TD relational history that future architecture agents must not reinterpret

## PR #314 corrected replay

Frozen/spent result:

- TD56 PASS;
- TD57B PASS;
- TD57C failed only the **universal nearest-third fine-local recurrence** claim at HVS P0 under sequential stop;
- TD59 PASS;
- overall route remained broad/mesoscale relational viable;
- no target winner.

Do **not** convert TD57C into "rare/local biology absent", "C2 invalid", or "dataset bad".

## Current successor chain

Historical PR #316 remains frozen at `2397ab83d8ae9d0c762a8fd5f3919edc350d137f`. Its earlier one-process external execution path is superseded for the synthetic test-of-test.

Current audited successor:

- TD custody/science PR #320 @ `1f474a44a6baabc667dbfda726e0755426c732e7`;
- synthetic V2.1 PR #321 @ `15f519c00137d581e25232c16be52c2b9badd83e`;
- package `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`;
- pre-fit archive `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`;
- controller archive `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`;
- raw controller manifest `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`;
- semantic/hiding commitment `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`;
- certification receipt `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`;
- terminal `READY_TO_EXECUTE_BLIND_FIT`.

No biological test-of-test has run. Controller truth remains unopened. Next lawful action is phase-1 blinded fit only, freeze the V4 receipt, STOP, independently audit that receipt, and authorize controller adjudication separately.

---

# JEPA-Anything / OPF audit

PR #322 adds a non-authorizing post-paper robustness audit and repaired-41K smoke probes. The conclusion is **not** "beat JEPA-Anything" and **not** "replace the target portfolio with OPF".

Carry forward:

- target semantics stay biologically typed/accountable;
- stable subspaces matter more than named latent coordinates;
- OPF-like factorization may later be a capacity-matched numerical challenger **inside** a qualified biological block;
- global orthogonality does not establish biological independence and cannot compensate for failed C1/C2/C3/rare/transport claims.

Sources:
- `docs/agent/JEPA_ROBUST_PIPELINE_POST_JEPA_ANYTHING_AUDIT_20261013.md`
- `results/target_discovery/JEPA_ROBUST_PIPELINE_SMOKE_AUDIT_V1.json`

---

# Reduced carry-forward set

After the historical audit and gene-ID reclassification, the downstream neural architecture space is intentionally much smaller:

**Primary teacher topology candidates**
- single rich EMA teacher;
- shared EMA backbone + biologically typed heads.

**Conditional teacher topology**
- independent complementary teachers only if a predeclared interference test demonstrates material loss in the shared teacher.

**Primary student topology**
- one full-capacity shared student backbone + typed prediction heads.

**Conditional student topology**
- specialist branches only if qualified target evidence demonstrates negative transfer/interference.

**Prediction semantics**
- typed point/mean/distributional/uncertainty/abstention according to recoverability.

**EMA**
- presentation-normalized half-life; compact timescale screen; no inherited production beta.

**Optional numerical challenger**
- capacity-matched internal factorization/OPF only after biological target blocks are frozen.

This reduced set is the state future implementation work should start from. Everything else in this ledger is a closed result, control, negative prior, historical design reference, or replay-required question.

---

# Authority boundary

This ledger creates **no** target selection, TD60, Stage4, multimodal-training or JEPA-training authority. It is a navigation/supersession artifact whose purpose is to stop repeated work and repeated mistakes.
