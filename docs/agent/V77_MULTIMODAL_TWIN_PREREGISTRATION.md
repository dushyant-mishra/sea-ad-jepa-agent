# V77 multimodal semantic-twin challenge: prospective pre-registration (not executed)

**schema:** V77_MULTIMODAL_TWIN_PREREGISTRATION_V1

**claim_class:** V77_SYNTHETIC_WORLD_QUALIFICATION

**execution_status:** NOT_EXECUTED__REQUIRES_EVIDENCE_OBJECT_CHOICE

**question:** Can a scorer, or a learned representation, that also sees an independent object separate biology from an RNA twin, and does it correctly fail to separate a multimodal twin whose nuisance also drives the object?

## builds_on

**s157:** results/v77/V77_S157_TERMINAL_RECEIPT_V1.json: the RNA arms reuse S157 BIO, TWIN_EXACT and NULL unchanged

**matrix:** results/v77/V77_INDEPENDENT_EVIDENCE_MATRIX_V1.json: P1 (only query-matched objects can identify), P2 (object nuisance)

**circularity:** results/v77/V77_REGULATORY_CIRCULARITY_AUDIT_V1.json: construction rules for the object

## object_classes

| id | meaning | matrix_rows |
|---|---|---|
| O_NUCLEUS | per-nucleus paired features over a fixed universe | R1, R10a |
| O_DONOR | per-donor features from separate nuclei or tissue of the same donors | R2a, R7a, R10b |
| O_STATIC | a fixed annotation; included only as the STATIC_OBJECT control, since by P1 it cannot separate worlds that share RNA | R3, R4, R5b, R6 |

## generator

**rna:** the S157 construction on the repaired observer: base world, state k*, program module, operator set. BIO, RNA_TWIN, MULTIMODAL_TWIN, MULTIMODAL_TWIN_GLOBAL and QUERY_LEAK share byte-identical model-visible RNA

**hidden_variables:** z, per-cell program activity (BIO); m, the hidden measurement process, equal to z cell by cell in the twins, which is what makes their RNA identical; q, an object-only process (OBJECT_NUISANCE_ONLY)

**object_noise_stream:** its own stream, id 7720, seeded by (truth seed, stream, global cell index) and never by RNA values; BIO and MULTIMODAL_TWIN share it by design

**truth_seed:** a new truth seed declared at execution; seed 7302 only for plumbing, as DEVELOPMENT_CALIBRATION

**feature_universe:** program features (mapped to program genes), matched decoys and background, fixed before generation; the feature-to-gene map is static and identical in every arm

## observation_operators

**rna:** the repaired V77 observer and adapter V3, unchanged (structural support, per-element support masks)

**object:** per-feature counts from the object law, an object depth and a noise family (object slots); O_DONOR aggregates separate draws per donor

## hidden_truth

- z, m and q per cell
- arm label
- program gene and feature sets, decoy set
- gamma and gamma_g
- state k* and operator-set membership
- object noise stream state

## oracle_only_fields

- z
- m
- q
- arm_label
- program_gene_set
- program_feature_set
- decoy_feature_set
- gamma
- gamma_g
- state_k_star
- operator_set_membership
- object_noise_stream_state

## permitted_model_inputs

### fields

- gene_ids
- student_expression
- measurement_mask
- hidden_target_mask
- visible_library_size
- object_counts
- object_depth
- object_feature_universe
- feature_to_gene_map

**notes:** raw source and operator identity are excluded (S157 T2); the measurable-address count is an identity proxy (S157 T4) reachable through the measurement mask, and the Phase 5 shortcut audit reports its risk; donor identity is split context only

## independent_evidence_construction

- the object is drawn from its own noise stream, never from RNA values
- the feature universe and the feature-to-gene map are fixed before generation and are identical in every arm
- no RNA-derived grouping, label, metacell or feature selection enters the object
- QUERY_LEAK is the only arm that violates this; it declares the violation in its provenance record, which the scorer must refuse

## negative_controls

| arm | catches |
|---|---|
| CLEAN | a scorer that reports a program where there is none |
| QUERY_LEAK | a scorer or pipeline that credits an object built from the query RNA |
| STATIC_OBJECT | a claim that a static object separates worlds sharing RNA (matrix P1) |
| OBJECT_NUISANCE_ONLY | object signal read as a program without RNA coupling |
| MULTIMODAL_TWIN_GLOBAL | a scorer blind to within-object decoy contrasts |

## arms

| arm | rna | object | designed_identifiability_against_BIO | expected_outcome |
|---|---|---|---|---|
| BIO | S157 BIO: latent z drives the program module in state k* | base plus gamma times z at program features; decoys at base | REFERENCE | the reference world |
| RNA_TWIN | byte-identical to BIO: a hidden process m with m equal to z cell by cell (S157 TWIN_EXACT) | base everywhere: the object does not see m | IDENTIFIABLE_BY_DESIGN | a scorer that reads the object separates it from BIO; any RNA-only scorer cannot, because the RNA is identical |
| MULTIMODAL_TWIN | byte-identical to BIO, as RNA_TWIN | base plus gamma times m at program features from BIO's object noise stream; since m equals z, the object bytes equal BIO's (the V63 anchor-keyed pattern made exact) | NON_IDENTIFIABLE_BY_DESIGN | every statistic identical to BIO, bitwise. Equality is the pass; a difference is a leak |
| MULTIMODAL_TWIN_GLOBAL | byte-identical to BIO | base times (1 + gamma_g times m) at every feature, program and decoy alike: a yield effect, not a program effect | IDENTIFIABLE_BY_DESIGN | separable only through the program-versus-decoy contrast inside the object |
| CLEAN | S157 NULL: no program | base everywhere | NO_PROGRAM | no program-object coupling reported |
| QUERY_LEAK | byte-identical to BIO | a function of the query's model-visible RNA written into program features; its provenance record declares this | CIRCULAR_BY_CONSTRUCTION | refused by the provenance check before scoring; any agreement it shows is guaranteed and never counted |
| STATIC_OBJECT | the BIO and RNA_TWIN worlds, scored with a static object only | the feature-to-gene map itself, identical in both worlds | NON_IDENTIFIABLE_BY_DESIGN | identical statistics for the BIO and RNA_TWIN worlds (matrix P1); a difference is a leak |
| OBJECT_NUISANCE_ONLY | S157 NULL: no program | base plus gamma times q at program features, q an object-only per-cell process | NO_PROGRAM | no program-object coupling reported: object signal without an RNA program is not a program |

## scoring

**statistic_family:** declared by the deciding lane before generation, once the object is chosen; a function of permitted inputs only; computed blind with arm labels hidden (the S157 Blinding pattern) and with resampling indices fixed and shared across arms (the S171 repair)

### comparisons

- BIO vs RNA_TWIN
- BIO vs MULTIMODAL_TWIN
- BIO vs MULTIMODAL_TWIN_GLOBAL
- BIO vs CLEAN
- BIO vs OBJECT_NUISANCE_ONLY
- STATIC_OBJECT: BIO world vs RNA_TWIN world
- QUERY_LEAK: provenance check only

**reporting:** effect sizes with intervals for designed-identifiable pairs; bitwise equality checks for designed-non-identifiable pairs; no pass or fail threshold

## falsification_logic

| id | arms | condition | consequence |
|---|---|---|---|
| F1_LEAK | BIO; MULTIMODAL_TWIN | any statistic differs | the scorer reads something the observables do not contain: STOP |
| F2_STATIC_LEAK | STATIC_OBJECT | the BIO and RNA_TWIN worlds differ under the static object | STOP |
| F3_CIRCULARITY_BLIND | QUERY_LEAK | not refused by the provenance check, or its agreement counted | STOP |
| F4_FALSE_PROGRAM | CLEAN; OBJECT_NUISANCE_ONLY | program-object coupling reported | STOP |
| F5_INSENSITIVE | BIO; RNA_TWIN | not separated when the designed object effect is present | report that the object or scorer is insufficient; do not tune to rescue |
| F6_DECOY_BLIND | BIO; MULTIMODAL_TWIN_GLOBAL | not separated although decoys allow it | report that the scorer ignores within-object controls |

## object_choice_slots

| slot | value | why |
|---|---|---|
| object_class | UNSET | O_NUCLEUS or O_DONOR is the choice of evidence object |
| feature_universe_size_and_decoy_matching | UNSET | depends on the object's features |
| object_depth_distribution | UNSET | measured from the chosen object, never invented |
| noise_family_and_dispersion | UNSET | measured from the chosen object |
| gamma | UNSET | the program's effect size on the object is object-specific |
| gamma_g | UNSET | the yield effect size is object-specific |
| fraction_of_program_genes_with_a_footprint | UNSET | object-specific |
| object_nuisance_law | UNSET | the object's own nuisance (matrix P2), for example nucleus quality |
| donor_count_and_nuclei_per_donor | UNSET | for O_DONOR, set from the chosen cohort |

## acceptance_thresholds


**threshold_policy:** No acceptance threshold is defined, and none is derived from S149 or S159: the within-cohort envelopes are a candidate diagnostic without authority and the S159 interval rule is open. Designed-non-identifiable pairs are checked for bitwise equality; designed-identifiable pairs are reported as effect sizes with intervals.

**claim_discipline:** A pass would show that a scorer and an object of the chosen class can break an RNA-confined twin in a world built to allow it, and correctly cannot break a multimodal twin. It would not show that a real object breaks a real twin (matrix P5), and it qualifies no target, representation or object.

## governance

- TRAINING=OFF; ZERO_UPDATE only
- no real RNA, TEST, Morabito, 500K or Stage 4
- no target, representation, estimand, weighting or threshold selected

**recorded_utc:** 2026-10-07T06:18:05Z

**head_when_recorded:** de9bd5110c3c07ab1e00770b2ce45c603bb8e3ff

## evidence

**results/v77/V77_S157_TERMINAL_RECEIPT_V1.json:** 9c4fd3820631dc9920f91278a75899291101045eab2ed785a457fcd2ab0cec00

**results/v77/V77_INDEPENDENT_EVIDENCE_MATRIX_V1.json:** 6f2a61831ae816264b943b777bcfd43df7d40a48f17a98d11180c313898a5b32

**results/v77/V77_REGULATORY_CIRCULARITY_AUDIT_V1.json:** 4de5f27371202b584a7c3230f7a8911928970e4f8352852d51d0144268a869e0

**results/v77/V77_S157_PAIRED_CHALLENGE_PREREGISTRATION_V1.json:** 628d8be0f50b94ee4d6974161f25bd58ecba5ea5c2b38327f7dd3438cd47ed55
