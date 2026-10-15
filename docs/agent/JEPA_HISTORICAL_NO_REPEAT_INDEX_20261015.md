# JEPA historical no-repeat index — takeover custody

Date: 2026-10-15

Purpose: prevent successor agents from repeating settled historical audits, rerunning spent experiments, or silently promoting superseded evidence. New work is justified only when bytes changed, authority/scientific context changed, or a concrete uncovered defect exists.

## Current frozen authority

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Unified Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Unified Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Unified Task 3 candidate `851544e8dc2a3881193a4d5bbcf07933e1d61149` is REJECTED. Do not treat it as authority.
- Task 4 production implementation remains blocked.

Global stop state: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## No-repeat classification framework

Use one of:

- `ALREADY_AUDITED`
- `SUPERSEDED`
- `OPEN`
- `CHANGED_INPUT_REQUIRES_REQUALIFICATION`

Never silently reinterpret historical mechanics evidence as biological evidence.

## Population / support / ETL custody

PR #349 exact head `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7` established the authenticated population/support registry lineage. Registry SHA-256: `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`.

Recorded census: 6,351,753 rows; 149 donors; 42 observation operators; 3 sources; 2,028 donor×operator strata; 104 reader-fit / 22 reader-validation / 23 reader-oracle donors. Macha real-data audit counted 4,553,407 reader-fit nuclei and 1,400 reader-fit donor×operator groups.

Do not recompute the census/support registry unless inputs change or a concrete defect is demonstrated. Protected validation/oracle partitions cannot be used to rescue reader-fit estimability.

## Repaired Target Discovery units

Controlling repaired lineages already audited:

- G8 — PR #364
- G6 — PR #365
- geometry G9/S1/S2 — PR #366
- R1 — PR #367
- G2 — PR #368
- G7 — PR #362
- R4/C6/C4 — PR #358
- C4→C6 firewall — PR #351
- G12 — PR #360
- system battery — PR #369

PRs #375–#378 are superseded duplicate lineages. Do not revive them.

No repaired unit is promoted beyond its explicitly qualified stage merely because a system battery passed.

## Old production-synthetic Tasks 1–2

Exact reviewed implementation code head: `ff597faf2182522a320ec5322f8db9b67c9c6094`.

Macha checkpoint/docs descendant: `f53c13e6eed329651b1088775782fea399ba1bf6`. Do not confuse this docs descendant with code authority.

### Old Task 1

Classification: `ADAPT_AND_WRAP__DIRECT_REUSE_CANDIDATE_FOR_CANONICAL_PRIMITIVES`.

Primary module: `scripts/production_synthetic/canonical_v1.py`.

Known preserved semantics: None-only missingness; reject NaN/Inf; -0→0; `1.0 != 1`; bool != int; Unicode code-point map ordering; order-sensitive registry digest; order-invariant identity-keyed row-set digest; bytes rejected by semantic hashing; explicit text/JSON entry points.

This substrate was absorbed into frozen Unified Task 1. Do not rebuild it from scratch.

### Old Task 2

Classification: `ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE`.

Primary module: `scripts/production_synthetic/custody_v1.py`.

This maps mainly to future Unified Task 4 sealed-custody mechanics, NOT Unified Task 2.

The 13 repaired historical custody failures remain mandatory Task 4 regressions: incomplete can’t-get-easier accounting; superseded version still usable; debug nonce accepted for withheld commitment; easier withheld-family swap; unchanged successor reroll; reused family still secret; class-nonce reveal leakage; successor reversion to public family; method rename resets draw count; late exposure after fit freeze; realistic-secret scan failure; eligibility before own reveal; pathological ledger build/replay.

D1 remains a required repair before reuse: broad exception wrapping must not turn internal programming bugs into normal custody refusal.

E2 is prospectively interpreted non-circularly; no self-hashing fixed-point requirement.

## Downstream teacher/student mechanics already audited

Historical mechanics evidence already covers optimizer/gradient flow, teacher no-grad, optimizer-before-EMA ordering, no EMA on invalid updates, Adam moment behavior, checkpoint/restart mechanics, identity RNG, packing/scientific weights, FULL104 support/normalization mechanics, donor-primary target, p/q separation, visibility/context, masking, registry anti-carryover, semantic carryover and V5 inactive one-update mechanics.

Do not rerun these merely because a later biological target changes. Requalify only the changed input/interface.

Target-address identity shortcut remains scientifically open. Historical BlockPredictor carried a trainable queried-gene identity embedding. Later downstream qualification must preserve identity-only/shared/fixed/stop-grad/shuffle comparators.

## Observation-operator / representation conclusions already recorded

Treat technology as observation operator `O_t`, not donor/dataset identity. Allowed information has physical acquisition meaning (assay/chemistry/platform/vocabulary/depth/detected-gene/count-split noise). Disallow free donor IDs, arbitrary matrix IDs and unrestricted dataset embeddings.

Separate measurement OOD from biological novelty; preserve legitimate donor biology; use held-donor/matrix/dataset-family/technology transfer; audit subspace/axis stability with principal angles, canonical correlation, Procrustes alignment and eigengaps; distinguish evidence-response from measurement-depth uncertainty; prefer hierarchical dataset→donor→cell sampling before real training.

Historical note imported at `docs/agent/historical_imports/WSL_EXECUTION_ISSUE_AND_FOUNDATION_DESIGN_NOTES_20260824.txt`.

## FULL104 / dimension-authority historical work

Historical planning note imported at `docs/agent/historical_imports/STATUS_AND_REPAIR_PLAN_20260912.txt`.

Important historical conclusions: TRAIN-cache cannot substitute for FULL104 authority; artifacts must be hash-bound; physical FULL104 closure remains distinct from row-identity closure; D_shared uses the frozen selection law rather than equality to longest supported prefix; held-donor predictability is a required gate; D_private metrics descend from exact D_shared selection; D_obs is based on lawful observation descriptors; historical Monte-Carlo replicate counts are not authority absent a prospective precision rule.

Do not confuse this machinery with an actual current numeric dimension result or training authorization.

## Task 0–2 acceptance history

Task 0 was rejected by Macha at `db92f80d...` only for B5 after B1–B4 closure. B5 was repaired at `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3` and independently accepted. Task 0 is frozen there.

Unified Task 1 initial candidate `86fa996f...` was rejected for T1-B1–B5. Focused repair `799d2e235901dfad9ce3b305c767a1c989e362f6` was independently accepted and is frozen.

Unified Task 2 initial candidate `2c391137...` was rejected for T2-B1–B4. Focused repair `c7dfff1cee608e4a101855d42cf0af08491c2aaf` was independently accepted and is frozen.

Do not repeat these audits unless those exact frozen bytes or their authority context change.

## Task 3 current rejected state

Rejected candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`, PR #392.

Independent review head: `869ca777a498181c519ccfc04b8bf5db0f2888c7`.

Verdict: `REJECT_UNIFIED_TASK3` / `TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`.

Blocking findings:

- T3-B1: unit-scoped + `NO_TRAINING_AUTHORITY` record can reach `TRAINING_AUTHORIZED` because promotions do not apply frozen Task 1 authority validation.
- T3-B2: `KNOWN_TRUTH_QUALIFIED` and `HUMAN_EXECUTED` lack closed evidence gates.
- T3-B3: actor aliasing/free self-minted actor IDs defeat no-self-qualification.
- T3-B4: caller-owned verification cache is poisonable and survives resolver changes.
- T3-B5: revocation/history can be rebuilt or fabricated because history is not replayed from an anchored genesis.
- T3-B6: write-capable CI workflows rewrite Task 3 code/tests after pushes and can neutralize future RED tests.

Read exact Macha evidence on review head `869ca777...`:

- `docs/agent/MACHA_UNIFIED_TASK3_INDEPENDENT_REVIEW_851544E8_20261015.md`
- `results/target_discovery/unified_qualification_v1/MACHA_UNIFIED_TASK3_REVIEW_VERDICT_V1.json`
- `docs/agent/macha_task3_review_evidence_851544e8/task3_probe1.py`

Repair order is binding: disarm B6 workflows FIRST, then preserve Macha probes as RED tests, then repair B1–B5. Do not patch production logic before the RED failures are demonstrated.

## Task 4 controlling preparation

Controlling design: `docs/superpowers/specs/2026-10-15-unified-task4-sealed-challenge-custody-design.md`.

The design is prepared only. Task 4 production code, final challenge roots/nonces/worlds and RED execution branch remain blocked until exact Task 3 acceptance/freeze.

Key laws already settled: one QualificationCampaign genesis is the anti-reset anchor; complete finite realization set sealed before exposure; exposure spends information budget even on crash/abort; stale/revoked Task 3 authority blocks transitions; no generic scientific harder/easier oracle; harness owns exposure/finalization; output freezes before reveal; persistent externally anchored ledger; signing secret outside producer process; publication-surface secret scanning; custody result distinct from biological qualification.

## Local/private artifact custody

See `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_20261015.json` for exact SHA-256 and sizes of local-only expression, calibration, checkpoint and NPZ artifacts. Large/private binaries are not copied into Git. Verify bytes against the manifest before use.

## Permanent successor protocol

Every future agent must inherit this rule in every handoff:

1. assimilate existing audits before new work;
2. work iteratively: self-audit → RED → minimal repair → focused regression → inherited regression → renewed hostile audit;
3. continuously update PR #322 (durable audit/custody) and PR #323 (read-first takeover navigation);
4. preserve scripts, results, receipts, failures, exact identities and no-repeat classifications;
5. do not repeat settled work absent a changed input/authority context or a concrete new defect;
6. never promote mechanics evidence into biological authority;
7. protected validation/oracle values and real training remain blocked until explicit later gates.
