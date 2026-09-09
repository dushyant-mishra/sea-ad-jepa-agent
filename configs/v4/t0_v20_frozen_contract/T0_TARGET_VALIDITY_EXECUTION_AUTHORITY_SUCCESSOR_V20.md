# T0 target-validity execution-authority successor V20

Status: `T0_V18_SCIENTIFIC_SPECIFICATION_PRESERVED__V20_EXECUTION_AUTHORITY_REPAIR_CANDIDATE__REAL_T0_FORBIDDEN`

## 1. Scope and chronology

V20 is a prospective implementation/governance successor to the failed V19 candidate.

V19 is preserved byte-for-byte inside:

`history/JEPA_T0_V19_EXECUTION_AUTHORITY_REVIEW_PACKAGE_20260907.zip`

V20 does **not** alter the T0 scientific/statistical specification frozen in:

`T0_TARGET_VALIDITY_SCIENTIFIC_FREEZE_CANDIDATE_V18.md`

SHA-256:

`0851b47d2351ded1be35a772bb9d7c05ed57d4bbbe551d81c7845a87ace85050`

All V18 estimands, donor-role rules, feature split, q=.95 tail, nuisance models, HC3/Freedman-Lane engines, alpha levels, hierarchy, claim scope, and external-data requirements remain controlling.

V20 retains the V19 execution-input binding design and repairs only two defects found by independent review:

1. malformed permutation input could be absorbed into a legitimate `NOT_ESTIMABLE` result when an estimability failure occurred first;
2. superseded V1 API-map authority remained in the declared-active set, while the live V2 map lacked an exact public-definition completeness test.

No V18 scientific rule is reopened.

## 2. INVALID outranks NOT_ESTIMABLE

`t0_studentized_fl_v1.studentized_freedman_lane` now validates structural permutation well-formedness **before any rank, leverage, HC3-variance, or other estimability calculation**.

The required ordering is:

1. validate finite one-dimensional response;
2. validate reduced-design shape/rows/finiteness;
3. validate predictor shape/length/finiteness;
4. validate permutation object:
   - two-dimensional;
   - at least one row;
   - exact width `n`;
   - integer dtype;
   - every row is a permutation of `0..n-1`;
5. only then evaluate reduced/full-design rank, residual degrees of freedom, leverage, HC3 variance, and other estimability conditions.

Malformed permutation input raises `ValueError` even when the supplied predictor is aliased or another legitimate not-estimable condition is also present.

`t0_inference_safe_v1.safe_studentized_fl` catches only `NotEstimableError`. Structural `ValueError` therefore propagates and cannot be converted into `{'estimable': False}`.

The active regression set includes known-answer tests for:

- valid aliased input → `estimable=False` with an alias reason;
- float permutation dtype + aliased predictor → `ValueError`;
- malformed permutation shape + aliased predictor → `ValueError`;
- out-of-range permutation row + aliased predictor → `ValueError`.

Thus a structural integrity failure cannot be byte-equivalent to a legitimate scientific `NOT_ESTIMABLE` verdict.

## 3. Current public API authority is V3 only

The sole current public API authority is:

`T0_PUBLIC_API_AUTHORITY_MAP_V3.csv`

SHA-256:

`4aa3a3d11d7f851b106b8a2f33e1b4b345eddbcdd1f2baaab9f30b0aff1bec2c`

V3 is tested against the actual top-level public function definitions in `current/code/*.py` for:

- exact set equality;
- uniqueness;
- allowed classification vocabulary;
- nonempty claim boundaries;
- exactly three canonical conclusion entrypoints.

The canonical conclusion entrypoints remain exactly:

1. `t0_canonical_freeze_v2.freeze_target_after_role_v2`
2. `t0_canonical_freeze_v2.freeze_tail_after_discovery_authority_v2`
3. `t0_adjudicator_v2.adjudicate_from_raw_v2`

The V18 entrypoints remain `SUPERSEDED_NON_AUTHORITATIVE_PRIMITIVE`.

## 4. Superseded authorities cannot remain active

The exact supersession registry is:

`T0_V20_SUPERSEDED_AUTHORITY_REGISTRY.csv`

SHA-256:

`ef54a8d0cc2f2e9c160e459bd8e239c20c10a0e052a369cc2ec3688096de909c`

It binds the historical bytes and archived locations of:

- API map V1;
- API map V2;
- their active tests;
- V19 active-manifest/equivalence tests;
- historical V18/V19 equivalence audit code.

The V20 audit requires simultaneously that:

- each archived artifact exists and matches its frozen bytes/hash;
- none of the old active paths exists under `current/`;
- no superseded test path occurs in the V20 active-test manifest.

The failed V19 package remains separately preserved in full for exact external-review chronology.

## 5. V19 execution-input binding remains unchanged

V20 retains V19's pretarget and preadjudication authority model unchanged.

Pretarget authority binds:

- donor-role root;
- exact role metadata;
- discovery AT8/age/sex;
- discovery full-scalar expression identity/count payload;
- `source_library`;
- external source-reference hashes.

Preadjudication authority binds:

- pretarget root;
- role/target/tail/discovery/technical/family roots;
- confirmation AT8/age/sex/IMMUNE_FRACTION/technical fields;
- confirmation expression identity/count payload;
- confirmation `source_library`;
- rare5 status authority digest/status;
- external source-reference hashes.

The V19 behavioral execution-binding attacks remain active in V20.

## 6. Rare5 and technical firewalls remain unchanged

V20 retains:

- `t0_target_family_authority_v3` status-file binding;
- PRIMARY_ONLY family semantics;
- STOP/new contract if rare5 becomes decision-capable;
- `t0_technical_registry_v3` reserved-field firewall;
- exact confirmation technical-value binding through the preadjudication authority.

## 7. Production/test separation remains unchanged

Synthetic local authorities set `real_execution_ready=false`.

The three production conclusion entrypoints hard-require real execution readiness and expose no caller bypass argument.

`_for_test` entrypoints remain diagnostic/regression-only.

Therefore real disease-linked T0 remains structurally impossible from this package.

## 8. Exact active implementation/test authorities

V20 implementation manifest:

`T0_V20_IMPLEMENTATION_MANIFEST.csv`

SHA-256:

`1f55741e83bf1b504c052975649ec3a8978428b311251c9b0bd5271cf20c6b9d`

V20 active-test manifest:

`T0_V20_ACTIVE_TEST_MANIFEST.csv`

SHA-256:

`99b9aeacea525ff06d6ab6d64aaed2fd74167795c2da21c02ef912f867fb0d6b`

V20 execution constants:

`T0_V20_EXECUTION_AUTHORITY_CONSTANTS.json`

SHA-256:

`d15a1773469f67140de199ddcaf784b3c811c92ae7ed3f8bc4d6ab9f90252833`

The V20 equivalence audit verifies exact current implementation coverage, exact active-test membership/hashes, complete V3 API mapping, supersession hygiene, V18 scientific immutability, production/test separation, and these exact contract citations.

A static audit PASS is **not** represented as proof that pytest passed. Full-suite execution is a separate required review step and is recorded separately after execution.

## 9. Required V20 independent review terminal

If a substantive defect remains, preserve V20 unchanged and return:

`STOP_T0_V20_INDEPENDENT_REVIEW__<PRECISE_REASON>`

If clean, return:

`PASS_T0_V20_INDEPENDENT_REVIEW`

A PASS means only:

`T0_V18_SCIENTIFIC_SPECIFICATION_PRESERVED__V20_EXECUTION_BINDING_AND_INVALID_PRECEDENCE_ACCEPTED__REAL_T0_STILL_UNAUTHORIZED`

It does not authorize pathology access or real T0 execution.

## 10. External blockers remain

Even after V20 PASS, real T0 still requires prospective materialization/binding of:

- exact canonical MTG AT8 source bytes;
- donor join, units, missingness and identity transform;
- canonical age/sex and technical metadata;
- exact raw expression and `source_library` authorities;
- final metadata-complete donor roles;
- any large-source membership regeneration authority required for independent execution.
