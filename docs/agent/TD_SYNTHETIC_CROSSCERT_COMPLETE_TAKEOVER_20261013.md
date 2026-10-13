# TD + synthetic cross-certification complete takeover — 2026-10-13

Status: `PREFLIGHT_CROSS_CERTIFIED__READY_TO_EXECUTE_BLIND_FIT__BIOLOGICAL_EXECUTION_NOT_YET_RUN`

This is the durable takeover document for the current target-discovery / synthetic known-truth lane. Read this before opening old chat history or launching any new audit. The purpose is to prevent duplicate historical work and to preserve every known authority boundary and error correction.

## 1. Start here: current frozen execution pair

The only pair cross-certified for the next step is:

- TD repair PR #320, branch `audit/td-relational-blind-custody-v3-20261013`, commit `1f474a44a6baabc667dbfda726e0755426c732e7`.
- Synthetic V2.1 PR #321, branch `synthetic/td-relational-test-package-v2-1-20261013`, commit `15f519c00137d581e25232c16be52c2b9badd83e`.

Final corrected package/custody identities:

- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- pre-fit tar.xz SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- controller tar.xz SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`
- raw controller-manifest file SHA-256: `87219ad5f2bc1c514c6771c52dbf0e2529645a7221aaafd0774a8d3e186d03f9`
- controller semantic/hiding commitment SHA-256: `a3d8ea34339aa06d995d498c2651d4dfd4e1058eec3640a7cd7ea1128efce293`
- controller realization receipt SHA-256: `531966f132f7d1127d7aff586eba5452d6650e115b840193082fef8db2feb255`
- final cross-certification receipt SHA-256: `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`
- terminal: `READY_TO_EXECUTE_BLIND_FIT`

The nine authenticated fit-view SHA-256 values are frozen in the archived `separated_transport_receipt.json` and `compatibility_certification_receipt.json` copied beside this document.

## 2. Current authority state

The cross-certification is a **preflight compatibility/custody result only**. It proves the exact synthetic pre-fit transport can be authenticated by the exact repaired TD runtime while controller bytes are absent from phase-1 custody.

Still OFF:

- biological TD test-of-test execution;
- controller truth opening/adjudication;
- real TD execution;
- target selection/promotion;
- TD60;
- Stage4;
- JEPA/foundation training.

No TD geometry was computed during cross-certification. No blinded biological fit has run.

## 3. Exact next legitimate action

A future independent agent may execute **phase 1 only** of the blinded synthetic TD test-of-test against the frozen pair above:

1. authenticate the exact pre-fit transport and package identity;
2. use the TD V4 two-phase runner at commit `1f474a44...`;
3. run the blinded-fit phase with no controller transport in custody;
4. freeze the resulting V4 blinded receipt, including its fit-engine identity;
5. stop;
6. audit that frozen blinded receipt before any controller transport is introduced.

Do **not** open controller truth in the same phase-1 environment. Do **not** run phase 2 just because phase 1 succeeds. Do **not** inspect biological answers before the receipt itself is audited.

## 4. Current TD runtime identity

The final receipt binds the executed TD science code by SHA-256. The authoritative values are in `compatibility_certification_receipt.json`; the core interface values are:

- `scripts/v5/td_test_qualification_package_v2.py`: `aeedae32ae4c6cde8741ea9bbeee5459915fac6b8e33ab4e2d9531675c2e130d`
- `scripts/v5/td_relational_successor_synthetic_adapter_v2.py`: `c76aff20dedc5768cf1a59af5dd96187a9e71e318f7abe5a201811b6a34e3e8e`
- `scripts/v5/td_relational_successor_disk_runner_v4.py`: `ae3f9a580ddb10173e5af349355d5affe8ac06fb91985fb0f4f21691b28c6903`
- `scripts/v5/td_relational_successor_qualification_runner_v3.py`: `b0cf3985ab03c4f7d5bc3bc1e58e2bc0bccbd8c45430342733c08c2e0cb59f08`

The receipt also binds the gate, observed executor, estimability, capability reducer, and the remaining fit-engine modules. Do not substitute a later file with the same filename unless a new prospective qualification explicitly rebinds it.

## 5. Current synthetic runtime identity

At synthetic commit `15f519c00137d581e25232c16be52c2b9badd83e`:

- generator: `scripts/v79/build_td_relational_synthetic_package_v2_1.py`
- legacy V2.1 transport finalizer: `scripts/v79/finalize_td_relational_synthetic_package_v2_1.py`
- corrected identity finalizer: `scripts/v79/finalize_td_relational_synthetic_package_v2_1_1.py`
- final cross-cert workflow: `.github/workflows/td-relational-synthetic-v2-1-cross-cert.yml`

Important: the original V2.1 finalizer returns a field named `controller_manifest_sha256` containing the **semantic commitment**, not the raw file hash. The corrected `v2_1_1` finalizer must be used for custody because it preserves both identities separately. This defect was found only during independent byte review after an earlier CI pass; that earlier certification is superseded.

## 6. Historical audits that must not be repeated by default

The following work is already historical evidence. Reopen only if a concrete contradiction, changed input, or changed scientific question requires it.

### Stage81A3 synthetic mechanics

Commit `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777` contains the historical biological synthetic mechanics in `src/sea_ad_jepa/v4/conditional_predictability.py` and the readout in `docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md`.

This already established the controlled-universe precedent: latent biology, noise-free expected molecular state, independent observation realizations, counterfactual interventions, and explicit separation between biological truth and measurement. It did **not** authorize real training or establish learned biology.

### Frozen V79 Q00-Q11 observation/statistical worlds

Audit history is preserved on `audit/v79-synthetic-lane-history-20261012` @ `414cac96a6491855f06e3382c59fefbd63a9a547`, with takeover lineage on `handoff/v79-synthetic-lane-takeover-v2-20261012` @ `93ca7ffc689c86fb7fcd4f77e44a668af41b39c8`.

Q00-Q11 are frozen observation/statistical qualification worlds. They are **not** the full biological synthetic universe. Do not regenerate or mutate them.

### Rare biology / multimodal synthetic components

PR #311 / `integration/rare-biology-v79-realdata-20261012` @ `2b6d3439105e087acdab53a318c57bbb468eae26` is reusable component evidence, not proof of a final unified synthetic substrate. Rare biology is a cross-cutting activity/frequency regime in the same biological population; never restore the earlier “separate rare world/lane” interpretation.

### Unified synthetic design self-audit

PR #315 / `science/unified-synthetic-td-rehearsal-20261012` @ `af03ef67d52651463944a6de3a08e101ad00e0ea` records the failed V1 design and corrected V2 architecture. Do not repeat the V1 mistake of planting C1/C2/C3/C5 candidate-shaped latent coordinates or conflating controller oracle with teacher evidence.

### Real tournament executor framework

PR #313 / `science/td-real-target-tournament-executor-20261012` @ `206167a1eb86f1dec5f8285db56accbcd469bce9` already established outcome-blind candidate dependencies, case ledger, field firewalls and mandatory falsifiers. Its historical blocker was executable real gate-specific estimands/decision rules; historical outcomes must never be used to invent thresholds.

### Relational successor and custody repair

PR #316 frozen prefreeze head: `2397ab83d8ae9d0c762a8fd5f3919edc350d137f`.
PR #320 repaired successor head: `1f474a44a6baabc667dbfda726e0755426c732e7`.

The custody review already found and repaired:

- controller truth present too early in a single-process design;
- insufficient hiding of the controller mapping;
- phase-2 receipt authentication gaps;
- output-path overlap with fit custody;
- blinded receipt not bound to exact science-code identity;
- final controller raw-file identity vs semantic-commitment label ambiguity.

Do not “simplify” the two-phase process back into one invocation.

## 7. Science conclusions that remain governing

- Synthetic biology must be candidate-agnostic first; candidate-specific truth is derived controller-side later.
- Controller oracle truth is never teacher input.
- Teacher constructs state from lawful measured evidence; student receives less evidence.
- Measured zero and structurally unmeasured are distinct.
- Same-nucleus and separate-nucleus multimodal evidence are distinct experimental semantics.
- Source/operator can affect acquisition/observation and correlate with biology through sampling, but cannot be allowed to directly define latent biology.
- Relational targets concern ordering/geometry, not exact coordinates.
- Recoverability classes remain deterministic/highly recoverable, stochastic/distributional, teacher-private, and NOT_ESTIMABLE.
- Biological uncertainty and measurement uncertainty must remain distinct.
- Synthetic planted effect size can qualify implementation/sign/falsifiers/estimability logic; it cannot automatically set real-human biological cutoffs.
- A specialist regulatory target cannot rescue a failed foundation target.
- No aggregate portfolio score may rescue a component that failed its own required gate.

## 8. Real-data / multimodal boundaries already established

- GSE214979: true same-nucleus RNA+ATAC; primary identifiability substrate in the existing plan.
- GSE174367 / Morabito: separate nuclei / donor-level relation; partially exposed historically, so it is not pristine unseen validation.
- GSE272082: secondary; pairing/barcode/microglia issues were unresolved historically.
- spatial evidence is corroborative and support-limited; do not silently promote it to causal truth.
- SCENIC/regulatory topology is candidate support, not causal truth.
- perturbation data can support/calibrate mechanism tests but do not automatically become target truth.

## 9. Local/project custody assets copied or indexed here

See `docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`.

Small text audits/results that were only present in this project environment are archived under `archive/project_custody/20261013/` on this handoff branch. Very large binary assets are **not falsely claimed as GitHub-resident**; their current exact byte sizes and SHA-256 values are in the manifest.

Important large custody assets include:

- 41K expression split archive parts plus the part checksum manifest;
- FOUNDATION calibration bundle;
- historical checkpoints;
- 50K `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`;
- expression/checkpoint NPZ/ZIP bundles;
- final and superseded GitHub Actions artifact wrappers.

### 50K sample-row caveat remains unresolved

The current `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` has 50,000 rows but only 25,000 unique `sample_row` values. Both `A_NATURAL_MIXTURE` and `B_COVERAGE_DISCOVERY` use 0..24,999. Any analysis that used `sample_row` as a physical 0..49,999 row locator must be rechecked using physical row identity. Do not silently treat older STAT1 calibration numbers as row-index-certified.

## 10. What a future agent should read, in order

1. This file.
2. `docs/agent/TD_SYNTHETIC_HISTORICAL_NO_REPEAT_LEDGER_20261013.md`.
3. `docs/agent/CURRENT_LANE_GIT_OBJECT_INDEX_20261013.json`.
4. `docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`.
5. archived final cross-cert receipts under `archive/td_synthetic_crosscert_20261013/final/`.
6. only then the historical branch/PR relevant to the specific question.

This ordering is deliberate. Do not begin with a repository-wide re-audit merely because the lane has a long history.

## 11. Takeover terminal

`TAKEOVER_READY__HISTORICAL_AUDITS_INDEXED__FINAL_CROSSCERT_FROZEN__NEXT_ACTION_PHASE1_BLINDED_FIT_ONLY__CONTROLLER_REMAINS_SEALED`
