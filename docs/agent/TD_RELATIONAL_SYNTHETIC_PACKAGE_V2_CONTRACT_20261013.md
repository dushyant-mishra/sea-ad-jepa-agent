# TD relational synthetic package V2 — prospective interface-repair contract

Date: 2026-10-13
Status: `PROVISIONAL_BUILD_CONTRACT__AWAITING_FINAL_REPAIRED_PR316_HEAD__NO_FINAL_ARCHIVE_FREEZE__NO_TD_EXECUTION`

## Purpose

Repair the synthetic-to-TD interface mismatch identified after PR #318 without changing TD science or weakening the TD-owned execution path.

PR #318 / V1 remains byte-immutable historical evidence with status:

`AUTHENTIC_BUT_INTERFACE_SUPERSEDED`

V2 is a prospective successor package. It preserves the nine previously frozen biological challenge intents while delivering only raw pre-geometry observations compatible with the repaired TD V2 package boundary.

## Nine biological challenge intents

1. `REL_BROAD_MESO_POSITIVE`
2. `REL_FINE_RECURRENT_POSITIVE`
3. `REL_RARE_LOCAL_ISLAND_POSITIVE`
4. `REL_MULTI_ISLAND_POSITIVE`
5. `REL_DONOR_RESTRICTED_POSITIVE`
6. `REL_SOURCE_VISIBILITY_STRESS`
7. `REL_TECHNICAL_TWIN_NEGATIVE`
8. `REL_NULL_NEGATIVE`
9. `REL_UNDERPOWERED_POSITIVE`

The worlds may not be tuned using TD57C, TD59, or any V2 TD qualification outcome.

## Blind pre-fit binding

The pre-fit binding schema is:

`JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2`

It contains exactly:

- package ID;
- package SHA-256;
- controller-manifest SHA-256;
- allowed fit-view field list;
- nine opaque challenge IDs with their fit-file SHA-256 values;
- all-false authority fields.

It contains no capability mapping, semantic class, expected verdict, biological challenge name, rare-state label, or controller control-role mapping.

Challenge IDs must be semantically opaque.

## Raw NPZ surface

Every challenge is a SHA-named `<sha256>.npz` file loadable with `allow_pickle=False`, with no object arrays.

Exact fit-side fields:

- `source`, `panel_id`;
- `z_values`, `x_values`, `y_values`;
- `z_measured`, `x_measured`, `y_measured`;
- `z_feature_ids`, `x_feature_ids`, `y_feature_ids`;
- `donor_ids`, `operator_ids`, `global_rows`;
- `source_library`, `detected_genes`;
- `focal_mask`, `neighbor_pool_mask`, `min_focal_anchors_per_donor`;
- `control_ids`, `control_focal_masks`, `control_neighbor_pool_masks`, `control_min_focal_anchors_per_donor`.

Each Z/X/Y view has exactly 512 features.

The package must never deliver distance matrices, selected pairs, pair signs, relational triplets, null Y maps, TD statistics, PASS/FAIL/NOT_ESTIMABLE results, or any post-fit quantity.

## Uniform five-control blindness rule

Every one of the nine challenges carries exactly five opaque control profiles, including non-rare challenges.

This prevents control presence/count from revealing which opaque challenges participate in rare/control-bearing adjudication.

Each challenge therefore has the same structural control surface:

- five opaque control IDs;
- five focal masks;
- five neighbor-pool masks;
- five positive minimum-focal-support values.

Control IDs may not contain biological or role semantics.

For the four TD controller capabilities that actually use rare-control adjudication, the controller-only manifest maps those opaque controls onto:

- `DONOR_MATCHED_COMMON`;
- `DEPTH_DETECTED_SUM_MATCHED`;
- `SOURCE_OPERATOR_MATCHED`;
- `WRONG_CELL`;
- `PSEUDO_RARE_TECHNICAL`.

For all other capabilities, the five controls remain blinded nuisance profiles and controller `control_roles` is empty.

## Controller manifest

Controller schema:

`JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V2`

Top-level fields are exactly:

- `schema`;
- `package_sha256`;
- `claims`;
- `authority`.

`claims` maps the nine biological capabilities, in frozen TD order, to:

- opaque challenge ID;
- semantic class;
- controller-only control-role mapping where applicable;
- explicit expected status only for the prospectively defined source-visibility stress case.

Allowed semantic classes:

- `POSITIVE_TRUTH`;
- `NEGATIVE_TRUTH`;
- `UNDERIDENTIFIED_TRUTH`;
- `STRESS_TRUTH`.

No semantic mapping exists in the pre-fit binding or NPZ files.

## Package identity without a hash cycle

The synthetic generator defines a semantically blind fit-package root from:

- package ID;
- exact fit-view field list;
- nine opaque challenge IDs and NPZ hashes;
- all-false binding authority.

Its canonical SHA-256 is the package SHA used by both binding and controller manifest.

The controller manifest is then canonical-hashed separately and that SHA is recorded in the pre-fit binding.

The final transport archive hash is a separate identity and will not be frozen until the TD agent supplies the final repaired PR #316 commit SHA.

## Biological construction rules

- Broad/mesoscale and fine recurrent positive worlds use shared latent biological geometry observed through raw 512-feature molecular views.
- Rare-local and multi-island worlds place donor-recurrent local biological structure inside the same per-donor population rather than creating a separate rare dataset.
- Donor-restricted truth is present in exactly five donors with at least one true zero-prevalence donor.
- Source-visibility stress shares the same latent biological state as its broad counterpart while degrading observation/support only.
- Technical-twin truth is observation-driven with no target shared X/Y biological relation.
- Null truth contains no target X/Y relational biology.
- Underpowered positive truth contains real relational biology but only four recurring donors; the synthetic lane does not inject the TD `NOT_ESTIMABLE` verdict.

## Synthetic-side tests

Before any final compatibility certification, synthetic tests must establish:

1. exact blind V2 binding shape;
2. nine distinct opaque challenge IDs;
3. SHA-named NPZ byte authentication;
4. exact raw NPZ schema;
5. 512 features per Z/X/Y view;
6. `allow_pickle=False` loadability and no object arrays;
7. exactly five opaque controls per challenge;
8. no TD geometry/statistic/verdict fields;
9. controller-only semantic mapping;
10. donor-restricted and underpowered structural invariants;
11. source-visibility latent identity with observation-layer difference;
12. byte-deterministic generation.

The focused CI qualification on PR #319 passed `9/9` tests on run `38426772504`, job `115398118488`. This is synthetic package engineering evidence only, not TD gate qualification.

## Final compatibility boundary

Do not freeze the final archive or compatibility certificate against historical PR #316 head `0ebbdd47...` or any intermediate self-audit head.

After the TD agent explicitly supplies the final repaired PR #316 SHA, the synthetic lane may import that exact head and run only the permitted preflight:

1. authenticate package SHA;
2. authenticate all nine SHA-named NPZ files;
3. load exact raw NPZ schema;
4. verify semantic blindness;
5. verify five opaque controls on every challenge;
6. require repaired adapter status `READY` / disk-preflight terminal `READY_TO_EXECUTE_BLIND_FIT`.

The compatibility run must stop before `execute_blinded_fit(...)` and must not compute TD geometry or inspect biological qualification outcomes.

Only after that preflight may the final transport archive, package receipt, TD-interface identity, and handoff hashes be frozen.

## Authority

All remain false:

- real TD execution;
- target selection;
- TD60;
- Stage4;
- JEPA training.

Current terminal:

`V2_RAW_WORLD_GENERATOR_AND_BLIND_PACKAGE_CONTRACT_BUILT__NINE_CHALLENGES__FIVE_OPAQUE_CONTROLS_EACH__FOCUSED_SYNTHETIC_TESTS_9_OF_9_PASS__FINAL_ARCHIVE_AND_TD_PREFLIGHT_CERTIFICATION_WAIT_FOR_EXPLICIT_FINAL_PR316_SHA__NO_EXECUTE_BLINDED_FIT__REAL_TD_OFF__TRAINING_OFF`
