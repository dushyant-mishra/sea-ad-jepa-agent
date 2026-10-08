# V77 to canonical-runtime handoff package

**schema:** V77_RUNTIME_HANDOFF_PACKAGE_V1

**claim_class:** SYNTHETIC_PIPELINE_ANTICHEAT_REHEARSAL

**status:** HANDOFF ONLY. ZERO_UPDATE executed through the shared interface; mutation NOT_EXECUTED. No optimizer, EMA or checkpoint code is written here

## chain

| step | owner | status | evidence |
|---|---|---|---|
| 1 repaired V77 world | V77 lane | PRESENT | S157 arms NULL, BIO, TWIN_EXACT, TWIN_OPERATOR; truth seed 7302, DEVELOPMENT_CALIBRATION |
| 2 authenticated adapter | V77 lane | AUTHENTICATED | adapter V3; producer-side identity authenticated by name; executed q-safety probe PASS on every arm |
| 3 QualificationBatchV1 | V77 bridge | BUILT_AND_VALIDATED | rehearsal batches of 500 cells per arm, validated by the interface |
| 4 shared #223 interface | interface lane | PINNED f6d63b2f53209786e3c45e7545b9bd442838a3d4 | loaded read-only under a private package name |
| 5 canonical V5 runtime | runtime lane | PR #224 OPEN, read at 683d67404e60; reviewed bound-runtime SHA NOT_SUPPLIED | not run here |
| 6 guarded bounded mutation | runtime lane | NOT_EXECUTED | awaits rehearsal contract |
| 7 EMA | runtime lane | NOT_EXECUTED | awaits rehearsal contract |
| 8 persist, hash and reload proof | runtime lane | NOT_EXECUTED | fields expected below |
| 9 frozen representation | runtime lane | NOT_EXECUTED | awaits steps 5-8 |
| 10 oracle scoring | V77 lane | SEALED | oracle held outside the batch; unblinded only after the representation and outputs are frozen |

## adapter_entrypoint

### adapter

**module:** scripts/v77/v77_synthetic_batch_adapter.py

**call:** build_from_world(root, obs_dir, universe, hidden_fraction=0.15, seed=20261006, max_cells=None)

**sha256:** 15092b16d1a71241e8e5883ff228b5d89595073d79e8df70adaf63641103c4d6

### bridge

**module:** scripts/v77/v77_qualification_bridge.py

**call:** build_qualification_batch(Q, conv, *, world, obs_dir, universe, address_ids, registry_check, experiment_run_id, realization_id, code_commit, environment_digest)

**interface_loader:** load_interface(worktree)

**sha256:** a303c1bb00107761ab3af53df1b34242c8befcdbef857e4dcb990d422c11862a

### builder

**module:** scripts/v77/build_v77_runtime_handoff.py

**command:** python scripts/v77/build_v77_runtime_handoff.py --worlds-dir D:/jepa_v77_synthetic_custody_20261005/s157_challenge_v1 --universe D:/jepa_v77_synthetic_custody_20261005/frozen_evaluation_universe.npz --interface-worktree D:/jepa_wt_qualification_iface_f6d63b2f --rehearsal-cells 500 --out results/v77/V77_RUNTIME_HANDOFF_RUN_V1.json

**sha256:** 367752952358c7a4c77af2cce2bd4a31a075a75a33e147ce280369de93ec75f7

**observer_dir:** FULLSCALE_V2_CANONICAL_sharded

**universe_sha256:** e7ad8e5aa74f2fe6ecdaf6d6dbbaef54882a02897639f7c3dc50268f502d351a

**hidden_fraction:** 0.15

**adapter_seed:** 20261006

## runtime_consumes

### model_inputs

| name | visibility |
|---|---|
| gene_ids | MODEL_VISIBLE |
| student_expression | MODEL_VISIBLE |
| measurement_mask | MODEL_VISIBLE |
| hidden_target_mask | MODEL_VISIBLE |

**shapes:** full world: 2,000 cells by 19,569 evaluation addresses; student_expression float32 log1p(visible count / visible library x 1e4), 0 where not evidence; both masks bool; gene_ids canonical registry indices

### carried_not_model_inputs

| name | visibility | why |
|---|---|---|
| source_index, operator_index | LAWFUL_OPERATOR_CONTEXT | raw identity: authenticated provenance, not an authorized learned covariate (S157 T2) |
| n_measured | LAWFUL_OPERATOR_CONTEXT | high identity proxy (S157 T4; Phase 5) |
| visible_library_size | LAWFUL_OPERATOR_CONTEXT | no context field is a model input until the real-data lane approves one |
| donor_id | SPLIT_ONLY | grouping for splits and inference units |
| query_counts, full_library_size | READOUT_ONLY | scoring only, never an input |
| global_cell_index, observer_manifest_sha256 | PROVENANCE_ONLY | identity binding |
| every oracle field | ORACLE_ONLY | physically outside the batch; the interface refuses it |

**known_identity_channel:** the measurement mask is MODEL_VISIBLE because measurement semantics require it, and Phase 5 rates the support pattern a high identity proxy; the Phase 7 readouts D1 and D2 watch it

## arms

### NULL

#### full_world

**n_cells:** 2000

##### adapter_digests

**model:** 99d0588d7cd64e1774538b0d7f66b0a6a0ed2e4575cdf73a270d42f41801bcce

**operator_context:** e3dc552c9d817a610b589c55618832e731761477b20456de2e542443ba05968c

**split_context:** 28def1575cff80c307e2972cba51d0cbf57e52f4f85108b3d3957d9fe1f6fd5a

**readout:** a0207dca40471709ed1320920f0412f3fa5adb53ae54aed2ecaa5c48b4bab3b0

#### rehearsal_batch

**n_cells:** 500

**n_features:** 19569

**adapter_model_digest:** ace72cd450f4a7200fcaa6dd29ece0907d3b859fafbb195500ad0924fefb61d3

**feature_identity_digest:** 90fcbedf75893ff9bb8da4ac94b70d0d3b0b5a461d519835c65943ff9b5c0c0b

**operator_identity_digest:** 03b920e4d13d1ad19eab93bfa0471a73bded3e526cb48bad2262f0796ee9c102

**measurement_support_digest:** f167956bd0a7ecc96c8b524556ea17f612381f2b848e8d6ea40c08995372be4c

**batch_scientific_identity_digest:** df60e2515bd284d4e067e2d5d7122e221db1c7405394ac636d16045a151c70e9

**synthetic_realization_id:** V77_SEED7302_ba16e2f270360094

**challenge_partition:** DEVELOPMENT_CALIBRATION

##### field_visibility

**gene_ids:** MODEL_VISIBLE

**student_expression:** MODEL_VISIBLE

**measurement_mask:** MODEL_VISIBLE

**hidden_target_mask:** MODEL_VISIBLE

**source_index:** LAWFUL_OPERATOR_CONTEXT

**operator_index:** LAWFUL_OPERATOR_CONTEXT

**visible_library_size:** LAWFUL_OPERATOR_CONTEXT

**n_measured:** LAWFUL_OPERATOR_CONTEXT

**donor_id:** SPLIT_ONLY

**query_counts:** READOUT_ONLY

**full_library_size:** READOUT_ONLY

**global_cell_index:** PROVENANCE_ONLY

**observer_manifest_sha256:** PROVENANCE_ONLY

#### zero_update_plumbing

**output_digest:** 010d05d9c786224911542d9a325b063afcfda606cd9d3ed2f3cdbb82f3ef3904

**provenance_receipt_digest:** 16138d72dacff92282e80179582d888bd7d9fca7857dcbf0eb75f4866551bdbe

**mutation_proof_status:** NOT_PROVEN_BY_SHARED_INTERFACE

**q_safety_execution_proof_status:** POLICY_ONLY_NOT_EXECUTION_PROVEN

##### seen_by_representation_function

###### model_inputs

- gene_ids
- hidden_target_mask
- measurement_mask
- student_expression

###### lawful_operator_context

- n_measured
- operator_index
- source_index
- visible_library_size

###### readout_only

- full_library_size
- query_counts

###### split_only

- donor_id

#### hidden_value_invariance

**hidden_entries_changed:** 234798

**model_digest_unchanged:** True

**operator_context_digest_unchanged:** True

**split_digest_unchanged:** True

**readout_digest_changed:** True

**leaky_control_digest_changed:** True

**verdict:** PASS

**reading:** the probe passes the adapter and refuses the leaky control: changing only hidden values moves the readout and the leaky view, never the model view or the context

### BIO

#### full_world

**n_cells:** 2000

##### adapter_digests

**model:** 68f91abe87ba89d3aa88745791caebe7b80e12197064aababd6b40f5861b094e

**operator_context:** 6a19d2cab78ca6cc89e882247166d9997900ef1d5ea0bd72c0ce4ee0e8bf6536

**split_context:** 28def1575cff80c307e2972cba51d0cbf57e52f4f85108b3d3957d9fe1f6fd5a

**readout:** c29273a79141274d1cba40c3769716f4cd2343787279a77c059198e59282d3a7

#### rehearsal_batch

**n_cells:** 500

**n_features:** 19569

**adapter_model_digest:** e90791efa8bc94bca11665134eaa2c2a9be86b8abef3cd1b09d4567029c3460b

**feature_identity_digest:** 90fcbedf75893ff9bb8da4ac94b70d0d3b0b5a461d519835c65943ff9b5c0c0b

**operator_identity_digest:** 03b920e4d13d1ad19eab93bfa0471a73bded3e526cb48bad2262f0796ee9c102

**measurement_support_digest:** f34bb77b208f6c435c559091d3e2c7b8c6926ed41d14594055b0667841750cf1

**batch_scientific_identity_digest:** 6d33e0399c82b59929dea887608db10da14357e47c7ba7618a40286682a48e8e

**synthetic_realization_id:** V77_SEED7302_ba16e2f270360094

**challenge_partition:** DEVELOPMENT_CALIBRATION

##### field_visibility

**gene_ids:** MODEL_VISIBLE

**student_expression:** MODEL_VISIBLE

**measurement_mask:** MODEL_VISIBLE

**hidden_target_mask:** MODEL_VISIBLE

**source_index:** LAWFUL_OPERATOR_CONTEXT

**operator_index:** LAWFUL_OPERATOR_CONTEXT

**visible_library_size:** LAWFUL_OPERATOR_CONTEXT

**n_measured:** LAWFUL_OPERATOR_CONTEXT

**donor_id:** SPLIT_ONLY

**query_counts:** READOUT_ONLY

**full_library_size:** READOUT_ONLY

**global_cell_index:** PROVENANCE_ONLY

**observer_manifest_sha256:** PROVENANCE_ONLY

#### zero_update_plumbing

**output_digest:** 010d05d9c786224911542d9a325b063afcfda606cd9d3ed2f3cdbb82f3ef3904

**provenance_receipt_digest:** 3785517b8d20c10e76e0437e2ff809eeb58e77860e45b1c1c263f51a05d4f9d3

**mutation_proof_status:** NOT_PROVEN_BY_SHARED_INTERFACE

**q_safety_execution_proof_status:** POLICY_ONLY_NOT_EXECUTION_PROVEN

##### seen_by_representation_function

###### model_inputs

- gene_ids
- hidden_target_mask
- measurement_mask
- student_expression

###### lawful_operator_context

- n_measured
- operator_index
- source_index
- visible_library_size

###### readout_only

- full_library_size
- query_counts

###### split_only

- donor_id

#### hidden_value_invariance

**hidden_entries_changed:** 234942

**model_digest_unchanged:** True

**operator_context_digest_unchanged:** True

**split_digest_unchanged:** True

**readout_digest_changed:** True

**leaky_control_digest_changed:** True

**verdict:** PASS

**reading:** the probe passes the adapter and refuses the leaky control: changing only hidden values moves the readout and the leaky view, never the model view or the context

### TWIN_EXACT

#### full_world

**n_cells:** 2000

##### adapter_digests

**model:** 68f91abe87ba89d3aa88745791caebe7b80e12197064aababd6b40f5861b094e

**operator_context:** 6a19d2cab78ca6cc89e882247166d9997900ef1d5ea0bd72c0ce4ee0e8bf6536

**split_context:** 28def1575cff80c307e2972cba51d0cbf57e52f4f85108b3d3957d9fe1f6fd5a

**readout:** c29273a79141274d1cba40c3769716f4cd2343787279a77c059198e59282d3a7

#### rehearsal_batch

**n_cells:** 500

**n_features:** 19569

**adapter_model_digest:** e90791efa8bc94bca11665134eaa2c2a9be86b8abef3cd1b09d4567029c3460b

**feature_identity_digest:** 90fcbedf75893ff9bb8da4ac94b70d0d3b0b5a461d519835c65943ff9b5c0c0b

**operator_identity_digest:** 03b920e4d13d1ad19eab93bfa0471a73bded3e526cb48bad2262f0796ee9c102

**measurement_support_digest:** f34bb77b208f6c435c559091d3e2c7b8c6926ed41d14594055b0667841750cf1

**batch_scientific_identity_digest:** 6d33e0399c82b59929dea887608db10da14357e47c7ba7618a40286682a48e8e

**synthetic_realization_id:** V77_SEED7302_ba16e2f270360094

**challenge_partition:** DEVELOPMENT_CALIBRATION

##### field_visibility

**gene_ids:** MODEL_VISIBLE

**student_expression:** MODEL_VISIBLE

**measurement_mask:** MODEL_VISIBLE

**hidden_target_mask:** MODEL_VISIBLE

**source_index:** LAWFUL_OPERATOR_CONTEXT

**operator_index:** LAWFUL_OPERATOR_CONTEXT

**visible_library_size:** LAWFUL_OPERATOR_CONTEXT

**n_measured:** LAWFUL_OPERATOR_CONTEXT

**donor_id:** SPLIT_ONLY

**query_counts:** READOUT_ONLY

**full_library_size:** READOUT_ONLY

**global_cell_index:** PROVENANCE_ONLY

**observer_manifest_sha256:** PROVENANCE_ONLY

#### zero_update_plumbing

**output_digest:** 010d05d9c786224911542d9a325b063afcfda606cd9d3ed2f3cdbb82f3ef3904

**provenance_receipt_digest:** 57e562ecb245cdd2a9bd491cae7304173372e51dc064e4e98ec3718992df809e

**mutation_proof_status:** NOT_PROVEN_BY_SHARED_INTERFACE

**q_safety_execution_proof_status:** POLICY_ONLY_NOT_EXECUTION_PROVEN

##### seen_by_representation_function

###### model_inputs

- gene_ids
- hidden_target_mask
- measurement_mask
- student_expression

###### lawful_operator_context

- n_measured
- operator_index
- source_index
- visible_library_size

###### readout_only

- full_library_size
- query_counts

###### split_only

- donor_id

#### hidden_value_invariance

**hidden_entries_changed:** 234942

**model_digest_unchanged:** True

**operator_context_digest_unchanged:** True

**split_digest_unchanged:** True

**readout_digest_changed:** True

**leaky_control_digest_changed:** True

**verdict:** PASS

**reading:** the probe passes the adapter and refuses the leaky control: changing only hidden values moves the readout and the leaky view, never the model view or the context

### TWIN_OPERATOR

#### full_world

**n_cells:** 2000

##### adapter_digests

**model:** 9ca19c541772d120008ded8fd7d8057ce032490642991f12a98c2001d6a17576

**operator_context:** 550d9e36cee4a46a2b78ee6ec8f49a1386805e24832beb7c178188dcad67e573

**split_context:** 28def1575cff80c307e2972cba51d0cbf57e52f4f85108b3d3957d9fe1f6fd5a

**readout:** 5b676e8877c362505d9e33b26c2dc33fba61a8ad7e1d2585da2a51f12e369b2d

#### rehearsal_batch

**n_cells:** 500

**n_features:** 19569

**adapter_model_digest:** 754809d81be3c1cc9ea5b5bfe1f0d08cb3722afcd44122d9838fb8ea40fcee79

**feature_identity_digest:** 90fcbedf75893ff9bb8da4ac94b70d0d3b0b5a461d519835c65943ff9b5c0c0b

**operator_identity_digest:** 03b920e4d13d1ad19eab93bfa0471a73bded3e526cb48bad2262f0796ee9c102

**measurement_support_digest:** d8e64dd5702e07efe970eac7bc833fb9e7ca1523aa8e43c21fa25c13e1cef696

**batch_scientific_identity_digest:** 0f9eae5cb16f9cdd26402331083a9acd4d33d7d10adf360f74b546c9b9bcb61d

**synthetic_realization_id:** V77_SEED7302_ba16e2f270360094

**challenge_partition:** DEVELOPMENT_CALIBRATION

##### field_visibility

**gene_ids:** MODEL_VISIBLE

**student_expression:** MODEL_VISIBLE

**measurement_mask:** MODEL_VISIBLE

**hidden_target_mask:** MODEL_VISIBLE

**source_index:** LAWFUL_OPERATOR_CONTEXT

**operator_index:** LAWFUL_OPERATOR_CONTEXT

**visible_library_size:** LAWFUL_OPERATOR_CONTEXT

**n_measured:** LAWFUL_OPERATOR_CONTEXT

**donor_id:** SPLIT_ONLY

**query_counts:** READOUT_ONLY

**full_library_size:** READOUT_ONLY

**global_cell_index:** PROVENANCE_ONLY

**observer_manifest_sha256:** PROVENANCE_ONLY

#### zero_update_plumbing

**output_digest:** 010d05d9c786224911542d9a325b063afcfda606cd9d3ed2f3cdbb82f3ef3904

**provenance_receipt_digest:** 6dec16f4f495838178e41369d260a38884a4ac407b58b5e3b04327ca8065e78b

**mutation_proof_status:** NOT_PROVEN_BY_SHARED_INTERFACE

**q_safety_execution_proof_status:** POLICY_ONLY_NOT_EXECUTION_PROVEN

##### seen_by_representation_function

###### model_inputs

- gene_ids
- hidden_target_mask
- measurement_mask
- student_expression

###### lawful_operator_context

- n_measured
- operator_index
- source_index
- visible_library_size

###### readout_only

- full_library_size
- query_counts

###### split_only

- donor_id

#### hidden_value_invariance

**hidden_entries_changed:** 235070

**model_digest_unchanged:** True

**operator_context_digest_unchanged:** True

**split_digest_unchanged:** True

**readout_digest_changed:** True

**leaky_control_digest_changed:** True

**verdict:** PASS

**reading:** the probe passes the adapter and refuses the leaky control: changing only hidden values moves the readout and the leaky view, never the model view or the context

## q_safety_boundary

| channel | v77_evidence | status_at_interface | required_at_boundary |
|---|---|---|---|
| QUERY_VALUE | the model batch holds no hidden value: test_hidden_values_cannot_reach_model_or_operator_context, test_no_oracle_or_hidden_value_is_model_visible; executed hidden-value invariance probe on every arm (arms.*.hidden_value_invariance) | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| NORMALIZATION_DENOMINATOR | evidence is normalized by the visible library, hidden counts excluded (S167): test_student_evidence_is_visible_counts_over_the_visible_library; executed hidden-value invariance probe on every arm (arms.*.hidden_value_invariance) | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| LIBRARY_SIZE_SUMMARY | visible_library_size excludes hidden targets; full_library_size is READOUT_ONLY; executed hidden-value invariance probe on every arm (arms.*.hidden_value_invariance) | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| DETECTED_FEATURE_SUMMARY | n_measured counts structural support, not detection: test_measurement_mask_is_the_worlds_per_element_support; executed hidden-value invariance probe on every arm (arms.*.hidden_value_invariance) | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| QC_DESCENDANTS | no field derived from full counts exists on the model or context side; executed hidden-value invariance probe on every arm (arms.*.hidden_value_invariance) | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| SUPPORT_OR_MISSINGNESS_SUMMARY | the mask is producer structural support, value-independent, and the interface refuses a batch mask that differs from it: test_interface_refuses_a_batch_mask_that_differs_from_producer_support. Not a query leak, but a high identity proxy (Phase 5) | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| MASK_CONSTRUCTION | hidden targets drawn within structural support, seeded by (seed, global_cell_index): test_hidden_mask_is_value_independent, test_hidden_draw_follows_cell_identity_not_row_order | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| QUERY_DEPENDENT_PREPROCESSING | the adapter has none; executed hidden-value invariance probe on every arm (arms.*.hidden_value_invariance) | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |
| TARGET_OR_TEACHER_PRE_CONTEXT | no target or teacher is constructed; target spec UNSET in the bridge | POLICY_ONLY_NOT_EXECUTION_PROVEN | the bound runtime reruns the probe through its own adapter path and records PROVEN_BY_BOUND_ADAPTER_RUNTIME |

## runtime_proof_fields_expected

### interface_provenance

- mutation_proof_status = PROVEN_BY_BOUND_RUNTIME
- q_safety_execution_proof_status = PROVEN_BY_BOUND_ADAPTER_RUNTIME
- runtime_successor_digest
- checkpoint_digest
- feature_identity_digest, operator_identity_digest, measurement_support_digest and batch_scientific_identity_digest equal to this package's

### lifecycle

- PREPARED
- MUTATED
- EMA_APPLIED
- CHECKPOINTED
- QUALIFICATION_OUTPUTS_FROZEN
- VERIFIED

**run_mode:** BOUNDED_MUTATION_REHEARSAL

### runtime_receipts_as_read_at_pr224

**read_at:** 683d67404e60

**superseded_by:** the reviewed bound-runtime SHA when the runtime lane supplies it

#### persisted_checkpoint_proof

- schema
- runtime_contract
- governance_digest
- artifact_sha256
- logical_checkpoint_sha256
- premise_state_sha256
- runtime_source_sha256
- completed_guard_receipt_digest
- next_update_index
- presentations_seen
- persisted_verified_reload

#### bound_checkpoint

- schema
- runtime_contract
- premise_state_sha256
- runtime_source_sha256
- reference_checkpoint
- completed_guard_receipt
- training_authority_digest
- execution_authorized
- training_authorized
- production_promotable

#### guarded_step_start

- schema
- authority_digest
- governance_digest
- optimizer_identity
- checkpoint_digest
- rehearsal_only
- training_authorized
- execution_authorized
- receipt_digest

#### guarded_step_completion

- schema
- authority_digest
- governance_digest
- optimizer_identity
- parent_checkpoint_digest
- checkpoint_digest
- guarded_step_token
- rehearsal_only
- training_authorized
- execution_authorized
- receipt_digest

## boundary_findings

| id | finding | requirement |
|---|---|---|
| BF1_MODEL_VIEW_CARRIES_OPERATOR_CONTEXT | the shared interface's model view returns lawful_operator_context beside model_inputs (pipeline.py model_view at f6d63b2f), and the V77 bridge declares raw source and operator identity, n_measured and visible_library_size there. A runtime that feeds the whole view to learnable parameters would learn from raw identity and a high identity proxy | the first rehearsal feeds model_inputs only; no lawful_operator_context key reaches a learnable parameter, and the runtime records which view keys reached the model. Whether raw identity should leave the batch fields altogether, with the receipts still authenticating it, is for the interface owner and the real-data lane; the bridge and the plumbing receipt stay unchanged as instructed |
| BF2_RUN_IDS_NAME_THE_ARM | this handoff's run ids name the arm (v77-s157-handoff-<arm>-<head>) | harmless for ZERO_UPDATE; the mutation experiment uses coded run ids and paths with a sealed code map (Phase 7) |
| BF3_EXACT_TWIN_IDENTITY | BIO and TWIN_EXACT share the batch scientific identity digest and the adapter model digest, as an exact twin must; all arms share one realization id because they share the base truth manifest | any runtime-side difference between BIO and TWIN_EXACT is a leak (Phase 7 STOP_1) |

## gating

- mutation is NOT executed on this branch
- it needs the runtime lane's reviewed bound-runtime SHA and an explicit rehearsal contract
- the runtime must reproduce this package's digests through the same entrypoint before any update
- the Phase 7 pre-registration must be frozen and named in the rehearsal contract

## does_not

- write optimizer, EMA or checkpoint code
- execute any mutation
- change runtime architecture
- admit raw identity or any context field as a model input

## run_record

**path:** results/v77/V77_RUNTIME_HANDOFF_RUN_V1.json

**sha256:** ba50eaf018542633e679f82daa9fbd40ed209356e05293975313fc9cab7a633f

**recorded_utc:** 2026-10-07T06:56:27Z

**head_when_recorded:** 86907199c6d564476a4d44ce9206b9e83971ad5c
