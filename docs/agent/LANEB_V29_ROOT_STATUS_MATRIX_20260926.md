# JEPA V29 Lane B — exact 33-root authority status matrix

Revision `258f84fa4b4df2ea2a421df5b2f66bcd6538689f` (branch `lane-b/v29-root-closure-20260926`).

**Bottom line: no root is fully closed. `fully_closed = 0`. No training authority is issued or issuable.**

## Ledger

| quantity | value |
|---|---|
| upstream roots | 32 |
| receipt roots | 33 |
| receipt adds | `preexecution_authority_sha256` |
| **fully closed** | **0** |
| blocking roots | 33 |
| own-schema validated candidates (required class) | 4 |
| roots with no committed artifact of the required class | 26 |
| raw-string cross-binding slots | 3 |
| raw slots byte-authenticated | 1 |
| closure equality assertions | 59 |

### Closure enforcement census

| enforcement | roots |
|---|---|
| `isinstance` enforced | 24 |
| duck-typed, **no class check at all** | 5 |
| raw string cross-binding constant | 3 |

## Substrate byte authentication

```
path   : D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv
bytes  : 2372002
sha256 : 66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
matches expected: True
known decoy    : e482d9da21232bdeb6b3f198f42b9fbcf1530ba1b3e86e104ffbb651ca9df808 (2380918 bytes, two history trees)
```

Reproduce:

```bash
sha256sum "D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
stat -c %s "D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
```

## Task 1 — substrate root downstream bindings, per consumer

The closure equality-checks the substrate against **6** consuming authorities, not four.

| # | consumer parameter | attribute the closure reads | class enforcement | committed artifact | carries `66f589e5…` | blocks |
|---|---|---|---|---|---|---|
| 1 | `representation` | `substrate_authority_sha256` | duck typed no class check | `docs/agent/V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json` | ARTIFACT_CARRIES_AUTHENTIC_SUBSTRATE | no |
| 2 | `support_estimability` | `full104_substrate_sha256` | duck typed no class check | `docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json` | ARTIFACT_CARRIES_AUTHENTIC_SUBSTRATE | no |
| 3 | `canonical_address_registry` | `full104_block_manifest_sha256` | isinstance enforced | `docs/agent/V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json` | CARRIES_AUTHENTIC_SUBSTRATE_VIA_DOCUMENT_ADAPTER | no |
| 4 | `outer_split` | `full104_substrate_sha256` | isinstance enforced | **none** | NO_COMMITTED_ARTIFACT | YES |
| 5 | `target_panel` | `full104_substrate_sha256` | isinstance enforced | **none** | NO_COMMITTED_ARTIFACT | YES |
| 6 | `masking_qualification_design` | `full104_substrate_sha256` | isinstance enforced | **none** | NO_COMMITTED_ARTIFACT | YES |

**Result: 3 of 6 consumers carry the authenticated substrate; 3 block. `substrate_root_closed = False`.**

## Task 2 — V3 masking artifacts against the V1-typed closure

### `masking_rng_replay_authority_sha256`

* closure requires `MaskingRngReplayAuthorityV1`; committed artifact is `MaskingRngReplayAuthorityV3`
* closure reads: `canonical_registry_authority_sha256`, `outer_split_authority_sha256`, `target_panel_authority_sha256`
* V3 supplies: **none**
* V3 missing: `canonical_registry_authority_sha256`, `outer_split_authority_sha256`, `target_panel_authority_sha256`
* V3 is field-superset of V1: False; V3 subclasses V1: False
* V3 artifact own-class validate: True; declared digest agrees: True
* **classification: SCIENTIFIC_DIVERGENCE**

  V3 does not expose 3 attribute(s) the closure compares: canonical_registry_authority_sha256, outer_split_authority_sha256, target_panel_authority_sha256. Even with the isinstance check removed the closure would raise. This is a design decision, not a type mismatch.

### `masking_qualification_parameters_authority_sha256`

* closure requires `MaskingQualificationParametersAuthorityV1`; committed artifact is `MaskingQualificationParametersAuthorityV3`
* closure reads: `primary_attacker_id`, `primary_score_id`
* V3 supplies: `primary_attacker_id`, `primary_score_id`
* V3 missing: none
* V3 is field-superset of V1: True; V3 subclasses V1: False
* V3 artifact own-class validate: True; declared digest agrees: True
* **classification: NOMINAL_TYPING_CONFLICT**

  V3 exposes every attribute the closure compares (primary_attacker_id, primary_score_id). The sole obstruction is the isinstance(MaskingQualificationParametersAuthorityV1) check.

## The 33 roots

| root | defining class | enforcement | expected schema | candidates | authentic digest | outcome | deps | blocking |
|---|---|---|---|---|---|---|---|---|
| `full104_substrate_sha256` | - | raw str cross binding constant | - | 0 | `66f589e56badb148...` | VALUE_AND_BYTES_AUTHENTICATED | 6 | YES |
| `representation_authority_sha256` | `PrimaryRepresentationAuthorityV1` | duck typed no class check | `V5_PRIMARY_REPRESENTATION_AUTHORITY_V1` | 1 | `92756711fde939e2...` | OWN_SCHEMA_VALIDATED_CANDIDATE | 5 | YES |
| `support_estimability_authority_sha256` | `SupportEstimabilityAuthorityV1` | duck typed no class check | `V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1` | 1 | `cab2cecdd5ff31c2...` | OWN_SCHEMA_VALIDATED_CANDIDATE | 8 | YES |
| `canonical_address_registry_authority_sha256` | `CanonicalAddressRegistryAuthorityV1` | isinstance enforced | `V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1` | 1 | `28b20a457c44ac86...` | OWN_SCHEMA_VALIDATED_CANDIDATE | 5 | YES |
| `base_training_estimand_sha256` | `BaseTrainingEstimandAuthorityV1` | duck typed no class check | `V5_BASE_TRAINING_ESTIMAND_AUTHORITY_V1` | 1 | `a766d42f9f8e37aa...` | OWN_SCHEMA_VALIDATED_CANDIDATE | 3 | YES |
| `target_address_provider_authority_sha256` | `CurrentTargetAddressProviderAuthorityV1` | isinstance enforced | `V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 2 | YES |
| `target_evidence_budget_authority_sha256` | `TargetEvidenceBudgetAuthorityV1` | isinstance enforced | `V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `precision_authority_sha256` | `QualificationPrecisionAuthorityV1` | isinstance enforced | `V5_QUALIFICATION_PRECISION_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 2 | YES |
| `outer_split_authority_sha256` | `OuterDonorSplitAuthorityV1` | isinstance enforced | `V5_OUTER_DONOR_SPLIT_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `target_panel_authority_sha256` | `TargetPanelAuthorityV1` | isinstance enforced | `V5_TARGET_PANEL_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `address_universe_ladder_authority_sha256` | `AddressUniverseLadderAuthorityV1` | isinstance enforced | `V5_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `masking_rng_replay_authority_sha256` | `MaskingRngReplayAuthorityV1` | isinstance enforced | `V5_MASKING_RNG_REPLAY_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `masking_qualification_design_authority_sha256` | `MaskingQualificationDesignAuthorityV1` | isinstance enforced | `V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `masking_qualification_parameters_authority_sha256` | `MaskingQualificationParametersAuthorityV1` | isinstance enforced | `V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `masking_qualification_run_contract_authority_sha256` | `MaskingQualificationRunContractV1` | isinstance enforced | `V5_MASKING_QUALIFICATION_RUN_CONTRACT_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `masking_qualification_execution_authority_sha256` | `MaskingQualificationExecutionAuthorityV2` | isinstance enforced | `V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `masking_authority_sha256` | `CurrentMaskingPolicyAuthorityV2` | isinstance enforced | `V5_CURRENT_MASKING_POLICY_AUTHORITY_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 4 | YES |
| `target_construction_authority_sha256` | `TargetConstructionAuthorityV1` | isinstance enforced | `V5_TARGET_CONSTRUCTION_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `remaining_rna_necessity_authority_sha256` | `RemainingRnaNecessityAuthorityV1` | isinstance enforced | `V5_REMAINING_RNA_NECESSITY_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `remaining_rna_execution_authority_sha256` | `RemainingRnaExecutionAuthorityV1` | isinstance enforced | `V5_REMAINING_RNA_EXECUTION_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `teacher_target_semantics_authority_sha256` | `TeacherTargetSemanticsAuthorityV2` | isinstance enforced | `V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 3 | YES |
| `schedule_authority_sha256` | - | raw str cross binding constant | - | 0 | `-` | UNBOUND__NO_COMMITTED_ARTIFACT_CARRIES_THE_KEY | 1 | YES |
| `ema_authority_sha256` | `EmaTimescaleAuthorityV2` | isinstance enforced | `V5_EMA_TIMESCALE_AUTHORITY_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `measurement_robustness_authority_sha256` | `MeasurementRobustnessAuthorityV2` | isinstance enforced | `V5_MEASUREMENT_ROBUSTNESS_AUTHORITY_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `target_identity_gate_authority_sha256` | `TargetIdentityShortcutGateAuthorityV1` | isinstance enforced | `V5_TARGET_IDENTITY_SHORTCUT_GATE_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `anti_cheat_authority_sha256` | `AntiCheatAuthorityBundleV2` | isinstance enforced | `V5_ANTI_CHEAT_AUTHORITY_BUNDLE_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `model_geometry_authority_sha256` | `ModelGeometryAuthorityV2` | isinstance enforced | `V5_MODEL_GEOMETRY_AUTHORITY_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `geometry_memorization_qualification_authority_sha256` | `GeometryMemorizationQualificationAuthorityV1` | isinstance enforced | `V5_GEOMETRY_MEMORIZATION_QUALIFICATION_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `protected_registry_authority_sha256` | `ProductionProtectedRegistryAuthorityV1` | duck typed no class check | `V5_PRODUCTION_PROTECTED_REGISTRY_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 2 | YES |
| `critical_test_authority_sha256` | `CriticalTestExecutionAuthorityV1` | duck typed no class check | `V5_CRITICAL_TEST_EXECUTION_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |
| `observation_gradient_firewall_authority_sha256` | - | raw str cross binding constant | - | 0 | `-` | UNBOUND__NO_COMMITTED_ARTIFACT_CARRIES_THE_KEY | 1 | YES |
| `runtime_source_authority_sha256` | `CurrentRuntimeSourceAuthorityV1` | isinstance enforced | `V5_CURRENT_RUNTIME_SOURCE_AUTHORITY_V1` | 0 | `-` | NO_COMMITTED_ARTIFACT | 0 | YES |
| `preexecution_authority_sha256` | `CurrentTrainerPreexecutionAuthorityV2` | receipt only  not a closure parameter | `V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V2` | 0 | `-` | NO_COMMITTED_ARTIFACT | 1 | YES |

## Per-root detail

### `full104_substrate_sha256`

* defining module: `-`
* defining class: `-` (NONE)
* closure parameter: `full104_substrate_sha256` — RAW_STR_CROSS_BINDING_CONSTANT
* expected artifact schema: `-`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=full104_substrate_sha256
  ```

* validation outcome: **VALUE_AND_BYTES_AUTHENTICATED**
* dependencies the closure enforces on this root:
  * `representation.substrate_authority_sha256` (line 195) — fails with: *representation substrate root mismatch*
  * `support_estimability.full104_substrate_sha256` (line 196) — fails with: *support substrate root mismatch*
  * `canonical_address_registry.full104_block_manifest_sha256` (line 202) — fails with: *registry FULL104 substrate root mismatch*
  * `outer_split.full104_substrate_sha256` (line 209) — fails with: *outer split FULL104 root mismatch*
  * `target_panel.full104_substrate_sha256` (line 210) — fails with: *target panel FULL104 root mismatch*
  * `masking_qualification_design.full104_substrate_sha256` (line 245) — fails with: *masking design FULL104 root mismatch*
* blocking: **True** — every consuming authority must exist and carry this same value; consumers are unqualified
* fully closed: **False**

### `representation_authority_sha256`

* defining module: `sea_ad_jepa.v5.primary_representation_authority_v1`
* defining class: `PrimaryRepresentationAuthorityV1` (INFERRED_BY_ROLE__NOT_ENFORCED)
* closure parameter: `representation` — DUCK_TYPED_NO_CLASS_CHECK
* expected artifact schema: `V5_PRIMARY_REPRESENTATION_AUTHORITY_V1`
* source path: `docs/agent/V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json`
  * source commit: `258f84fa4b4df2ea2a421df5b2f66bcd6538689f`
  * committed blob sha256: `92756711fde939e27abc982d6ab1a0bc0dab53fae209c0f5a3fba4fde86ef4b1`
  * own-schema validation: **PASS** (DIRECT_INSTANCE_SERIALIZATION)
  * authentic digest: `92756711fde939e27abc982d6ab1a0bc0dab53fae209c0f5a3fba4fde86ef4b1`
  * artifact bytes ARE its canonical digest: True
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=representation_authority_sha256
  ```

* validation outcome: **OWN_SCHEMA_VALIDATED_CANDIDATE**
* dependencies the closure enforces on this root:
  * `remaining_rna_necessity.representation_authority_sha256` (line 226) — fails with: *remaining-RNA representation root mismatch*
  * `teacher_target.representation_authority_sha256` (line 237) — fails with: *teacher representation root mismatch*
  * `masking_qualification_design.representation_authority_sha256` (line 246) — fails with: *masking design representation root mismatch*
  * `measurement_robustness.representation_authority_sha256` (line 303) — fails with: *measurement representation root mismatch*
  * `target_identity_gate.representation_authority_sha256` (line 309) — fails with: *identity gate representation root mismatch*
* blocking: **True** — own-schema validation only; parent-source bytes and the closure cross-bindings that name this root are not qualified
* fully closed: **False**

### `support_estimability_authority_sha256`

* defining module: `sea_ad_jepa.v5.support_estimability_authority_v1`
* defining class: `SupportEstimabilityAuthorityV1` (INFERRED_BY_ROLE__NOT_ENFORCED)
* closure parameter: `support_estimability` — DUCK_TYPED_NO_CLASS_CHECK
* expected artifact schema: `V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1`
* source path: `docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json`
  * source commit: `258f84fa4b4df2ea2a421df5b2f66bcd6538689f`
  * committed blob sha256: `cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08`
  * own-schema validation: **PASS** (DIRECT_INSTANCE_SERIALIZATION)
  * authentic digest: `cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08`
  * artifact bytes ARE its canonical digest: True
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=support_estimability_authority_sha256
  ```

* validation outcome: **OWN_SCHEMA_VALIDATED_CANDIDATE**
* dependencies the closure enforces on this root:
  * `base_training_estimand.support_estimability_authority_sha256` (line 203) — fails with: *estimand support root mismatch*
  * `target_evidence_budget.support_estimability_authority_sha256` (line 207) — fails with: *budget support root mismatch*
  * `precision.support_estimability_authority_sha256` (line 208) — fails with: *precision support root mismatch*
  * `target_panel.support_estimability_authority_sha256` (line 212) — fails with: *target panel support root mismatch*
  * `address_universe_ladder.support_estimability_authority_sha256` (line 214) — fails with: *address ladder support root mismatch*
  * `remaining_rna_necessity.support_estimability_authority_sha256` (line 227) — fails with: *remaining-RNA support root mismatch*
  * `teacher_target.support_estimability_authority_sha256` (line 238) — fails with: *teacher support root mismatch*
  * `masking_qualification_design.support_estimability_authority_sha256` (line 247) — fails with: *masking design support root mismatch*
* blocking: **True** — own-schema validation only; parent-source bytes and the closure cross-bindings that name this root are not qualified
* fully closed: **False**

### `canonical_address_registry_authority_sha256`

* defining module: `sea_ad_jepa.v5.canonical_address_registry_authority_v1`
* defining class: `CanonicalAddressRegistryAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `canonical_address_registry` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_V1`
* source path: `docs/agent/V5_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_20260916.json`
  * source commit: `258f84fa4b4df2ea2a421df5b2f66bcd6538689f`
  * committed blob sha256: `a621d33535fd7993459625a323a96560b9b911669c0bd4656b63a8af126a39e0`
  * own-schema validation: **PASS_VIA_ADAPTER** (EXTERNAL_DOCUMENT_ADAPTER)
  * authentic digest: `28b20a457c44ac864c375492c8875e865ed6fe6d2000338d5fd46d9557a25676`
  * artifact bytes ARE its canonical digest: False
  * adapter digest agrees with document: True
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=canonical_address_registry_authority_sha256
  ```

* validation outcome: **OWN_SCHEMA_VALIDATED_CANDIDATE**
* dependencies the closure enforces on this root:
  * `target_panel.canonical_registry_authority_sha256` (line 211) — fails with: *target panel registry root mismatch*
  * `address_universe_ladder.canonical_registry_authority_sha256` (line 213) — fails with: *address ladder registry root mismatch*
  * `masking_rng_replay.canonical_registry_authority_sha256` (line 215) — fails with: *masking RNG registry root mismatch*
  * `masking.canonical_registry_authority_sha256` (line 223) — fails with: *masking registry root mismatch*
  * `masking_qualification_design.canonical_registry_authority_sha256` (line 248) — fails with: *masking design registry root mismatch*
* blocking: **True** — own-schema validation only; parent-source bytes and the closure cross-bindings that name this root are not qualified
* fully closed: **False**

### `base_training_estimand_sha256`

* defining module: `sea_ad_jepa.v5.base_training_estimand_authority_v1`
* defining class: `BaseTrainingEstimandAuthorityV1` (INFERRED_BY_ROLE__NOT_ENFORCED)
* closure parameter: `base_training_estimand` — DUCK_TYPED_NO_CLASS_CHECK
* expected artifact schema: `V5_BASE_TRAINING_ESTIMAND_AUTHORITY_V1`
* source path: `docs/agent/V5_BASE_TRAINING_ESTIMAND_AUTHORITY_20260915.json`
  * source commit: `258f84fa4b4df2ea2a421df5b2f66bcd6538689f`
  * committed blob sha256: `a766d42f9f8e37aa63e6c694d6c65b30962e45568f41b1cde8199cbed118ce26`
  * own-schema validation: **PASS** (DIRECT_INSTANCE_SERIALIZATION)
  * authentic digest: `a766d42f9f8e37aa63e6c694d6c65b30962e45568f41b1cde8199cbed118ce26`
  * artifact bytes ARE its canonical digest: True
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=base_training_estimand_sha256
  ```

* validation outcome: **OWN_SCHEMA_VALIDATED_CANDIDATE**
* dependencies the closure enforces on this root:
  * `teacher_target.scientific_weight_authority_sha256` (line 240) — fails with: *teacher estimand root mismatch*
  * `ema.base_training_estimand_sha256` (line 300) — fails with: *EMA estimand root mismatch*
  * `target_identity_gate.base_training_estimand_sha256` (line 310) — fails with: *identity gate estimand root mismatch*
* blocking: **True** — own-schema validation only; parent-source bytes and the closure cross-bindings that name this root are not qualified
* fully closed: **False**

### `target_address_provider_authority_sha256`

* defining module: `sea_ad_jepa.v5.current_target_address_provider_authority_v1`
* defining class: `CurrentTargetAddressProviderAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `target_address` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=target_address_provider_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `remaining_rna_necessity.target_address_provider_authority_sha256` (line 228) — fails with: *remaining-RNA target-address root mismatch*
  * `teacher_target.target_address_query_authority_sha256` (line 239) — fails with: *teacher target-address root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `target_evidence_budget_authority_sha256`

* defining module: `sea_ad_jepa.v5.target_evidence_budget_authority_v1`
* defining class: `TargetEvidenceBudgetAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `target_evidence_budget` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=target_evidence_budget_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `precision_authority_sha256`

* defining module: `sea_ad_jepa.v5.precision_authority_v1`
* defining class: `QualificationPrecisionAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `precision` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_QUALIFICATION_PRECISION_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=precision_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `remaining_rna_necessity.precision_authority_sha256` (line 230) — fails with: *remaining-RNA precision root mismatch*
  * `measurement_robustness.precision_authority_sha256` (line 305) — fails with: *measurement precision root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_QUALIFICATION_PRECISION_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `outer_split_authority_sha256`

* defining module: `sea_ad_jepa.v5.outer_split_authority_v1`
* defining class: `OuterDonorSplitAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `outer_split` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_OUTER_DONOR_SPLIT_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=outer_split_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `masking_rng_replay.outer_split_authority_sha256` (line 216) — fails with: *masking RNG split root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_OUTER_DONOR_SPLIT_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `target_panel_authority_sha256`

* defining module: `sea_ad_jepa.v5.target_panel_authority_v1`
* defining class: `TargetPanelAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `target_panel` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_TARGET_PANEL_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=target_panel_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `masking_rng_replay.target_panel_authority_sha256` (line 217) — fails with: *masking RNG target-panel root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_TARGET_PANEL_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `address_universe_ladder_authority_sha256`

* defining module: `sea_ad_jepa.v5.address_universe_ladder_authority_v1`
* defining class: `AddressUniverseLadderAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `address_universe_ladder` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=address_universe_ladder_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_ADDRESS_UNIVERSE_LADDER_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `masking_rng_replay_authority_sha256`

* defining module: `sea_ad_jepa.v5.masking_rng_replay_authority_v1`
* defining class: `MaskingRngReplayAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `masking_rng_replay` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_MASKING_RNG_REPLAY_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* cross-version evidence: `MaskingRngReplayAuthorityV3` artifact(s) exist at `analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/MASKING_RNG_REPLAY_AUTHORITY_V3.json` — **not promoted to this root**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=masking_rng_replay_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_MASKING_RNG_REPLAY_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `masking_qualification_design_authority_sha256`

* defining module: `sea_ad_jepa.v5.masking_qualification_design_authority_v1`
* defining class: `MaskingQualificationDesignAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `masking_qualification_design` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=masking_qualification_design_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_MASKING_QUALIFICATION_DESIGN_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `masking_qualification_parameters_authority_sha256`

* defining module: `sea_ad_jepa.v5.masking_qualification_parameters_authority_v1`
* defining class: `MaskingQualificationParametersAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `masking_qualification_parameters` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* cross-version evidence: `MaskingQualificationParametersAuthorityV3` artifact(s) exist at `analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V3.json` — **not promoted to this root**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=masking_qualification_parameters_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `masking_qualification_run_contract_authority_sha256`

* defining module: `sea_ad_jepa.v5.masking_qualification_run_contract_v1`
* defining class: `MaskingQualificationRunContractV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `masking_qualification_run_contract` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_MASKING_QUALIFICATION_RUN_CONTRACT_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=masking_qualification_run_contract_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_MASKING_QUALIFICATION_RUN_CONTRACT_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `masking_qualification_execution_authority_sha256`

* defining module: `sea_ad_jepa.v5.masking_qualification_execution_authority_v2`
* defining class: `MaskingQualificationExecutionAuthorityV2` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `masking_qualification_execution` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=masking_qualification_execution_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `anti_cheat.masking_qualification_execution_authority_sha256` (line 314) — fails with: *anti-cheat masking execution root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_MASKING_QUALIFICATION_EXECUTION_AUTHORITY_V2; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `masking_authority_sha256`

* defining module: `sea_ad_jepa.v5.current_masking_policy_authority_v2`
* defining class: `CurrentMaskingPolicyAuthorityV2` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `masking` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_CURRENT_MASKING_POLICY_AUTHORITY_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=masking_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `remaining_rna_necessity.masking_authority_sha256` (line 229) — fails with: *remaining-RNA masking root mismatch*
  * `teacher_target.masking_authority_sha256` (line 241) — fails with: *teacher masking root mismatch*
  * `target_identity_gate.masking_authority_sha256` (line 311) — fails with: *identity gate masking root mismatch*
  * `anti_cheat.masking_authority_sha256` (line 313) — fails with: *anti-cheat masking root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_CURRENT_MASKING_POLICY_AUTHORITY_V2; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `target_construction_authority_sha256`

* defining module: `sea_ad_jepa.v5.target_construction_authority_v1`
* defining class: `TargetConstructionAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `target_construction` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_TARGET_CONSTRUCTION_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=target_construction_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_TARGET_CONSTRUCTION_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `remaining_rna_necessity_authority_sha256`

* defining module: `sea_ad_jepa.v5.remaining_rna_necessity_v1`
* defining class: `RemainingRnaNecessityAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `remaining_rna_necessity` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_REMAINING_RNA_NECESSITY_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=remaining_rna_necessity_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `teacher_target.remaining_rna_necessity_authority_sha256` (line 242) — fails with: *teacher remaining-RNA root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_REMAINING_RNA_NECESSITY_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `remaining_rna_execution_authority_sha256`

* defining module: `sea_ad_jepa.v5.remaining_rna_execution_authority_v1`
* defining class: `RemainingRnaExecutionAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `remaining_rna_execution` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_REMAINING_RNA_EXECUTION_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=remaining_rna_execution_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `anti_cheat.remaining_rna_execution_authority_sha256` (line 315) — fails with: *anti-cheat remaining-RNA execution root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_REMAINING_RNA_EXECUTION_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `teacher_target_semantics_authority_sha256`

* defining module: `sea_ad_jepa.v5.teacher_target_semantics_authority_v2`
* defining class: `TeacherTargetSemanticsAuthorityV2` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `teacher_target` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=teacher_target_semantics_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `masking_qualification_design.teacher_target_semantics_authority_sha256` (line 249) — fails with: *masking design teacher root mismatch*
  * `measurement_robustness.teacher_target_semantics_sha256` (line 304) — fails with: *measurement teacher root mismatch*
  * `target_identity_gate.teacher_target_semantics_sha256` (line 308) — fails with: *identity gate teacher root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V2; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `schedule_authority_sha256`

* defining module: `-`
* defining class: `-` (NONE)
* closure parameter: `schedule_authority_sha256` — RAW_STR_CROSS_BINDING_CONSTANT
* expected artifact schema: `-`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=schedule_authority_sha256
  ```

* validation outcome: **UNBOUND__NO_COMMITTED_ARTIFACT_CARRIES_THE_KEY**
* dependencies the closure enforces on this root:
  * `ema.schedule_authority_sha256` (line 301) — fails with: *EMA schedule root mismatch*
* blocking: **True** — third raw-string slot, omitted from the V29 matrix. Equality-checked against ema.schedule_authority_sha256 only.
* fully closed: **False**

### `ema_authority_sha256`

* defining module: `sea_ad_jepa.v5.ema_timescale_authority_v2`
* defining class: `EmaTimescaleAuthorityV2` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `ema` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_EMA_TIMESCALE_AUTHORITY_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=ema_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `teacher_target.ema_boundary_authority_sha256` (line 302) — fails with: *teacher EMA root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_EMA_TIMESCALE_AUTHORITY_V2; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `measurement_robustness_authority_sha256`

* defining module: `sea_ad_jepa.v5.measurement_robustness_authority_v2`
* defining class: `MeasurementRobustnessAuthorityV2` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `measurement_robustness` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_MEASUREMENT_ROBUSTNESS_AUTHORITY_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=measurement_robustness_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `anti_cheat.measurement_robustness_authority_sha256` (line 316) — fails with: *anti-cheat measurement root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_MEASUREMENT_ROBUSTNESS_AUTHORITY_V2; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `target_identity_gate_authority_sha256`

* defining module: `sea_ad_jepa.v5.target_identity_shortcut_gate_authority_v1`
* defining class: `TargetIdentityShortcutGateAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `target_identity_gate` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_TARGET_IDENTITY_SHORTCUT_GATE_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=target_identity_gate_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `anti_cheat.target_identity_gate_authority_sha256` (line 312) — fails with: *anti-cheat identity root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_TARGET_IDENTITY_SHORTCUT_GATE_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `anti_cheat_authority_sha256`

* defining module: `sea_ad_jepa.v5.anti_cheat_authority_bundle_v2`
* defining class: `AntiCheatAuthorityBundleV2` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `anti_cheat` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_ANTI_CHEAT_AUTHORITY_BUNDLE_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=anti_cheat_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_ANTI_CHEAT_AUTHORITY_BUNDLE_V2; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `model_geometry_authority_sha256`

* defining module: `sea_ad_jepa.v5.model_geometry_authority_v2`
* defining class: `ModelGeometryAuthorityV2` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `model_geometry` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_MODEL_GEOMETRY_AUTHORITY_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=model_geometry_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_MODEL_GEOMETRY_AUTHORITY_V2; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `geometry_memorization_qualification_authority_sha256`

* defining module: `sea_ad_jepa.v5.geometry_memorization_qualification_authority_v1`
* defining class: `GeometryMemorizationQualificationAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `geometry_memorization_qualification` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_GEOMETRY_MEMORIZATION_QUALIFICATION_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=geometry_memorization_qualification_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `model_geometry.memorization_qualification_authority_sha256` (line 326) — fails with: *geometry memorization root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_GEOMETRY_MEMORIZATION_QUALIFICATION_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `protected_registry_authority_sha256`

* defining module: `sea_ad_jepa.v5.production_protected_registry_authority_v1`
* defining class: `ProductionProtectedRegistryAuthorityV1` (INFERRED_BY_ROLE__NOT_ENFORCED)
* closure parameter: `protected_registry` — DUCK_TYPED_NO_CLASS_CHECK
* expected artifact schema: `V5_PRODUCTION_PROTECTED_REGISTRY_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=protected_registry_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `model_geometry.protected_registry_authority_sha256` (line 325) — fails with: *geometry protected-registry root mismatch*
  * `geometry_memorization_qualification.protected_registry_authority_sha256` (line 332) — fails with: *geometry memorization protected-registry root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_PRODUCTION_PROTECTED_REGISTRY_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `critical_test_authority_sha256`

* defining module: `sea_ad_jepa.v5.critical_test_execution_authority_v1`
* defining class: `CriticalTestExecutionAuthorityV1` (INFERRED_BY_ROLE__NOT_ENFORCED)
* closure parameter: `critical_test` — DUCK_TYPED_NO_CLASS_CHECK
* expected artifact schema: `V5_CRITICAL_TEST_EXECUTION_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=critical_test_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `anti_cheat.critical_test_authority_sha256` (line 318) — fails with: *anti-cheat critical-test root mismatch*
* blocking: **True** — no committed JSON at this revision carries schema V5_CRITICAL_TEST_EXECUTION_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `observation_gradient_firewall_authority_sha256`

* defining module: `-`
* defining class: `-` (NONE)
* closure parameter: `observation_gradient_firewall_authority_sha256` — RAW_STR_CROSS_BINDING_CONSTANT
* expected artifact schema: `-`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=observation_gradient_firewall_authority_sha256
  ```

* validation outcome: **UNBOUND__NO_COMMITTED_ARTIFACT_CARRIES_THE_KEY**
* dependencies the closure enforces on this root:
  * `anti_cheat.observation_gradient_firewall_authority_sha256` (line 317) — fails with: *anti-cheat observation firewall root mismatch*
* blocking: **True** — unbound on both sides: no committed artifact carries the key and its only consumer (anti_cheat) has no committed artifact.
* fully closed: **False**

### `runtime_source_authority_sha256`

* defining module: `sea_ad_jepa.v5.current_runtime_source_authority_v1`
* defining class: `CurrentRuntimeSourceAuthorityV1` (ISINSTANCE_ENFORCED_BY_CLOSURE)
* closure parameter: `runtime_source` — ISINSTANCE_ENFORCED
* expected artifact schema: `V5_CURRENT_RUNTIME_SOURCE_AUTHORITY_V1`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>   # root=runtime_source_authority_sha256
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root: none
* blocking: **True** — no committed JSON at this revision carries schema V5_CURRENT_RUNTIME_SOURCE_AUTHORITY_V1; absence within the searched scope is not proof of global absence
* fully closed: **False**

### `preexecution_authority_sha256`

* defining module: `sea_ad_jepa.v5.current_trainer_preexecution_contract_v2`
* defining class: `CurrentTrainerPreexecutionAuthorityV2` (TYPED_PARAMETER_OF_ISSUER)
* closure parameter: `None` — RECEIPT_ONLY__NOT_A_CLOSURE_PARAMETER
* expected artifact schema: `V5_CURRENT_TRAINER_PREEXECUTION_AUTHORITY_V2`
* source path: **no committed artifact of this schema**
* validator command:

  ```bash
  python scripts/agent/laneb_v29_root_status_matrix_v2.py HEAD <index.json> <out_dir>
  ```

* validation outcome: **NO_COMMITTED_ARTIFACT**
* dependencies the closure enforces on this root:
  * `issue_training_authority_v1.preexecution.canonical_digest()` (line None) — fails with: *receipt roots must equal closure roots plus preexecution digest*
* blocking: **True** — derived at issuance from the caller-supplied roots mapping; it is self-referential and adds no independent evidence
* fully closed: **False**

---

TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED · D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
