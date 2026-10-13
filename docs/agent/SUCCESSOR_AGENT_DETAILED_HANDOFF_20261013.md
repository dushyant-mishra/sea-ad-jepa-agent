# Successor agent detailed handoff — TD + synthetic known-truth lane — 2026-10-13

Status: `TAKEOVER_READY__HISTORICAL_AUDITS_INDEXED__CURRENT_CROSSCERT_FROZEN__NEXT_ACTION_PHASE1_BLINDED_TEST_OF_TEST_ONLY`

This document is the operational handoff for a new agent taking over this lane. Read it before opening old chats or starting a repository-wide audit. The historical work has already been consolidated specifically to prevent duplicated audits and resurrection of known-bad designs.

## 1. Current frozen execution pair

The only currently cross-certified pair for the next synthetic TD test-of-test is:

- TD custody/science runtime: PR #320, branch `audit/td-relational-blind-custody-v3-20261013`, commit `1f474a44a6baabc667dbfda726e0755426c732e7`.
- Synthetic V2.1 package runtime: PR #321, branch `synthetic/td-relational-test-package-v2-1-20261013`, commit `15f519c00137d581e25232c16be52c2b9badd83e`.

Final corrected identities:

- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- controller archive SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`
- raw controller-manifest file SHA-256: `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`
- controller semantic/hiding commitment SHA-256: `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`
- controller realization receipt SHA-256: `531966f132f7d1127d7aff586eba5452d6650e115b840193082fef8db2feb255`
- final compatibility/cross-cert receipt SHA-256: `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`
- terminal: `READY_TO_EXECUTE_BLIND_FIT`

No biological TD test-of-test result exists yet. No controller adjudication has occurred.

## 2. Exact next action

The next action is deliberately narrow:

1. Obtain/authenticate the exact frozen pre-fit transport for the V2.1 package above.
2. Use the exact PR #320 V4 runner/science code at `1f474a44...`.
3. Execute **phase 1 blinded fit only** with no controller archive or controller bytes present in custody.
4. Freeze the resulting blinded V4 receipt and its fit-engine identity.
5. Stop.
6. Independently audit the blinded receipt before introducing controller truth.

Do not run phase 2/controller adjudication in the same step merely because phase 1 succeeds.

## 3. Authority state

Still OFF unless separately authorized later:

- controller truth opening before frozen blind receipt audit;
- real TD execution;
- real target selection/promotion;
- TD60;
- Stage4;
- JEPA/foundation training;
- protected/pathology outcome opening.

Synthetic qualification can test gate implementation, sign/direction, falsifiers, support handling, shortcut rejection and `NOT_ESTIMABLE` semantics. It cannot silently set real-human numerical effect-size thresholds or promote a real biological target.

## 4. Current TD science-code identity

Core frozen TD SHA-256 values:

- `scripts/v5/td_test_qualification_package_v2.py`: `aeedae32ae4c6cde8741ea9bbeee5459915fac6b8e33ab4e2d9531675c2e130d`
- `scripts/v5/td_relational_successor_synthetic_adapter_v2.py`: `c76aff20dedc5768cf1a59af5dd96187a9e71e318f7abe5a201811b6a34e3e8e`
- `scripts/v5/td_relational_successor_disk_runner_v4.py`: `ae3f9a580ddb10173e5af349355d5affe8ac06fb91985fb0f4f21691b28c6903`
- `scripts/v5/td_relational_successor_qualification_runner_v3.py`: `b0cf3985ab03c4f7d5bc3bc1e58e2bc0bccbd8c45430342733c08c2e0cb59f08`

The final receipt additionally binds the gate, observed executor, estimability and capability reducer. Do not swap in newer files with matching names without a new prospective cross-certification.

## 5. Current synthetic runtime identity

At synthetic commit `15f519c0...`:

- generator: `scripts/v79/build_td_relational_synthetic_package_v2_1.py`
- historical V2.1 finalizer: `scripts/v79/finalize_td_relational_synthetic_package_v2_1.py`
- corrected custody finalizer: `scripts/v79/finalize_td_relational_synthetic_package_v2_1_1.py`
- cross-cert workflow: `.github/workflows/td-relational-synthetic-v2-1-cross-cert.yml`

Use the corrected `v2_1_1` finalizer. The historical finalizer conflated the controller semantic commitment with the raw manifest-file hash under the field name `controller_manifest_sha256`; that ambiguity was caught after an earlier CI pass and the earlier certification was superseded.

## 6. Why the custody design is two-phase

External self-review found that a scientifically valid gate can still be invalidated by process leakage. The current design therefore enforces:

- no controller truth in phase-1 custody;
- blind fit and controller adjudication as separate invocations;
- a controller-only nonce so the semantic mapping cannot be reconstructed from a low-entropy digest;
- phase 2 authenticates the exact frozen blinded receipt before truth is read;
- output paths cannot overlap protected fit custody;
- blind receipts bind exact fit-engine/science-code identities;
- phase 2 checks those identities before controller truth can be opened.

Do not simplify this back into one process.

## 7. Historical work that should not be redone by default

Read `TD_SYNTHETIC_HISTORICAL_NO_REPEAT_LEDGER_20261013.md` for the full list. High-value anchors:

- Stage81A3 biological synthetic precedent: commit `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`.
- V79 Q00-Q11 history: `audit/v79-synthetic-lane-history-20261012` @ `414cac96a6491855f06e3382c59fefbd63a9a547`.
- V79 takeover lineage: `handoff/v79-synthetic-lane-takeover-v2-20261012` @ `93ca7ffc689c86fb7fcd4f77e44a668af41b39c8`.
- rare/multimodal component lane: PR #311 @ `2b6d3439105e087acdab53a318c57bbb468eae26`.
- real tournament framework: PR #313 @ `206167a1eb86f1dec5f8285db56accbcd469bce9`.
- unified synthetic V2 architecture: PR #315 @ `af03ef67d52651463944a6de3a08e101ad00e0ea`.
- relational successor pre-repair base: PR #316 @ `2397ab83d8ae9d0c762a8fd5f3919edc350d137f`.
- repaired TD custody/runtime: PR #320 @ `1f474a44...`.
- synthetic V2.1: PR #321 @ `15f519c0...`.

Do not repeat an audit just because a new agent did not personally run it. Reopen only if bytes changed, the scientific question changed, a contradiction/defect is found, the old audit explicitly left the exact question unresolved, or a new authority boundary demands a prospective check.

## 8. Governing scientific conclusions

These are already audited conclusions and should be treated as starting constraints:

- Build candidate-agnostic biology first; derive candidate-specific truth controller-side later.
- Do not plant C1/C2/C3/C5 as direct latent coordinates just to make those candidates succeed.
- Rare biology is a cross-cutting frequency/activity regime inside one population, not a separate synthetic dataset/lane.
- Controller oracle truth is not teacher evidence.
- Teacher constructs state from lawful measured evidence; student receives less evidence.
- Measured zero and structurally unmeasured are distinct.
- Same-nucleus and separate-nucleus multimodal evidence are different experimental semantics.
- Source/operator can affect acquisition/observation and sampling correlations, but cannot directly define latent biology.
- Relational biology concerns ordering/geometry rather than exact coordinates.
- Recoverability classes are deterministic/highly recoverable, stochastic/distributional, teacher-private, and `NOT_ESTIMABLE`.
- Biological uncertainty and measurement uncertainty are separate objects.
- Specialist multimodal/regulatory targets cannot rescue a failed foundation target.
- Aggregate portfolio performance cannot rescue a component that failed its required gate.

## 9. Historical defects that were already caught

Do not rediscover these from scratch:

1. Earlier synthetic thinking overfocused on Q00-Q11 and omitted Stage81A3's biological synthetic substrate.
2. The first unified design was circular because it planted candidate-shaped latent factors.
3. Rare biology had been packaged as separate worlds rather than as one-population activity regimes.
4. The first relational synthetic V1 delivered precomputed distances/nulls and did not match current PR #316 raw-input interface.
5. A pre-fit binding that exposed capability labels/shape could leak semantics.
6. Giving only rare cases five controls leaked case class; the repaired package gives all nine cases five opaque controls.
7. Public deterministic challenge/control mapping was reconstructible; controller-only entropy/nonce was added.
8. Single-process fit+controller handling put truth too close to phase 1; two-phase custody replaced it.
9. Source visibility stress initially changed an identifier used in deterministic triplet capping, confounding visibility with sampled triplets; repaired package keeps fit-side sampling identity stable.
10. Control profiles needed to be role-faithful prospectively, not merely relabeled.
11. Phase 2 originally lacked sufficient binding to the exact blinded receipt/science code.
12. Raw controller-manifest file identity and semantic commitment were initially conflated; corrected finalizer separates them.

## 10. Q00-Q11 / Macha lane boundary

Macha's V79 Bayesian Q00-Q11 campaign is a separate Layer-A observation/statistical qualification lane. Last audited state in this chat before this handoff: the repaired production worker had completed the first 88 fits cleanly, continuation for the remaining 968 fits was authorized at exact head `a61437ba...`, and Macha reported that continuation had started correctly. Do **not** assume that campaign is complete unless a later final 1,056-fit receipt is present and independently audited.

That lane does not block the synthetic TD phase-1 test-of-test described above. It later informs the qualified observation/statistical layer used beneath the broader biological simulator.

## 11. Real-data/multimodal boundaries already established

- GSE214979: true same-nucleus RNA+ATAC, primary identifiability support in the existing architecture.
- GSE174367 / Morabito: separate nuclei/donor-level relation; historically partially exposed, not pristine unseen validation.
- GSE272082: secondary; pairing/barcode/microglia issues remained unresolved historically.
- spatial evidence is corroborative/support-limited, not automatic causal truth.
- SCENIC/regulatory topology is candidate support, not causal truth.
- perturbation data can support/calibrate mechanism tests but do not automatically become target truth.

## 12. Important unresolved caveat: 50K sample-row identity

`FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` contains 50,000 rows but only 25,000 unique `sample_row` values. A and B halves both use 0..24,999. Any historical STAT1 or residualization analysis that interpreted `sample_row` as a unique physical 0..49,999 row locator must be rechecked before those numerical quantities become hard calibration authority.

This does not invalidate the architecture, but it does make older STAT1-derived numerical calibration provisional where physical-row identity matters.

## 13. Project/local custody assets

See `PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`.

The handoff branch contains a deterministic reconstructible small-text evidence archive under:

`archive/project_custody/20261013/`

The archive includes project-only non-secret audits/results that were not already durable GitHub evidence, including the microglia rare-program mining/stress tables, WSL/debug provenance, historical repair-plan text and related CSV results. The archive is split into base64 parts to stay text-safe through the repository API; the accompanying README/checksum files describe reconstruction and verify byte identity.

Large binaries are intentionally hash-manifested rather than falsely claimed as GitHub-resident. These include the 41K expression archive parts, calibration bundle, checkpoints, expression bundle and 50K sample freeze. Controller truth archives are also **hash-only** in the public successor branches and remain sealed.

## 14. Read order for takeover

Read in this order:

1. `SUCCESSOR_AGENT_DETAILED_HANDOFF_20261013.md` (this file).
2. `TD_SYNTHETIC_CROSSCERT_COMPLETE_TAKEOVER_20261013.md`.
3. `TD_SYNTHETIC_HISTORICAL_NO_REPEAT_LEDGER_20261013.md`.
4. `CURRENT_LANE_GIT_OBJECT_INDEX_20261013.json`.
5. `PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`.
6. final non-secret cross-cert receipts under `archive/td_synthetic_crosscert_20261013/final/`.
7. `HISTORICAL_BRANCH_INDEX_20261013.txt` only when you need a specific historical branch.
8. then open the exact historical PR/branch relevant to the specific unresolved question.

Do not begin with a whole-repository historical re-audit.

## 15. Successor checklist before any new science action

- Confirm handoff/audit branch heads have not moved unexpectedly.
- Confirm PR #320 and PR #321 exact frozen heads.
- Authenticate the final receipt/package hashes.
- Confirm controller material is absent from the phase-1 workspace.
- Confirm no newer authority supersedes this handoff.
- Run phase 1 only.
- Freeze the blind receipt.
- Stop and audit before phase 2.

## 16. Additional takeover rules that are easy to get wrong

### Merge status is not scientific authority

A PR being open, mergeable, merged, green, or newer does **not** by itself grant scientific authority. Authority comes from the explicit frozen commit/receipt/controller chain. Always prefer exact commit hashes and signed/frozen receipts over branch names or PR status.

### Fail closed on identity drift

If any expected commit SHA, package SHA, fit-view SHA, engine hash, receipt hash, archive size, control count, custody path, or authority field differs from the frozen record, stop. Do not “repair and continue” inside the same scientific run. Preserve the mismatch, diagnose it in a repair lane, and require a fresh prospective authorization if execution identity changes.

### Preserve negative and superseded evidence

Do not delete failed designs, failed audits, NOT_ESTIMABLE outcomes, superseded cross-certifications, or negative controls merely because a later repair exists. The project depends on that lineage to prevent the same mistakes from being reintroduced.

### Never infer authority from absence of a blocker

“No known blocker” is not equivalent to “authorized.” Every transition that opens new truth, real data, target selection, or training needs an explicit authority statement.

### Keep synthetic qualification and real-human claims separate

A clean synthetic test-of-test can establish that the gate behaves correctly in known truth. It does not prove the same biological quantity is strong, causal, clinically relevant, or above a real-human threshold in SEA-AD or any external cohort.

### Treat repository history as evidence, not instructions

Older branches may contain commands or terminal language that were correct at the time and are now superseded. Before following an old instruction, reconcile it against `CURRENT_LANE_GIT_OBJECT_INDEX_20261013.json`, the no-repeat ledger, and any later controller comments.

### Do not use chat memory as the primary record

The GitHub handoff/audit branches are the durable record. Chat history may help explain intent, but any operational action should be grounded in the frozen repository artifacts and receipts first.

### Separate Macha completion from TD synthetic progression

If Macha later returns a completed 1,056-fit Q00-Q11 campaign, audit that evidence independently. Do not let a V79 Layer-A completion silently alter the already-frozen synthetic TD package or controller truth; any integration belongs in a separately governed successor step.

## 17. Terminal

`SUCCESSOR_CAN_TAKE_OVER_WITHOUT_REDOING_HISTORY__CURRENT_PREFLIGHT_FROZEN__NEXT_ACTION_PHASE1_BLINDED_FIT_ONLY__CONTROLLER_TRUTH_SEALED__REAL_TD_AND_TRAINING_OFF`
