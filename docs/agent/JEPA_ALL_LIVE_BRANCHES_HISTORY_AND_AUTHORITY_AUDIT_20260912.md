# JEPA all-live-branches history and authority audit — 2026-09-12

Status: `ALL_LIVE_BRANCHES_ENUMERATED_AND_REVIEWED_FOR_HISTORY_AUTHORITY__NO_TRAINING_AUTHORITY`

Purpose: preserve an explicit branch-by-branch reconstruction after discovering that current `main` does not contain all authority-bearing historical evidence. This audit reviews every live branch present during the 2026-09-12 inventory by comparing it to `main`, classifying its unique content, and opening the authority-bearing files that materially affect project history. It does not promote branch-local claims into current authority merely because they exist. Branch names are not authority.

## 1. Canonical current base

Current canonical `main` observed for this audit:

`ba3f2a1200d0bbaf4b9ee0d7d16ddc17341d779f`

`main` remains current governance, but it contains a semantic conflation in `START_HERE.md`: the heading `T0 / target discovery` and surrounding V21 wording collapse two historically distinct lanes. The separate lineage reconstruction in PR #16 corrects this without discarding the valid requirement that upstream biological-object qualification and downstream V5 anti-shortcut qualification must both close.

## 2. Audit method

For each live branch:

1. enumerate the remote ref;
2. compare branch head to `main`;
3. classify as ancestral/no unique delta, duplicate tip, divergent historical evidence, or current/active work;
4. inspect unique authority-bearing docs/configs/scripts/evidence where the comparison exposed scientifically or methodologically material content;
5. preserve historical evidence without silently promoting superseded or branch-local claims.

This is a history/authority audit, not a claim that every source-code line in every branch has received a full code-quality review.

## 3. Branch-wide findings that materially change the project reconstruction

### 3.1 T0 is separate from Foundation Target Discovery, but it was not meant to be methodologically isolated

The strongest cross-lane evidence recovered from the T0 branch family is `docs/agent/JEPA_DATASET_FIRST_FRAMEWORK_MASTER_LIST_20260909.md` on `review/t0-r5-dataset-first-framework-20260909`. It states:

- `The dataset is the authority.`
- synthetic fixtures are for fail-closed/regression mechanics, not production evidence;
- the intended authority DAG runs from frozen source assets through B2/raw-source/technical/demographic/estimability/eligible-donor authorities and then to the `Teacher/student framework`;
- teacher/student production claims must not depend on unmaterialized T0 authorities.

The companion `TEACHER_STUDENT_FRAMEWORK_HOLD_UNTIL_T0_REPLAY_20260909.md` explicitly says teacher/student production should wait for replayed real-dataset T0 authorities and that a production teacher/student run must consume explicit authority roots and fail closed when they are missing.

Therefore the intended relation is not `T0 == Target Discovery`; it is:

`T0 as a separate real-data/method proving ground -> transferable dataset-first, provenance, estimability, firewall, and fail-closed lessons -> Foundation Target Discovery / Teacher-Student / V5`.

### 3.2 Historical T1 mechanics failure was explicitly written as a future-framework design guide

`docs/agent/T1_FAILURE_FINDINGS_AND_FRAMEWORK_DESIGN_GUIDE.md`, preserved on the T0 lineage, says the reason to preserve the 128/8 failure analysis is what it teaches future frameworks. The transferable rule is that missing/nonfinite checks are insufficient: exact-zero gradients can coexist with plausible loss reduction. It freezes a per-tensor/per-role pre-optimizer gate and explicitly warns that aggregate norms/global checks/loss curves cannot substitute.

This supports the broader anti-cheat design philosophy: a seemingly successful scalar objective is never sufficient evidence that the intended biological route is learning.

### 3.3 Target Discovery -> V5 integration was explicit and prospective

`planning/v5-pretraining-qualification-20260909` contains `TARGET_DISCOVERY_TO_V5_INTEGRATION_CONTRACT_V1.json`, which freezes the intended scientific family as scale-free anchored triplet ordering in direct 160-D cell-state cosine geometry. It records:

- TD57B global recurrence PASS;
- TD59 mesoscale pilot PASS;
- TD57C nearest-third failed closed;
- TD60 waiting for a lawful full-reader learned teacher;
- relational training initially inactive;
- activation requires a lawful exposure-defined teacher checkpoint, TD60 PASS, partial-evidence relational predictability PASS, frozen finite triplet budget, frozen common-core/native-support view policy, and independent relational-integration review.

This is direct historical evidence for a real Target Discovery -> Teacher/Student V5 bridge independent of T0 target identity.

### 3.4 TD60 biological time was prospectively repaired away from historical mechanics u40

`planning/teacher-student-v5-dataset-schedule-20260909` contains `TD60_EXPOSURE_CHECKPOINT_PROSPECTIVE_AMENDMENT_CANDIDATE_V1.json`. It says historical u40 is a mechanics update label from the 3,292-cell fixture and cannot define biological learning time for the 4,553,407-cell full-reader successor. The candidate milestone is one reader-fit-population-equivalent EMA teacher: 4,553,407 base presentations, without outcome-selected checkpointing. TD60 scientific geometry remains unchanged.

### 3.5 V5 branches contain direct anti-shortcut attacks against the Target Discovery objects

`planning/v5-full-population-cheat-proofing-20260909` contains direct Target Discovery measurement-shortcut attack artifacts, plus same-cell intervention, QC, dimension, dependency, representation-firewall, rejection-power and FULL104 substrate work. This is another concrete bridge: V5 anti-cheat design is not generic mechanics only; it explicitly attacks whether the Target Discovery relational objects can be explained or gamed by measurement/support structure.

## 4. Live branch inventory and classification

The inventory contained 40 pre-existing live branches. During this audit two audit-only refs were accidentally created by the reviewing session (`tmp-audit-test` and `governance/project-lineage-reconstruction-20260911-audit`); both point to an already existing governance commit and contain no unique commits. They are safe-to-delete ref noise and are not part of project history.

### 4.1 Current governance / handoff branches

| Branch | Observed head | Relation / classification | Historical use |
|---|---|---|---|
| `main` | `ba3f2a1200d0bbaf4b9ee0d7d16ddc17341d779f` | canonical current base | current governance, but contains Sep-11 T0/Target-Discovery label drift corrected by PR #16 |
| `governance/project-lineage-reconstruction-20260911` | evolving; pre-audit head `6054d105...` | current governance repair branch | lineage reconstruction, T0-method feedback, legacy corroboration, this branch audit |
| `governance/integrated-target-discovery-v5-handoff-20260911` | `dac11696...` | diverged; unique integration-governance history | valid integrated-review intent; source of later label conflation |
| `handoff/jepa-new-chat-20260910-t0-v21-v5` | `0dc40fae...` | behind main, ahead 0 | fully ancestral historical handoff |
| `handoff/jepa-new-chat-20260911-asap-repair-status` | `5ee85fc8...` | deeply diverged historical evidence | large T0/V21 evidence corpus, T1 framework guide, actual discovery/confirmation artifacts |
| `handoff/jepa-new-chat-20260911-post-v21-repair-current` | `a47e9a16...` | small unique delta over main | post-V21 repair handoff context |
| `handoff/jepa-new-chat-r2-20260908` | `2f7aeaf0...` | behind main, ahead 0 | fully ancestral; corroborates Sep-8 consolidation |
| `handoff/jepa-t0-v2-claude-ready-20260911` | `f727a820...` | deeply diverged historical evidence | V21/T0 repair state, Claude work order, environment/FULL104 runbook |

### 4.2 V5 / Teacher-Student / Target-Discovery integration branches

| Branch | Observed head | Classification | Unique value |
|---|---|---|---|
| `fix/v5-schedule-metadata-hash-revalidation-20260910` | `bede5a1b...` | deeply diverged V5 lineage | full-pop/schedule/metadata revalidation history |
| `planning/teacher-student-v5-dataset-schedule-20260909` | `78981dcb...` | divergent scientific-schedule design | TD60 exposure amendment, support-family policy, finite relational sampling, exposure clock |
| `planning/teacher-student-v5-gpu-rng-mechanics-20260908` | `19671b50...` | small divergent mechanics delta | keyed GPU Philox/RNG candidate |
| `planning/v5-full-population-cheat-proofing-20260909` | `1de20b1c222c7fb27fcef5ec1a4b798d5b26a534` | major divergent V5 production/anti-cheat lane | FULL104 binder, representation firewall, proposal/packing/restart, TD measurement-shortcut attacks, same-cell/QC/rejection-power work |
| `planning/v5-preexecution-hardening-20260909` | `782f2c52...` | behind main, ahead 0 | fully ancestral; no unique live delta |
| `planning/v5-pretraining-qualification-20260909` | `ae1709e2...` | divergent qualification design | explicit `TARGET_DISCOVERY_TO_V5_INTEGRATION_CONTRACT_V1`, real shortcut atlas, anti-cheat qualification runtime, atomic checkpoint/preexecution contracts |
| `repair/v5-executable-power-authority-20260911` | `52fca8ab...` | divergent repair successor | executable rejection-power authority, qualified optimizer/runtime/teacher-target guards |
| `repair/v5-qualified-target-guard-20260911` | `da8bd7df...` | divergent repair predecessor/sibling | qualified-target guard lineage |
| `review/integrated-target-v5-repairs-20260911` | `01192bbe...` | divergent external-review/governance | integrated repair review, also preserves F1/QID lineage context |
| `review/integrated-target-v5-repairs-code-20260911` | `2ccf942e...` | divergent review tip | one reviewed code tip |
| `review/integrated-target-v5-repairs-exec-20260911` | `2ccf942e...` | duplicate tip | no unique delta beyond `...-code` |
| `review/integrated-target-v5-repairs-finalwork-20260911` | `2ccf942e...` | duplicate tip | no unique delta beyond `...-code` |
| `review/integrated-target-v5-repairs-work-20260911` | `2ccf942e...` | duplicate tip | no unique delta beyond `...-code` |

### 4.3 T0 R4/R5 dataset-first review lineage

| Branch | Observed head | Classification | Unique value |
|---|---|---|---|
| `review/t0-r4-dataset-bound-hardening-20260909` | `fedad5ed...` | divergent historical review | technical completeness, estimability, age/sex, IMMUNE fraction, row/count hardening |
| `review/t0-r4-dataset-bound-inputs-20260908` | `68d6206e...` | divergent historical review | dataset-bound inputs and exact dataset-binding red tests |
| `review/t0-r4-independent-reds-20260909` | `f7d8dfb5...` | divergent review evidence | independent red suite and R4 STOP evidence |
| `review/t0-r4-independent-review-20260909` | `37da1b61...` | divergent review evidence | independent-review workflow and red suite |
| `review/t0-r5-dataset-chain-hardening-20260909` | `1f4b47db...` | divergent successor | stronger raw-source/technical/estimability chain |
| `review/t0-r5-dataset-first-framework-20260909` | `5038642c...` | **high-value divergent methodology branch** | dataset-first framework master list; T0->teacher/student authority DAG; hold-until-real-replay rule |
| `review/t0-r5-external-hardening-20260909` | `61797f35...` | divergent external-hardening branch | independent acceptance workflow and hardening |

### 4.4 T0 V20/V21 authority, replay and restoration lineage

All of these descend from an older T0 merge base and are therefore deeply divergent from current `main`. Their existence is historical evidence; their branch-local files are not automatically current authority.

| Branch | Observed head | Classification / role |
|---|---|---|
| `t0/v20-pathology-blind-materialization-20260908` | `d5d67e21398da92e39095afd864b4fb9ebe3da02` | immutable V20 historical authority and evidence corpus |
| `t0/v21-prospective-design-20260910` | historically/currently cited `11e76d36ace556ac48cdd2992995e63c1e35df18` | V21 prospective design draft lineage; not frozen/execution authority |
| `review/t0-v20-replay-equivalence-20260910` | `3b5933f6...` | V20 replay-equivalence/sensitivity/tail-probe history |
| `review/t0-v21-successor-20260911` | `3a8c8e3e...` | V21 successor implementation candidate history |
| `review/t0-v21-integrated-candidate-20260911` | `c8a1947e...` | integrated V21 candidate with crossfit/null evidence |
| `repair/t0-v21-authority-hardening-20260911` | `9f98320f...` | authority-hardening intermediate; historically known truncated/bad candidate |
| `repair/t0-v21-authority-restoration-20260911` | `b27978af...` | restoration lineage |
| `review/t0-v21-integrated-restored-20260911` | `93abcf50...` | restored candidate/review lineage |
| `review/t0-v21-integrated-restored-v2-20260911` | `42efc55f...` | later restored-v2 candidate with CI restoration tests |
| `repair/t0-v21-integrated-authority-regression-20260911` | `9a861b41...` | integrated regression-repair lineage |
| `review/t0-v2-api-surface-portability-20260911` | `2797c4d715770c9481b53b75a8bd2cac5cfeda74` | portability repair; independently known clean exact-head candidate |

The V21 family contains many overlapping files because later branches inherit earlier T0/V20 evidence. Supersession must be determined by exact commit/review lineage, not by counting duplicate files across branches.

### 4.5 F1

| Branch | Observed head | Classification | Unique value |
|---|---|---|---|
| `fix/f1-review-closeout-20260911` | `06012a11...` | ahead of main; unique F1 closeout | F1 closeout CI/scripts/status only; not Foundation Target Discovery authority |

## 5. Cross-branch authority interpretation

### Foundation Target Discovery authority

Source of biological-object authority remains the historical Target Discovery TD lineage and its exact frozen/result artifacts, not T0 branch names or V21 estimator-selection machinery.

### T0 authority

V20 remains immutable historical T0 authority at `d5d67e...`. V21 branch family is prospective/repair history and, where later repaired, must be interpreted through the exact reviewed candidate and fail-closed effect-transport state. T0 is also an explicit methodological proving ground for dataset-first/provenance/gate/firewall design.

### Teacher/Student/V5 authority

V4 provides the original relational-object bridge. V5 branch family adds data-first support, scientific target/proposal, full-reader scheduling, anti-cheat qualification, FULL104 integration and protected execution guards. No V5 branch currently authorizes production training.

### Main-governance rule

`main` remains canonical for current project governance, but historical branch-local evidence must be consulted when `main` has compressed, renamed, or omitted an older scientific distinction. A later summary does not silently supersede exact earlier science without explicit supersession authority.

## 6. Branches that can eventually be cleaned without losing scientific history

Do **not** delete branches merely from this audit. First preserve exact heads/commits and ensure all unique history is reachable or intentionally archived.

Likely cleanup candidates after preservation/review include:

- fully ancestral handoff branches with `ahead=0`;
- four duplicate `2ccf942e...` integrated-review refs, keeping one named ref or exact commit record;
- superseded intermediate T0 restoration branches once the accepted reviewed exact head and all unique evidence are durably indexed;
- audit-only accidental refs `tmp-audit-test` and `governance/project-lineage-reconstruction-20260911-audit`.

Deeply divergent V20/V21/R4/R5/V5 branches should **not** be deleted merely because a newer summary exists. They contain unique scientific/methodological evidence not currently present on `main`.

## 7. Correct project graph after branch-wide review

```text
Foundation Target Discovery TD13-TD60
  -> qualified relational biological object/protocol
  -> explicit Target Discovery-to-V5 integration contract
  -> lawful exposure-defined learned teacher / TD60
  -> partial-evidence relational qualification
  -> V5 anti-shortcut/full-reader production qualification
  -> explicit training authority only after all gates close

T0 V18/V20/V21
  -> separate MTG broad-IMMUNE/AT8 biological-claim lane
  -> real-data dataset-first/provenance/estimability/power/firewall proving ground
  -> methodological feedback into Foundation Target Discovery and V5
  -X-> does not supply AT8/pathology or the T0 score as the JEPA biological target

Historical T1 mechanics failure
  -> per-tensor gradient/optimizer/EMA and anti-cheat lessons
  -> framework safeguards
```

## 8. Current execution boundary

This audit creates no new authority. The following remain unauthorized unless a separate exact authority says otherwise:

- V5 production training;
- production optimizer/checkpoint progression;
- TD60 decision-bearing execution;
- T0 S0-S4 execution while effect-transport authority remains open/disabled;
- opening fresh `reader_validation` or `reader_oracle` for design/tuning;
- pathology-guided Target Discovery/V5 tuning;
- treating the corrected TRAIN cache, 50k discovery archive, or synthetic fixtures as FULL104 production substrate.

**Training remains OFF.**
