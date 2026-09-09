# T0 target-validity execution-authority successor V19

Status: `T0_V18_SCIENTIFIC_SPECIFICATION_PRESERVED__V19_EXECUTION_AUTHORITY_REPAIR_CANDIDATE__REAL_T0_FORBIDDEN`

## 1. Scientific authority is unchanged

This V19 successor does **not** alter the scientific/statistical specification frozen in:

`T0_TARGET_VALIDITY_SCIENTIFIC_FREEZE_CANDIDATE_V18.md`

SHA-256:

`0851b47d2351ded1be35a772bb9d7c05ed57d4bbbe551d81c7845a87ace85050`

All V18 estimands, donor-role rules, feature split, q=.95 tail, nuisance models, permutation/HC3 engines, alpha thresholds, hierarchical non-rescue rule, claim scope, and external-data requirements remain controlling.

V19 exists only because independent review showed that V18's conclusion-bearing APIs could accept caller-supplied AT8/age/sex/technical/expression/source_library values without proving that those exact values were the values frozen for execution.

## 2. V18 execution entrypoints are superseded

The following V18 functions remain byte-preserved for regression/history but are no longer conclusion-bearing:

- `t0_canonical_freeze_v1.freeze_target_after_role`
- `t0_canonical_freeze_v1.freeze_tail_after_discovery_authority`
- `t0_adjudicator_v1.adjudicate_from_raw`

Only the V19 V2 production entrypoints may create a conclusion-bearing stage:

1. `t0_canonical_freeze_v2.freeze_target_after_role_v2`
2. `t0_canonical_freeze_v2.freeze_tail_after_discovery_authority_v2`
3. `t0_adjudicator_v2.adjudicate_from_raw_v2`

The exact classification authority is:

`current/authority/T0_PUBLIC_API_AUTHORITY_MAP_V2.csv`.

## 3. Pretarget execution-input authority

Before target fitting, V19 requires a flat, hash-verified pretarget authority binding:

- the frozen donor-role package root;
- the exact complete role metadata payload used to regenerate the donor-role package:
  - donor_id
  - AT8_available
  - age
  - sex
  - technical_complete
- the exact discovery donor metadata payload:
  - donor_id
  - AT8
  - age
  - sex
- exact full-scalar expression payload for every discovery cell:
  - frozen 35,076 feature order
  - matrix_id
  - local_row
  - cell_id
  - donor_id
  - stable_key
  - source_library
  - sparse raw integer counts
- external source-reference hashes carried for later materialization review.

The authority builder independently regenerates the frozen V2 donor-role package from packaged membership support plus the supplied role metadata. Discovery age/sex must equal the age/sex used in the donor-role authority.

A one-value change to discovery AT8, age, sex, raw count, row identity, feature order, or source_library must change the authority payload and be rejected under the old root.

## 4. Preadjudication execution-input authority

After target, tail, technical-registry and family freeze but before confirmation inference, V19 requires a second flat, hash-verified authority binding:

- pretarget authority root;
- donor-role root;
- target root;
- tail root;
- discovery-authority root;
- technical-registry root;
- target-family root;
- exact confirmation metadata columns and values;
- exact confirmation full-scalar expression/source_library payload;
- exact technical-block registry;
- exact rare5-status authority digest and status;
- external source-reference hashes carried for later materialization review.

Any change to confirmation AT8, age, sex, IMMUNE_FRACTION, a predeclared extra technical value, raw count, row identity, feature order, or source_library must be rejected before inference under the previously frozen authority root.

## 5. Rare5/family freshness

V18 scientific family semantics remain `PRIMARY_ONLY` with historical rare5 non-decision-capable.

V19 removes the caller-supplied status-string trust boundary. `t0_target_family_authority_v3` builds the family package only from an exact rare5 decision-capability status-authority file with schema:

`JEPA_T0_RARE5_DECISION_CAPABILITY_STATUS_V1`

Allowed current status:

`NOT_DECISION_CAPABLE_AUTHORITY_MISSING`

The adjudicator rehashes the status-authority bytes immediately before inference and requires byte identity with the status digest frozen in the family package. A status-file change or transition to decision-capable requires a new reviewed family/multiplicity contract.

## 6. Technical-covariate firewall

V18 technical sensitivity semantics are unchanged.

`t0_technical_registry_v3` additionally forbids outcome/nuisance/composition/state fields from being smuggled into an "extra technical" block. Reserved fields include AT8, age, sex, IMMUNE_FRACTION, STATE_SCORE and TAIL_PREVALENCE.

The exact confirmation technical values are included in the preadjudication metadata payload, so altering one under a frozen execution root is rejected before inference.

## 7. Production/test separation

The local package contains synthetic regression builders. They intentionally set:

`real_execution_ready = false`

The three production V2 conclusion entrypoints hard-require `real_execution_ready == true` and expose **no caller flag** that can bypass this check.

Explicit `_for_test` entrypoints exist solely to prove the binding logic with synthetic fixtures. They are classified `DIAGNOSTIC_OR_REGRESSION_ONLY` and are not production authority.

Therefore this package itself cannot authorize real disease-linked T0 execution.

A later data-only external materialization step must bind the exact canonical external pathology/demographic/technical/expression/source-library authorities before the production V2 entrypoints can run.

## 8. Required mutation attacks

The V19 active regression set must demonstrate rejection of at least:

1. confirmation AT8 mutation;
2. discovery AT8 mutation;
3. role age mutation;
4. discovery age/sex mismatch with role authority;
5. confirmation age/sex mutation;
6. IMMUNE_FRACTION mutation;
7. extra technical-value mutation;
8. confirmation raw-count mutation;
9. discovery raw-count mutation;
10. source_library mutation;
11. rerooted/tampered execution authority;
12. changed rare5 status-authority bytes;
13. decision-capable rare5 authority passed to family builder;
14. outcome field declared as technical covariate;
15. missing execution authority;
16. production adjudicator invoked with test-only/unmaterialized authority.

`NOT_APPLICABLE` is not a success state for any required execution-binding attack.

## 9. Claim boundary after V19 review

A successful independent review of V19 means only:

`T0_V18_SCIENTIFIC_SPECIFICATION_PRESERVED__V19_EXECUTION_BINDING_MECHANICS_ACCEPTED__REAL_T0_STILL_UNAUTHORIZED`

It does not authorize pathology access or real T0 execution.

External blockers remain the exact canonical AT8/join/units/missingness authority, canonical age/sex/technical metadata, raw expression plus source_library, final metadata-complete donor-role materialization, and any required large-source membership regeneration authority.
