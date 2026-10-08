# V77 first bounded-mutation experiment around S157: prospective pre-registration (not executed)

**schema:** V77_S157_BOUNDED_MUTATION_PREREGISTRATION_V1

**claim_class:** V77_SYNTHETIC_WORLD_QUALIFICATION

**execution_status:** NOT_EXECUTED__AWAITS_BOUND_RUNTIME_SHA_AND_REHEARSAL_CONTRACT

**primary_question:** Does learned representation behaviour distinguish biology from nuisance beyond what is possible from the admitted observations?

## admitted_observation_ceiling

**TWIN_EXACT:** zero by construction: the admitted observations are byte-identical to BIO's, so any separation is a leak

**TWIN_OPERATOR:** not computable exactly. The admitted observations do carry operator information: the Phase 5 audit recovers source perfectly and operator at 0.52 against a 0.81 ceiling from the support pattern. Separation attributable to those channels (D1, D2) is possible from the admitted observations and is a shortcut, not biology

**NULL:** no program exists, so any program readout is invented

## reading_rules

- Exact twins remaining identical is a valid result, and the expected one.
- Loss reduction is not a success criterion; it is reported only as mechanical evidence that an update happened.
- No pass or fail threshold exists. Each comparison has a declared reading; nothing is tuned after an outcome.
- Seed 7302 makes this DEVELOPMENT_CALIBRATION: a result here is never independent confirmation.

## arms

| arm | roster_arm | world | note |
|---|---|---|---|
| BIO | PLANTED_RECOVERABLE_BIOLOGICAL | S157 BIO | recoverable by the frozen known-support readout (S157 ARM1 R2 0.853); not established at the unsupervised level (S157 T5) |
| BIO_REPEAT | NOT_IN_ROSTER: replicate control | S157 BIO, run again identically | measures the run-to-run nondeterminism floor that C1 is judged against |
| TWIN_EXACT | PLANTED_INACCESSIBLE_PRIVATE_STATE | S157 TWIN_EXACT | model-facing inputs byte-identical to BIO (S157 RED_1) |
| TWIN_OPERATOR | TECHNICAL_OPERATOR_SHORTCUT | S157 TWIN_OPERATOR | operator-linked capture; zero-update readout R2 0.872 for the nuisance, NOT_SEPARATED by lawful descriptors (S157 T3) |
| NULL | CLEAN_NEGATIVE | S157 NULL | no planted program |
| QUERY_LEAK | QUERY_LEAK | S157 BIO with hidden values written into the evidence | must be refused at the boundary by the handoff probe and the runtime's q-safety execution proof; it never trains |

## identical_across_arms

- runtime and its reviewed bound SHA
- optimizer identity and settings
- initial checkpoint digest
- update count
- batch order rule
- EMA rule
- seeds
- permitted inputs
- frozen readout code and its digest

## permitted_inputs

### model

- gene_ids
- student_expression
- measurement_mask
- hidden_target_mask

### excluded

- source_index
- operator_index
- donor_id
- global_cell_index
- n_measured
- visible_library_size
- every ORACLE_ONLY and READOUT_ONLY field

**why:** MODEL_VISIBLE only, the same for every arm. Raw identity is restricted (S157 T2). No context field is a model input until the real-data lane approves one. The measurement mask stays because measurement semantics require it, although the Phase 5 audit rates the support pattern a high identity proxy; D1 and D2 watch that channel. The interface's model view also carries lawful_operator_context (handoff BF1): only model_inputs may reach learnable parameters

**blinding:** arms run under coded run ids and paths; the code-to-arm map is sealed with the oracle and opened only after every output is frozen (handoff BF2)

**split:** train on even global_cell_index; frozen readouts fitted on even and scored on odd cells (the S157 split)

**bounded_update:** a tiny bounded number of guarded updates, set by the rehearsal contract; the same in every arm

## frozen_readouts

| id | what |
|---|---|
| R1_BIO_MODULE | ridge readout of the hidden program activity from the frozen representation |
| R2_NUISANCE | the same readout for the hidden operator-linked nuisance |
| D1_OPERATOR_PROBE | linear and k-NN probes of operator identity from the representation (Phase 5 method) |
| D2_SUPPORT_ONLY | the readouts recomputed on representations of support-only inputs (evidence values zeroed, masks kept): how much the representation carries from the mask alone |
| E1_TWIN_EQUALITY | representation digest and every readout output, BIO against TWIN_EXACT |

## comparisons

| id | arms | reading |
|---|---|---|
| C1 | BIO; TWIN_EXACT; BIO_REPEAT | inputs are identical, so the representation and every readout must agree within the BIO_REPEAT floor (bitwise if the runtime is deterministic). A larger difference means the runtime read something outside the batch: STOP |
| C2 | BIO; TWIN_OPERATOR | compare post-update separation with the zero-update baseline: the same frozen readouts on the same runtime's initial checkpoint, update count 0, in each arm (the S157 raw-evidence values are context, not the baseline). A rise explained by D1 and D2 (operator identity up, support-only readouts high) is a learned shortcut, not biology. No rise means the update added nothing beyond the admitted observations. A fall means operator information was discarded, which is neither success nor failure on its own |
| C3 | BIO; NULL | the program readout must not appear in NULL; if it does, the readout or representation invents structure |
| C4 | QUERY_LEAK | refused before any update; if it trains or its batch is accepted: STOP |
| C5 | BIO; BIO_REPEAT | defines the nondeterminism floor; reported, never tuned |

## stop_rules

| id | arms | condition |
|---|---|---|
| STOP_1 | BIO; TWIN_EXACT | twin divergence beyond the BIO_REPEAT floor |
| STOP_2 | QUERY_LEAK | the leak batch is accepted or trains |
| STOP_3 | BIO; BIO_REPEAT; TWIN_EXACT; TWIN_OPERATOR; NULL | any oracle field reaches the runtime |
| STOP_4 | BIO; TWIN_EXACT; TWIN_OPERATOR; NULL; BIO_REPEAT | arms differ in optimizer, initial checkpoint, update count, seeds or permitted inputs |
| STOP_5 | BIO; TWIN_EXACT; TWIN_OPERATOR; NULL; BIO_REPEAT | any lawful_operator_context key, raw identity above all, reaches a learnable parameter |

**oracle_policy:** oracle values are revealed only after the representation and every readout output are frozen and hashed (the interface's FrozenQualificationOutputsV1 and OracleUnblindingReceiptV1, the S157 Blinding pattern); any change after unblinding requires a successor pre-registration and a new truth seed

## runtime_proof_required

- mutation_proof_status PROVEN_BY_BOUND_RUNTIME
- q_safety_execution_proof_status PROVEN_BY_BOUND_ADAPTER_RUNTIME
- guarded-step start and completion receipts
- EMA applied and digested
- persisted checkpoint with verified reload, for every arm
- handoff digests reproduced by the runtime (results/v77/V77_RUNTIME_HANDOFF_PACKAGE_V1.json)

## unset_slots

| slot | value | owner |
|---|---|---|
| update_count | UNSET | runtime lane rehearsal contract |
| optimizer_identity_and_settings | UNSET | runtime lane rehearsal contract |
| learning_rate_schedule | UNSET | runtime lane rehearsal contract |
| ema_rule | UNSET | runtime lane rehearsal contract |
| initial_checkpoint_digest | UNSET | runtime lane rehearsal contract |
| batch_order_rule | UNSET | runtime lane rehearsal contract |
| nondeterminism_policy | UNSET | runtime lane rehearsal contract |
| bound_runtime_sha | UNSET | runtime lane rehearsal contract |

## gating

- the runtime lane's reviewed bound-runtime SHA
- an explicit rehearsal contract filling every UNSET slot
- the handoff digests reproduced by that runtime
- this pre-registration frozen, its digest named in the contract

## governance

- TRAINING=OFF until the rehearsal contract changes the status; ZERO_UPDATE remains the only executed mode
- no real RNA, TEST, Morabito, 500K or Stage 4
- no target, representation, estimand, weighting or deciding threshold selected

**recorded_utc:** 2026-10-07T06:58:50Z

**head_when_recorded:** 223a41fcf748f2ae4d210884a0ece0d15afec925

## evidence

**results/v77/V77_S157_TERMINAL_RECEIPT_V1.json:** 9c4fd3820631dc9920f91278a75899291101045eab2ed785a457fcd2ab0cec00

**results/v77/V77_S157_PAIRED_CHALLENGE_SCORE_ARMS_V1.json:** 23e613979e5014ce29797b0e4585a66fbea4fded2ceaaed2751d3f29f6e18153

**results/v77/V77_S157_CONTEXT_ABLATION_SUMMARY_V1.json:** 85c13f5db4075ad0e8bcf2cb4f6341eb0723ace138241a5826f9b33d3297f78a

**results/v77/V77_CONTEXT_SHORTCUT_AUDIT_V1.json:** 858a850506b9b52c42542f27594a47b3b7240a6a1470a8b21d05cf8217e60800

**results/v77/V77_RUNTIME_HANDOFF_PACKAGE_V1.json:** 7add1023b5f57c36251b97e5d1b52ef800c7fc024f2a0b75ddc5f5cb61886999
