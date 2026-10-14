# Successor-agent handoff — TD synthetic known-truth lane — 2026-10-13

Terminal: `TAKEOVER_READY__DO_NOT_REPEAT_HISTORICAL_AUDITS__NEXT_ACTION_PHASE1_BLINDED_TEST_OF_TEST_ONLY__CONTROLLER_TRUTH_REMAINS_SEALED`

## Mission

Take over the target-discovery synthetic known-truth qualification lane from the current cross-certified preflight boundary. Do not restart repository-wide historical auditing. The historical audits, failure lineage, immutable refs, custody hashes, repaired scripts and exact non-secret receipts needed to continue are already indexed on this branch and its companion audit branch.

## Read these first, in this order

1. `docs/agent/TD_SYNTHETIC_CROSSCERT_COMPLETE_TAKEOVER_20261013.md`
2. `docs/agent/TD_SYNTHETIC_HISTORICAL_NO_REPEAT_LEDGER_20261013.md`
3. `docs/agent/TD_SYNTHETIC_HISTORICAL_CUSTODY_AUDIT_20261013.md` on companion audit branch `audit/td-synthetic-historical-custody-20261013`
4. `docs/agent/CURRENT_LANE_GIT_OBJECT_INDEX_20261013.json`
5. `docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`
6. `docs/agent/HISTORICAL_BRANCH_INDEX_20261013.txt`
7. exact final non-secret receipts under `archive/td_synthetic_crosscert_20261013/final/`

Only after those files should you open an older branch/PR relevant to a specific unresolved question.

## Frozen science/runtime pair

TD execution/custody repair:

- PR #320
- branch `audit/td-relational-blind-custody-v3-20261013`
- exact commit `1f474a44a6baabc667dbfda726e0755426c732e7`

Synthetic sealed package:

- PR #321
- branch `synthetic/td-relational-test-package-v2-1-20261013`
- exact commit `15f519c00137d581e25232c16be52c2b9badd83e`

Do not substitute later commits merely because filenames are unchanged.

## Final cross-cert identities

- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- controller archive SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`
- raw controller-manifest file SHA-256: `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`
- controller semantic/hiding commitment: `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`
- controller realization receipt SHA-256: `531966f132f7d1127d7aff586eba5452d6650e115b840193082fef8db2feb255`
- compatibility/cross-cert receipt SHA-256: `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`
- terminal: `READY_TO_EXECUTE_BLIND_FIT`

The nine fit-view SHA-256 values and the complete fit-engine identity are in the exact archived compatibility receipt.

## What has been qualified already

Cross-certification established, without executing biological TD statistics:

- the pre-fit package authenticates;
- all nine raw SHA-named NPZs authenticate and load with `allow_pickle=False`;
- each challenge has the uniform opaque five-control structure;
- challenge/control semantics are absent from phase-1 fit custody;
- controller bytes are physically absent from phase 1;
- the exact TD fit-engine/science-code hashes are bound into custody;
- phase 2 must authenticate the exact frozen blind receipt and engine identity before controller truth can be opened;
- output paths cannot collide with protected fit custody;
- final raw controller-manifest file identity and semantic hiding commitment are distinct fields.

This is preflight/custody qualification, not biological PASS/FAIL.

## Exact next legitimate action

Run **phase 1 only** of the blinded synthetic TD test-of-test using the frozen pair above.

Required sequence:

1. authenticate exact pre-fit transport/package hashes;
2. use the V4 TD disk runner at exact TD commit `1f474a44...`;
3. place only pre-fit transport in the phase-1 custody environment;
4. execute the blinded-fit phase over all nine opaque challenges;
5. freeze the V4 blinded output/receipt and all required engine/code identities;
6. verify input files were not mutated and controller bytes were never introduced;
7. STOP;
8. independently audit the frozen blind receipt before any phase-2/controller action.

Do not run phase 2 automatically after phase 1 succeeds.

## What remains OFF

- controller truth opening before phase-1 receipt audit;
- real TD execution;
- real target selection/promotion;
- TD60;
- Stage4;
- JEPA/foundation training;
- use of synthetic planted effect size as a real-human numerical decision threshold.

## Historical work that should not be repeated by default

The no-repeat ledger contains the complete list. Especially do not repeat these simply for familiarity:

- Stage81A3 controlled biological synthetic mechanics audit;
- V79 Q00-Q11 observation/statistical world audit;
- PR #311 rare/multimodal/context/perturbation component audit;
- PR #315 unified synthetic V1 failure + V2 architectural correction;
- PR #313 real tournament/case-ledger/firewall audit;
- PR #316 relational successor self-audit;
- PR #320 controller-custody and science-code-binding repair audit;
- PR #321 V2.1 interface/blindness/cross-cert audit.

Reopen a historical audit only if underlying bytes changed, the scientific question changed, a concrete contradiction appears, or the historical audit explicitly left that exact issue unresolved.

## Governing scientific conclusions carried forward

- Build candidate-agnostic biology first; derive candidate-specific truth controller-side.
- Controller oracle is not the teacher.
- Teacher must construct state from lawful measured evidence; student receives less evidence.
- Measured zero != structurally unmeasured.
- Same-nucleus and separate-nucleus multimodal evidence have different semantics.
- Rare biology is a cross-cutting activity/frequency regime in one biological population, not a separate synthetic dataset.
- Relational targets concern ordering/geometry, not exact coordinates.
- Recoverability classes: deterministic/highly recoverable, stochastic/distributional, teacher-private, NOT_ESTIMABLE.
- Biological uncertainty and measurement uncertainty remain distinct.
- Specialist/regulatory blocks cannot rescue a failed foundation target.
- No aggregate portfolio score may rescue a component that failed its own mandatory gate.

## Known unresolved caveats

### 50K row identity

`FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` has 50,000 rows but only 25,000 unique `sample_row` values; both A and B halves use 0..24999. Any historical STAT1/module calibration using `sample_row` as a physical 0..49999 locator must be rechecked before it becomes hard authority.

### Real numerical thresholds

Synthetic known-truth can qualify implementation, direction/sign, null behavior, shortcut detection, support/estimability and NOT_ESTIMABLE handling. It cannot silently create real-human effect-size cutoffs.

### Morabito independence

Morabito/GSE174367 has prior exposure through coverage work. Never describe it as pristine unseen validation.

## Project/local data custody

`docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv` is authoritative for project-only files not safely copied to GitHub. It records filename, byte size, SHA-256, custody disposition and caveats.

Large binaries/checkpoints and controller-truth bytes are intentionally manifest-only. This is not missing documentation; it preserves size and blindness boundaries.

The attempted base64 convenience copy under `archive/project_custody/20261013/` is explicitly marked `NON_AUTHORITATIVE` because the connector blocked/interrupted completion. Ignore it for science. Use the custody manifest and immutable Git refs.

## Important historical refs

- historical target-discovery takeover: `handoff/target-discovery-complete-takeover-20261012-v2` @ `c2daa4e3912a430886e4588eb793f497be08cf8d`
- target-discovery takeover audit: `audit/target-discovery-takeover-20261011-v2` @ `73a2820bf6057d28937ad337d401b7ee51b5c5ab`
- V79 synthetic history: `audit/v79-synthetic-lane-history-20261012` @ `414cac96a6491855f06e3382c59fefbd63a9a547`
- V79 synthetic takeover: `handoff/v79-synthetic-lane-takeover-v2-20261012` @ `93ca7ffc689c86fb7fcd4f77e44a668af41b39c8`
- PR #311 rare components: `2b6d3439105e087acdab53a318c57bbb468eae26`
- PR #313 tournament executor: `206167a1eb86f1dec5f8285db56accbcd469bce9`
- PR #315 unified synthetic V2 architecture: `af03ef67d52651463944a6de3a08e101ad00e0ea`
- PR #316 preserved pre-repair relational head: `2397ab83d8ae9d0c762a8fd5f3919edc350d137f`
- PR #320 repaired TD execution/custody head: `1f474a44a6baabc667dbfda726e0755426c732e7`
- PR #321 current synthetic V2.1 head: `15f519c00137d581e25232c16be52c2b9badd83e`
- Stage81A3 biological synthetic precedent: `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

## Stop rule after takeover

Do not broaden scope after phase 1. The next controller decision should be based on an audit of the frozen blind receipt, not on informal inspection of biological-looking outputs.

Successor terminal:

`READ_HISTORY_INDEX_FIRST__RUN_PHASE1_BLIND_ONLY__FREEZE_RECEIPT__AUDIT_BEFORE_TRUTH_OPEN__NO_REAL_TD_OR_TRAINING_AUTHORITY`
