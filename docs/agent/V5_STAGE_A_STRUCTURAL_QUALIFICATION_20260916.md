# V5 Stage-A structural qualification — 2026-09-16

Branch `audit/v5-stage-a-spillover-firewall-20260916` @ `15e2d76e`. PR #17.
No training. No `D_shared`. No protected outcomes. No production geometry selected.

---

## Defect repair that preceded implementation (ChatGPT review, upheld)

`address_registry_authority_sha256` accepted any well-formed digest that was not one of
three known raw-artifact hashes. **RED proven** against `f33e0a7b`: `b`×64, `0`×64, `f`×64,
`deadbeef`×8 and `1234567890abcdef`×4 all validated.

Repaired with an **allowlist of exactly one value** plus a cross-authority closure
(`bind_provider_to_registry_authority`) that recomputes the live registry authority's own
`canonical_digest()` rather than trusting a transcribed constant. Unknown digests now fail
closed, including one differing by a single character.

The two hashes stay distinct: raw artifact `7d61ed7b…` (the CSV) vs registry **authority**
`28b20a45…` (what the provider binds).

---

## Provider mechanism, and why it is not memorization

`V5_SHARED_ADDRESS_QUERY_PROVIDER_V1` = deterministic k-of-m feature hashing over canonical
identity → **one shared trainable projection**.

| | trainable parameters | scales with 41,238? | per-address free vector? |
|---|---|---|---|
| `nn.Embedding(41238, d)` | `41238·d` | yes | yes — rejected |
| this provider | `m·d + d` | **no** | **no** |

Measured: 32 addresses × 4 hashes = 128 bucket draws landing in **57 distinct buckets** —
addresses provably share projection rows. `is_per_address_memorization()` returns `True` for
the embedding attack and `False` for the provider.

`m`, `n_hashes`, `query_width`, `init_seed` are **required constructor arguments with no
defaults** (asserted by test), supplied later by model-geometry/runtime authority. No
historical seed, no Layer-2 rank, no TD-derived width, no 128/256/320/512.

Lawfulness is structural, not conventional: `forward()` takes only `molecular_address_ids`;
every privileged field raises `ForbiddenProviderInputError`. The encoder is deliberately
torch-free so determinism, sharing, replay and field safety are verifiable without autograd.

---

## Defect CI caught in my own work

`6e21ecde` failed CI: 129 passed, **1 failed** — `test_skipped_optimizer_step_cannot_advance_ema_state`.

My first EMA helper was ungated and assumed `decay·x + (1−decay)·x == x` when the student is
unchanged. In float32 that differs by up to one ULP, so an ungated teacher **drifts on every
skipped step** — precisely what check 3 forbids. Arithmetic neutrality is not the requirement;
a gate is. `ProviderEmaState.update(..., step_taken=False)` now returns `False` and mutates
nothing. A companion test asserts the float drift still exists, so if the naive form ever
becomes neutral the fixture reports that it no longer guards anything.

---

## Stage-A 11-check matrix

| # | criterion | structural authority | executable test | actual evidence | verdict |
|---|---|---|---|---|---|
| 1 | shared trainable mechanism; no per-target memorization | `address_identity_encoding_v1`, provider | `test_trainable_parameters_do_not_scale_with_address_count`, `…_invariant_to_registry_row_count`, `test_unrestricted_per_address_embedding_is_rejected_by_qualification`, `test_distinct_addresses_provably_share_projection_rows` | params = 520 = 64·8+8, invariant across N ∈ {10, 1e3, 41238, 1e6}; embedding flagged, provider not; 57 distinct buckets of 128 draws | **PASS** |
| 2 | context/evidence gradient path into the mechanism | provider | `test_provider_parameters_receive_nonzero_gradient_from_the_prediction_path`, `test_broken_gradient_pathways_fail_qualification[detach/drop]`, `test_stop_gradient_provider_fails_qualification` | finite nonzero grads on `projection` and `bias` through context→prediction MSE; detached, unused and stop-grad variants all yield exactly 0 | **PASS** *(smallest real path; no production trainer exists yet)* |
| 3 | correct teacher/EMA reachability | `ProviderEmaState` | `test_every_trainable_parameter_is_enrolled_in_ema_state`, `…_silently_omitted…`, `test_skipped_optimizer_step_cannot_advance_ema_state`, `test_ungated_ema_would_drift_on_a_skipped_step`, `test_ema_rejects_a_provider_missing_enrolled_parameters`, `test_teacher_and_student…distinguishable` | enrolment == full trainable set; skipped step is a no-op; missing parameter fails closed; teacher/student distinguishable | **PASS** *(reachability + gating; numeric timescale correctly not frozen)* |
| 4 | checkpoint/restart deterministic replay | `replay_state` / `from_replay_state` | `test_checkpoint_roundtrip…`, 6× `test_partial_replay_state_fails_closed`, `test_wrong_provider_id…`, `test_tampered_encoding_fingerprint…`, `test_missing_parameter_in_checkpoint…`, `test_replay_is_deterministic_across_fresh_construction` | round-trip `torch.equal` exact; every missing key, tampered fingerprint, wrong provider id and dropped parameter fails closed | **PASS** |
| 5 | eligibility independent of hidden target value | `reject_forbidden_inputs` | `test_query_is_unchanged_by_hidden_target_values` | `target_value` raises; query bit-identical before/after three attempted permutations | **PASS** |
| 6 | no post-hoc/value-derived QC eligibility | `reject_forbidden_inputs` | 7× `test_qc_and_visibility_cannot_enter_the_provider` | depth, q_depth, q_detect, detection, visibility, expression_mean, support_frequency all raise; query unchanged after each rejection | **PASS** |
| 7 | no unauthorized lookup/coordinate/ontology/graph leakage | `FORBIDDEN_PROVIDER_INPUT_FIELDS` | 12× `test_privileged_metadata_cannot_be_fed_to_the_provider`, `test_encoding_depends_only_on_canonical_identity` | symbol, biotype, ontology, graph_neighborhood, chromosomal_coordinate, source, operator_index, donor_id, dataset_id, expression_variance, target_rank, canonical_cell_id all rejected by construction | **PASS** |
| 8 | provider source/provenance bound | `CurrentTargetAddressProviderAuthorityV1` + closure | 6× `test_arbitrary_registry_authority_digest_fails_closed`, `test_provider_rejects_a_raw_registry_file_hash…`, `test_cross_authority_closure_binds_the_live_registry_authority`, `…rejects_a_mutated_registry_authority`, `test_different_registry_authority_changes_the_query_artifact_binding` | only `28b20a45…` accepted; raw registry, observation-state, block-manifest, arbitrary and off-by-one-char digests all rejected | **PASS** |
| 9 | no unauthorized historical carryover | spillover firewall | `…firewall_v1` + `…firewall_v2` (28 tests) | 17 Stage-A modules × 13 quarantined modules clean; transitive closure clean; wildcard loads nothing | **PASS** |
| 10 | no visibility/QC re-entry to primary molecular path | provider signature | `test_provider_signature_offers_no_visibility_or_qc_channel`, `test_provider_output_shape_is_geometry_supplied_not_registry_derived`, plus check-6 runtime attacks | only positional channel is canonical identity; static signature inspection + runtime rejection | **PASS** |
| 11 | no authority-by-name from historical experiments | enumerated vocabulary | `test_approved_vocabularies_are_nonempty_and_carry_no_historical_names`, `test_provider_id_carries_no_historical_experiment_name`, `test_no_historical_constant_is_a_provider_default`, 24× policy attacks | TD57/TD59/TD60 rejected in every policy field; no constructor default exists | **PASS** |

**11 PASS · 0 FAIL · 0 UNPROVEN.**

Pre-provider accounting was 2 PASS / 0 FAIL / 9 UNPROVEN (check 8 having been correctly
reverted from PASS to UNPROVEN on review, because an authority schema is not execution
evidence). Every promotion above rests on an instantiated implementation and an executed test.

---

## Execution accounting

| category | local (py3.9, torch 2.1.2+cpu) | CI (py3.12, torch 2.14.0+cpu) |
|---|---|---|
| PASSED | **133** | **133**, plus 54 in the anti-skip guard step |
| FAILED | 0 | 0 |
| SKIPPED | 0 | 0 — guard fails the job on any skip |
| DESELECTED | 0 | 0 |
| NOT EXECUTED | broader non-v5 suite | — |
| ENVIRONMENT BLOCKED | 0 (torch installed mid-task) | 0 |
| HEAVY/DATA-DEPENDENT NOT RUN | FULL104 reads were read-only provenance only; no heavy run needed for structural qualification | — |

CI run on `15e2d76e` is green. The workflow fails closed if the provider suite skips.

---

## Red-team results

| attack | outcome |
|---|---|
| unrestricted per-address learned memory | rejected by qualification predicate |
| target-value leakage / target-derived eligibility | rejected at the interface |
| visibility/QC side channel | rejected; query unchanged |
| source/operator/donor/dataset leakage | rejected |
| biological annotation, coordinate, ontology, graph leakage | rejected |
| detached / unused / stop-grad context | zero provider gradient — fails qualification |
| omitted EMA parameters | fails closed |
| EMA update on skipped step | **real defect, found by CI, fixed by gating** |
| checkpoint omission / partial / tampered state | fails closed |
| wrong or arbitrary registry authority | **real defect, found by review, fixed by allowlist** |
| raw-hash vs authority-hash confusion | rejected |
| historical constant carryover / experiment-name selection | rejected; no defaults exist |
| nondeterministic replay | exact `torch.equal` round-trip |

---

## Residual risk

1. Check 2's context path is the smallest real one, not the production trainer — that does
   not exist yet, and building one here would select architecture Stage-A must not select.
2. Check 3 demonstrates reachability and gating; the numeric EMA timescale is deliberately
   unfrozen and belongs to the EMA-timescale authority.
3. `query_artifact_sha256` binds provider id, registry authority, encoding fingerprint and
   configuration — not learned weights (checkpoint state) and not later geometry.
4. Capacity `m` and width `d` remain unchosen. A later authority must pick them; the
   memorization predicate should be re-run once it does, since a sufficiently large `m·d`
   could in principle approach per-address capacity.

---

## Disposition

`STAGE_A_STRUCTURAL_QUALIFICATION_PASS__READY_FOR_MASKING_AUTHORITY`

This does **not** authorize training. `TRAINING_OFF`,
`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION` and all standing boundaries remain in force.
